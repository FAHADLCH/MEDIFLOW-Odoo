# -*- coding: utf-8 -*-
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError


def _tz_get(self):
    return [(tz, tz) for tz in sorted(pytz.all_timezones)]


class MediflowRegionProfile(models.Model):
    """A packaged, applyable regional configuration. Bundles localization
    (language/currency/timezone) with the regulatory framework that governs PHI
    handling for that region. Applying a profile configures the active company
    and publishes compliance parameters used across the platform.
    """

    _name = "mediflow.region.profile"
    _description = "MEDIFLOW Region Profile"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True,
                       help="Stable key, e.g. US, EU, KSA.")
    country_id = fields.Many2one("res.country", string="Country")
    lang = fields.Char(string="Default Language", default="en_US",
                       help="Locale code, e.g. en_US, fr_FR, ar_001.")
    currency_id = fields.Many2one("res.currency", string="Currency")
    timezone = fields.Selection(_tz_get, string="Timezone", default="UTC")

    regulatory_framework = fields.Selection([
        ("hipaa", "HIPAA (United States)"),
        ("gdpr", "GDPR (European Union / EEA)"),
        ("uk_gdpr", "UK GDPR / DPA 2018"),
        ("pdpa", "PDPA (Singapore / Thailand)"),
        ("lgpd", "LGPD (Brazil)"),
        ("pipeda", "PIPEDA (Canada)"),
        ("pdpl", "PDPL (GCC / Saudi Arabia, UAE)"),
        ("dpdp", "DPDP Act (India)"),
        ("generic", "Generic privacy baseline"),
    ], string="Regulatory Framework", required=True, default="generic")

    patient_id_label = fields.Char(string="Patient ID Label", default="National ID",
                                   help="Label shown for the national identifier field.")
    retention_years = fields.Integer(string="PHI Retention (years)", default=10)
    consent_required = fields.Boolean(string="Explicit Consent Required", default=True)
    breach_notification_hours = fields.Integer(
        string="Breach Notification (hours)", default=72,
        help="Maximum window to report a data breach to the regulator.")
    emergency_number = fields.Char(string="Emergency Number")
    phone_country_code = fields.Char(string="Phone Code")
    is_applied = fields.Boolean(string="Applied", readonly=True, copy=False)
    notes = fields.Text()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_uniq", "unique(code)", "Region profile code must be unique."),
    ]

    def action_apply(self):
        """Apply this profile to the current company and publish compliance
        parameters. Idempotent."""
        self.ensure_one()
        company = self.env.company

        # Activate the language if not already enabled.
        if self.lang:
            lang_rec = self.env["res.lang"].with_context(active_test=False).search(
                [("code", "=", self.lang)], limit=1)
            if lang_rec and not lang_rec.active:
                lang_rec.write({"active": True})

        company_vals = {"mediflow_region_profile_id": self.id}
        if self.country_id:
            company_vals["country_id"] = self.country_id.id
        if self.currency_id:
            # Multi-currency is standard in MEDIFLOW: make sure the region's
            # currency is active before it becomes the company currency.
            if not self.currency_id.active:
                self.currency_id.sudo().write({"active": True})
            company_vals["currency_id"] = self.currency_id.id
        company.sudo().write(company_vals)

        # Surface multi-currency features so cross-border billing works at once.
        multi_currency = self.env.ref("base.group_multi_currency",
                                      raise_if_not_found=False)
        if multi_currency:
            multi_currency.sudo().write(
                {"users": [(4, self.env.user.id)]})

        params = self.env["ir.config_parameter"].sudo()
        prefix = "mediflow.region."
        params.set_param(prefix + "code", self.code)
        params.set_param(prefix + "framework", self.regulatory_framework)
        params.set_param(prefix + "patient_id_label", self.patient_id_label or "")
        params.set_param(prefix + "retention_years", str(self.retention_years or 0))
        params.set_param(prefix + "consent_required",
                         "1" if self.consent_required else "0")
        params.set_param(prefix + "breach_hours", str(self.breach_notification_hours or 0))
        params.set_param(prefix + "timezone", self.timezone or "UTC")

        self.search([("is_applied", "=", True)]).write({"is_applied": False})
        self.is_applied = True

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Region applied"),
                "message": _("%(name)s is now the active region for %(co)s.") % {
                    "name": self.name, "co": company.name},
                "type": "success",
                "sticky": False,
            },
        }

    @api.model
    def _get_applied(self):
        return self.search([("is_applied", "=", True)], limit=1)
