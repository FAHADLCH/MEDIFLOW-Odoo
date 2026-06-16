# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW FHIR R4 API",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "FHIR R4 REST API: Patient, Encounter, Observation, DiagnosticReport, MedicationRequest, Coverage",
    "description": """
MEDIFLOW FHIR R4 API
====================
Read-oriented FHIR R4 boundary for MEDIFLOW. The mapping lives entirely in this
module's serializers (docs/phase-1/03-data-model.md §5): Odoo models stay relational
and FHIR resources are *projected on read*. Storage is never coupled to the wire format.

Resources
---------
* Patient           <- mediflow.patient        (MRN -> identifier; national_id consent-gated)
* Practitioner      <- mediflow.practitioner
* Encounter         <- mediflow.encounter
* Appointment       <- mediflow.appointment
* Observation       <- mediflow.lab.result / mediflow.vital.sign  (LOINC CodeableConcept)
* DiagnosticReport  <- mediflow.lab.order      (references its Observations)
* MedicationRequest <- mediflow.prescription   (ATC/RxNorm CodeableConcept, dosageInstruction)
* Coverage          <- mediflow.coverage

Design
------
* Versioned resources expose ``meta.versionId`` from the model ``version`` field.
* PHI export is consent-gated: a resource for a patient without an active consent
  is refused (HTTP 403) unless the caller holds the compliance/admin group.
* Token bearer auth via ``mediflow.fhir.token`` (opaque, hashed at rest, scoped,
  expiring). This is a pragmatic stand-in for full SMART-on-FHIR/OAuth2, which the
  upgrade strategy schedules for a later phase.
* Every endpoint is company-scoped through the authenticated user's allowed companies.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": [
        "mediflow_emr",
        "mediflow_lab",
        "mediflow_appointment",
        "mediflow_pharmacy",
        "mediflow_insurance",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/mediflow_fhir_security.xml",
        "views/mediflow_fhir_token_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
