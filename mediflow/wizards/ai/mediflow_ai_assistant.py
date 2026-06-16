# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class MediflowAiAssistant(models.TransientModel):
    """Lightweight, on-demand clinical assistant. Produces plain-language
    explanations of released lab results or a history snapshot. Always advisory:
    output is labelled and never written back to the clinical record automatically.
    """

    _name = "mediflow.ai.assistant"
    _description = "MEDIFLOW AI Assistant"

    patient_id = fields.Many2one("mediflow.patient", string="Patient", required=True)
    mode = fields.Selection([
        ("explain_results", "Explain recent lab results"),
        ("summarize_history", "Summarize clinical history"),
        ("free", "Ask a question"),
    ], string="Mode", required=True, default="explain_results")
    question = fields.Text(string="Question")
    answer = fields.Text(string="Answer", readonly=True)
    source = fields.Selection([
        ("ai", "AI provider"),
        ("template", "Local summary"),
        ("blocked", "Blocked — no consent"),
    ], string="Source", readonly=True)

    def action_run(self):
        self.ensure_one()
        system = (
            "You are a careful clinical assistant. Explain in plain, reassuring "
            "language suitable for the audience. Never give a diagnosis or change "
            "treatment. Recommend contacting the care team for anything abnormal.")
        context = self._build_context()
        result = self.env["mediflow.ai.service"].complete(
            "assistant_%s" % self.mode, system, context, patient=self.patient_id)
        if result.get("ok"):
            self.answer = result["text"]
            self.source = "ai"
        elif result.get("status") == "blocked":
            self.answer = _(
                "This patient has no active consent for AI processing. "
                "Showing a basic local summary is also blocked. Capture consent first.")
            self.source = "blocked"
        else:
            self.answer = self._local_summary()
            self.source = "template"
        return {
            "type": "ir.actions.act_window",
            "res_model": "mediflow.ai.assistant",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def _released_results(self):
        return self.env["mediflow.lab.result"].search([
            ("patient_id", "=", self.patient_id.id),
            ("state", "=", "released"),
        ], order="create_date desc", limit=20)

    def _build_context(self):
        self.ensure_one()
        if self.mode == "free":
            return self.question or ""
        if self.mode == "explain_results":
            rows = []
            for r in self._released_results():
                flag = dict(r._fields["abnormal_flag"].selection).get(r.abnormal_flag)
                value = r.value_text or ("%s %s" % (r.value_numeric, r.uom_name or ""))
                rows.append("%s: %s [%s] ref %s-%s" % (
                    r.test_id.display_name, value, flag, r.ref_low, r.ref_high))
            return "Explain these released lab results for the patient:\n" + "\n".join(rows)
        # summarize_history
        enc = self.env["mediflow.encounter"].search(
            [("patient_id", "=", self.patient_id.id)], order="start desc", limit=10)
        lines = ["Recent encounters:"]
        for e in enc:
            lines.append("- %s: %s | %s" % (e.start, e.reason or "n/a",
                                            e.assessment or "n/a"))
        return "\n".join(lines)

    def _local_summary(self):
        self.ensure_one()
        if self.mode == "explain_results":
            results = self._released_results()
            abnormal = results.filtered(lambda r: r.abnormal_flag != "normal")
            if not results:
                return _("No released lab results are available for this patient.")
            if not abnormal:
                return _("All %s released result(s) are within normal reference "
                         "ranges. Continue routine care.") % len(results)
            parts = [_("The following result(s) are outside the normal range and "
                       "should be reviewed with the care team:")]
            for r in abnormal:
                value = r.value_text or ("%s %s" % (r.value_numeric, r.uom_name or ""))
                parts.append("• %s: %s (%s)" % (
                    r.test_id.display_name, value,
                    dict(r._fields["abnormal_flag"].selection).get(r.abnormal_flag)))
            return "\n".join(parts)
        if self.mode == "summarize_history":
            return self._build_context()
        return _("Connect an AI provider to answer free-form questions.")
