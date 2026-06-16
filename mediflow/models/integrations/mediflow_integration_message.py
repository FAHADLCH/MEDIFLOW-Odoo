# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class MediflowIntegrationMessage(models.Model):
    """Inbox for inbound integration payloads (HL7 v2, FHIR, JSON). Received
    messages are stored durably and a ``integration.inbound.received`` event is
    emitted so downstream processors can pick them up asynchronously."""

    _name = "mediflow.integration.message"
    _description = "MEDIFLOW Inbound Message"
    _inherit = ["mediflow.company.scope.mixin", "mediflow.event.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(string="Reference", required=True, default=lambda self: _("Inbound"),
                       copy=False)
    integration_id = fields.Many2one("mediflow.integration", string="Integration",
                                     ondelete="set null", index=True)
    message_type = fields.Selection([
        ("hl7v2", "HL7 v2"),
        ("fhir", "FHIR"),
        ("json", "JSON"),
        ("raw", "Raw"),
    ], string="Format", default="raw", required=True)
    payload = fields.Text(string="Payload")
    source_ip = fields.Char(string="Source IP")
    state = fields.Selection([
        ("received", "Received"),
        ("processed", "Processed"),
        ("error", "Error"),
    ], default="received", required=True, index=True)
    processed_on = fields.Datetime(readonly=True)
    note = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        messages = super().create(vals_list)
        for msg in messages:
            msg._emit_event("integration.inbound.received", {
                "id": msg.id,
                "integration_type": msg.integration_id.integration_type if msg.integration_id else False,
                "message_type": msg.message_type,
            })
        return messages

    def action_mark_processed(self):
        self.write({"state": "processed", "processed_on": fields.Datetime.now()})
