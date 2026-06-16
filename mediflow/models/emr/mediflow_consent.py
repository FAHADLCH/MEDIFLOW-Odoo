# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowConsent(models.Model):
    """Patient consent. Gates portal exposure and FHIR export of PHI. Projects to
    FHIR ``Consent``."""

    _name = "mediflow.consent"
    _description = "Consent"
    _inherit = ["mediflow.company.scope.mixin", "mediflow.phi.audit.mixin"]
    _order = "id desc"

    name = fields.Char(string="Reference", compute="_compute_name", store=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True, ondelete="cascade")
    scope = fields.Selection([
        ("treatment", "Treatment"),
        ("data_sharing", "Data Sharing (Portal)"),
        ("research", "Research"),
        ("marketing", "Marketing"),
    ], default="treatment", required=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("active", "Active"),
        ("revoked", "Revoked"),
        ("expired", "Expired"),
    ], default="draft", required=True, index=True)
    granted_date = fields.Date(string="Granted On")
    expiry_date = fields.Date(string="Expires On")
    document_id = fields.Many2one("ir.attachment", string="Signed Document")
    note = fields.Text()

    @api.depends("patient_id", "scope")
    def _compute_name(self):
        for consent in self:
            scope = dict(self._fields["scope"].selection).get(consent.scope, "")
            consent.name = "%s - %s" % (consent.patient_id.name or "", scope)

    def action_activate(self):
        self.write({"state": "active",
                    "granted_date": fields.Date.context_today(self)})

    def action_revoke(self):
        self.write({"state": "revoked"})
