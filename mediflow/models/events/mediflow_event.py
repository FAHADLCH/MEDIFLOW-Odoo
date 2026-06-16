# -*- coding: utf-8 -*-
import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 8


class MediflowEvent(models.Model):
    """Durable domain event. Created synchronously inside the originating
    transaction (so it is never lost), then delivered asynchronously by the
    delivery cron. Supports retry with capped attempts and manual replay."""

    _name = "mediflow.event"
    _description = "MEDIFLOW Domain Event"
    _order = "id desc"

    name = fields.Char(string="Event", required=True, index=True)
    version = fields.Char(string="Payload Version", default="1")
    payload = fields.Text(string="Payload (JSON)")
    source_model = fields.Char(string="Source Model", index=True)
    source_res_id = fields.Integer(string="Source Record")
    company_id = fields.Many2one("res.company", string="Clinic", index=True,
                                 default=lambda self: self.env.company)
    state = fields.Selection([
        ("pending", "Pending"),
        ("delivering", "Delivering"),
        ("done", "Delivered"),
        ("failed", "Failed"),
    ], default="pending", required=True, index=True)
    attempts = fields.Integer(string="Attempts", default=0)
    last_error = fields.Text(string="Last Error")
    delivered_at = fields.Datetime(string="Delivered At")

    @api.model
    def emit(self, name, payload, source_model=None, source_res_id=None, version="1",
             company_id=None):
        return self.sudo().create({
            "name": name,
            "version": version,
            "payload": json.dumps(payload, default=str),
            "source_model": source_model,
            "source_res_id": source_res_id,
            "company_id": company_id or self.env.company.id,
        })

    @api.model
    def cron_deliver(self, limit=200):
        """Delivery worker. Picks pending events and dispatches them to matching
        webhooks. Designed to be idempotent and safe to run frequently."""
        events = self.search([("state", "in", ("pending", "failed")),
                              ("attempts", "<", MAX_ATTEMPTS)], limit=limit)
        Webhook = self.env["mediflow.webhook"].sudo()
        for event in events:
            event.state = "delivering"
            try:
                subscribers = Webhook.search([
                    ("active", "=", True),
                    "|", ("company_id", "=", False), ("company_id", "=", event.company_id.id),
                ])
                payload = json.loads(event.payload or "{}")
                for hook in subscribers:
                    if hook._matches(event.name):
                        hook._deliver(event.name, event.version, payload)
                event.write({"state": "done", "delivered_at": fields.Datetime.now(),
                             "attempts": event.attempts + 1, "last_error": False})
            except Exception as exc:  # noqa: BLE001 - record and retry
                _logger.warning("MEDIFLOW event %s delivery failed: %s", event.name, exc)
                event.write({"state": "failed", "attempts": event.attempts + 1,
                             "last_error": str(exc)})
        return True

    def action_replay(self):
        self.write({"state": "pending", "attempts": 0, "last_error": False})
        return True
