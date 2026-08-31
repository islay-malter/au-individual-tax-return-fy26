# AU Individual Tax Return FY26

An Agent Skill for preparing, reviewing, or sanity-checking an Australian individual income tax return for the `2025-26` income year (year ended 30 June 2026). It uses an intake-first, evidence-reconciled workflow and is intended to support myTax preparation or accountant review.

This package is FY26-only. It does not lodge returns, provide tax advice, or replace a registered tax agent.

**The packaged source set expires.** The `reverify-by` date in the [`SKILL.md`](SKILL.md) frontmatter is the authoritative expiry. Past that date the skill will still run intake, evidence collection, and document organisation, but it will refuse to calculate or assert current rules until the official sources are revalidated and the dates advanced. The shareability preflight fails after the same date. This is deliberate: tax settings change, and a stale snapshot presented confidently is worse than no snapshot.

## What This Does Differently

Three deliberate constraints. A reviewer has proposed removing each of them at some point.

- **No tax calculator.** No script here performs financial arithmetic. Every estimate is model-produced and carries the label `Unchecked model-produced working scenario` until it is independently recomputed, or compared against myTax or a registered tax agent.
- **No identifiers, no amounts.** The profile holds booleans, enums, a display name, and an occupation. There is no field for a TFN, ABN, bank details, or a dollar figure. Those stay in the taxpayer's own working folder and never enter this repository. `.gitignore` and `scripts/check_shareable.py` are privacy controls, not tidiness.
- **The expiry is checked, not just declared.** Advancing `reverify-by` in the frontmatter alone is not enough: the preflight requires the same date to appear in the rates and sources references, and `evals/cases.json` carries a behavioural case for the cosmetic-bump failure mode. This catches a metadata-only bump. It cannot prove the sources were actually re-opened, since a determined editor can change all three files, so the maintainer rule in `AGENTS.md` still governs.

## Why It Is Built This Way

In April 2026 the ATO warned taxpayers about acting on AI-generated tax information. Assistant Commissioner Anita Challen cautioned that such tools may draw on tax laws "from outside of Australia or outdated sources" ([media release](https://www.ato.gov.au/media-centre/from-hacks-to-half-truths-ato-warns-of-tax-time-misinformation-and-reveals-focus-areas), 27 April 2026).

Those are the two failure modes this package is designed against. The FY26-only scope addresses the first; the enforced expiry gate addresses the second. Neither makes the output correct; you remain accountable for what you lodge.

**If you are a registered tax agent or BAS agent**, using AI in the provision of tax agent services does not reduce your obligations under the Tax Agent Services Act 2009 and the Code of Professional Conduct. See [TPB(GS) 55/2026](https://www.tpb.gov.au/tpbgs-552026-use-artificial-intelligence-and-code-professional-conduct) (issued 22 July 2026), which covers competence, reasonable care, confidentiality, record keeping, professional judgement, and supervision. This package is a preparation aid; it does not discharge any of them.

## Install

The skill is harness-agnostic. It is a plain folder containing `SKILL.md` at its root, with no host-specific requirements.

Download the repository ZIP, or clone it:

```bash
git clone https://github.com/islay-malter/au-individual-tax-return-fy26.git
```

Keep the folder name `au-individual-tax-return-fy26` and ensure `SKILL.md` is at the folder root. Place the complete folder in your agent's skills directory:

```text
~/.agents/skills/au-individual-tax-return-fy26/
```

If your harness does not read `~/.agents/skills` yet, copy the same folder to whichever directory it does read:

```text
~/.claude/skills/au-individual-tax-return-fy26/
~/.codex/skills/au-individual-tax-return-fy26/
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

Run the preflight last. It sorts what it finds into three groups:

- **Blocking findings**: private config, taxpayer documents, possible identifiers, missing files, and an expired source set. These always fail the check.
- **Advisories**: build artefacts such as `__pycache__` and `.DS_Store`. Delete them; `--strict` fails on them.
- **Notes**: harness-local directories such as `.claude/`. Any checkout an agent host has run in contains one, and `git archive` never writes them, so these are reported for review when archiving by hand and never fail the check, including under `--strict`.

Add `--strict` when building a release archive, or `--json` for machine-readable output.

The preflight also checks that the verification date in `SKILL.md` matches the date stated in the rates and sources references, so a metadata-only freshness bump cannot pass.

`validate_evals.py` checks the structure and coverage of the behavioural eval manifest in [`evals/cases.json`](evals/cases.json); it does not run the model, so a clean result only confirms the cases are well-formed, not that the skill currently passes them. Review the final file list manually before publishing or sharing it.

## Building A Share Archive

Build the bundle with `git archive` rather than zipping the folder:

```bash
git archive --format=zip --output=au-individual-tax-return-fy26.zip main
```

`git archive` writes only tracked files, so untracked local state cannot leak into a shared archive regardless of what is sitting in the working directory: no `__pycache__`, no `.DS_Store`, no `__MACOSX/` resource forks from the macOS Finder, and no `config/` or taxpayer documents. Zipping the folder by hand offers none of those guarantees.

It protects against untracked state, not against a bad commit. Anything force-added to the index with `git add -f` is tracked, and `git archive` will ship it. That is why `scripts/check_shareable.py` blocks on any file under `config/`, any `*.local.json`, and any generated taxpayer output, whatever the ignore rules say. Run the preflight as well as trusting the archive.

Check the result before sending it:

```bash
unzip -l au-individual-tax-return-fy26.zip
```

## Licence

Released under the [MIT Licence](LICENSE).
