"""Validate the structure and coverage of the local behavioral-eval manifest.

This does not run the skill against a model. It only checks that the manifest
is well-formed enough for a human or a future automated runner to execute:
required fields are present, ids are unique, and each case states at least
one required and one prohibited criterion.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "evals" / "cases.json"

EXPECTED_SCHEMA_VERSION = 1
EXPECTED_SKILL = "au-individual-tax-return-fy26"
KNOWN_PASS_RULES = {"all_required_and_no_prohibited"}
TOP_LEVEL_FIELDS = ("schema_version", "skill", "pass_rule", "cases")
CASE_FIELDS = ("id", "category", "as_of_date", "prompt", "required", "prohibited")
CRITERION_FIELDS = ("id", "criterion")


def _validate_criteria(case_id: str, field: str, value: object, issues: list[str]) -> None:
    if not isinstance(value, list) or not value:
        issues.append(f"case '{case_id}': '{field}' must be a non-empty list")
        return
    seen_ids: set[str] = set()
    for entry in value:
        if not isinstance(entry, dict):
            issues.append(f"case '{case_id}': '{field}' entries must be objects")
            continue
        missing = [f for f in CRITERION_FIELDS if not entry.get(f)]
        if missing:
            issues.append(f"case '{case_id}': '{field}' entry missing {missing}")
            continue

        # Both are reported independently: a criterion carrying the wrong type
        # in both fields should surface both problems in one pass, rather than
        # hiding the second behind a fix for the first.
        entry_id = entry["id"]
        if not isinstance(entry_id, str) or not entry_id.strip():
            issues.append(
                f"case '{case_id}': '{field}' criterion id must be a non-empty string, "
                f"got {entry_id!r}"
            )
        criterion = entry["criterion"]
        if not isinstance(criterion, str) or not criterion.strip():
            issues.append(
                f"case '{case_id}': '{field}' criterion text must be a non-empty string, "
                f"got {criterion!r}"
            )

        if isinstance(entry_id, str):
            if entry_id in seen_ids:
                issues.append(f"case '{case_id}': duplicate '{field}' entry id '{entry_id}'")
            seen_ids.add(entry_id)


def _validate_case(case: object, issues: list[str]) -> str | None:
    if not isinstance(case, dict):
        issues.append("case is not an object")
        return None

    missing = [f for f in CASE_FIELDS if not case.get(f) and case.get(f) != []]
    if missing:
        issues.append(f"case {case.get('id', '<no id>')!r} missing required field(s): {missing}")

    case_id = case.get("id")
    if case_id is not None and not isinstance(case_id, str):
        issues.append(f"case id {case_id!r} must be a string")
        case_id = None

    prompt = case.get("prompt")
    if prompt is not None and (not isinstance(prompt, str) or not prompt.strip()):
        issues.append(f"case {case_id!r}: 'prompt' must be a non-empty string")

    category = case.get("category")
    if category is not None and (not isinstance(category, str) or not category.strip()):
        issues.append(f"case {case_id!r}: 'category' must be a non-empty string")

    as_of_date = case.get("as_of_date")
    if as_of_date is not None:
        try:
            date.fromisoformat(as_of_date)
        except (TypeError, ValueError):
            issues.append(f"case {case_id!r}: 'as_of_date' must be YYYY-MM-DD")

    if "required" in case:
        _validate_criteria(case_id or "<no id>", "required", case["required"], issues)
    if "prohibited" in case:
        _validate_criteria(case_id or "<no id>", "prohibited", case["prohibited"], issues)

    return case_id if isinstance(case_id, str) else None


def validate(manifest: object) -> list[str]:
    issues: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest root must be a JSON object"]

    missing_top = [f for f in TOP_LEVEL_FIELDS if f not in manifest]
    if missing_top:
        issues.append(f"manifest missing top-level field(s): {missing_top}")

    schema_version = manifest.get("schema_version")
    if schema_version != EXPECTED_SCHEMA_VERSION or isinstance(schema_version, bool):
        issues.append(
            f"schema_version must be {EXPECTED_SCHEMA_VERSION}, got {schema_version!r}"
        )

    skill = manifest.get("skill")
    if skill != EXPECTED_SKILL:
        issues.append(f"skill must be {EXPECTED_SKILL!r}, got {skill!r}")

    pass_rule = manifest.get("pass_rule")
    if "pass_rule" in manifest and pass_rule not in KNOWN_PASS_RULES:
        issues.append(f"unknown pass_rule: {pass_rule!r}")

    cases = manifest.get("cases")
    if cases is not None:
        if not isinstance(cases, list) or not cases:
            issues.append("'cases' must be a non-empty list")
        else:
            seen_ids: set[str] = set()
            for case in cases:
                case_id = _validate_case(case, issues)
                if case_id:
                    if case_id in seen_ids:
                        issues.append(f"duplicate case id: {case_id}")
                    seen_ids.add(case_id)

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Eval manifest; defaults to evals/cases.json in this skill.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    manifest_path = args.manifest.resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        report = {
            "manifest": str(manifest_path),
            "manifest_valid": False,
            "behavior_run": False,
            "case_count": 0,
            "findings": [str(exc)],
        }
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"Eval manifest validation failed: {exc}", file=sys.stderr)
        return 1

    issues = validate(manifest)
    case_count = len(manifest.get("cases", [])) if isinstance(manifest, dict) else 0
    report = {
        "manifest": str(manifest_path),
        "manifest_valid": not issues,
        "behavior_run": False,
        "case_count": case_count,
        "findings": issues,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    elif issues:
        print("Eval manifest validation failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
    else:
        print(f"Eval manifest structure and coverage passed: {manifest_path}")
        print("No model behavior was run.")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
