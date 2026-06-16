# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MediflowAiProvider(models.Model):
    """Connection settings for a Large Language Model provider used by the
    narrative AI features. Predictive features do not require a provider.

    The API key is stored on an admin-restricted field. Only one provider per
    company should be active at a time; ``_get_active`` enforces last-write-wins.
    """

    _name = "mediflow.ai.provider"
    _description = "MEDIFLOW AI Provider"
    _inherit = ["mediflow.company.scope.mixin"]
    _order = "is_active desc, name"

    name = fields.Char(required=True)
    provider_type = fields.Selection([
        ("openai", "OpenAI (chat completions)"),
        ("azure_openai", "Azure OpenAI"),
        ("anthropic", "Anthropic (Claude)"),
        ("ollama", "Local / Ollama (OpenAI-compatible)"),
    ], string="Provider", required=True, default="openai")
    model_name = fields.Char(string="Model", required=True, default="gpt-4o-mini",
                             help="Model/deployment name, e.g. gpt-4o-mini, claude-3-5-sonnet, llama3.1")
    api_base_url = fields.Char(
        string="API Base URL",
        help="Override for self-hosted/Azure endpoints. Leave blank to use the provider default.")
    api_key = fields.Char(
        string="API Key", groups="mediflow_base.group_mediflow_admin",
        help="Secret credential. Visible to administrators only.")
    temperature = fields.Float(default=0.2)
    max_tokens = fields.Integer(string="Max Output Tokens", default=800)
    request_timeout = fields.Integer(string="Timeout (s)", default=30)
    is_active = fields.Boolean(string="Active", default=False)

    @api.onchange("is_active")
    def _onchange_is_active(self):
        if self.is_active:
            return {"warning": {
                "title": _("PHI leaves your system"),
                "message": _(
                    "When active, de-identified clinical context may be sent to this "
                    "provider for narrative features. PHI redaction and patient consent "
                    "checks are always applied. Predictive features remain fully local."),
            }}

    def write(self, vals):
        res = super().write(vals)
        if vals.get("is_active"):
            # Deactivate sibling providers in the same company (single active).
            for provider in self.filtered("is_active"):
                self.search([
                    ("id", "!=", provider.id),
                    ("company_id", "=", provider.company_id.id),
                    ("is_active", "=", True),
                ]).with_context(mf_skip_active_cascade=True).write({"is_active": False})
        return res

    @api.model
    def _get_active(self):
        """Return the active provider for the current company, or empty."""
        return self.search([
            ("is_active", "=", True),
            ("company_id", "in", [self.env.company.id, False]),
        ], order="company_id desc", limit=1)

    def action_test_connection(self):
        self.ensure_one()
        result = self.env["mediflow.ai.service"]._complete_with_provider(
            self, "You are a test probe.", "Reply with the single word: OK.")
        if result.get("ok"):
            message = _("Connection succeeded. Model replied: %s") % (result.get("text") or "")[:120]
            kind = "success"
        else:
            message = _("Connection failed: %s") % (result.get("error") or _("unknown error"))
            kind = "danger"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": _("AI Provider Test"), "message": message,
                       "type": kind, "sticky": False},
        }
