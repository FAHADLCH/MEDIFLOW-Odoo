# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowPayer(models.Model):
    _name = "mediflow.payer"
    _description = "Insurance Payer (Organization)"
    _order = "name"

    name = fields.Char(string="Payer Name", required=True, index=True)
    code = fields.Char(string="Payer Code", required=True, index=True)
    partner_id = fields.Many2one("res.partner", string="Billing Contact",
                                 help="Accounting partner used when posting payer "
                                 "payments.")
    payer_type = fields.Selection([
        ("private", "Private Insurer"),
        ("government", "Government Scheme"),
        ("corporate", "Corporate / TPA"),
        ("self", "Self-pay"),
    ], string="Type", default="private", required=True, index=True)
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    claim_address = fields.Text(string="Claims Address")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", index=True,
        default=lambda self: self.env.company)
    coverage_ids = fields.One2many("mediflow.coverage", "payer_id", string="Coverages")

    _sql_constraints = [
        ("code_company_uniq", "unique(code, company_id)",
         "Payer code must be unique per company."),
    ]
