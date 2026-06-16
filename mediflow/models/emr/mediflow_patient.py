# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MediflowPatient(models.Model):
    """Patient master record. Bridges to ``res.partner`` for portal/accounting and
    projects to the FHIR ``Patient`` resource at the API boundary."""

    _name = "mediflow.patient"
    _description = "Patient"
    _inherit = [
        "mediflow.company.scope.mixin",
        "mediflow.phi.audit.mixin",
        "mediflow.state.machine.mixin",
        "mediflow.event.mixin",
        "mail.thread",
        "mail.activity.mixin",
    ]
    _order = "name"

    # ----- State machine (see docs/phase-1/07-state-machines.md §11) -----
    _sm_field = "state"
    _sm_transitions = {
        "draft": {"active"},
        "active": {"inactive", "deceased", "merged"},
        "inactive": {"active"},
    }
    _sm_terminal = {"deceased", "merged"}

    name = fields.Char(string="Full Name", compute="_compute_name", store=True, index=True)
    first_name = fields.Char(required=True, tracking=True)
    last_name = fields.Char(required=True, tracking=True)
    mrn = fields.Char(string="MRN", required=True, copy=False, index=True,
                      default=lambda self: _("New"),
                      help="Medical Record Number, unique per clinic.")
    national_id = fields.Char(string="National ID", index=True, copy=False, groups="mediflow.group_mediflow_reception,mediflow.group_mediflow_admin")
    birthdate = fields.Date(string="Date of Birth", index=True, tracking=True)
    age = fields.Integer(string="Age", compute="_compute_age")
    gender = fields.Selection([
        ("male", "Male"), ("female", "Female"),
        ("other", "Other"), ("unknown", "Unknown"),
    ], default="unknown", tracking=True)
    blood_group = fields.Selection([
        ("A+", "A+"), ("A-", "A-"), ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"), ("O+", "O+"), ("O-", "O-"),
    ])
    phone = fields.Char(index=True, tracking=True)
    email = fields.Char(index=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Contact", ondelete="restrict",
                                 help="Linked contact for billing and portal.")
    portal_user_id = fields.Many2one("res.users", string="Portal User", ondelete="set null")
    emergency_contact_ids = fields.One2many("res.partner", "mediflow_emergency_for_id",
                                            string="Emergency Contacts")
    encounter_ids = fields.One2many("mediflow.encounter", "patient_id", string="Encounters")
    encounter_count = fields.Integer(compute="_compute_encounter_count")
    allergy_ids = fields.One2many("mediflow.allergy", "patient_id", string="Allergies")
    problem_ids = fields.One2many("mediflow.problem", "patient_id", string="Problems")
    consent_ids = fields.One2many("mediflow.consent", "patient_id", string="Consents")
    has_active_consent = fields.Boolean(compute="_compute_has_active_consent",
                                        search="_search_has_active_consent",
                                        string="Consent on File")
    merged_into_id = fields.Many2one("mediflow.patient", string="Merged Into", readonly=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("deceased", "Deceased"),
        ("merged", "Merged"),
    ], default="draft", required=True, tracking=True, index=True)
    deceased_date = fields.Date(string="Date of Death")

    _sql_constraints = [
        ("mrn_company_uniq", "unique(mrn, company_id)",
         "The MRN must be unique per clinic."),
    ]

    @api.depends("first_name", "last_name")
    def _compute_name(self):
        for patient in self:
            patient.name = " ".join(filter(None, [patient.first_name, patient.last_name]))

    @api.depends("birthdate")
    def _compute_age(self):
        today = date.today()
        for patient in self:
            if patient.birthdate:
                bd = patient.birthdate
                patient.age = today.year - bd.year - (
                    (today.month, today.day) < (bd.month, bd.day))
            else:
                patient.age = 0

    def _compute_encounter_count(self):
        data = self.env["mediflow.encounter"].read_group(
            [("patient_id", "in", self.ids)], ["patient_id"], ["patient_id"])
        mapping = {d["patient_id"][0]: d["patient_id_count"] for d in data}
        for patient in self:
            patient.encounter_count = mapping.get(patient.id, 0)

    @api.depends("consent_ids.state", "consent_ids.scope")
    def _compute_has_active_consent(self):
        for patient in self:
            patient.has_active_consent = any(
                c.state == "active" for c in patient.consent_ids)

    def _search_has_active_consent(self, operator, value):
        if operator not in ("=", "!="):
            raise ValidationError(_("Unsupported operator for consent filter."))
        with_consent = self.env["mediflow.consent"].search(
            [("state", "=", "active")]).mapped("patient_id").ids
        positive = (operator == "=" and value) or (operator == "!=" and not value)
        return [("id", "in" if positive else "not in", with_consent)]

    @api.constrains("birthdate")
    def _check_birthdate(self):
        for patient in self:
            if patient.birthdate and patient.birthdate > date.today():
                raise ValidationError(_("Date of birth cannot be in the future."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("mrn", _("New")) == _("New"):
                company_id = vals.get("company_id") or self.env.company.id
                seq = self.env["ir.sequence"].with_company(company_id)
                vals["mrn"] = seq.next_by_code("mediflow.patient.mrn") or _("New")
        return super().create(vals_list)

    # ----- Actions -----
    def action_activate(self):
        self.transition("active")

    def action_set_inactive(self):
        self.transition("inactive")

    def action_view_encounters(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Encounters"),
            "res_model": "mediflow.encounter",
            "view_mode": "list,form",
            "domain": [("patient_id", "=", self.id)],
            "context": {"default_patient_id": self.id},
        }
