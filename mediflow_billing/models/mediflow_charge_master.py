# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowChargeMaster(models.Model):
    _name = "mediflow.charge.master"
    _description = "Charge Master (Service Catalog)"
    _order = "name"

    name = fields.Char(string="Service", required=True, index=True)
    code = fields.Char(string="Code", required=True, index=True,
                       help="Billing code (CPT/HCPCS/local) for FHIR "
                       "ChargeItemDefinition.")
    category = fields.Selection([
        ("consultation", "Consultation"),
        ("procedure", "Procedure"),
        ("lab", "Laboratory"),
        ("imaging", "Imaging"),
        ("pharmacy", "Pharmacy"),
        ("supply", "Supply"),
        ("other", "Other"),
    ], string="Category", default="consultation", required=True, index=True)
    currency_id = fields.Many2one(
        "res.currency", string="Currency",
        default=lambda self: self.env.company.currency_id,
        help="Pricing currency. Defaults to the clinic's company currency so "
        "MEDIFLOW is fully multi-currency.")
    price = fields.Monetary(string="Unit Price", required=True,
                            currency_field="currency_id")
    product_id = fields.Many2one(
        "product.product", string="Linked Product",
        help="Optional product used on the invoice line for accounting.")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", index=True,
        default=lambda self: self.env.company)

    _sql_constraints = [
        ("code_company_uniq", "unique(code, company_id)",
         "Charge code must be unique per company."),
    ]

    @api.depends("name", "code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.code}] {rec.name}" if rec.code else rec.name
