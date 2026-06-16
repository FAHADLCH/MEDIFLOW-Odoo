# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class MediflowQueueEntry(models.Model):
    """A token/ticket in a service queue with its full lifecycle. Every state
    change pushes a live-board update over the event bus and records wait/serve
    durations for analytics."""

    _name = "mediflow.queue.entry"
    _description = "Queue Entry"
    _inherit = [
        "mediflow.company.scope.mixin",
        "mediflow.state.machine.mixin",
        "mediflow.event.mixin",
    ]
    _order = "sequence, id"

    # ----- State machine (docs/phase-1/07-state-machines.md §10) -----
    _sm_field = "state"
    _sm_transitions = {
        "waiting": {"called", "no_show"},
        "called": {"serving", "waiting"},
        "serving": {"done"},
    }
    _sm_terminal = {"done", "no_show"}

    token = fields.Char(string="Token", required=True, copy=False, index=True,
                        default=lambda self: _("New"))
    queue_id = fields.Many2one("mediflow.queue", string="Queue", required=True,
                               index=True, ondelete="cascade")
    patient_id = fields.Many2one("mediflow.patient", string="Patient", index=True,
                                 ondelete="cascade")
    appointment_id = fields.Many2one("mediflow.appointment", string="Appointment",
                                     ondelete="set null")
    sequence = fields.Integer(default=10, index=True)
    priority = fields.Selection([
        ("0", "Normal"), ("1", "Urgent"), ("2", "Emergency"),
    ], default="0")
    state = fields.Selection([
        ("waiting", "Waiting"),
        ("called", "Called"),
        ("serving", "Serving"),
        ("done", "Done"),
        ("no_show", "No-show"),
    ], default="waiting", required=True, index=True)
    created_at = fields.Datetime(default=fields.Datetime.now, index=True)
    called_at = fields.Datetime()
    serving_at = fields.Datetime()
    done_at = fields.Datetime()
    wait_minutes = fields.Float(compute="_compute_durations", store=True)
    serve_minutes = fields.Float(compute="_compute_durations", store=True)
    counter = fields.Char(string="Counter / Room")

    @api.depends("created_at", "called_at", "serving_at", "done_at")
    def _compute_durations(self):
        for entry in self:
            entry.wait_minutes = entry._minutes(entry.created_at, entry.called_at)
            entry.serve_minutes = entry._minutes(entry.serving_at, entry.done_at)

    @staticmethod
    def _minutes(start, stop):
        if start and stop:
            return round((stop - start).total_seconds() / 60.0, 1)
        return 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("token", _("New")) == _("New"):
                queue = self.env["mediflow.queue"].browse(vals.get("queue_id"))
                seq = self.env["ir.sequence"].next_by_code("mediflow.queue.entry") or "0"
                vals["token"] = "%s-%s" % (queue.code or "Q", seq)
        entries = super().create(vals_list)
        for entry in entries:
            entry._emit_event("queue.entry.created",
                              {"id": entry.id, "queue_id": entry.queue_id.id,
                               "token": entry.token})
        return entries

    # ----- Actions -----
    def action_call(self):
        self.with_context(sm_internal=True).write({"called_at": fields.Datetime.now()})
        self.transition("called")

    def action_start_serving(self):
        self.with_context(sm_internal=True).write({"serving_at": fields.Datetime.now()})
        self.transition("serving")

    def action_done(self):
        self.with_context(sm_internal=True).write({"done_at": fields.Datetime.now()})
        self.transition("done")

    def action_recycle(self):
        """Missed when called: send back to waiting."""
        self.transition("waiting")

    def action_no_show(self):
        self.transition("no_show")
