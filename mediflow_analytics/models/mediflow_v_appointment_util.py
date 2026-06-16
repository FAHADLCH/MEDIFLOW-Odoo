# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class MediflowVAppointmentUtil(models.Model):
    """Read-only SQL view: one row per appointment with flags and lead time for
    the Appointment & Utilization dashboard (docs 08 §2). Slot utilization is the
    ratio of booked appointments to generated slots; it is computed in the
    dashboard by comparing this view's count against mediflow.appointment.slot."""

    _name = "mediflow.v.appointment.util"
    _description = "Appointment Utilization (view)"
    _auto = False
    _order = "start desc"

    id = fields.Integer(readonly=True)
    company_id = fields.Many2one("res.company", string="Clinic", readonly=True)
    practitioner_id = fields.Many2one("mediflow.practitioner", string="Practitioner",
                                      readonly=True)
    state = fields.Selection([
        ("booked", "Booked"),
        ("confirmed", "Confirmed"),
        ("in_consult", "In Consultation"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("no_show", "No-show"),
    ], readonly=True)
    start = fields.Datetime(readonly=True)
    create_date = fields.Datetime(string="Booked On", readonly=True)
    lead_time_hours = fields.Float(string="Lead Time (h)", readonly=True, aggregator="avg")
    is_cancelled = fields.Integer(readonly=True, aggregator="sum")
    is_no_show = fields.Integer(readonly=True, aggregator="sum")
    is_walk_in = fields.Integer(readonly=True, aggregator="sum")
    is_completed = fields.Integer(readonly=True, aggregator="sum")
    appt_count = fields.Integer(string="Appointments", readonly=True, aggregator="sum")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    a.id                AS id,
                    a.company_id        AS company_id,
                    a.practitioner_id   AS practitioner_id,
                    a.state             AS state,
                    a.start             AS start,
                    a.create_date       AS create_date,
                    CASE WHEN a.start IS NOT NULL AND a.create_date IS NOT NULL
                         THEN EXTRACT(EPOCH FROM (a.start - a.create_date)) / 3600.0
                         ELSE NULL END  AS lead_time_hours,
                    CASE WHEN a.state = 'cancelled' THEN 1 ELSE 0 END AS is_cancelled,
                    CASE WHEN a.state = 'no_show'   THEN 1 ELSE 0 END AS is_no_show,
                    CASE WHEN a.walk_in IS TRUE     THEN 1 ELSE 0 END AS is_walk_in,
                    CASE WHEN a.state = 'completed' THEN 1 ELSE 0 END AS is_completed,
                    1                   AS appt_count
                FROM mediflow_appointment a
            )
        """ % self._table)
