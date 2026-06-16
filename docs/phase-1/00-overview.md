# MEDIFLOW ODOO PLATFORM — Phase 1 Master Index

**Document set version:** 1.0
**Status:** Phase 1 — Design & Specification (no runtime code yet)
**Authoring roles:** Healthcare Domain Architect · Odoo Technical Lead · Compliance Product Designer
**Target deployment:** 100 clinics · 1,000,000+ clinical records · multi-tenant, high performance

---

## 1. What Phase 1 delivers

Phase 1 is a **complete, build-ready blueprint**. It does not ship executable Odoo code; it produces the
authoritative design that Phase 2 (scaffolding) and Phase 3 (implementation) will follow without ambiguity.

| # | Deliverable | File |
|---|-------------|------|
| 1 | Product specification | [01-product-specification.md](01-product-specification.md) |
| 2 | User journeys | [02-user-journeys.md](02-user-journeys.md) |
| 3 | Data model | [03-data-model.md](03-data-model.md) |
| 4 | Odoo modules | [04-odoo-modules.md](04-odoo-modules.md) |
| 5 | Security matrix | [05-security-matrix.md](05-security-matrix.md) |
| 6 | Record rules | [06-record-rules.md](06-record-rules.md) |
| 7 | State machines | [07-state-machines.md](07-state-machines.md) |
| 8 | Dashboard definitions | [08-dashboard-definitions.md](08-dashboard-definitions.md) |
| 9 | Upgrade strategy | [09-upgrade-strategy.md](09-upgrade-strategy.md) |

---

## 2. Scope of Phase 1 functional domains

EMR-lite · Appointment scheduling · Queue management · Doctor workflow · Lab workflow ·
Pharmacy · Billing · Insurance · Inventory · Patient portal · Analytics.

## 3. Architecture pillars

- **Odoo custom modules** — clean dependency graph, no monolith; each domain is independently upgradable.
- **FHIR-compatible APIs** — R4 resource mapping at the integration boundary (Patient, Practitioner,
  Encounter, Appointment, Observation, DiagnosticReport, MedicationRequest, Coverage, Invoice).
- **Event-driven integrations** — internal bus (`bus.bus`) + outbound webhook/queue layer for HL7/FHIR
  subscribers, lab analyzers, payment gateways, and SMS/email notification providers.

## 4. Non-functional targets (drive every design choice)

| Dimension | Target |
|-----------|--------|
| Tenancy | 100 clinics, company-segregated (`res.company`) |
| Volume | 1M+ patients/encounters; 10M+ observation rows over time |
| Read latency | P95 < 300 ms on indexed clinical lookups |
| Appointment booking | P95 < 500 ms incl. slot conflict check |
| Availability | 99.9% business-hours; degrade gracefully when analyzers offline |
| Auditability | Every PHI read/write traceable (append-only audit log) |
| Compliance posture | HIPAA-aligned access control, encryption at rest/in transit, minimum-necessary access |

## 5. Reading order

Read `01` → `09` in sequence. The data model (`03`) and module map (`04`) are referenced by every
later document. Security (`05`), record rules (`06`), and state machines (`07`) are the compliance core.

> **Phase boundary:** Work pauses after Phase 1 per instruction. No scaffolding or `.py`/`.xml`
> implementation is produced until Phase 1 is reviewed and signed off.
