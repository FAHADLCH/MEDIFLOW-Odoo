# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class MediflowClaim(models.Model):
    _name = "mediflow.claim"
    _description = "Insurance Claim"
    _inherit = [
        "mediflow.company.scope.mixin",
        "mediflow.state.machine.mixin",
        "mediflow.event.mixin",
        "mail.thread",
        "mail.activity.mixin",
    ]
    _order = "create_date desc, id desc"

    # ----- State machine -----
    _sm_field = "state"
    _sm_transitions = {
        "draft": ["submitted"],
        "submitted": ["adjudicated"],
        "adjudicated": ["paid", "denied"],
        "denied": ["appealed"],
        "appealed": ["submitted"],
    }
    _sm_terminal = {"paid"}

    name = fields.Char(string="Claim #", required=True, copy=False, readonly=True,
                       default="New", index=True, tracking=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True)
    coverage_id = fields.Many2one("mediflow.coverage", string="Coverage", required=True,
                                  index=True)
    payer_id = fields.Many2one("mediflow.payer", related="coverage_id.payer_id",
                               store=True, index=True)
    invoice_id = fields.Many2one("account.move", string="Invoice", index=True,
                                 domain="[('is_mediflow_invoice', '=', True)]")
    encounter_id = fields.Many2one("mediflow.encounter", string="Encounter", index=True)
    preauth_id = fields.Many2one("mediflow.preauth", string="Pre-Authorization")

    state = fields.Selection([
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("adjudicated", "Adjudicated"),
        ("paid", "Paid"),
        ("denied", "Denied"),
        ("appealed", "Appealed"),
    ], string="Status", default="draft", index=True, tracking=True,
        group_expand="_expand_states")

    line_ids = fields.One2many("mediflow.claim.line", "claim_id", string="Claim Lines")
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", store=True)
    claimed_amount = fields.Monetary(string="Claimed", compute="_compute_amounts",
                                     store=True)
    approved_amount = fields.Monetary(string="Approved", compute="_compute_amounts",
                                      store=True)
    patient_responsibility = fields.Monetary(string="Patient Responsibility",
                                             compute="_compute_amounts", store=True)

    submission_date = fields.Date(string="Submitted On")
    adjudication_date = fields.Date(string="Adjudicated On")
    denial_code = fields.Char(string="Denial Code")
    denial_reason = fields.Char(string="Denial Reason")
    note = fields.Text(string="Notes")

    @api.model
    def _expand_states(self, states, domain):
        return [k for k, _ in type(self).state.selection]

    @api.depends("line_ids.charged_amount", "line_ids.approved_amount")
    def _compute_amounts(self):
        for claim in self:
            claimed = sum(claim.line_ids.mapped("charged_amount"))
            approved = sum(claim.line_ids.mapped("approved_amount"))
            claim.claimed_amount = claimed
            claim.approved_amount = approved
            claim.patient_responsibility = max(claimed - approved, 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "mediflow.claim") or "New"
        return super().create(vals_list)

    # ----- Helpers -----
    def action_pull_invoice_lines(self):
        """Populate claim lines from the linked invoice, applying coverage %."""
        self.ensure_one()
        if not self.invoice_id:
            raise UserError("Link an invoice before pulling lines.")
        self.line_ids.unlink()
        coverage_pct = (self.coverage_id.coverage_percent or 100.0) / 100.0
        line_vals = []
        for inv_line in self.invoice_id.invoice_line_ids.filtered(
                lambda l: l.display_type == "product"):
            charged = inv_line.price_subtotal
            line_vals.append((0, 0, {
                "name": inv_line.name or inv_line.product_id.display_name,
                "charged_amount": charged,
                "approved_amount": charged * coverage_pct,
                "invoice_line_id": inv_line.id,
            }))
        self.line_ids = line_vals

    # ----- Workflow actions -----
    def action_submit(self):
        for claim in self:
            if not claim.line_ids:
                raise ValidationError("Add at least one claim line before submitting.")
            claim.with_context(sm_internal=True).write(
                {"submission_date": fields.Date.context_today(claim)})
            claim.transition("submitted")
            claim._emit_event("claim.submitted", {
                "claim_id": claim.id,
                "patient_id": claim.patient_id.id,
                "payer_id": claim.payer_id.id,
                "claimed_amount": claim.claimed_amount,
            })

    def action_adjudicate(self):
        for claim in self:
            claim.with_context(sm_internal=True).write(
                {"adjudication_date": fields.Date.context_today(claim)})
            claim.transition("adjudicated")
            claim._recompute_patient_balance()
            claim._emit_event("claim.adjudicated", {
                "claim_id": claim.id,
                "patient_id": claim.patient_id.id,
                "approved_amount": claim.approved_amount,
                "patient_responsibility": claim.patient_responsibility,
            })

    def action_mark_paid(self):
        for claim in self:
            claim.transition("paid")

    def action_deny(self):
        for claim in self:
            claim.transition("denied", reason=claim.denial_reason)
            claim._emit_event("claim.denied", {
                "claim_id": claim.id,
                "patient_id": claim.patient_id.id,
                "denial_code": claim.denial_code,
                "denial_reason": claim.denial_reason,
            })

    def action_appeal(self):
        for claim in self:
            claim.transition("appealed")

    def _recompute_patient_balance(self):
        """Record the patient-responsibility figure on the linked invoice for
        downstream balance reporting. Money stays on account.move."""
        for claim in self:
            if claim.invoice_id and "mediflow_patient_responsibility" in \
                    claim.invoice_id._fields:
                claim.invoice_id.sudo().write({
                    "mediflow_patient_responsibility": claim.patient_responsibility,
                })


class MediflowClaimLine(models.Model):
    _name = "mediflow.claim.line"
    _description = "Claim Line"
    _order = "claim_id, id"

    claim_id = fields.Many2one("mediflow.claim", string="Claim", required=True,
                               ondelete="cascade", index=True)
    name = fields.Char(string="Service", required=True)
    invoice_line_id = fields.Many2one("account.move.line", string="Invoice Line")
    charged_amount = fields.Float(string="Charged", required=True)
    approved_amount = fields.Float(string="Approved")
    denied_amount = fields.Float(string="Denied", compute="_compute_denied", store=True)
    adjustment_code = fields.Char(string="Adjustment Code")

    @api.depends("charged_amount", "approved_amount")
    def _compute_denied(self):
        for line in self:
            line.denied_amount = max(line.charged_amount - line.approved_amount, 0.0)
