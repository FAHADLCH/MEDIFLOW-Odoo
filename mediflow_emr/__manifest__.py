# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW EMR",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "EMR-lite: patients, practitioners, encounters, problems, allergies, vitals",
    "description": """
MEDIFLOW EMR (lite)
===================
Clinical core of the MEDIFLOW platform:

* mediflow.patient            - patient master (bridges res.partner, FHIR Patient)
* mediflow.practitioner       - clinical staff identity (FHIR Practitioner)
* mediflow.encounter          - visit / clinical episode (FHIR Encounter)
* mediflow.problem            - problem / diagnosis list (FHIR Condition)
* mediflow.allergy            - allergy & intolerance (FHIR AllergyIntolerance)
* mediflow.vital.sign         - vitals (FHIR Observation, vital-signs)
* mediflow.immunization       - immunizations (FHIR Immunization)
* mediflow.consent            - consent capture (FHIR Consent)
* mediflow.clinical.document  - structured note / attachment (FHIR DocumentReference)

All models are clinic-scoped, PHI-audited, and (where stateful) governed by the
MEDIFLOW state machine.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": ["mediflow_base", "mediflow_events", "contacts"],
    "data": [
        "security/mediflow_emr_security.xml",
        "security/ir.model.access.csv",
        "data/mediflow_emr_data.xml",
        "views/mediflow_patient_views.xml",
        "views/mediflow_practitioner_views.xml",
        "views/mediflow_encounter_views.xml",
        "views/mediflow_clinical_views.xml",
        "views/mediflow_emr_menus.xml",
    ],
    "installable": True,
    "auto_install": False,
}
