# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mf_region_profile_id = fields.Many2one(
        "mediflow.region.profile", string="Active Region",
        related="company_id.mediflow_region_profile_id", readonly=False)
    mf_region_framework = fields.Char(
        string="Regulatory Framework", compute="_compute_mf_region_framework")
    group_multi_currency = fields.Boolean(
        string="Multi-Currency", implied_group="base.group_multi_currency")

    @api.depends("mf_region_profile_id")
    def _compute_mf_region_framework(self):
        for rec in self:
            profile = rec.mf_region_profile_id
            rec.mf_region_framework = (
                dict(profile._fields["regulatory_framework"].selection).get(
                    profile.regulatory_framework) if profile else "")

    def action_mf_apply_region(self):
        self.ensure_one()
        if self.mf_region_profile_id:
            return self.mf_region_profile_id.action_apply()

    def action_mf_open_regions(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Region Profiles",
            "res_model": "mediflow.region.profile",
            "view_mode": "list,form",
        }
