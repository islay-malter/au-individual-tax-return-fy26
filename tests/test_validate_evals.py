from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "validate_evals.py"
MANIFEST_PATH = SKILL_DIR / "evals" / "cases.json"

SPEC = importlib.util.spec_from_file_location("validate_evals", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_case(**overrides: object) -> dict:
    case = {
        "id": "sample-case",
        "category": "scope",
        "as_of_date": "2026-09-15",
        "prompt": "Prepare my FY26 return.",
        "required": [{"id": "req-1", "criterion": "Does the required thing."}],
        "prohibited": [{"id": "proh-1", "criterion": "Avoids the prohibited thing."}],
    }
    case.update(overrides)
    return case


def valid_manifest(cases: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "skill": "au-individual-tax-return-fy26",
        "pass_rule": "all_required_and_no_prohibited",
        "cases": cases,
    }


class EvalManifestStructureTests(unittest.TestCase):
    def test_committed_manifest_is_clean(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(MODULE.validate(manifest), [])

    def test_missing_top_level_field_is_rejected(self) -> None:
        manifest = valid_manifest([valid_case()])
        del manifest["pass_rule"]
        issues = MODULE.validate(manifest)
        self.assertTrue(any("pass_rule" in issue for issue in issues))

    def test_unknown_schema_version_is_rejected(self) -> None:
        manifest = valid_manifest([valid_case()])
        manifest["schema_version"] = 2
        issues = MODULE.validate(manifest)
        self.assertTrue(any("schema_version" in issue for issue in issues))

    def test_wrong_skill_name_is_rejected(self) -> None:
        manifest = valid_manifest([valid_case()])
        manifest["skill"] = "another-skill"
        issues = MODULE.validate(manifest)
        self.assertTrue(any("skill" in issue for issue in issues))

    def test_case_missing_required_field_is_rejected(self) -> None:
        case = valid_case()
        del case["required"]
        issues = MODULE.validate(valid_manifest([case]))
        self.assertTrue(any("required" in issue for issue in issues))

    def test_case_missing_category_is_rejected(self) -> None:
        case = valid_case()
        del case["category"]
        issues = MODULE.validate(valid_manifest([case]))
        self.assertTrue(any("category" in issue for issue in issues))

    def test_duplicate_case_id_is_rejected(self) -> None:
        issues = MODULE.validate(valid_manifest([valid_case(), valid_case()]))
        self.assertTrue(any("duplicate case id" in issue for issue in issues))

    def test_empty_prompt_is_rejected(self) -> None:
        issues = MODULE.validate(valid_manifest([valid_case(prompt="   ")]))
        self.assertTrue(any("prompt" in issue for issue in issues))

    def test_invalid_as_of_date_is_rejected(self) -> None:
        issues = MODULE.validate(valid_manifest([valid_case(as_of_date="not-a-date")]))
        self.assertTrue(any("as_of_date" in issue for issue in issues))

    def test_empty_required_list_is_rejected(self) -> None:
        issues = MODULE.validate(valid_manifest([valid_case(required=[])]))
        self.assertTrue(any("required" in issue for issue in issues))

    def test_criterion_fields_must_be_non_empty_strings(self) -> None:
        required = [{"id": 7, "criterion": 42}]
        issues = MODULE.validate(valid_manifest([valid_case(required=required)]))
        self.assertTrue(any("criterion id" in issue for issue in issues))
        self.assertTrue(any("criterion text" in issue for issue in issues))

    def test_unknown_pass_rule_is_rejected(self) -> None:
        manifest = valid_manifest([valid_case()])
        manifest["pass_rule"] = "vibes"
        issues = MODULE.validate(manifest)
        self.assertTrue(any("pass_rule" in issue for issue in issues))

    def test_null_pass_rule_is_rejected(self) -> None:
        manifest = valid_manifest([valid_case()])
        manifest["pass_rule"] = None
        issues = MODULE.validate(manifest)
        self.assertTrue(any("pass_rule" in issue for issue in issues))


class EvalManifestCliTests(unittest.TestCase):
    def test_committed_manifest_validates_without_claiming_behavior_ran(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(MANIFEST_PATH), "--json"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["manifest_valid"])
        self.assertFalse(report["behavior_run"])

    def test_broken_manifest_fails_the_cli(self) -> None:
        case = valid_case()
        del case["required"]
        broken = valid_manifest([case, case])  # also duplicates the id

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "cases.json"
            manifest_path.write_text(json.dumps(broken), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), str(manifest_path), "--json"],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertFalse(report["manifest_valid"])
        self.assertTrue(report["findings"])


if __name__ == "__main__":
    unittest.main()
