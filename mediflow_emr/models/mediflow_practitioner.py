# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowPractitioner(models.Model):
    """Clinical staff identity (doctor, nurse, technician). Projects to FHIR
    ``Practitioner`` / ``PractitionerRole``."""

    _name = "mediflow.practitioner"
    _description = "Practitioner"
    _inherit = ["mediflow.company.scope.mixin", "mail.thread"]
    _order = "name"

    name = fields.Char(required=True, index=True, tracking=True)
    user_id = fields.Many2one("res.users", string="Login User", ondelete="set null",
                              index=True, help="System user for this practitioner.")
    partner_id = fields.Many2one("res.partner", string="Contact", ondelete="restrict")
    role = fields.Selection([
        ("doctor", "Doctor"),
        ("nurse", "Nurse"),
        ("lab_tech", "Lab Technician"),
        ("pharmacist", "Pharmacist"),
        ("radiologist", "Radiologist"),
        ("other", "Other"),
    ], default="doctor", required=True, tracking=True)
    specialty_id = fields.Many2one("mediflow.specialty", string="Specialty")
    license_number = fields.Char(string="License No.", tracking=True)
    npi = fields.Char(string="NPI / Registration", help="National Provider Identifier "
                      "or local registration number.")
    active = fields.Boolean(default=True)

    @api.onchange("user_id")
    def _onchange_user_id(self):
        if self.user_id and not self.name:
            self.name = self.user_id.name
            self.partner_id = self.user_id.partner_id


class MediflowSpecialty(models.Model):
    _name = "mediflow.specialty"
    _description = "Clinical Specialty"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)
