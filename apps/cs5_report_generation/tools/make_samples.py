"""Author's tool: builds the three sample workbooks in samples/ from the synthetic data below.

    python tools/make_samples.py

Not needed to run the app. It writes one Excel workbook per fictitious insurer: figures for 2021-2026 (inputs typed,
totals and ratios as Excel formulas with their values cached), driver bullets for 2022-2026, the E.1 and E.2 texts
"published" for 2022-2025, the house phrases and the terminology. Every text is written as a template whose figures
are placeholders and whose movement words come from the house phrases, then rendered; the script asserts that the
app's own reader recovers exactly these placeholders from the rendered text, so that the old method of the app
(last year's text, figures updated) and the examples given to the model are built on the intended links.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import xlsxwriter

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

import report_core as rc  # noqa: E402

YEARS = [2021, 2022, 2023, 2024, 2025, 2026]
HISTORY = [2022, 2023, 2024, 2025]
CURRENT = 2026
OUT_DIR = APP_DIR / "samples"


def ph(pid: str) -> str:
    return "{{" + pid + "}}"


def series(**columns: list[float]) -> dict[int, dict[str, float]]:
    """Inputs by year from one list of six values (2021-2026) per input metric."""
    out = {y: {} for y in YEARS}
    for mid, values in columns.items():
        assert mid in rc.INPUT_IDS, mid
        assert len(values) == len(YEARS), mid
        for y, v in zip(YEARS, values):
            out[y][mid] = float(v)
    for y in YEARS:
        for mid in rc.INPUT_IDS:
            out[y].setdefault(mid, 0.0)
    return out


def with_equity(inputs: dict[int, dict[str, float]]) -> None:
    """Equity in the financial statements = excess of assets over liabilities minus the reconciliation items, where
    the excess of assets over liabilities = basic own funds + foreseeable dividends - subordinated liabilities."""
    for y, v in inputs.items():
        eaol = (Decimal(str(v["of_t1"])) + Decimal(str(v["of_t2"])) + Decimal(str(v["of_t3"]))
                + Decimal(str(v["foreseeable_div"])) - Decimal(str(v["sub_liab"])))
        items = sum(Decimal(str(v[k])) for k in ("rec_tp", "rec_intangibles", "rec_dt", "rec_other"))
        v["equity_fs"] = float(eaol - items)


# ---------------------------------------------------------------------------
# House phrases (one bank per company) and terminology
# ---------------------------------------------------------------------------

def phrase_bank(stable: str, small: tuple[str, str], mid: tuple[str, str], large: tuple[str, str]) -> list[dict]:
    rows = []
    for applies, bounds in (("amount", (1.0, 5.0, 15.0)), ("ratio", (2.0, 10.0, 25.0))):
        b1, b2, b3 = bounds
        rows += [
            {"applies_to": applies, "from": 0.0, "to": b1, "up": stable, "down": stable},
            {"applies_to": applies, "from": b1, "to": b2, "up": small[0], "down": small[1]},
            {"applies_to": applies, "from": b2, "to": b3, "up": mid[0], "down": mid[1]},
            {"applies_to": applies, "from": b3, "to": 1e9, "up": large[0], "down": large[1]},
        ]
    return rows


# ---------------------------------------------------------------------------
# Brisendale Mutual: the insurer of the Case Study 5 notebook (2025 and 2026 figures identical to the notebook)
# ---------------------------------------------------------------------------

BRISENDALE_INPUTS = series(
    scr_market=[172.9, 168.4, 181.2, 195.7, 206.0, 211.3],
    scr_default=[24.1, 25.7, 27.4, 30.2, 33.1, 46.2],
    scr_nonlife=[219.8, 231.5, 240.9, 252.3, 260.8, 216.9],
    div_benefit=[101.7, 104.6, 110.3, 123.5, 128.8, 116.9],
    scr_operational=[32.6, 33.9, 35.1, 36.6, 37.8, 38.4],
    lac_dt=[21.3, 22.5, 24.0, 25.4, 26.2, 22.8],
    mcr=[95.2, 97.3, 104.6, 113.8, 118.6, 108.7],
    of_t1=[636.1, 612.8, 674.8, 636.3, 700.2, 748.2],
    of_t2=[0.0, 0.0, 0.0, 61.9, 61.9, 61.9],
    of_t3=[12.9, 19.4, 18.1, 17.5, 16.8, 10.5],
    sub_liab=[0.0, 0.0, 0.0, 61.9, 61.9, 61.9],
    rec_tp=[24.3, 21.7, 27.9, 25.6, 29.4, 32.1],
    rec_intangibles=[-36.9, -38.5, -41.2, -44.0, -46.3, -48.6],
    rec_dt=[-4.1, -3.6, -4.8, -4.3, -5.2, -6.7],
)
with_equity(BRISENDALE_INPUTS)

BRISENDALE_TEXT = {
    "company_id": "brisendale",
    "company_name": "Brisendale Mutual",
    "legal_form": "a mutual insurance undertaking owned by its policyholder members; it has no shareholders",
    "lines_of_business": "motor insurance and home insurance (non-life); home insurance in Lithuania under the "
                         "freedom to provide services since 2025",
    "home_member_state": "Ireland",
    "supervisor": "Home Supervisory Authority (fictitious placeholder)",
    "fictitious_note": "Brisendale Mutual is a fictitious insurer created for teaching; all figures are synthetic. "
                       "Its 2025 and 2026 figures are those of the Case Study 5 notebook.",
    "appetite_low": "160",
    "appetite_high": "",
    "capital_policy": "Hold enough capital of good quality to meet the obligations to policyholder members at all "
                      "times and to cover the SCR with a margin; the Board approves the capital management policy "
                      "and reviews it every year as part of the own risk and solvency assessment. As a mutual, "
                      "Brisendale Mutual pays no dividends; profits are retained in own funds.",
    "planning_horizon": "three years (business plan)",
    "tier1_items": "initial fund and reconciliation reserve",
    "tier2_items": "subordinated notes issued in March 2024",
    "tier3_items": "net deferred tax assets",
    "ancillary_own_funds": "none",
    "deductions_restrictions": "no items deducted; no significant restrictions on availability or transferability",
    "calculation": "standard formula",
    "simplifications": "none",
    "undertaking_specific_parameters": "none",
    "capital_add_on": "none",
    "mcr_inputs": "linear formula for non-life insurance: net best estimate of technical provisions and net written "
                  "premiums of the last twelve months for each line of business; floor 25% and cap 45% of the SCR",
    "style": "first person plural ('we', 'our'); short sentences; every movement with its size and its cause",
}

BRISENDALE_BULLETS = {
    2022: [
        ("B1", "Interest rates", "Euro interest rates rose sharply in 2022. The market value of our bond portfolio "
                                 "fell, which reduced Tier 1 own funds; the lower value of the bonds also reduced "
                                 "the capital charge for market risk."),
        ("B2", "Claims inflation", "Inflation raised the cost of motor repairs and home rebuilding. We strengthened "
                                   "our claims provisions, which reduced Tier 1 own funds."),
        ("B3", "Premium growth", "Higher average premiums increased premium volumes; this increased premium and "
                                 "reserve risk in non-life underwriting risk and raised the MCR."),
        ("B4", "Deferred taxes", "Unrealised losses on bonds increased the net deferred tax assets, which are "
                                 "classified as Tier 3."),
    ],
    2023: [
        ("B1", "Underwriting result", "A year without major storms produced a strong underwriting result, which "
                                      "increased Tier 1 own funds."),
        ("B2", "Bond values", "Euro interest rates fell towards the end of 2023; the higher market value of our "
                              "bonds increased own funds and the capital charge for market risk."),
        ("B3", "Premium growth", "Premium growth in motor and home insurance increased non-life underwriting risk "
                                 "and the MCR."),
        ("B4", "Deferred taxes", "Net deferred tax assets fell as unrealised losses on bonds decreased."),
    ],
    2024: [
        ("B1", "Subordinated notes", "In March 2024 we issued subordinated notes, which are classified as Tier 2 "
                                     "own funds. They support our planned growth."),
        ("B2", "Floods", "Severe floods in September 2024 caused many home insurance claims; the lower underwriting "
                         "result reduced Tier 1 own funds."),
        ("B3", "Investments", "We invested the proceeds of the subordinated notes in bonds; the larger bond "
                              "portfolio increased market risk."),
        ("B4", "Reinsurance recoveries", "Amounts due from reinsurers after the floods increased counterparty "
                                         "default risk."),
        ("B5", "Growth", "Premium growth increased non-life underwriting risk and the MCR."),
    ],
    2025: [
        ("B1", "Lithuania", "In 2025 we began selling home insurance in Lithuania under the freedom to provide "
                            "services; the new business increased non-life underwriting risk and the MCR."),
        ("B2", "Result", "A good underwriting year and higher investment income increased Tier 1 own funds."),
        ("B3", "Investments", "A larger bond portfolio increased market risk."),
        ("B4", "Reinsurance", "Larger reinsurance recoverables increased counterparty default risk."),
    ],
    2026: [  # DR1-DR6 are the driver bullets of the Case Study 5 notebook; DR7 and DR8 add the capital side
        ("DR1", "Motor claims inflation", "Motor repair costs rose during the year because spare parts and labour "
                                          "became more expensive; this raised the average cost of a motor claim."),
        ("DR2", "New motor reinsurance", "From the start of the year, a new quota-share reinsurance contract passes "
                                         "a fixed share of the premiums and claims of every motor policy to "
                                         "reinsurers; this reduces the insurance risk that Brisendale Mutual keeps "
                                         "and increases the amounts owed by reinsurers."),
        ("DR3", "Interest rates", "Euro interest rates fell in the second half of the year, which increased the "
                                  "market value of the bonds that Brisendale Mutual holds."),
        ("DR4", "October windstorm", "A windstorm in October caused a large number of home insurance claims, "
                                     "mainly for roof and fence damage."),
        ("DR5", "Investment policy", "The investment policy was updated during the year to exclude companies that "
                                     "earn most of their revenue from thermal coal; the effect on investment returns "
                                     "has not been measured."),
        ("DR6", "Expenses", "Operating expenses were higher than a year earlier; the finance team has not yet "
                            "analysed the reasons."),
        ("DR7", "Deferred taxes", "Net deferred tax assets fell because the higher market value of our bonds "
                                  "reduced unrealised losses."),
        ("DR8", "MCR", "The MCR fell because the motor quota share reduced the net premiums and the net technical "
                       "provisions on which the MCR is based."),
    ],
}

BRISENDALE_PHRASES = phrase_bank("remained broadly stable", ("increased slightly", "decreased slightly"),
                                 ("increased", "decreased"), ("increased significantly", "decreased significantly"))
BRISENDALE_TERMS = [
    {"preferred": "SCR coverage ratio", "avoid": ["solvency ratio", "Solvency II ratio", "SCR ratio"],
     "note": "the ratio of eligible own funds to the SCR"},
    {"preferred": "eligible own funds", "avoid": ["available capital", "capital resources", "free capital"],
     "note": "own funds after the tier limits"},
    {"preferred": "net deferred tax assets", "avoid": ["DTA"], "note": "Tier 3 own funds; no abbreviation"},
    {"preferred": "policyholder members", "avoid": ["customers"], "note": "a mutual is owned by its members"},
]


def brisendale_templates(c: rc.Company, y: int) -> dict[str, tuple[str, str]]:
    F = rc.facts_for(c, y)
    t: dict[str, tuple[str, str]] = {}
    policy = ("Our objective in managing own funds is to hold enough capital of good quality to meet our obligations "
              "to our policyholder members at all times and to cover the Solvency Capital Requirement (SCR) with a "
              "margin. The Board approves the capital management policy and reviews it every year as part of our own "
              "risk and solvency assessment. Our business planning covers a time horizon of three years, and our "
              "risk appetite is an SCR coverage ratio of at least " + ph("appetite_low") + ". As a mutual, we pay "
              "no dividends; profits are retained in own funds. ")
    policy += {2024: "In " + ph("year_cur") + ", the Board approved the issue of subordinated notes to support our "
                     "planned growth; the policy and the processes did not change otherwise."}.get(
        y, "There were no material changes to the policy or the processes in " + ph("year_cur") + ".")
    t["e1_policy"] = (policy, "")

    s = ("At " + ph("date_cur") + ", our basic own funds amounted to " + ph("of_total_cur") + " (" + ph("year_prev")
         + ": " + ph("of_total_prev") + "). ")
    t1_cause = {
        2022: ", because the market value of our bonds fell when interest rates rose sharply and because we "
              "strengthened claims provisions for inflation",
        2023: ", mainly because a year without major storms produced a strong underwriting result and because the "
              "market value of our bonds rose",
        2024: ", mainly because the floods of September " + ph("year_cur") + " caused many home insurance claims and "
              "reduced the underwriting result",
        2025: ", mainly because of a good underwriting year and higher investment income",
    }[y]
    s += mv(F, "of_t1", "Tier 1 own funds, which consist of our initial fund and the reconciliation reserve,",
            t1_cause) + ". "
    if y == 2024:
        s += "Tier 2 own funds of " + ph("of_t2_cur") + " consist of the subordinated notes that we issued in March " \
             + ph("year_cur") + ". "
    elif y == 2025:
        s += mv(F, "of_t2", "Tier 2 own funds, which consist of the subordinated notes issued in March "
                + ph("year_prev") + ",") + ". "
    t3_cause = {2022: ", because unrealised losses on bonds increased",
                2023: ", because unrealised losses on bonds decreased"}.get(y, "")
    s += mv(F, "of_t3", "Tier 3 own funds, which consist of net deferred tax assets,", t3_cause) + ". "
    s += ("We have no Tier 2 own funds and hold no ancillary own funds. " if y < 2024
          else "We hold no ancillary own funds. ")
    s += "Table E.1 shows the own funds by tier."
    t["e1_structure"] = (s, {2022: "B1; B2; B4", 2023: "B1; B2; B4", 2024: "B1; B2", 2025: "B2"}[y])

    s = ("All our basic own funds are eligible to cover the SCR: Tier 1 exceeds half of the SCR, and Tier 3 stays "
         "below " + ph("lim_t3_scr") + " of the SCR. Eligible own funds to cover the SCR amounted to "
         + ph("eof_scr_cur") + " at " + ph("date_cur") + " (" + ph("year_prev") + ": " + ph("eof_scr_prev") + "). ")
    if y < 2024:
        s += ("To cover the Minimum Capital Requirement (MCR), Tier 3 own funds are not eligible; eligible own funds "
              "to cover the MCR amounted to ")
    else:
        s += ("To cover the Minimum Capital Requirement (MCR), Tier 3 own funds are not eligible and Tier 2 own funds "
              "are eligible up to " + ph("lim_t2_mcr") + " of the MCR; eligible own funds to cover the MCR amounted "
              "to ")
    s += (ph("eof_mcr_cur") + " (" + ph("year_prev") + ": " + ph("eof_mcr_prev") + "). No items were deducted from "
          "own funds, and there are no significant restrictions on their availability or transferability.")
    t["e1_eligibility"] = (s, "")

    s = ("Equity in our financial statements amounted to " + ph("equity_fs_cur") + " at " + ph("date_cur")
         + ", and the excess of assets over liabilities valued for solvency purposes to " + ph("eaol_cur") + " ("
         + ph("year_prev") + ": " + ph("equity_fs_prev") + " and " + ph("eaol_prev") + "). The difference arises "
         "from three valuation differences: intangible assets of " + ph("rec_intangibles_cur") + " are not "
         "recognised for solvency purposes; the valuation of technical provisions at best estimate plus risk margin "
         "is " + ph("rec_tp_cur") + " lower than in the financial statements, which adds to the excess of assets "
         "over liabilities; and the deferred taxes on these differences reduce it by " + ph("rec_dt_cur") + ".")
    t["e1_reconciliation"] = (s, "")

    s = ("At " + ph("date_cur") + ", our SCR amounted to " + ph("scr_cur") + " and our MCR to " + ph("mcr_cur") + " ("
         + ph("year_prev") + ": " + ph("scr_prev") + " and " + ph("mcr_prev") + "). With eligible own funds of "
         + ph("eof_scr_cur") + ", the SCR coverage ratio was " + ph("cov_scr_cur") + " (" + ph("year_prev") + ": "
         + ph("cov_scr_prev") + "); the MCR coverage ratio was " + ph("cov_mcr_cur") + " (" + ph("year_prev") + ": "
         + ph("cov_mcr_prev") + "). The final amount of the SCR is not subject to supervisory assessment. Table E.2 "
         "shows the SCR by risk module.")
    t["e2_amounts"] = (s, "")

    s = ("We calculate the SCR with the standard formula. We do not use simplified calculations or undertaking-"
         "specific parameters, and no capital add-on has been imposed. The MCR is calculated with the linear formula "
         "from the net best estimate of technical provisions and the net written premiums of the last twelve months "
         "for each line of business; the result is bounded by a floor of " + ph("mcr_floor") + " and a cap of "
         + ph("mcr_cap") + " of the SCR.")
    t["e2_methods"] = (s, "")

    if y == 2022:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_nonlife", "Non-life underwriting risk", ", because higher average premiums increased "
                  "premium and reserve risk") + "; "
             + mv(F, "scr_market", "market risk", ", because the market value of our bonds fell", lower=True) + ". "
             + mv(F, "mcr", "The MCR", " with the higher premiums") + ". "
             + mv(F, "cov_scr", "The SCR coverage ratio", ", because eligible own funds fell while the SCR rose")
             + ".")
        based = "B1; B3"
    elif y == 2023:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_market", "Market risk", ", because the market value of our bonds rose") + "; "
             + mv(F, "scr_nonlife", "non-life underwriting risk", ", because of premium growth in motor and home "
                  "insurance", lower=True) + ". "
             + mv(F, "mcr", "The MCR", " with the premium growth") + ". "
             + mv(F, "cov_scr", "The SCR coverage ratio", ", because eligible own funds rose faster than the SCR")
             + ".")
        based = "B2; B3"
    elif y == 2024:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_market", "Market risk", ", because we invested the proceeds of the subordinated notes in "
                  "bonds") + "; "
             + mv(F, "scr_default", "counterparty default risk", ", because of the amounts due from reinsurers after "
                  "the floods", lower=True) + "; "
             + mv(F, "scr_nonlife", "non-life underwriting risk", " with premium growth", lower=True) + ". "
             + mv(F, "mcr", "The MCR") + ". "
             + mv(F, "cov_scr", "The SCR coverage ratio") + ": the subordinated notes added to eligible own funds, "
             "but the flood claims reduced Tier 1 own funds.")
        based = "B1; B2; B3; B4; B5"
    else:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_nonlife", "Non-life underwriting risk", ", mainly because of our new home insurance "
                  "business in Lithuania") + "; "
             + mv(F, "scr_market", "market risk", " with a larger bond portfolio", lower=True) + ", and "
             + mv(F, "scr_default", "counterparty default risk", " with larger reinsurance recoverables",
                  lower=True) + ". "
             + mv(F, "mcr", "The MCR", " with the new business") + ". "
             + mv(F, "cov_scr", "The SCR coverage ratio", ", because eligible own funds rose faster than the SCR")
             + ".")
        based = "B1; B3; B4"
    t["e2_changes"] = (s, based)
    return t


# ---------------------------------------------------------------------------
# Tallowmere Life: a life insurer whose ratio moves with interest rates
# ---------------------------------------------------------------------------

TALLOWMERE_INPUTS = series(
    scr_market=[330.4, 341.2, 352.9, 380.4, 371.8, 412.6],
    scr_default=[17.2, 17.9, 18.7, 20.3, 19.6, 21.4],
    scr_life=[251.6, 262.0, 270.4, 279.1, 287.5, 298.3],
    scr_health=[14.9, 15.5, 16.1, 16.8, 17.4, 18.2],
    div_benefit=[146.3, 152.0, 157.2, 165.4, 166.2, 178.9],
    scr_operational=[28.5, 29.1, 29.6, 30.2, 30.9, 31.7],
    lac_tp=[80.2, 84.1, 88.6, 94.8, 90.3, 96.4],
    lac_dt=[59.6, 61.8, 64.0, 68.9, 71.5, 74.2],
    mcr=[115.6, 119.3, 122.7, 129.6, 131.8, 140.6],
    of_t1=[624.0, 720.9, 759.6, 577.8, 600.6, 568.0],
    of_t2=[0.0, 0.0, 0.0, 150.0, 150.0, 150.0],
    sub_liab=[0.0, 0.0, 0.0, 150.0, 150.0, 150.0],
    foreseeable_div=[18.0, 20.0, 22.0, 0.0, 15.0, 10.0],
    rec_tp=[212.4, 254.8, 268.1, 198.7, 214.3, 201.5],
    rec_intangibles=[-31.2, -29.8, -28.5, -27.1, -25.9, -24.4],
    rec_dt=[-52.3, -62.4, -65.6, -48.6, -52.4, -49.3],
)
with_equity(TALLOWMERE_INPUTS)

TALLOWMERE_TEXT = {
    "company_id": "tallowmere",
    "company_name": "Tallowmere Life",
    "legal_form": "a public limited company (life insurance undertaking) wholly owned by Tallowmere Holding",
    "lines_of_business": "traditional life insurance with profit participation, unit-linked insurance, term life "
                         "insurance, annuities and a small income protection (health) portfolio",
    "home_member_state": "Austria",
    "supervisor": "Home Supervisory Authority (fictitious placeholder)",
    "fictitious_note": "Tallowmere Life is a fictitious insurer created for teaching; all figures are synthetic.",
    "appetite_low": "150",
    "appetite_high": "200",
    "capital_policy": "Meet obligations to policyholders at all times, cover the SCR with a margin and pay "
                      "sustainable dividends; the Board of Directors approves the capital management policy, which "
                      "defines a risk appetite range for the Solvency II ratio, and reviews the capital position "
                      "every quarter.",
    "planning_horizon": "three years (business plan)",
    "tier1_items": "share capital, share premium and reconciliation reserve",
    "tier2_items": "subordinated notes issued in June 2024",
    "tier3_items": "none",
    "ancillary_own_funds": "none",
    "deductions_restrictions": "foreseeable dividends deducted from the reconciliation reserve; no other deductions; "
                               "no restrictions on availability or transferability",
    "calculation": "standard formula; the loss-absorbing capacity of technical provisions reflects future "
                   "discretionary benefits",
    "simplifications": "none",
    "undertaking_specific_parameters": "none",
    "capital_add_on": "none",
    "mcr_inputs": "linear formula for life insurance: technical provisions without risk margin (guaranteed benefits, "
                  "future discretionary benefits, unit-linked) and the capital at risk; floor 25% and cap 45% of "
                  "the SCR",
    "style": "third person ('Tallowmere Life'); formal; 'Solvency II ratio' for the SCR coverage ratio; causes "
             "introduced with 'reflecting' or 'as a result of'",
}

TALLOWMERE_BULLETS = {
    2022: [
        ("B1", "Interest rates", "Euro interest rates rose sharply in 2022. The value of our technical provisions fell "
                                 "by more than the value of our bonds, which increased the reconciliation reserve "
                                 "and Tier 1 own funds."),
        ("B2", "Credit spreads", "Wider credit spreads on corporate bonds increased spread risk within market risk."),
        ("B3", "Lapse risk", "Higher interest rates make surrenders more attractive for policyholders; the mass "
                             "lapse scenario increased life underwriting risk."),
        ("B4", "Dividend", "The Board proposed a dividend of EUR 20.0 million, which is deducted from own funds as a "
                           "foreseeable dividend."),
    ],
    2023: [
        ("B1", "Investment result", "Strong equity markets produced a good investment result, which increased the "
                                    "reconciliation reserve; higher equity values also increased equity risk."),
        ("B2", "New business", "Sales of unit-linked and term life products grew; the new business increased life "
                               "underwriting risk."),
        ("B3", "Dividend", "The Board proposed a dividend of EUR 22.0 million, deducted as a foreseeable dividend."),
        ("B4", "Assumptions", "There were no material changes to actuarial assumptions."),
    ],
    2024: [
        ("B1", "Interest rates", "Euro interest rates fell in 2024. The value of our technical provisions rose by "
                                 "more than the value of our assets, which reduced the reconciliation reserve and "
                                 "Tier 1 own funds; lower rates also increased the interest rate risk within market "
                                 "risk."),
        ("B2", "Lapse assumptions", "After an experience study we updated our lapse assumptions; this increased the "
                                    "best estimate of technical provisions and reduced Tier 1 own funds."),
        ("B3", "Subordinated notes", "In June 2024 we issued subordinated notes of EUR 150.0 million, classified as "
                                     "Tier 2 own funds, to strengthen our capital position."),
        ("B4", "Dividend", "The Board decided not to pay a dividend for 2024; no foreseeable dividend was deducted."),
    ],
    2025: [
        ("B1", "Asset allocation", "We reduced our equity holdings in favour of government bonds, which lowered "
                                   "equity risk within market risk."),
        ("B2", "Profit", "The profit of the year increased the reconciliation reserve and Tier 1 own funds."),
        ("B3", "Annuities", "Higher sales of annuities increased longevity risk within life underwriting risk."),
        ("B4", "Dividend", "The Board proposed a dividend of EUR 15.0 million, deducted as a foreseeable dividend."),
    ],
    2026: [
        ("B1", "Interest rates", "Euro interest rates fell in the second half of 2026. The value of our technical "
                                 "provisions rose by more than the value of our bonds, which reduced the "
                                 "reconciliation reserve and Tier 1 own funds."),
        ("B2", "Market risk", "Lower interest rates increased the interest rate risk within market risk."),
        ("B3", "Loss absorbency", "Higher future discretionary benefits increased the loss-absorbing capacity of "
                                  "technical provisions, which partly offset the increase in market risk."),
        ("B4", "Dividend", "The Board proposed a dividend of EUR 10.0 million, deducted as a foreseeable dividend."),
        ("B5", "Risk appetite", "The Solvency II ratio remained within our risk appetite range of 150% to 200%; no "
                                "management actions were required."),
        ("B6", "MCR", "The MCR increased; the finance team has not yet analysed the reasons by line of business."),
    ],
}

TALLOWMERE_PHRASES = phrase_bank("remained stable", ("increased moderately", "decreased moderately"),
                                 ("increased", "decreased"), ("increased materially", "decreased materially"))
TALLOWMERE_TERMS = [
    {"preferred": "Solvency II ratio", "avoid": ["SCR coverage ratio", "solvency ratio", "SCR ratio"],
     "note": "Tallowmere Life's name for the ratio of eligible own funds to the SCR"},
    {"preferred": "eligible own funds", "avoid": ["available capital", "capital resources"], "note": ""},
    {"preferred": "foreseeable dividend", "avoid": ["proposed payout", "expected dividend"], "note": ""},
    {"preferred": "reconciliation reserve", "avoid": ["retained earnings"], "note": "the Solvency II term"},
]


def tallowmere_templates(c: rc.Company, y: int) -> dict[str, tuple[str, str]]:
    F = rc.facts_for(c, y)
    t: dict[str, tuple[str, str]] = {}
    policy = ("Tallowmere Life manages its own funds to meet its obligations to policyholders at all times, to cover "
              "its Solvency Capital Requirement (SCR) with a margin and to pay sustainable dividends to its "
              "shareholder. The capital management policy, approved by the Board of Directors, defines a risk "
              "appetite range for the Solvency II ratio of " + ph("appetite_low") + " to " + ph("appetite_high")
              + ", and the Board reviews the capital position every quarter. Capital planning is part of the "
              "business plan, which covers a time horizon of three years. ")
    policy += {2024: "In " + ph("year_cur") + ", the Board decided to issue subordinated notes and not to pay a "
                     "dividend for the year, in order to strengthen the capital position."}.get(
        y, "No material changes were made to the capital management policy in " + ph("year_cur") + ".")
    t["e1_policy"] = (policy, {2024: "B3; B4"}.get(y, ""))

    s = ("At " + ph("date_cur") + ", basic own funds amounted to " + ph("of_total_cur") + " (" + ph("year_prev") + ": "
         + ph("of_total_prev") + "). ")
    t1_cause = {
        2022: ", reflecting the rise in interest rates, which reduced the value of technical provisions by more "
              "than the value of the bonds and increased the reconciliation reserve",
        2023: ", reflecting a good investment result on equities, which increased the reconciliation reserve",
        2024: ", as a result of falling interest rates and updated lapse assumptions, which increased the value of "
              "technical provisions and reduced the reconciliation reserve",
        2025: ", reflecting the profit of the year, which increased the reconciliation reserve",
    }[y]
    s += mv(F, "of_t1", "Tier 1 own funds, which comprise the share capital, the share premium and the "
            "reconciliation reserve,", t1_cause) + ". "
    if y == 2024:
        s += "Tier 2 own funds of " + ph("of_t2_cur") + " consist of the subordinated notes issued in June " \
             + ph("year_cur") + ". Tallowmere Life has no Tier 3 own funds. "
    elif y == 2025:
        s += "Tier 2 own funds of " + ph("of_t2_cur") + " consist of the subordinated notes issued in June " \
             + ph("year_prev") + ". Tallowmere Life has no Tier 3 own funds. "
    else:
        s += "Tallowmere Life has no Tier 2 or Tier 3 own funds. "
    if y == 2024:
        s += "No foreseeable dividend was deducted, as the Board decided not to pay a dividend for " + ph("year_cur") \
             + ". "
    else:
        s += "The foreseeable dividend of " + ph("foreseeable_div_cur") + " has been deducted from the " \
             "reconciliation reserve. "
    s += "Tallowmere Life holds no ancillary own funds. Table E.1 shows the own funds by tier."
    t["e1_structure"] = (s, {2022: "B1; B4", 2023: "B1; B3", 2024: "B1; B2; B3; B4", 2025: "B2; B4"}[y])

    s = ("All basic own funds of Tallowmere Life are eligible to cover the SCR. Eligible own funds to cover the SCR "
         "amounted to " + ph("eof_scr_cur") + " at " + ph("date_cur") + " (" + ph("year_prev") + ": "
         + ph("eof_scr_prev") + "). ")
    if y < 2024:
        s += ("Eligible own funds to cover the Minimum Capital Requirement (MCR) amounted to " + ph("eof_mcr_cur")
              + " (" + ph("year_prev") + ": " + ph("eof_mcr_prev") + "). ")
    else:
        s += ("To cover the Minimum Capital Requirement (MCR), Tier 2 own funds are eligible only up to "
              + ph("lim_t2_mcr") + " of the MCR; eligible own funds to cover the MCR therefore amounted to "
              + ph("eof_mcr_cur") + " (" + ph("year_prev") + ": " + ph("eof_mcr_prev") + "). ")
    s += ("No items were deducted from own funds" if y == 2024 else
          "Apart from the foreseeable dividend, no items were deducted from own funds")
    s += ", and there are no restrictions on their availability or transferability."
    t["e1_eligibility"] = (s, "")

    s = ("Equity in the financial statements of Tallowmere Life amounted to " + ph("equity_fs_cur") + " at "
         + ph("date_cur") + " (" + ph("year_prev") + ": " + ph("equity_fs_prev") + "), and the excess of assets over "
         "liabilities for solvency purposes to " + ph("eaol_cur") + " (" + ph("year_prev") + ": " + ph("eaol_prev")
         + "). The main difference is the valuation of technical provisions: the best estimate includes the expected "
         "future profits of the in-force business, which adds " + ph("rec_tp_cur") + ". Intangible assets of "
         + ph("rec_intangibles_cur") + " are not recognised for solvency purposes, and deferred taxes on the "
         "valuation differences reduce the excess of assets over liabilities by " + ph("rec_dt_cur") + ".")
    t["e1_reconciliation"] = (s, "")

    s = ("At " + ph("date_cur") + ", the SCR of Tallowmere Life amounted to " + ph("scr_cur") + " and the MCR to "
         + ph("mcr_cur") + " (" + ph("year_prev") + ": " + ph("scr_prev") + " and " + ph("mcr_prev") + "). The "
         "Solvency II ratio was " + ph("cov_scr_cur") + " (" + ph("year_prev") + ": " + ph("cov_scr_prev") + "), and "
         "the MCR coverage ratio was " + ph("cov_mcr_cur") + " (" + ph("year_prev") + ": " + ph("cov_mcr_prev")
         + "). The final amount of the SCR is not subject to supervisory assessment. Table E.2 shows the SCR by risk "
         "module.")
    t["e2_amounts"] = (s, "")

    s = ("Tallowmere Life calculates the SCR with the standard formula. It uses no simplified calculations and no "
         "undertaking-specific parameters, and no capital add-on has been imposed. The loss-absorbing capacity of "
         "technical provisions takes into account the future discretionary benefits of the with-profits business. "
         "The MCR is "
         "calculated with the linear formula for life insurance, whose inputs are the technical provisions without "
         "risk margin, split into guaranteed benefits, future discretionary benefits and unit-linked business, and "
         "the capital at risk; the result is bounded by a floor of " + ph("mcr_floor") + " and a cap of "
         + ph("mcr_cap") + " of the SCR.")
    t["e2_methods"] = (s, "")

    if y == 2022:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_market", "Market risk", ", reflecting wider credit spreads on corporate bonds") + ", and "
             + mv(F, "scr_life", "life underwriting risk", ", reflecting the higher mass lapse risk after the rise "
                  "in interest rates", lower=True) + ". "
             + mv(F, "mcr", "The MCR") + ". "
             + mv(F, "cov_scr", "The Solvency II ratio", ", as a result of the higher reconciliation reserve") + ".")
        based = "B1; B2; B3"
    elif y == 2023:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_market", "Market risk", ", reflecting higher equity values") + ", and "
             + mv(F, "scr_life", "life underwriting risk", ", reflecting the growth in unit-linked and term life "
                  "business", lower=True) + ". "
             + mv(F, "mcr", "The MCR") + ". "
             + mv(F, "cov_scr", "The Solvency II ratio", ", reflecting the good investment result") + ".")
        based = "B1; B2"
    elif y == 2024:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_market", "Market risk", ", reflecting the higher interest rate risk after the fall in "
                  "interest rates") + ". "
             + mv(F, "lac_tp", "The loss-absorbing capacity of technical provisions") + ". "
             + mv(F, "mcr", "The MCR") + ". "
             + mv(F, "cov_scr", "The Solvency II ratio", " as a result of the lower reconciliation reserve") + "; "
             "the subordinated notes issued in June " + ph("year_cur") + " partly offset the decrease.")
        based = "B1; B2; B3"
    else:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_market", "Market risk", ", reflecting the reduction of equity holdings in favour of "
                  "government bonds") + ", while "
             + mv(F, "scr_life", "life underwriting risk", ", reflecting higher sales of annuities and the "
                  "resulting longevity risk", lower=True) + ". "
             + mv(F, "mcr", "The MCR") + ". "
             + mv(F, "cov_scr", "The Solvency II ratio", ", reflecting the profit of the year") + ".")
        based = "B1; B2; B3"
    t["e2_changes"] = (s, based)
    return t


# ---------------------------------------------------------------------------
# Quillbrook Insurance: a composite whose tier limits bind and whose coverage approaches its risk appetite
# ---------------------------------------------------------------------------

QUILLBROOK_INPUTS = series(
    scr_market=[241.0, 228.7, 236.2, 244.9, 252.7, 247.3],
    scr_default=[35.6, 37.9, 38.8, 40.3, 41.1, 43.4],
    scr_life=[118.9, 113.4, 121.7, 125.2, 128.3, 131.9],
    scr_health=[41.2, 43.0, 44.6, 45.9, 47.0, 48.8],
    scr_nonlife=[176.5, 189.6, 197.3, 201.8, 204.6, 209.7],
    div_benefit=[204.7, 205.1, 213.4, 219.9, 225.5, 228.0],
    scr_operational=[35.2, 36.3, 37.0, 38.1, 38.9, 41.4],
    lac_tp=[18.3, 16.9, 18.8, 20.4, 21.6, 22.1],
    lac_dt=[48.2, 47.6, 51.6, 53.8, 55.1, 50.2],
    mcr=[135.8, 137.1, 141.1, 144.8, 147.6, 152.0],
    of_t1=[395.0, 372.4, 381.1, 363.5, 366.9, 352.0],
    of_t2=[165.0, 165.0, 165.0, 165.0, 165.0, 165.0],
    of_t3=[41.8, 58.9, 57.3, 66.4, 61.3, 79.2],
    sub_liab=[165.0, 165.0, 165.0, 165.0, 165.0, 165.0],
    foreseeable_div=[30.0, 30.0, 25.0, 25.0, 20.0, 0.0],
    rec_tp=[118.6, 127.3, 121.9, 109.4, 114.8, 106.2],
    rec_intangibles=[-64.2, -62.7, -61.0, -59.8, -58.1, -56.9],
    rec_dt=[-20.1, -23.4, -21.2, -17.6, -19.9, -16.3],
    rec_other=[-8.4, -7.9, -9.1, -8.8, -9.6, -10.2],
)
with_equity(QUILLBROOK_INPUTS)

QUILLBROOK_TEXT = {
    "company_id": "quillbrook",
    "company_name": "Quillbrook Insurance",
    "legal_form": "a public limited company (composite insurance undertaking)",
    "lines_of_business": "motor, property and liability insurance, protection life insurance and health insurance",
    "home_member_state": "Lithuania",
    "supervisor": "Home Supervisory Authority (fictitious placeholder)",
    "fictitious_note": "Quillbrook Insurance is a fictitious insurer created for teaching; all figures are synthetic.",
    "appetite_low": "140",
    "appetite_high": "",
    "capital_policy": "Cover the SCR at all times with own funds of sufficient quality, maintain SCR coverage of at "
                      "least the risk appetite and pay dividends only where this level is maintained after the "
                      "payment; the Board of Directors approves the policy and reviews it every year.",
    "planning_horizon": "three years (capital plan within the business plan)",
    "tier1_items": "share capital and reconciliation reserve",
    "tier2_items": "subordinated bonds",
    "tier3_items": "net deferred tax assets",
    "ancillary_own_funds": "none",
    "deductions_restrictions": "foreseeable dividends deducted; no restrictions on availability or transferability",
    "calculation": "standard formula",
    "simplifications": "simplified calculation of the risk-mitigating effect of reinsurance arrangements in the "
                       "counterparty default risk module",
    "undertaking_specific_parameters": "none",
    "capital_add_on": "none",
    "mcr_inputs": "linear formulas for life and non-life insurance: technical provisions without risk margin and "
                  "capital at risk (life), technical provisions without risk margin and written premiums of the last "
                  "twelve months (non-life); floor 25% and cap 45% of the SCR",
    "style": "third person ('the Company'); formal; 'SCR coverage' without 'ratio'; movements with 'rose' and "
             "'fell'; tier limits always explained",
}

QUILLBROOK_BULLETS = {
    2022: [
        ("B1", "Interest rates and markets", "Rising interest rates and falling equity markets reduced the market "
                                             "value of our investments; Tier 1 own funds fell and market risk "
                                             "decreased."),
        ("B2", "Deferred taxes", "Unrealised losses increased net deferred tax assets (Tier 3); the amount above "
                                 "15% of the SCR is not eligible."),
        ("B3", "Tier limits", "Because Tier 2 and Tier 3 together exceed half of the SCR, part of the subordinated "
                              "bonds (Tier 2) is not eligible to cover the SCR."),
        ("B4", "Non-life growth", "Growth in motor and property insurance increased non-life underwriting risk."),
        ("B5", "Dividend", "The Board proposed a dividend of EUR 30.0 million, deducted as a foreseeable dividend."),
    ],
    2023: [
        ("B1", "Equity markets", "Recovering equity markets increased the value of our investments, Tier 1 own funds "
                                 "and market risk."),
        ("B2", "Non-life", "Claims inflation in motor insurance reduced the non-life result; growth increased "
                           "non-life underwriting risk."),
        ("B3", "Life", "Higher sales of protection products increased life underwriting risk."),
        ("B4", "Tier limits", "Tier 2 own funds remain partly ineligible because Tier 2 and Tier 3 together exceed "
                              "half of the SCR."),
        ("B5", "Dividend", "The Board proposed a dividend of EUR 25.0 million, deducted as a foreseeable dividend."),
    ],
    2024: [
        ("B1", "Hailstorms", "Two severe hailstorms in June 2024 caused many motor and property claims; the loss "
                             "reduced Tier 1 own funds."),
        ("B2", "Deferred taxes", "The loss increased net deferred tax assets (Tier 3); the amount above 15% of the "
                                 "SCR is not eligible."),
        ("B3", "Risk appetite", "SCR coverage reached the lower end of our risk appetite of at least 140%; the Board "
                                "started a review of capital measures."),
        ("B4", "Dividend", "The Board proposed a dividend of EUR 25.0 million, deducted as a foreseeable dividend."),
    ],
    2025: [
        ("B1", "Dividend", "To support own funds, the Board reduced the dividend to EUR 20.0 million, deducted as a "
                           "foreseeable dividend."),
        ("B2", "Non-life", "Rate increases restored the non-life result; growth increased non-life underwriting "
                           "risk slightly."),
        ("B3", "Deferred taxes", "Net deferred tax assets fell as part of the 2024 tax loss was used."),
        ("B4", "Below risk appetite", "SCR coverage fell below our risk appetite of at least 140%; the Board decided "
                                      "on management actions for 2026."),
    ],
    2026: [
        ("B1", "Hailstorm", "A severe hailstorm in July 2026 caused many motor and property claims; the loss reduced "
                            "Tier 1 own funds."),
        ("B2", "Deferred taxes", "The loss increased net deferred tax assets (Tier 3); the amount above 15% of the "
                                 "SCR is not eligible."),
        ("B3", "Dividend", "As a management action, the Board suspended the dividend for 2026; no foreseeable "
                           "dividend is deducted."),
        ("B4", "Capital plan", "In December 2026 the Board approved a capital plan that includes new Tier 2 notes in "
                               "2027; they are not part of own funds at the end of 2026."),
        ("B5", "Reinsurance", "A higher catastrophe reinsurance cover will apply from 1 January 2027; it does not "
                              "affect the SCR at the end of 2026."),
        ("B6", "Operational risk", "Operational risk increased; the reasons have not yet been analysed."),
    ],
}

QUILLBROOK_PHRASES = phrase_bank("remained stable", ("rose slightly", "fell slightly"), ("rose", "fell"),
                                 ("rose sharply", "fell sharply"))
QUILLBROOK_TERMS = [
    {"preferred": "SCR coverage", "avoid": ["solvency ratio", "Solvency II ratio", "SCR ratio"],
     "note": "the Company writes 'SCR coverage' and 'MCR coverage', without 'ratio'"},
    {"preferred": "own funds eligible to cover the SCR", "avoid": ["available capital", "capital resources"],
     "note": ""},
    {"preferred": "subordinated bonds", "avoid": ["hybrid capital", "hybrids"], "note": "Tier 2 own funds"},
    {"preferred": "the Company", "avoid": ["Quillbrook Group"], "note": "Quillbrook Insurance belongs to no group"},
]


def quillbrook_templates(c: rc.Company, y: int) -> dict[str, tuple[str, str]]:
    F = rc.facts_for(c, y)
    t: dict[str, tuple[str, str]] = {}
    policy = ("The Company manages its own funds in line with its capital management policy, which the Board of "
              "Directors approves and reviews every year. The policy aims to cover the Solvency Capital Requirement "
              "(SCR) at all times with own funds of sufficient quality, to maintain SCR coverage of at least "
              + ph("appetite_low") + " and to pay dividends only where this level is maintained after the payment. "
              "The capital plan covers the three years of the business plan and is updated every year. ")
    policy += {
        2024: "In " + ph("year_cur") + ", SCR coverage reached the lower end of the risk appetite, and the Board "
              "started a review of capital measures.",
        2025: "In " + ph("year_cur") + ", SCR coverage fell below the risk appetite; the Board reduced the dividend "
              "and decided on management actions for the following year.",
    }.get(y, "There were no material changes to the policy or the processes in " + ph("year_cur") + ".")
    t["e1_policy"] = (policy, {2024: "B3", 2025: "B1; B4"}.get(y, ""))

    s = ("Basic own funds amounted to " + ph("of_total_cur") + " at " + ph("date_cur") + " (" + ph("year_prev") + ": "
         + ph("of_total_prev") + "). ")
    t1_cause = {
        2022: ", because rising interest rates and falling equity markets reduced the market value of the "
              "investments",
        2023: ", owing to the recovery of equity markets",
        2024: ", because two severe hailstorms in June " + ph("year_cur") + " caused many motor and property claims",
        2025: "",
    }[y]
    s += mv(F, "of_t1", "Tier 1 own funds, consisting of the share capital and the reconciliation reserve,",
            t1_cause) + ". "
    s += mv(F, "of_t2", "Tier 2 own funds, which consist of subordinated bonds,") + ". "
    t3_cause = {2022: ", because of higher unrealised losses on investments",
                2024: ", because the loss from the hailstorms increased the tax loss carried forward",
                2025: ", because part of the tax loss of " + ph("year_prev") + " was used"}.get(y, "")
    s += mv(F, "of_t3", "Tier 3 own funds, consisting of net deferred tax assets,", t3_cause) + ". "
    s += ("The foreseeable dividend of " + ph("foreseeable_div_cur") + " was deducted from the reconciliation "
          "reserve. The Company holds no ancillary own funds. Table E.1 shows the own funds by tier and their "
          "eligibility.")
    t["e1_structure"] = (s, {2022: "B1; B2; B5", 2023: "B1; B5", 2024: "B1; B2; B4", 2025: "B1; B3"}[y])

    s = ("Under the tier limits, Tier 3 own funds are eligible to cover the SCR only up to " + ph("lim_t3_scr")
         + " of the SCR, and Tier 2 and Tier 3 together only up to " + ph("lim_t2t3_scr") + " of the SCR. ")
    if y in (2022, 2024):
        s += ("At " + ph("date_cur") + ", both limits applied, and " + ph("of_inelig_scr_cur") + " of Tier 2 and "
              "Tier 3 own funds were not eligible. ")
    else:
        s += ("At " + ph("date_cur") + ", the limit for Tier 2 and Tier 3 together applied, and "
              + ph("of_inelig_scr_cur") + " of Tier 2 own funds were not eligible. ")
    s += ("Own funds eligible to cover the SCR therefore amounted to " + ph("eof_scr_cur") + " (" + ph("year_prev")
          + ": " + ph("eof_scr_prev") + "). To cover the Minimum Capital Requirement (MCR), Tier 3 own funds are not "
          "eligible and Tier 2 own funds are eligible up to " + ph("lim_t2_mcr") + " of the MCR; own funds eligible "
          "to cover the MCR amounted to " + ph("eof_mcr_cur") + " (" + ph("year_prev") + ": " + ph("eof_mcr_prev")
          + "). Apart from the foreseeable dividend, no items were deducted from own funds, and there are no "
          "restrictions on their availability or transferability.")
    t["e1_eligibility"] = (s, {2022: "B2; B3", 2023: "B4", 2024: "B2", 2025: ""}[y])

    s = ("Equity in the Company's financial statements amounted to " + ph("equity_fs_cur") + " at " + ph("date_cur")
         + " (" + ph("year_prev") + ": " + ph("equity_fs_prev") + "); the excess of assets over liabilities for "
         "solvency purposes amounted to " + ph("eaol_cur") + " (" + ph("year_prev") + ": " + ph("eaol_prev") + "). "
         "The revaluation of technical provisions adds " + ph("rec_tp_cur") + ". Intangible assets of "
         + ph("rec_intangibles_cur") + " are not recognised, deferred taxes on the valuation differences deduct "
         + ph("rec_dt_cur") + ", and other valuation differences, mainly on participations, deduct "
         + ph("rec_other_cur") + ".")
    t["e1_reconciliation"] = (s, "")

    s = ("The SCR amounted to " + ph("scr_cur") + " at " + ph("date_cur") + " (" + ph("year_prev") + ": "
         + ph("scr_prev") + "), and the MCR to " + ph("mcr_cur") + " (" + ph("year_prev") + ": " + ph("mcr_prev")
         + "). SCR coverage was " + ph("cov_scr_cur") + " (" + ph("year_prev") + ": " + ph("cov_scr_prev") + ") and "
         "MCR coverage " + ph("cov_mcr_cur") + " (" + ph("year_prev") + ": " + ph("cov_mcr_prev") + "). The final "
         "amount of the SCR is not subject to supervisory assessment. Table E.2 shows the SCR by risk module.")
    t["e2_amounts"] = (s, "")

    s = ("The Company calculates the SCR with the standard formula. It uses one simplified calculation: the "
         "simplified calculation of the risk-mitigating effect of reinsurance arrangements in the counterparty "
         "default risk module. It uses no undertaking-specific parameters, and no capital add-on has been imposed. "
         "The MCR is calculated with the linear formulas for life and non-life insurance; the inputs are the "
         "technical provisions without risk margin and the capital at risk for life insurance, and the technical "
         "provisions without risk margin and the written premiums of the last twelve months for non-life insurance. "
         "The result is bounded by a floor of " + ph("mcr_floor") + " and a cap of " + ph("mcr_cap") + " of the SCR.")
    t["e2_methods"] = (s, "")

    if y == 2022:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_nonlife", "Non-life underwriting risk", " because of growth in motor and property "
                  "insurance") + ", while "
             + mv(F, "scr_market", "market risk", " because of the lower market value of the investments",
                  lower=True) + ". "
             + mv(F, "mcr", "The MCR") + ". "
             + mv(F, "cov_scr", "SCR coverage", ", because Tier 1 own funds fell and the tier limits restricted the "
                  "eligibility of Tier 3 own funds") + ".")
        based = "B1; B2; B4"
    elif y == 2023:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_market", "Market risk", " with the recovery of equity markets") + ", "
             + mv(F, "scr_nonlife", "non-life underwriting risk", " because of growth", lower=True) + ", and "
             + mv(F, "scr_life", "life underwriting risk", " because of higher sales of protection products",
                  lower=True) + ". "
             + mv(F, "mcr", "The MCR") + ". "
             + mv(F, "cov_scr", "SCR coverage") + ".")
        based = "B1; B2; B3"
    elif y == 2024:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_nonlife", "Non-life underwriting risk", " because of growth") + ". "
             + mv(F, "mcr", "The MCR") + ". "
             + mv(F, "cov_scr", "SCR coverage", ", because the hailstorms reduced Tier 1 own funds and the tier "
                  "limits restricted the eligibility of the higher Tier 3 own funds") + ".")
        based = "B1; B2"
    else:
        s = (mv(F, "scr", "The SCR") + ". "
             + mv(F, "scr_nonlife", "Non-life underwriting risk", " because of growth") + ". "
             + mv(F, "mcr", "The MCR") + ". "
             + mv(F, "cov_scr", "SCR coverage") + ", below the risk appetite of " + ph("appetite_low") + ".")
        based = "B2; B4"
    t["e2_changes"] = (s, based)
    return t


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def mv(F: dict, metric: str, subject: str, tail: str = "", lower: bool = False) -> str:
    """A movement clause in the house frame: '<subject> [[metric]] by <change> to <level><tail>', or
    '<subject> [[metric]] at <level><tail>' when the house phrase says the figure remained stable."""
    m = rc.movements(F)[metric]
    if not m.phrase:
        raise AssertionError(f"no house phrase for {metric}")
    if lower:
        subject = subject[:1].lower() + subject[1:]
    if "stable" in m.phrase:
        return f"{subject} [[{metric}]] at " + ph(metric + "_cur") + tail
    unit = "pp" if metric in rc.RATIOS else "pct"
    return f"{subject} [[{metric}]] by " + ph(f"{metric}_change_{unit}") + " to " + ph(metric + "_cur") + tail


def apply_phrases(template: str, F: dict) -> str:
    moves = rc.movements(F)

    def fill(match) -> str:
        return moves[match.group(1)].phrase
    import re
    return re.sub(r"\[\[([a-z0-9_]+)\]\]", fill, template)


COMPANIES = [
    ("brisendale_mutual", BRISENDALE_TEXT, BRISENDALE_INPUTS, BRISENDALE_BULLETS, BRISENDALE_PHRASES,
     BRISENDALE_TERMS, brisendale_templates),
    ("tallowmere_life", TALLOWMERE_TEXT, TALLOWMERE_INPUTS, TALLOWMERE_BULLETS, TALLOWMERE_PHRASES,
     TALLOWMERE_TERMS, tallowmere_templates),
    ("quillbrook_insurance", QUILLBROOK_TEXT, QUILLBROOK_INPUTS, QUILLBROOK_BULLETS, QUILLBROOK_PHRASES,
     QUILLBROOK_TERMS, quillbrook_templates),
]


def build_company(text, inputs, bullets, phrases, terms) -> rc.Company:
    figures = {y: rc.derive(inputs[y]) for y in YEARS}
    return rc.Company(
        company_id=text["company_id"], name=text["company_name"], text=dict(text), years=list(YEARS), inputs=inputs,
        figures=figures,
        bullets={y: [{"id": b[0], "topic": b[1], "text": b[2]} for b in rows] for y, rows in bullets.items()},
        narratives={}, phrases=phrases, terminology=terms)


def check_figures(c: rc.Company) -> None:
    """The synthetic figures must pass the workbook checks and print consistently."""
    problems = [r for r in rc.consistency_findings(c.figures) if r["severity"] in ("error", "warning")]
    assert not problems, (c.name, problems)
    for y in YEARS[1:]:
        F = rc.facts_for(c, y)
        for mid in rc.RATIOS:
            printed = round(F[f"{mid}_cur"].value) - round(F[f"{mid}_prev"].value)
            change = F[f"{mid}_change_pp"].value
            assert printed == round(change) or abs(printed) == round(abs(change)), \
                (c.name, y, mid, printed, change, "printed levels and printed change disagree")
    # no tier-limit calculation may land exactly on a half of EUR 0.1 million (Excel and Python would round apart)
    for y in YEARS:
        v = c.figures[y]
        scr, mcr = Decimal(str(v["scr"])), Decimal(str(v["mcr"]))
        t2, t3 = Decimal(str(v["of_t2"])), Decimal(str(v["of_t3"]))
        for raw in (min(t3, Decimal("0.15") * scr), min(t2, Decimal("0.5") * scr - min(t3, Decimal("0.15") * scr)),
                    min(t2, Decimal("0.2") * mcr)):
            assert (raw * 100) % 10 != 5 or (raw * 1000) % 10 != 0, (c.name, y, raw, "rounding half")


def write_workbook(path: Path, c: rc.Company, phrases: list[dict], terms: list[dict],
                   narratives: dict[int, list[dict]]) -> None:
    wb = xlsxwriter.Workbook(str(path))
    # A fixed creation date makes the file byte-identical on every build, so the checksum that ties the recorded
    # LLM runs to a workbook stays valid when the workbooks are rebuilt from unchanged data.
    from datetime import datetime
    wb.set_properties({"title": f"{c.name}: figures, bullets and SFCR texts E.1/E.2 (fictitious)",
                       "author": "EAA seminar E0572 (synthetic data)", "created": datetime(2026, 10, 1)})
    navy, cyan = "#0F2B72", "#009CDB"
    head = wb.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": navy, "border": 1, "text_wrap": True,
                          "valign": "top"})
    wrap = wb.add_format({"text_wrap": True, "valign": "top"})
    bold = wb.add_format({"bold": True, "valign": "top"})
    title = wb.add_format({"bold": True, "font_size": 14, "font_color": navy})
    inp = wb.add_format({"num_format": "#,##0.0", "bg_color": "#FFF8DC", "border": 1, "border_color": "#D5DEEA"})
    der = wb.add_format({"num_format": "#,##0.0", "bg_color": "#EEF2F7", "italic": True, "border": 1,
                         "border_color": "#D5DEEA"})
    pct = wb.add_format({"num_format": "0.0", "bg_color": "#EEF2F7", "italic": True, "border": 1,
                         "border_color": "#D5DEEA"})
    sec = wb.add_format({"bold": True, "font_color": cyan})

    ws = wb.add_worksheet("About")
    ws.set_column(0, 0, 110, wrap)
    lines = [
        (f"{c.name}: figures, driver bullets and SFCR texts for sections E.1 and E.2", title),
        (c.text["fictitious_note"], wrap),
        ("", wrap),
        ("This workbook feeds the Case Study 5 report app (apps/cs5_report_generation). Edit it, save it, and upload it "
         "in the app.", wrap),
        ("Company: the text facts of the insurer (legal form, capital management policy, calculation methods, risk "
         "appetite). appetite_low and appetite_high are numbers in per cent.", wrap),
        ("Figures: EUR million at 31 December. Yellow cells are inputs; grey cells are totals and ratios computed by "
         "formulas. The app reads only the inputs and computes every total, every amount eligible under the tier "
         "limits and every ratio itself; deductions (diversification, loss-absorbing capacity) are positive amounts.",
         wrap),
        ("Bullets: the driver bullets of the finance and risk teams for each year. They are the only evidence for a "
         "cause that the text may state.", wrap),
        ("Narratives: the E.1 and E.2 texts published for 2022 to 2025, one row per text block (slot); 'based_on' "
         "names the bullets a block draws on. 2026 has figures and bullets but no text yet: that is the year to "
         "draft.", wrap),
        ("House phrases: the words for a movement by its size (per cent for amounts, percentage points for ratios). "
         "Terminology: the house terms and the terms to avoid.", wrap),
    ]
    for i, (text, fmt) in enumerate(lines):
        ws.write(i, 0, text, fmt)

    ws = wb.add_worksheet("Company")
    ws.set_column(0, 0, 30, bold)
    ws.set_column(1, 1, 110, wrap)
    ws.write_row(0, 0, ["field", "value"], head)
    for i, (k, v) in enumerate(c.text.items(), start=1):
        ws.write(i, 0, k, bold)
        ws.write(i, 1, v, wrap)

    ws = wb.add_worksheet("Figures")
    header = ["id", "item", "unit", "kind", "section"] + [str(y) for y in YEARS]
    ws.write_row(0, 0, header, head)
    ws.set_column(0, 0, 18)
    ws.set_column(1, 1, 58)
    ws.set_column(2, 4, 9)
    ws.set_column(5, 5 + len(YEARS), 11)
    ws.freeze_panes(1, 2)
    order = [m for m in rc.METRICS]
    row_of = {m.id: i + 1 for i, m in enumerate(order)}

    def ref(mid: str, col: int) -> str:
        return xlsxwriter.utility.xl_rowcol_to_cell(row_of[mid], col)

    formulas = {
        "bscr": lambda k: f"=ROUND({ref('scr_market', k)}+{ref('scr_default', k)}+{ref('scr_life', k)}"
                          f"+{ref('scr_health', k)}+{ref('scr_nonlife', k)}-{ref('div_benefit', k)},1)",
        "scr": lambda k: f"=ROUND({ref('bscr', k)}+{ref('scr_operational', k)}-{ref('lac_tp', k)}-{ref('lac_dt', k)},1)",
        "of_total": lambda k: f"=ROUND({ref('of_t1', k)}+{ref('of_t2', k)}+{ref('of_t3', k)},1)",
        "eof_scr_t1": lambda k: f"={ref('of_t1', k)}",
        "eof_scr_t3": lambda k: f"=ROUND(MIN({ref('of_t3', k)},0.15*{ref('scr', k)}),1)",
        "eof_scr_t2": lambda k: f"=ROUND(MAX(0,MIN({ref('of_t2', k)},0.5*{ref('scr', k)}-MIN({ref('of_t3', k)},"
                                f"0.15*{ref('scr', k)}))),1)",
        "eof_scr": lambda k: f"=ROUND({ref('eof_scr_t1', k)}+{ref('eof_scr_t2', k)}+{ref('eof_scr_t3', k)},1)",
        "eof_mcr_t1": lambda k: f"={ref('of_t1', k)}",
        "eof_mcr_t2": lambda k: f"=ROUND(MIN({ref('of_t2', k)},0.2*{ref('mcr', k)}),1)",
        "eof_mcr": lambda k: f"=ROUND({ref('eof_mcr_t1', k)}+{ref('eof_mcr_t2', k)},1)",
        "of_inelig_scr": lambda k: f"=ROUND({ref('of_total', k)}-{ref('eof_scr', k)},1)",
        "cov_scr": lambda k: f"=100*{ref('eof_scr', k)}/{ref('scr', k)}",
        "cov_mcr": lambda k: f"=100*{ref('eof_mcr', k)}/{ref('mcr', k)}",
        "eaol": lambda k: f"=ROUND({ref('equity_fs', k)}+{ref('rec_tp', k)}+{ref('rec_intangibles', k)}"
                          f"+{ref('rec_dt', k)}+{ref('rec_other', k)},1)",
    }
    for m in order:
        r = row_of[m.id]
        unit = "%" if m.unit == "pct" else "EUR m"
        ws.write_row(r, 0, [m.id, m.label, unit, m.kind, m.section], sec if m.kind == "derived" else None)
        for k, y in enumerate(YEARS):
            col = 5 + k
            value = c.figures[y][m.id]
            if m.kind == "input":
                ws.write_number(r, col, value, inp)
            else:
                ws.write_formula(r, col, formulas[m.id](col), pct if m.unit == "pct" else der, round(value, 6))

    ws = wb.add_worksheet("Bullets")
    ws.write_row(0, 0, ["year", "id", "topic", "text"], head)
    ws.set_column(0, 1, 7)
    ws.set_column(2, 2, 24)
    ws.set_column(3, 3, 120, wrap)
    r = 1
    for y in sorted(c.bullets):
        for b in c.bullets[y]:
            ws.write_row(r, 0, [y, b["id"], b["topic"], b["text"]], wrap)
            r += 1

    ws = wb.add_worksheet("Narratives")
    ws.write_row(0, 0, ["year", "section", "slot", "title", "based_on", "text"], head)
    ws.set_column(0, 1, 8)
    ws.set_column(2, 2, 18)
    ws.set_column(3, 3, 34, wrap)
    ws.set_column(4, 4, 12)
    ws.set_column(5, 5, 120, wrap)
    r = 1
    for y in sorted(narratives):
        for row in narratives[y]:
            ws.write_row(r, 0, [y, row["section"], row["slot"], row["title"], row["based_on"], row["text"]], wrap)
            r += 1

    ws = wb.add_worksheet("House phrases")
    ws.write_row(0, 0, ["applies_to", "from", "to", "phrase_up", "phrase_down", "note"], head)
    ws.set_column(0, 2, 11)
    ws.set_column(3, 4, 26)
    ws.set_column(5, 5, 70, wrap)
    for i, p in enumerate(phrases, start=1):
        note = ("relative change in per cent, absolute value" if p["applies_to"] == "amount"
                else "change in percentage points, absolute value")
        ws.write_row(i, 0, [p["applies_to"], p["from"]], None)
        if p["to"] < 1e8:
            ws.write_number(i, 2, p["to"])
        ws.write_row(i, 3, [p["up"], p["down"], note], wrap)

    ws = wb.add_worksheet("Terminology")
    ws.write_row(0, 0, ["preferred", "avoid", "note"], head)
    ws.set_column(0, 0, 36)
    ws.set_column(1, 1, 50, wrap)
    ws.set_column(2, 2, 60, wrap)
    for i, term in enumerate(terms, start=1):
        ws.write_row(i, 0, [term["preferred"], "; ".join(term["avoid"]), term["note"]], wrap)
    wb.close()


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for stem, text, inputs, bullets, phrases, terms, templates in COMPANIES:
        c = build_company(text, inputs, bullets, phrases, terms)
        check_figures(c)
        narratives: dict[int, list[dict]] = {}
        for y in HISTORY:
            F = rc.facts_for(c, y)
            rows = []
            for slot, (template, based_on) in templates(c, y).items():
                with_words = apply_phrases(template, F)
                published = rc.render(with_words, F)
                assert "[unknown" not in published, (c.name, y, slot, published)
                recovered, unlinked = rc.templatize(published, F)
                assert not unlinked, (c.name, y, slot, unlinked)
                if recovered != with_words:
                    import difflib
                    diff = [d for d in difflib.ndiff([with_words], [recovered])]
                    raise AssertionError(f"{c.name} {y} {slot}: the reader links a number differently\n"
                                         + "\n".join(diff))
                rows.append({"section": rc.SLOT_SECTION[slot], "slot": slot, "title": rc.SLOT_TITLE[slot],
                             "based_on": based_on, "text": published})
            assert [r["slot"] for r in rows] == rc.SLOT_IDS, (c.name, y)
            narratives[y] = rows
        path = OUT_DIR / f"{stem}.xlsx"
        write_workbook(path, c, phrases, terms, narratives)
        back = rc.load_workbook(path)
        assert back.current_year == CURRENT and back.history_years == HISTORY, (back.current_year, back.history_years)
        for y in YEARS:
            for mid in rc.METRIC:
                assert abs(back.figures[y][mid] - c.figures[y][mid]) < 1e-6, (c.name, y, mid)
        assert not rc.cached_differences(back), rc.cached_differences(back)
        words = sum(len(r["text"].split()) for y in HISTORY for r in narratives[y])
        cov = ", ".join(f"{y}: {c.figures[y]['cov_scr']:.0f}%" for y in YEARS)
        print(f"{path.name}: {sum(len(v) for v in c.bullets.values())} bullets, {words} words of published text; "
              f"SCR coverage {cov}")


if __name__ == "__main__":
    main()
