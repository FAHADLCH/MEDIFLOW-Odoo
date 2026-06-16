# -*- coding: utf-8 -*-
from odoo import fields, models


class MediflowAiRequest(models.Model):
    """Append-only audit trail of every AI call: which feature, which user,
    whether PHI redaction and consent checks were applied, and the outcome.

    Prompts/responses are stored truncated and de-identified so the log itself
    never becomes a new PHI store.
    """

    _name = "mediflow.ai.request"
    _description = "MEDIFLOW AI Request Log"
    _inherit = ["mediflow.company.scope.mixin"]
    _order = "create_date desc, id desc"

    feature = fields.Char(string="Feature", required=True, index=True)
    provider_id = fields.Many2one("mediflow.ai.provider", string="Provider",
                                  ondelete="set null")
    model_name = fields.Char(string="Model")
    user_id = fields.Many2one("res.users", string="Requested By",
                              default=lambda self: self.env.user, index=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", index=True,
                                 ondelete="set null")
    status = fields.Selection([
        ("ok", "Success"),
        ("fallback", "Local Fallback"),
        ("blocked", "Blocked (no consent)"),
        ("error", "Error"),
    ], required=True, default="ok", index=True)
    redacted = fields.Boolean(string="PHI Redacted")
    prompt_excerpt = fields.Text(string="Prompt (de-identified excerpt)")
    response_excerpt = fields.Text(string="Response (excerpt)")
    error_message = fields.Char(string="Error")
    duration_ms = fields.Integer(string="Duration (ms)")
