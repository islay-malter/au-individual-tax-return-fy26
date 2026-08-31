from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "check_shareable.py"
SPEC = importlib.util.spec_from_file_location("check_shareable", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def populate_package(
    root: Path,
    *,
    reverify_by: str = "2026-11-30",
    verified: str = "2026-08-31",
    reference_verified: str | None = None,
) -> None:
    for relative in MODULE.REQUIRED_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")
    stamp = verified if reference_verified is None else reference_verified
    for relative in MODULE.SOURCE_DATED_REFERENCES:
        (root / relative).write_text(
            f"Sources verified on `{stamp}`.\n", encoding="utf-8"
        )
    (root / "SKILL.md").write_text(
        "---\n"
        "name: au-itr-assessment-fy26\n"
        "description: Test package.\n"
        "license: MIT\n"
        "metadata:\n"
        '  package-version: "0.2.0"\n'
        f'  sources-last-verified: "{verified}"\n'
        f'  reverify-by: "{reverify_by}"\n'
        "---\n",
        encoding="utf-8",
    )


class ShareabilityTests(unittest.TestCase):
    def test_local_config_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            config = root / "config" / "client-profile.local.json"
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text("{}", encoding="utf-8")
            issues = MODULE.findings(root, as_of=date(2026, 8, 31))
            self.assertTrue(any("private config directory" in issue for issue in issues))

    def test_git_config_is_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            git_config = root / ".git" / "config"
            git_config.parent.mkdir(parents=True, exist_ok=True)
            git_config.write_text("[core]\n\trepositoryformatversion = 0\n", encoding="utf-8")
            blocking, advisory = MODULE.scan(root, as_of=date(2026, 8, 31))
            self.assertEqual(blocking, [])
            self.assertEqual(advisory, [])

    def test_package_is_current_through_reverify_date(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            issues = MODULE.findings(root, as_of=date(2026, 11, 30))
            self.assertEqual(issues, [])

    def test_expired_package_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            issues = MODULE.findings(root, as_of=date(2026, 12, 1))
            self.assertTrue(any("expired on 2026-11-30" in issue for issue in issues))

    def test_missing_package_metadata_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            (root / "SKILL.md").write_text(
                "---\nname: au-itr-assessment-fy26\ndescription: Test package.\n---\n",
                encoding="utf-8",
            )
            issues = MODULE.findings(root, as_of=date(2026, 8, 31))
            self.assertTrue(any("missing package-version" in issue for issue in issues))

    def test_interface_manifest_is_optional(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            self.assertNotIn("agents/openai.yaml", MODULE.REQUIRED_FILES)
            issues = MODULE.findings(root, as_of=date(2026, 8, 31))
            self.assertEqual(issues, [])

    def test_metadata_only_freshness_bump_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(
                root,
                verified="2027-02-01",
                reverify_by="2027-05-01",
                reference_verified="2026-08-31",
            )
            issues = MODULE.findings(root, as_of=date(2027, 2, 2))
            self.assertTrue(
                any("does not state the SKILL.md sources-last-verified date" in issue for issue in issues)
            )

    def test_build_artefacts_are_advisory_not_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            cache = root / "scripts" / "__pycache__"
            cache.mkdir(parents=True, exist_ok=True)
            (cache / "check_shareable.cpython-313.pyc").write_bytes(b"\x00")
            (root / ".DS_Store").write_bytes(b"\x00")
            blocking, advisory = MODULE.scan(root, as_of=date(2026, 8, 31))
            self.assertEqual(blocking, [])
            self.assertTrue(any("scripts/__pycache__/" in note for note in advisory))
            self.assertTrue(any(".DS_Store" in note for note in advisory))

    def test_artefacts_reported_once_per_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            cache = root / "scripts" / "__pycache__"
            cache.mkdir(parents=True, exist_ok=True)
            for name in ("a.cpython-313.pyc", "b.cpython-313.pyc", "c.cpython-313.pyc"):
                (cache / name).write_bytes(b"\x00")
            _, advisory = MODULE.scan(root, as_of=date(2026, 8, 31))
            self.assertEqual(len([n for n in advisory if "__pycache__" in n]), 1)

    def test_harness_local_directory_is_advisory_and_not_walked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            worktree = root / ".claude" / "worktrees" / "wip"
            worktree.mkdir(parents=True, exist_ok=True)
            (worktree / "notes.pdf").write_bytes(b"%PDF-1.4\n")
            blocking, advisory = MODULE.scan(root, as_of=date(2026, 8, 31))
            self.assertEqual(blocking, [])
            self.assertTrue(any(".claude/" in note for note in advisory))

    def test_real_taxpayer_documents_still_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            (root / "statement.pdf").write_bytes(b"%PDF-1.4\n")
            # Assembled at runtime so this test file does not itself contain a
            # literal email address for the preflight to flag.
            address = "jo" + "@" + "example.com"
            (root / "references" / "leak.md").write_text(
                f"contact {address}\n", encoding="utf-8"
            )
            issues = MODULE.findings(root, as_of=date(2026, 8, 31))
            self.assertTrue(any("blocked document/archive type" in issue for issue in issues))
            self.assertTrue(any("email-like value" in issue for issue in issues))

    def test_bank_identifiers_are_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            # Assembled at runtime so this test file does not itself contain a
            # literal bank identifier for the preflight to flag.
            bsb = "123" + "-" + "456"
            account = "8765" + "4321"
            (root / "references" / "refund.md").write_text(
                f"Refund account: {bsb} {account}\n", encoding="utf-8"
            )
            issues = MODULE.findings(root, as_of=date(2026, 8, 31))
            self.assertTrue(any("BSB and account number" in issue for issue in issues))

    def test_section_references_are_not_mistaken_for_bank_details(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            populate_package(root)
            (root / "references" / "law.md").write_text(
                "See sections 154-1 to 154-20, the 2025-26 year, and F2024L00697.\n",
                encoding="utf-8",
            )
            issues = MODULE.findings(root, as_of=date(2026, 8, 31))
            self.assertFalse(any("BSB" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
