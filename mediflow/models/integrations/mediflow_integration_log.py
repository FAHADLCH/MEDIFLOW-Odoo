# -*- coding: utf-8 -*-
from odoo import fields, models


class MediflowIntegrationLog(models.Model):
    """Append-only record of every integration call (inbound and outbound)."""

    _name = "mediflow.integration.log"
    _description = "MEDIFLOW Integration Log"
    _inherit = ["mediflow.company.scope.mixin"]
    _order = "create_date desc, id desc"

    integration_id = fields.Many2one("mediflow.integration", string="Integration",
                                     ondelete="set null", index=True)
    integration_type = fields.Char(string="Type", index=True)
    direction = fields.Selection([
        ("outbound", "Outbound"),
        ("inbound", "Inbound"),
    ], required=True, default="outbound")
    channel = fields.Char(string="Channel")
    reference = fields.Char(string="Reference")
    patient_id = fields.Many2one("mediflow.patient", string="Patient",
                                 ondelete="set null", index=True)
    status = fields.Selection([
        ("ok", "Success"),
        ("error", "Error"),
        ("skipped", "Skipped"),
    ], required=True, default="ok", index=True)
    request_excerpt = fields.Text(string="Request")
    response_excerpt = fields.Text(string="Response")
    error_message = fields.Char(string="Error")
