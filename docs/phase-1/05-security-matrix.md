# 05 — Security Matrix

Defines security groups, the CRUD access matrix (`ir.model.access.csv` intent), PHI handling, audit, and
the compliance controls that enforce **minimum-necessary** access. Record-level scoping is in
[06-record-rules.md](06-record-rules.md).

---

## 1. Security groups (roles)

Groups are layered under category **MEDIFLOW**. Higher roles inherit lower where sensible.

| Group (xml id) | Role | Inherits |
|----------------|------|----------|
| `group_mediflow_portal_patient` | Patient (portal) | base portal |
| `group_mediflow_reception` | Receptionist / front desk | internal user |
| `group_mediflow_nurse` | Nurse / MA | reception (clinical-lite) |
| `group_mediflow_doctor` | Doctor / Practitioner | nurse |
| `group_mediflow_lab_tech` | Lab technician | internal user |
| `group_mediflow_lab_verifier` | Pathologist / verifier | lab_tech |
| `group_mediflow_pharmacist` | Pharmacist | internal user |
| `group_mediflow_cashier` | Billing / cashier | internal user |
| `group_mediflow_insurance` | Insurance coordinator | cashier |
| `group_mediflow_inventory` | Inventory manager | internal user |
| `group_mediflow_clinic_manager` | Clinic manager | doctor + cashier (read-wide) |
| `group_mediflow_compliance` | Compliance officer (audit read) | internal user |
| `group_mediflow_admin` | MEDIFLOW administrator | all (config) |

---

## 2. CRUD access matrix (model × role)

Legend: **C**reate **R**ead **W**rite **D**elete · `–` none · `R*` own/assigned only (enforced by record rule).

| Model | Patient | Recep | Nurse | Doctor | LabTech | Verifier | Pharm | Cashier | Insurance | Inventory | Manager | Compliance | Admin |
|-------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| patient | R* | CRW | CRW | CRW | R* | R* | R* | R | R | – | R | R | CRWD |
| encounter | R* | CR | CRW | CRW | R | R | R* | R | R | – | R | R | CRWD |
| problem/allergy/vital | R* | R | CRW | CRW | R | R | R* | – | – | – | R | R | CRWD |
| appointment | CR*W* | CRWD | CRW | CRW | – | – | – | R | – | – | R | R | CRWD |
| queue.entry | R* | CRW | CRW | RW | RW | – | RW | – | – | – | R | R | CRWD |
| lab.order | R* | – | CR | CRW | RW | RW | – | R | – | – | R | R | CRWD |
| lab.result | R* (released) | – | R | R | CRW(prelim) | RW(verify/release) | – | R | – | – | R | R | CRWD |
| prescription | R* | – | R | CRW | – | – | RW | R | – | – | R | R | CRWD |
| dispense | R* | – | – | R | – | – | CRW | R | – | R | R | R | CRWD |
| product/lot (drug) | – | – | – | R | R | – | RW | – | – | CRWD | R | R | CRWD |
| invoice (account.move) | R* | CR | – | R | – | – | R | CRW | RW | – | R | R | CRWD |
| charge.item | R* | R | R | R | – | – | R | CRW | R | – | R | R | CRWD |
| payer/coverage | R* | CR | – | R | – | – | – | RW | CRW | – | R | R | CRWD |
| preauth/claim | R* | – | – | R | – | – | – | R | CRW | – | R | R | CRWD |
| audit.log | – | – | – | – | – | – | – | – | – | – | R | R | R |
| event | – | – | – | – | – | – | – | – | – | – | R | R | CRWD |
| config (catalogs, schedules) | – | R | R | R | R | R | R | R | R | R | RW | R | CRWD |

**Notes**
- `audit.log` is **read-only for everyone** (compliance/manager/admin) — no Create/Write/Delete via ORM;
  rows are written by the audit mixin through a privileged sudo path only.
- `lab.result` Create/Write is **state-bounded**: tech writes only `preliminary`; verifier transitions
  `verified`→`released`; nobody writes `released` rows (state machine + record rule, see `06`/`07`).
- Patient (portal) never has write on clinical data; only on own appointment booking/cancel and consent.

---

## 3. PHI handling & minimum-necessary

- **Field-level protection:** `national_id` and other sensitive identifiers are encrypted at rest and
  masked in list views; full value visible only to `reception`/`admin` with audit on read.
- **Minimum-necessary by record rule:** roles see only records tied to their clinic + their assignment
  (e.g., doctor sees patients with an encounter/appointment assigned to them or shared in their clinic).
- **Break-glass:** an emergency override group flag allows a clinician to open a record outside normal
  scope; the access is **always** logged to `audit.log` with `action=break_glass` + mandatory reason.
- **Consent gating:** portal exposure and FHIR export of a patient's data require an active
  `mediflow.consent`; absence blocks the read at the controller/serializer layer.

---

## 4. Audit (append-only)

Every model using the PHI audit mixin records to `mediflow.audit.log`:

| Captured | Detail |
|----------|--------|
| Who | `user_id`, source IP, session |
| What | `model`, `res_id`, `patient_id` |
| Action | read / create / write / unlink / state-change / break_glass / export |
| When | `timestamp` |
| Why | `reason` (mandatory for break_glass, export, override) |
| Change | `field_changes` jsonb (old→new, PHI values redacted/hashed) |

Audit rows cannot be modified or deleted through any UI/API path. Retention + cold-storage rollover is a
scheduled job; legal hold prevents archival.

---

## 5. API & authentication security

- FHIR API uses **OAuth2 client-credentials / SMART-on-FHIR style scopes** (`patient/*.read`,
  `Observation.read`, etc.); tokens are clinic-scoped.
- Rate limiting + IP allowlist on integration controllers; HMAC-signed inbound webhooks.
- All endpoints enforce the same record rules as the UI (no privileged bypass except audited sudo paths).
- Secrets via environment/secret manager — never in source or DB plaintext.

---

## 6. Compliance control checklist

- [ ] Every PHI model uses audit mixin + `company_id`.
- [ ] No model grants global cross-company read of PHI.
- [ ] Released/signed clinical records are immutable (state machine enforced).
- [ ] Break-glass requires reason and is logged.
- [ ] Portal/FHIR PHI exposure is consent-gated.
- [ ] Sensitive identifiers encrypted + masked.
- [ ] Audit log append-only and retained per policy.
