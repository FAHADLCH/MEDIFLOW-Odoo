# -*- coding: utf-8 -*-
import json

from odoo import api, fields, models


class MediflowAuditLog(models.Model):
    """Append-only audit trail for PHI access and clinical state changes.

    Rows are written exclusively through the privileged ``log()`` helper. Write
    and unlink are blocked at the ORM level so the trail is tamper-evident.
    """

    _name = "mediflow.audit.log"
    _description = "MEDIFLOW Audit Log"
    _order = "id desc"
    _rec_name = "id"

    ACTIONS = [
        ("read", "Read"),
        ("create", "Create"),
        ("write", "Write"),
        ("unlink", "Delete"),
        ("state", "State Change"),
        ("break_glass", "Break-Glass Access"),
        ("export", "Export"),
        ("login", "Login"),
    ]

    user_id = fields.Many2one("res.users", string="User", required=True, index=True,
                              ondelete="restrict")
    company_id = fields.Many2one("res.company", string="Clinic", required=True, index=True,
                                 ondelete="restrict")
    model = fields.Char(string="Model", required=True, index=True)
    res_id = fields.Integer(string="Record ID", index=True)
    patient_id = fields.Many2one("res.partner", string="Patient", index=True, ondelete="set null")
    action = fields.Selection(ACTIONS, string="Action", required=True, index=True)
    timestamp = fields.Datetime(string="Timestamp", required=True, default=fields.Datetime.now,
                                index=True)
    ip_address = fields.Char(string="Source IP")
    reason = fields.Text(string="Reason")
    field_changes = fields.Text(string="Field Changes (JSON)")

    @api.model
    def log(self, model, res_id, action, patient_id=None, reason=None,
            field_changes=None, company_id=None):
        """Privileged entry point. Always writes via sudo so audit cannot be
        suppressed by the acting user's access rights."""
        values = {
            "user_id": self.env.uid,
            "company_id": company_id or self.env.company.id,
            "model": model,
            "res_id": res_id or 0,
            "patient_id": patient_id,
            "action": action,
            "timestamp": fields.Datetime.now(),
            "reason": reason,
        }
        if field_changes is not None:
            values["field_changes"] = json.dumps(field_changes, default=str)
        request = getattr(self.env, "request", None)
        if request is not None and getattr(request, "httprequest", None) is not None:
            values["ip_address"] = request.httprequest.remote_addr
        return self.sudo().create(values)

    def write(self, vals):
        raise self._immutable_error()

    def unlink(self):
        raise self._immutable_error()

    def _immutable_error(self):
        from odoo.exceptions import UserError
        from odoo.tools.translate import _
        return UserError(_("Audit log entries are append-only and cannot be modified or deleted."))
