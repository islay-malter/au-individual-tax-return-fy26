# AU ITR Assessment — FY26

An Agent Skill for preparing, reviewing, or sanity-checking an Australian individual income tax return for the `2025-26` income year (year ended 30 June 2026). It uses an intake-first, evidence-reconciled workflow and is intended to support myTax preparation or accountant review.

This package is FY26-only. It does not lodge returns, provide tax advice, or replace a registered tax agent.

**The packaged source set expires.** The `reverify-by` date in the [`SKILL.md`](SKILL.md) frontmatter is the authoritative expiry. Past that date the skill will still run intake, evidence collection, and document organisation, but it will refuse to calculate or assert current rules until the official sources are revalidated and the dates advanced. The shareability preflight fails after the same date. This is deliberate: tax settings change, and a stale snapshot presented confidently is worse than no snapshot.

## Install

The skill is harness-agnostic. It is a plain folder containing `SKILL.md` at its root, with no host-specific requirements.

Download the repository ZIP, or clone it:

```bash
git clone https://github.com/islay-malter/au-itr-assessment-fy26.git
```

Keep the folder name `au-itr-assessment-fy26` and ensure `SKILL.md` is at the folder root. Place the complete folder in your agent's skills directory:

```text
~/.agents/skills/au-itr-assessment-fy26/
```

If your harness does not read `~/.agents/skills` yet, copy the same folder to whichever directory it does read:

```text
~/.claude/skills/au-itr-assessment-fy26/
~/.codex/skills/au-itr-assessment-fy26/
```

Restart or refresh the Agent Skills host if it does not discover the skill immediately.

`agents/openai.yaml` supplies an optional display name, colour, and default prompt for hosts that read it. Hosts that ignore it lose nothing; the preflight does not require it.

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
python3 -m unittest discover -s tests
```

```bash
python3 scripts/validate_evals.py evals/cases.json
```

```bash
python3 scripts/check_shareable.py .
```

Run the preflight last. It separates **blocking findings** — private config, taxpayer documents, possible identifiers, missing files, and an expired source set — from **advisories**, which are local build artefacts and harness-local directories that Git already ignores. Only blocking findings fail the check. Add `--strict` to fail on advisories too when building a release archive, or `--json` for machine-readable output.

The preflight also checks that the verification date in `SKILL.md` matches the date stated in the rates and sources references, so a metadata-only freshness bump cannot pass.

`validate_evals.py` checks the structure and coverage of the behavioural eval manifest in [`evals/cases.json`](evals/cases.json); it does not run the model, so a clean result only confirms the cases are well-formed, not that the skill currently passes them. Review the final file list manually before publishing or sharing it.

## Licence

Released under the [MIT Licence](LICENSE).
