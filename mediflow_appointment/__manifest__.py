# -*- coding: utf-8 -*-
{
    "name": "MEDIFLOW Appointments",
    "version": "2.0.0",
    "category": "Healthcare/MEDIFLOW",
    "summary": "Scheduling: resources, schedules, slots, appointments, booking engine",
    "description": """
MEDIFLOW Appointments
=====================
Resource-based scheduling with conflict-free booking:

* mediflow.resource           - room / equipment (FHIR Location/Device)
* mediflow.schedule           - practitioner / resource working schedule
* mediflow.appointment.slot   - bookable slot (FHIR Slot)
* mediflow.appointment        - appointment (FHIR Appointment)

A database-level exclusion prevents double-booking the same practitioner or
resource for the same start time. State transitions are governed by the MEDIFLOW
state machine and emit domain events.
""",
    "author": "SA Systems",
    "maintainer": "SA Systems",
    "website": "https://sasystems.solutions/custom-web-app-development",
    "support": "info@sasystems.solutions",
    "license": "LGPL-3",
    "depends": ["mediflow_emr", "calendar"],
    "data": [
        "security/mediflow_appointment_security.xml",
        "security/ir.model.access.csv",
        "data/mediflow_appointment_data.xml",
        "views/mediflow_resource_views.xml",
        "views/mediflow_schedule_views.xml",
        "views/mediflow_appointment_views.xml",
        "views/mediflow_appointment_menus.xml",
    ],
    "installable": True,
    "auto_install": False,
}
