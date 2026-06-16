# -*- coding: utf-8 -*-
from odoo import fields, models


class MediflowImmunization(models.Model):
    """Vaccination record. Projects to FHIR ``Immunization``."""

    _name = "mediflow.immunization"
    _description = "Immunization"
    _inherit = ["mediflow.company.scope.mixin", "mediflow.phi.audit.mixin"]
    _order = "administered_date desc, id desc"

    name = fields.Char(string="Vaccine", required=True, index=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True, ondelete="cascade")
    vaccine_code = fields.Char(string="Vaccine Code", help="CVX/SNOMED for FHIR coding.")
    administered_date = fields.Date(string="Date Administered", index=True)
    dose_number = fields.Integer(string="Dose #")
    lot_number = fields.Char(string="Lot No.")
    administered_by_id = fields.Many2one("mediflow.practitioner", string="Administered By")
    status = fields.Selection([
        ("completed", "Completed"),
        ("not_done", "Not Done"),
        ("entered_in_error", "Entered in Error"),
    ], default="completed", required=True)
    note = fields.Text()
