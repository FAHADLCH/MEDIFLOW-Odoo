# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class MediflowVClaims(models.Model):
    """Read-only SQL view: one row per insurance claim with denial / approval
    flags for the Revenue Cycle dashboard (docs 08 §6). Denial rate is
    sum(is_denied) / sum(is_submitted) computed in the dashboard."""

    _name = "mediflow.v.claims"
    _description = "Claims Analytics (view)"
    _auto = False
    _order = "submission_date desc"

    id = fields.Integer(readonly=True)
    company_id = fields.Many2one("res.company", string="Clinic", readonly=True)
    payer_id = fields.Many2one("mediflow.payer", string="Payer", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("adjudicated", "Adjudicated"),
        ("paid", "Paid"),
        ("denied", "Denied"),
        ("appealed", "Appealed"),
    ], readonly=True)
    submission_date = fields.Date(readonly=True)
    adjudication_date = fields.Date(readonly=True)
    claimed_amount = fields.Monetary(string="Claimed", readonly=True, aggregator="sum")
    approved_amount = fields.Monetary(string="Approved", readonly=True, aggregator="sum")
    patient_responsibility = fields.Monetary(string="Patient Responsibility",
                                             readonly=True, aggregator="sum")
    is_submitted = fields.Integer(string="Submitted", readonly=True, aggregator="sum")
    is_denied = fields.Integer(string="Denied", readonly=True, aggregator="sum")
    is_paid = fields.Integer(string="Paid", readonly=True, aggregator="sum")
    claim_count = fields.Integer(string="Claims", readonly=True, aggregator="sum")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    c.id                        AS id,
                    c.company_id                AS company_id,
                    c.payer_id                  AS payer_id,
                    c.currency_id               AS currency_id,
                    c.state                     AS state,
                    c.submission_date           AS submission_date,
                    c.adjudication_date         AS adjudication_date,
                    COALESCE(c.claimed_amount, 0.0)         AS claimed_amount,
                    COALESCE(c.approved_amount, 0.0)        AS approved_amount,
                    COALESCE(c.patient_responsibility, 0.0) AS patient_responsibility,
                    CASE WHEN c.state IN ('submitted', 'adjudicated', 'paid',
                                          'denied', 'appealed')
                         THEN 1 ELSE 0 END      AS is_submitted,
                    CASE WHEN c.state = 'denied' THEN 1 ELSE 0 END AS is_denied,
                    CASE WHEN c.state = 'paid'   THEN 1 ELSE 0 END AS is_paid,
                    1                           AS claim_count
                FROM mediflow_claim c
            )
        """ % self._table)
