# SA Systems — Brand Kit (MEDIFLOW)

> Official brand identity for the MEDIFLOW platform, aligned to the SA Systems
> corporate brand. Reference: [www.sasystems.solutions](https://www.sasystems.solutions).
> To update artwork, replace the SVG files in
> `addons/mediflow_theme/static/src/img/` (keep the same file names) and the whole
> platform re-skins automatically.

## Logo assets (vector = infinite resolution)

The mark is the SA Systems **honeycomb "sas" lattice** — a light-grey honeycomb
substrate with red letterforms — paired with the lowercase **`sa systems`** wordmark.

| File | Use |
|------|-----|
| `sa_systems_logo.svg` | Corporate stacked lockup (honeycomb + `sa systems`) for footers, docs, invoices |
| `sa_systems_mark.svg` | Square honeycomb icon mark (favicons, app tiles, avatars) |
| `mediflow_logo.svg` | Product lockup (honeycomb mark + MEDIFLOW) used on login + backend navbar |

Export to PNG at any DPI with: `rsvg-convert -w 1024 sa_systems_mark.svg > mark@1024.png`.

## Color palette

### Corporate (SA Systems)

| Token | Hex | Role |
|-------|-----|------|
| SA Red (primary) | `#E5232A` | Logo, primary brand accent, CTAs |
| Honeycomb Grey | `#DCDDDE` | Logo substrate, dividers |
| Ink Black | `#0B0B0B` | Wordmark, primary text |

### MEDIFLOW product accents

| Token | Hex | Role |
|-------|-----|------|
| Ocean | `#1B5E7E` | Clinical headers, links |
| Mint | `#21C7A8` | Highlights, success, AI features |
| Slate | `#5B7282` | Secondary text, captions |
| Cloud | `#F5F8FA` | App background / surfaces |
| Signal Amber | `#F2A900` | Warnings, near-expiry, pending |
| Signal Red | `#E5484D` | Critical results, denials, errors |

The SA Systems red anchors the corporate identity; the ocean→mint clinical palette
carries the MEDIFLOW product surfaces.

## Typography

- **UI / product:** Segoe UI → Helvetica Neue → Arial → system-ui (no web-font dependency, fast LCP).
- **Wordmark:** lowercase, weight 700, near-black `#0B0B0B`.
- **Headings:** weight 700, tight tracking.
- **Captions / eyebrows:** weight 600, letter-spacing 2–3px, uppercase.

## Voice

Clinical-grade confidence, plain language, outcome-first. We sell **safety, speed, and scale** —
never hype. Every AI claim is paired with a human-in-the-loop safeguard.

## Tagline options

- *MEDIFLOW — Healthcare that flows.*
- *SA Systems — Where business grows smarter.*
- *Clinic to lab to claim — in one secure flow.*

## Company

**SA Systems** · [www.sasystems.solutions](https://www.sasystems.solutions) · info@sasystems.solutions
Offices: Lahore · United Kingdom · United States · ISO 27001 Certified · GDPR Compliant

