# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowCoverage(models.Model):
    _name = "mediflow.coverage"
    _description = "Insurance Coverage"
    _inherit = ["mediflow.company.scope.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(string="Policy Reference", compute="_compute_name", store=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True)
    payer_id = fields.Many2one("mediflow.payer", string="Payer", required=True, index=True)
    member_id = fields.Char(string="Member ID", required=True, index=True)
    plan_name = fields.Char(string="Plan")
    relationship = fields.Selection([
        ("self", "Self"),
        ("spouse", "Spouse"),
        ("child", "Child"),
        ("other", "Other"),
    ], string="Relationship to Subscriber", default="self")
    priority = fields.Selection([
        ("primary", "Primary"),
        ("secondary", "Secondary"),
        ("tertiary", "Tertiary"),
    ], string="Priority", default="primary", index=True)
    start_date = fields.Date(string="Effective From")
    end_date = fields.Date(string="Effective To")
    copay_percent = fields.Float(string="Co-pay %", help="Patient share percentage.")
    coverage_percent = fields.Float(string="Coverage %", default=100.0,
                                    help="Payer share percentage of covered charges.")
    is_active = fields.Boolean(string="Active", default=True)

    @api.depends("payer_id", "member_id")
    def _compute_name(self):
        for rec in self:
            payer = rec.payer_id.name or ""
            rec.name = f"{payer} — {rec.member_id}" if rec.member_id else payer
