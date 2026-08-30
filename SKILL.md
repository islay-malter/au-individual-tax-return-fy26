---
name: au-itr-assessment-fy26
description: Prepare, review, or sanity-check an Australian individual income tax return for 2025-26 (year ended 30 June 2026) using an intake-first, evidence-reconciled workflow. Use before accountant review, for a myTax preparation check, or for a cautious working estimate. Do not use for another income year or as legal or tax advice.
license: MIT
metadata:
  package-version: "0.1.1"
  sources-last-verified: "2026-08-31"
  reverify-by: "2026-11-30"
---

# AU ITR Assessment FY26

Prepare an evidence-backed working assessment for the Australian `2025-26` income year. This skill supports preparation and review only: do not lodge a return, present the result as tax advice, or imply that it replaces a registered tax agent.

## Package Status And Freshness

The frontmatter fields `package-version`, `sources-last-verified`, and `reverify-by` are the authoritative package status.

At the start of substantive tax work, compare the current date with `reverify-by` in the frontmatter. Through that date, re-verify any mutable official page when it is material to the result. After that date, tell the user the package's source set is expired. Intake, privacy-safe evidence collection, and document organisation may continue, but complete these steps before calculating or making current-rule assertions:

1. Revalidate every material rate, threshold, formula, return label, and record rule against the official sources routed below.
2. Record the new access dates and resolve any change in the references and workflow.
3. Advance the package version, `sources-last-verified`, and `reverify-by`, then run the validator, tests, and shareability preflight.

## Scope And Privacy

- Confirm the income year is `2025-26` before using FY26 settings. If it is another year, stop and use a matching year skill or freshly verify that year's rules.
- Start with intake unless a complete, current-taxpayer profile and evidence set already exist.
- Treat every taxpayer independently. Never reuse another person's facts, documents, assumptions, or output folder.
- Prefer a display name or initials. Never ask for a TFN, myGov credentials, MFA codes, passwords, full bank identifiers, or unrelated identity or medical information.
- Accept redacted documents. Do not reproduce identifiers visible in source documents.
- Read only files the user placed in scope. Keep profiles, tax documents, and generated outputs outside the distributable skill folder unless the user explicitly chooses the private local-config option described in `references/privacy-and-configuration.md`.
- Never write personal facts into `SKILL.md`, `agents/`, `references/`, `scripts/`, tests, or shareable templates.

## Calculation Reliability

This package does not contain a deterministic tax calculator. Unless a separate deterministic tool is explicitly used and named, every tax estimate is a model-produced working scenario.

For every working estimate:

- Show the inputs, formulas, intermediate components, and final reconciliation, keeping income tax, Medicare, study-loan repayment, offsets, credits, withholding, and instalments visible.
- Label the arithmetic status `Unchecked model-produced working scenario` until the result has been recomputed independently of the initial model calculation or compared with myTax or registered-tax-agent output.
- Name the independent method or reviewer, record the comparison, and resolve or surface every material difference before describing the arithmetic as checked or reliable.
- Keep the registered-tax-agent review gates for complex residency, foreign tax, ESS, crypto, trusts, rental, business, deceased-estate, and unusual CGT cases even when the arithmetic has been independently checked.

## Workflow

### 1. Establish The Case

Confirm:

- Current taxpayer and `2025-26` income year.
- Australian tax-residency status: full-year resident, part-year resident, foreign resident, temporary resident, or unresolved.
- Lodgment path: accountant, myTax, amendment, or estimate only.
- Taxpayer working folder and which files are in scope.
- Whether the available ATO material is an official tax-agent pre-filling report, myTax pre-filled data, a saved myTax draft/customer copy, or not yet available.

If residency is not clearly full-year Australian resident, gather evidence but do not apply ordinary resident-rate assumptions without resolving the specialist issues.

### 2. Complete Intake

Read `references/intake-questionnaire.md` and ask questions in small, sensible batches. Use a profile shaped like `assets/templates/client-profile.example.json`; keep unknown booleans as `null` rather than guessing.

Use a package-local `config/client-profile.local.json` only when the user explicitly identifies it as the current taxpayer's config. Read `references/privacy-and-configuration.md` first.

### 3. Produce The Tailored Evidence Checklist

Read `references/evidence-checklists.md` or run the checklist helper resolved relative to this loaded skill directory:

```bash
python3 "<skill-directory>/scripts/build_file_checklist.py" --profile "<profile.json>" --out "<taxpayer-working-folder>/ITR_File_Checklist.md"
```

The first deliverable is normally the file checklist, not a tax estimate. Unknown facts should become the next intake questions, not assumptions that every document category applies.

### 4. Reconcile Evidence

After documents arrive, read `references/assessment-and-reconciliation.md`.

- Build a source register mapping every amount to a document, ATO pre-fill line, or user-confirmed fact.
- Reconcile documents to pre-fill; do not treat pre-fill as proof that an amount is correct or deductible.
- Distinguish official pre-fill from saved myTax draft data.
- Mark absent evidence and unresolved treatments as accountant questions instead of forcing a conclusion.

### 5. Apply FY26 Settings Conservatively

Before any calculation, read both:

- `references/fy26-rates-and-thresholds.md`
- `references/fy26-ato-sources.md`

Use only substantive tax rules enacted and applicable to `2025-26`. Re-verify mutable official pages when a threshold, rate, return label, or record rule is material to the result. Exclude substantive rules that first apply to the `2026-27` income year, while retaining post-year-end lodgment and reporting changes that operate for the FY26 return, such as trust-distribution pre-fill.

Apply the package-freshness gate and calculation-reliability requirements above before producing a working estimate.

Gather evidence and escalate uncertain or complex residency, foreign-tax, ESS, crypto, trust, rental, business, deceased-estate, and unusual CGT cases for registered-tax-agent review. A working scenario may be shown when the assumptions and exclusions are prominent.

### 6. Deliver Status Clearly

Use `references/output-templates.md`. State whether the result is:

- intake or evidence checklist only;
- preliminary because pre-fill or documents are missing;
- source-reconciled working estimate; or
- ready for registered-tax-agent review.

Keep assumptions near the top and separate material tax-dollar issues from factual-consistency or record-hygiene questions.

## Reference Routing

- `references/privacy-and-configuration.md`: personal-data minimisation and optional local profile config.
- `references/intake-questionnaire.md`: taxpayer discovery and profile mapping.
- `references/evidence-checklists.md`: baseline and conditional evidence.
- `references/assessment-and-reconciliation.md`: document classification, source register, calculation gates, and review rules.
- `references/fy26-rates-and-thresholds.md`: confirmed FY26 settings and later-year exclusions.
- `references/fy26-ato-sources.md`: official source register and live-verification rules.
- `references/output-templates.md`: checklist, source register, assessment, and accountant-question structures.
- `references/client-profile.schema.json`: machine-readable profile contract.
- `assets/templates/client-profile.example.json`: blank, share-safe profile.

Before sharing the skill folder, run `scripts/check_shareable.py` and review its findings. Do not include `config/`, taxpayer documents, or generated outputs.
