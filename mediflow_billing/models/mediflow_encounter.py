# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class MediflowEncounter(models.Model):
    _inherit = "mediflow.encounter"

    charge_item_ids = fields.One2many(
        "mediflow.charge.item", "encounter_id", string="Charges")
    charge_total = fields.Float(string="Charge Total", compute="_compute_charge_total")
    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True,
                                 copy=False, index=True)
    invoice_count = fields.Integer(compute="_compute_invoice_count")

    @api.depends("charge_item_ids.amount", "charge_item_ids.state")
    def _compute_charge_total(self):
        for rec in self:
            rec.charge_total = sum(
                rec.charge_item_ids.filtered(lambda c: c.state != "cancelled").mapped(
                    "amount"))

    @api.depends("invoice_id")
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = 1 if rec.invoice_id else 0

    def action_add_consultation_charge(self):
        """Capture a default consultation charge for this encounter."""
        self.ensure_one()
        master = self.env["mediflow.charge.master"].search([
            ("category", "=", "consultation"),
            ("company_id", "in", (self.company_id.id, False)),
        ], limit=1)
        self.env["mediflow.charge.item"].capture(
            patient=self.patient_id,
            name=master.name if master else "Consultation",
            unit_price=master.price if master else 0.0,
            category="consultation",
            encounter=self,
            source_model=self._name,
            source_res_id=self.id,
            charge_master=master or None,
        )

    def action_create_invoice(self):
        self.ensure_one()
        draft_charges = self.charge_item_ids.filtered(lambda c: c.state == "draft")
        if not draft_charges:
            raise UserError("Capture at least one charge before invoicing.")
        invoice = self.env["account.move"].create_from_charges(
            patient=self.patient_id, charges=draft_charges, encounter=self)
        self.invoice_id = invoice.id
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError("No invoice has been created for this encounter.")
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.invoice_id.id,
            "view_mode": "form",
            "target": "current",
        }
