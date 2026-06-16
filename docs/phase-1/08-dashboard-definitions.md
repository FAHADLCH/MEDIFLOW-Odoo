# 08 — Dashboard Definitions

Analytics for MEDIFLOW (`mediflow_analytics`). Each dashboard lists audience, data source (always a SQL
view or `read_group`, never row-by-row ORM — see scale rules in [03-data-model.md](03-data-model.md) §4),
KPIs with formulas, visualizations, filters, and refresh cadence. Heavy aggregation targets a read
replica (see [09-upgrade-strategy.md](09-upgrade-strategy.md)).

---

## 1. Operational Throughput (Clinic Manager, Reception)

**Source:** `mediflow_v_queue_metrics` (view over `queue.entry` with timestamps).

| KPI | Formula | Viz |
|-----|---------|-----|
| Avg wait time | `avg(called_at - created_at)` per service point | line + gauge |
| Avg service time | `avg(done_at - serving_at)` | bar |
| Patients in queue (live) | count `state in (waiting,called,serving)` | live tile (bus) |
| No-show rate | `no_show / total` | gauge |
| Throughput/hour | count `done` bucketed hourly | heatmap (hour×day) |

Filters: clinic, service point, date range, practitioner. Refresh: live tiles via bus; aggregates 5 min.

---

## 2. Appointment & Utilization (Manager)

**Source:** `mediflow_v_appointment_util`.

| KPI | Formula | Viz |
|-----|---------|-----|
| Slot utilization | `booked_slots / available_slots` | stacked bar per practitioner |
| Cancellation rate | `cancelled / booked` | line |
| No-show rate | `no_show / confirmed` | gauge |
| Lead time | `avg(start - create_date)` | histogram |
| Walk-in ratio | `walk_in / total` | donut |

Filters: clinic, specialty, practitioner, period. Refresh: 15 min.

---

## 3. Lab Diagnostics (Lab Manager, Verifier)

**Source:** `mediflow_v_lab_tat`.

| KPI | Formula | Viz |
|-----|---------|-----|
| Turnaround time (TAT) | `avg(released_at - ordered_at)` by test/panel | bar + P95 line |
| Pending verification | count `status=preliminary` aging | aging buckets |
| Abnormal result rate | `abnormal / total` by test | bar |
| Critical value count | count `critical flagged` | alert tile |
| Sample rejection rate | rejected specimens / received | gauge |

Filters: clinic, test, panel, analyzer, date. Refresh: 5 min; critical tile live.

---

## 4. Pharmacy & Dispensing (Pharmacist, Inventory)

**Source:** `mediflow_v_pharmacy`.

| KPI | Formula | Viz |
|-----|---------|-----|
| Dispense volume | count `dispense.done` | line |
| Avg dispense time | `avg(done_at - ordered_at)` | bar |
| Interaction overrides | count override events | tile (governance) |
| Partial-fill / backorder rate | `partially_dispensed / ordered` | gauge |

Refresh: 15 min.

---

## 5. Inventory & Expiry (Inventory Manager)

**Source:** `mediflow_v_inventory`.

| KPI | Formula | Viz |
|-----|---------|-----|
| Stockout incidents | count lots reaching 0 below min | tile + list |
| Near-expiry exposure | sum value of lots expiring < 90d | bar by category |
| Expired write-off value | sum value expired | tile |
| Reorder triggers | count reorder events | line |
| Inventory turnover | COGS / avg inventory value | gauge |

Refresh: hourly; expiry job daily.

---

## 6. Revenue Cycle (Cashier, Insurance, Manager)

**Source:** `mediflow_v_revenue`, `mediflow_v_claims`.

| KPI | Formula | Viz |
|-----|---------|-----|
| Collections | sum posted payments | line (daily) |
| AR aging | open balance bucketed 0-30/31-60/61-90/90+ | stacked bar |
| Claim denial rate | `denied / submitted` | gauge |
| Days in AR | `AR / (revenue/period_days)` | tile |
| Patient responsibility | sum `patient_resp` | bar |
| Payer mix | revenue by payer | donut |

Filters: clinic, payer, period. Refresh: 30 min; daily reconciliation snapshot.

---

## 7. Clinical Quality (Compliance, Medical Director)

**Source:** `mediflow_v_clinical_quality`, `audit.log`.

| KPI | Formula | Viz |
|-----|---------|-----|
| Encounters completed | count `completed` | line |
| Documentation completeness | `% encounters with required fields` | gauge |
| Break-glass accesses | count `action=break_glass` | governance tile + list |
| Amendment rate (results/encounters) | amended / total | bar |
| Consent coverage | `% active patients with consent` | gauge |

Refresh: hourly; governance tiles surfaced to compliance immediately.

---

## 8. Executive Group Overview (Medical group leadership)

Cross-clinic roll-up (respecting company access of the viewer): patients seen, revenue, utilization,
denial rate, TAT, top clinics by throughput. Multi-company comparison bar charts + map. Refresh: 30 min.

---

## 9. Implementation notes

- Each dashboard = an Odoo `spreadsheet`/dashboard action backed by **named SQL views** (created in
  module `data/` as `ir.model` SQL views or `auto=False` models) for index-friendly aggregation.
- All views filter by `company_id`; the viewer's record rules still apply (no leakage in roll-ups).
- Expensive dashboards run against a **read replica** connection; transactional DB stays unblocked.
- Every KPI has a documented formula here so Phase 3 has no ambiguity and metrics are auditable.
