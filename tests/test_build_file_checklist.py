from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "build_file_checklist.py"
SPEC = importlib.util.spec_from_file_location("build_file_checklist", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def blank_profile() -> dict:
    path = SKILL_DIR / "assets" / "templates" / "client-profile.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


class ChecklistTests(unittest.TestCase):
    def test_blank_profile_asks_a_bounded_batch_without_over_requesting(self) -> None:
        output = MODULE.build(blank_profile())
        question_lines = [line for line in output.splitlines() if line[:1].isdigit() and ". " in line]
        self.assertLessEqual(len(question_lines), MODULE.MAX_NEXT_QUESTIONS)
        self.assertIn("additional question(s) remain", output)
        self.assertNotIn("Spouse income-test details |", output)
        self.assertNotIn("Bank interest summaries |", output)

    def test_simple_employee_only_triggers_employment_evidence(self) -> None:
        profile = blank_profile()
        profile["scope"]["residency_status"] = "full-year-resident"
        profile["scope"]["deceased_return"] = False
        profile["records"]["ato_prefill_status"] = "official-agent-prefill"
        profile["records"]["prior_year_return_available"] = True
        profile["records"]["prior_year_noa_available"] = True
        profile["records"]["refund_account_available_to_lodger"] = True
        profile["household"]["had_spouse"] = False
        profile["household"]["dependent_children_count"] = 0
        profile["household"]["private_hospital_cover"] = False
        profile["household"]["private_health_changed_during_year"] = False
        profile["household"]["medicare_exemption_or_entitlement_gap"] = False
        profile["employment"]["has_salary_or_wages"] = True
        profile["employment"]["employers"] = ["Example employer"]
        output = MODULE.build(profile)
        self.assertIn("Tax-ready income statement/payment summary", output)
        self.assertNotIn("Spouse income-test details |", output)
        self.assertNotIn("Private health insurance statement", output)

    def test_wrong_year_is_rejected(self) -> None:
        profile = blank_profile()
        profile["scope"]["tax_year"] = "2024-25"
        with self.assertRaisesRegex(MODULE.ProfileError, "must be 2025-26"):
            MODULE.build(profile)

    def test_newline_in_display_name_is_rejected(self) -> None:
        profile = blank_profile()
        profile["identity"]["display_name"] = "Name\nInjected heading"
        with self.assertRaisesRegex(MODULE.ProfileError, "single line"):
            MODULE.build(profile)

    def test_part_year_residency_creates_review_gate(self) -> None:
        profile = blank_profile()
        profile["scope"]["residency_status"] = "part-year-resident"
        output = MODULE.build(profile)
        self.assertIn("Residency is not confirmed as full-year Australian resident", output)

    def test_estimate_only_does_not_request_refund_account(self) -> None:
        profile = blank_profile()
        profile["scope"]["lodgment_path"] = "estimate-only"
        profile["records"]["refund_account_available_to_lodger"] = False
        output = MODULE.build(profile)
        self.assertNotIn("refund-account details", output)

    def test_output_is_not_overwritten_without_force(self) -> None:
        profile = blank_profile()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            profile_path = temp_path / "profile.json"
            output_path = temp_path / "checklist.md"
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            output_path.write_text("keep", encoding="utf-8")
            result = MODULE.main(["--profile", str(profile_path), "--out", str(output_path)])
            self.assertEqual(result, 2)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
