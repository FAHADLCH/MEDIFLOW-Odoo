# MEDIFLOW — Local Test Guide

Run the full MEDIFLOW platform on your machine before any deployment. Two paths:
**Docker (recommended)** or **native Python**.

---

## Option A — Docker (recommended)

Requires Docker Desktop.

```bash
# from the project root
docker compose up -d
# first boot pulls images and starts Odoo 18 + PostgreSQL
docker compose logs -f odoo      # watch until "HTTP service running"
```

1. Open **http://localhost:8069**
2. Create a database:
   - Master Password: `mediflow-admin` (from `config/odoo.conf`)
   - Database name: `mediflow`
   - Email / Password: your admin login
   - **Untick** "Load demonstration data" (or keep it for sample records)
3. After it loads, go to **Apps**, click **Update Apps List**, then search
   `MEDIFLOW` and install **MEDIFLOW Base** — dependencies pull the rest.

### Install everything in one command (faster)

Stop the stack and run a one-shot install of all modules in dependency order:

```bash
docker compose run --rm odoo odoo \
  -d mediflow --without-demo=False --stop-after-init \
  -i mediflow_base,mediflow_events,mediflow_emr,mediflow_appointment,mediflow_queue,mediflow_inventory_ext,mediflow_lab,mediflow_pharmacy,mediflow_billing,mediflow_insurance,mediflow_portal,mediflow_analytics,mediflow_fhir_api,mediflow_theme,mediflow_localization,mediflow_ai,mediflow_integrations
docker compose up -d
```

---

## Option B — Native (Python venv)

Requires Python 3.10+, PostgreSQL 14+, and the Odoo 18 source.

```bash
# 1) Odoo source (once)
git clone --depth 1 -b 18.0 https://github.com/odoo/odoo.git ~/odoo18
python3 -m venv ~/odoo18-venv && source ~/odoo18-venv/bin/activate
pip install -r ~/odoo18/requirements.txt
pip install requests pytz          # used by AI + localization

# 2) PostgreSQL role
createuser -s "$USER" 2>/dev/null || true

# 3) Run, pointing at this repo's addons/
~/odoo18/odoo-bin \
  --addons-path="$HOME/odoo18/addons,$(pwd)/addons" \
  -d mediflow \
  -i mediflow_base,mediflow_events,mediflow_emr,mediflow_appointment,mediflow_queue,mediflow_inventory_ext,mediflow_lab,mediflow_pharmacy,mediflow_billing,mediflow_insurance,mediflow_portal,mediflow_analytics,mediflow_fhir_api,mediflow_theme,mediflow_localization,mediflow_ai,mediflow_integrations
```

Open **http://localhost:8069**.

> To re-apply code changes after editing a module, restart with
> `-u <module_name>` (e.g. `-u mediflow_ai`).

---

## Module load order

Odoo resolves dependencies automatically, but for reference the graph is:

```
mediflow_base
 ├─ mediflow_events
 ├─ mediflow_emr ── mediflow_appointment ── mediflow_queue
 │                   └─ mediflow_lab ── mediflow_pharmacy
 ├─ mediflow_inventory_ext
 ├─ mediflow_billing ── mediflow_insurance
 ├─ mediflow_portal · mediflow_analytics · mediflow_fhir_api
 ├─ mediflow_theme · mediflow_localization
 ├─ mediflow_ai           (base, emr, appointment, lab)
 └─ mediflow_integrations (base, events, emr, appointment, billing)
```

---

## 5-minute smoke test

1. **Branding** — the login screen and navbar show the MEDIFLOW / SA Systems
   theme (ocean→mint gradient).
2. **Region** — *Settings → Technical → MEDIFLOW config → Regions & Compliance*:
   open a profile (e.g. *Saudi Arabia (PDPL)*) and click **Apply to Company**.
3. **Patient & appointment** — create a patient, book an appointment; confirm the
   **No-show Risk** badge appears and the list can group by *Risk Band*.
4. **AI assist** — on an encounter, add vitals, check the **Suggested Acuity**
   badge, then click **AI Draft Summary** (works offline via local template;
   connect a provider under *Config → AI Providers* for LLM output).
5. **AI assistant** — *MEDIFLOW → AI Assist → Clinical Assistant*: pick a patient,
   "Explain recent lab results", **Run**.
6. **Integrations** — *Config → Integrations → Connectors*: add an SMS (Twilio)
   or Telehealth connector; on an appointment use **Telehealth Link** /
   **Send Reminder**.
7. **HL7 inbound** — create an `hl7_lab` connector, copy its **Inbound Token**:
   ```bash
   curl -X POST http://localhost:8069/mediflow/integration/hl7 \
     -H "Authorization: Bearer <INBOUND_TOKEN>" \
     --data-binary $'MSH|^~\\&|LAB|FAC|MEDIFLOW|CLINIC|20260101||ORU^R01|1|P|2.5'
   ```
   Then check *Integrations → Inbound Messages*.
8. **FHIR API** — *Config → FHIR API Tokens*, generate a token, then:
   ```bash
   curl http://localhost:8069/fhir/R4/metadata \
     -H "Authorization: Bearer <FHIR_TOKEN>"
   ```
9. **Portal** — log in as a portal patient user to see appointments,
   consent-gated results, and invoices.

---

## Configuring AI (optional)

Predictive features (no-show, triage) work with **no setup**. For narrative AI:

1. *MEDIFLOW → Config → AI Providers* → create a provider.
2. Choose a type:
   - **OpenAI / Azure / Anthropic** — paste your API key.
   - **Local / Ollama** — run `ollama serve`, set Base URL `http://host.docker.internal:11434/v1`, model e.g. `llama3.1`; **no key, no PHI leaves your machine**.
3. Tick **Active**, click **Test Connection**.

All AI calls are de-identified, consent-checked, and recorded under
*AI Assist → AI Request Log*.

---

## Swapping in your own logo

Replace these files (keep the names) and restart with `-u mediflow_theme`:

```
addons/mediflow_theme/static/src/img/mediflow_logo.svg
addons/mediflow_theme/static/src/img/sa_systems_logo.svg
addons/mediflow_theme/static/src/img/sa_systems_mark.svg
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Apps list empty of MEDIFLOW | Apps → **Update Apps List**; enable developer mode |
| "module not found" | Check `addons_path` includes this repo's `addons/` |
| AI test fails | Expected with no/invalid key — predictive features still work |
| Port 8069 busy | Change the host port mapping in `docker-compose.yml` |
| Reset everything | `docker compose down -v` (wipes the test DB) |
