# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowQueue(models.Model):
    """A service-point queue (reception, triage, doctor room, lab draw, pharmacy).
    Each clinic can run several queues in parallel."""

    _name = "mediflow.queue"
    _description = "Service Queue"
    _inherit = ["mediflow.company.scope.mixin"]
    _order = "sequence, name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, help="Short code used on printed tokens, e.g. 'TRI'.")
    service_point = fields.Selection([
        ("reception", "Reception"),
        ("triage", "Triage"),
        ("doctor", "Doctor"),
        ("lab", "Lab Draw"),
        ("pharmacy", "Pharmacy"),
        ("billing", "Billing"),
    ], default="reception", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    entry_ids = fields.One2many("mediflow.queue.entry", "queue_id", string="Entries")
    waiting_count = fields.Integer(compute="_compute_counts", string="Waiting")
    serving_count = fields.Integer(compute="_compute_counts", string="Serving")
    avg_wait_minutes = fields.Float(compute="_compute_counts", string="Avg Wait (min)")

    def _compute_counts(self):
        Entry = self.env["mediflow.queue.entry"]
        for queue in self:
            queue.waiting_count = Entry.search_count([
                ("queue_id", "=", queue.id), ("state", "=", "waiting")])
            queue.serving_count = Entry.search_count([
                ("queue_id", "=", queue.id), ("state", "=", "serving")])
            done = Entry.search([
                ("queue_id", "=", queue.id), ("state", "=", "done"),
                ("wait_minutes", ">", 0)], limit=50)
            queue.avg_wait_minutes = round(
                sum(done.mapped("wait_minutes")) / len(done), 1) if done else 0.0

    def action_call_next(self):
        """Call the next waiting entry (lowest sequence)."""
        self.ensure_one()
        nxt = self.env["mediflow.queue.entry"].search([
            ("queue_id", "=", self.id), ("state", "=", "waiting"),
        ], order="sequence, id", limit=1)
        if nxt:
            nxt.action_call()
        return nxt

    def action_open_board(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "mediflow.queue.entry",
            "view_mode": "list,form",
            "domain": [("queue_id", "=", self.id),
                       ("state", "in", ("waiting", "called", "serving"))],
            "context": {"default_queue_id": self.id},
        }
