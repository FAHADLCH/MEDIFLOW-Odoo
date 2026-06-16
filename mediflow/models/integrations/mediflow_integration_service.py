# -*- coding: utf-8 -*-
import logging
import secrets

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class MediflowIntegrationService(models.AbstractModel):
    """Dispatcher for outbound integrations. Each method resolves the active
    connector, performs the call defensively, writes an audit log row, and
    returns a result dict. Failures are logged, never raised into the UI."""

    _name = "mediflow.integration.service"
    _description = "MEDIFLOW Integration Service"

    # ----- helpers -----
    @api.model
    def _requests(self):
        try:
            import requests  # noqa: PLC0415
            return requests
        except ImportError:
            return None

    @api.model
    def _log(self, integration, direction, channel, reference, status,
             request=None, response=None, error=None, patient=None):
        try:
            self.env["mediflow.integration.log"].sudo().create({
                "integration_id": integration.id if integration else False,
                "integration_type": integration.integration_type if integration else channel,
                "direction": direction,
                "channel": channel,
                "reference": reference,
                "patient_id": patient.id if patient else False,
                "status": status,
                "request_excerpt": (request or "")[:1000] if request else False,
                "response_excerpt": (response or "")[:1000] if response else False,
                "error_message": (error or "")[:200] if error else False,
            })
            if integration and status == "ok":
                integration.sudo().last_used = fields.Datetime.now()
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Integration log failed: %s", exc)

    @api.model
    def _ping(self, integration):
        if integration.integration_type == "telehealth":
            return True
        requests = self._requests()
        if not requests or not integration.base_url:
            return bool(integration.sudo().auth_token)
        try:
            resp = requests.get(integration.base_url, timeout=10)
            return resp.status_code < 500
        except Exception:  # noqa: BLE001
            return False

    # ----- SMS / WhatsApp (Twilio) -----
    @api.model
    def send_sms(self, to_number, body, patient=None, whatsapp=False):
        itype = "whatsapp_twilio" if whatsapp else "sms_twilio"
        integration = self.env["mediflow.integration"]._get_active(itype)
        if not integration or not to_number:
            self._log(integration, "outbound", itype, to_number, "skipped",
                      error="not configured" if not integration else "no recipient",
                      patient=patient)
            return {"ok": False, "reason": "not_configured"}
        requests = self._requests()
        if not requests:
            self._log(integration, "outbound", itype, to_number, "error",
                      error="requests unavailable", patient=patient)
            return {"ok": False, "reason": "requests_unavailable"}

        sid = integration.sudo().auth_token or ""
        token = integration.sudo().auth_secret or ""
        sender = integration.from_identifier or ""
        to = ("whatsapp:%s" % to_number) if whatsapp else to_number
        sender = ("whatsapp:%s" % sender) if whatsapp and not sender.startswith("whatsapp:") else sender
        url = "https://api.twilio.com/2010-04-01/Accounts/%s/Messages.json" % sid
        try:
            resp = requests.post(url, data={"From": sender, "To": to, "Body": body},
                                 auth=(sid, token), timeout=20)
            ok = resp.status_code in (200, 201)
            self._log(integration, "outbound", itype, to_number,
                      "ok" if ok else "error", request=body,
                      response=resp.text, patient=patient,
                      error=None if ok else "HTTP %s" % resp.status_code)
            return {"ok": ok}
        except Exception as exc:  # noqa: BLE001
            _logger.warning("SMS send failed: %s", exc)
            self._log(integration, "outbound", itype, to_number, "error",
                      request=body, error=str(exc), patient=patient)
            return {"ok": False, "reason": str(exc)}

    # ----- Payments (Stripe) -----
    @api.model
    def create_payment_link(self, invoice):
        integration = self.env["mediflow.integration"]._get_active("payment_stripe")
        amount = getattr(invoice, "mediflow_patient_responsibility", 0) or invoice.amount_residual
        if not integration or amount <= 0:
            self._log(integration, "outbound", "payment_stripe", invoice.name, "skipped",
                      error="not configured or zero amount")
            return {"ok": False, "reason": "not_configured"}
        requests = self._requests()
        if not requests:
            return {"ok": False, "reason": "requests_unavailable"}

        secret = integration.sudo().auth_token or ""
        currency = (invoice.currency_id.name or "usd").lower()
        data = {
            "mode": "payment",
            "success_url": (integration.base_url or "https://example.com") + "/paid",
            "cancel_url": (integration.base_url or "https://example.com") + "/cancel",
            "line_items[0][quantity]": "1",
            "line_items[0][price_data][currency]": currency,
            "line_items[0][price_data][unit_amount]": str(int(round(amount * 100))),
            "line_items[0][price_data][product_data][name]":
                "%s - %s" % (invoice.name, invoice.company_id.name),
            "client_reference_id": invoice.name or str(invoice.id),
        }
        try:
            resp = requests.post("https://api.stripe.com/v1/checkout/sessions",
                                 data=data, headers={"Authorization": "Bearer %s" % secret},
                                 timeout=20)
            payload = resp.json()
            url = payload.get("url")
            ok = bool(url)
            self._log(integration, "outbound", "payment_stripe", invoice.name,
                      "ok" if ok else "error", request=str(amount),
                      response=resp.text[:500],
                      error=None if ok else "no url returned")
            return {"ok": ok, "url": url}
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Payment link failed: %s", exc)
            self._log(integration, "outbound", "payment_stripe", invoice.name, "error",
                      error=str(exc))
            return {"ok": False, "reason": str(exc)}

    # ----- Telehealth (no external credentials required) -----
    @api.model
    def create_video_room(self, label="visit"):
        token = secrets.token_urlsafe(9)
        slug = "".join(c for c in (label or "visit") if c.isalnum()) or "visit"
        integration = self.env["mediflow.integration"]._get_active("telehealth")
        base = (integration.base_url if integration else None) or "https://meet.jit.si"
        url = "%s/MEDIFLOW-%s-%s" % (base.rstrip("/"), slug[:24], token)
        self._log(integration, "outbound", "telehealth", label, "ok", response=url)
        return {"ok": True, "url": url}
