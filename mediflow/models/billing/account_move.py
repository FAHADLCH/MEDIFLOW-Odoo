# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    mediflow_patient_id = fields.Many2one("mediflow.patient", string="Patient", index=True)
    mediflow_encounter_id = fields.Many2one("mediflow.encounter", string="Encounter",
                                            index=True)
    mediflow_charge_item_ids = fields.One2many(
        "mediflow.charge.item", "invoice_id", string="Charge Items")
    is_mediflow_invoice = fields.Boolean(string="MEDIFLOW Invoice", default=False)
    mediflow_patient_responsibility = fields.Monetary(
        string="Patient Responsibility", default=0.0,
        help="Patient out-of-pocket amount after insurance adjudication.")

    @api.model
    def _mediflow_income_account(self, company):
        account = self.env["account.account"].search([
            ("account_type", "=", "income"),
            ("company_ids", "in", company.id),
        ], limit=1)
        return account

    @api.model
    def create_from_charges(self, patient, charges, encounter=None):
        """Aggregate draft charge items into a single customer invoice and mark them
        billed. Returns the created ``account.move``."""
        charges = charges.filtered(lambda c: c.state == "draft")
        if not charges:
            raise UserError("There are no draft charges to invoice.")
        company = encounter.company_id if encounter else patient.company_id
        partner = patient.partner_id
        if not partner:
            raise UserError(
                "Patient %s has no linked contact for invoicing." % patient.display_name)
        income_account = self._mediflow_income_account(company)
        line_vals = []
        for charge in charges:
            vals = {
                "name": charge.name,
                "quantity": charge.quantity,
                "price_unit": charge.unit_price,
            }
            if charge.charge_master_id.product_id:
                vals["product_id"] = charge.charge_master_id.product_id.id
            elif income_account:
                vals["account_id"] = income_account.id
            line_vals.append((0, 0, vals))
        invoice = self.with_company(company).create({
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "company_id": company.id,
            "is_mediflow_invoice": True,
            "mediflow_patient_id": patient.id,
            "mediflow_encounter_id": encounter.id if encounter else False,
            "invoice_line_ids": line_vals,
        })
        # Link charges to invoice lines and flip them to billed.
        for charge, line in zip(charges, invoice.invoice_line_ids):
            charge.with_context(sm_internal=True).write({
                "invoice_id": invoice.id,
                "invoice_line_id": line.id,
            })
            charge.transition("billed")
        return invoice

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted:
            if move.is_mediflow_invoice and hasattr(move, "_emit_event"):
                move._emit_event("invoice.posted", {
                    "move_id": move.id,
                    "patient_id": move.mediflow_patient_id.id,
                    "amount_total": move.amount_total,
                })
        return posted

    def _emit_event(self, name, payload=None, version="1"):
        """Bridge to the durable event store + bus without inheriting EventMixin on
        account.move (keeps the accounting model lean)."""
        company_id = self.company_id.id if self.company_id else self.env.company.id
        event = self.env["mediflow.event"].sudo().create({
            "name": name,
            "version": version,
            "payload": payload or {},
            "source_model": self._name,
            "source_res_id": self.id,
            "company_id": company_id,
        })
        event.emit()
        return event


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payments(self):
        payments = super()._create_payments()
        for payment in payments:
            moves = payment.reconciled_invoice_ids
            for move in moves.filtered(lambda m: m.is_mediflow_invoice):
                move._emit_event("payment.received", {
                    "move_id": move.id,
                    "patient_id": move.mediflow_patient_id.id,
                    "amount": payment.amount,
                })
        return payments
