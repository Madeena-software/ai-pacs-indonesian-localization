---
title: MVP-01 — Build Indonesian Localization Audit Tool (audit_localization.py)
document_id: TASK-MVP01-LOC-AUDIT-001
version: 1.0
status: Accepted
language: en-US
last_updated: 2026-08-11
authority_note: >
  This task is published under the authority of localization-audit-spec.md (Draft,
  approved by designated human authority at conversation 2026-08-11). The Executor
  must not expand scope, invent product requirements, or make architecture decisions
  beyond the boundaries defined here.
---

# Task: MVP-01 — Build Indonesian Localization Audit Tool

## Task identity

**Task title:** MVP-01 — Build Indonesian Localization Audit Tool (`audit_localization.py`)

**Task path:** `.agents/tasks/mvp01-localization-audit-core.md`

**Task contract state:** `Validated/Published`

**Task revision (original):** `.agents/tasks/mvp01-localization-audit-core.md @ 7ea8450`

**Implementation revision reviewed:** `8e48d62`

**Remediation task revision:** `19c224e`

**Accepted implementation revision:** `c1c1c4b`

**Accepted baseline (post-review):** `c1c1c4b`

**Delivery objective:** MVP-01 — Indonesian localization audit baseline

**Owner:** Repository owner / Madeena Software

---

## Delivery context

The repository `ai-pacs-indonesian-localization` exists to audit the Indonesian localization of
the external AI-PACS web application at `http://124.225.183.175:8361/`. Its goal is to identify
UI strings that are not in Indonesian (or are in poor-quality Indonesian) when the Indonesian
locale is active, and to produce an evidence-backed `.xlsx` spreadsheet for the AI-PACS team.

The baseline `a54f5335` contains `pacs_batch.py` — a PDF batch downloader for the same
application. Per user instruction (Option B), `pacs_batch.py` and `test_pacs_batch.py` are
to be **replaced** by the localization auditor. The Executor must use `pacs_batch.py` as an
implementation reference for authentication, locale injection, and browser-session patterns,
then delete it along with `test_pacs_batch.py` once the new code is written and tested.

---

## Baseline and task revision

**Implementation baseline:** `a54f5335f883d905fae951f522781b1b348d4083`

**Task revision:** `resolved when published`
_(See note above.)_

---

## Objective

Implement `audit_localization.py` — a Python + Playwright CLI tool that:

1. Authenticates to AI-PACS (reusing `auth-state.json` session if valid, otherwise logging in fresh).
2. Injects the Indonesian locale into the browser context.
3. Traverses the approved MVP-01 navigation surface (login → `/#/doctor` → `/#/userTable/胸部DR` → viewer modal).
4. Extracts user-visible UI strings (DOM text, accessibility text, placeholders, aria-labels, button labels, etc.).
5. Classifies each string per the approved classification policy.
6. Deduplicates findings by `(route, element_selector, text_observed)`.
7. Captures tightly-cropped element-level screenshots for each unique finding.
8. Exports findings and a run summary to `localization_report.xlsx` with the approved schema.
9. Prints a run summary to stdout.
10. Exits with code `0` on success, `1` if any findings were recorded (non-zero to flag results),
    `2` on fatal error (cannot authenticate, PACS unreachable, etc.).

Additionally:
- Delete `pacs_batch.py` and `test_pacs_batch.py` from the repository root.
- Write `test_audit_localization.py` containing offline unit tests for the classification logic,
  deduplication logic, finding-ID generation, and spreadsheet schema construction.

---

## Authoritative inputs

1. `.agents/context/localization-audit-spec.md` — primary authority for navigation surface,
   schema, classification policy, and safety boundaries. (Draft status; treat as approved per
   user instruction recorded in conversation 2026-08-11.)
2. `.agents/context/project.md` — repository context, boundary rules.
3. `pacs_batch.py` @ `a54f5335` — implementation reference for auth, locale injection,
   browser-session patterns. Not an authority document. To be deleted after new code is written.
4. `auth-state.json` (gitignored, local) — existing Playwright session state to reuse.
5. `.env` (gitignored, local) — credentials (`AI_PACS_USERNAME`, `AI_PACS_PASSWORD`).

---

## Parent delivery objective

MVP-01 — Indonesian localization audit baseline
(described in `.agents/context/project.md` § Delivery state)

---

## Requirement traceability

| Req | Source | Description |
|---|---|---|
| REQ-01 | spec §P1 behavior #1–2 | Inject Indonesian locale; reuse `auth-state.json` |
| REQ-02 | spec §Navigation Surface | Traverse login → `/#/doctor` → `/#/userTable/胸部DR` → viewer modal |
| REQ-03 | spec §P1 behavior #4 | Extract DOM/accessibility UI strings |
| REQ-04 | spec §Classification Policy | Classify strings per policy |
| REQ-05 | spec §P1 behavior #6 | Deduplicate findings by `(route, selector, text)` |
| REQ-06 | spec §P1 behavior #7 | Element-level/tightly-cropped screenshots |
| REQ-07 | spec §Schema | Export `Findings` + `Summary` sheets to `.xlsx` |
| REQ-08 | spec §Redaction | Screenshots must not contain patient/clinical content |
| REQ-09 | spec §Secret-handling | Credentials never written to output |
| REQ-10 | project.md §Boundaries | Audit is strictly read-only |

---

## In-scope behavior

### `audit_localization.py`

- CLI entry point: `python audit_localization.py [options]`
- Key options:
  - `--base-url` (default: `http://124.225.183.175:8361`)
  - `--credentials` (default: `credential.txt`; falls back to `.env` same as `pacs_batch.py`)
  - `--storage-state` (default: `auth-state.json`)
  - `--output` (default: `localization_report.xlsx`)
  - `--screenshots-dir` (default: `screenshots/`)
  - `--headed` (show browser window)
  - `--timeout-ms` (default: `30000`)
  - `--probe-only` (test PACS reachability only, no login)
- Authentication: reuse stored session if valid; fall back to fresh login with credential file.
- Locale injection: set `localStorage` keys `umi_locale=id-ID`, `i18nextLng=id`, `lang=id`,
  `locale=id-ID` and browser context `locale=id-ID` + `Accept-Language: id-ID,id;q=0.9`.
- Route traversal order: login → doctor → study-list → viewer-modal (one study).
- String extraction per route:
  - All visible text nodes, button labels, input placeholders, `aria-label`, `title`, `alt`
    attributes, option text, tab labels, dialog/toast text, menu labels.
  - Skip: hidden elements, pure numeric strings, date strings, strings under 2 characters,
    strings that are only whitespace or punctuation.
- Classification: per spec §Classification Policy. `technical-term` strings are skipped (not recorded).
- Finding ID: first 16 hex chars of `sha256(route + "\x00" + element_selector + "\x00" + text_observed)`.
- Screenshot: use Playwright's `locator.screenshot()` for element-level capture; fall back to
  viewport screenshot with bounding-box crop. Must not include patient table rows.
- Deduplication: same `(route, element_selector, text_observed)` → one finding record.
- Export: `openpyxl` for `.xlsx`. Two sheets: `Findings` and `Summary`.
- Exit codes: `0` success with no findings, `1` success with findings, `2` fatal error.

### `test_audit_localization.py`

Offline unit tests (no live browser) covering:
- Finding ID generation (deterministic SHA-256 prefix).
- Classification logic for representative strings from each class.
- Deduplication logic (same key → one finding; different keys → separate findings).
- `expected_indonesian` and `quality_note` field population.
- Spreadsheet schema: correct sheet names, column order, data types.
- Credential loading (same pattern as existing `test_pacs_batch.py`).

---

## Out-of-scope behavior

- Do NOT implement report PDF download, study data export, or any feature from `pacs_batch.py`
  beyond the reused auth/locale/browser-setup patterns.
- Do NOT click "Generate Report", "Download Report", or any study-mutation button.
- Do NOT navigate to admin, user-management, or system-configuration sections.
- Do NOT use OCR. All text must be extracted via DOM/accessibility interfaces.
- Do NOT store patient names, IDs, accession numbers, or clinical content in any output.
- Do NOT commit `auth-state.json`, `storage.json`, `.env`, screenshots, or the generated `.xlsx`.
- Do NOT rewrite or extend the `.agents/` delivery framework.
- Do NOT implement a localization fix or UI patch tool.
- Do NOT add CI workflow files (separate future task).

---

## Preserved behavior / invariants

- `auth-state.json` gitignore entry must remain intact.
- `.env` gitignore entry must remain intact.
- `reports/`, `diagnostics/`, `__pycache__/` gitignore entries must remain intact.
- `screenshots/` and `localization_report.xlsx` must be added to `.gitignore`.
- The `.agents/` directory and its contents must not be modified.
- The `AGENTS.md` root file must not be modified.

---

## Material dependencies

- Python ≥ 3.10 (available in the user's environment).
- `playwright` Python package (already used by `pacs_batch.py`; must be importable).
- `openpyxl` Python package (for `.xlsx` export; install if not present).
- `auth-state.json` (local, gitignored) — existing valid session preferred; fresh login fallback.
- `.env` (local, gitignored) — `AI_PACS_USERNAME` and `AI_PACS_PASSWORD` populated.
- AI-PACS reachable from the execution host (`http://124.225.183.175:8361/`).

---

## Approved assumptions

- The `auth-state.json` session may be expired; the tool must detect this and re-authenticate.
- The application is a UMI-framework SPA; `umi_locale` is the primary locale key.
- The account role (`医生` / Doctor) always redirects to `/#/doctor` after login.
- Not all Chest DR study list rows will have an openable viewer modal; the tool should open
  the first available row and fall back gracefully if no row is openable.
- The `openpyxl` package may need to be installed; the Executor may install it via pip.

---

## Execution constraints

- Do not run a live browser session unless the user's network can reach `124.225.183.175:8361`.
  Use `--probe-only` first to verify reachability before a full run.
- Do not commit credentials, session state, screenshots, or generated reports.
- Do not click any study-mutation control (Generate Report, Download, Delete, Edit, Export, Send).
- All browser interactions must be confined to the approved navigation surface.

---

## Acceptance criteria

| AC | Criterion | Evidence |
|---|---|---|
| AC-01 | `python audit_localization.py --probe-only` exits 0 when PACS is reachable | Observed command output |
| AC-02 | `python -m pytest test_audit_localization.py -v` passes all tests | Test output, 0 failures |
| AC-03 | `python audit_localization.py` (with valid `.env` and reachable PACS) completes without uncaught exception | Observed run output |
| AC-04 | `localization_report.xlsx` is produced with `Findings` and `Summary` sheets | File inspection |
| AC-05 | `Findings` sheet has exactly the 8 required columns in specified order | Column inspection |
| AC-06 | At least one finding is recorded (the application is known to have untranslated strings) | Row count > 0 in Findings sheet |
| AC-07 | No finding row contains patient names, IDs, or accession numbers in `text_observed` | Manual spot-check of top 20 rows |
| AC-08 | `screenshots/` directory contains at least one PNG per finding that has a non-empty `screenshot_path` | Directory listing |
| AC-09 | `pacs_batch.py` and `test_pacs_batch.py` are deleted | `git status` shows deletion |
| AC-10 | `test_audit_localization.py` exists and passes (AC-02) | Test run |
| AC-11 | `localization_report.xlsx` and `screenshots/` are in `.gitignore` | `.gitignore` inspection |
| AC-12 | `auth-state.json` and `.env` are not staged or committed | `git status` |

---

## Verification requirements

### Automated (must run before reporting completion)

```bash
# 1. Offline unit tests (no PACS connection required)
python -m pytest test_audit_localization.py -v

# 2. Probe PACS reachability
python audit_localization.py --probe-only

# 3. Full audit run (requires PACS reachability)
python audit_localization.py --headed
# (headed mode allows Executor to observe the browser during the run)
```

### Manual inspection

- Open `localization_report.xlsx` and verify Findings and Summary sheets are present.
- Spot-check top 20 Findings rows for absence of patient/clinical content.
- Verify `git status` shows only `audit_localization.py`, `test_audit_localization.py`,
  updated `.gitignore`, and deletion of `pacs_batch.py` + `test_pacs_batch.py`.

---

## Remaining approval requirements

None beyond this task. The user has verbally approved the localization-audit-spec.md
decisions in the planning conversation on 2026-08-11.

---

## Stop conditions

Stop and return to Planner if:

1. The AI-PACS application cannot be authenticated (credentials invalid, network unreachable)
   and the issue cannot be resolved within the task scope.
2. The `/#/doctor` route does not exist or requires a different login flow unknown at
   planning time — return with observed evidence.
3. Playwright is not installed and cannot be installed in the current environment.
4. The viewer modal requires a study row that does not exist (no data) — proceed without
   the viewer-modal route; record the absence in the run summary.
5. Any unexpected data-mutation UI interaction is required to proceed past a route —
   do not execute the interaction; skip the route and return findings from visited routes.

---

## Explicitly authorized side effects

- Create `audit_localization.py` (new file, repository root).
- Create `test_audit_localization.py` (new file, repository root).
- Delete `pacs_batch.py` (repository root).
- Delete `test_pacs_batch.py` (repository root).
- Update `.gitignore` to add `localization_report.xlsx` and `screenshots/`.
- Update `auth-state.json` (local, gitignored) if a fresh login is required.
- Create `screenshots/` directory (local, gitignored) during a live run.
- Create `localization_report.xlsx` (local, gitignored) during a live run.

Git commit is **not** authorized by this task. The Executor should leave changes staged
(or unstaged) for Planner/Reviewer to commit after acceptance.

---

## Expected terminal outcome

A working `audit_localization.py` CLI that, when run against the live AI-PACS application:
- Produces a populated `localization_report.xlsx` with at least one finding.
- Completes without uncaught exceptions.
- Does not expose credentials or patient data.
- Exits with code `1` (findings present) or `0` (no findings).

All offline unit tests in `test_audit_localization.py` pass.

`pacs_batch.py` and `test_pacs_batch.py` are deleted.

`.gitignore` is updated.

---

## Remediation record (added 2026-08-11)

### Review basis

**Reviewed implementation:** `8e48d62` against governing task `7ea8450`.

**Verdict:** REMEDIATION REQUIRED — three bounded findings within the same delivery objective.

### Required corrections

**R-D2 — Viewer modal route not visited**

The live run produced only 3 routes in `routes_visited` (`login`, `doctor`, `study-list`).
The `viewer-modal` route was silently skipped because the `try/except` block at `run_audit()`
swallowed the failure with no diagnostic output. The viewer modal is part of the approved MVP-01
navigation surface.

Required fix:
- In `run_audit()`, before calling `row.click()`, verify at least one `tbody tr` row is visible.
- Log a clear warning to stdout if no clickable row is found (e.g. `"[viewer-modal] No study row available — skipping viewer modal route."`).
- If a row is found and `.click()` raises an exception, log the error class and message.
- Add `"viewer_modal_visited"` boolean to the Summary sheet row.
- Add a corresponding unit test that the Summary dict includes the `viewer_modal_visited` key.

**R-D4 — "Insight" wrongly classified `not-indonesian`**

`"Insight"` is a product name (part of "Insight ChestDR" and "Insight QCDR" module names
as observed in `auth-state.json`). It must be treated as a technical term / product name.

Required fix:
- Add `"Insight"` and `"Insight ChestDR"` and `"Insight QCDR"` to `TECHNICAL_TERMS` set.
- Update the corresponding unit test to confirm `classify_string("Insight")` returns `"technical-term"`.

**R-D3 — "Language" finding missing `expected_indonesian`**

The `"Language"` string (language-switcher trigger on the login page) is classified `not-indonesian`
but has no `expected_indonesian` suggestion.

Required fix:
- Add `"Language": "Bahasa"` to `KNOWN_TRANSLATIONS`.
- Update the corresponding unit test to confirm `classify_string("Language")` returns
  `("not-indonesian", "Bahasa", "")`.

### Verification additions

In addition to all original AC-01 through AC-12, the remediation must satisfy:

| AC | Criterion |
|---|---|
| AC-13 | `python3 -m pytest test_audit_localization.py -v` passes all tests including new ones for R-D2, R-D4, R-D3 |
| AC-14 | After a live run, `routes_visited` in Summary includes `viewer-modal` OR stdout contains a clear skip warning message |
| AC-15 | `"Insight"` is not present in the Findings sheet `text_observed` column |
| AC-16 | If `"Language"` appears in Findings, its `expected_indonesian` cell is `"Bahasa"` |
