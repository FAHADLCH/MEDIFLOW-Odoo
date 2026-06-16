# -*- coding: utf-8 -*-
"""FHIR R4 serializers.

Each function projects one Odoo record into a FHIR R4 resource ``dict``. Mapping
lives here at the API boundary only (docs/phase-1/03-data-model.md §5); the ORM
models remain relational. Functions are pure and side-effect free so they can be
unit-tested without a request context.
"""

# Clinic-scoped identifier system URN. A real deployment would derive this per
# company; kept stable here so MRNs round-trip as Patient.identifier.
MRN_SYSTEM = "urn:mediflow:mrn"
NATIONAL_ID_SYSTEM = "urn:mediflow:national-id"
LOINC_SYSTEM = "http://loinc.org"
ATC_SYSTEM = "http://www.whocc.no/atc"
RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"


def _ref(resource_type, res_id):
    return {"reference": "%s/%s" % (resource_type, res_id)} if res_id else None


def _instant(dt):
    """Odoo Datetime (naive UTC) -> FHIR instant string."""
    return dt.isoformat() + "Z" if dt else None


def _date(d):
    return d.isoformat() if d else None


# ---------------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------------
def patient_to_fhir(patient, include_national_id=False):
    identifiers = [{
        "use": "usual",
        "system": MRN_SYSTEM,
        "value": patient.mrn,
    }]
    # national_id is a secondary identifier and only surfaces when the caller is
    # explicitly permitted (compliance/admin), mirroring the storage-side group.
    if include_national_id and patient.national_id:
        identifiers.append({
            "use": "secondary",
            "system": NATIONAL_ID_SYSTEM,
            "value": patient.national_id,
        })
    telecom = []
    if patient.phone:
        telecom.append({"system": "phone", "value": patient.phone})
    if patient.email:
        telecom.append({"system": "email", "value": patient.email})
    resource = {
        "resourceType": "Patient",
        "id": str(patient.id),
        "identifier": identifiers,
        "active": patient.state == "active",
        "name": [{
            "use": "official",
            "family": patient.last_name or "",
            "given": [patient.first_name] if patient.first_name else [],
        }],
        "gender": patient.gender or "unknown",
    }
    if patient.birthdate:
        resource["birthDate"] = _date(patient.birthdate)
    if telecom:
        resource["telecom"] = telecom
    if patient.state == "deceased":
        resource["deceasedBoolean"] = True
    return resource


# ---------------------------------------------------------------------------
# Practitioner
# ---------------------------------------------------------------------------
def practitioner_to_fhir(practitioner):
    resource = {
        "resourceType": "Practitioner",
        "id": str(practitioner.id),
        "active": True,
        "name": [{"text": practitioner.name or ""}],
    }
    if getattr(practitioner, "license_number", False):
        resource["identifier"] = [{
            "system": "urn:mediflow:license",
            "value": practitioner.license_number,
        }]
    return resource


# ---------------------------------------------------------------------------
# Encounter
# ---------------------------------------------------------------------------
_ENCOUNTER_STATUS = {
    "planned": "planned",
    "in_progress": "in-progress",
    "completed": "finished",
    "amended": "finished",
    "cancelled": "cancelled",
}


def encounter_to_fhir(encounter):
    resource = {
        "resourceType": "Encounter",
        "id": str(encounter.id),
        "status": _ENCOUNTER_STATUS.get(encounter.state, "unknown"),
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB" if encounter.encounter_type != "emergency" else "EMER",
        },
        "subject": _ref("Patient", encounter.patient_id.id),
    }
    if encounter.practitioner_id:
        resource["participant"] = [{
            "individual": _ref("Practitioner", encounter.practitioner_id.id),
        }]
    period = {}
    if encounter.start:
        period["start"] = _instant(encounter.start)
    if encounter.stop:
        period["end"] = _instant(encounter.stop)
    if period:
        resource["period"] = period
    if encounter.reason:
        resource["reasonCode"] = [{"text": encounter.reason}]
    return resource


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------
_APPT_STATUS = {
    "booked": "booked",
    "confirmed": "booked",
    "in_consult": "arrived",
    "completed": "fulfilled",
    "cancelled": "cancelled",
    "no_show": "noshow",
}


def appointment_to_fhir(appointment):
    resource = {
        "resourceType": "Appointment",
        "id": str(appointment.id),
        "status": _APPT_STATUS.get(appointment.state, "pending"),
        "start": _instant(appointment.start),
        "end": _instant(appointment.stop),
        "participant": [
            {"actor": _ref("Patient", appointment.patient_id.id), "status": "accepted"},
        ],
    }
    if appointment.practitioner_id:
        resource["participant"].append({
            "actor": _ref("Practitioner", appointment.practitioner_id.id),
            "status": "accepted",
        })
    if appointment.reason:
        resource["description"] = appointment.reason
    return resource


# ---------------------------------------------------------------------------
# Observation (lab result and vital sign)
# ---------------------------------------------------------------------------
_OBS_STATUS = {
    "preliminary": "preliminary",
    "verified": "preliminary",
    "released": "final",
    "amended": "amended",
    "cancelled": "cancelled",
}

_INTERPRETATION = {
    "low": ("L", "Low"),
    "high": ("H", "High"),
    "critical_low": ("LL", "Critical low"),
    "critical_high": ("HH", "Critical high"),
}


def lab_result_to_fhir(result):
    code = {"text": result.test_id.name or ""}
    if result.loinc_code:
        code["coding"] = [{
            "system": LOINC_SYSTEM,
            "code": result.loinc_code,
            "display": result.test_id.name or "",
        }]
    resource = {
        "resourceType": "Observation",
        "id": str(result.id),
        "meta": {"versionId": str(result.version or 1)},
        "status": _OBS_STATUS.get(result.state, "unknown"),
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory",
            }],
        }],
        "code": code,
        "subject": _ref("Patient", result.patient_id.id),
    }
    if result.released_at:
        resource["effectiveDateTime"] = _instant(result.released_at)
    if result.value_text:
        resource["valueString"] = result.value_text
    elif result.value_numeric:
        resource["valueQuantity"] = {
            "value": result.value_numeric,
            "unit": result.uom_name or "",
        }
    if result.abnormal_flag and result.abnormal_flag != "normal":
        code_disp = _INTERPRETATION.get(result.abnormal_flag)
        if code_disp:
            resource["interpretation"] = [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": code_disp[0],
                    "display": code_disp[1],
                }],
            }]
    if result.ref_low or result.ref_high:
        resource["referenceRange"] = [{
            "low": {"value": result.ref_low} if result.ref_low else None,
            "high": {"value": result.ref_high} if result.ref_high else None,
        }]
    return resource


def vital_sign_to_fhir(vital):
    resource = {
        "resourceType": "Observation",
        "id": "vital-%s" % vital.id,
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
            }],
        }],
        "code": {"text": dict(vital._fields["vital_type"].selection).get(
            vital.vital_type, vital.vital_type) if "vital_type" in vital._fields else "Vital"},
        "subject": _ref("Patient", vital.patient_id.id),
    }
    if getattr(vital, "measured_at", False):
        resource["effectiveDateTime"] = _instant(vital.measured_at)
    if getattr(vital, "value_numeric", False):
        resource["valueQuantity"] = {
            "value": vital.value_numeric,
            "unit": getattr(vital, "uom_name", "") or "",
        }
    return resource


# ---------------------------------------------------------------------------
# DiagnosticReport (lab order, references its observations)
# ---------------------------------------------------------------------------
_REPORT_STATUS = {
    "ordered": "registered",
    "collected": "partial",
    "received": "partial",
    "in_process": "partial",
    "resulted": "preliminary",
    "completed": "final",
    "cancelled": "cancelled",
}


def lab_order_to_fhir(order):
    resource = {
        "resourceType": "DiagnosticReport",
        "id": str(order.id),
        "status": _REPORT_STATUS.get(order.state, "unknown"),
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                "code": "LAB",
            }],
        }],
        "code": {"text": order.name or "Lab Order"},
        "subject": _ref("Patient", order.patient_id.id),
        "result": [
            _ref("Observation", r.id)
            for r in order.result_ids.filtered(lambda x: x.state == "released")
        ],
    }
    if getattr(order, "order_date", False):
        resource["effectiveDateTime"] = _instant(order.order_date)
    return resource


# ---------------------------------------------------------------------------
# MedicationRequest (prescription)
# ---------------------------------------------------------------------------
_MEDREQ_STATUS = {
    "draft": "draft",
    "ordered": "active",
    "partially_dispensed": "active",
    "dispensed": "completed",
    "handed_over": "completed",
    "cancelled": "cancelled",
}


def _medication_codeable(line):
    product = line.product_id
    coding = []
    atc = getattr(product, "atc_code", False)
    rxnorm = getattr(product, "rxnorm_code", False)
    if atc:
        coding.append({"system": ATC_SYSTEM, "code": atc})
    if rxnorm:
        coding.append({"system": RXNORM_SYSTEM, "code": rxnorm})
    cc = {"text": product.display_name or ""}
    if coding:
        cc["coding"] = coding
    return cc


def prescription_to_fhir(prescription):
    lines = prescription.line_ids
    first = lines[:1]
    resource = {
        "resourceType": "MedicationRequest",
        "id": str(prescription.id),
        "status": _MEDREQ_STATUS.get(prescription.state, "unknown"),
        "intent": "order",
        "subject": _ref("Patient", prescription.patient_id.id),
        "dosageInstruction": [],
    }
    if first:
        resource["medicationCodeableConcept"] = _medication_codeable(first)
    for line in lines:
        dosage = {"text": line.instructions or ""}
        if getattr(line, "route", False):
            dosage["route"] = {"text": line.route}
        resource["dosageInstruction"].append(dosage)
    return resource


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------
def coverage_to_fhir(coverage):
    resource = {
        "resourceType": "Coverage",
        "id": str(coverage.id),
        "status": "active" if coverage.is_active else "cancelled",
        "subscriberId": coverage.member_id or "",
        "beneficiary": _ref("Patient", coverage.patient_id.id),
        "payor": [_ref("Organization", coverage.payer_id.id)] if coverage.payer_id else [],
        "order": {"primary": 1, "secondary": 2, "tertiary": 3}.get(
            coverage.priority, 1),
    }
    if coverage.plan_name:
        resource["class"] = [{
            "type": {"coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/coverage-class",
                "code": "plan",
            }]},
            "value": coverage.plan_name,
        }]
    return resource


# ---------------------------------------------------------------------------
# Bundle helpers
# ---------------------------------------------------------------------------
def make_bundle(resources, bundle_type="searchset"):
    return {
        "resourceType": "Bundle",
        "type": bundle_type,
        "total": len(resources),
        "entry": [{"resource": r} for r in resources],
    }


def operation_outcome(severity, code, diagnostics):
    return {
        "resourceType": "OperationOutcome",
        "issue": [{
            "severity": severity,
            "code": code,
            "diagnostics": diagnostics,
        }],
    }
