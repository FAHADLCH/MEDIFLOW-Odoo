# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MediflowIntegrationController(http.Controller):
    """Authenticated inbound endpoint for lab analyzers / HIS systems.

    External systems POST an HL7 v2 or FHIR payload with a bearer token that
    matches an active ``hl7_lab`` integration's ``inbound_token``. The payload is
    persisted to the inbound inbox and an event is emitted; no PHI parsing is
    performed inline so the request returns fast and stays robust.
    """

    @http.route("/mediflow/integration/hl7", type="http", auth="public",
                methods=["POST"], csrf=False, save_session=False)
    def hl7_inbound(self, **kwargs):
        token = self._bearer()
        if not token:
            return self._json({"status": "error", "message": "missing token"}, 401)

        integration = request.env["mediflow.integration"].sudo().search([
            ("integration_type", "=", "hl7_lab"),
            ("is_active", "=", True),
            ("inbound_token", "=", token),
        ], limit=1)
        if not integration:
            return self._json({"status": "error", "message": "unauthorized"}, 401)

        raw = request.httprequest.get_data(as_text=True) or ""
        if not raw.strip():
            return self._json({"status": "error", "message": "empty payload"}, 400)

        message_type = self._detect_format(raw)
        try:
            message = request.env["mediflow.integration.message"].sudo().with_company(
                integration.company_id.id or request.env.company.id).create({
                    "integration_id": integration.id,
                    "company_id": integration.company_id.id or request.env.company.id,
                    "message_type": message_type,
                    "payload": raw[:65535],
                    "source_ip": request.httprequest.remote_addr,
                })
        except Exception as exc:  # noqa: BLE001
            _logger.exception("HL7 inbound store failed")
            return self._json({"status": "error", "message": str(exc)[:200]}, 500)

        return self._json({"status": "received", "id": message.id,
                           "format": message_type}, 200)

    # ----- helpers -----
    def _bearer(self):
        header = request.httprequest.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            return header[7:].strip()
        return request.httprequest.headers.get("X-Mediflow-Token", "").strip() or None

    def _detect_format(self, raw):
        head = raw.lstrip()[:8].upper()
        if head.startswith("MSH"):
            return "hl7v2"
        if head.startswith("{") or head.startswith("["):
            try:
                data = json.loads(raw)
                if isinstance(data, dict) and data.get("resourceType"):
                    return "fhir"
            except ValueError:
                pass
            return "json"
        return "raw"

    def _json(self, payload, status):
        return request.make_response(
            json.dumps(payload),
            headers=[("Content-Type", "application/json")],
            status=status)
