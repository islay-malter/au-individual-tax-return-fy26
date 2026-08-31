from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
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


def scoped_profile() -> dict:
    """A profile with the opening scope batch answered.

    Next Intake Questions is deliberately capped at MAX_NEXT_QUESTIONS, so a
    later-batch question only reaches the rendered output once the earlier
    priority questions have been resolved.
    """
    profile = blank_profile()
    profile["identity"]["display_name"] = "QK"
    profile["scope"]["lodgment_path"] = "accountant"
    profile["scope"]["residency_status"] = "full-year-resident"
    profile["scope"]["deceased_return"] = False
    profile["records"]["ato_prefill_status"] = "official-agent-prefill"
    profile["records"]["prior_year_return_available"] = True
    profile["records"]["prior_year_noa_available"] = True
    profile["records"]["refund_account_available_to_lodger"] = True
    profile["household"]["had_spouse"] = False
    profile["household"]["dependent_children_count"] = 0
    profile["household"]["private_hospital_cover"] = True
    profile["household"]["private_health_changed_during_year"] = False
    profile["household"]["medicare_exemption_or_entitlement_gap"] = False
    for key in profile["investments_and_business"]:
        profile["investments_and_business"][key] = False
    profile["payg"]["payg_instalments_issued"] = False
    return profile


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
            # The refusal message is expected; keep it out of the test report.
            with contextlib.redirect_stderr(io.StringIO()) as captured:
                result = MODULE.main(["--profile", str(profile_path), "--out", str(output_path)])
            self.assertEqual(result, 2)
            self.assertIn("refusing to overwrite", captured.getvalue())
            self.assertEqual(output_path.read_text(encoding="utf-8"), "keep")

    def test_named_employers_appear_in_the_income_statement_row(self) -> None:
        profile = blank_profile()
        profile["employment"]["has_salary_or_wages"] = True
        profile["employment"]["employers"] = ["Acme Pty Ltd", "Globex Ltd"]
        output = MODULE.build(profile)
        self.assertIn("each of 2 employer(s): Acme Pty Ltd, Globex Ltd", output)
        self.assertNotIn("Which employers paid salary or wages", output)

    def test_unnamed_employers_become_an_intake_question(self) -> None:
        profile = scoped_profile()
        profile["employment"]["has_salary_or_wages"] = True
        output = MODULE.build(profile)
        self.assertIn("Which employers paid salary or wages", output)

    def test_occupation_drives_the_ato_guide_row(self) -> None:
        profile = blank_profile()
        profile["identity"]["occupation"] = "Software engineer"
        profile["employment"]["has_other_work_related_deductions"] = True
        output = MODULE.build(profile)
        self.assertIn("ATO occupation and industry guide for: Software engineer", output)

    def test_missing_occupation_is_asked_only_when_work_expenses_are_claimed(self) -> None:
        without_claim = MODULE.build(scoped_profile())
        self.assertNotIn("What was the taxpayer's occupation?", without_claim)

        profile = scoped_profile()
        profile["employment"]["works_from_home"] = True
        self.assertIn("What was the taxpayer's occupation?", MODULE.build(profile))

    def test_cross_border_equity_raises_a_review_gate(self) -> None:
        profile = blank_profile()
        profile["employee_share_plans"]["has_ess_rsus_options_or_espp"] = True
        profile["employee_share_plans"]["foreign_employer_or_overseas_workdays"] = True
        output = MODULE.build(profile)
        self.assertIn("foreign employer or overseas workdays", output)
        self.assertIn("overseas-workday calendar", output)

    def test_retained_shares_request_the_cost_base_bridge(self) -> None:
        profile = blank_profile()
        profile["employee_share_plans"]["has_ess_rsus_options_or_espp"] = True
        profile["employee_share_plans"]["retained_shares"] = True
        output = MODULE.build(profile)
        self.assertIn("cost-base bridge", output)

    def test_unknown_ess_sub_facts_become_questions(self) -> None:
        profile = scoped_profile()
        profile["employee_share_plans"]["has_ess_rsus_options_or_espp"] = True
        output = MODULE.build(profile)
        self.assertIn("vesting, exercise, or sale events", output)

    def test_pipe_is_escaped_in_cells_but_not_in_the_display_name_line(self) -> None:
        profile = blank_profile()
        profile["identity"]["display_name"] = "Q|K"
        profile["employment"]["has_salary_or_wages"] = True
        profile["employment"]["employers"] = ["Globex | Ltd"]
        output = MODULE.build(profile)
        self.assertIn("Taxpayer display name: Q|K", output)
        self.assertIn(r"Globex \| Ltd", output)

    def test_empty_sections_point_at_the_intake_questions(self) -> None:
        output = MODULE.build(blank_profile())
        self.assertIn("Answer the intake questions below", output)
        self.assertNotIn("No items triggered by the current profile", output)


if __name__ == "__main__":
    unittest.main()
