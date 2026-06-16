# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class MediflowVLabTat(models.Model):
    """Read-only SQL view: one row per released-or-final lab result joined to its
    order, exposing turnaround time and abnormal/critical flags for the Lab
    Diagnostics dashboard (docs 08 §3). TAT = released_at - order_date."""

    _name = "mediflow.v.lab.tat"
    _description = "Lab Turnaround (view)"
    _auto = False
    _order = "released_at desc"

    id = fields.Integer(readonly=True)
    company_id = fields.Many2one("res.company", string="Clinic", readonly=True)
    test_id = fields.Many2one("mediflow.lab.test", string="Test", readonly=True)
    order_id = fields.Many2one("mediflow.lab.order", string="Lab Order", readonly=True)
    state = fields.Selection([
        ("preliminary", "Preliminary"),
        ("verified", "Verified"),
        ("released", "Released"),
        ("amended", "Amended"),
        ("cancelled", "Cancelled"),
    ], readonly=True)
    order_date = fields.Datetime(string="Ordered On", readonly=True)
    released_at = fields.Datetime(string="Released At", readonly=True)
    tat_hours = fields.Float(string="TAT (h)", readonly=True, aggregator="avg")
    is_abnormal = fields.Integer(string="Abnormal", readonly=True, aggregator="sum")
    is_critical = fields.Integer(string="Critical", readonly=True, aggregator="sum")
    is_pending = fields.Integer(string="Pending Verify", readonly=True, aggregator="sum")
    result_count = fields.Integer(string="Results", readonly=True, aggregator="sum")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    r.id                AS id,
                    r.company_id        AS company_id,
                    r.test_id           AS test_id,
                    r.order_id          AS order_id,
                    r.state             AS state,
                    o.order_date        AS order_date,
                    r.released_at       AS released_at,
                    CASE WHEN r.released_at IS NOT NULL AND o.order_date IS NOT NULL
                         THEN EXTRACT(EPOCH FROM (r.released_at - o.order_date)) / 3600.0
                         ELSE NULL END  AS tat_hours,
                    CASE WHEN r.abnormal_flag IS NOT NULL
                              AND r.abnormal_flag != 'normal' THEN 1 ELSE 0 END
                                        AS is_abnormal,
                    CASE WHEN r.is_critical IS TRUE THEN 1 ELSE 0 END AS is_critical,
                    CASE WHEN r.state = 'preliminary' THEN 1 ELSE 0 END AS is_pending,
                    1                   AS result_count
                FROM mediflow_lab_result r
                JOIN mediflow_lab_order o ON o.id = r.order_id
            )
        """ % self._table)
