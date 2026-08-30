# AU ITR Assessment — FY26

An Agent Skill for preparing, reviewing, or sanity-checking an Australian individual income tax return for the `2025-26` income year (year ended 30 June 2026). It uses an intake-first, evidence-reconciled workflow and is intended to support myTax preparation or accountant review.

This package is FY26-only. It does not lodge returns, provide tax advice, or replace a registered tax agent. Current version and source-verification dates are recorded in the frontmatter at the top of [`SKILL.md`](SKILL.md) and enforced as described under **Package Status And Freshness**.

## Install

Download the repository ZIP, or clone it:

```bash
git clone https://github.com/islay-malter/au-itr-assessment-fy26.git
```

Keep the folder name `au-itr-assessment-fy26` and ensure `SKILL.md` is at the folder root.

For Codex, place the complete folder at:

```text
~/.codex/skills/au-itr-assessment-fy26/
```

Restart or refresh the Agent Skills host if it does not discover the skill immediately. Other compatible hosts may use a different skills directory.

## Safe First Use

Start with the intake and evidence checklist. Confirm the taxpayer and the `2025-26` income year before applying any settings.

- Keep taxpayer profiles, tax documents, and generated outputs outside this repository and distributable skill folder.
- Never commit or share `config/`, `*.local.json`, taxpayer documents, or generated assessments.
- A private `config/client-profile.local.json` is supported only as a local, current-taxpayer file; it is ignored by Git and rejected by the shareability preflight.
- Redact TFNs, myGov credentials, MFA codes, passwords, full bank identifiers, and unrelated identity or medical information.

See [`references/privacy-and-configuration.md`](references/privacy-and-configuration.md) before using a local profile.

## Calculation Limitation

The package does not include a deterministic tax calculator. Unless a separate deterministic tool is explicitly used and named, estimates are model-produced working scenarios. Each estimate must show its inputs, formulas, intermediate components, and reconciliation, and must be labelled `Unchecked model-produced working scenario` until independently recomputed or compared with myTax or registered-tax-agent output.

Complex or uncertain residency, foreign-tax, ESS, crypto, trust, rental, business, deceased-estate, and unusual CGT cases require registered-tax-agent review.

## Validate Before Sharing

From the skill folder, run:

```bash
python3 scripts/check_shareable.py .
python3 -m unittest discover -s tests -v
```

The preflight rejects common private/generated files and fails after the package's `reverify-by` date. Review the final file list manually before publishing or sharing it.

## Licence

Released under the [MIT Licence](LICENSE).
