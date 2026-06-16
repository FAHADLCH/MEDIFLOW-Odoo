# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MediflowAppointment(models.Model):
    """Appointment. Booking acquires a row lock on the slot to guarantee no
    double-booking under concurrency, in addition to the slot's DB uniqueness.
    Projects to FHIR ``Appointment``."""

    _name = "mediflow.appointment"
    _description = "Appointment"
    _inherit = [
        "mediflow.company.scope.mixin",
        "mediflow.phi.audit.mixin",
        "mediflow.state.machine.mixin",
        "mediflow.event.mixin",
        "mail.thread",
        "mail.activity.mixin",
    ]
    _order = "start desc, id desc"

    # ----- State machine (docs/phase-1/07-state-machines.md §1) -----
    _sm_field = "state"
    _sm_transitions = {
        "booked": {"confirmed", "cancelled", "no_show"},
        "confirmed": {"in_consult", "cancelled", "no_show"},
        "in_consult": {"completed"},
    }
    _sm_terminal = {"cancelled", "no_show", "completed"}

    name = fields.Char(string="Reference", required=True, copy=False, index=True,
                       default=lambda self: _("New"))
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True, ondelete="restrict", tracking=True)
    practitioner_id = fields.Many2one("mediflow.practitioner", string="Practitioner",
                                      required=True, index=True, ondelete="restrict",
                                      tracking=True)
    resource_id = fields.Many2one("mediflow.resource", string="Room")
    slot_id = fields.Many2one("mediflow.appointment.slot", string="Slot",
                              ondelete="restrict", copy=False)
    start = fields.Datetime(required=True, index=True, tracking=True)
    stop = fields.Datetime(tracking=True)
    duration = fields.Integer(string="Duration (min)", default=15)
    walk_in = fields.Boolean(string="Walk-in", default=False)
    reason = fields.Char(string="Reason")
    reason_code = fields.Selection([
        ("consult", "Consultation"),
        ("followup", "Follow-up"),
        ("procedure", "Procedure"),
        ("lab", "Lab Only"),
    ], default="consult")
    cancel_reason = fields.Char(string="Cancellation Reason")
    encounter_id = fields.Many2one("mediflow.encounter", string="Encounter", readonly=True)
    state = fields.Selection([
        ("booked", "Booked"),
        ("confirmed", "Confirmed"),
        ("in_consult", "In Consultation"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("no_show", "No-show"),
    ], default="booked", required=True, tracking=True, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                company_id = vals.get("company_id") or self.env.company.id
                seq = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = seq.next_by_code("mediflow.appointment") or _("New")
        appointments = super().create(vals_list)
        appointments._lock_slot()
        for appt in appointments:
            appt._emit_event("appointment.booked", {"id": appt.id,
                                                     "patient_id": appt.patient_id.id})
        return appointments

    def _lock_slot(self):
        """Acquire a row lock on the chosen slot and mark it busy. Raises if the
        slot was taken concurrently."""
        for appt in self.filtered("slot_id"):
            slot = appt.slot_id
            # Lock the row to serialize concurrent bookings of the same slot.
            self.env.cr.execute(
                "SELECT state FROM mediflow_appointment_slot WHERE id = %s FOR UPDATE",
                (slot.id,))
            row = self.env.cr.fetchone()
            if row and row[0] == "busy" and not slot.schedule_id.allow_overbook:
                raise UserError(_(
                    "This slot was just booked by someone else. Please choose another time."))
            slot.write({"state": "busy", "appointment_id": appt.id})
            appt.write({"start": slot.start, "stop": slot.stop,
                        "practitioner_id": slot.practitioner_id.id,
                        "resource_id": slot.resource_id.id or appt.resource_id.id})

    @api.constrains("start", "practitioner_id", "state")
    def _check_no_conflict(self):
        for appt in self:
            if appt.state in ("cancelled", "no_show"):
                continue
            clash = self.search_count([
                ("id", "!=", appt.id),
                ("practitioner_id", "=", appt.practitioner_id.id),
                ("start", "=", appt.start),
                ("state", "not in", ("cancelled", "no_show")),
            ])
            if clash and not (appt.slot_id and appt.slot_id.schedule_id.allow_overbook):
                raise ValidationError(_(
                    "%(prac)s already has an appointment at %(time)s.",
                    prac=appt.practitioner_id.name, time=appt.start))

    # ----- Actions / transitions -----
    def action_confirm(self):
        self.transition("confirmed")

    def action_cancel(self):
        for appt in self:
            if appt.slot_id:
                appt.slot_id.write({"state": "free", "appointment_id": False})
        self.transition("cancelled")

    def action_no_show(self):
        self.transition("no_show")

    def action_start_consult(self):
        """Open or create the encounter and move to in_consult."""
        self.ensure_one()
        if self.state == "booked":
            self.transition("confirmed")
        if not self.encounter_id:
            encounter = self.env["mediflow.encounter"].create({
                "patient_id": self.patient_id.id,
                "practitioner_id": self.practitioner_id.id,
                "appointment_id": self.id,
                "company_id": self.company_id.id,
                "state": "in_progress",
                "start": fields.Datetime.now(),
            })
            self.with_context(sm_internal=True).write({"encounter_id": encounter.id})
        if self.state == "confirmed":
            self.transition("in_consult")
        return {
            "type": "ir.actions.act_window",
            "res_model": "mediflow.encounter",
            "res_id": self.encounter_id.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.model
    def cron_mark_no_show(self, grace_minutes=30):
        """Flag confirmed/booked appointments past their start + grace as no-show."""
        deadline = fields.Datetime.now()
        candidates = self.search([
            ("state", "in", ("booked", "confirmed")),
            ("start", "<", deadline),
        ])
        from datetime import timedelta
        for appt in candidates:
            if appt.start + timedelta(minutes=grace_minutes) < deadline:
                appt.action_no_show()
        return True
