---
title: MVP-02 — Full-Surface Indonesian Localization Audit Crawler
document_id: TASK-MVP02-LOC-AUDIT-002
version: 1.0
status: Accepted
language: en-US
last_updated: 2026-08-11
authority_note: >
  This task is published under the authority of localization-audit-spec.md and the user-approved
  MVP-02 plan (conversation 2026-08-11). The Executor must observe read-only safety boundaries
  and must not execute state-changing or destructive interactions on the AI-PACS application.
---

# Task: MVP-02 — Full-Surface Indonesian Localization Audit Crawler

## Task identity

**Task title:** MVP-02 — Full-Surface Indonesian Localization Audit Crawler (`audit_localization.py`)

**Task path:** `.agents/tasks/mvp02-full-surface-localization-audit.md`

**Task contract state:** `Accepted`

**Delivery objective:** MVP-02 — Full-Surface Indonesian Localization Audit Coverage

**Owner:** Repository owner / Madeena Software

---

## Delivery context

The baseline MVP-01 audit tool covered only 4 hardcoded routes (`login`, `doctor`, `study-list`, `viewer-modal`). Under MVP-02, the tool will be expanded into a comprehensive localization crawler capable of automatically traversing all accessible navigation menus, sidebar sub-sections, modality tables (`/#/userTable/*`), sub-tabs, filter dropdowns, and informational dialog overlays. This will produce a complete UI text localization report categorized by functional module.

---

## Baseline and task revision

**Implementation baseline:** `c1c1c4b57054beea28b8200b98e702f2aee52a2b` (HEAD commit `97b535b26582a7cb4eacae123ba374609800c32f`)

**Task revision:** `.agents/tasks/mvp02-full-surface-localization-audit.md @ Draft`

---

## Objective

Enhance `audit_localization.py` and `test_audit_localization.py` to:

1. **Dynamically discover & traverse navigation surfaces**:
   - Parse and click all visible sidebar menu items, main navigation links, and sub-category routing under `/#/userTable/*`.
   - Traverse sub-tabs and filter/segment controls on each view.
2. **Expand UI string extraction**:
   - Extract text from dropdown options, select menus, input hints/placeholders, tooltips, sub-table column headers, dialog overlays, and toast/notification messages.
3. **Preserve Read-Only Safety**:
   - Maintain strict read-only execution boundaries: do NOT click submit, delete, export, edit, or data-mutating buttons.
4. **Categorize findings by Module/Route**:
   - Map findings to functional components (e.g., `Authentication`, `Doctor Portal`, `Study List (Chest DR)`, `Viewer Toolbar`, `System Settings`) in `localization_report.xlsx`.
5. **Update offline unit tests**:
   - Ensure `test_audit_localization.py` covers the dynamic menu crawler, component text extraction, and multi-module Excel export schema.

---

## Authoritative inputs

1. `.agents/context/localization-audit-spec.md` — primary authority for navigation rules, schema, classification policy, and safety boundaries.
2. `.agents/context/project.md` — repository context and boundaries.
3. Approved MVP-02 Plan (conversation 2026-08-11).

---

## Parent delivery objective

MVP-02 — Full-Surface Indonesian Localization Audit Coverage

---

## Requirement traceability

| Req | Source | Description |
|---|---|---|
| REQ-11 | MVP-02 Plan §2.A | Dynamic navigation & sub-menu discovery (`/#/userTable/*`, sub-tabs) |
| REQ-12 | MVP-02 Plan §2.B | Comprehensive extraction (dropdown options, hints, tooltips, dialogs) |
| REQ-13 | MVP-02 Plan §2.B | Read-only safety guard (skip mutating controls) |
| REQ-14 | MVP-02 Plan §2.C | Categorize findings by functional module in Excel report |
| REQ-15 | MVP-02 Plan §3 | Unit tests for dynamic crawling, extraction, and schema |

---

## Scope

### In scope

- Update `audit_localization.py` to add dynamic menu/tab discovery and extraction functions.
- Add an explicit read-only interaction allowlist for sub-tabs and informational popups.
- Include `module_name` in Findings sheet in `localization_report.xlsx`.
- Update `test_audit_localization.py` with offline unit tests validating dynamic navigation discovery logic, text extraction, and module categorization.

### Out of scope

- Do NOT perform OCR or image-based text recognition.
- Do NOT click any button that submits forms, edits settings, deletes studies, or triggers data downloads.
- Do NOT commit `localization_report.xlsx`, `screenshots/`, or session state files.

### Preserved behavior

- Keep existing classification rules (`TECHNICAL_TERMS`, `KNOWN_TRANSLATIONS`, hex finding IDs) intact.
- Keep `--probe-only`, `--headed`, `--output`, and CLI options fully compatible.
- All existing unit tests in `test_audit_localization.py` must continue to pass.

---

## Execution constraints

- All browser interactions must adhere to read-only safety.
- All tests in `test_audit_localization.py` must be runnable offline (`python3 -m pytest test_audit_localization.py -v`).

---

## Acceptance criteria

| AC | Criterion | Evidence |
|---|---|---|
| AC-17 | `python3 -m pytest test_audit_localization.py -v` passes all tests | Test output, 0 failures |
| AC-18 | `audit_localization.py` includes dynamic discovery of navigation menus and sub-tabs | Code inspection |
| AC-19 | `audit_localization.py --probe-only` exits 0 | Command output |
| AC-20 | `localization_report.xlsx` Findings sheet includes `module_name` column for enhanced categorization | Column inspection |
| AC-21 | Mutating/destructive buttons are explicitly filtered out during crawling | Code inspection / safety check |

---

## Verification requirements

### Automated checks

```bash
python3 -m pytest test_audit_localization.py -v
python3 audit_localization.py --probe-only
```

---

## Explicitly authorized side effects

- Modify `audit_localization.py` (repository root).
- Modify `test_audit_localization.py` (repository root).

Git commit is **not** authorized by this task.

---

## Expected terminal outcome

A fully enhanced `audit_localization.py` crawler that dynamically discovers all accessible routes and sub-tabs, safely extracts UI strings, categorizes findings by module, and passes all unit tests in `test_audit_localization.py`.
