# FY26 Intake Questionnaire

Use this to build a `2025-26` profile before requesting documents. Ask in short batches, beginning with scope, residency, household, and major income categories. Stop once enough facts exist to generate a useful checklist.

Because each batch is short, order matters. Ask in three tiers: scope facts that change how everything else is treated; then facts that move the tax outcome or open a review gate, such as residency detail, employee equity, foreign involvement, and Medicare or private-health status; then completeness and record-hygiene confirmations. A working-papers convenience such as a display name is a hygiene question, not a scope question; the checklist renders a placeholder without it.

Do not request a TFN, myGov credentials, MFA codes, passwords, or full bank identifiers. A display name or initials is sufficient.

## First Batch: Scope

- Display name or initials for the working papers.
- Confirm income year `2025-26`, ended 30 June 2026.
- Residency status: full-year Australian resident, part-year resident, foreign resident, temporary resident, or unsure.
- Lodgment path: accountant, myTax, amendment, or estimate only.
- Prior-year lodged return and Notice of Assessment available?
- Official ATO/tax-agent pre-fill available, myTax pre-filled data only, saved myTax draft/customer copy only, or none yet?
- Any PAYG instalments, ATO debts/payment plans, or study and training loan accounts?

## Household, Medicare, And Private Health

- Spouse/de facto status and dates during the year, including spouse details at 30 June.
- Whether the spouse income-test details are available: taxable income, reportable fringe benefits, reportable super, net investment losses, tax-free government pensions, relevant foreign income, and relevant super lump sums.
- Each dependant's date of birth, student status, adjusted taxable income, maintenance facts, and coverage period.
- Private hospital cover for taxpayer, spouse, and dependants: insured-person age bands, hospital versus extras cover, insurers, covered days/periods, policy and family-status changes, benefit codes, premiums, and rebate information.
- Any Medicare entitlement gaps, exemption certificates, or low-income/family reduction circumstances.

## Employment And Other Payments

- Employers and employment periods; are all income statements tax ready?
- Allowances, bonuses, commissions, termination payments, paid parental leave, workers compensation, or government payments.
- Reportable fringe benefits, salary packaging, novated leases, and reportable employer super.
- Work-from-home dates and hours records.
- Occupation, where any work expense is claimed. It selects the ATO occupation and industry guide that governs which claims are ordinarily deductible.
- Work expenses: tools, equipment, phone/internet, subscriptions, training, memberships, uniforms, travel, and car use.
- Reimbursements or employer-provided items relating to any proposed deduction.

## Investments, Property, And Business

- Interest-bearing and joint accounts, including ownership proportions.
- Australian dividends, franking credits, DRP participation, ETFs, managed funds, trusts, and annual tax statements.
- Disposals of shares, units, property, crypto, collectables, personal-use assets, or other CGT assets.
- Broker/platform exports, contract notes, registry history, corporate actions, and carried-forward capital losses.
- Foreign employment, pensions, rent, investments, entities/attributed income, country, gross amount, foreign tax paid, FX method/date, workday or residency allocation, foreign return, and whether foreign assets totalled at least AUD 50,000 at any time.
- Rental ownership and acquisition/disposal facts, leases and availability listings, private/holiday-use calendar, floor-area basis, loan/refinance tracing, repairs versus improvements, capital works/depreciation, platform income, bonds, and insurance.
- Partnership/trust distributions, sole-trader/business/PSI activity, or sharing-economy/side-hustle income. For business, capture ABN/status, cash/accrual basis, TPAR, grants, opening/closing stock, BAS/GST, asset register, and non-commercial losses.
- Crypto disposals, swaps, gifts, staking, airdrops, mining/rewards, NFTs, DeFi, wrapped assets, bridges, liquidity pools, fees, AUD value/valuation source, wallet addresses, same-owner wallet transfers, and exchange/wallet/tax-software completeness.

## ESS, RSUs, Options, And ESPP

- ESS statement from each employer, or written details from a foreign employer, plus award/plan rules.
- Grants, associate acquisitions, vests, exercises, sales, dividend equivalents, tax withheld, and retained shares.
- Startup-concession status, prior-year deferred taxing points, and foreign-employer or overseas-workday facts.
- Cessation, restructures, corporate actions, market values, and FX rates used at taxing points and disposals. Ceasing employment is not, by itself, a deferred taxing point.

## Super, Loans, Deductions, And Offsets

- Super statements, personal contributions, and notice-of-intent acknowledgement.
- Division 293 or excess-contribution determinations.
- HELP, VSL, SFSS, SSL, ABSTUDY SSL, or AASL account/repayment information needed for an estimate.
- Tax-agent fees, income-protection premiums, professional fees/training, and other proposed deductions.
- Gifts, donations, political contributions, property gifts, or contributions involving a material benefit; capture the type, recipient, receipt, and either ordinary DGR evidence or the facts required by the relevant special rule.
- Carried-forward tax losses, capital losses, foreign income tax offsets, or other recurring schedules.

## Profile Mapping

Map answers to `assets/templates/client-profile.example.json`. Use `true`, `false`, or `null` for booleans and the documented enum values for status fields. Do not guess. Store actual source amounts in the source register rather than expanding the intake profile into a second tax return.
