# -*- coding: utf-8 -*-
from odoo import fields, models


class MediflowAppointmentSlot(models.Model):
    """A bookable time slot for a practitioner (and optional resource).

    The ``(practitioner_id, start)`` uniqueness is enforced at the database level
    so two slots can never collide and, combined with the appointment booking
    lock, double-booking is impossible even under concurrency. Projects to FHIR
    ``Slot``."""

    _name = "mediflow.appointment.slot"
    _description = "Appointment Slot"
    _inherit = ["mediflow.company.scope.mixin"]
    _order = "start"

    schedule_id = fields.Many2one("mediflow.schedule", string="Schedule",
                                  ondelete="set null")
    practitioner_id = fields.Many2one("mediflow.practitioner", string="Practitioner",
                                      required=True, index=True, ondelete="cascade")
    resource_id = fields.Many2one("mediflow.resource", string="Room")
    start = fields.Datetime(required=True, index=True)
    stop = fields.Datetime(required=True)
    state = fields.Selection([
        ("free", "Free"),
        ("busy", "Booked"),
        ("blocked", "Blocked"),
    ], default="free", required=True, index=True)
    appointment_id = fields.Many2one("mediflow.appointment", string="Appointment",
                                     ondelete="set null")

    _sql_constraints = [
        ("practitioner_start_uniq", "unique(practitioner_id, start)",
         "A slot already exists for this practitioner at this time."),
    ]

    def name_get(self):
        result = []
        for slot in self:
            label = "%s @ %s" % (slot.practitioner_id.name or "",
                                 fields.Datetime.to_string(slot.start))
            result.append((slot.id, label))
        return result
