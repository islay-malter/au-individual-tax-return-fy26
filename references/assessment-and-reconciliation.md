# FY26 Assessment And Reconciliation

Use this after intake and evidence collection. The goal is an auditable working assessment, not a substitute for professional advice.

## Classify The Evidence

Tag each source as one of:

- `official-prefill`: ATO or tax-agent pre-filling report/data.
- `mytax-prefilled`: values displayed as pre-filled inside myTax.
- `mytax-draft`: saved return/customer-copy output that may include user-entered or carried-forward tool data.
- `issuer-document`: employer, bank, registry, fund, insurer, broker, platform, charity, or other issuer evidence.
- `transaction-record`: contract note, invoice, receipt, CSV, statement, or contemporaneous log.
- `taxpayer-fact`: a fact confirmed by the taxpayer but not yet documented.
- `calculation`: a derived amount with formula and input sources.

A document that says it cannot be used to lodge a return but displays return labels or taxable income is normally a saved myTax draft/customer copy unless clearly identified as a pre-filling report.

## Source Register Minimum Fields

For every amount used, capture:

- area and return label/use;
- source file or user-confirmed fact;
- page, section, row, or transaction reference where available;
- gross amount, withholding/credit, ownership split, and currency/FX basis as relevant;
- evidence class and confidence;
- reconciliation status and unresolved questions.

Never copy TFNs, credentials, account identifiers, or unrelated identifiers into the register.

## Reconciliation Rules

- Reconcile issuer documents and transaction records against pre-fill; investigate differences rather than choosing one silently.
- Pre-fill is evidence, not proof that an item is complete, correct, or deductible.
- A pre-filled depreciation/capital-allowance amount may be saved tool data. Obtain the underlying asset and substantiation before including it.
- Reconcile joint accounts and holdings to legal/economic ownership rather than defaulting to an even split without evidence.
- Reconcile AMIT cost-base adjustments, DRP acquisitions, corporate actions, brokerage, FX, and carried-forward losses before relying on a CGT summary.
- Reconcile ESS income and later CGT separately; a platform sale total does not establish the correct ESS taxing point or CGT cost base.
- Reconcile trust distributions to the issuer annual statement even when FY26 trust detail is pre-filled.
- Classify each gift or contribution first. Apply ordinary DGR rules to ordinary gifts, and apply the separate political-contribution, property-gift, or material-benefit contribution rules when those facts are present.
- Track PAYG withholding and PAYG instalments separately.

## Calculation Gates

Before calculating, confirm:

- The package is within its `reverify-by` date, or its material official sources have been revalidated and the package metadata updated.
- `2025-26` income year and relevant residency basis.
- Official sources and access date for every material rate, threshold, label, and record rule.
- Income for Medicare levy surcharge/private-health purposes, spouse/family status, dependants, and cover days.
- Study/training-loan repayment income and the FY26 marginal repayment formula.
- Taxable income, offsets, credits, Medicare treatment, and PAYG amounts all reconcile to sources.

For part-year/foreign/temporary residency, foreign tax, deceased estates, ESS with cross-border service, complex trusts, crypto reconstruction, rental/business/PSI schedules, and unusual CGT events, prepare evidence and scenarios but require registered-tax-agent confirmation before presenting a single treatment as settled.

## Working Calculation Order

This is a documentation and reconciliation sequence, not a deterministic calculator. Unless a separate deterministic tool is explicitly used and named, label the result `Unchecked model-produced working scenario` until an independent method, myTax, or a registered tax agent has checked it.

1. Reconcile assessable income by label/category.
2. Reconcile deductions and identify substantiation gaps.
3. Calculate taxable income under the supported residency assumptions.
4. Apply FY26 income-tax rates and offsets.
5. Apply Medicare levy, any reduction/exemption, MLS, and private-health rebate adjustment.
6. Apply FY26 study/training-loan compulsory repayment where relevant.
7. Apply refundable/non-refundable credits, PAYG withholding, and PAYG instalments.
8. Present payable/refund scenarios and sensitivity to unresolved items.

Show every input, formula, intermediate component, and final reconciliation. Do not silently net items that appear separately on an assessment. Keep tax, Medicare, study-loan repayment, credits, withholding, and instalments visible.

## Final Review

- Every amount maps to a source or labelled assumption.
- Every material discrepancy has an explanation or question.
- Proposals and later-year changes are excluded.
- The result states whether it is preliminary, source-reconciled, or ready for agent review.
- The arithmetic status is `Unchecked model-produced working scenario` or names the independent check and records its reconciliation.
- Material tax-dollar issues are separate from zero-dollar or factual-consistency issues.
