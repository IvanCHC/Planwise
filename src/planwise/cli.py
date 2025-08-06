"""
Command-line interface for the Planwise library.

This module provides a user-friendly CLI for running UK investment and retirement projections,
generating reports, and saving results to CSV. It supports configuration via command-line arguments
or a JSON config file.
"""

import argparse
import json
import sys
from typing import Any

import pandas as pd

from .core import (
    LIMITS_DB,
    ContributionRates,
    InvestmentReturns,
    UserProfile,
    project_retirement,
)


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser for Planwise CLI.
    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="UK Investment & Retirement Planning CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic projection
  planwise --current-age 30 --retirement-age 67 --salary 40000

  # With custom contribution rates
  planwise --current-age 30 --retirement-age 67 --salary 40000 \\
    --lisa-rate 0.05 --isa-rate 0.10 --sipp-employee-rate 0.05

  # Save results to CSV
  planwise --current-age 30 --retirement-age 67 --salary 40000 \\
    --output results.csv

  # Load parameters from JSON file
  planwise --config config.json
        """,
    )

    # Basic user parameters
    parser.add_argument(
        "--current-age", type=int, default=30, help="Current age (default: 30)"
    )
    parser.add_argument(
        "--retirement-age", type=int, default=67, help="Retirement age (default: 67)"
    )
    parser.add_argument(
        "--salary",
        type=float,
        default=40000,
        help="Annual salary in £ (default: 40000)",
    )

    # Contribution rates
    parser.add_argument(
        "--lisa-rate",
        type=float,
        default=0.05,
        help="LISA contribution rate (default: 0.05)",
    )
    parser.add_argument(
        "--isa-rate",
        type=float,
        default=0.05,
        help="ISA contribution rate (default: 0.05)",
    )
    parser.add_argument(
        "--sipp-employee-rate",
        type=float,
        default=0.05,
        help="SIPP employee contribution rate (default: 0.05)",
    )
    parser.add_argument(
        "--sipp-employer-rate",
        type=float,
        default=0.0,
        help="SIPP employer contribution rate (default: 0.0)",
    )
    parser.add_argument(
        "--workplace-employee-rate",
        type=float,
        default=0.05,
        help="Workplace pension employee rate (default: 0.05)",
    )
    parser.add_argument(
        "--workplace-employer-rate",
        type=float,
        default=0.03,
        help="Workplace pension employer rate (default: 0.03)",
    )

    # Post-50 redirection
    parser.add_argument(
        "--shift-lisa-to-isa",
        type=float,
        default=0.5,
        help="Fraction of LISA redirected to ISA after 50 (default: 0.5)",
    )
    parser.add_argument(
        "--shift-lisa-to-sipp",
        type=float,
        default=0.5,
        help="Fraction of LISA redirected to SIPP after 50 (default: 0.5)",
    )

    # Returns and inflation
    parser.add_argument(
        "--roi-lisa",
        type=float,
        default=0.05,
        help="LISA annual return (default: 0.05)",
    )
    parser.add_argument(
        "--roi-isa", type=float, default=0.05, help="ISA annual return (default: 0.05)"
    )
    parser.add_argument(
        "--roi-sipp",
        type=float,
        default=0.05,
        help="SIPP annual return (default: 0.05)",
    )
    parser.add_argument(
        "--roi-workplace",
        type=float,
        default=0.05,
        help="Workplace pension annual return (default: 0.05)",
    )
    parser.add_argument(
        "--inflation",
        type=float,
        default=0.02,
        help="Annual inflation rate (default: 0.02)",
    )

    # Tax settings
    parser.add_argument(
        "--scotland", action="store_true", help="Use Scottish tax bands"
    )
    parser.add_argument(
        "--use-qualifying-earnings",
        action="store_true",
        default=False,
        help="Use qualifying earnings for workplace pension (default: False)",
    )

    # Tax year
    parser.add_argument(
        "--tax-year",
        type=int,
        default=max([int(y) for y in LIMITS_DB.keys()]),
        help="Tax year for calculations (default: latest available)",
    )

    # Configuration and output
    parser.add_argument(
        "--config", type=str, help="Load parameters from JSON config file"
    )
    parser.add_argument("--output", type=str, help="Output CSV file path")
    parser.add_argument(
        "--summary", action="store_true", help="Show summary statistics"
    )

    return parser


def load_config(config_path: str) -> Any:
    """
    Load configuration from a JSON file.
    Args:
        config_path (str): Path to the JSON config file.
    Returns:
        dict: Loaded configuration.
    """
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_path}: {e}")
        sys.exit(1)


def print_summary(df: pd.DataFrame) -> None:
    """
    Print summary statistics for the retirement projection.
    Args:
        df (pd.DataFrame): DataFrame with projection results.
    """
    final_row = df.iloc[-1]
    total_final = (
        final_row["Pot LISA"]
        + final_row["Pot ISA"]
        + final_row["Pot SIPP"]
        + final_row["Pot Workplace"]
    )

    print("\n" + "=" * 50)
    print("RETIREMENT PROJECTION SUMMARY")
    print("=" * 50)
    print(f"Final age: {final_row['Age']}")
    print(f"Final salary: £{final_row['Salary']:,.0f}")
    print()
    print("Final pot values:")
    print(f"  LISA:      £{final_row['Pot LISA']:,.0f}")
    print(f"  ISA:       £{final_row['Pot ISA']:,.0f}")
    print(f"  SIPP:      £{final_row['Pot SIPP']:,.0f}")
    print(f"  Workplace: £{final_row['Pot Workplace']:,.0f}")
    print(f"  TOTAL:     £{total_final:,.0f}")
    print()

    total_contributions = df["Net Contribution Cost"].sum()
    print(f"Total net contributions: £{total_contributions:,.0f}")
    print(f"Total growth: £{total_final - total_contributions:,.0f}")
    print(f"Growth multiple: {total_final / max(total_contributions, 1):.1f}x")


def main() -> None:
    """
    Main CLI entry point for Planwise.
    Parses arguments, runs the projection, and outputs results.
    """
    parser = create_parser()
    args = parser.parse_args()

    # Optionally load config file and override args
    if args.config:
        config = load_config(args.config)
        for key, value in config.items():
            if hasattr(args, key.replace("-", "_")):
                setattr(args, key.replace("-", "_"), value)

    # Prepare user, contribution, and return dataclasses
    user = UserProfile(
        current_age=args.current_age,
        retirement_age=args.retirement_age,
        salary=args.salary,
        scotland=args.scotland,
    )
    contrib = ContributionRates(
        lisa=args.lisa_rate,
        isa=args.isa_rate,
        sipp_employee=args.sipp_employee_rate,
        sipp_employer=args.sipp_employer_rate,
        workplace_employee=args.workplace_employee_rate,
        workplace_employer=args.workplace_employer_rate,
        shift_lisa_to_isa=args.shift_lisa_to_isa,
        shift_lisa_to_sipp=args.shift_lisa_to_sipp,
    )
    returns = InvestmentReturns(
        lisa=args.roi_lisa,
        isa=args.roi_isa,
        sipp=args.roi_sipp,
        workplace=args.roi_workplace,
    )

    # Prepare a dummy IncomeBreakdown (not used in CLI projections)
    from .core import IncomeBreakdown

    income = IncomeBreakdown(
        salary=args.salary,
        take_home_salary=args.salary,  # Placeholder
        income_tax=0.0,  # Placeholder
        ni_due=0.0,  # Placeholder
    )
    try:
        df = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            income=income,
            inflation=args.inflation,
            use_qualifying_earnings=args.use_qualifying_earnings,
            year=args.tax_year,
        )
    except Exception as e:
        print(f"Error running projection: {e}")
        sys.exit(1)

    # Output results to CSV if requested
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Results saved to {args.output}")

    # Print summary if requested
    if args.summary:
        print_summary(df)

    # Otherwise, print the full DataFrame
    if not args.output and not args.summary:
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
