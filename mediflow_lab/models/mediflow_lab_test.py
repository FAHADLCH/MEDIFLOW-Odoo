# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowLabTest(models.Model):
    _name = "mediflow.lab.test"
    _description = "Lab Test / Analyte"
    _order = "name"

    name = fields.Char(string="Test Name", required=True, index=True)
    code = fields.Char(string="Internal Code", required=True, index=True)
    loinc_code = fields.Char(string="LOINC Code",
                             help="Logical Observation Identifiers Names and Codes "
                             "for FHIR Observation.code.")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", index=True,
        default=lambda self: self.env.company)

    specimen_type = fields.Selection([
        ("blood", "Blood"),
        ("serum", "Serum"),
        ("plasma", "Plasma"),
        ("urine", "Urine"),
        ("stool", "Stool"),
        ("swab", "Swab"),
        ("tissue", "Tissue"),
        ("other", "Other"),
    ], string="Specimen Type", default="blood")
    result_type = fields.Selection([
        ("numeric", "Numeric"),
        ("text", "Text"),
        ("coded", "Coded"),
    ], string="Result Type", default="numeric", required=True)
    uom_name = fields.Char(string="Unit", help="Unit of measure label, e.g. mg/dL.")

    # Reference range (numeric).
    ref_low = fields.Float(string="Reference Low")
    ref_high = fields.Float(string="Reference High")
    # Critical thresholds — breaching these raises lab.critical.flagged.
    critical_low = fields.Float(string="Critical Low")
    critical_high = fields.Float(string="Critical High")

    price = fields.Float(string="List Price")
    tat_hours = fields.Integer(string="Turnaround (hours)", default=24,
                               help="Target turnaround time used by analytics.")

    _sql_constraints = [
        ("code_company_uniq", "unique(code, company_id)",
         "Test code must be unique per company."),
    ]

    @api.depends("name", "code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.code}] {rec.name}" if rec.code else rec.name
