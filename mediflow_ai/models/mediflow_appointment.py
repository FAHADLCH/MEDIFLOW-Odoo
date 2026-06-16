# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowAppointment(models.Model):
    """No-show risk scoring. Transparent and fully offline — the score is an
    explainable weighted heuristic, not a black box, so clinics can trust and
    audit it. It can later be swapped for a trained model behind the same field.
    """

    _inherit = "mediflow.appointment"

    mf_no_show_score = fields.Integer(
        string="No-show Risk", compute="_compute_no_show_risk", store=True,
        help="0-100. Higher means more likely to miss the appointment.")
    mf_no_show_band = fields.Selection([
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ], string="Risk Band", compute="_compute_no_show_risk", store=True, index=True)
    mf_risk_factors = fields.Char(string="Risk Drivers", compute="_compute_no_show_risk",
                                  store=True)

    @api.depends("patient_id", "start", "walk_in", "reason_code", "create_date", "state")
    def _compute_no_show_risk(self):
        now = fields.Datetime.now()
        for appt in self:
            score, factors = appt._score_no_show(now)
            appt.mf_no_show_score = score
            appt.mf_risk_factors = ", ".join(factors) if factors else "No elevated risk"
            appt.mf_no_show_band = (
                "high" if score >= 60 else "medium" if score >= 30 else "low")

    def _score_no_show(self, now):
        """Return ``(score 0-100, [factors])`` for one appointment."""
        self.ensure_one()
        score = 10
        factors = []

        # 1) Historical no-show rate for this patient.
        if self.patient_id:
            history = self.search_count([
                ("patient_id", "=", self.patient_id.id),
                ("id", "!=", self.id or 0),
                ("state", "in", ("completed", "no_show")),
            ])
            misses = self.search_count([
                ("patient_id", "=", self.patient_id.id),
                ("id", "!=", self.id or 0),
                ("state", "=", "no_show"),
            ])
            if history >= 1:
                rate = misses / float(history)
                score += int(rate * 45)
                if rate >= 0.34:
                    factors.append("history of no-shows")

        # 2) Lead time — very early bookings drift more.
        if self.start and self.create_date:
            lead_days = (self.start - self.create_date).days
            if lead_days >= 30:
                score += 18
                factors.append("booked >30 days ahead")
            elif lead_days >= 14:
                score += 10
                factors.append("booked >2 weeks ahead")

        # 3) Walk-ins effectively never no-show.
        if self.walk_in:
            score = max(0, score - 25)

        # 4) Appointment type.
        if self.reason_code == "followup":
            score += 8
            factors.append("follow-up visit")

        return max(0, min(100, score)), factors

    @api.model
    def _cron_score_upcoming_no_show(self):
        """Refresh risk for upcoming appointments so dashboards stay current as
        patient history changes. Batched to stay cheap at scale."""
        upcoming = self.search([
            ("start", ">=", fields.Datetime.now()),
            ("state", "in", ("booked", "confirmed")),
        ], limit=5000)
        upcoming._compute_no_show_risk()
