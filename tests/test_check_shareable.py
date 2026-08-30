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


def populate_package(root: Path, *, reverify_by: str = "2026-11-30") -> None:
    for relative in MODULE.REQUIRED_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")
    (root / "SKILL.md").write_text(
        "---\n"
        "name: au-itr-assessment-fy26\n"
        "description: Test package.\n"
        "license: MIT\n"
        "metadata:\n"
        '  package-version: "0.1.0"\n'
        '  sources-last-verified: "2026-08-31"\n'
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


if __name__ == "__main__":
    unittest.main()
