"""Preflight an Agent Skill folder for privacy, package metadata, and freshness.

Findings are split by severity:

- Blocking findings are privacy, packaging, or freshness problems that make the
  folder unsafe or invalid to share. They set a non-zero exit status.
- Advisories are local build artefacts and harness-local directories. They are
  worth cleaning before building an archive but are normally ignored by version
  control, so they do not fail the check unless --strict is passed.
"""

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
    "assets/templates/client-profile.example.json",
    "references/client-profile.schema.json",
    "references/fy26-ato-sources.md",
    "references/fy26-rates-and-thresholds.md",
    "scripts/build_file_checklist.py",
    "scripts/check_shareable.py",
}

# Files that may ship but are not required, so the package stays valid on a
# harness that does not read a given interface manifest.
OPTIONAL_FILES = {
    "agents/openai.yaml",
}

# Reference files whose stated verification date must agree with SKILL.md.
SOURCE_DATED_REFERENCES = (
    "references/fy26-rates-and-thresholds.md",
    "references/fy26-ato-sources.md",
)

PACKAGE_METADATA_FIELDS = (
    "package-version",
    "sources-last-verified",
    "reverify-by",
)

SEMVER_PATTERN = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")

# Walked but never reported; a repository checkout is expected to contain this.
SILENT_DIRS = {".git"}

# Not walked, and reported as an advisory: harness-local or vendored state that
# belongs to a machine rather than to the distributable package.
LOCAL_DIRS = {".claude", ".codex", ".agents", "node_modules", ".venv", "venv"}

# Not walked, and reported once per directory rather than once per file.
TRANSIENT_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}

BLOCKED_SUFFIXES = {
    ".pdf",
    ".csv",
    ".tsv",
    ".xls",
    ".xlsx",
    ".doc",
    ".docx",
    ".zip",
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


def _walk(skill_dir: Path) -> tuple[list[Path], list[str], list[str]]:
    """Return scannable files, skipped local directories, and skipped artefact directories."""
    files: list[Path] = []
    local_dirs: list[str] = []
    transient_dirs: list[str] = []

    def descend(directory: Path) -> None:
        for entry in sorted(directory.iterdir(), key=lambda item: item.name):
            if entry.is_symlink():
                continue
            if entry.is_dir():
                relative = entry.relative_to(skill_dir).as_posix()
                if entry.name in SILENT_DIRS:
                    continue
                if entry.name in LOCAL_DIRS:
                    local_dirs.append(relative)
                    continue
                if entry.name in TRANSIENT_DIRS:
                    transient_dirs.append(relative)
                    continue
                descend(entry)
            elif entry.is_file():
                files.append(entry)

    descend(skill_dir)
    return files, local_dirs, transient_dirs


def scan(skill_dir: Path, *, as_of: date | None = None) -> tuple[list[str], list[str]]:
    """Return (blocking findings, advisories) for a skill folder."""
    blocking: list[str] = []
    advisory: list[str] = []
    check_date = as_of or date.today()
    if not skill_dir.is_dir():
        return [f"not a directory: {skill_dir}"], []

    files, local_dirs, transient_dirs = _walk(skill_dir)

    for relative in local_dirs:
        advisory.append(f"harness-local directory, exclude from any archive: {relative}/")
    for relative in transient_dirs:
        advisory.append(f"build artefacts, safe to delete: {relative}/")

    present = {path.relative_to(skill_dir).as_posix() for path in files}
    for required in sorted(REQUIRED_FILES - present):
        blocking.append(f"missing required file: {required}")

    for path in sorted(files, key=lambda item: item.as_posix()):
        relative_path = path.relative_to(skill_dir)
        relative = relative_path.as_posix()
        directory_parts = set(relative_path.parts[:-1])
        lower_name = path.name.lower()

        if "config" in directory_parts:
            blocking.append(f"private config directory must not be distributed: {relative}")
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            blocking.append(f"blocked document/archive type: {relative}")
        if lower_name.endswith(".local.json"):
            blocking.append(f"local profile/config file: {relative}")
        if lower_name.startswith(("itr_", "accountant_", "missing_info_")):
            blocking.append(f"generated taxpayer output: {relative}")
        if path.stat().st_size > 5_000_000:
            blocking.append(f"unexpectedly large file (review manually): {relative}")

        if lower_name == ".ds_store" or path.suffix.lower() == ".pyc":
            advisory.append(f"junk file, safe to delete: {relative}")
            continue

        if path.suffix.lower() in TEXT_SUFFIXES:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                blocking.append(f"non-UTF-8 text file: {relative}")
                continue
            for label, pattern in PII_PATTERNS.items():
                if pattern.search(content):
                    blocking.append(f"possible {label}: {relative}")

    skill_file = skill_dir / "SKILL.md"
    if skill_file.is_file():
        content = skill_file.read_text(encoding="utf-8")
        if "name: au-itr-assessment-fy26" not in content:
            blocking.append("SKILL.md name is not au-itr-assessment-fy26")
        if not re.search(r"(?m)^license:\s*MIT\s*$", content):
            blocking.append("SKILL.md license is not MIT")
        if "2024-25" in content:
            blocking.append("SKILL.md contains the prior income year 2024-25")

        metadata, metadata_issues = package_metadata(content)
        blocking.extend(metadata_issues)
        package_version = metadata.get("package-version")
        if package_version and not SEMVER_PATTERN.fullmatch(package_version):
            blocking.append("SKILL.md package-version must use MAJOR.MINOR.PATCH")

        parsed_dates: dict[str, date] = {}
        for field in ("sources-last-verified", "reverify-by"):
            raw_value = metadata.get(field)
            if not raw_value:
                continue
            try:
                parsed_dates[field] = date.fromisoformat(raw_value)
            except ValueError:
                blocking.append(f"SKILL.md {field} must use YYYY-MM-DD")

        verified = parsed_dates.get("sources-last-verified")
        reverify_by = parsed_dates.get("reverify-by")
        if verified and verified > check_date:
            blocking.append(
                f"SKILL.md sources-last-verified {verified.isoformat()} is after check date {check_date.isoformat()}"
            )
        if verified and reverify_by and reverify_by < verified:
            blocking.append("SKILL.md reverify-by is earlier than sources-last-verified")
        if reverify_by and check_date > reverify_by:
            blocking.append(
                "package source verification expired on "
                f"{reverify_by.isoformat()}; revalidate material official sources before sharing"
            )

        if verified:
            blocking.extend(_source_date_findings(skill_dir, verified))

    return blocking, advisory


def _source_date_findings(skill_dir: Path, verified: date) -> list[str]:
    """Reference files must state the same verification date as SKILL.md.

    This makes a metadata-only freshness bump fail the preflight instead of
    silently disagreeing with the reference snapshots it claims to cover.
    """
    issues: list[str] = []
    stamp = verified.isoformat()
    for relative in SOURCE_DATED_REFERENCES:
        path = skill_dir / relative
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if stamp not in content:
            issues.append(
                f"{relative} does not state the SKILL.md sources-last-verified date {stamp}; "
                "re-verify the sources and update the reference, or correct the frontmatter"
            )
    return issues


def findings(skill_dir: Path, *, as_of: date | None = None) -> list[str]:
    """Blocking findings only; an empty list means the folder is safe to share."""
    return scan(skill_dir, as_of=as_of)[0]


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
    parser.add_argument("--strict", action="store_true", help="Treat advisories as failures too.")
    args = parser.parse_args(argv)

    skill_dir = args.skill_dir.resolve()
    blocking, advisory = scan(skill_dir)
    failed = bool(blocking) or (args.strict and bool(advisory))

    if args.json:
        print(
            json.dumps(
                {
                    "skill_dir": str(skill_dir),
                    "shareable": not failed,
                    "findings": blocking,
                    "advisories": advisory,
                },
                indent=2,
            )
        )
        return 1 if failed else 0

    if blocking:
        print("Shareability preflight failed:", file=sys.stderr)
        for issue in blocking:
            print(f"- {issue}", file=sys.stderr)
    else:
        print(f"Shareability preflight passed: {skill_dir}")

    if advisory:
        stream = sys.stderr if args.strict else sys.stdout
        print("", file=stream)
        print("Advisories (not shared by Git; delete before building an archive):", file=stream)
        for note in advisory:
            print(f"- {note}", file=stream)

    if not failed:
        print("")
        print("Review the final archive contents manually before sharing.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
