# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW AI Assist",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "AI clinical assist: no-show prediction, smart triage, documentation & result summaries",
    "description": """
MEDIFLOW AI Assist
==================
Adds genuine, safety-first AI value across the platform:

* No-show risk prediction on appointments (transparent, explainable scoring)
* Smart triage / acuity suggestion from vitals and chief complaint
* AI-drafted clinical summaries (SOAP) — always human-reviewed, never auto-final
* Plain-language lab result explanations for patients and clinicians
* Pluggable LLM provider (OpenAI-compatible, Azure OpenAI, Anthropic, local Ollama)
* PHI redaction before any external call + consent gating + full request audit

Predictive features run fully offline; narrative features fall back to deterministic
templates when no LLM provider is configured.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "support": "info@sasystems.solutions",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "license": "LGPL-3",
    "depends": [
        "mediflow_base",
        "mediflow_emr",
        "mediflow_appointment",
        "mediflow_lab",
    ],
    "data": [
        "security/mediflow_ai_security.xml",
        "security/ir.model.access.csv",
        "data/mediflow_ai_data.xml",
        "views/mediflow_ai_provider_views.xml",
        "views/mediflow_ai_request_views.xml",
        "views/mediflow_appointment_views.xml",
        "views/mediflow_encounter_views.xml",
        "wizards/mediflow_ai_assistant_views.xml",
        "views/mediflow_ai_menus.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
