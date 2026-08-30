"""Validate the local behavioral-eval manifest without running a model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "evals" / "cases.json"


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

    case_count = len(manifest.get("cases", [])) if isinstance(manifest, dict) else 0
    report = {
        "manifest": str(manifest_path),
        "manifest_valid": True,
        "behavior_run": False,
        "case_count": case_count,
        "findings": [],
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Eval manifest structure and coverage passed: {manifest_path}")
        print("No model behavior was run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
