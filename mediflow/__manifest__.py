# -*- coding: utf-8 -*-
{
    "name": 'MEDIFLOW by SA Systems — Clinic & Diagnostics ERP',
    "summary": 'All-in-one healthcare ERP: EMR, appointments, lab, pharmacy, billing, insurance claims, patient portal, FHIR API, AI assist, analytics — multi-currency & global-ready.',
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
    "license": "OPL-1",
    "price": 199.00,
    "currency": "USD",
    "category": "Healthcare",
    # Series-agnostic: a bare "2.0.0" installs on Odoo 18 and 19 alike.
    "version": "2.0.0",
    "depends": ['base', 'mail', 'contacts', 'calendar', 'account', 'stock', 'portal', 'website', 'bus', 'web'],
    "data": [
        'security/base/mediflow_security.xml',
        'security/base/ir.model.access.csv',
        'data/base/mediflow_data.xml',
        'views/base/mediflow_audit_log_views.xml',
        'views/base/mediflow_menus.xml',
        'security/events/ir.model.access.csv',
        'data/events/mediflow_events_cron.xml',
        'views/events/mediflow_event_views.xml',
        'views/events/mediflow_webhook_views.xml',
        'views/events/mediflow_events_menus.xml',
        'security/emr/mediflow_emr_security.xml',
        'security/emr/ir.model.access.csv',
        'data/emr/mediflow_emr_data.xml',
        'views/emr/mediflow_patient_views.xml',
        'views/emr/mediflow_practitioner_views.xml',
        'views/emr/mediflow_encounter_views.xml',
        'views/emr/mediflow_clinical_views.xml',
        'views/emr/mediflow_emr_menus.xml',
        'security/appointment/mediflow_appointment_security.xml',
        'security/appointment/ir.model.access.csv',
        'data/appointment/mediflow_appointment_data.xml',
        'views/appointment/mediflow_resource_views.xml',
        'views/appointment/mediflow_schedule_views.xml',
        'views/appointment/mediflow_appointment_views.xml',
        'views/appointment/mediflow_appointment_menus.xml',
        'security/lab/mediflow_lab_security.xml',
        'security/lab/ir.model.access.csv',
        'data/lab/mediflow_lab_data.xml',
        'views/lab/mediflow_lab_test_views.xml',
        'views/lab/mediflow_lab_panel_views.xml',
        'views/lab/mediflow_lab_order_views.xml',
        'views/lab/mediflow_specimen_views.xml',
        'views/lab/mediflow_lab_result_views.xml',
        'views/lab/mediflow_lab_menus.xml',
        'data/inventory_ext/mediflow_inventory_data.xml',
        'views/inventory_ext/product_views.xml',
        'views/inventory_ext/stock_lot_views.xml',
        'views/inventory_ext/mediflow_inventory_menus.xml',
        'security/pharmacy/mediflow_pharmacy_security.xml',
        'security/pharmacy/ir.model.access.csv',
        'data/pharmacy/mediflow_pharmacy_data.xml',
        'views/pharmacy/mediflow_dispense_views.xml',
        'views/pharmacy/mediflow_prescription_views.xml',
        'views/pharmacy/mediflow_pharmacy_menus.xml',
        'security/billing/mediflow_billing_security.xml',
        'security/billing/ir.model.access.csv',
        'data/billing/mediflow_billing_data.xml',
        'views/billing/mediflow_charge_master_views.xml',
        'views/billing/mediflow_charge_item_views.xml',
        'views/billing/account_move_views.xml',
        'views/billing/mediflow_encounter_views.xml',
        'views/billing/mediflow_billing_menus.xml',
        'security/insurance/mediflow_insurance_security.xml',
        'security/insurance/ir.model.access.csv',
        'data/insurance/mediflow_insurance_data.xml',
        'views/insurance/mediflow_payer_views.xml',
        'views/insurance/mediflow_coverage_views.xml',
        'views/insurance/mediflow_preauth_views.xml',
        'views/insurance/mediflow_claim_views.xml',
        'views/insurance/mediflow_insurance_menus.xml',
        'security/queue/mediflow_queue_security.xml',
        'security/queue/ir.model.access.csv',
        'data/queue/mediflow_queue_data.xml',
        'views/queue/mediflow_queue_views.xml',
        'views/queue/mediflow_queue_entry_views.xml',
        'views/queue/mediflow_queue_menus.xml',
        'security/portal/mediflow_portal_security.xml',
        'views/portal/portal_templates.xml',
        'security/fhir_api/ir.model.access.csv',
        'security/fhir_api/mediflow_fhir_security.xml',
        'views/fhir_api/mediflow_fhir_token_views.xml',
        'security/analytics/ir.model.access.csv',
        'security/analytics/mediflow_analytics_security.xml',
        'views/analytics/mediflow_v_queue_metrics_views.xml',
        'views/analytics/mediflow_v_appointment_util_views.xml',
        'views/analytics/mediflow_v_lab_tat_views.xml',
        'views/analytics/mediflow_v_revenue_views.xml',
        'views/analytics/mediflow_v_claims_views.xml',
        'views/analytics/mediflow_v_clinical_quality_views.xml',
        'views/analytics/mediflow_analytics_menus.xml',
        'security/localization/ir.model.access.csv',
        'data/localization/mediflow_region_profiles.xml',
        'views/localization/mediflow_region_profile_views.xml',
        'views/localization/mediflow_localization_menus.xml',
        'security/integrations/mediflow_integrations_security.xml',
        'security/integrations/ir.model.access.csv',
        'views/integrations/mediflow_integration_views.xml',
        'views/integrations/mediflow_integration_log_views.xml',
        'views/integrations/mediflow_integration_message_views.xml',
        'views/integrations/mediflow_appointment_views.xml',
        'views/integrations/mediflow_integration_menus.xml',
        'security/ai/mediflow_ai_security.xml',
        'security/ai/ir.model.access.csv',
        'data/ai/mediflow_ai_data.xml',
        'views/ai/mediflow_ai_provider_views.xml',
        'views/ai/mediflow_ai_request_views.xml',
        'views/ai/mediflow_appointment_views.xml',
        'views/ai/mediflow_encounter_views.xml',
        'wizards/ai/mediflow_ai_assistant_views.xml',
        'views/ai/mediflow_ai_menus.xml',
        'views/theme/login_templates.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "mediflow/static/src/scss/mediflow_backend.scss",
        ],
        "web.assets_frontend": [
            "mediflow/static/src/scss/mediflow_frontend.scss",
        ],
    },
    "images": ["static/description/banner.png"],
    "application": True,
    "installable": True,
    "auto_install": False,
}
