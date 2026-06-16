# -*- coding: utf-8 -*-
import json
import logging
import re
import time

from odoo import api, models, _

_logger = logging.getLogger(__name__)

# De-identification patterns applied to any text before it leaves the platform.
_REDACTORS = (
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[email]"),
    (re.compile(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b"), "[phone]"),
    (re.compile(r"\b\d{6,}\b"), "[id]"),
)


class MediflowAiService(models.AbstractModel):
    """Single entry point for narrative AI features.

    ``complete()`` resolves the active provider, enforces patient consent for
    external processing, redacts PHI, calls the provider, and records an audit
    row. It NEVER raises into clinical UI — on any failure it returns
    ``ok=False`` so the caller can use a deterministic local fallback.
    """

    _name = "mediflow.ai.service"
    _description = "MEDIFLOW AI Service"

    # ----- public API -----
    @api.model
    def complete(self, feature, system_prompt, user_prompt, patient=None):
        """Return ``{ok, text, status, error}``.

        :param feature: short feature key for auditing (e.g. ``soap_draft``)
        :param patient: optional ``mediflow.patient`` record; when set, external
            processing requires an active data-sharing/treatment consent.
        """
        provider = self.env["mediflow.ai.provider"]._get_active()
        if not provider:
            self._log(feature, provider, "fallback", patient, user_prompt, None,
                      redacted=False)
            return {"ok": False, "status": "fallback", "text": None}

        if patient and not self._external_processing_allowed(patient):
            self._log(feature, provider, "blocked", patient, user_prompt, None,
                      redacted=False, error=_("No active consent for AI processing"))
            return {"ok": False, "status": "blocked", "text": None}

        safe_system = self._redact(system_prompt or "")
        safe_user = self._redact(user_prompt or "")
        result = self._complete_with_provider(provider, safe_system, safe_user)

        status = "ok" if result.get("ok") else "error"
        self._log(feature, provider, status if result.get("ok") else "error",
                  patient, safe_user, result.get("text"), redacted=True,
                  error=result.get("error"), duration_ms=result.get("duration_ms"))
        if not result.get("ok"):
            return {"ok": False, "status": "error", "text": None,
                    "error": result.get("error")}
        return {"ok": True, "status": "ok", "text": result.get("text")}

    # ----- consent / redaction -----
    @api.model
    def _external_processing_allowed(self, patient):
        if self.env.user.has_group("mediflow.group_mediflow_compliance"):
            return True
        return bool(getattr(patient, "has_active_consent", False))

    @api.model
    def _redact(self, text):
        if not text:
            return text
        for pattern, replacement in _REDACTORS:
            text = pattern.sub(replacement, text)
        return text

    # ----- provider transport -----
    @api.model
    def _complete_with_provider(self, provider, system_prompt, user_prompt):
        """Low-level call. Returns ``{ok, text, error, duration_ms}``."""
        try:
            import requests  # noqa: PLC0415
        except ImportError:
            return {"ok": False, "error": "python 'requests' package not available"}

        api_key = provider.sudo().api_key or ""
        if provider.provider_type != "ollama" and not api_key:
            return {"ok": False, "error": "API key not configured"}

        started = time.time()
        try:
            if provider.provider_type == "anthropic":
                payload = self._call_anthropic(requests, provider, api_key,
                                               system_prompt, user_prompt)
            else:
                payload = self._call_openai_compatible(requests, provider, api_key,
                                                       system_prompt, user_prompt)
        except Exception as exc:  # noqa: BLE001 - never propagate to clinical UI
            _logger.warning("MEDIFLOW AI call failed: %s", exc)
            return {"ok": False, "error": str(exc)[:300],
                    "duration_ms": int((time.time() - started) * 1000)}
        payload["duration_ms"] = int((time.time() - started) * 1000)
        return payload

    def _call_openai_compatible(self, requests, provider, api_key, system_prompt, user_prompt):
        base = (provider.api_base_url or "").rstrip("/")
        if not base:
            base = ("http://localhost:11434/v1" if provider.provider_type == "ollama"
                    else "https://api.openai.com/v1")
        url = "%s/chat/completions" % base
        headers = {"Content-Type": "application/json"}
        if api_key:
            if provider.provider_type == "azure_openai":
                headers["api-key"] = api_key
            else:
                headers["Authorization"] = "Bearer %s" % api_key
        body = {
            "model": provider.model_name,
            "temperature": provider.temperature,
            "max_tokens": provider.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        resp = requests.post(url, headers=headers, data=json.dumps(body),
                             timeout=provider.request_timeout or 30)
        resp.raise_for_status()
        data = resp.json()
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content")
        return {"ok": bool(text), "text": (text or "").strip(),
                "error": None if text else "empty response"}

    def _call_anthropic(self, requests, provider, api_key, system_prompt, user_prompt):
        base = (provider.api_base_url or "https://api.anthropic.com").rstrip("/")
        url = "%s/v1/messages" % base
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        body = {
            "model": provider.model_name,
            "max_tokens": provider.max_tokens,
            "temperature": provider.temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        resp = requests.post(url, headers=headers, data=json.dumps(body),
                             timeout=provider.request_timeout or 30)
        resp.raise_for_status()
        data = resp.json()
        blocks = data.get("content") or []
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        return {"ok": bool(text), "text": text.strip(),
                "error": None if text else "empty response"}

    # ----- audit -----
    @api.model
    def _log(self, feature, provider, status, patient, prompt, response,
             redacted=False, error=None, duration_ms=0):
        try:
            self.env["mediflow.ai.request"].sudo().create({
                "feature": feature,
                "provider_id": provider.id if provider else False,
                "model_name": provider.model_name if provider else False,
                "patient_id": patient.id if patient else False,
                "status": status,
                "redacted": redacted,
                "prompt_excerpt": (prompt or "")[:1000],
                "response_excerpt": (response or "")[:1000] if response else False,
                "error_message": (error or "")[:200] if error else False,
                "duration_ms": duration_ms or 0,
            })
        except Exception as exc:  # noqa: BLE001 - logging must never break a feature
            _logger.warning("MEDIFLOW AI audit log failed: %s", exc)
