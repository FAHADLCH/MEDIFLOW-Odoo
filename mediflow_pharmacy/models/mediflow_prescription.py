# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class MediflowPrescription(models.Model):
    _name = "mediflow.prescription"
    _description = "Prescription (MedicationRequest)"
    _inherit = [
        "mediflow.company.scope.mixin",
        "mediflow.phi.audit.mixin",
        "mediflow.state.machine.mixin",
        "mediflow.event.mixin",
        "mail.thread",
        "mail.activity.mixin",
    ]
    _order = "create_date desc, id desc"

    # ----- State machine -----
    _sm_field = "state"
    _sm_transitions = {
        "draft": ["ordered", "cancelled"],
        "ordered": ["partially_dispensed", "dispensed", "cancelled"],
        "partially_dispensed": ["dispensed", "cancelled"],
        "dispensed": ["handed_over"],
    }
    _sm_groups = {
        ("draft", "ordered"): "mediflow_base.group_mediflow_doctor",
    }
    _sm_terminal = {"cancelled", "handed_over"}

    name = fields.Char(string="Rx #", required=True, copy=False, readonly=True,
                       default="New", index=True, tracking=True)
    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True,
                                 index=True, tracking=True)
    encounter_id = fields.Many2one("mediflow.encounter", string="Encounter", index=True)
    practitioner_id = fields.Many2one("mediflow.practitioner", string="Prescriber",
                                      tracking=True)
    prescribed_date = fields.Datetime(string="Prescribed On", default=fields.Datetime.now)
    state = fields.Selection([
        ("draft", "Draft"),
        ("ordered", "Ordered"),
        ("partially_dispensed", "Partially Dispensed"),
        ("dispensed", "Dispensed"),
        ("handed_over", "Handed Over"),
        ("cancelled", "Cancelled"),
    ], string="Status", default="draft", index=True, tracking=True,
        group_expand="_expand_states")

    line_ids = fields.One2many("mediflow.prescription.line", "prescription_id",
                               string="Medications")
    dispense_ids = fields.One2many("mediflow.dispense", "prescription_id",
                                   string="Dispenses")
    dispense_count = fields.Integer(compute="_compute_dispense_count")

    # Safety-check override audit trail.
    override_warnings = fields.Boolean(string="Override Safety Warnings", default=False)
    override_reason = fields.Char(string="Override Reason")
    warning_text = fields.Text(string="Detected Warnings", readonly=True)
    cancel_reason = fields.Char(string="Cancellation Reason")
    note = fields.Text(string="Notes")

    @api.model
    def _expand_states(self, states, domain):
        return [k for k, _ in type(self).state.selection]

    @api.depends("dispense_ids")
    def _compute_dispense_count(self):
        for rec in self:
            rec.dispense_count = len(rec.dispense_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "mediflow.prescription") or "New"
        records = super().create(vals_list)
        for rx in records:
            rx._emit_event("prescription.created", {
                "prescription_id": rx.id,
                "patient_id": rx.patient_id.id,
            })
        return records

    # ----- Safety checks -----
    def _detect_safety_warnings(self):
        """Return a human-readable warning string (or empty) for allergy and
        duplicate-class interaction risks across the prescription lines."""
        self.ensure_one()
        warnings = []
        patient = self.patient_id
        allergy_substances = {
            (a.substance_code or "").strip().lower()
            for a in patient.allergy_ids
            if a.clinical_status == "active" and a.substance_code
        }
        seen_classes = {}
        for line in self.line_ids:
            product = line.product_id
            if not product:
                continue
            # Allergy: match on ATC/RxNorm/drug name against recorded substances.
            tokens = {
                (product.atc_code or "").strip().lower(),
                (product.rxnorm_code or "").strip().lower(),
                (product.name or "").strip().lower(),
            }
            hit = tokens & allergy_substances
            if hit:
                warnings.append(
                    "Allergy alert: patient is allergic to '%s' (matches %s)."
                    % (next(iter(hit)), product.name))
            # Interaction proxy: duplicate therapeutic class.
            klass = (product.drug_class or "").strip().lower()
            if klass:
                if klass in seen_classes:
                    warnings.append(
                        "Duplicate therapeutic class '%s': %s and %s."
                        % (product.drug_class, seen_classes[klass], product.name))
                else:
                    seen_classes[klass] = product.name
        return "\n".join(warnings)

    def _guard_order(self):
        """Block draft->ordered when safety warnings exist unless an audited
        override is supplied."""
        for rx in self:
            if not rx.line_ids:
                raise ValidationError("Add at least one medication before signing.")
            warnings = rx._detect_safety_warnings()
            rx.with_context(sm_internal=True).write({"warning_text": warnings or False})
            if warnings and not rx.override_warnings:
                raise UserError(
                    "Safety warnings detected:\n\n%s\n\n"
                    "To proceed, tick 'Override Safety Warnings' and provide a reason."
                    % warnings)
            if warnings and rx.override_warnings and not rx.override_reason:
                raise UserError("An override reason is required to bypass safety warnings.")

    _sm_guards = {
        ("draft", "ordered"): lambda rec: rec._guard_order(),
    }

    # ----- Workflow actions -----
    def action_order(self):
        for rx in self:
            reason = None
            if rx.override_warnings and rx.warning_text:
                reason = "OVERRIDE: %s" % (rx.override_reason or "")
            rx.transition("ordered", reason=reason)

    def action_cancel(self):
        for rx in self:
            rx.transition("cancelled", reason=rx.cancel_reason)

    def action_hand_over(self):
        for rx in self:
            rx.transition("handed_over")

    def _sync_dispensed_state(self):
        """Recompute ordered/partially/dispensed based on fulfilled quantities."""
        for rx in self:
            if rx.state not in ("ordered", "partially_dispensed"):
                continue
            done = rx.dispense_ids.filtered(lambda d: d.state == "done")
            dispensed_qty = {}
            for disp in done:
                for dl in disp.line_ids:
                    dispensed_qty.setdefault(dl.product_id.id, 0.0)
                    dispensed_qty[dl.product_id.id] += dl.quantity
            fully = True
            any_done = False
            for line in rx.line_ids:
                got = dispensed_qty.get(line.product_id.id, 0.0)
                if got > 0:
                    any_done = True
                if got < line.quantity:
                    fully = False
            if fully and rx.line_ids:
                rx.transition("dispensed")
            elif any_done and rx.state == "ordered":
                rx.transition("partially_dispensed")

    def action_new_dispense(self):
        self.ensure_one()
        if self.state not in ("ordered", "partially_dispensed"):
            raise UserError("Only ordered prescriptions can be dispensed.")
        dispense = self.env["mediflow.dispense"].create({
            "prescription_id": self.id,
            "patient_id": self.patient_id.id,
            "company_id": self.company_id.id,
            "line_ids": [(0, 0, {
                "product_id": line.product_id.id,
                "quantity": line.quantity,
            }) for line in self.line_ids],
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "mediflow.dispense",
            "res_id": dispense.id,
            "view_mode": "form",
            "target": "current",
        }


class MediflowPrescriptionLine(models.Model):
    _name = "mediflow.prescription.line"
    _description = "Prescription Line"
    _order = "prescription_id, sequence, id"

    prescription_id = fields.Many2one("mediflow.prescription", string="Prescription",
                                      required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(
        "product.product", string="Medication", required=True,
        domain="[('is_medication', '=', True)]")
    dose = fields.Char(string="Dose", help="e.g. '1 tablet'.")
    frequency = fields.Char(string="Frequency", help="e.g. 'twice daily'.")
    duration_days = fields.Integer(string="Duration (days)")
    route = fields.Selection([
        ("oral", "Oral"),
        ("iv", "Intravenous"),
        ("im", "Intramuscular"),
        ("sc", "Subcutaneous"),
        ("topical", "Topical"),
        ("inhalation", "Inhalation"),
        ("other", "Other"),
    ], string="Route", default="oral")
    quantity = fields.Float(string="Quantity", default=1.0, required=True)
    instructions = fields.Char(string="Patient Instructions")
