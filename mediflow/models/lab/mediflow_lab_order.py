# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MediflowLabOrder(models.Model):
    _name = "mediflow.lab.order"
    _description = "Lab Order"
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
        "ordered": ["collected", "cancelled"],
        "collected": ["received"],
        "received": ["in_process"],
        "in_process": ["resulted"],
        "resulted": ["completed"],
    }
    _sm_terminal = {"cancelled", "completed"}

    name = fields.Char(string="Order #", required=True, copy=False, readonly=True,
                       default="New", index=True, tracking=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True, tracking=True)
    encounter_id = fields.Many2one("mediflow.encounter", string="Encounter", index=True)
    practitioner_id = fields.Many2one("mediflow.practitioner", string="Ordering Provider",
                                      tracking=True)
    priority = fields.Selection([
        ("routine", "Routine"),
        ("urgent", "Urgent"),
        ("stat", "STAT"),
    ], string="Priority", default="routine", index=True, tracking=True)
    order_date = fields.Datetime(string="Ordered On", default=fields.Datetime.now)
    state = fields.Selection([
        ("ordered", "Ordered"),
        ("collected", "Collected"),
        ("received", "Received"),
        ("in_process", "In Process"),
        ("resulted", "Resulted"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ], string="Status", default="ordered", index=True, tracking=True,
        group_expand="_expand_states")

    test_ids = fields.Many2many(
        "mediflow.lab.test", "mediflow_lab_order_test_rel",
        "order_id", "test_id", string="Tests")
    panel_ids = fields.Many2many(
        "mediflow.lab.panel", "mediflow_lab_order_panel_rel",
        "order_id", "panel_id", string="Panels")
    specimen_ids = fields.One2many("mediflow.specimen", "order_id", string="Specimens")
    result_ids = fields.One2many("mediflow.lab.result", "order_id", string="Results")
    result_count = fields.Integer(compute="_compute_result_count")
    cancel_reason = fields.Char(string="Cancellation Reason")
    note = fields.Text(string="Clinical Notes")

    @api.model
    def _expand_states(self, states, domain):
        return [k for k, _ in type(self).state.selection]

    @api.depends("result_ids")
    def _compute_result_count(self):
        for rec in self:
            rec.result_count = len(rec.result_ids)

    @api.constrains("test_ids", "panel_ids")
    def _check_has_tests(self):
        for rec in self:
            if rec.state != "ordered":
                continue
            if not rec.test_ids and not rec.panel_ids:
                raise ValidationError("A lab order must include at least one test or panel.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "mediflow.lab.order") or "New"
        orders = super().create(vals_list)
        for order in orders:
            order._emit_event("lab.order.created", {
                "order_id": order.id,
                "patient_id": order.patient_id.id,
                "priority": order.priority,
            })
        return orders

    def _all_panel_tests(self):
        """Flatten panel tests + direct tests into a unique set of test records."""
        self.ensure_one()
        tests = self.test_ids
        for panel in self.panel_ids:
            tests |= panel.test_ids
        return tests

    # ----- Workflow actions -----
    def action_collect(self):
        for order in self:
            if not order.specimen_ids:
                self.env["mediflow.specimen"].create({
                    "order_id": order.id,
                    "company_id": order.company_id.id,
                    "collected_at": fields.Datetime.now(),
                })
            else:
                order.specimen_ids.filtered(lambda s: not s.collected_at).write(
                    {"collected_at": fields.Datetime.now()})
            order.transition("collected")

    def action_receive(self):
        for order in self:
            order.specimen_ids.filtered(lambda s: s.state == "collected").write({
                "state": "received",
                "received_at": fields.Datetime.now(),
            })
            order.transition("received")

    def action_start_process(self):
        for order in self:
            order.transition("in_process")
            # Pre-create preliminary result rows for each ordered test.
            existing = order.result_ids.mapped("test_id")
            for test in order._all_panel_tests():
                if test in existing:
                    continue
                self.env["mediflow.lab.result"].create({
                    "order_id": order.id,
                    "company_id": order.company_id.id,
                    "test_id": test.id,
                })

    def action_mark_resulted(self):
        for order in self:
            order.transition("resulted")

    def action_complete(self):
        for order in self:
            pending = order.result_ids.filtered(lambda r: r.state != "released")
            if pending:
                raise ValidationError(
                    "All results must be released before completing the order.")
            order.transition("completed")

    def action_cancel(self):
        for order in self:
            order.transition("cancelled", reason=order.cancel_reason)
