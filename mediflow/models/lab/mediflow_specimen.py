# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MediflowSpecimen(models.Model):
    _name = "mediflow.specimen"
    _description = "Lab Specimen"
    _inherit = ["mediflow.company.scope.mixin"]
    _order = "collected_at desc, id desc"

    name = fields.Char(string="Accession #", required=True, copy=False,
                       readonly=True, default="New", index=True)
    order_id = fields.Many2one("mediflow.lab.order", string="Lab Order",
                               ondelete="cascade", index=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient",
                                 related="order_id.patient_id", store=True, index=True)
    specimen_type = fields.Selection([
        ("blood", "Blood"),
        ("serum", "Serum"),
        ("plasma", "Plasma"),
        ("urine", "Urine"),
        ("stool", "Stool"),
        ("swab", "Swab"),
        ("tissue", "Tissue"),
        ("other", "Other"),
    ], string="Specimen Type", default="blood", required=True)
    container = fields.Char(string="Container")
    collected_at = fields.Datetime(string="Collected At")
    collected_by_id = fields.Many2one("mediflow.practitioner", string="Collected By")
    received_at = fields.Datetime(string="Received At")
    state = fields.Selection([
        ("collected", "Collected"),
        ("received", "Received"),
        ("rejected", "Rejected"),
    ], string="Status", default="collected", index=True)
    reject_reason = fields.Char(string="Rejection Reason")
    note = fields.Text(string="Notes")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "mediflow.specimen") or "New"
        return super().create(vals_list)
