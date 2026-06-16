# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class MediflowVRevenue(models.Model):
    """Read-only SQL view: one row per posted MEDIFLOW customer invoice with
    AR-aging bucket and patient-responsibility for the Revenue Cycle dashboard
    (docs 08 §6). Aging is computed from invoice_date_due relative to today."""

    _name = "mediflow.v.revenue"
    _description = "Revenue Cycle (view)"
    _auto = False
    _order = "invoice_date desc"

    id = fields.Integer(readonly=True)
    company_id = fields.Many2one("res.company", string="Clinic", readonly=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    invoice_date = fields.Date(readonly=True)
    payment_state = fields.Char(readonly=True)
    amount_total = fields.Monetary(string="Invoiced", readonly=True, aggregator="sum")
    amount_residual = fields.Monetary(string="Open Balance", readonly=True,
                                      aggregator="sum")
    amount_paid = fields.Monetary(string="Collected", readonly=True, aggregator="sum")
    patient_responsibility = fields.Monetary(string="Patient Responsibility",
                                             readonly=True, aggregator="sum")
    aging_bucket = fields.Selection([
        ("current", "0-30"),
        ("b31_60", "31-60"),
        ("b61_90", "61-90"),
        ("b90_plus", "90+"),
    ], string="AR Aging", readonly=True)
    invoice_count = fields.Integer(string="Invoices", readonly=True, aggregator="sum")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    m.id                        AS id,
                    m.company_id                AS company_id,
                    m.mediflow_patient_id       AS patient_id,
                    m.currency_id               AS currency_id,
                    m.invoice_date              AS invoice_date,
                    m.payment_state             AS payment_state,
                    m.amount_total              AS amount_total,
                    m.amount_residual           AS amount_residual,
                    (m.amount_total - m.amount_residual) AS amount_paid,
                    COALESCE(m.mediflow_patient_responsibility, 0.0)
                                                AS patient_responsibility,
                    CASE
                        WHEN m.amount_residual <= 0 THEN 'current'
                        WHEN m.invoice_date_due IS NULL THEN 'current'
                        WHEN (CURRENT_DATE - m.invoice_date_due) <= 30 THEN 'current'
                        WHEN (CURRENT_DATE - m.invoice_date_due) <= 60 THEN 'b31_60'
                        WHEN (CURRENT_DATE - m.invoice_date_due) <= 90 THEN 'b61_90'
                        ELSE 'b90_plus'
                    END                         AS aging_bucket,
                    1                           AS invoice_count
                FROM account_move m
                WHERE m.is_mediflow_invoice IS TRUE
                  AND m.move_type = 'out_invoice'
                  AND m.state = 'posted'
            )
        """ % self._table)
