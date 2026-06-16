# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request

from . import fhir_serializers as S

_logger = logging.getLogger(__name__)

FHIR_CT = "application/fhir+json"


class MediflowFhirController(http.Controller):
    """FHIR R4 read/search endpoints under ``/fhir/R4``.

    Auth is a bearer token (``Authorization: Bearer <token>``) resolved to a
    service user; all ORM access then runs as that user so company record rules
    and ACLs apply automatically. PHI resources are additionally consent-gated.
    """

    # ------------------------------------------------------------------
    # Infrastructure
    # ------------------------------------------------------------------
    def _json_response(self, payload, status=200):
        return request.make_response(
            json.dumps(payload),
            headers=[("Content-Type", FHIR_CT)],
            status=status,
        )

    def _error(self, status, code, message):
        return self._json_response(
            S.operation_outcome("error", code, message), status=status)

    def _authenticate(self):
        """Return the authenticated service user (as an env-bound recordset) or
        None. Reads the bearer token from the Authorization header only."""
        auth = request.httprequest.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        raw = auth[len("Bearer "):].strip()
        token = request.env["mediflow.fhir.token"].sudo()._authenticate(raw)
        if not token:
            return None
        return token.user_id

    def _can_see_national_id(self, user):
        return user.has_group("mediflow_base.group_mediflow_compliance") or \
            user.has_group("mediflow_base.group_mediflow_admin")

    def _consent_ok(self, user, patient):
        """PHI gate: export is allowed when the patient has an active consent, or
        when the caller holds compliance/admin (break-glass governed elsewhere)."""
        if patient.has_active_consent:
            return True
        return user.has_group("mediflow_base.group_mediflow_compliance") or \
            user.has_group("mediflow_base.group_mediflow_admin")

    def _env(self, user):
        return request.env(user=user.id)

    # ------------------------------------------------------------------
    # Capability statement
    # ------------------------------------------------------------------
    @http.route("/fhir/R4/metadata", type="http", auth="none", methods=["GET"],
                csrf=False)
    def metadata(self, **kw):
        statement = {
            "resourceType": "CapabilityStatement",
            "status": "active",
            "fhirVersion": "4.0.1",
            "format": ["json"],
            "rest": [{
                "mode": "server",
                "resource": [
                    {"type": t, "interaction": [{"code": "read"}, {"code": "search-type"}]}
                    for t in ("Patient", "Practitioner", "Encounter", "Appointment",
                              "Observation", "DiagnosticReport", "MedicationRequest",
                              "Coverage")
                ],
            }],
        }
        return self._json_response(statement)

    # ------------------------------------------------------------------
    # Patient
    # ------------------------------------------------------------------
    @http.route("/fhir/R4/Patient/<int:res_id>", type="http", auth="none",
                methods=["GET"], csrf=False)
    def patient_read(self, res_id, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        patient = self._env(user)["mediflow.patient"].browse(res_id)
        if not patient.exists():
            return self._error(404, "not-found", "Patient not found.")
        if not self._consent_ok(user, patient):
            return self._error(403, "forbidden", "No active consent for disclosure.")
        return self._json_response(
            S.patient_to_fhir(patient, self._can_see_national_id(user)))

    @http.route("/fhir/R4/Patient", type="http", auth="none", methods=["GET"],
                csrf=False)
    def patient_search(self, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        env = self._env(user)
        domain = []
        if kw.get("identifier"):
            domain.append(("mrn", "=", kw["identifier"]))
        if kw.get("family"):
            domain.append(("last_name", "ilike", kw["family"]))
        patients = env["mediflow.patient"].search(domain, limit=200)
        show_nid = self._can_see_national_id(user)
        resources = [
            S.patient_to_fhir(p, show_nid)
            for p in patients if self._consent_ok(user, p)
        ]
        return self._json_response(S.make_bundle(resources))

    # ------------------------------------------------------------------
    # Practitioner
    # ------------------------------------------------------------------
    @http.route("/fhir/R4/Practitioner/<int:res_id>", type="http", auth="none",
                methods=["GET"], csrf=False)
    def practitioner_read(self, res_id, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        rec = self._env(user)["mediflow.practitioner"].browse(res_id)
        if not rec.exists():
            return self._error(404, "not-found", "Practitioner not found.")
        return self._json_response(S.practitioner_to_fhir(rec))

    # ------------------------------------------------------------------
    # Encounter
    # ------------------------------------------------------------------
    @http.route("/fhir/R4/Encounter/<int:res_id>", type="http", auth="none",
                methods=["GET"], csrf=False)
    def encounter_read(self, res_id, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        rec = self._env(user)["mediflow.encounter"].browse(res_id)
        if not rec.exists():
            return self._error(404, "not-found", "Encounter not found.")
        if not self._consent_ok(user, rec.patient_id):
            return self._error(403, "forbidden", "No active consent for disclosure.")
        return self._json_response(S.encounter_to_fhir(rec))

    @http.route("/fhir/R4/Encounter", type="http", auth="none", methods=["GET"],
                csrf=False)
    def encounter_search(self, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        env = self._env(user)
        domain = []
        patient_id = self._patient_param(kw)
        if patient_id:
            domain.append(("patient_id", "=", patient_id))
        encounters = env["mediflow.encounter"].search(domain, limit=200)
        resources = [
            S.encounter_to_fhir(e)
            for e in encounters if self._consent_ok(user, e.patient_id)
        ]
        return self._json_response(S.make_bundle(resources))

    # ------------------------------------------------------------------
    # Appointment
    # ------------------------------------------------------------------
    @http.route("/fhir/R4/Appointment/<int:res_id>", type="http", auth="none",
                methods=["GET"], csrf=False)
    def appointment_read(self, res_id, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        rec = self._env(user)["mediflow.appointment"].browse(res_id)
        if not rec.exists():
            return self._error(404, "not-found", "Appointment not found.")
        return self._json_response(S.appointment_to_fhir(rec))

    # ------------------------------------------------------------------
    # Observation (lab results)
    # ------------------------------------------------------------------
    @http.route("/fhir/R4/Observation/<int:res_id>", type="http", auth="none",
                methods=["GET"], csrf=False)
    def observation_read(self, res_id, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        rec = self._env(user)["mediflow.lab.result"].browse(res_id)
        if not rec.exists():
            return self._error(404, "not-found", "Observation not found.")
        if not self._consent_ok(user, rec.patient_id):
            return self._error(403, "forbidden", "No active consent for disclosure.")
        return self._json_response(S.lab_result_to_fhir(rec))

    @http.route("/fhir/R4/Observation", type="http", auth="none", methods=["GET"],
                csrf=False)
    def observation_search(self, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        env = self._env(user)
        domain = [("state", "=", "released")]
        patient_id = self._patient_param(kw)
        if patient_id:
            domain.append(("patient_id", "=", patient_id))
        results = env["mediflow.lab.result"].search(domain, limit=200)
        resources = [
            S.lab_result_to_fhir(r)
            for r in results if self._consent_ok(user, r.patient_id)
        ]
        return self._json_response(S.make_bundle(resources))

    # ------------------------------------------------------------------
    # DiagnosticReport (lab orders)
    # ------------------------------------------------------------------
    @http.route("/fhir/R4/DiagnosticReport/<int:res_id>", type="http", auth="none",
                methods=["GET"], csrf=False)
    def diagnostic_report_read(self, res_id, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        rec = self._env(user)["mediflow.lab.order"].browse(res_id)
        if not rec.exists():
            return self._error(404, "not-found", "DiagnosticReport not found.")
        if not self._consent_ok(user, rec.patient_id):
            return self._error(403, "forbidden", "No active consent for disclosure.")
        return self._json_response(S.lab_order_to_fhir(rec))

    # ------------------------------------------------------------------
    # MedicationRequest (prescriptions)
    # ------------------------------------------------------------------
    @http.route("/fhir/R4/MedicationRequest/<int:res_id>", type="http", auth="none",
                methods=["GET"], csrf=False)
    def medication_request_read(self, res_id, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        rec = self._env(user)["mediflow.prescription"].browse(res_id)
        if not rec.exists():
            return self._error(404, "not-found", "MedicationRequest not found.")
        if not self._consent_ok(user, rec.patient_id):
            return self._error(403, "forbidden", "No active consent for disclosure.")
        return self._json_response(S.prescription_to_fhir(rec))

    @http.route("/fhir/R4/MedicationRequest", type="http", auth="none",
                methods=["GET"], csrf=False)
    def medication_request_search(self, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        env = self._env(user)
        domain = []
        patient_id = self._patient_param(kw)
        if patient_id:
            domain.append(("patient_id", "=", patient_id))
        scripts = env["mediflow.prescription"].search(domain, limit=200)
        resources = [
            S.prescription_to_fhir(p)
            for p in scripts if self._consent_ok(user, p.patient_id)
        ]
        return self._json_response(S.make_bundle(resources))

    # ------------------------------------------------------------------
    # Coverage
    # ------------------------------------------------------------------
    @http.route("/fhir/R4/Coverage/<int:res_id>", type="http", auth="none",
                methods=["GET"], csrf=False)
    def coverage_read(self, res_id, **kw):
        user = self._authenticate()
        if not user:
            return self._error(401, "login", "Invalid or missing bearer token.")
        rec = self._env(user)["mediflow.coverage"].browse(res_id)
        if not rec.exists():
            return self._error(404, "not-found", "Coverage not found.")
        return self._json_response(S.coverage_to_fhir(rec))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _patient_param(self, kw):
        """Extract a numeric patient id from a ?patient= search parameter, which
        may be a bare id or a 'Patient/<id>' reference."""
        raw = kw.get("patient") or kw.get("subject")
        if not raw:
            return None
        if "/" in raw:
            raw = raw.rsplit("/", 1)[-1]
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
