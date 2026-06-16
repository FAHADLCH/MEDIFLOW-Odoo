# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    mediflow_emergency_for_id = fields.Many2one(
        "mediflow.patient", string="Emergency Contact For", ondelete="cascade",
        help="Patient for whom this contact is an emergency contact.")
    mediflow_patient_ids = fields.One2many(
        "mediflow.patient", "partner_id", string="Patient Records")
