# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal


class MediflowPortal(CustomerPortal):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_portal_patient(self):
        """Resolve the signed-in user to their patient record, or None.

        Resolution is by explicit portal_user_id link first, then by the shared
        partner. Returns a sudo() recordset scoped to exactly one patient so that
        downstream queries can be safely constrained to ``patient.id``."""
        user = request.env.user
        Patient = request.env["mediflow.patient"].sudo()
        patient = Patient.search([("portal_user_id", "=", user.id)], limit=1)
        if not patient and user.partner_id:
            patient = Patient.search([("partner_id", "=", user.partner_id.id)], limit=1)
        return patient or None

    def _patient_has_active_consent(self, patient):
        """True if the patient has an active data-sharing (or treatment) consent
        gating disclosure of clinical results on the portal."""
        consents = patient.consent_ids.filtered(
            lambda c: c.state == "active" and c.scope in ("data_sharing", "treatment"))
        return bool(consents)

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        patient = self._get_portal_patient()
        if not patient:
            return values
        if "mediflow_appointment_count" in counters:
            values["mediflow_appointment_count"] = request.env[
                "mediflow.appointment"].sudo().search_count(
                [("patient_id", "=", patient.id)])
        if "mediflow_result_count" in counters:
            count = 0
            if self._patient_has_active_consent(patient):
                count = request.env["mediflow.lab.result"].sudo().search_count([
                    ("patient_id", "=", patient.id),
                    ("state", "=", "released"),
                ])
            values["mediflow_result_count"] = count
        if "mediflow_invoice_count" in counters:
            values["mediflow_invoice_count"] = request.env["account.move"].sudo().search_count([
                ("mediflow_patient_id", "=", patient.id),
                ("is_mediflow_invoice", "=", True),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
            ])
        return values

    # ------------------------------------------------------------------
    # Appointments
    # ------------------------------------------------------------------
    @http.route(["/my/appointments"], type="http", auth="user", website=True)
    def portal_my_appointments(self, **kw):
        patient = self._get_portal_patient()
        if not patient:
            return request.redirect("/my")
        appointments = request.env["mediflow.appointment"].sudo().search(
            [("patient_id", "=", patient.id)], order="start desc")
        values = {
            "appointments": appointments,
            "patient": patient,
            "page_name": "mediflow_appointments",
        }
        return request.render("mediflow.portal_my_appointments", values)

    # ------------------------------------------------------------------
    # Lab results (consent-gated, released only)
    # ------------------------------------------------------------------
    @http.route(["/my/lab-results"], type="http", auth="user", website=True)
    def portal_my_lab_results(self, **kw):
        patient = self._get_portal_patient()
        if not patient:
            return request.redirect("/my")
        has_consent = self._patient_has_active_consent(patient)
        results = request.env["mediflow.lab.result"]
        if has_consent:
            results = request.env["mediflow.lab.result"].sudo().search([
                ("patient_id", "=", patient.id),
                ("state", "=", "released"),
            ], order="released_at desc")
        values = {
            "results": results,
            "has_consent": has_consent,
            "patient": patient,
            "page_name": "mediflow_lab_results",
        }
        return request.render("mediflow.portal_my_lab_results", values)

    # ------------------------------------------------------------------
    # Invoices
    # ------------------------------------------------------------------
    @http.route(["/my/invoices"], type="http", auth="user", website=True)
    def portal_my_invoices(self, **kw):
        patient = self._get_portal_patient()
        if not patient:
            return request.redirect("/my")
        invoices = request.env["account.move"].sudo().search([
            ("mediflow_patient_id", "=", patient.id),
            ("is_mediflow_invoice", "=", True),
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
        ], order="invoice_date desc")
        values = {
            "invoices": invoices,
            "patient": patient,
            "page_name": "mediflow_invoices",
        }
        return request.render("mediflow.portal_my_invoices", values)

    # ------------------------------------------------------------------
    # Consents
    # ------------------------------------------------------------------
    @http.route(["/my/consents"], type="http", auth="user", website=True)
    def portal_my_consents(self, **kw):
        patient = self._get_portal_patient()
        if not patient:
            return request.redirect("/my")
        values = {
            "consents": patient.consent_ids,
            "patient": patient,
            "page_name": "mediflow_consents",
        }
        return request.render("mediflow.portal_my_consents", values)

    @http.route(["/my/consents/<int:consent_id>/revoke"], type="http", auth="user",
                website=True, methods=["POST"])
    def portal_revoke_consent(self, consent_id, **kw):
        patient = self._get_portal_patient()
        if not patient:
            return request.redirect("/my")
        # Ownership guard: only operate on a consent that belongs to this patient.
        consent = request.env["mediflow.consent"].sudo().browse(consent_id)
        if not consent.exists() or consent.patient_id.id != patient.id:
            raise AccessError("You cannot modify this consent.")
        if consent.state == "active":
            consent.action_revoke()
        return request.redirect("/my/consents")
