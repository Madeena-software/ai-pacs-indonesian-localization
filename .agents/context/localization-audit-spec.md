---
title: AI-PACS Indonesian Localization Audit — Business & Product Specification
document_id: AI-PACS-ID-LOC-SPEC-001
version: 1.0
status: draft
language: en-US
last_updated: 2026-08-11
authority_note: >
  AI-generated Draft. Becomes repository authority only after explicit approval
  by the designated human authority (repository owner / Madeena Software).
  Downstream executable tasks MUST NOT be published as Validated/Published before
  this document is approved.
---

# AI-PACS Indonesian Localization Audit — Business & Product Specification

## B0 — Business Framing

### Why this work exists

The external AI-PACS web application ("Madeena AI-Assisted Diagnosis System") at
`http://124.225.183.175:8361/` supports an Indonesian locale (`id-ID`). Not all UI strings
are fully translated; many remain in Chinese or English, and some Indonesian strings use
suboptimal phrasing. This creates a usability barrier for Indonesian clinical operators.

Madeena Software requires a structured, evidence-backed list of untranslated or
poorly-translated UI strings so that the AI-PACS vendor or localization team can prioritize
and fix them.

### Business intent

1. Identify AI-PACS UI areas that remain non-Indonesian after the Indonesian locale is active.
2. Identify UI strings that are in Indonesian but use awkward, non-standard, or misleading phrasing.
3. For each finding, suggest the correct or best-practice Indonesian rendering where possible.
4. Provide the AI-PACS team a structured, reviewable `.xlsx` spreadsheet as the primary handoff artifact.
5. Keep the audit **strictly read-only** with respect to PACS data, study records, user management,
   and system configuration.

### Owner

Repository owner / Madeena Software.

### Material constraints

- Plain HTTP transport — credentials are in cleartext on the wire. Authenticated live execution
  must occur only from the user's trusted/authorized network.
- Credentials must never be committed, embedded in source, written to reports, or exposed in screenshots.
- The tool must not save, submit, delete, import, approve, edit, upload, configure, or otherwise
  mutate any business or clinical data on the external system.

---

## P1 — Product Definition

### System identity

**Tool name:** `audit_localization.py` (Python + Playwright CLI)

**Repository:** `Madeena-software/ai-pacs-indonesian-localization`

**Primary output:** `localization_report.xlsx`

### Observed application context

The target application is a UMI-framework React SPA. Key observed facts:

- Login page: `http://124.225.183.175:8361/#/login`
- After login the account role `医生` (Doctor) redirects to `/#/doctor`
- Chest DR study list: `/#/userTable/胸部DR`
- Locale is stored in `localStorage` keys: `umi_locale` (`id-ID`), `i18nextLng` (`id`),
  `lang` (`id`), `locale` (`id-ID`)
- Existing `auth-state.json` has a valid stored session that can be reused
- Application title (from stored theme): "Madeena AI-Assisted Diagnosis System"

### Approved user/system behavior

1. The tool injects Indonesian locale into the browser session (localStorage + Accept-Language
   + browser locale `id-ID`) before navigating, reusing patterns from `pacs_batch.py`.
2. The tool reuses `auth-state.json` if valid; otherwise authenticates fresh and saves new state.
3. The tool traverses the approved read-only navigation surface (§ Navigation Surface).
4. On each route, the tool extracts user-visible UI strings from the DOM and accessibility tree.
5. Each string is classified against the approved classification policy (§ below).
6. Strings classified as `not-indonesian`, `mixed`, or `quality-issue` are recorded as findings.
7. Findings are deduplicated by `(route, text_observed)` — each unique string per route is recorded once.
8. A tightly-cropped or element-level screenshot is captured for each unique finding.
9. The tool exports all findings to `localization_report.xlsx` using the approved schema (§ below).
10. A run summary (routes visited, strings inspected, findings total by classification) is printed to stdout.

### Functional boundaries

| In scope | Out of scope |
|---|---|
| Static UI labels, menu items, tab labels, button text, table headers, placeholder text, dialog text, toast messages, dropdown options, sidebar navigation, form labels, filter panel labels | Patient names, IDs, accession numbers, clinical report text, AI analysis results, diagnostic findings, study metadata values |
| Indonesian locale injection and verification | Modifying AI-PACS translations or locale configuration |
| Read-only navigation: login → `/#/doctor` → `/#/userTable/胸部DR` → menus → viewer modal tabs/labels | Any write/submit/delete/configure operations |
| Localization quality notes (already-Indonesian but poor phrasing) | Clinical interpretation or diagnosis |
| `.xlsx` report generation | Any other output format (future scope) |
| Suggesting correct Indonesian rendering where possible | Guaranteeing translation accuracy |

### Success conditions

- Tool completes a full run against the approved navigation surface without uncaught exceptions.
- Produces a non-empty `localization_report.xlsx` with the correct schema.
- All findings include `element_selector`, `text_observed`, `classification`, and a valid `screenshot_path`.
- Screenshots contain no patient names, IDs, or clinical content.
- Credentials are never written to any generated file.

### Failure behavior

- Network or authentication failure → diagnostic error printed, exit code 2.
- A specific route fails to load → record a `route-error` finding and continue.
- Screenshot capture fails → record finding without screenshot path; do not abort run.

---

## Approved Navigation Surface (MVP-01)

The confirmed post-login navigation flow is:

```
/#/login  →  (submit credentials)  →  /#/doctor  →  /#/userTable/胸部DR
```

| Route ID | URL fragment | Allowed observations | Allowed interactions |
|---|---|---|---|
| `login` | `/#/login` | Field labels, placeholders, button text, page title, language-switcher label | Fill credentials, submit. Read all visible text before submission. |
| `doctor` | `/#/doctor` | All visible text on the landing page, sidebar navigation items, header items, top-menu labels, user-menu text | Open user-menu dropdown to read options. Do not click logout. Expand any collapsed menu sections. |
| `study-list` | `/#/userTable/胸部DR` | Table column headers, toolbar buttons, filter/search placeholders, pagination labels, status dropdown options, any visible filter panel labels | Open visible filter dropdowns to read option text; close after. Paginate if available to verify consistent header labels. Do not click any action button in the study table rows. |
| `viewer-modal` | (opened from one study row in study-list) | Tab labels inside the modal, modal heading, field labels, button labels (Generate Report, Download Report, AI Report, Image Report, etc.) | Click one study row to open the viewer/report modal. Read all visible labels. Do NOT click Generate Report, Download Report, or any control that mutates study data. Close/dismiss modal when done. |

**Explicitly prohibited interactions at all times:**

- Clicking "Generate Report" / "Buat Laporan" or any report-generation trigger.
- Clicking "Download Report" / "Unduh Laporan" or saving any file.
- Editing, deleting, exporting, sending, or recalculating any study record.
- Opening admin, user-management, or system-configuration sections.
- Clicking logout (preserves session for repeated runs).
- Interacting with patient data input forms.

---

## Spreadsheet Output Schema

### Sheet 1: `Findings`

| # | Column | Type | Description |
|---|---|---|---|
| 1 | `finding_id` | string | First 16 hex chars of SHA-256 of `route + "\x00" + element_selector + "\x00" + text_observed`. Stable across repeated runs for the same string/location. |
| 2 | `route` | string | Route ID where observed: `login`, `doctor`, `study-list`, `viewer-modal`. |
| 3 | `element_selector` | string | CSS selector or aria path identifying the element. Helps developers locate the string. |
| 4 | `text_observed` | string | Exact string as extracted from the DOM/accessibility tree. |
| 5 | `classification` | string | One of: `not-indonesian`, `mixed`, `quality-issue`, `uncertain`, `technical-term`. |
| 6 | `expected_indonesian` | string | Recommended correct Indonesian rendering of the string. Empty when no reliable suggestion can be made. |
| 7 | `quality_note` | string | For `quality-issue` strings: free-text note explaining the concern (e.g., "kata kerja tidak baku", "gunakan 'Unduh' bukan 'Download'"). Empty for other classifications. |
| 8 | `screenshot_path` | string | Relative path to evidence screenshot (e.g., `screenshots/login_001.png`). Empty if capture failed. |

### Sheet 2: `Summary`

Single row per run:

| Column | Description |
|---|---|
| `run_timestamp` | ISO-8601 run start time |
| `base_url` | AI-PACS base URL |
| `routes_visited` | Count of distinct routes visited |
| `strings_inspected` | Total DOM strings extracted |
| `findings_total` | Total findings recorded |
| `findings_not_indonesian` | Count: `not-indonesian` |
| `findings_mixed` | Count: `mixed` |
| `findings_quality_issue` | Count: `quality-issue` |
| `findings_uncertain` | Count: `uncertain` |

---

## Classification Policy

Classify conservatively. When uncertain, prefer `uncertain` over asserting a defect.

| Classification | Meaning | Examples |
|---|---|---|
| `not-indonesian` | String entirely in Chinese or English, not a technical term/product name/identifier, and the Indonesian locale is active. | `"用户名"`, `"Login"`, `"Download Report"`, `"Status"` (when Indonesian UI is active) |
| `mixed` | String mixes Indonesian and non-Indonesian text in a way that appears unintentional or incomplete. | `"Unduh Report"` (should be `"Unduh Laporan"`), `"Laporan AI (AI Report)"` |
| `quality-issue` | String is in Indonesian but uses awkward, non-standard, grammatically incorrect, or misleading phrasing. Use `quality_note` to explain the concern and `expected_indonesian` to suggest the corrected form. | `"Masukan kata sandi"` (typo: should be `"Masukkan"`), inconsistent capitalization across similar labels, overly literal translation |
| `uncertain` | Language cannot be confidently determined, or the string is ambiguous between acceptable technical English and a localization gap. | Short strings, mixed-script labels, codes |
| `technical-term` | Approved technical term, product name, acronym, modality code, or identifier that must not be translated. **Not recorded as a finding.** | `"AI"`, `"PACS"`, `"DICOM"`, `"DR"`, `"CR"`, `"CT"`, `"MRI"`, `"JPEG"`, `"PDF"`, `"ID"`, numeric values, dates |

**Exclusions — do not collect:**

- Patient names, patient IDs, accession numbers, study identifiers.
- Clinical report text, AI finding text, diagnostic narratives.
- Pure numeric values, date strings, and measurement units when not part of a static UI label.
- DICOM image canvas content.

---

## Sensitive-data redaction policy

- Use element-level or tightly-cropped screenshots. Full-page screenshots are prohibited when
  the visible area may contain patient or clinical information.
- Before persisting a screenshot, confirm the captured region does not contain patient names,
  patient IDs, clinical findings, or study identifiers.
- If a UI element cannot be captured without exposing clinical content, skip the screenshot
  and record `screenshot_path` as empty.

---

## Secret-handling policy

- Credentials are read from `.env` at runtime and never written to any output file.
- `auth-state.json` and `storage.json` are gitignored and must not be committed.
- No credential material may appear in log output, diagnostics, screenshots, or the spreadsheet.

---

## Context verification

**Status:** Draft — requires explicit approval by repository owner before use as authority.

**Last updated:** 2026-08-11T08:47:00+07:00

**Verified against:** User instructions (conversation), `project.md` v1.1,
`pacs_batch.py` implementation at baseline `a54f5335`,
`auth-state.json` localStorage content (routes, locale keys, account role confirmed).
