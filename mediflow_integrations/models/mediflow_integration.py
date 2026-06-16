# -*- coding: utf-8 -*-
import secrets

from odoo import api, fields, models, _


class MediflowIntegration(models.Model):
    """A configured external connector. One active integration per type per
    company is used by the dispatcher service. Credentials are stored on
    admin-restricted fields and never logged."""

    _name = "mediflow.integration"
    _description = "MEDIFLOW Integration"
    _inherit = ["mediflow.company.scope.mixin"]
    _order = "integration_type, name"

    name = fields.Char(required=True)
    integration_type = fields.Selection([
        ("payment_stripe", "Payments — Stripe"),
        ("sms_twilio", "SMS — Twilio"),
        ("whatsapp_twilio", "WhatsApp — Twilio"),
        ("telehealth", "Telehealth — Video Rooms"),
        ("hl7_lab", "Lab / HL7 Inbound"),
        ("eprescribe", "e-Prescribing Network"),
        ("clearinghouse", "Insurance Clearinghouse"),
        ("accounting", "Accounting Export"),
        ("calendar", "Calendar Sync"),
    ], string="Type", required=True)
    is_active = fields.Boolean(string="Active", default=False)
    base_url = fields.Char(string="Base URL")
    auth_token = fields.Char(string="API Key / SID",
                             groups="mediflow_base.group_mediflow_admin")
    auth_secret = fields.Char(string="API Secret / Token",
                              groups="mediflow_base.group_mediflow_admin")
    from_identifier = fields.Char(
        string="Sender / From",
        help="e.g. Twilio sender number, Stripe account, FHIR endpoint id.")
    inbound_token = fields.Char(
        string="Inbound Token", copy=False,
        help="Bearer token external systems present to the inbound endpoint.")
    last_used = fields.Datetime(string="Last Used", readonly=True)
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("integration_type") == "hl7_lab" and not vals.get("inbound_token"):
                vals["inbound_token"] = secrets.token_urlsafe(24)
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if vals.get("is_active"):
            for integ in self.filtered("is_active"):
                self.search([
                    ("id", "!=", integ.id),
                    ("integration_type", "=", integ.integration_type),
                    ("company_id", "=", integ.company_id.id),
                    ("is_active", "=", True),
                ]).write({"is_active": False})
        return res

    @api.model
    def _get_active(self, integration_type):
        return self.search([
            ("integration_type", "=", integration_type),
            ("is_active", "=", True),
            ("company_id", "in", [self.env.company.id, False]),
        ], order="company_id desc", limit=1)

    def action_regenerate_inbound_token(self):
        self.ensure_one()
        self.inbound_token = secrets.token_urlsafe(24)

    def action_test_connection(self):
        self.ensure_one()
        ok = self.env["mediflow.integration.service"]._ping(self)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Integration Test"),
                "message": _("Reachable.") if ok else _("Not reachable / not configured."),
                "type": "success" if ok else "warning",
                "sticky": False,
            },
        }
