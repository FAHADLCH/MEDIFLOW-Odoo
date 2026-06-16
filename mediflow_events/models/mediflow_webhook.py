# -*- coding: utf-8 -*-
import fnmatch
import hashlib
import hmac
import json
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:  # pragma: no cover - requests ships with Odoo
    requests = None


class MediflowWebhook(models.Model):
    """Outbound webhook subscription. Subscribers register an endpoint and an
    event pattern (glob, e.g. ``lab.result.*``). Payloads are HMAC-SHA256 signed
    so the receiver can verify authenticity."""

    _name = "mediflow.webhook"
    _description = "MEDIFLOW Webhook Subscription"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", string="Clinic",
                                 help="Leave empty to subscribe across all clinics.")
    url = fields.Char(string="Endpoint URL", required=True)
    event_pattern = fields.Char(string="Event Pattern", default="*", required=True,
                                help="Glob pattern, e.g. 'lab.result.*' or '*'.")
    secret = fields.Char(string="Signing Secret", required=True)
    timeout = fields.Integer(string="Timeout (s)", default=10)

    def _matches(self, event_name):
        self.ensure_one()
        return fnmatch.fnmatch(event_name, self.event_pattern or "*")

    def _deliver(self, event_name, version, payload):
        self.ensure_one()
        if requests is None:
            raise RuntimeError("python-requests is not available for webhook delivery")
        body = json.dumps({
            "event": event_name,
            "version": version,
            "payload": payload,
        }, default=str).encode("utf-8")
        signature = hmac.new(self.secret.encode("utf-8"), body,
                             hashlib.sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-Mediflow-Event": event_name,
            "X-Mediflow-Signature": "sha256=%s" % signature,
        }
        response = requests.post(self.url, data=body, headers=headers,
                                 timeout=self.timeout or 10)
        response.raise_for_status()
        return True
