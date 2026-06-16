# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class MediflowDispense(models.Model):
    _name = "mediflow.dispense"
    _description = "Medication Dispense"
    _inherit = [
        "mediflow.company.scope.mixin",
        "mediflow.phi.audit.mixin",
        "mediflow.state.machine.mixin",
        "mediflow.event.mixin",
        "mail.thread",
    ]
    _order = "create_date desc, id desc"

    # ----- State machine -----
    _sm_field = "state"
    _sm_transitions = {
        "draft": ["confirmed", "cancelled"],
        "confirmed": ["done"],
    }
    _sm_terminal = {"cancelled", "done"}

    name = fields.Char(string="Dispense #", required=True, copy=False, readonly=True,
                       default="New", index=True)
    prescription_id = fields.Many2one("mediflow.prescription", string="Prescription",
                                      required=True, ondelete="cascade", index=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient",
                                 related="prescription_id.patient_id", store=True, index=True)
    dispensed_by_id = fields.Many2one("mediflow.practitioner", string="Dispensed By")
    location_id = fields.Many2one(
        "stock.location", string="Source Location",
        domain="[('usage', '=', 'internal')]")
    dispensed_at = fields.Datetime(string="Dispensed At", readonly=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ], string="Status", default="draft", index=True, tracking=True)
    line_ids = fields.One2many("mediflow.dispense.line", "dispense_id", string="Lines")
    picking_id = fields.Many2one("stock.picking", string="Stock Picking", readonly=True)
    note = fields.Text(string="Notes")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "mediflow.dispense") or "New"
        return super().create(vals_list)

    def _default_source_location(self):
        self.ensure_one()
        if self.location_id:
            return self.location_id
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company_id.id)], limit=1)
        return warehouse.lot_stock_id if warehouse else self.env["stock.location"]

    # ----- Workflow actions -----
    def action_confirm(self):
        """Allocate lots by FEFO; block if expired-only or insufficient stock."""
        Lot = self.env["stock.lot"]
        for disp in self:
            location = disp._default_source_location()
            if not location:
                raise UserError("No internal source location available for dispensing.")
            disp.with_context(sm_internal=True).write({"location_id": location.id})
            for line in disp.line_ids:
                if line.quantity <= 0:
                    raise ValidationError("Dispense quantity must be positive.")
                allocation, remaining = Lot._select_fefo_lot(
                    line.product_id, line.quantity, location=location)
                if remaining > 0:
                    raise UserError(
                        "Insufficient non-expired stock for %s: short by %.2f "
                        "(expired lots are excluded from dispensing)."
                        % (line.product_id.display_name, remaining))
                # Record the chosen (earliest-expiry) lot on the line.
                if allocation:
                    line.with_context(sm_internal=True).write({
                        "lot_id": allocation[0][0].id,
                        "lot_allocation": ", ".join(
                            "%s:%.2f" % (lot.name, qty) for lot, qty in allocation),
                    })
            disp.transition("confirmed")

    def action_done(self):
        """Create and validate the outgoing stock move, then emit pharmacy.dispensed."""
        for disp in self:
            disp._create_stock_move()
            disp.with_context(sm_internal=True).write(
                {"dispensed_at": fields.Datetime.now()})
            disp.transition("done")
            disp._emit_event("pharmacy.dispensed", {
                "dispense_id": disp.id,
                "prescription_id": disp.prescription_id.id,
                "patient_id": disp.patient_id.id,
                "lines": [{
                    "product_id": l.product_id.id,
                    "quantity": l.quantity,
                } for l in disp.line_ids],
            })
            disp.prescription_id._sync_dispensed_state()

    def _create_stock_move(self):
        """Issue stock from the source location to the customer location."""
        self.ensure_one()
        source = self.location_id or self._default_source_location()
        customer_loc = self.env.ref("stock.stock_location_customers",
                                    raise_if_not_found=False)
        if not source or not customer_loc:
            return
        picking_type = self.env["stock.picking.type"].search([
            ("code", "=", "outgoing"),
            ("warehouse_id.company_id", "=", self.company_id.id),
        ], limit=1)
        if not picking_type:
            return
        picking = self.env["stock.picking"].create({
            "picking_type_id": picking_type.id,
            "location_id": source.id,
            "location_dest_id": customer_loc.id,
            "origin": self.name,
            "company_id": self.company_id.id,
        })
        for line in self.line_ids:
            move = self.env["stock.move"].create({
                "name": line.product_id.display_name,
                "product_id": line.product_id.id,
                "product_uom_qty": line.quantity,
                "product_uom": line.product_id.uom_id.id,
                "picking_id": picking.id,
                "location_id": source.id,
                "location_dest_id": customer_loc.id,
                "company_id": self.company_id.id,
            })
            if line.lot_id:
                move.move_line_ids = [(0, 0, {
                    "product_id": line.product_id.id,
                    "lot_id": line.lot_id.id,
                    "quantity": line.quantity,
                    "product_uom_id": line.product_id.uom_id.id,
                    "location_id": source.id,
                    "location_dest_id": customer_loc.id,
                })]
        picking.action_confirm()
        picking.button_validate()
        self.with_context(sm_internal=True).write({"picking_id": picking.id})

    def action_cancel(self):
        for disp in self:
            disp.transition("cancelled")


class MediflowDispenseLine(models.Model):
    _name = "mediflow.dispense.line"
    _description = "Dispense Line"
    _order = "dispense_id, id"

    dispense_id = fields.Many2one("mediflow.dispense", string="Dispense",
                                  required=True, ondelete="cascade", index=True)
    product_id = fields.Many2one(
        "product.product", string="Medication", required=True,
        domain="[('is_medication', '=', True)]")
    quantity = fields.Float(string="Quantity", default=1.0, required=True)
    lot_id = fields.Many2one("stock.lot", string="Lot (FEFO)", readonly=True)
    lot_allocation = fields.Char(string="Lot Allocation", readonly=True)
