"""Build a tailored FY26 Australian ITR evidence checklist from a profile JSON."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


SUPPORTED_TAX_YEAR = "2025-26"
MAX_NEXT_QUESTIONS = 8


class ProfileError(ValueError):
    """A concise, user-correctable profile error."""


def template_path() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "templates" / "client-profile.example.json"


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProfileError(f"profile file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProfileError(f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}") from exc
    except OSError as exc:
        raise ProfileError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ProfileError("profile root must be a JSON object")
    return data


def nested(profile: dict[str, Any], dotted: str) -> Any:
    current: Any = profile
    for part in dotted.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def validate_text(value: str, path: str, maximum: int) -> None:
    if any(char in value for char in ("\n", "\r", "\x00")):
        raise ProfileError(f"{path} must be a single line")
    if len(value) > maximum:
        raise ProfileError(f"{path} must be {maximum} characters or fewer")


def validate_profile(profile: dict[str, Any]) -> None:
    template = load_json(template_path())
    validate_shape(profile, template)

    if isinstance(profile["schema_version"], bool) or not isinstance(profile["schema_version"], int) or profile["schema_version"] != 1:
        raise ProfileError("schema_version must be 1")
    if nested(profile, "scope.tax_year") != SUPPORTED_TAX_YEAR:
        raise ProfileError(f"scope.tax_year must be {SUPPORTED_TAX_YEAR}; use a matching skill for another year")

    enums: dict[str, set[Any]] = {
        "scope.lodgment_path": {"accountant", "mytax", "amendment", "estimate-only", None},
        "scope.residency_status": {
            "full-year-resident",
            "part-year-resident",
            "foreign-resident",
            "temporary-resident",
            "unsure",
            None,
        },
        "records.ato_prefill_status": {
            "official-agent-prefill",
            "mytax-prefilled",
            "saved-mytax-draft",
            "not-available",
            None,
        },
    }
    for path, allowed in enums.items():
        if nested(profile, path) not in allowed:
            options = ", ".join(sorted(repr(item) for item in allowed))
            raise ProfileError(f"{path} must be one of: {options}")

    for path, maximum in (("identity.display_name", 100), ("identity.occupation", 150)):
        value = nested(profile, path)
        if not isinstance(value, str):
            raise ProfileError(f"{path} must be a string")
        validate_text(value, path, maximum)

    dependants = nested(profile, "household.dependent_children_count")
    if dependants is not None and (isinstance(dependants, bool) or not isinstance(dependants, int) or dependants < 0):
        raise ProfileError("household.dependent_children_count must be a non-negative integer or null")

    employers = nested(profile, "employment.employers")
    if not isinstance(employers, list) or not all(isinstance(item, str) for item in employers):
        raise ProfileError("employment.employers must be an array of strings")
    for index, employer in enumerate(employers):
        validate_text(employer, f"employment.employers[{index}]", 150)

    special_paths = set(enums) | {
        "schema_version",
        "scope.tax_year",
        "identity.display_name",
        "identity.occupation",
        "household.dependent_children_count",
        "employment.employers",
    }
    for path, value in leaf_values(profile):
        if path in special_paths:
            continue
        if value is not None and not isinstance(value, bool):
            raise ProfileError(f"{path} must be true, false, or null")


def validate_shape(profile: dict[str, Any], template: dict[str, Any], path: str = "") -> None:
    actual = set(profile)
    expected = set(template)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    label = path or "profile"
    if missing:
        raise ProfileError(f"{label} is missing field(s): {', '.join(missing)}")
    if extra:
        raise ProfileError(f"{label} has unsupported field(s): {', '.join(extra)}")
    for key, example in template.items():
        child_path = f"{path}.{key}" if path else key
        value = profile[key]
        if isinstance(example, dict):
            if not isinstance(value, dict):
                raise ProfileError(f"{child_path} must be an object")
            validate_shape(value, example, child_path)


def leaf_values(value: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
    leaves: list[tuple[str, Any]] = []
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            leaves.extend(leaf_values(item, path))
        else:
            leaves.append((path, item))
    return leaves


def flag(profile: dict[str, Any], dotted: str) -> bool | None:
    value = nested(profile, dotted)
    return value if isinstance(value, bool) else None


def add(rows: list[tuple[str, str, str]], item: str, why: str, status: str = "Obtain") -> None:
    rows.append((item, why, status))


def ask_if_unknown(profile: dict[str, Any], dotted: str, question: str, questions: list[str]) -> None:
    if nested(profile, dotted) is None:
        questions.append(question)


def build(profile: dict[str, Any]) -> str:
    validate_profile(profile)
    raw_display_name = nested(profile, "identity.display_name")
    # Rendered on a plain line rather than in a table, so no cell escaping is
    # applied; validate_text has already rejected newlines and control characters.
    display_name = str(raw_display_name or "[display name / initials]")

    required: list[tuple[str, str, str]] = []
    conditional: list[tuple[str, str, str]] = []
    priority_questions: list[str] = []
    questions: list[str] = []
    review_gates: list[str] = []

    if not raw_display_name:
        priority_questions.append("What display name or initials should be used in the working papers?")
    if nested(profile, "scope.lodgment_path") is None:
        priority_questions.append("Is the FY26 work for an accountant, myTax, an amendment, or an estimate only?")

    residency = nested(profile, "scope.residency_status")
    if residency in (None, "unsure"):
        priority_questions.append("What was the taxpayer's Australian tax-residency status for 2025-26?")
    elif residency != "full-year-resident":
        review_gates.append(
            "Residency is not confirmed as full-year Australian resident. Gather arrival/departure, domicile, home, family, work, treaty, and Medicare facts; obtain specialist review before applying ordinary resident assumptions."
        )

    if flag(profile, "scope.deceased_return") is True:
        review_gates.append("This is a deceased-estate/final individual return; obtain registered-tax-agent review of period, representative, and estate issues.")
    elif flag(profile, "scope.deceased_return") is None:
        questions.append("Is this a return for a living taxpayer rather than a deceased-estate/final individual return?")

    prefill = nested(profile, "records.ato_prefill_status")
    if prefill == "official-agent-prefill":
        add(required, "Official FY26 ATO/tax-agent pre-filling report", "Anchor for reconciliation of income, withholding, health, and reported data.", "Confirm/reconcile")
    elif prefill == "mytax-prefilled":
        add(required, "FY26 myTax pre-filled data export or screenshots", "Reconcile pre-filled data to source documents.", "Confirm/reconcile")
    elif prefill == "saved-mytax-draft":
        add(conditional, "Official FY26 pre-fill report or pre-filled data", "A saved myTax draft may include user-entered or carried-forward tool data.")
        review_gates.append("Available myTax material is a saved draft/customer copy, not official pre-fill. Label the assessment preliminary until reconciled.")
    elif prefill == "not-available":
        review_gates.append("FY26 pre-fill is not available. Label any result preliminary and reconcile later.")
    else:
        priority_questions.append("Is FY26 official pre-fill, myTax pre-filled data, only a saved myTax draft, or no pre-fill available?")

    for field, label, why in (
        ("records.prior_year_return_available", "Prior-year lodged return", "Recurring items, losses, and schedule comparison."),
        ("records.prior_year_noa_available", "Prior-year Notice of Assessment", "Prior assessment and account context."),
    ):
        value = flag(profile, field)
        if value is True:
            add(required, label, why, "Confirm/reconcile")
        elif value is False:
            add(conditional, f"{label}, if obtainable", why, "If obtainable")
        else:
            questions.append(f"Is the {label.lower()} available?")

    refund_account = flag(profile, "records.refund_account_available_to_lodger")
    lodgment_path = nested(profile, "scope.lodgment_path")
    if lodgment_path in ("accountant", "mytax", "amendment") and refund_account is not True:
        questions.append("Will valid Australian refund-account details be provided directly to the lodger? Do not put the identifiers in this profile.")

    spouse = flag(profile, "household.had_spouse")
    if spouse is True:
        add(required, "Spouse income-test details", "Medicare, private health, offsets, and other income tests.")
        if flag(profile, "household.spouse_income_details_available") is False:
            review_gates.append("Spouse income-test details are missing; Medicare/private-health and some offset results may be unreliable.")
    elif spouse is None:
        priority_questions.append("Did the taxpayer have a spouse or de facto partner at any time during 2025-26?")

    dependants = nested(profile, "household.dependent_children_count")
    if isinstance(dependants, int) and dependants > 0:
        add(required, "Dependant details and relevant status dates", "Family Medicare/private-health thresholds and cover tests.")
    elif dependants is None:
        priority_questions.append("How many dependant children were relevant during 2025-26?")

    private_health = flag(profile, "household.private_hospital_cover")
    if private_health is True:
        add(required, "Private health insurance statement or FY26 pre-fill details", "Covered periods, benefit codes, premiums, and rebate reconciliation.")
        if flag(profile, "household.private_health_changed_during_year") is True:
            add(required, "Private hospital-cover start/end and policy-change records", "MLS and rebate may require day or period apportionment.")
    elif private_health is None:
        questions.append("Did the taxpayer hold appropriate private hospital cover during 2025-26, and did it change?")

    medicare_gap = flag(profile, "household.medicare_exemption_or_entitlement_gap")
    if medicare_gap is True:
        add(required, "Medicare Entitlement Statement or other exemption evidence", "Supports exempt days or entitlement-gap treatment.")
    elif medicare_gap is None:
        questions.append("Were there any Medicare entitlement gaps or exemption circumstances during the year?")

    salary = flag(profile, "employment.has_salary_or_wages")
    employers = nested(profile, "employment.employers") or []
    if salary is True:
        if employers:
            named = ", ".join(str(employer) for employer in employers)
            add(
                required,
                f"Tax-ready income statement/payment summary for each of {len(employers)} employer(s): {named}",
                "Salary, allowances, withholding, RFBA, and reportable employer super. Confirm every employer is marked Tax ready.",
            )
        else:
            add(required, "Tax-ready income statement/payment summary for each employer", "Salary, allowances, withholding, RFBA, and reportable employer super.")
            questions.append("Which employers paid salary or wages during 2025-26? Naming them confirms no income statement is missed.")
        add(conditional, "Final payslip for each employer", "Useful for payroll and 12% super-guarantee reconciliation.", "If useful")
    elif salary is None:
        priority_questions.append("Did the taxpayer receive salary, wages, or employment income?")

    employment_rows = (
        ("employment.has_allowances_or_lump_sums", "Allowance, bonus, termination, or lump-sum statements", "Correct income category and withholding."),
        ("employment.has_government_payments", "Government-payment statements", "Assessable/exempt payment and withholding reconciliation."),
        ("employment.has_salary_packaging_or_novated_lease", "Salary-packaging or novated-lease statement", "RFBA and income-test treatment."),
    )
    for field, item, why in employment_rows:
        if flag(profile, field) is True:
            add(conditional, item, why)

    if flag(profile, "employment.has_reportable_fringe_benefits") is True:
        add(conditional, "Reportable fringe benefits details", "MLS, study-loan, Division 293, and other income tests.")
    if flag(profile, "employment.has_reportable_employer_super") is True:
        add(conditional, "Reportable employer super details", "Study-loan, Division 293, and other income tests.")
    if flag(profile, "employment.works_from_home") is True:
        add(conditional, "Full-period work-from-home hours record", "Required for the FY26 fixed-rate method.")
        add(conditional, "Evidence for each covered running-expense category actually incurred", "Supports fixed-rate eligibility; covered costs cannot be double claimed.")
    if flag(profile, "employment.has_other_work_related_deductions") is True:
        add(conditional, "Work-expense receipts and work-use basis", "Substantiation and apportionment of proposed deductions.")
    if flag(profile, "employment.has_car_or_travel_claim") is True:
        add(conditional, "Car/travel records", "Work kilometres per car or logbook/odometer/cost records; FY26 cents-per-kilometre cap and rate must be applied.")

    claims_work_expenses = any(
        flag(profile, f"employment.{field}") is True
        for field in ("works_from_home", "has_other_work_related_deductions", "has_car_or_travel_claim")
    )
    occupation = nested(profile, "identity.occupation")
    if claims_work_expenses:
        if occupation:
            add(
                conditional,
                f"ATO occupation and industry guide for: {occupation}",
                "Confirms which work expenses are ordinarily deductible for this occupation and which are commonly disallowed.",
                "Check",
            )
        else:
            questions.append(
                "What was the taxpayer's occupation? It determines which ATO occupation guide applies to the work-expense claims."
            )

    investment = "investments_and_business"
    if flag(profile, f"{investment}.has_bank_interest") is True:
        add(required, "Bank interest summaries", "Interest, TFN withholding, and joint ownership proportions.")
    if flag(profile, f"{investment}.has_australian_dividends") is True:
        add(conditional, "Dividend statements and registry history", "Franked/unfranked amounts, credits, withholding, ownership, and DRP.")
    if flag(profile, f"{investment}.has_managed_funds_etfs_or_trusts") is True:
        add(conditional, "ETF, managed-fund, AMIT, and trust annual tax statements", "Trust labels, credits, capital gains, foreign income, and cost-base adjustments.")
    if flag(profile, f"{investment}.disposed_of_cgt_assets") is True:
        add(conditional, "CGT transaction records and auditable calculation", "Dates, cost base, proceeds, adjustments, losses, and discount eligibility.")
        add(conditional, "CGT schedule working papers, if current-year capital gains exceed $10,000", "FY26 schedule trigger and return reconciliation.", "If threshold met")
    if flag(profile, f"{investment}.has_drp") is True:
        add(conditional, "DRP statements or registry transaction history", "Acquisition dates and cost bases for reinvested dividends.")
    if flag(profile, f"{investment}.has_foreign_income") is True:
        add(conditional, "Foreign income, foreign tax/FITO, country, allocation, and FX records by income type", "Employment, pension, rental, investment, and entity income require source-specific reconciliation.")
        review_gates.append("Foreign income/tax is present; confirm source, residency, treaty, attribution, and FITO treatment with a registered tax agent where material.")
    if flag(profile, f"{investment}.foreign_assets_over_aud_50000") is True:
        add(conditional, "Foreign-asset ownership/value details", "Supports the FY26 foreign-assets disclosure question.")
    if flag(profile, f"{investment}.has_crypto") is True:
        add(conditional, "Complete crypto exchange, wallet, AUD-valuation, fee, DeFi/NFT, and same-owner transfer records", "Distinguishes transfers from CGT and income events across swaps, gifts, rewards, wrapping, bridges, and liquidity pools.")
        review_gates.append("Crypto activity is present; use a reconstructable transaction history and escalate unresolved classification or cost-base issues.")
    if flag(profile, f"{investment}.has_rental_property") is True:
        add(conditional, "Rental ownership, availability/private-use, income, loan tracing, repair/improvement, and depreciation records", "Rental schedule, apportionment, capital/revenue, and deduction reconciliation.")
        review_gates.append("Rental activity is present; obtain registered-tax-agent review for capital/revenue, interest, private use, and depreciation issues.")
    if flag(profile, f"{investment}.has_partnership_or_trust_income") is True:
        add(conditional, "Partnership/trust statements and distribution advice", "Reconcile issuer labels to any FY26 pre-fill detail.")
        review_gates.append("Partnership/trust income is present; reconcile the statement and obtain agent review of complex or discrepant allocations.")
    if flag(profile, f"{investment}.has_sole_trader_business_or_psi") is True:
        add(conditional, "Business/PSI status, accounting basis, TPAR/grants, stock, BAS/GST, asset, loss, and prior-schedule records", "Income, expenses, depreciation, non-commercial losses, and PSI tests.")
        review_gates.append("Business or PSI activity is present; obtain registered-tax-agent review of schedule, loss, depreciation, and PSI treatment.")

    investment_unknown_labels = [
        label
        for key, label in (
            ("has_bank_interest", "bank interest"),
            ("has_australian_dividends", "Australian dividends"),
            ("has_managed_funds_etfs_or_trusts", "managed funds, ETFs, or trusts"),
            ("disposed_of_cgt_assets", "CGT disposals"),
            ("has_drp", "dividend reinvestment"),
            ("has_foreign_income", "foreign income"),
            ("has_crypto", "crypto activity"),
        )
        if nested(profile, f"{investment}.{key}") is None
    ]
    if investment_unknown_labels:
        priority_questions.append(
            "Were any of these still-unconfirmed investment categories relevant: "
            + ", ".join(investment_unknown_labels)
            + "?"
        )

    business_unknown_labels = [
        label
        for key, label in (
            ("has_rental_property", "rental property"),
            ("has_partnership_or_trust_income", "partnership or trust income"),
            ("has_sole_trader_business_or_psi", "sole-trader, business, or PSI activity"),
        )
        if nested(profile, f"{investment}.{key}") is None
    ]
    if business_unknown_labels:
        questions.append("Were any of these still-unconfirmed categories relevant: " + ", ".join(business_unknown_labels) + "?")

    ess = flag(profile, "employee_share_plans.has_ess_rsus_options_or_espp")
    if ess is True:
        add(conditional, "ESS statement from each employer, plan rules, startup-concession status, and prior deferred-taxing-point records", "Establishes the ESS taxing point, discount, and withholding basis.")
        review_gates.append("Employee equity is present; reconcile ESS income and later CGT separately and escalate cross-border or deferred-taxing-point issues.")

        vested = flag(profile, "employee_share_plans.had_vest_exercise_or_sale")
        if vested is True:
            add(conditional, "Grant, vest, exercise, cessation, restructure, and sale records with market values, amounts paid, and FX at each taxing point", "Fixes the taxing-point amount and the acquisition cost base for any later disposal.")
        elif vested is None:
            questions.append("Were there any employee-equity vesting, exercise, or sale events during 2025-26?")

        retained = flag(profile, "employee_share_plans.retained_shares")
        if retained is True:
            add(conditional, "Year-end holding records and a cost-base bridge from the ESS taxing point to later CGT", "Retained shares carry a cost base set at the taxing point; without the bridge, a later disposal is miscalculated.")
        elif retained is None:
            questions.append("Were any shares acquired under employee equity still held at 30 June 2026?")

        cross_border = flag(profile, "employee_share_plans.foreign_employer_or_overseas_workdays")
        if cross_border is True:
            add(conditional, "Foreign-employer plan details, overseas-workday calendar, source-allocation basis, and foreign tax withheld", "Cross-border equity must be apportioned by workday source before FITO or treaty relief is considered.")
            review_gates.append("Employee equity involves a foreign employer or overseas workdays; obtain registered-tax-agent confirmation of source allocation, treaty position, and FITO before relying on any figure.")
        elif cross_border is None:
            questions.append("Was the employee equity granted by a foreign employer, or does it relate to overseas workdays?")
    elif ess is None:
        questions.append("Did the taxpayer have ESS, RSUs, options, ESPP, or other employee-equity activity?")

    if flag(profile, "super_and_loans.super_statement_available") is True:
        add(conditional, "Super annual statement/contribution history", "Contribution caps and Division 293 context where relevant.", "Confirm/reconcile")
    if flag(profile, "super_and_loans.made_personal_super_contributions") is True:
        add(conditional, "Personal-super contribution receipt and acknowledged notice of intent", "Required before claiming a personal-super deduction.")
        if flag(profile, "super_and_loans.notice_of_intent_acknowledged") is not True:
            review_gates.append("A personal-super deduction is contemplated but an acknowledged notice of intent is not confirmed.")
    if flag(profile, "super_and_loans.has_division_293_or_excess_contributions") is True:
        add(conditional, "Division 293 or excess-contribution determination", "Separate assessment and contribution-cap review.")
    if flag(profile, "super_and_loans.has_study_or_training_loan") is True:
        add(conditional, "ATO study/training-loan account and FY26 withholding details", "Apply the FY26 marginal repayment system and reconcile any 20% account reduction.")

    deduction_rows = (
        ("deductions_and_offsets.has_tax_agent_fees", "Tax-agent fee invoices paid in 2025-26", "Potential tax-affairs deduction."),
        ("deductions_and_offsets.has_donations", "Gift/contribution receipts and classification evidence", "Apply ordinary DGR or the relevant political, property-gift, or material-benefit contribution rules."),
        ("deductions_and_offsets.has_income_protection", "Income-protection premium statement", "Eligibility and private/capital exclusions."),
        ("deductions_and_offsets.has_ato_interest_charges", "ATO GIC/SIC transaction details split by incurred date", "Charges incurred on or after 1 July 2025 are not deductible."),
        ("deductions_and_offsets.has_other_deductions_or_offsets", "Source records for other deductions or offsets", "Eligibility, amount, and income-test treatment."),
        ("deductions_and_offsets.has_carried_forward_capital_losses", "Prior-year carried-forward capital-loss record", "Net capital gain/loss calculation."),
        ("deductions_and_offsets.has_carried_forward_tax_losses", "Prior-year carried-forward tax-loss record", "Tax-loss availability and utilisation."),
    )
    for field, item, why in deduction_rows:
        if flag(profile, field) is True:
            add(conditional, item, why)

    if flag(profile, "payg.payg_instalments_issued") is True:
        add(required, "PAYG instalment notices and account/payment evidence", "Keep instalment credits separate from PAYG withholding.")
    elif flag(profile, "payg.payg_instalments_issued") is None:
        questions.append("Were PAYG instalments issued or paid for 2025-26?")

    lines = [
        "# FY26 ITR File Checklist",
        "",
        f"Taxpayer display name: {display_name}",
        f"Income year: {SUPPORTED_TAX_YEAR}",
        f"Prepared: {date.today().isoformat()}",
        "",
        "This checklist supports preparation and registered-tax-agent review. It is not tax advice.",
        "",
    ]
    lines.extend(table("Evidence To Obtain Or Reconcile", required))
    lines.extend(table("Conditional Evidence", conditional))

    if review_gates:
        lines.extend(["## Review Gates", ""])
        for gate in review_gates:
            lines.append(f"- {gate}")
        lines.append("")

    all_questions = list(dict.fromkeys(priority_questions + questions))
    if all_questions:
        shown = all_questions[:MAX_NEXT_QUESTIONS]
        lines.extend(["## Next Intake Questions", ""])
        for index, question in enumerate(shown, 1):
            lines.append(f"{index}. {question}")
        remaining = len(all_questions) - len(shown)
        if remaining:
            lines.extend(["", f"Continue intake after this batch; {remaining} additional question(s) remain."])
        lines.append("")

    return "\n".join(lines)


def table_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|")


def table(title: str, rows: list[tuple[str, str, str]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not rows:
        lines.extend(
            ["Nothing triggered yet. Answer the intake questions below to populate this section.", ""]
        )
        return lines
    lines.extend(["| Item | Why needed | Status |", "|---|---|---|"])
    for item, why, status in rows:
        lines.append(f"| {table_cell(item)} | {table_cell(why)} | {table_cell(status)} |")
    lines.append("")
    return lines


def profile_template() -> str:
    return template_path().read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, help="Path to a complete FY26 client-profile JSON.")
    parser.add_argument("--out", type=Path, help="Optional Markdown output path outside the skill directory.")
    parser.add_argument("--force", action="store_true", help="Allow replacement of an existing --out file.")
    parser.add_argument("--init-profile", action="store_true", help="Print the blank share-safe FY26 profile template.")
    args = parser.parse_args(argv)

    try:
        if args.init_profile:
            if args.profile or args.out:
                raise ProfileError("--init-profile cannot be combined with --profile or --out")
            print(profile_template(), end="")
            return 0
        if not args.profile:
            raise ProfileError("--profile is required unless --init-profile is used")

        profile = load_json(args.profile)
        markdown = build(profile)
        if args.out:
            if args.out.exists() and not args.force:
                raise ProfileError(f"refusing to overwrite existing output: {args.out}; use --force to replace it")
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(markdown + "\n", encoding="utf-8")
        else:
            print(markdown)
        return 0
    except (ProfileError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
