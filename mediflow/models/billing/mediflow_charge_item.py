# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowChargeItem(models.Model):
    _name = "mediflow.charge.item"
    _description = "Charge Item (ChargeItem)"
    _inherit = [
        "mediflow.company.scope.mixin",
        "mediflow.state.machine.mixin",
        "mediflow.event.mixin",
    ]
    _order = "create_date desc, id desc"

    # ----- State machine -----
    _sm_field = "state"
    _sm_transitions = {
        "draft": ["billed", "cancelled"],
        "billed": ["cancelled"],
    }
    _sm_terminal = {"cancelled"}

    name = fields.Char(string="Description", required=True, index=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True)
    encounter_id = fields.Many2one("mediflow.encounter", string="Encounter", index=True)
    charge_master_id = fields.Many2one("mediflow.charge.master", string="Service")
    category = fields.Selection([
        ("consultation", "Consultation"),
        ("procedure", "Procedure"),
        ("lab", "Laboratory"),
        ("imaging", "Imaging"),
        ("pharmacy", "Pharmacy"),
        ("supply", "Supply"),
        ("other", "Other"),
    ], string="Category", default="consultation", required=True, index=True)
    quantity = fields.Float(string="Quantity", default=1.0, required=True)
    unit_price = fields.Float(string="Unit Price", required=True)
    amount = fields.Float(string="Amount", compute="_compute_amount", store=True)
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", store=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("billed", "Billed"),
        ("cancelled", "Cancelled"),
    ], string="Status", default="draft", index=True)

    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True, index=True)
    invoice_line_id = fields.Many2one("account.move.line", string="Invoice Line",
                                      readonly=True)

    # Source traceability (set by the capturing module).
    source_model = fields.Char(string="Source Model", index=True)
    source_res_id = fields.Integer(string="Source Record")

    @api.depends("quantity", "unit_price")
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.quantity * rec.unit_price

    @api.onchange("charge_master_id")
    def _onchange_charge_master(self):
        if self.charge_master_id:
            self.name = self.charge_master_id.name
            self.unit_price = self.charge_master_id.price
            self.category = self.charge_master_id.category

    @api.model
    def capture(self, patient, name, unit_price, category="other", quantity=1.0,
                encounter=None, source_model=None, source_res_id=None,
                charge_master=None, company=None):
        """Programmatic charge-capture entry point used by lab/pharmacy/encounter."""
        company = company or (encounter.company_id if encounter else self.env.company)
        return self.create({
            "name": name,
            "patient_id": patient.id,
            "encounter_id": encounter.id if encounter else False,
            "category": category,
            "quantity": quantity,
            "unit_price": unit_price,
            "company_id": company.id,
            "source_model": source_model,
            "source_res_id": source_res_id,
            "charge_master_id": charge_master.id if charge_master else False,
        })

    def action_cancel(self):
        for rec in self:
            rec.transition("cancelled")
