"""
Core retirement projection calculations for Planwise.

This module contains the main projection function that models retirement
savings across various UK tax wrappers over time. It provides dataclasses for user
profile, contribution rates, and investment returns, as well as helper functions for
calculating contributions and projecting account balances.
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd

from .tax import calculate_income_tax


@dataclass
class UserProfile:
    """
    User profile for retirement projection.
    Attributes:
        current_age (int): Current age of the user.
        retirement_age (int): Target retirement age.
        salary (float): Current annual salary.
        scotland (bool): Use Scottish tax bands if True.
    """

    current_age: int
    retirement_age: int
    salary: float
    scotland: bool


@dataclass
class ContributionRates:
    """
    Contribution rates for each account type and post-50 redirection.
    Attributes:
        lisa (float): LISA contribution rate.
        isa (float): ISA contribution rate.
        sipp_employee (float): SIPP employee contribution rate.
        sipp_employer (float): SIPP employer contribution rate.
        workplace_employee (float): Workplace pension employee rate.
        workplace_employer (float): Workplace pension employer rate.
        shift_lisa_to_isa (float): Fraction of LISA redirected to ISA after 50.
        shift_lisa_to_sipp (float): Fraction of LISA redirected to SIPP after 50.
    """

    lisa: float
    isa: float
    sipp_employee: float
    sipp_employer: float
    workplace_employee: float
    workplace_employer: float
    shift_lisa_to_isa: float
    shift_lisa_to_sipp: float


@dataclass
class InvestmentReturns:
    """
    Expected annual rates of return for each account type.
    Attributes:
        lisa (float): LISA annual return.
        isa (float): ISA annual return.
        sipp (float): SIPP annual return.
        workplace (float): Workplace pension annual return.
    """

    lisa: float
    isa: float
    sipp: float
    workplace: float


@dataclass
class IncomeBreakdown:
    """
    Breakdown of income sources for retirement projection.
    Attributes:
        salary (float): Annual salary.
        take_home_salary (float): Net salary after tax and NI.
        income_tax (float): Total income tax due.
        ni_due (float): National Insurance contributions due.
    """

    salary: float
    take_home_salary: float
    income_tax: float
    ni_due: float


def load_limits_db() -> Any:
    """
    Load annual limits and constants from JSON file.
    Returns:
        dict: Limits for each tax year.
    """
    json_path = os.path.join(os.path.dirname(__file__), "data", "limits.json")
    with open(json_path, "r") as f:
        return json.load(f)


def calculate_lisa_isa_contributions(
    current_salary: float,
    age: int,
    contrib: ContributionRates,
    lisa_limit: float,
    isa_limit: float,
) -> dict:
    """
    Calculate LISA and ISA contributions, including redirection after age 50.
    Args:
        current_salary (float): Current annual salary.
        age (int): Current age.
        contrib (ContributionRates): Contribution rates.
        lisa_limit (float): Annual LISA contribution limit.
        isa_limit (float): Annual ISA contribution limit.
    Returns:
        dict: Calculated net/gross contributions and redirections.
    """
    # LISA contributions (only allowed under age 50)
    this_lisa_rate = contrib.lisa if age < 50 else 0.0
    lisa_net = current_salary * this_lisa_rate
    if lisa_net > lisa_limit:
        lisa_net = lisa_limit
    lisa_bonus = lisa_net * 0.25
    lisa_gross = lisa_net + lisa_bonus

    # If over age 50, redirect LISA contribution amount into ISA and SIPP
    lisa_to_isa_rate = contrib.shift_lisa_to_isa if age >= 50 else 0.0
    lisa_to_sipp_rate = contrib.shift_lisa_to_sipp if age >= 50 else 0.0
    redirected_amount = current_salary * contrib.lisa if age >= 50 else 0.0
    redirected_isa_net = redirected_amount * lisa_to_isa_rate

    # ISA contributions (net)
    isa_net = current_salary * contrib.isa + redirected_isa_net
    remaining_isa_allowance = isa_limit - (lisa_net if this_lisa_rate > 0 else 0)
    if isa_net > remaining_isa_allowance:
        isa_net = remaining_isa_allowance

    # For SIPP redirection
    redirected_sipp_net = redirected_amount * lisa_to_sipp_rate

    return {
        "lisa_net": lisa_net,
        "lisa_bonus": lisa_bonus,
        "lisa_gross": lisa_gross,
        "isa_net": isa_net,
        "redirected_sipp_net": redirected_sipp_net,
    }


def calculate_pension_contributions(
    current_salary: float,
    base_for_workplace: float,
    contrib: ContributionRates,
    redirected_sipp_net: float,
) -> dict:
    """
    Calculate SIPP and workplace pension contributions.
    Args:
        current_salary (float): Current annual salary.
        base_for_workplace (float): Salary base for workplace pension (may be qualifying earnings).
        contrib (ContributionRates): Contribution rates.
        redirected_sipp_net (float): Amount redirected to SIPP from LISA after age 50.
    Returns:
        dict: Calculated net/gross contributions for SIPP and workplace pension.
    """
    # SIPP personal contributions (employee) – relief at source
    sipp_employee_net = current_salary * contrib.sipp_employee + redirected_sipp_net
    sipp_employee_gross = sipp_employee_net / 0.8 if sipp_employee_net > 0 else 0.0

    # Employer contributions into SIPP (rare); no tax relief needed
    sipp_employer_gross = current_salary * contrib.sipp_employer

    # Workplace pension contributions – relief at source (employee)
    wp_employee_net = base_for_workplace * contrib.workplace_employee
    wp_employee_gross = wp_employee_net / 0.8 if wp_employee_net > 0 else 0.0

    # Employer contributions to workplace pension
    wp_employer_gross = base_for_workplace * contrib.workplace_employer

    return {
        "sipp_employee_net": sipp_employee_net,
        "sipp_employee_gross": sipp_employee_gross,
        "sipp_employer_gross": sipp_employer_gross,
        "wp_employee_net": wp_employee_net,
        "wp_employee_gross": wp_employee_gross,
        "wp_employer_gross": wp_employer_gross,
    }


LIMITS_DB = load_limits_db()


def project_retirement(
    user: UserProfile,
    contrib: ContributionRates,
    returns: InvestmentReturns,
    inflation: float,
    use_qualifying_earnings: bool,
    year: int,
) -> pd.DataFrame:
    """
    Compute the year-by-year contributions, tax relief, and account balances.

    Args:
        user (UserProfile): User profile including age, retirement age, salary, and region.
        contrib (ContributionRates): Contribution rates for each wrapper and shift rates after age 50.
        returns (InvestmentReturns): Expected annual rates of return for each wrapper.
        inflation (float): Annual inflation rate used to index salary and contributions (decimal).
        use_qualifying_earnings (bool): If True, workplace pension contributions are calculated on qualifying earnings (£6,240–£50,270). Otherwise, contributions are based on total salary.
        year (int): Tax year to use for income tax calculations (e.g., 2025 for 2025/26).

    Returns:
        pd.DataFrame: DataFrame with each year's age and financial metrics.
    """
    years = user.retirement_age - user.current_age

    # Load annual limits for the selected tax year
    limits = LIMITS_DB[str(year)]
    qualifying_lower = limits["qualifying_lower"]
    qualifying_upper = limits["qualifying_upper"]
    lisa_limit = limits["lisa_limit"]
    isa_limit = limits["isa_limit"]
    pension_annual_allowance = limits["pension_annual_allowance"]

    records: List[Dict] = []

    # Initialize account pots and salary
    pot_lisa = 0.0
    pot_isa = 0.0
    pot_sipp = 0.0
    pot_workplace = 0.0
    current_salary = user.salary

    # Initialize accumulators for net and gross contributions
    acc_lisa_net = 0.0
    acc_lisa_gross = 0.0
    acc_isa_net = 0.0
    acc_isa_gross = 0.0
    acc_sipp_net = 0.0
    acc_sipp_gross = 0.0
    acc_workplace_net = 0.0
    acc_workplace_gross = 0.0

    for year_index in range(years):
        age = user.current_age + year_index

        # Determine the contribution base for workplace pension
        if use_qualifying_earnings:
            qualifying_salary = min(
                max(current_salary - qualifying_lower, 0),
                qualifying_upper - qualifying_lower,
            )
            base_for_workplace = qualifying_salary
        else:
            base_for_workplace = current_salary

        # Calculate LISA/ISA contributions and redirections
        lisa_isa = calculate_lisa_isa_contributions(
            current_salary=current_salary,
            age=age,
            contrib=contrib,
            lisa_limit=lisa_limit,
            isa_limit=isa_limit,
        )
        lisa_net = lisa_isa["lisa_net"]
        lisa_bonus = lisa_isa["lisa_bonus"]
        lisa_gross = lisa_isa["lisa_gross"]
        isa_net = lisa_isa["isa_net"]
        redirected_sipp_net = lisa_isa["redirected_sipp_net"]

        # Calculate SIPP and workplace pension contributions
        pensions = calculate_pension_contributions(
            current_salary=current_salary,
            base_for_workplace=base_for_workplace,
            contrib=contrib,
            redirected_sipp_net=redirected_sipp_net,
        )
        sipp_employee_net = pensions["sipp_employee_net"]
        sipp_employee_gross = pensions["sipp_employee_gross"]
        sipp_employer_gross = pensions["sipp_employer_gross"]
        wp_employee_net = pensions["wp_employee_net"]
        wp_employee_gross = pensions["wp_employee_gross"]
        wp_employer_gross = pensions["wp_employer_gross"]

        # Total gross pension contributions (employee and employer)
        total_pension_gross = (
            sipp_employee_gross
            + sipp_employer_gross
            + wp_employee_gross
            + wp_employer_gross
        )

        # Ensure we do not exceed annual allowance; cap employee contributions to respect the allowance
        if total_pension_gross > pension_annual_allowance:
            excess = total_pension_gross - pension_annual_allowance
            # Reduce SIPP employee gross first
            if sipp_employee_gross >= excess:
                sipp_employee_gross -= excess
                sipp_employee_net = sipp_employee_gross * 0.8
                excess = 0
            else:
                excess -= sipp_employee_gross
                sipp_employee_gross = 0
                sipp_employee_net = 0
                # Then reduce workplace employee gross
                if wp_employee_gross >= excess:
                    wp_employee_gross -= excess
                    wp_employee_net = wp_employee_gross * 0.8
                    excess = 0
                else:
                    excess -= wp_employee_gross
                    wp_employee_gross = 0
                    wp_employee_net = 0
            total_pension_gross = pension_annual_allowance

        # Tax calculations
        tax_before = calculate_income_tax(current_salary, user.scotland, year=year)
        total_personal_gross = sipp_employee_gross + wp_employee_gross
        tax_after = calculate_income_tax(
            max(current_salary - total_personal_gross, 0), user.scotland, year=year
        )
        tax_relief_total = tax_before - tax_after

        # 20% basic relief has already been granted by the pension provider; additional relief is refundable
        basic_relief = total_personal_gross * 0.20
        tax_refund = max(tax_relief_total - basic_relief, 0)

        # Net cost to the individual
        net_contrib_total = sipp_employee_net + wp_employee_net + lisa_net + isa_net
        net_cost_after_refund = net_contrib_total - tax_refund

        # Update accumulated net and gross contributions
        acc_lisa_net += lisa_net
        acc_lisa_gross += lisa_gross
        acc_isa_net += isa_net
        acc_isa_gross += isa_net  # ISA gross = net (no bonus)
        acc_sipp_net += sipp_employee_net
        acc_sipp_gross += sipp_employee_gross + sipp_employer_gross
        acc_workplace_net += wp_employee_net
        acc_workplace_gross += wp_employee_gross + wp_employer_gross

        # Update pots by adding gross contributions and applying growth
        pot_lisa = pot_lisa * (1 + returns.lisa) + lisa_gross
        pot_isa = pot_isa * (1 + returns.isa) + isa_net
        pot_sipp = (
            pot_sipp * (1 + returns.sipp) + sipp_employee_gross + sipp_employer_gross
        )
        pot_workplace = (
            pot_workplace * (1 + returns.workplace)
            + wp_employee_gross
            + wp_employer_gross
        )

        # Record results for this year
        records.append(
            {
                "Age": age,
                "Salary": current_salary,
                "LISA Net": lisa_net,
                "LISA Bonus": lisa_bonus,
                "ISA Net": isa_net,
                "SIPP Employee Net": sipp_employee_net,
                "SIPP Employee Gross": sipp_employee_gross,
                "SIPP Employer": sipp_employer_gross,
                "Workplace Employee Net": wp_employee_net,
                "Workplace Employee Gross": wp_employee_gross,
                "Workplace Employer": wp_employer_gross,
                "Tax Relief (total)": tax_relief_total,
                "Tax Refund": tax_refund,
                "Net Contribution Cost": net_cost_after_refund,
                "Pot LISA": pot_lisa,
                "Pot ISA": pot_isa,
                "Pot SIPP": pot_sipp,
                "Pot Workplace": pot_workplace,
                # New columns for accumulated contributions
                "Accumulated LISA Net": acc_lisa_net,
                "Accumulated LISA Gross": acc_lisa_gross,
                "Accumulated ISA Net": acc_isa_net,
                "Accumulated ISA Gross": acc_isa_gross,
                "Accumulated SIPP Net": acc_sipp_net,
                "Accumulated SIPP Gross": acc_sipp_gross,
                "Accumulated Workplace Net": acc_workplace_net,
                "Accumulated Workplace Gross": acc_workplace_gross,
            }
        )

    df = pd.DataFrame(records)
    return df
