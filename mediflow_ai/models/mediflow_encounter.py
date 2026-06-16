# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

# Chief-complaint keywords that escalate acuity regardless of vitals.
_RED_FLAGS = (
    ("emergent", ("chest pain", "shortness of breath", "difficulty breathing",
                  "stroke", "unconscious", "severe bleeding", "anaphylax",
                  "seizure", "suicidal")),
    ("urgent", ("fever", "vomiting", "dehydration", "fracture", "head injury",
                "abdominal pain", "palpitation")),
)


class MediflowEncounter(models.Model):
    """Smart triage suggestion (offline) and AI-assisted documentation drafting
    (human-reviewed, never auto-finalized)."""

    _inherit = "mediflow.encounter"

    mf_acuity_suggestion = fields.Selection([
        ("routine", "Routine"),
        ("urgent", "Urgent"),
        ("emergent", "Emergent"),
    ], string="Suggested Acuity", compute="_compute_acuity")
    mf_acuity_rationale = fields.Char(string="Triage Rationale", compute="_compute_acuity")

    mf_ai_summary = fields.Text(string="AI Draft Summary", copy=False)
    mf_ai_summary_source = fields.Selection([
        ("ai", "AI provider"),
        ("template", "Local template"),
    ], string="Draft Source", copy=False)
    mf_ai_summary_date = fields.Datetime(string="Draft Generated", copy=False)

    @api.depends("reason", "vital_ids", "vital_ids.spo2", "vital_ids.systolic",
                 "vital_ids.pulse", "vital_ids.temperature",
                 "vital_ids.respiratory_rate", "vital_ids.pain_score")
    def _compute_acuity(self):
        for enc in self:
            level, reasons = enc._assess_acuity()
            enc.mf_acuity_suggestion = level
            enc.mf_acuity_rationale = ", ".join(reasons) if reasons else _("Stable presentation")

    def _assess_acuity(self):
        self.ensure_one()
        reasons = []
        rank = {"routine": 0, "urgent": 1, "emergent": 2}
        level = "routine"

        def bump(target, why):
            nonlocal level
            if rank[target] > rank[level]:
                level = target
            reasons.append(why)

        text = (self.reason or "").lower()
        for target, keywords in _RED_FLAGS:
            if any(k in text for k in keywords):
                bump(target, _("complaint: %s") % next(k for k in keywords if k in text))

        vital = self.vital_ids[:1]
        if vital:
            v = vital
            if v.spo2 and v.spo2 < 92:
                bump("emergent", _("SpO2 %.0f%%") % v.spo2)
            if v.systolic and (v.systolic >= 180 or v.systolic <= 90):
                bump("urgent", _("BP %s mmHg") % v.systolic)
            if v.pulse and (v.pulse > 120 or v.pulse < 50):
                bump("urgent", _("HR %s") % v.pulse)
            if v.temperature and v.temperature >= 39.5:
                bump("urgent", _("Temp %.1f°C") % v.temperature)
            if v.respiratory_rate and (v.respiratory_rate >= 24 or v.respiratory_rate <= 8):
                bump("urgent", _("RR %s") % v.respiratory_rate)
            if v.pain_score and v.pain_score >= 8:
                bump("urgent", _("pain %s/10") % v.pain_score)
        return level, reasons

    # ----- AI documentation draft (human-reviewed) -----
    def action_mf_ai_draft_summary(self):
        self.ensure_one()
        context = self._mf_build_clinical_context()
        system = (
            "You are a clinical scribe assistant. Draft a concise SOAP-style "
            "encounter summary from the structured data provided. Be factual, do "
            "not invent findings, and end with a clear note that a clinician must "
            "review and sign. Use short sections: Subjective, Objective, "
            "Assessment, Plan.")
        result = self.env["mediflow.ai.service"].complete(
            "soap_draft", system, context, patient=self.patient_id)
        if result.get("ok"):
            body = result["text"]
            source = "ai"
        else:
            body = self._mf_template_summary()
            source = "template"
        banner = _("AI-GENERATED DRAFT — REVIEW AND SIGN BEFORE USE.\n\n")
        self.write({
            "mf_ai_summary": banner + body,
            "mf_ai_summary_source": source,
            "mf_ai_summary_date": fields.Datetime.now(),
        })
        return True

    def _mf_build_clinical_context(self):
        self.ensure_one()
        lines = [
            "Encounter type: %s" % (self.encounter_type or "n/a"),
            "Chief complaint: %s" % (self.reason or "n/a"),
            "Suggested acuity: %s (%s)" % (self.mf_acuity_suggestion or "n/a",
                                           self.mf_acuity_rationale or ""),
        ]
        v = self.vital_ids[:1]
        if v:
            lines.append(
                "Vitals: T %.1f, HR %s, BP %s/%s, RR %s, SpO2 %.0f, pain %s/10" % (
                    v.temperature or 0, v.pulse or 0, v.systolic or 0,
                    v.diastolic or 0, v.respiratory_rate or 0, v.spo2 or 0,
                    v.pain_score or 0))
        if self.problem_ids:
            lines.append("Active problems: %s" % ", ".join(
                p.display_name for p in self.problem_ids[:10]))
        if self.assessment:
            lines.append("Clinician assessment: %s" % self.assessment)
        if self.plan:
            lines.append("Plan: %s" % self.plan)
        return "\n".join(lines)

    def _mf_template_summary(self):
        self.ensure_one()
        v = self.vital_ids[:1]
        vitals = (
            "T %.1f°C, HR %s, BP %s/%s, RR %s, SpO2 %.0f%%" % (
                v.temperature or 0, v.pulse or 0, v.systolic or 0,
                v.diastolic or 0, v.respiratory_rate or 0, v.spo2 or 0)
            if v else _("not recorded"))
        return _(
            "Subjective: %(reason)s\n"
            "Objective: %(vitals)s\n"
            "Assessment: %(assessment)s\n"
            "Plan: %(plan)s") % {
            "reason": self.reason or _("not recorded"),
            "vitals": vitals,
            "assessment": self.assessment or _("pending"),
            "plan": self.plan or _("pending"),
        }
