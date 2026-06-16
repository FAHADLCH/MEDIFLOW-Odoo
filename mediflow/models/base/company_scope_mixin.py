# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CompanyScopeMixin(models.AbstractModel):
    """Mandatory multi-clinic scoping. Every PHI/operational model that mixes this
    in gets an indexed, required ``company_id`` defaulting to the active company.

    Record rules (see security XML in each module) build on this field to provide
    the multi-tenant isolation floor across all 100 clinics."""

    _name = "mediflow.company.scope.mixin"
    _description = "MEDIFLOW Company Scope Mixin"

    company_id = fields.Many2one(
        "res.company", string="Clinic", required=True, index=True,
        default=lambda self: self.env.company, ondelete="restrict",
    )

    @api.constrains("company_id")
    def _check_company_id(self):
        for record in self:
            if not record.company_id:
                raise ValidationError(_("A clinic (company) is required on %s.", record._name))
