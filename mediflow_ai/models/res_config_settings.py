# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mf_ai_active_provider_id = fields.Many2one(
        "mediflow.ai.provider", string="Active AI Provider",
        compute="_compute_mf_ai_active_provider")
    mf_ai_narrative_enabled = fields.Boolean(
        string="Enable narrative AI (summaries, explanations)",
        config_parameter="mediflow_ai.narrative_enabled", default=True)
    mf_ai_patient_explanations = fields.Boolean(
        string="Allow patient-facing result explanations",
        config_parameter="mediflow_ai.patient_explanations", default=True)

    @api.depends_context("company")
    def _compute_mf_ai_active_provider(self):
        provider = self.env["mediflow.ai.provider"]._get_active()
        for rec in self:
            rec.mf_ai_active_provider_id = provider

    def action_mf_open_ai_providers(self):
        return {
            "type": "ir.actions.act_window",
            "name": "AI Providers",
            "res_model": "mediflow.ai.provider",
            "view_mode": "list,form",
        }
