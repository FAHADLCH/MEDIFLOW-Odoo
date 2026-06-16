# -*- coding: utf-8 -*-
from odoo import fields, models


class MediflowProblem(models.Model):
    """Problem / diagnosis list item. Projects to FHIR ``Condition``."""

    _name = "mediflow.problem"
    _description = "Problem / Diagnosis"
    _inherit = ["mediflow.company.scope.mixin", "mediflow.phi.audit.mixin"]
    _order = "onset_date desc, id desc"

    name = fields.Char(string="Problem", required=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True, ondelete="cascade")
    encounter_id = fields.Many2one("mediflow.encounter", string="Encounter",
                                   index=True, ondelete="set null")
    icd_code = fields.Char(string="ICD-10 Code", index=True,
                           help="Diagnosis code for FHIR CodeableConcept output.")
    clinical_status = fields.Selection([
        ("active", "Active"),
        ("recurrence", "Recurrence"),
        ("inactive", "Inactive"),
        ("resolved", "Resolved"),
    ], default="active", required=True)
    severity = fields.Selection([
        ("mild", "Mild"), ("moderate", "Moderate"), ("severe", "Severe"),
    ])
    onset_date = fields.Date(string="Onset")
    abatement_date = fields.Date(string="Resolved On")
    note = fields.Text()
