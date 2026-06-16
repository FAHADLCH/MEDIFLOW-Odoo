# -*- coding: utf-8 -*-
from odoo import fields, models


class MediflowAllergy(models.Model):
    """Allergy / intolerance. Projects to FHIR ``AllergyIntolerance``. Used by the
    pharmacy interaction/allergy checks."""

    _name = "mediflow.allergy"
    _description = "Allergy / Intolerance"
    _inherit = ["mediflow.company.scope.mixin", "mediflow.phi.audit.mixin"]
    _order = "id desc"

    name = fields.Char(string="Substance", required=True, index=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True, ondelete="cascade")
    category = fields.Selection([
        ("medication", "Medication"),
        ("food", "Food"),
        ("environment", "Environment"),
        ("biologic", "Biologic"),
    ], default="medication", required=True)
    criticality = fields.Selection([
        ("low", "Low"),
        ("high", "High"),
        ("unable", "Unable to Assess"),
    ], default="low")
    reaction = fields.Char(string="Reaction")
    clinical_status = fields.Selection([
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("resolved", "Resolved"),
    ], default="active", required=True)
    substance_code = fields.Char(string="Substance Code",
                                 help="ATC/RxNorm code for interaction checks and FHIR coding.")
    note = fields.Text()
