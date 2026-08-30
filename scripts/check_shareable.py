"""Preflight an Agent Skill folder for privacy, package metadata, and freshness."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


REQUIRED_FILES = {
    "LICENSE",
    "README.md",
    "SKILL.md",
    "agents/openai.yaml",
    "assets/templates/client-profile.example.json",
    "references/client-profile.schema.json",
    "references/fy26-ato-sources.md",
    "references/fy26-rates-and-thresholds.md",
    "scripts/build_file_checklist.py",
    "scripts/check_shareable.py",
}

PACKAGE_METADATA_FIELDS = (
    "package-version",
    "sources-last-verified",
    "reverify-by",
)

SEMVER_PATTERN = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")

BLOCKED_SUFFIXES = {
    ".pdf",
    ".csv",
    ".tsv",
    ".xls",
    ".xlsx",
    ".doc",
    ".docx",
    ".zip",
    ".pyc",
}

TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".txt"}

PII_PATTERNS = {
    "email-like value": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "TFN-like 9-digit value": re.compile(r"(?<!\d)(?:\d[ -]?){8}\d(?!\d)"),
    "ABN-like 11-digit value": re.compile(r"(?<!\d)(?:\d[ -]?){10}\d(?!\d)"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def package_metadata(skill_content: str) -> tuple[dict[str, str], list[str]]:
    metadata: dict[str, str] = {}
    issues: list[str] = []
    frontmatter_match = re.match(r"^---\n(.*?)\n---", skill_content, re.DOTALL)
    if not frontmatter_match:
        return metadata, ["SKILL.md has no valid YAML frontmatter"]

    frontmatter = frontmatter_match.group(1)
    for field in PACKAGE_METADATA_FIELDS:
        field_match = re.search(
            rf"(?m)^  {re.escape(field)}:\s*[\"']?([^\"'\n]+?)[\"']?\s*$",
            frontmatter,
        )
        if field_match:
            metadata[field] = field_match.group(1).strip()
        else:
            issues.append(f"SKILL.md metadata is missing {field}")
    return metadata, issues


def _package_files(skill_dir: Path) -> list[Path]:
    return [
        path
        for path in skill_dir.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(skill_dir).parts
    ]


def findings(skill_dir: Path, *, as_of: date | None = None) -> list[str]:
    issues: list[str] = []
    check_date = as_of or date.today()
    if not skill_dir.is_dir():
        return [f"not a directory: {skill_dir}"]

    present = {path.relative_to(skill_dir).as_posix() for path in _package_files(skill_dir)}
    for required in sorted(REQUIRED_FILES - present):
        issues.append(f"missing required file: {required}")

    for path in sorted(_package_files(skill_dir), key=lambda item: item.as_posix()):
        relative_path = path.relative_to(skill_dir)
        relative = relative_path.as_posix()
        parts = set(relative_path.parts)
        directory_parts = set(relative_path.parts[:-1])
        lower_name = path.name.lower()

        if "config" in directory_parts:
            issues.append(f"private config directory must not be distributed: {relative}")
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            issues.append(f"blocked document/archive type: {relative}")
        if lower_name == ".ds_store" or "__pycache__" in parts or ".pytest_cache" in parts:
            issues.append(f"generated/junk file: {relative}")
        if lower_name.endswith(".local.json"):
            issues.append(f"local profile/config file: {relative}")
        if lower_name.startswith(("itr_", "accountant_", "missing_info_")):
            issues.append(f"generated taxpayer output: {relative}")
        if path.stat().st_size > 5_000_000:
            issues.append(f"unexpectedly large file (review manually): {relative}")

        if path.suffix.lower() in TEXT_SUFFIXES:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                issues.append(f"non-UTF-8 text file: {relative}")
                continue
            for label, pattern in PII_PATTERNS.items():
                if pattern.search(content):
                    issues.append(f"possible {label}: {relative}")

    skill_file = skill_dir / "SKILL.md"
    if skill_file.is_file():
        content = skill_file.read_text(encoding="utf-8")
        if "name: au-itr-assessment-fy26" not in content:
            issues.append("SKILL.md name is not au-itr-assessment-fy26")
        if not re.search(r"(?m)^license:\s*MIT\s*$", content):
            issues.append("SKILL.md license is not MIT")
        if "2024-25" in content:
            issues.append("SKILL.md contains the prior income year 2024-25")

        metadata, metadata_issues = package_metadata(content)
        issues.extend(metadata_issues)
        package_version = metadata.get("package-version")
        if package_version and not SEMVER_PATTERN.fullmatch(package_version):
            issues.append("SKILL.md package-version must use MAJOR.MINOR.PATCH")

        parsed_dates: dict[str, date] = {}
        for field in ("sources-last-verified", "reverify-by"):
            raw_value = metadata.get(field)
            if not raw_value:
                continue
            try:
                parsed_dates[field] = date.fromisoformat(raw_value)
            except ValueError:
                issues.append(f"SKILL.md {field} must use YYYY-MM-DD")

        verified = parsed_dates.get("sources-last-verified")
        reverify_by = parsed_dates.get("reverify-by")
        if verified and verified > check_date:
            issues.append(
                f"SKILL.md sources-last-verified {verified.isoformat()} is after check date {check_date.isoformat()}"
            )
        if verified and reverify_by and reverify_by < verified:
            issues.append("SKILL.md reverify-by is earlier than sources-last-verified")
        if reverify_by and check_date > reverify_by:
            issues.append(
                "package source verification expired on "
                f"{reverify_by.isoformat()}; revalidate material official sources before sharing"
            )

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skill_dir",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Skill directory; defaults to the parent of this script directory.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    skill_dir = args.skill_dir.resolve()
    issues = findings(skill_dir)
    if args.json:
        print(json.dumps({"skill_dir": str(skill_dir), "shareable": not issues, "findings": issues}, indent=2))
    elif issues:
        print("Shareability preflight failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
    else:
        print(f"Shareability preflight passed: {skill_dir}")
        print("Review the final archive contents manually before sharing.")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
