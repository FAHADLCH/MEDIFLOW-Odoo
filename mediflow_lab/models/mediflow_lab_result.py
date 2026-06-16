# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class MediflowLabResult(models.Model):
    _name = "mediflow.lab.result"
    _description = "Lab Result (Observation)"
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
        "preliminary": ["verified", "cancelled"],
        "verified": ["released"],
        "released": ["amended"],
    }
    # verifier-gated transitions
    _sm_groups = {
        ("preliminary", "verified"): "mediflow_base.group_mediflow_lab_verifier",
        ("verified", "released"): "mediflow_base.group_mediflow_lab_verifier",
        ("released", "amended"): "mediflow_base.group_mediflow_lab_verifier",
    }
    _sm_terminal = {"cancelled", "amended"}

    name = fields.Char(string="Result", compute="_compute_name", store=True)
    order_id = fields.Many2one("mediflow.lab.order", string="Lab Order",
                               required=True, ondelete="cascade", index=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient",
                                 related="order_id.patient_id", store=True, index=True)
    test_id = fields.Many2one("mediflow.lab.test", string="Test", required=True, index=True)
    loinc_code = fields.Char(related="test_id.loinc_code", store=True)

    state = fields.Selection([
        ("preliminary", "Preliminary"),
        ("verified", "Verified"),
        ("released", "Released"),
        ("amended", "Amended"),
        ("cancelled", "Cancelled"),
    ], string="Status", default="preliminary", index=True, tracking=True,
        group_expand="_expand_states")

    # Result payload.
    value_numeric = fields.Float(string="Numeric Value")
    value_text = fields.Char(string="Text Value")
    uom_name = fields.Char(related="test_id.uom_name", string="Unit", store=True)
    ref_low = fields.Float(related="test_id.ref_low", store=True)
    ref_high = fields.Float(related="test_id.ref_high", store=True)
    abnormal_flag = fields.Selection([
        ("normal", "Normal"),
        ("low", "Low"),
        ("high", "High"),
        ("critical_low", "Critical Low"),
        ("critical_high", "Critical High"),
    ], string="Flag", default="normal", index=True)
    is_critical = fields.Boolean(string="Critical", compute="_compute_is_critical",
                                 store=True, index=True)

    verified_by_id = fields.Many2one("mediflow.practitioner", string="Verified By",
                                     readonly=True)
    released_at = fields.Datetime(string="Released At", readonly=True)
    note = fields.Text(string="Notes")

    # Versioning / amendment chain.
    version = fields.Integer(string="Version", default=1, readonly=True)
    replaces_id = fields.Many2one("mediflow.lab.result", string="Replaces",
                                  readonly=True, index=True)
    replaced_by_id = fields.Many2one("mediflow.lab.result", string="Replaced By",
                                     readonly=True, index=True)

    @api.model
    def _expand_states(self, states, domain):
        return [k for k, _ in type(self).state.selection]

    @api.depends("test_id", "value_numeric", "value_text", "version")
    def _compute_name(self):
        for rec in self:
            val = rec.value_text or (rec.value_numeric if rec.value_numeric else "")
            base = f"{rec.test_id.name}: {val}" if rec.test_id else "Result"
            rec.name = f"{base} (v{rec.version})" if rec.version > 1 else base

    @api.depends("abnormal_flag")
    def _compute_is_critical(self):
        for rec in self:
            rec.is_critical = rec.abnormal_flag in ("critical_low", "critical_high")

    # ----- Abnormal / critical evaluation -----
    def _evaluate_flags(self):
        """Compute abnormal_flag from the test reference & critical thresholds.
        Critical breaches raise lab.critical.flagged immediately, independent of
        workflow state."""
        for rec in self:
            test = rec.test_id
            if not test or test.result_type != "numeric":
                rec.abnormal_flag = "normal"
                continue
            v = rec.value_numeric
            flag = "normal"
            if test.critical_low and v <= test.critical_low:
                flag = "critical_low"
            elif test.critical_high and v >= test.critical_high:
                flag = "critical_high"
            elif test.ref_low and v < test.ref_low:
                flag = "low"
            elif test.ref_high and v > test.ref_high:
                flag = "high"
            previous = rec.abnormal_flag
            rec.abnormal_flag = flag
            if flag in ("critical_low", "critical_high") and previous != flag:
                rec._emit_event("lab.critical.flagged", {
                    "result_id": rec.id,
                    "patient_id": rec.patient_id.id,
                    "test": test.name,
                    "value": v,
                    "flag": flag,
                })

    # ----- Immutability guard -----
    # Fields permitted to change while a row is in the released chain (admin/audit only).
    _RELEASED_WRITABLE = {"replaced_by_id", "message_main_attachment_id"}

    def write(self, vals):
        if not self.env.context.get("sm_internal") and not self.env.context.get(
                "mediflow_amend"):
            for rec in self:
                if rec.state == "released":
                    if set(vals.keys()) - self._RELEASED_WRITABLE:
                        raise UserError(
                            "A released lab result is immutable. Create an amendment "
                            "instead of editing it.")
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state in ("released", "verified"):
                raise UserError("Verified or released results cannot be deleted.")
        return super().unlink()

    # ----- Workflow actions -----
    def action_enter_result(self):
        """Recompute flags when a tech enters/updates a preliminary value."""
        self.filtered(lambda r: r.state == "preliminary")._evaluate_flags()

    def action_verify(self):
        for rec in self:
            rec._evaluate_flags()
            practitioner = self.env["mediflow.practitioner"].search(
                [("user_id", "=", self.env.uid)], limit=1)
            rec.with_context(sm_internal=True).write(
                {"verified_by_id": practitioner.id})
            rec.transition("verified")

    def action_release(self):
        for rec in self:
            rec.with_context(sm_internal=True).write(
                {"released_at": fields.Datetime.now()})
            rec.transition("released")
            rec._emit_event("lab.result.released", {
                "result_id": rec.id,
                "patient_id": rec.patient_id.id,
                "test": rec.test_id.name,
                "order_id": rec.order_id.id,
            })

    def action_cancel(self):
        for rec in self:
            rec.transition("cancelled")

    def action_amend(self):
        """Create a corrected successor; the original released row is preserved and
        marked replaced. Returns the new version for editing."""
        self.ensure_one()
        if self.state != "released":
            raise ValidationError("Only released results can be amended.")
        new = self.copy(default={
            "state": "preliminary",
            "version": self.version + 1,
            "replaces_id": self.id,
            "verified_by_id": False,
            "released_at": False,
        })
        # Mark the original as amended (terminal) and link forward.
        self.with_context(mediflow_amend=True).write({"replaced_by_id": new.id})
        self.transition("amended", reason="Superseded by amended result")
        self._emit_event("lab.result.amended", {
            "original_id": self.id,
            "amended_id": new.id,
            "patient_id": self.patient_id.id,
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "mediflow.lab.result",
            "res_id": new.id,
            "view_mode": "form",
            "target": "current",
        }
