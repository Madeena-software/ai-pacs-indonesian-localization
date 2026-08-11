---
title: AI-PACS Indonesian Localization Repository Context
document_id: AI-PACS-ID-LOC-CONTEXT-001
version: 1.1
status: draft
language: en-US
last_updated: 2026-08-10
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
`greenfield`

**Relevant summary:**  
As of 2026-08-10, `Madeena-software/ai-pacs-indonesian-localization` was not found in the connected GitHub organization. No repository implementation, accepted baseline, test suite, CI evidence, published executable task, or repository-resident authority artifact can therefore be claimed yet.

A related repository, `Madeena-software/ai-report-download-automation`, contains observed implementation evidence for authenticating to the same AI-PACS application, selecting the Indonesian language, and interacting with Indonesian UI labels. That repository may be used as implementation reference evidence only; it is not authority for this repository's intended behavior.

Existing valid patterns from related tooling should be reused where appropriate rather than re-created without reason, while preserving this repository's narrower localization-audit responsibility and read-only safety boundary.

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

Only repository evidence can pass a quality gate. The target repository does not yet exist, so no gate is currently passed.

| Gate | Status | Evidence / authority |
|---|---|---|
| B0 — Business Framing | `pending` | Initial intent is known, but no approved repository business source exists. |
| P1 — Product Definition | `pending` | No approved PRD or bounded product specification exists. |
| R2 — Requirements Traceability | `pending` | No approved requirement registry or matrices exist. |
| A3 — Architecture Clarity | `pending` | High-level boundaries are recorded here, but no approved architecture authority exists. |
| D4 — Delivery Readiness | `pending` | MVP orientation exists only in supporting context; dependencies and acceptance are not yet approved. |
| T5 — Task Readiness | `pending` | No validated immutable executable task exists. |
| E6 — Execution Verification | `pending` | No target-repository implementation has been executed or verified. |
| V7 — Implementation Review | `pending` | No implementation revision exists to review. |
| R8 — Remediation Closure | `pending` | No reviewed findings/remediation cycle exists. |
| A9 — Baseline Acceptance | `pending` | No accepted immutable repository revision exists. |
| G10 — Release Approval | `pending` | No release candidate or approved internal execution baseline exists. |

**Earliest unmet or materially unreliable gate:**  
`B0 — Business Framing: repository-resident approved business framing has not yet been created.`

### Active task(s)

- None. No validated or published executable task exists for the target repository.

### Blocking items

- Create the target Git repository and initialize its repository instructions/workflow artifacts.
- Promote the agreed localization-audit objective into an approved repository business/product source.
- Define the safe navigation/interaction boundary before an automated crawler is allowed to explore the live AI-PACS UI.

## Accepted baseline

**Accepted baseline:**  
`unknown`

**Accepted scope:**  
No target-repository implementation has been accepted.

**Evidence reference:**  
No acceptance record exists because the target repository was not present at the time of verification.

Branch names, tags, or labels MUST NOT be substituted for an accepted immutable revision once implementation begins.

## Known gaps and open decisions

### Blocking

- Target repository has not yet been created.
  - owner: repository owner / Madeena Software
  - impact: no immutable repository authority, baseline, source, tests, or executable task can yet exist
  - resolution trigger: create and initialize `Madeena-software/ai-pacs-indonesian-localization`

- Safe AI-PACS navigation and interaction policy is not yet formalized.
  - owner: repository/product authority
  - impact: blind crawling could activate state-changing controls on an external medical application
  - resolution trigger: approve a read-only route and interaction allowlist before live crawling

### Non-blocking

- Indonesian localization glossary and approved technical-term allowlist are not yet defined.
  - owner: product/localization authority
  - impact: language classification may produce false positives for acceptable English technical terminology, acronyms, product names, and modality labels
  - resolution trigger: define before final localization-audit acceptance

- Exact spreadsheet schema is not yet approved.
  - owner: product/localization authority
  - impact: generated evidence may require reformatting before external handoff
  - resolution trigger: approve before spreadsheet-export acceptance

- Classification policy for mixed-language, English, Chinese, technical terms, product names, numeric/data content, and uncertain strings is not yet approved.
  - owner: product/localization authority
  - impact: finding counts and severity may not be reproducible
  - resolution trigger: approve before implementation verification

- Screenshot evidence strategy is not yet finalized.
  - owner: implementation/product authority
  - impact: external reviewers may lack sufficient UI context or screenshots may accidentally include unnecessary sensitive data
  - resolution trigger: define redaction/cropping/highlighting rules before live evidence collection

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
`2026-08-10T20:19:00+07:00`

**Verified against repository revision:**  
`not applicable — target repository not yet created`

**Verified sources:**  

- `faliqadlan/code-agent-template/.agents/context/project.md` on `main`, template blob SHA `25c0e6d870f52792dd228959add96baeeac603f3`.
- GitHub repository lookup for `Madeena-software/ai-pacs-indonesian-localization`: repository returned `404 Not Found` at verification time.
- `Madeena-software/ai-report-download-automation` observed Git history, including commit `9f555691cf6e76c554c97655be1f55b565000404` introducing Indonesian language selection and Indonesian UI selectors for the same external AI-PACS application.
- User-approved project objective and observed AI-PACS workflow supplied in the project conversation.

**Known verification limitations:**  

- The target repository does not yet exist, so repository-resident implementation, tests, CI, architecture, requirements, and delivery artifacts cannot be verified.
- The AI-PACS application is an external mutable system; its current route structure, labels, and selectors must be reverified during live execution.
- Prior ChatGPT execution environments could not connect to `124.225.183.175:8361`, so live runtime verification may need to occur from the user's authorized network environment.
