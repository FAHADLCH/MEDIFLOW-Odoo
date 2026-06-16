# -*- coding: utf-8 -*-
import hashlib
import secrets

from odoo import api, fields, models
from odoo.exceptions import UserError


class MediflowFhirToken(models.Model):
    """Opaque bearer token for the FHIR API. The raw secret is shown exactly once
    at creation and never stored; only its SHA-256 hash is persisted, so a database
    leak cannot reveal usable tokens. Each token is bound to a service user (whose
    company access and record rules govern what the API can see), an optional scope
    string, and an expiry."""

    _name = "mediflow.fhir.token"
    _description = "FHIR API Token"
    _order = "create_date desc"

    name = fields.Char(string="Label", required=True)
    user_id = fields.Many2one(
        "res.users", string="Service User", required=True, ondelete="cascade",
        help="API calls run with this user's access rights and company scope.")
    token_hash = fields.Char(string="Token Hash", readonly=True, copy=False, index=True)
    scope = fields.Char(
        string="Scopes", default="patient/*.read",
        help="Space-separated SMART-style scopes. Read-only in this phase.")
    expires_at = fields.Datetime(string="Expires At")
    active = fields.Boolean(default=True)
    last_used_at = fields.Datetime(string="Last Used", readonly=True)

    # Transient display of the freshly minted secret (never persisted).
    token_plain = fields.Char(string="Token (copy now)", store=False, readonly=True)

    @staticmethod
    def _hash(raw):
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def action_generate(self):
        """(Re)generate the secret for this token. Returns nothing persistent; the
        plaintext is held only on the in-memory record for the form to display."""
        self.ensure_one()
        raw = secrets.token_urlsafe(32)
        self.write({"token_hash": self._hash(raw)})
        # token_plain is non-stored: assignment stays on the record in this request.
        self.token_plain = raw
        return {
            "type": "ir.actions.act_window",
            "res_model": "mediflow.fhir.token",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.model_create_multi
    def create(self, vals_list):
        tokens = super().create(vals_list)
        for token in tokens:
            if not token.token_hash:
                token.action_generate()
        return tokens

    @api.model
    def _authenticate(self, raw_token):
        """Resolve a raw bearer token to its (valid, non-expired, active) record or
        None. Updates last_used_at on success. Constant work regardless of match to
        avoid trivial timing oracles on token existence."""
        if not raw_token:
            return None
        digest = self._hash(raw_token)
        token = self.sudo().search([
            ("token_hash", "=", digest),
            ("active", "=", True),
        ], limit=1)
        if not token:
            return None
        if token.expires_at and token.expires_at < fields.Datetime.now():
            return None
        token.sudo().write({"last_used_at": fields.Datetime.now()})
        return token

    def action_revoke(self):
        self.write({"active": False})

    def write(self, vals):
        # Guard against silently overwriting a hash with a blank value.
        if "token_hash" in vals and not vals["token_hash"]:
            raise UserError("Token hash cannot be cleared.")
        return super().write(vals)
