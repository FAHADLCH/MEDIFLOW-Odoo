# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MediflowSchedule(models.Model):
    """Working schedule for a practitioner (and optionally a resource). Drives
    slot generation. Projects to FHIR ``Schedule``."""

    _name = "mediflow.schedule"
    _description = "Practitioner Schedule"
    _inherit = ["mediflow.company.scope.mixin"]
    _order = "practitioner_id, weekday, start_hour"

    name = fields.Char(compute="_compute_name", store=True)
    practitioner_id = fields.Many2one("mediflow.practitioner", string="Practitioner",
                                      required=True, index=True, ondelete="cascade")
    resource_id = fields.Many2one("mediflow.resource", string="Default Room")
    weekday = fields.Selection([
        ("0", "Monday"), ("1", "Tuesday"), ("2", "Wednesday"), ("3", "Thursday"),
        ("4", "Friday"), ("5", "Saturday"), ("6", "Sunday"),
    ], required=True)
    start_hour = fields.Float(string="From", required=True, default=9.0)
    end_hour = fields.Float(string="To", required=True, default=17.0)
    slot_duration = fields.Integer(string="Slot (min)", default=15, required=True)
    allow_overbook = fields.Boolean(string="Allow Overbooking", default=False)
    active = fields.Boolean(default=True)

    @api.depends("practitioner_id", "weekday")
    def _compute_name(self):
        labels = dict(self._fields["weekday"].selection)
        for sched in self:
            sched.name = "%s - %s" % (sched.practitioner_id.name or "",
                                      labels.get(sched.weekday, ""))

    @api.constrains("start_hour", "end_hour", "slot_duration")
    def _check_hours(self):
        for sched in self:
            if sched.end_hour <= sched.start_hour:
                raise UserError(_("Schedule end time must be after start time."))
            if sched.slot_duration <= 0:
                raise UserError(_("Slot duration must be positive."))

    def action_generate_slots(self, days_ahead=14):
        """Generate free slots for the next ``days_ahead`` days from this schedule.
        Idempotent: existing slots for the same (practitioner, start) are skipped."""
        Slot = self.env["mediflow.appointment.slot"]
        today = fields.Date.context_today(self)
        created = Slot
        for sched in self:
            for offset in range(days_ahead):
                day = today + timedelta(days=offset)
                if str(day.weekday()) != sched.weekday:
                    continue
                cursor = sched.start_hour
                while cursor + sched.slot_duration / 60.0 <= sched.end_hour + 1e-6:
                    start_dt = datetime.combine(day, datetime.min.time()) + timedelta(hours=cursor)
                    stop_dt = start_dt + timedelta(minutes=sched.slot_duration)
                    exists = Slot.search_count([
                        ("practitioner_id", "=", sched.practitioner_id.id),
                        ("start", "=", start_dt),
                    ])
                    if not exists:
                        created |= Slot.create({
                            "schedule_id": sched.id,
                            "practitioner_id": sched.practitioner_id.id,
                            "resource_id": sched.resource_id.id,
                            "start": start_dt,
                            "stop": stop_dt,
                            "company_id": sched.company_id.id,
                        })
                    cursor += sched.slot_duration / 60.0
        return created

    @api.model
    def cron_generate_slots(self, days_ahead=14):
        self.search([("active", "=", True)]).action_generate_slots(days_ahead=days_ahead)
        return True
