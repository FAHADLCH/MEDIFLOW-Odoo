# -*- coding: utf-8 -*-
from odoo import fields, models


class MediflowClinicalDocument(models.Model):
    """Structured clinical note or attachment. Projects to FHIR
    ``DocumentReference``. ``portal_visible`` controls patient portal exposure
    (combined with consent in the portal record rules)."""

    _name = "mediflow.clinical.document"
    _description = "Clinical Document"
    _inherit = ["mediflow.company.scope.mixin", "mediflow.phi.audit.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(string="Title", required=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True, ondelete="cascade")
    encounter_id = fields.Many2one("mediflow.encounter", string="Encounter",
                                   index=True, ondelete="set null")
    doc_type = fields.Selection([
        ("note", "Clinical Note"),
        ("referral", "Referral"),
        ("discharge", "Discharge Summary"),
        ("report", "Report"),
        ("other", "Other"),
    ], default="note", required=True)
    body = fields.Html(string="Content")
    attachment_id = fields.Many2one("ir.attachment", string="Attachment")
    portal_visible = fields.Boolean(string="Visible on Portal", default=False)
    author_id = fields.Many2one("mediflow.practitioner", string="Author")
