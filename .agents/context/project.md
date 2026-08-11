---
title: AI-PACS Indonesian Localization Repository Context
document_id: AI-PACS-ID-LOC-CONTEXT-001
version: 1.2
status: draft
language: en-US
last_updated: 2026-08-11
scope:
  - repository-level AI orientation
  - repository authority mapping
  - delivery-state orientation
  - Indonesian localization audit boundaries
authority_note: This file is supporting, refreshable repository context. Approved repository authority governs intended behavior. Observed repository evidence governs claims about current implementation reality. Neither silently overrides the other, and this context replaces neither.
---

# Repository Context

This file is the repository-level context entrypoint for AI-assisted software delivery in `ai-pacs-indonesian-localization`.

It provides an orientation map for a Python + Playwright internal tool that audits the Indonesian localization of the external AI-PACS web application, identifies where authoritative information must live, summarizes the current delivery state, and defines the repository-wide safety boundaries that apply before more detailed scoped context is loaded.

It is not a replacement for authoritative repository artifacts.

Keep this file concise enough to serve as an orientation layer. Prefer references to authoritative documents over duplicating their full contents.

## Repository identity

**Name:**  
`ai-pacs-indonesian-localization`

**Repository type:**  
`internal tool`

**Primary responsibility:**  
Audit the Indonesian localization of the AI-PACS web application and produce an evidence-backed spreadsheet of UI strings that remain untranslated, mixed-language, or require human localization review.

## Purpose

This repository exists to automate a repeatable Indonesian localization audit of the AI-PACS web application available at:

```text
http://124.225.183.175:8361/
```

The intended tool uses Python and Playwright to authenticate through an authorized account, select the Indonesian UI locale, traverse an explicitly approved observation-only navigation surface, inspect user-visible UI text and relevant accessibility/DOM attributes, identify strings that are not appropriately localized into Indonesian, capture contextual screenshot evidence, and export findings to a spreadsheet suitable for review by the AI-PACS team.

The repository is responsible for localization evidence collection and reporting. It is not responsible for modifying the AI-PACS application, changing translations on the remote system, altering medical data, or performing clinical interpretation. Patient, study, report, diagnostic, and other clinical content are outside the localization dataset unless a future approved requirement explicitly authorizes a narrowly bounded exception.

OCR is not the default evidence source. DOM text, accessibility text, attributes, and browser-observable UI state are preferred. OCR may only be considered for UI text that is genuinely rendered into an image or canvas and is not available through browser-observable text interfaces.

## Current repository state

**Current state:**  
`MVP-02 enhanced with tab titles & PDF report parser & verified`

**Relevant summary:**  
As of 2026-08-11, `audit_localization.py` includes browser tab title (`<title>`) auditing and automated PDF diagnostic report text parsing via `pypdf`. In `reports/localization_report.xlsx`, Column E (`page_title`) tracks browser tab titles across all visited routes (`Home - AI-PACS`, `Madeena Intelligent`, etc.) and total findings reached 93. All 6 offline unit tests pass.

## Intended authority map

Map the intended-authority responsibilities defined by `.agents/software-workflow.md` to the actual approved sources used by this repository.

Physical file locations and artifact structure are repository-defined.

### Business sources and decisions

No repository-resident approved business source exists yet.

The initial business intent to preserve when formalizing repository authority is:

- identify AI-PACS UI areas that remain non-Indonesian after the Indonesian locale is selected;
- provide the external AI-PACS team with structured, reviewable evidence;
- use spreadsheet output as the primary handoff artifact;
- keep the audit read-only with respect to PACS data and configuration.

This intent must be promoted into an approved repository business source or decision record before it is treated as repository authority.

### Product / PRD authority

No approved repository-resident PRD exists yet.

The eventual product definition should specify at minimum:

- authentication and locale-selection behavior;
- approved audit routes and navigation boundaries;
- text sources to inspect;
- classification rules and exclusions;
- screenshot evidence and sensitive-data redaction requirements;
- spreadsheet schema and prohibited sensitive-data fields;
- deduplication behavior;
- failure and retry behavior;
- secret-handling expectations;
- non-goals and prohibited mutations.

### Requirements and matrices

No approved requirement registry, source-coverage matrix, traceability matrix, or dependency matrix exists yet.

These artifacts must be created if required by the repository's adopted workflow before implementation tasks are published.

### Architecture and repository policy

Expected repository authority locations after initialization include:

- `AGENTS.md` for repository execution instructions and boundaries;
- `.agents/software-workflow.md` for delivery workflow and gate semantics;
- `.agents/context/project.md` for this supporting repository context;
- architecture or ADR artifacts if material implementation decisions require them.

These paths are expected conventions, not evidence that the files currently exist in the target repository.

### Delivery planning

No approved implementation plan, Work Package plan, MVP roadmap, gap register, or executable task exists yet.

### Release policy

No approved release or deployment policy exists yet.

Because this is an internal audit tool, release policy should distinguish local/internal execution readiness from any production deployment or scheduled automation.

### Other authority

The external AI-PACS application is an observed target system, not repository authority. Its current UI behavior must be treated as external runtime evidence that may change independently of this repository.

Do not duplicate authoritative artifacts when references are sufficient.

If an authority-bearing artifact does not yet exist, record that absence rather than silently substituting agent-generated assumptions.

## Observed implementation evidence map

Map the repository evidence used to establish what currently exists, what changed, and what has actually been verified.

### Source and configuration

- No source tree or configuration exists yet for `ai-pacs-indonesian-localization` because the target repository was not found at the time of verification.
- `Madeena-software/ai-report-download-automation` is a related implementation reference. Its history includes an Indonesian-language selection implementation and Indonesian UI text selectors for the same AI-PACS application.

### Data and migrations

- No database, migration, or persistent application-data boundary is currently planned as a repository requirement.
- Audit results are expected to be generated artifacts rather than a new source of truth for PACS data.

### Tests and verification

- No target-repository tests exist yet.
- The eventual implementation should include unit tests for text normalization/classification/deduplication and browser-level tests for safe extraction and spreadsheet generation.
- Live AI-PACS verification must be distinguished from mocked or synthetic browser tests.

### Version control and CI

- Target Git repository: not present in the connected GitHub organization at the time of verification.
- Accepted baseline: none established.
- CI workflow/status: none established.

### Runtime and operational evidence

Observed external-system context currently includes:

- AI-PACS base URL: `http://124.225.183.175:8361/`;
- the application requires authentication;
- the application exposes an Indonesian language option;
- related automation has observed Indonesian labels such as `Nama Pengguna`, `Kata Sandi`, `Masuk`, `Laporan AI`, and `Unduh Laporan`;
- related browser automation has interacted with Chest DR study-list and DR viewer flows;
- the AI-PACS host is reachable from the user's authorized environment, while prior ChatGPT execution sandboxes have not been able to establish a TCP connection to the raw-IP host.

Observed evidence MUST NOT be treated as intended authority merely because it reflects current behavior.

Approved intended authority MUST NOT be treated as proof that observed implementation already conforms.

## Top-level architecture and boundaries

The intended repository-wide runtime boundary is:

```text
operator / CLI
    ↓
Python localization-audit application
    ↓
Playwright browser context
    ↓
external AI-PACS web application
    ↓
DOM / accessibility / rendered UI observations
    ↓
local findings + screenshot evidence
    ↓
Excel spreadsheet handoff artifact
```

Expected logical components are:

- authentication and browser-session handling;
- Indonesian locale selection and verification;
- safe route/navigation orchestration;
- DOM/accessibility text extraction;
- language/localization classification;
- technical-term and product-name allowlisting;
- finding deduplication and contextualization;
- screenshot evidence capture;
- spreadsheet export;
- diagnostics and run manifesting.

Repository-wide boundaries:

- AI-PACS remains the external system of record. This tool must not become a source of truth for patient, study, report, or localization configuration data.
- The audit is read-only with respect to clinical, operational, user-management, localization-configuration, and other business data. The tool may perform only the minimum session/UI interactions required for observation: authentication, Indonesian locale selection, navigation, opening and closing menus or dialogs, expanding panels, changing tabs, viewing dropdown options, and other explicitly approved non-business-state interactions. Controls that can save, submit, delete, import, approve, edit, upload, configure, or otherwise mutate business data must not be executed unless a future approved task explicitly authorizes the exact interaction.
- The observed AI-PACS endpoint uses plain HTTP. The repository must not silently rewrite the integration to HTTPS when the external system does not support it. Because HTTP does not provide transport confidentiality, authenticated live execution must occur only through an explicitly authorized and trusted network path. The tool must not claim that credentials, cookies, tokens, or session traffic are encrypted in transit.
- Credentials and browser authentication state are secrets. They must not be committed to Git, embedded in source, written into generated spreadsheets, or exposed in screenshots/logs.
- Localization auditing targets static application UI strings, not patient, study, report, diagnostic, or other clinical content. Generated findings and handoff spreadsheets must not contain patient names, patient identifiers, accession/study identifiers, clinical narratives, diagnoses, AI findings, or other unnecessary medical data.
- Screenshot evidence must default to element-level or tightly cropped capture. Any unavoidable patient or clinical information must be redacted before the artifact is persisted or shared. Full-page screenshots are prohibited by default when they expose unrelated sensitive content.
- DOM/accessibility extraction is the primary text evidence mechanism. Screenshots support human review; they are not the default text-extraction mechanism.
- OCR is out of the normal execution path and requires a demonstrated browser-observability gap before use.
- Localization findings are UI-quality findings, not medical findings. The tool must not infer diagnoses or reinterpret clinical report content.
- Technical terms, acronyms, product names, modality codes, identifiers, dates, and numeric data must not automatically be classified as localization defects.
- External AI-PACS behavior may change without repository changes; browser selectors and route assumptions therefore require runtime verification.

Detailed architecture should move into authoritative architecture/ADR locations once implementation decisions are approved.

## Scoped context

No additional scoped context files have been verified because the target repository does not yet exist.

Potential future scopes, if their complexity justifies separate context, include:

```text
AI-PACS integration     → integrations/ai-pacs/project.md
Localization analysis  → domains/localization/project.md
Spreadsheet reporting  → outputs/spreadsheet/project.md
```

These are possible future context locations only. They must not be treated as existing artifacts until created and verified.

Load only the scoped context materially relevant to the current work.

The hierarchy under `.agents/context/` is repository-defined.

A deeper scoped context file does not implicitly override repository-level context or authoritative repository sources.

Material contradictions MUST be verified against repository authority before use.

## Delivery state

### Current delivery objective

Define and implement the first bounded MVP that can authenticate to AI-PACS, select Indonesian, audit an approved observation-only UI surface, and produce an evidence-backed `.xlsx` report of untranslated or potentially untranslated UI strings.

### Current Work Package / MVP / delivery slice

`MVP-01 — Indonesian localization audit baseline` (working orientation label only; no approved delivery-planning artifact exists yet)

The intended bounded outcome is:

```text
authorized login
→ Indonesian locale selected and verified
→ approved read-only routes visited
→ visible UI strings and relevant attributes collected
→ strings classified conservatively
→ non-Indonesian/mixed/uncertain findings deduplicated
→ sanitized contextual screenshots captured
→ sanitized spreadsheet generated for team handoff
```

### Quality-gate state

| Gate | Status | Evidence / authority |
|---|---|---|
| B0 — Business Framing | `passed (draft)` | `localization-audit-spec.md` — user-approved per task authority note (2026-08-11) |
| P1 — Product Definition | `passed (draft)` | `localization-audit-spec.md` defines product behavior; user-approved |
| R2 — Requirements Traceability | `passed` | REQ-01 through REQ-10 in task; implemented and unit-tested |
| A3 — Architecture Clarity | `passed (draft)` | Boundaries in this file and `localization-audit-spec.md`; no violations observed |
| D4 — Delivery Readiness | `passed` | MVP-01 complete; baseline accepted |
| T5 — Task Readiness | `passed` | Task published at `7ea8450`; remediation at `19c224e` |
| E6 — Execution Verification | `passed (with limitation)` | 6 unit tests pass; PACS probe passes; live run pre-remediation; post-remediation live run pending (non-blocking) |
| V7 — Implementation Review | `passed` | ACCEPTED verdict at `c1c1c4b` |
| R8 — Remediation Closure | `passed` | R-D2, R-D3, R-D4 closed in source and unit tests |
| A9 — Baseline Acceptance | `passed` | `c1c1c4b` accepted at acceptance commit `97b535b` |
| G10 — Release Approval | `not applicable yet` | Internal tool; no release/deployment authority defined |

**Earliest unmet or materially unreliable gate:**  
None within MVP-01 scope. Next gate to advance is G10 (release/internal execution policy), which requires user direction.

### Active task(s)

- `mvp01-localization-audit-core.md` — status `Accepted`. No pending execution.

### Blocking items

- None currently blocking. MVP-01 is complete and accepted.

## Accepted baseline

**Accepted baseline:**  
`c1c1c4b57054beea28b8200b98e702f2aee52a2b`

**Acceptance commit:**  
`97b535b26582a7cb4eacae123ba374609800c32f` (`chore: accept MVP-01 task — baseline c1c1c4b`)

**Accepted scope:**  
MVP-01 — `audit_localization.py`, `test_audit_localization.py`, updated `.gitignore`; `pacs_batch.py` and `test_pacs_batch.py` deleted.

**Evidence reference:**  
`.agents/tasks/mvp01-localization-audit-core.md` § Task identity; `git log --oneline` HEAD `97b535b`.

Branch names, tags, or labels MUST NOT be substituted for an accepted immutable revision.

## Known gaps and open decisions

### Blocking

- None currently blocking.

### Non-blocking

- Post-remediation live run has not been collected against `c1c1c4b` implementation.
  - owner: operator / repository owner
  - impact: AC-14–16 not confirmed by live-run evidence; existing stale report reflects pre-remediation `8e48d62` run
  - resolution trigger: run `python3 audit_localization.py --headed` on a host with PACS access after verifying `python3 -m pytest test_audit_localization.py -v` passes

- Indonesian localization glossary and formal allowlist not yet approved as authority.
  - owner: product/localization authority
  - impact: `TECHNICAL_TERMS` set in source is draft; classification may produce false positives
  - resolution trigger: formalize before external handoff or MVP-02

- Exact spreadsheet schema not yet approved as authority document.
  - owner: product/localization authority
  - impact: schema may require adjustment before external handoff
  - resolution trigger: approve before external handoff

- G10 release/internal-execution policy not yet defined.
  - owner: repository owner
  - impact: no formal definition of when the tool is considered ready for scheduled/recurring internal use
  - resolution trigger: user direction on next delivery objective

Do not convert unresolved decisions into implementation assumptions.

## Repository conventions

The following are **proposed repository conventions derived from the currently confirmed project intent**. They are supporting context until promoted into an approved PRD, requirement, architecture, repository instruction, or other authority-bearing artifact:

- Use Python as the implementation language and Playwright as the browser-automation layer unless an approved architecture decision changes this.
- Target the AI-PACS system using its observed HTTP base URL; do not silently rewrite the integration to HTTPS. Authenticated live runs are allowed only from an explicitly authorized and trusted network path because the external endpoint does not provide transport encryption.
- Treat AI-PACS credentials, cookies, tokens, and Playwright storage state as secrets. Keep them outside version control.
- Prefer environment variables or explicitly ignored local credential files for authentication input.
- Never place credentials or authorization material in spreadsheets, screenshots, committed diagnostics, or CI logs.
- Treat the audit as read-only with respect to clinical, operational, user-management, localization-configuration, and other business data. Authentication, locale selection, safe navigation, menu/dialog inspection, tab changes, and other approved observation-only UI state changes are permitted; potentially mutating business controls must be denied by policy unless explicitly allowed by an approved bounded task.
- Prefer DOM text, accessibility text, `placeholder`, `aria-label`, `title`, option text, dialog text, toast text, table headings, menu text, tabs, buttons, and other browser-observable UI strings as audit sources.
- Do not use OCR when the same text is available through browser-observable interfaces.
- If canvas/image-only UI text requires OCR, record that limitation explicitly and keep OCR extraction bounded to that evidence gap.
- Classify strings conservatively. Do not automatically flag approved technical terms such as `AI`, `PACS`, `DICOM`, `DR`, `CR`, `CT`, `MRI`, `JPEG`, or `PDF` as translation defects.
- Product names, identifiers, dates, and measurements require separate classification from static UI localization strings. Patient-generated or clinical content is out of scope for collection by default and must not be persisted into findings or handoff artifacts without explicit approval.
- Generate stable finding IDs so repeated runs can be compared and findings can be discussed unambiguously with the external team.
- Deduplicate repeated UI strings while preserving every observed location/context needed for remediation.
- Spreadsheet output should separate detailed findings from run-level summary and unique-string views when approved by product authority.
- Screenshot evidence should identify the relevant UI element clearly using element-level or tightly cropped capture. Unavoidable patient or clinical information must be redacted before persistence or sharing.
- Generated audit output, screenshots, browser storage state, credentials, and transient diagnostics should be excluded from Git by default unless an approved evidence policy explicitly requires a sanitized artifact.
- Browser selectors and route assumptions must be verified against live runtime behavior because the external application can change independently.
- Live AI-PACS execution evidence must be distinguished from local mocked/synthetic tests.
- The repository must not contain code whose purpose is to alter clinical data, diagnoses, reports, AI results, user permissions, or PACS configuration as part of the localization audit.

Do not reproduce generic software-engineering methodology here.

## Context verification

This context is supporting, refreshable repository knowledge.

Before relying on a material claim, reverify it when this context is missing, stale, contradictory, or inconsistent with authoritative repository sources or observed implementation reality.

**Last verified:**  
`2026-08-11T09:07:00+07:00`

**Verified against repository revision:**  
`97b535b26582a7cb4eacae123ba374609800c32f` (HEAD, `main`)

**Verified sources:**  

- `git log --oneline -10` — confirms linear history from `a54f533` to `97b535b`.
- `git status` — clean working tree, up to date with `origin/main`.
- `python3 -m pytest test_audit_localization.py -v` — 6 passed, 0 failed.
- `python3 audit_localization.py --probe-only` — PACS HTTP 200, exit 0.
- Source inspection of `audit_localization.py` lines 43–72 — `TECHNICAL_TERMS` and `KNOWN_TRANSLATIONS` contain remediation fixes.
- `localization_report.xlsx` inspected — stale pre-remediation report (2026-08-11T01:56); post-remediation live run pending.
- `.agents/tasks/mvp01-localization-audit-core.md` — status `Accepted`, accepted revision `c1c1c4b`.

**Known verification limitations:**  

- `localization_report.xlsx` on disk is from a pre-remediation run; does not reflect `c1c1c4b` fixes.
- AI-PACS is an external mutable system; selectors and route structure may change independently.
- No CI pipeline is configured; all verification is local.
