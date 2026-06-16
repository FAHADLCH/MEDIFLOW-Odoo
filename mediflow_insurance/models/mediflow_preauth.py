# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowPreauth(models.Model):
    _name = "mediflow.preauth"
    _description = "Pre-Authorization"
    _inherit = [
        "mediflow.company.scope.mixin",
        "mediflow.state.machine.mixin",
        "mediflow.event.mixin",
        "mail.thread",
    ]
    _order = "create_date desc, id desc"

    # ----- State machine -----
    _sm_field = "state"
    _sm_transitions = {
        "requested": ["approved", "denied", "expired"],
    }
    _sm_terminal = {"approved", "denied", "expired"}

    name = fields.Char(string="Pre-Auth #", required=True, copy=False, readonly=True,
                       default="New", index=True, tracking=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True)
    coverage_id = fields.Many2one("mediflow.coverage", string="Coverage", required=True,
                                  index=True)
    payer_id = fields.Many2one("mediflow.payer", related="coverage_id.payer_id",
                               store=True, index=True)
    encounter_id = fields.Many2one("mediflow.encounter", string="Encounter", index=True)
    service_description = fields.Text(string="Requested Services")
    requested_amount = fields.Float(string="Requested Amount")
    approved_amount = fields.Float(string="Approved Amount")
    authorization_number = fields.Char(string="Authorization Number")
    request_date = fields.Date(string="Requested On", default=fields.Date.context_today)
    valid_until = fields.Date(string="Valid Until")
    state = fields.Selection([
        ("requested", "Requested"),
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("expired", "Expired"),
    ], string="Status", default="requested", index=True, tracking=True)
    denial_reason = fields.Char(string="Denial Reason")
    note = fields.Text(string="Notes")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "mediflow.preauth") or "New"
        return super().create(vals_list)

    def action_approve(self):
        for rec in self:
            rec.transition("approved")

    def action_deny(self):
        for rec in self:
            rec.transition("denied", reason=rec.denial_reason)

    @api.model
    def cron_expire(self):
        """Expire approved/requested pre-auths past their validity date."""
        today = fields.Date.context_today(self)
        stale = self.search([
            ("state", "=", "requested"),
            ("valid_until", "!=", False),
            ("valid_until", "<", today),
        ])
        for rec in stale:
            rec.transition("expired", reason="Validity period elapsed")
        return True
