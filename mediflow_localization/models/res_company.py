# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    mediflow_region_profile_id = fields.Many2one(
        "mediflow.region.profile", string="MEDIFLOW Region",
        help="Active regional/regulatory profile applied to this clinic company.")
