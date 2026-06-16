# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW by SA Systems — Clinic & Diagnostics ERP",
    "summary": "All-in-one healthcare ERP: EMR, appointments, lab, pharmacy, "
               "billing, insurance claims, patient portal, FHIR API, AI assist, "
               "analytics — multi-currency & global-ready.",
    "description": """
MEDIFLOW by SA Systems
======================

The complete, **country-agnostic** Clinic + Diagnostics ERP for Odoo. One install
gives a multi-specialty clinic, hospital outpatient department or reference
laboratory everything it needs — from the front desk to the lab bench to the
revenue cycle — on a secure, audited, FHIR-ready foundation.

Runs from a **single codebase on Odoo 18.0 and 19.0** (Community or Enterprise).
**Multi-currency and multi-company are standard**, and a one-click **Region
Profile** localizes language, currency, timezone and the governing privacy
framework (HIPAA, GDPR, UK GDPR, PDPA, LGPD, PIPEDA, PDPL, DPDP) for any market.

What you get
------------
* **EMR-lite** — patients, practitioners, encounters, problems, allergies,
  vitals, immunizations, consent and clinical documents.
* **Scheduling** — resource-based, conflict-free appointment booking with a
  database-level double-booking guard and a live calendar.
* **Laboratory / Diagnostics** — LOINC test catalog, panels, orders, specimen
  accessioning, verified & released results with hard immutability and critical
  value alerting.
* **Pharmacy** — prescriptions with allergy/interaction checks and FEFO,
  expiry-aware dispensing on real Odoo Inventory stock moves.
* **Billing** — charge capture from clinical events into Odoo Accounting
  invoices, fully multi-currency.
* **Insurance & Claims** — payers, coverage, pre-authorization and the full
  claim lifecycle with patient-responsibility recomputation.
* **Patient Portal** — self-service appointments, consent-gated lab results and
  online invoice payment.
* **Queue Management** — per-service-point tokens with a live waiting board.
* **AI Assist (safety-first)** — explainable no-show prediction, triage acuity
  suggestion and human-reviewed clinical summaries. Predictive features run
  fully offline; narrative features fall back to deterministic templates.
* **FHIR R4 API** — read-oriented, consent-gated Patient, Encounter,
  Observation, DiagnosticReport, MedicationRequest and Coverage resources.
* **Analytics** — operational, clinical and revenue dashboards computed in
  PostgreSQL views, isolated per company.
* **Event-driven integrations** — HMAC-signed webhooks, durable domain events,
  Stripe payment links, Twilio SMS/WhatsApp reminders, telehealth video rooms
  and an authenticated HL7/lab inbound endpoint.
* **SA Systems theme** — branded login, refined backend chrome and high-res
  vector logos.

Security & compliance
---------------------
Every clinical record is company-scoped, PHI-audited (append-only access &
change log) and governed by a guard-protected state machine. National
identifiers and clinical exports are consent-gated. Role-based access spans
reception, nursing, physicians, lab tech/verifier, pharmacist, cashier,
insurance, inventory, compliance and clinic manager.

Built On
--------
Pure Odoo core: ``base``, ``mail``, ``contacts``, ``calendar``, ``account``,
``stock``, ``portal``, ``website`` and ``bus``. No mandatory external Python
dependencies — deploys on Odoo.sh and on-premise alike. Optional connectors
(Stripe, Twilio) activate only when configured.

Compatibility
-------------
Verified on **Odoo 18.0 and 19.0** (Community & Enterprise) from one
series-agnostic codebase.

About SA Systems
----------------
SA Systems builds business software that grows smarter. Offices in Lahore, the
UK and the US. ISO 27001-aligned, GDPR-ready. https://www.sasystems.solutions
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "category": "Healthcare",
    # Series-agnostic version: a bare "2.0.0" installs on Odoo 18 and 19 alike.
    # Odoo prefixes the running series automatically.
    "version": "2.0.0",
    "depends": [
        "mediflow_base",
        "mediflow_events",
        "mediflow_emr",
        "mediflow_appointment",
        "mediflow_lab",
        "mediflow_inventory_ext",
        "mediflow_pharmacy",
        "mediflow_billing",
        "mediflow_insurance",
        "mediflow_queue",
        "mediflow_portal",
        "mediflow_fhir_api",
        "mediflow_analytics",
        "mediflow_localization",
        "mediflow_integrations",
        "mediflow_ai",
        "mediflow_theme",
    ],
    "data": [],
    "images": [
        "static/description/banner.png",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
}
