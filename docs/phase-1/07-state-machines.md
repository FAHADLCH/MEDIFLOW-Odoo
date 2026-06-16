# 07 — State Machines

Lifecycle definitions for every stateful entity. Each machine lists states, allowed transitions, guards
(who/what), side effects (events emitted), and immutability rules. Transitions are enforced in a shared
`StateMachineMixin` (in `mediflow_base`) so they cannot be bypassed by direct writes, and each transition
writes an audit entry.

---

## 1. Appointment — `mediflow.appointment`

```mermaid
stateDiagram-v2
  [*] --> booked
  booked --> confirmed: verify / check-in
  booked --> cancelled: cancel(reason)
  booked --> no_show: grace elapsed (cron)
  confirmed --> in_consult: encounter opened
  confirmed --> cancelled: cancel(reason)
  in_consult --> completed: encounter closed
  cancelled --> [*]
  no_show --> [*]
  completed --> [*]
```

| Transition | Guard | Side effect |
|-----------|-------|-------------|
| →booked | reception/portal; slot free (DB constraint) | `appointment.booked`; lock slot |
| booked→confirmed | reception (check-in) | enqueue to reception/triage queue |
| →cancelled | reception/portal; not completed | free slot; `appointment.cancelled` |
| booked→no_show | cron after grace | `appointment.no_show` |
| confirmed→in_consult | doctor opens encounter | create encounter |
| in_consult→completed | encounter completed | `appointment.completed` |

---

## 2. Encounter — `mediflow.encounter`

```mermaid
stateDiagram-v2
  [*] --> planned
  planned --> in_progress: doctor opens
  in_progress --> completed: close (mandatory fields valid)
  in_progress --> cancelled: cancel(reason)
  completed --> amended: addendum(version+1)
```

| Transition | Guard | Side effect |
|-----------|-------|-------------|
| in_progress→completed | required fields present; orders saved | capture charges → draft invoice; `encounter.completed` |
| completed→amended | doctor; creates linked addendum, original immutable | new version; `encounter.amended` |

**Immutability:** `completed` encounters are read-only except addendum; never hard-edited.

---

## 3. Lab order — `mediflow.lab.order`

```mermaid
stateDiagram-v2
  [*] --> ordered
  ordered --> collected: specimen taken
  collected --> received: accessioned
  received --> in_process: analyzer/manual
  in_process --> resulted: results entered
  resulted --> completed: all results released
  ordered --> cancelled: cancel(reason)
```

Side effects: `lab.order.created` on create; routes to lab queue; `collected`/`received` update specimen.

---

## 4. Lab result — `mediflow.lab.result` (critical immutability)

```mermaid
stateDiagram-v2
  [*] --> preliminary
  preliminary --> verified: verifier review
  preliminary --> cancelled: reject(reason)
  verified --> released: authorized release
  released --> amended: correction(version+1, replaces_id)
```

| Transition | Guard | Side effect |
|-----------|-------|-------------|
| →preliminary | lab tech / analyzer | abnormal flag computed vs reference range |
| preliminary→verified | `lab_verifier` only | — |
| verified→released | `lab_verifier`/authorized | `lab.result.released` → portal + FHIR DiagnosticReport; doctor notified |
| any→ (critical value) | auto-detect | `lab.critical.flagged` immediate alert (independent of state) |
| released→amended | verifier; original kept | new version row; `lab.result.amended` |

**Hard rule:** no transition or field write is permitted on a `released` row except creating an amended
successor. Enforced by mixin + record rule + DB write guard.

---

## 5. Prescription — `mediflow.prescription`

```mermaid
stateDiagram-v2
  [*] --> draft
  draft --> ordered: doctor signs (interaction/allergy checked)
  ordered --> partially_dispensed: partial fill
  ordered --> dispensed: full fill
  partially_dispensed --> dispensed: remainder filled
  dispensed --> handed_over: counseled
  ordered --> cancelled: cancel(reason)
```

Guards: `draft→ordered` blocked on unresolved allergy/interaction unless override+reason (audited).
Side effects: `prescription.created`; on dispense → inventory move + billing charge.

---

## 6. Dispense — `mediflow.dispense`

```mermaid
stateDiagram-v2
  [*] --> draft
  draft --> confirmed: lot selected (FEFO, not expired)
  confirmed --> done: stock move validated
  draft --> cancelled
```

Guard: expired/ insufficient lot blocked by constraint. Side effect: `pharmacy.dispensed`,
`inventory.move.done`, charge capture.

---

## 7. Invoice — `account.move` (MEDIFLOW usage)

```mermaid
stateDiagram-v2
  [*] --> draft
  draft --> posted: confirm charges
  posted --> paid: payment(s) reconciled
  posted --> cancelled: void(reason)
  paid --> refunded: credit note
```

Side effects: `invoice.posted`, `payment.received`. Insurance split computed at `draft→posted`.

---

## 8. Pre-authorization — `mediflow.preauth`

```mermaid
stateDiagram-v2
  [*] --> requested
  requested --> approved: payer response
  requested --> denied: payer response
  requested --> expired: validity elapsed (cron)
```

---

## 9. Claim — `mediflow.claim`

```mermaid
stateDiagram-v2
  [*] --> draft
  draft --> submitted: build & send
  submitted --> adjudicated: remittance received
  adjudicated --> paid: payer payment posted
  adjudicated --> denied: rejection(reason code)
  denied --> appealed: rework
  appealed --> submitted
```

Side effects: `claim.submitted`, `claim.adjudicated`, `claim.denied`. Patient responsibility recomputed
on adjudication → patient balance on invoice.

---

## 10. Queue entry — `mediflow.queue.entry`

```mermaid
stateDiagram-v2
  [*] --> waiting
  waiting --> called: call-next
  called --> serving: started
  serving --> done: completed
  waiting --> no_show: skipped after retries
  called --> waiting: recycle (missed)
```

Side effects: every transition pushes a `bus.bus` message → live board; `queue.entry.*` events.

---

## 11. Patient — `mediflow.patient`

```mermaid
stateDiagram-v2
  [*] --> draft
  draft --> active: verified
  active --> inactive: dormant
  active --> deceased: recorded(date)
  active --> merged: dedupe merge(target)
  inactive --> active: reactivate
```

`merged` patients become read-only pointers to the surviving record (audit-logged merge).

---

## 12. Cross-cutting enforcement

- All transitions go through `StateMachineMixin.transition(target, reason=None)` which validates the
  allowed map, checks the caller's group, writes audit, then emits the event.
- Illegal direct `write({'state': ...})` is rejected by an override that consults the transition map.
- Terminal/immutable states (`released`, `completed`, `merged`, `paid`) are write-guarded at ORM level.
