# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MediflowEncounter(models.Model):
    """Visit / clinical episode. Anchors documentation, orders, results and
    charges. Projects to FHIR ``Encounter``."""

    _name = "mediflow.encounter"
    _description = "Encounter"
    _inherit = [
        "mediflow.company.scope.mixin",
        "mediflow.phi.audit.mixin",
        "mediflow.state.machine.mixin",
        "mediflow.event.mixin",
        "mail.thread",
        "mail.activity.mixin",
    ]
    _order = "start desc, id desc"

    # ----- State machine (docs/phase-1/07-state-machines.md §2) -----
    _sm_field = "state"
    _sm_transitions = {
        "planned": {"in_progress", "cancelled"},
        "in_progress": {"completed", "cancelled"},
        "completed": {"amended"},
    }
    _sm_groups = {
        ("completed", "amended"): "mediflow_base.group_mediflow_doctor",
    }
    _sm_terminal = {"cancelled"}

    name = fields.Char(string="Encounter", required=True, copy=False, index=True,
                       default=lambda self: _("New"))
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True, ondelete="restrict", tracking=True)
    practitioner_id = fields.Many2one("mediflow.practitioner", string="Practitioner",
                                      index=True, ondelete="restrict", tracking=True)
    appointment_id = fields.Many2one("mediflow.appointment", string="Appointment",
                                     index=True, ondelete="set null")
    encounter_type = fields.Selection([
        ("ambulatory", "Ambulatory"),
        ("emergency", "Emergency"),
        ("followup", "Follow-up"),
        ("virtual", "Virtual"),
    ], default="ambulatory", required=True)
    start = fields.Datetime(string="Start", default=fields.Datetime.now, index=True,
                            tracking=True)
    stop = fields.Datetime(string="End", tracking=True)
    reason = fields.Char(string="Chief Complaint")
    problem_ids = fields.One2many("mediflow.problem", "encounter_id", string="Problems")
    vital_ids = fields.One2many("mediflow.vital.sign", "encounter_id", string="Vitals")
    document_ids = fields.One2many("mediflow.clinical.document", "encounter_id",
                                   string="Documents")
    assessment = fields.Text(string="Assessment")
    plan = fields.Text(string="Plan")
    parent_encounter_id = fields.Many2one("mediflow.encounter", string="Amends",
                                          readonly=True)
    state = fields.Selection([
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("amended", "Amended"),
        ("cancelled", "Cancelled"),
    ], default="planned", required=True, tracking=True, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                company_id = vals.get("company_id") or self.env.company.id
                seq = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = seq.next_by_code("mediflow.encounter") or _("New")
        return super().create(vals_list)

    # ----- Guards -----
    def _guard_complete(self):
        for enc in self:
            if not enc.practitioner_id:
                raise UserError(_("A practitioner is required before completing the encounter."))
            if not enc.assessment:
                raise UserError(_("An assessment is required before completing the encounter."))

    # ----- Actions -----
    def action_start(self):
        self._guard_open_from_appointment()
        self.transition("in_progress")
        if not self.start:
            self.with_context(sm_internal=True).write({"start": fields.Datetime.now()})

    def action_complete(self):
        self._guard_complete()
        self.with_context(sm_internal=True).write({"stop": fields.Datetime.now()})
        self.transition("completed")

    def action_cancel(self):
        self.transition("cancelled")

    def action_amend(self):
        """Create a linked addendum encounter; the original stays immutable."""
        self.ensure_one()
        addendum = self.copy({
            "name": _("New"),
            "parent_encounter_id": self.id,
            "state": "in_progress",
            "start": fields.Datetime.now(),
            "stop": False,
        })
        self.transition("amended")
        return {
            "type": "ir.actions.act_window",
            "res_model": "mediflow.encounter",
            "res_id": addendum.id,
            "view_mode": "form",
            "target": "current",
        }

    def _guard_open_from_appointment(self):
        for enc in self:
            if enc.appointment_id and enc.appointment_id.state in ("confirmed",):
                enc.appointment_id.action_start_consult()
