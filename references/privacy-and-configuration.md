# Privacy And Configuration

Tax records are sensitive. Collect only what the working assessment needs and keep the distributable skill free of taxpayer data.

## Runtime Intake

- Prefer a display name or initials in profiles and working papers.
- Never request or store a TFN, myGov username or password, MFA code, full bank account or card details, identity-document number, or unrelated medical information.
- Ask whether valid refund bank details are available for the lodger; do not ask the user to paste those details into the profile.
- Accept redacted documents and avoid reproducing identifiers that remain visible.
- Keep one taxpayer per working folder. Do not search sibling folders or infer facts from another return.

## Optional Local Config

The shareable template is `assets/templates/client-profile.example.json`. A user may copy it to `config/client-profile.local.json` inside their installed skill and fill in reusable facts. This is optional.

Only use a package-local config when the user explicitly identifies it as the current taxpayer's config. Confirm that its income year and facts are still current. Runtime user statements and current source documents take precedence over stale config values.

The `config/` directory and `*.local.json` files are ignored by the supplied `.gitignore` and rejected by `scripts/check_shareable.py`. They must not be included in a shared archive or repository.

## Output Location

Write checklists, source registers, estimates, questions, and correspondence drafts to the taxpayer's working folder, never under the skill directory. Before sharing, run:

```bash
python3 "<skill-directory>/scripts/check_shareable.py" "<skill-directory>"
```

The preflight is a guardrail, not a guarantee. Review the final archive contents manually.
