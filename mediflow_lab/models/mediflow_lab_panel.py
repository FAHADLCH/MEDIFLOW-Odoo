# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowLabPanel(models.Model):
    _name = "mediflow.lab.panel"
    _description = "Lab Panel"
    _order = "name"

    name = fields.Char(string="Panel Name", required=True, index=True)
    code = fields.Char(string="Code", required=True, index=True)
    loinc_code = fields.Char(string="LOINC Code")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", index=True,
        default=lambda self: self.env.company)
    test_ids = fields.Many2many(
        "mediflow.lab.test", "mediflow_lab_panel_test_rel",
        "panel_id", "test_id", string="Tests")
    test_count = fields.Integer(string="Test Count", compute="_compute_test_count")
    price = fields.Float(string="List Price")

    _sql_constraints = [
        ("code_company_uniq", "unique(code, company_id)",
         "Panel code must be unique per company."),
    ]

    @api.depends("test_ids")
    def _compute_test_count(self):
        for rec in self:
            rec.test_count = len(rec.test_ids)
