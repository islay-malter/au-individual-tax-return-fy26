# Working On This Package

Context for agents and contributors changing this repository. It is about
maintaining the package, not about using the skill — that is `SKILL.md`.

## What this is

A harness-agnostic Agent Skill for preparing and reviewing an Australian
individual tax return for the `2025-26` income year. It is an intake,
evidence-collection, and reconciliation aid. It does not lodge returns and
does not give tax advice.

Python is standard library only, tests included. Do not add dependencies. Tests
are `unittest`, not pytest.

## Invariants

These are deliberate. Several look like defects to a reviewer skimming the
repository, and have been proposed as "fixes" more than once. Do not change
them without an explicit decision from the maintainer.

**There is no tax calculator, on purpose.** No script performs financial
arithmetic. Every estimate is model-produced and must carry the label
`Unchecked model-produced working scenario` until independently recomputed or
compared against myTax or a registered tax agent. If a deterministic calculator
is ever added, it must use `decimal.Decimal` or integer cents, and it must be
named explicitly wherever its output is presented.

**The profile holds no personal identifiers and no money.** `schema_version`,
booleans, enums, a display name, an occupation, and employer names. No TFN, no
ABN, no bank details, no monetary amounts. Amounts belong in the source
register, which lives in the taxpayer's working folder and never in this
repository. Proposals to add TFN or ABN fields with validation patterns invert
the entire privacy design — reject them.

**`.gitignore` is a privacy control, not tidiness.** The entries for `config/`,
`*.local.json`, `ITR_*.md`, `Accountant_*.md`, `Missing_Info_And_Questions.md`,
and the document extensions stop a taxpayer's records being committed. Never
replace the file wholesale with a generic Python template; add to it instead.

**Never advance `reverify-by` without actually re-verifying the sources.**
Bumping the frontmatter dates is not revalidation, and neither is a passing
test run. Re-open each official source, confirm every material rate, threshold,
label, and record rule, update the reference files and their stated dates, then
advance `package-version`, `sources-last-verified`, and `reverify-by` together.
`scripts/check_shareable.py` enforces that the frontmatter date also appears in
the rates and sources references, and `evals/cases.json` has a behavioural case
for the cosmetic-bump failure mode.

**FY26 only.** Exclude substantive rules that first apply to `2026-27` or later,
while retaining post-year-end lodgment and reporting changes that operate for
the FY26 return. `scope.tax_year` must be `2025-26`; the validator rejects
anything else.

## Layout

```
SKILL.md                  workflow and routing; frontmatter is package status
references/               loaded on demand by the workflow
assets/templates/         the blank, share-safe profile
scripts/                  stdlib-only helpers
tests/                    unittest
evals/cases.json          behavioural cases; structure validated, not run
agents/openai.yaml        optional interface manifest; not required
```

`assets/templates/client-profile.example.json` is the authoritative profile
shape — `build_file_checklist.py` validates against it directly, and
`references/client-profile.schema.json` documents the same contract. Change
both together or they drift.

## Checks

```bash
python3 -m unittest discover -s tests
```

```bash
python3 scripts/validate_evals.py evals/cases.json
```

```bash
python3 scripts/check_shareable.py .
```

Run the preflight last. It separates blocking findings from advisories and
notes. Build artefacts are advisories and fail only under `--strict`;
harness-local directories are notes and never fail, because every checkout an
agent host touches has one and `git archive` excludes them regardless. Use
`--strict` when cutting a release.

Build share archives with `git archive`, never by zipping the folder:

```bash
git archive --format=zip --output=au-individual-tax-return-fy26.zip main
```

Two test fixtures assemble an email address and a bank identifier at runtime,
so the test files do not themselves contain values the preflight would flag.
Keep that pattern when adding fixtures with realistic identifiers.

## Intake question ordering

`Next Intake Questions` is capped at `MAX_NEXT_QUESTIONS`, so ordering decides
what actually gets asked. Questions are assembled in three tiers — scope, then
material tax impact, then record hygiene. When adding a question, put it in the
tier that matches its consequence, not the section it happens to sit in.

## Reviewing external suggestions

Verify claims against the tree before acting. Reviews of this repository have
asserted that build artefacts are committed (they are not — `git ls-files` is
clean), that the HELP repayment system needs updating to the marginal bands
(already documented), and that `validate_evals.py` should use `Decimal` (it
performs no arithmetic).

## Prior art

Other Australian tax packages exist and take different positions. Knowing them
stops the recurring "just add a calculator" and "the schema needs a TFN field"
suggestions being mistaken for gaps.

- `nijanthan-dev/taxmate-australia` — Apache-2.0, actively maintained, far
  broader (26 `SKILL.md` files, four harness manifests). It ships a calculator
  (`scripts/taxmate_calc.py`) and its intake carries `payg_employer_abn`,
  `partnership_tfn`, `tfn_withheld`, and dollar amounts. That is a different
  bet, not a better version of this one; do not import either choice here.
- `william-laverty/ato-mcp` — AGPL-3.0. Retrieval over the ATO corpus with
  citations, and it persists a user profile. Useful as a source-of-truth
  companion, but its licence means no text should be vendored into
  `references/`.
- `openaccountants/openaccountants` — AGPL-3.0 plus a bespoke content licence.
  Its Australian guide has carried `tax_year: 2024` frontmatter over a 2025-26
  body while marked `pending_review`. That is the exact defect the FY26-only
  rule and the enforced expiry gate exist to prevent.

No package found so far enforces source expiry — several record freshness
metadata, none refuse on it. Treat that and the zero-identifier profile as the
differentiators worth protecting.
