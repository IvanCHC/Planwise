import argparse
import sys
from pathlib import Path

import pandas as pd

import planwise as pw
from planwise.profile import (
    AccountBalances,
    ExpectedReturnsAndInflation,
    PostRetirementSettings,
    ProfileSettings,
    deserialise_profile_settings_from_json,
    get_contribution_settings,
    get_personal_details,
    get_post_50_contribution_settings,
    get_qualifying_earnings_info,
)

EPILOG = """
Examples:
    # Investment projection
    planwise --current-age 30 --retirement-age 67 --salary 40000

     # Save results to CSV
    planwise --current-age 30 --retirement-age 67 --salary 40000 --output results.csv

    # Load profile from JSON file
    planwise --config config.json
"""


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser for Planwise CLI.
    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="UK Investment & Retirement Planning CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )

    parser.add_argument(
        "--tax-year", type=int, default=2025, help="Tax year (default: 2025)"
    )
    parser.add_argument(
        "--scotland",
        action="store_true",
        help="Use Scottish tax rates (default: False)",
    )
    parser.add_argument(
        "--use-qualifying",
        action="store_true",
        help="Use qualifying contributions (default: False)",
    )
    parser.add_argument(
        "--current-age", type=int, default=25, help="Current age (default: 25)"
    )
    parser.add_argument(
        "--retirement-age", type=int, default=67, help="Retirement age (default: 67)"
    )
    parser.add_argument(
        "--salary",
        type=float,
        default=30000.0,
        help="Annual salary in £ (default: 30000)",
    )
    parser.add_argument(
        "--use-exact-amounts",
        action="store_true",
        help="Determine if contribution is rate or exact amount (default: False)",
    )
    parser.add_argument(
        "--workplace-employer-contribution",
        type=float,
        default=0.03,
        help="Workplace employer contribution rate (default: 0.03)",
    )
    parser.add_argument(
        "--workplace-employee-contribution",
        type=float,
        default=0.05,
        help="Workplace employee contribution rate (default: 0.05)",
    )
    parser.add_argument(
        "--lisa-contribution",
        type=float,
        default=0.0,
        help="LISA contribution (default: 0.0)",
    )
    parser.add_argument(
        "--isa-contribution",
        type=float,
        default=0.0,
        help="ISA contribution (default: 0.0)",
    )
    parser.add_argument(
        "--sipp-contribution",
        type=float,
        default=0.0,
        help="SIPP contribution (default: 0.0)",
    )
    parser.add_argument(
        "--lisa-balance",
        type=float,
        default=0.0,
        help="Initial LISA balance (default: 0.0)",
    )
    parser.add_argument(
        "--isa-balance",
        type=float,
        default=0.0,
        help="Initial ISA balance (default: 0.0)",
    )
    parser.add_argument(
        "--sipp-balance",
        type=float,
        default=0.0,
        help="Initial SIPP balance (default: 0.0)",
    )
    parser.add_argument(
        "--workplace-balance",
        type=float,
        default=0.0,
        help="Initial workplace balance (default: 0.0)",
    )
    parser.add_argument(
        "--use-exact-amount-post50",
        action="store_true",
        help="Determine if the redirectable is exact amount or rate (default: False)",
    )
    parser.add_argument(
        "--redirectable-to-isa",
        type=float,
        default=0.0,
        help="Amount redirectable to ISA from LISA(default: 0.0)",
    )
    parser.add_argument(
        "--roi-lisa",
        type=float,
        default=0.05,
        help="LISA return on investment (default: 0.05)",
    )
    parser.add_argument(
        "--roi-isa",
        type=float,
        default=0.05,
        help="ISA return on investment (default: 0.05)",
    )
    parser.add_argument(
        "--roi-sipp",
        type=float,
        default=0.05,
        help="SIPP return on investment (default: 0.05)",
    )
    parser.add_argument(
        "--roi-workplace",
        type=float,
        default=0.05,
        help="Workplace return on investment (default: 0.05)",
    )
    parser.add_argument(
        "--inflation", type=float, default=0.02, help="Inflation rate (default: 0.02)"
    )
    parser.add_argument(
        "--postret-withdrawal-today",
        type=float,
        default=0.0,
        help="Post-retirement withdrawal today (default: 0.0)",
    )
    parser.add_argument(
        "--postret-roi-lisa",
        type=float,
        default=0.05,
        help="Post-retirement LISA ROI (default: 0.05)",
    )
    parser.add_argument(
        "--postret-roi-isa",
        type=float,
        default=0.05,
        help="Post-retirement ISA ROI (default: 0.05)",
    )
    parser.add_argument(
        "--postret-roi-pension",
        type=float,
        default=0.05,
        help="Post-retirement pension ROI (default: 0.05)",
    )
    parser.add_argument(
        "--postret-lisa-withdrawal-age",
        type=int,
        default=67,
        help="Post-retirement LISA withdrawal age (default: 67)",
    )
    parser.add_argument(
        "--postret-lisa-targeted-withdrawal-percentage",
        type=float,
        default=0.0,
        help="Post-retirement LISA targeted withdrawal percentage (default: 0.0)",
    )
    parser.add_argument(
        "--postret-isa-withdrawal-age",
        type=int,
        default=67,
        help="Post-retirement ISA withdrawal age (default: 67)",
    )
    parser.add_argument(
        "--postret-isa-targeted-withdrawal-percentage",
        type=float,
        default=0.0,
        help="Post-retirement ISA targeted withdrawal percentage (default: 0.0)",
    )
    parser.add_argument(
        "--postret-taxfree-pension-withdrawal-age",
        type=int,
        default=67,
        help="Post-retirement tax-free pension withdrawal age (default: 67)",
    )
    parser.add_argument(
        "--postret-taxfree-pension-targeted-withdrawal-percentage",
        type=float,
        default=0.0,
        help="Post-retirement tax-free pension targeted withdrawal percentage (default: 0.0)",
    )
    parser.add_argument(
        "--postret-taxable-pension-withdrawal-age",
        type=int,
        default=67,
        help="Post-retirement taxable pension withdrawal age (default: 67)",
    )
    parser.add_argument(
        "--postret-taxable-pension-targeted-withdrawal-percentage",
        type=float,
        default=0.0,
        help="Post-retirement taxable pension targeted withdrawal percentage (default: 0.0)",
    )

    parser.add_argument(
        "--config", type=str, help="Load parameters from JSON config file"
    )
    parser.add_argument("--output", type=str, help="Output CSV file path")
    parser.add_argument(
        "--summary", action="store_true", help="Show summary statistics"
    )
    return parser


def load_profile_from_json(file_path: str) -> "ProfileSettings":
    try:
        path = Path(file_path)
        return deserialise_profile_settings_from_json(path)
    except Exception as e:
        print(f"Error loading profile json file {file_path}: {e}")
        sys.exit(1)


def convert_parser_arguments_to_profile(
    parse: argparse.Namespace,
) -> "ProfileSettings":
    args = vars(parse)
    qualifying_earnings = get_qualifying_earnings_info(
        args["use_qualifying"], args["tax_year"]
    )
    personal_details = get_personal_details(
        args["current_age"],
        args["retirement_age"],
        args["salary"],
        args["tax_year"],
        args["scotland"],
    )
    contribution_settings = get_contribution_settings(
        qualifying_earnings,
        personal_details,
        args["use_exact_amounts"],
        args["workplace_employer_contribution"],
        args["workplace_employee_contribution"],
        args["lisa_contribution"],
        args["isa_contribution"],
        args["sipp_contribution"],
    )

    account_balances = AccountBalances(
        lisa_balance=args["lisa_balance"],
        isa_balance=args["isa_balance"],
        sipp_balance=args["sipp_balance"],
        workplace_pension_balance=args["workplace_balance"],
    )

    lisa_contribution = contribution_settings.lisa_contribution
    post_50_contribution_settings = get_post_50_contribution_settings(
        use_exact_amount_post50=args["use_exact_amount_post50"],
        redirectable_to_isa_contribution=args["redirectable_to_isa"],
        lisa_contribution=lisa_contribution,
    )

    expected_returns_and_inflation = ExpectedReturnsAndInflation(
        expected_lisa_annual_return=args["roi_lisa"],
        expected_isa_annual_return=args["roi_isa"],
        expected_sipp_annual_return=args["roi_sipp"],
        expected_workplace_annual_return=args["roi_workplace"],
        expected_inflation=args["inflation"],
    )

    post_retirement_settings = PostRetirementSettings(
        withdrawal_today_amount=args["postret_withdrawal_today"],
        expected_post_retirement_lisa_annual_return=args["postret_roi_lisa"],
        expected_post_retirement_isa_annual_return=args["postret_roi_isa"],
        expected_post_retirement_pension_annual_return=args["postret_roi_pension"],
        postret_isa_withdrawal_age=args["postret_isa_withdrawal_age"],
        postret_isa_targeted_withdrawal_percentage=args[
            "postret_isa_targeted_withdrawal_percentage"
        ],
        postret_lisa_withdrawal_age=args["postret_lisa_withdrawal_age"],
        postret_lisa_targeted_withdrawal_percentage=args[
            "postret_lisa_targeted_withdrawal_percentage"
        ],
        postret_taxfree_pension_withdrawal_age=args[
            "postret_taxfree_pension_withdrawal_age"
        ],
        postret_taxfree_pension_targeted_withdrawal_percentage=args[
            "postret_taxfree_pension_targeted_withdrawal_percentage"
        ],
        postret_taxable_pension_withdrawal_age=args[
            "postret_taxable_pension_withdrawal_age"
        ],
        postret_taxable_pension_targeted_withdrawal_percentage=args[
            "postret_taxable_pension_targeted_withdrawal_percentage"
        ],
    )
    return ProfileSettings(
        tax_year=args["tax_year"],
        scotland=args["scotland"],
        personal_details=personal_details,
        qualifying_earnings=qualifying_earnings,
        contribution_settings=contribution_settings,
        account_balances=account_balances,
        post_50_contribution_settings=post_50_contribution_settings,
        expected_returns_and_inflation=expected_returns_and_inflation,
        post_retirement_settings=post_retirement_settings,
    )


def print_summary(dataframe: pd.DataFrame, total_initial_balance: float) -> None:
    total_final_balance = (
        dataframe["LISA Balance"].iloc[-1]
        + dataframe["ISA Balance"].iloc[-1]
        + dataframe["SIPP Balance"].iloc[-1]
        + dataframe["Workplace Balance"].iloc[-1]
    )
    final_year = dataframe.iloc[-1]
    portfilio_balance = final_year["Portfolio Balance"]
    net_contribution = final_year["Portfolio Net Contribution"]
    growth = portfilio_balance - net_contribution - total_initial_balance

    print("\n" + "=" * 50)
    print("RETIREMENT PROJECTION SUMMARY")
    print("=" * 50)
    print(f"Retirement age: {final_year['Age']}")
    print(f"Salary: £{final_year['Salary']:,.0f}")
    print()
    print("Final pot values:")
    print(f"  LISA:      £{final_year['LISA Balance']:,.0f}")
    print(f"  ISA:       £{final_year['ISA Balance']:,.0f}")
    print(f"  SIPP:      £{final_year['SIPP Balance']:,.0f}")
    print(f"  Workplace: £{final_year['Workplace Balance']:,.0f}")
    print(f"  TOTAL:     £{total_final_balance:,.0f}")
    print()

    print(f"Total net contributions: £{net_contribution:,.0f}")
    print(f"Total initial balance: £{total_initial_balance:,.0f}")
    print(f"Total growth: £{growth:,.0f}")
    multipler = max((portfilio_balance - total_initial_balance) / net_contribution, 1)
    if multipler == float("inf"):
        multipler = "inf"
    elif multipler == float("nan"):
        multipler = "NaN"
    else:
        multipler = f"{multipler:.2f}x"
    print(f"Growth multiple: {multipler}")


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    if args.config:
        profile_settings = load_profile_from_json(args.config)
    else:
        profile_settings = convert_parser_arguments_to_profile(args)

    investment_dataframe = pw.project_investment(profile_settings)
    retirement_dataframe = pw.project_retirement(profile_settings, investment_dataframe)

    if args.output:
        investment_dataframe.to_csv(f"investment_{args.output}", index=False)
        retirement_dataframe.to_csv(f"retirement_{args.output}", index=False)
        print(f"Results saved to investment_{args.output} and retirement_{args.output}")

    if args.summary:
        total_initial_balance = (
            profile_settings.account_balances.isa_balance
            + profile_settings.account_balances.lisa_balance
            + profile_settings.account_balances.sipp_balance
            + profile_settings.account_balances.workplace_pension_balance
        )
        print_summary(investment_dataframe, total_initial_balance)

    if not args.output and not args.summary:
        print(investment_dataframe.to_string(index=False))


if __name__ == "__main__":
    main()
