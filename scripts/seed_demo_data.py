"""MEDIFLOW sample/demo data seeder. Run via: odoo shell -d mediflow.
Idempotent-ish: skips if patients already seeded (tag in ref).
"""
import logging
from datetime import timedelta, datetime, time
from odoo import fields

_logger = logging.getLogger("mediflow.seed")


def run(env):
    env = env(context=dict(env.context, sm_internal=True, tracking_disable=True))
    Patient = env["mediflow.patient"]

    if Patient.search_count([("first_name", "=", "Aisha"), ("last_name", "=", "Khan")]):
        print(">> Seed data already present — skipping.")
        return

    now = fields.Datetime.now()
    today = fields.Date.context_today(Patient)

    # --- Specialties & practitioners ---
    Spec = env["mediflow.specialty"]
    sp_gp = Spec.create({"name": "General Practice"})
    sp_card = Spec.create({"name": "Cardiology"})
    sp_path = Spec.create({"name": "Pathology"})

    Prac = env["mediflow.practitioner"]
    dr_reed = Prac.create({"name": "Dr. Sarah Reed", "role": "doctor", "specialty_id": sp_gp.id})
    dr_okoro = Prac.create({"name": "Dr. James Okoro", "role": "doctor", "specialty_id": sp_card.id})
    nurse_lee = Prac.create({"name": "Nurse Mia Lee", "role": "nurse"})
    lab_tariq = Prac.create({"name": "Tariq Hassan (Lab)", "role": "lab_tech", "specialty_id": sp_path.id})
    docs = [dr_reed, dr_okoro]

    # --- Patients ---
    people = [
        ("Aisha", "Khan", "female", "1989-03-12", "O+", "+15125550101"),
        ("David", "Mwangi", "male", "1976-07-30", "A+", "+15125550102"),
        ("Elena", "Rossi", "female", "1995-11-05", "B+", "+15125550103"),
        ("Liam", "Murphy", "male", "1968-01-22", "AB+", "+15125550104"),
        ("Sofia", "Garcia", "female", "2001-09-18", "O-", "+15125550105"),
        ("Noah", "Smith", "male", "1983-05-09", "A-", "+15125550106"),
        ("Yuki", "Tanaka", "female", "1992-12-01", "B-", "+15125550107"),
        ("Omar", "Haddad", "male", "1959-04-14", "O+", "+15125550108"),
        ("Grace", "Nguyen", "female", "1974-08-25", "A+", "+15125550109"),
        ("Mateo", "Silva", "male", "2010-02-17", "O+", "+15125550110"),
        ("Fatima", "Ali", "female", "1987-06-03", "AB-", "+15125550111"),
        ("Ethan", "Brown", "male", "1998-10-21", "B+", "+15125550112"),
    ]
    patients = []
    for first, last, gender, bd, bg, phone in people:
        p = Patient.create({
            "first_name": first, "last_name": last, "gender": gender,
            "birthdate": bd, "blood_group": bg, "phone": phone,
            "email": f"{first.lower()}.{last.lower()}@example.com",
        })
        p.write({"state": "active"})
        patients.append(p)

    # Consent on file for all but the last two (so "Missing Consent" filter shows results)
    Consent = env["mediflow.consent"]
    for p in patients[:-2]:
        Consent.create({
            "patient_id": p.id, "scope": "treatment", "state": "active",
            "granted_date": today - timedelta(days=30),
        })

    # --- Lab catalog ---
    Test = env["mediflow.lab.test"]
    t_hgb = Test.create({"name": "Hemoglobin", "code": "HGB", "result_type": "numeric",
                         "loinc_code": "718-7", "uom_name": "g/dL",
                         "ref_low": 12.0, "ref_high": 17.0, "critical_low": 7.0, "critical_high": 20.0})
    t_glu = Test.create({"name": "Glucose, Fasting", "code": "GLU", "result_type": "numeric",
                         "loinc_code": "1558-6", "uom_name": "mg/dL",
                         "ref_low": 70.0, "ref_high": 99.0, "critical_low": 40.0, "critical_high": 400.0})
    t_k = Test.create({"name": "Potassium", "code": "K", "result_type": "numeric",
                       "loinc_code": "2823-3", "uom_name": "mmol/L",
                       "ref_low": 3.5, "ref_high": 5.1, "critical_low": 2.5, "critical_high": 6.5})

    def dt(days, hour, minute=0):
        base = (now + timedelta(days=days)).date()
        return datetime.combine(base, time(hour, minute))

    Appt = env["mediflow.appointment"]

    # --- Past appointments (history for no-show model) ---
    past_plan = [
        (patients[0], dr_reed, -40, 9, "completed", "consult"),
        (patients[0], dr_reed, -20, 9, "no_show", "followup"),
        (patients[1], dr_okoro, -35, 10, "completed", "consult"),
        (patients[3], dr_okoro, -28, 11, "no_show", "followup"),
        (patients[3], dr_okoro, -14, 11, "no_show", "followup"),
        (patients[4], dr_reed, -21, 14, "completed", "consult"),
        (patients[7], dr_okoro, -50, 13, "completed", "procedure"),
        (patients[8], dr_reed, -18, 15, "cancelled", "consult"),
    ]
    for pt, doc, d, h, st, rc in past_plan:
        a = Appt.create({"patient_id": pt.id, "practitioner_id": doc.id,
                         "start": dt(d, h), "stop": dt(d, h) + timedelta(minutes=20),
                         "duration": 20, "reason_code": rc})
        a.write({"state": st})

    # --- Future appointments (these get live no-show risk scores) ---
    future_plan = [
        (patients[0], dr_reed, 1, 9, "confirmed", "followup", False),
        (patients[1], dr_okoro, 1, 10, "booked", "consult", False),
        (patients[2], dr_reed, 2, 11, "booked", "consult", True),
        (patients[3], dr_okoro, 2, 13, "booked", "followup", False),
        (patients[4], dr_reed, 3, 9, "confirmed", "consult", False),
        (patients[5], dr_okoro, 3, 14, "booked", "procedure", False),
        (patients[6], dr_reed, 4, 10, "booked", "lab", True),
        (patients[7], dr_okoro, 5, 11, "confirmed", "followup", False),
        (patients[8], dr_reed, 6, 15, "booked", "consult", False),
        (patients[9], dr_reed, 7, 9, "booked", "consult", False),
        (patients[10], dr_okoro, 8, 13, "booked", "followup", False),
        (patients[11], dr_reed, 0, 16, "booked", "consult", True),
    ]
    for pt, doc, d, h, st, rc, walk in future_plan:
        a = Appt.create({"patient_id": pt.id, "practitioner_id": doc.id,
                         "start": dt(d, h), "stop": dt(d, h) + timedelta(minutes=20),
                         "duration": 20, "reason_code": rc, "walk_in": walk})
        if st != "booked":
            a.write({"state": st})

    # --- Encounters with vitals (some abnormal -> triage suggestions) ---
    Enc = env["mediflow.encounter"]
    Vital = env["mediflow.vital.sign"]

    # 1) Routine completed encounter
    e1 = Enc.create({"patient_id": patients[0].id, "practitioner_id": dr_reed.id,
                     "encounter_type": "ambulatory", "start": dt(-40, 9),
                     "stop": dt(-40, 9) + timedelta(minutes=25),
                     "reason": "Annual check-up"})
    Vital.create({"patient_id": patients[0].id, "encounter_id": e1.id, "measured_at": dt(-40, 9),
                   "measured_by_id": nurse_lee.id, "temperature": 36.7, "pulse": 72,
                   "respiratory_rate": 16, "systolic": 118, "diastolic": 76,
                   "spo2": 98.0, "weight": 64.0, "height": 167.0, "pain_score": 0})
    e1.write({"state": "completed"})

    # 2) In-progress emergency encounter with red-flag vitals (drives emergent acuity)
    e2 = Enc.create({"patient_id": patients[3].id, "practitioner_id": dr_okoro.id,
                     "encounter_type": "emergency", "start": now - timedelta(hours=1),
                     "reason": "Chest pain and shortness of breath"})
    Vital.create({"patient_id": patients[3].id, "encounter_id": e2.id,
                   "measured_at": now - timedelta(minutes=50), "measured_by_id": nurse_lee.id,
                   "temperature": 37.1, "pulse": 118, "respiratory_rate": 24,
                   "systolic": 158, "diastolic": 98, "spo2": 90.0,
                   "weight": 88.0, "height": 178.0, "pain_score": 8})
    e2.write({"state": "in_progress"})

    # 3) Follow-up completed
    e3 = Enc.create({"patient_id": patients[7].id, "practitioner_id": dr_okoro.id,
                     "encounter_type": "followup", "start": dt(-50, 13),
                     "stop": dt(-50, 13) + timedelta(minutes=20),
                     "reason": "Post-procedure review"})
    Vital.create({"patient_id": patients[7].id, "encounter_id": e3.id, "measured_at": dt(-50, 13),
                   "measured_by_id": nurse_lee.id, "temperature": 36.9, "pulse": 80,
                   "respiratory_rate": 18, "systolic": 132, "diastolic": 84,
                   "spo2": 96.0, "weight": 79.0, "height": 175.0, "pain_score": 2})
    e3.write({"state": "completed"})

    # --- Lab orders + results ---
    Order = env["mediflow.lab.order"]
    Result = env["mediflow.lab.result"]
    Specimen = env["mediflow.specimen"]

    # Order A: completed, normal + one critical potassium
    oa = Order.create({"patient_id": patients[3].id, "encounter_id": e2.id,
                       "practitioner_id": dr_okoro.id, "priority": "stat",
                       "order_date": now - timedelta(minutes=45)})
    Specimen.create({"order_id": oa.id, "specimen_type": "blood",
                     "collected_at": now - timedelta(minutes=40),
                     "collected_by_id": nurse_lee.id, "state": "received",
                     "received_at": now - timedelta(minutes=35)})
    ra1 = Result.create({"order_id": oa.id, "test_id": t_hgb.id, "value_numeric": 13.8})
    ra2 = Result.create({"order_id": oa.id, "test_id": t_k.id, "value_numeric": 6.7})  # critical high
    for r in (ra1, ra2):
        r.write({"state": "verified"})
        r.write({"state": "released"})
    oa.write({"state": "resulted"})

    # Order B: in process (no results yet)
    ob = Order.create({"patient_id": patients[0].id, "practitioner_id": dr_reed.id,
                       "priority": "routine", "order_date": now - timedelta(days=1)})
    Specimen.create({"order_id": ob.id, "specimen_type": "serum",
                     "collected_at": now - timedelta(hours=20),
                     "collected_by_id": lab_tariq.id, "state": "received",
                     "received_at": now - timedelta(hours=19)})
    Result.create({"order_id": ob.id, "test_id": t_glu.id, "value_numeric": 92.0})
    ob.write({"state": "in_process"})

    env.cr.commit()
    print(">> MEDIFLOW seed complete:")
    print("   patients:", Patient.search_count([]))
    print("   appointments:", Appt.search_count([]))
    print("   encounters:", Enc.search_count([]))
    print("   lab orders:", Order.search_count([]))
    print("   lab results:", Result.search_count([]))


run(env)  # noqa: F821  (env injected by odoo shell)
