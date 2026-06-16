# 06 — Record Rules

Record rules (`ir.rule`) enforce **row-level** access on top of the group CRUD matrix in
[05-security-matrix.md](05-security-matrix.md). They implement multi-tenant isolation (100 clinics) and
minimum-necessary scoping. Domains are expressed in Odoo domain syntax; `global=True` means it applies to
all groups (security floor), otherwise it is attached to specific groups.

---

## 1. Rule design principles

1. **Company isolation is a global floor.** Every PHI model carries a global multi-company rule so no row
   leaks across clinics, regardless of role.
2. **Layered, additive (OR) per-group rules.** Non-global rules for the same model are OR-combined; design
   them so each role gets exactly its slice.
3. **Assignment-based scoping** for clinicians (own/assigned patients), **clinic-wide** for managers.
4. **Patients see only themselves.** Portal rules pin to the linked partner/patient.
5. **State-aware visibility** where required (e.g., patients see only `released` results).

---

## 2. Global rules (apply to everyone)

| Model(s) | Rule name | Domain | Modes |
|----------|-----------|--------|-------|
| all PHI models | Multi-company isolation | `['|',('company_id','=',False),('company_id','in',company_ids)]` | RWCD |
| `mediflow.audit.log` | Append-only | write/unlink denied (perm flags off) | — |
| `mediflow.lab.result` | Released immutability | write denied when `status == 'released'` (combined with state machine) | W |

---

## 3. Role-scoped rules

### Patient (portal) — `group_mediflow_portal_patient`
| Model | Domain | Modes |
|-------|--------|-------|
| patient | `[('id','=', user.patient_id.id)]` | R |
| encounter | `[('patient_id','=', user.patient_id.id)]` | R |
| appointment | `[('patient_id','=', user.patient_id.id)]` | R, C(own), W(reschedule/cancel own) |
| lab.result | `[('order_id.patient_id','=', user.patient_id.id), ('status','=','released')]` | R |
| invoice | `[('patient_id','=', user.patient_id.id), ('state','=','posted')]` | R |
| consent | `[('patient_id','=', user.patient_id.id)]` | R, W |
| document | `[('patient_id','=', user.patient_id.id), ('portal_visible','=',True)]` | R |

> Released-only + consent + `portal_visible` together prevent leakage of preliminary or internal data.

### Reception — `group_mediflow_reception`
| Model | Domain | Modes |
|-------|--------|-------|
| patient | `[('company_id','in',company_ids)]` | CRW |
| appointment | `[('company_id','in',company_ids)]` | CRWD |
| queue.entry | `[('queue_id.company_id','in',company_ids)]` | CRW |
| invoice | `[('company_id','in',company_ids)]` | CR |

### Nurse / Doctor — `group_mediflow_nurse` / `group_mediflow_doctor`
| Model | Domain | Modes |
|-------|--------|-------|
| encounter | `['|',('practitioner_id.user_id','=',user.id),('clinic_id','in',company_ids)]` | CRW |
| patient | `[('company_id','in',company_ids)]` | R (+W nurse/doctor) |
| problem/allergy/vital | `[('encounter_id.clinic_id','in',company_ids)]` | CRW |
| lab.order | `['|',('ordering_practitioner_id.user_id','=',user.id),('clinic_id','in',company_ids)]` | CR(+W doctor) |
| prescription | `[('practitioner_id.user_id','=',user.id)]` create; `[('clinic_id','in',company_ids)]` read | CRW |

> Clinic-wide read enables care continuity within a clinic; cross-clinic requires break-glass (audited).

### Lab tech / verifier — `group_mediflow_lab_tech` / `group_mediflow_lab_verifier`
| Model | Domain | Modes |
|-------|--------|-------|
| lab.order | `[('clinic_id','in',company_ids)]` | RW |
| specimen | `[('order_id.clinic_id','in',company_ids)]` | CRW |
| lab.result | tech: `[('status','=','preliminary'),('clinic_id','in',company_ids)]` write; verifier: `[('status','in',('preliminary','verified')),('clinic_id','in',company_ids)]` write | CRW |

### Pharmacist — `group_mediflow_pharmacist`
| Model | Domain | Modes |
|-------|--------|-------|
| prescription | `[('clinic_id','in',company_ids)]` | RW |
| dispense | `[('clinic_id','in',company_ids)]` | CRW |
| stock.lot (drug) | `[('company_id','in',company_ids)]` | RW |

### Cashier / Insurance — `group_mediflow_cashier` / `group_mediflow_insurance`
| Model | Domain | Modes |
|-------|--------|-------|
| invoice | `[('company_id','in',company_ids)]` | CRW |
| coverage/payer | `[('company_id','in',company_ids)]` | (cashier R) / (insurance CRW) |
| preauth/claim | `[('company_id','in',company_ids)]` | insurance CRW; cashier R |

### Inventory — `group_mediflow_inventory`
| Model | Domain | Modes |
|-------|--------|-------|
| product/lot | `[('company_id','in',company_ids)]` | CRW |
| stock.move/quant | standard Odoo stock rules scoped by company | RW |

### Clinic manager — `group_mediflow_clinic_manager`
| Model | Domain | Modes |
|-------|--------|-------|
| all clinical/revenue | `[('company_id','in',company_ids)]` | R (wide read, no clinical write) |

### Compliance — `group_mediflow_compliance`
| Model | Domain | Modes |
|-------|--------|-------|
| audit.log | `[('company_id','in',company_ids)]` | R |
| all PHI | `[('company_id','in',company_ids)]` | R (read-only oversight) |

---

## 4. Break-glass override

A user temporarily in `group_mediflow_breakglass` gains a widened domain
(`[('company_id','in',company_ids)]` instead of assignment-only) for clinical models. Activation:
- requires reason entry,
- is time-boxed (auto-expires via scheduled job),
- writes `audit.log` with `action='break_glass'` on every record opened during the window.

---

## 5. Validation matrix (must-pass tests in Phase 3)

| Scenario | Expected |
|----------|----------|
| Doctor in Clinic A reads patient of Clinic B | Denied (global isolation) |
| Patient reads another patient's result | Denied |
| Patient reads own `preliminary` result | Denied (released-only) |
| Lab tech writes a `released` result | Denied (state + immutability) |
| Cashier writes a clinical note | Denied (no access right) |
| Break-glass read | Allowed + audit row created |
| Compliance writes audit log | Denied (append-only) |

Each row becomes an automated security test; CI fails if any rule regresses.
