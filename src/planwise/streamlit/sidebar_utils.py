"""
This module provides utility functions for configuring the Streamlit sidebar
in the Planwise application.
"""
from dataclasses import dataclass
from typing import Tuple

import streamlit as st

import planwise as pw


def get_qualifying_earnings_info(use_qualifying: bool, tax_year: int) -> "QualifyingEarnings":
    """Get qualifying earnings information for the specified tax year.

    Parameters
    ----------
    use_qualifying : bool
        Whether to use qualifying earnings for calculations.
    tax_year : int
        The start year of the tax year (e.g. 2024 for 2024/25).

    Returns
    -------
    QualifyingEarnings
        A dataclass containing qualifying earnings information.
    """
    limits_db = pw.LIMITS_DB[str(tax_year)]
    qualifying_upper = limits_db["qualifying_upper"]
    qualifying_lower = limits_db["qualifying_lower"]
    qualifying_earnings = qualifying_upper - qualifying_lower
    return QualifyingEarnings(use_qualifying, qualifying_earnings, qualifying_upper, qualifying_lower)

@dataclass
class QualifyingEarnings:
    """Data class to hold qualifying earnings information.

    Attributes
    ----------
    use_qualifying_earnings : bool
        Whether to use qualifying earnings for calculations.
    qualifying_earnings : float
        The difference between the qualifying upper and lower bounds.
    qualifying_upper : float
        The upper bound for qualifying earnings.
    qualifying_lower : float
        The lower bound for qualifying earnings.
    """
    use_qualifying_earnings: bool
    qualifying_earnings: float
    qualifying_upper: float
    qualifying_lower: float


@dataclass
class PersonalDetails:
    """Data class to hold personal details inputs from the user.

    Attributes
    ----------
    current_age : int
        The user's current age.
    retirement_age : int
        The age at which the user plans to retire.
    salary : float
        The user's gross annual salary.
    take_home_salary : float
        The estimated take-home salary after deductions.
    ni_contribution : float
        The estimated National Insurance contributions.
    income_tax : float
        The estimated income tax due.
    """
    current_age: int
    retirement_age: int
    salary: float
    take_home_salary: float
    ni_contribution: float
    income_tax: float

@dataclass
class ContributionSettings:
    """Data class to hold contribution settings.
    Attributes
    ----------
    workplace_er_rate: float
        The employer's contribution rate to the workplace pension.
    workplace_er_contribution: float
        The amount contributed by the employer to the workplace pension.
    workplace_ee_rate: float
        The employee's contribution rate to the workplace pension.
    workplace_ee_contribution: float
        The amount contributed by the employee to the workplace pension.
    lisa_rate: float
        The contribution rate to the Lifetime ISA (LISA).
    lisa_contribution: float
        The amount contributed to the LISA.
    isa_rate: float
        The contribution rate to the Individual Savings Account (ISA).
    isa_contribution: float
        The amount contributed to the ISA.
    sipp_rate: float
        The contribution rate to the Self-Invested Personal Pension (SIPP).
    sipp_contribution: float
        The amount contributed to the SIPP.
    total_workplace_contribution: float
        The total contribution to the workplace pension (employer + employee).
    total_sipp_contribution: float
        The total contribution to the SIPP.
    total_isa_contribution: float
        The total contribution to the ISA (including LISA).
    total_net_contribution: float
        The total net contribution made by the user across all accounts.
    total_pension_contribution: float
        The total pension contribution made by the user across pension accounts.
    """
    workplace_er_rate: float
    workplace_er_contribution: float
    workplace_ee_rate: float
    workplace_ee_contribution: float
    lisa_rate: float
    lisa_contribution: float
    isa_rate: float
    isa_contribution: float
    sipp_rate: float
    sipp_contribution: float
    total_workplace_contribution: float
    total_sipp_contribution: float
    total_isa_contribution: float
    total_net_contribution: float
    total_pension_contribution: float

@dataclass
class Post50ContributionSettings:
    """Data class to hold post-50 contribution settings.

    Attributes
    ----------
    post_50_lisa_to_isa_rate: float
        The rate at which LISA contributions can be redirected to ISA after age 50.
    post_50_lisa_to_isa_contribution: float
        The amount redirected from LISA to ISA after age 50.
    post_50_lisa_to_sipp_rate: float
        The rate at which LISA contributions can be redirected to SIPP after age 50.
    post_50_lisa_to_sipp_contribution: float
        The amount redirected from LISA to SIPP after age 50.
    """
    post_50_lisa_to_isa_rate: float
    post_50_lisa_to_isa_contribution: float
    post_50_lisa_to_sipp_rate: float
    post_50_lisa_to_sipp_contribution: float

@dataclass
class ExpectedReturnsAndInflation:
    """Data class to hold expected returns and inflation rates.

    Attributes
    ----------
    expected_lisa_annual_return: float
        The expected annual return rate for the LISA account.
    expected_isa_annual_return: float
        The expected annual return rate for the ISA account.
    expected_sipp_annual_return: float
        The expected annual return rate for the SIPP account.
    expected_workplace_annual_return: float
        The expected annual return rate for the workplace pension account.
    expected_inflation: float
        The expected annual inflation rate.
    """
    expected_lisa_annual_return: float
    expected_isa_annual_return: float
    expected_sipp_annual_return: float
    expected_workplace_annual_return: float
    expected_inflation: float

@dataclass
class PostRetirementSettings:
    """Data class to hold post-retirement settings.

    Attributes
    ----------
    withdrawal_today_amount: float
        The amount to withdraw today from the retirement accounts.
    expected_post_retirement_lisa_annual_return: float
        The expected annual return rate for the LISA account after retirement.
    expected_post_retirement_isa_annual_return: float
        The expected annual return rate for the ISA account after retirement.
    expected_post_retirement_pension_annual_return: float
        The expected annual return rate for the pension account after retirement.
    postret_lisa_withdrawal_age: int
        The age at which the user plans to start withdrawing from the LISA account.
    postret_lisa_targeted_withdrawal_percentage: float
        The targeted percentage of the LISA account to withdraw after retirement.
    postret_isa_withdrawal_age: int
        The age at which the user plans to start withdrawing from the ISA account.
    postret_isa_targeted_withdrawal_percentage: float
        The targeted percentage of the ISA account to withdraw after retirement.
    postret_pension_withdrawal_age: int
        The age at which the user plans to start withdrawing from the pension account.
    postret_pension_targeted_withdrawal_percentage: float
        The targeted percentage of the pension account to withdraw after retirement.
    """
    withdrawal_today_amount: float
    expected_post_retirement_lisa_annual_return: float
    expected_post_retirement_isa_annual_return: float
    expected_post_retirement_pension_annual_return: float
    postret_lisa_withdrawal_age: int
    postret_lisa_targeted_withdrawal_percentage: float
    postret_isa_withdrawal_age: int
    postret_isa_targeted_withdrawal_percentage: float
    postret_pension_withdrawal_age: int
    postret_pension_targeted_withdrawal_percentage: float

@dataclass
class ProfileSettings:
    """Data class to hold all profile settings for the Planwise application.

    Attributes
    ----------
    tax_year : int
        The tax year for which the profile settings apply.
    scotland : bool
        Whether the profile is for a user in Scotland.
    qualifying_earnings : QualifyingEarnings
        The qualifying earnings information for the user.
    personal_details : PersonalDetails
        The personal details of the user, including salary and take-home salary.
    contribution_settings : ContributionSettings
        The contribution settings for the user, including rates and amounts.
    post_50_contribution_settings : Post50ContributionSettings
        The contribution settings for the user after age 50.
    expected_returns_and_inflation : ExpectedReturnsAndInflation
        The expected returns and inflation rates for the user's investments.
    post_retirement_settings : PostRetirementSettings
        The post-retirement settings for the user, including withdrawal strategies.
    """
    tax_year: int
    scotland: bool
    qualifying_earnings: "QualifyingEarnings"
    personal_details: "PersonalDetails"
    contribution_settings: "ContributionSettings"
    post_50_contribution_settings: "Post50ContributionSettings"
    expected_returns_and_inflation: "ExpectedReturnsAndInflation"
    post_retirement_settings: "PostRetirementSettings"


def lisa_contribution_rate(tax_year: int, take_home_salary: float, total_contribution: float, use_exact_amount: bool = False) -> Tuple[float, float]:
    """
    Subsection of _contribution_rates_section to handle LISA contributions.

    Parameters
    ----------
    tax_year : int
        The tax year for which the LISA contribution is being calculated.
    take_home_salary : float
        The user's take-home salary.
    total_contribution : float
        The total amount contributed to pensions so far.
    use_exact_amount : bool, optional
        If True, allows the user to input an exact LISA contribution amount.
        If False, calculates the contribution as a percentage of take-home salary.

    Returns
    -------
    Tuple[float, float]
        A tuple containing the LISA contribution rate and the actual contribution amount.
    """
    lisa_limit = pw.LIMITS_DB[str(tax_year)]["lisa_limit"]
    unused_salary = take_home_salary - total_contribution
    if not use_exact_amount:
        max_lisa_rate = min(lisa_limit / take_home_salary, 1.0, unused_salary / take_home_salary)
        lisa_rate = st.slider(
            "LISA contribution %",
            0.0,
            max_lisa_rate,
            0.0,
            step=0.001,
            key="lisa_rate",
            help=f"LISA contribution limit is £{lisa_limit:,.0f}.")
        lisa_contribution = take_home_salary * lisa_rate
    else:
        lisa_contribution = st.number_input(
            "LISA contribution (£)",
            min_value=0.0,
            max_value=min(lisa_limit, unused_salary),
            value=0.0,
            step=100.0,
            key="lisa_contribution",
            help=f"LISA contribution limit is £{lisa_limit:,.0f}."
        )
        lisa_rate = lisa_contribution / take_home_salary if take_home_salary > 0 else 0.0
    st.write(f"**LISA contribution:** £{lisa_contribution:,.0f} ({lisa_rate*100:,.3}%)")
    return lisa_rate, lisa_contribution


def isa_contribution_rate(tax_year: int, take_home_salary: float, lisa_contribution: float, total_contribution: float, use_exact_amount: bool = False) -> Tuple[float, float]:
    """
    Subsection of _contribution_rates_section to handle ISA contributions.

    Parameters
    ----------
    tax_year : int
        The tax year for which the ISA contribution is being calculated.
    take_home_salary : float
        The user's take-home salary.
    lisa_contribution : float
        The amount contributed to the LISA.
    total_contribution : float
        The total amount contributed to pensions so far.
    use_exact_amount : bool, optional
        If True, allows the user to input an exact ISA contribution amount.
        If False, calculates the contribution as a percentage of take-home salary.

    Returns
    -------
    Tuple[float, float]
        A tuple containing the ISA contribution rate and the actual contribution amount.
    """
    isa_limit = pw.LIMITS_DB[str(tax_year)]["isa_limit"]
    remaining_isa_allowance = max(isa_limit - lisa_contribution, 0.0)
    unused_salary = take_home_salary - total_contribution - lisa_contribution
    if not use_exact_amount:
        max_isa_rate = min(remaining_isa_allowance / take_home_salary, 1.0, unused_salary / take_home_salary)
        isa_rate = st.slider(
            "ISA contribution %",
            0.0,
            max_isa_rate,
            0.0,
            step=0.001,
            key="isa_rate",
            help=f"ISA contribution limit is £{isa_limit:,.0f} including LISA contributions."
        )
        isa_contribution = take_home_salary * isa_rate
    else:
        isa_contribution = st.number_input(
            "ISA contribution (£)",
            min_value=0.0,
            max_value=min(remaining_isa_allowance, unused_salary),
            value=0.0,
            step=100.0,
            key="isa_contribution",
            help=f"ISA contribution limit is £{isa_limit:,.0f} including LISA contributions."
        )
        isa_rate = isa_contribution / take_home_salary if take_home_salary > 0 else 0.0
    st.write(f"**ISA contribution:** £{isa_contribution:,.0f} ({isa_rate*100:,.3}%)")
    return isa_rate, isa_contribution


def workplace_er_contribution_rate(tax_year: int, personal_details: "PersonalDetails", qualifying_earnings: "QualifyingEarnings", use_exact_amount: bool = False) -> Tuple[float, float]:
    """
    Subsection of _contribution_rates_section to handle workplace employer contributions.

    Parameters
    ----------
    tax_year : int
        The tax year for which the contribution is being calculated.
    personal_details : PersonalDetails
        The personal details of the user, including salary and take-home salary.
    qualifying_earnings : QualifyingEarnings
        The qualifying earnings information for the user.
    use_exact_amount : bool, optional
        If True, allows the user to input an exact contribution amount.
        If False, calculates the contribution as a percentage of full salary.

    Returns
    -------
    Tuple[float, float]
        A tuple containing the employer contribution rate and the actual contribution amount.
    """
    pension_allowance = pw.LIMITS_DB[str(tax_year)]["pension_annual_allowance"]
    if not use_exact_amount:
        workplace_employer_rate = st.slider(
            "Workplace Pension (Employer) %",
            0.0,
            1.0,
            0.03,
            step=0.001,
            key="workplace_employer_rate",
            help="Employer contributions to workplace pension. Max allowed by annual allowance (£{pension_allowance:,.0f}).",
        )
        if qualifying_earnings.use_qualifying_earnings:
            potential_contribution_amount = personal_details.salary - qualifying_earnings.qualifying_lower if personal_details.salary < qualifying_earnings.qualifying_upper else qualifying_earnings.qualifying_earnings
            workplace_employer_contribution = potential_contribution_amount * workplace_employer_rate
        else:
            workplace_employer_contribution = personal_details.salary * workplace_employer_rate
    else:
        if qualifying_earnings.use_qualifying_earnings:
            potential_contribution_amount = personal_details.salary - qualifying_earnings.qualifying_lower if personal_details.salary < qualifying_earnings.qualifying_upper else qualifying_earnings.qualifying_earnings
            workplace_employer_contribution = st.number_input(
                "Workplace Pension (Employer) (£)",
                min_value=0.0,
                max_value=min(potential_contribution_amount, pension_allowance),
                value=0.0,
                step=100.0,
                key="workplace_employer_contribution",
                help=f"Employer contributions to workplace pension. Max allowed by annual allowance (£{pension_allowance:,.0f})."
            )
        else:
            workplace_employer_contribution = st.number_input(
                "Workplace Pension (Employer) (£)",
                min_value=0.0,
                max_value=min(personal_details.salary, pension_allowance),
                value=0.0,
                step=100.0,
                key="workplace_employer_contribution",
                help=f"Employer contributions to workplace pension. Max allowed by annual allowance (£{pension_allowance:,.0f})."
            )
        workplace_employer_rate = workplace_employer_contribution / personal_details.salary if personal_details.salary > 0 else 0.0
    st.write(f"**Workplace (ER) Pension:** £{workplace_employer_contribution:,.0f} ({workplace_employer_rate*100:,.4}%)")
    return workplace_employer_rate, workplace_employer_contribution


def workplace_ee_contribution_rate(tax_year: int, personal_details: "PersonalDetails", workspace_er_contribution: float, qualifying_earnings: "QualifyingEarnings", use_exact_amount: bool = False) -> Tuple[float, float]:
    """
    Subsection of _contribution_rates_section to handle workplace employee contributions.

    Parameters
    ----------
    tax_year : int
        The tax year for which the contribution is being calculated.
    personal_details : PersonalDetails
        The personal details of the user, including salary and take-home salary.
    workspace_er_contribution : float
        The amount contributed by the employer to the workplace pension.
    qualifying_earnings : QualifyingEarnings
        The qualifying earnings information for the user.
    use_exact_amount : bool, optional
        If True, allows the user to input an exact contribution amount.
        If False, calculates the contribution as a percentage of full salary.

    Returns
    -------
    Tuple[float, float]
        A tuple containing the employee contribution rate and the actual contribution amount.
    """
    pension_allowance = pw.LIMITS_DB[str(tax_year)]["pension_annual_allowance"]
    unused_allowance = pension_allowance - workspace_er_contribution
    tax_relief_rate = 1.25 # 25% tax relief on pension contributions
    if not use_exact_amount:
        if qualifying_earnings.use_qualifying_earnings:
            max_workspace_ee_rate = min(
                (personal_details.salary - qualifying_earnings.qualifying_lower) / qualifying_earnings.qualifying_earnings,
                (personal_details.salary - qualifying_earnings.qualifying_lower) / personal_details.take_home_salary, # Cannot exceed take-home salary
                1, # full qualifying_earnings.qualifying_earnings
                unused_allowance / (pension_allowance * tax_relief_rate),
            )
        else:
            max_workspace_ee_rate = min(
                personal_details.take_home_salary / personal_details.salary, # Cannot exceed take-home salary
                1, # full salary
                unused_allowance / (personal_details.salary * tax_relief_rate),
            )

        workplace_employee_rate = st.slider(
            "Net Workplace Pension (Employee) %",
            0.0,
            max_workspace_ee_rate,
            0.05,
            step=0.001,
            key="workplace_employee_rate",
            help="Employee contributions to workplace pension, exluding tax relief.",
        )
        if qualifying_earnings.use_qualifying_earnings:
            potential_contribution_amount = personal_details.salary - qualifying_earnings.qualifying_lower if personal_details.salary < qualifying_earnings.qualifying_upper else qualifying_earnings.qualifying_earnings
            workplace_employee_contribution = potential_contribution_amount * workplace_employee_rate
        else:
            workplace_employee_contribution = personal_details.salary * workplace_employee_rate
    else:
        if qualifying_earnings.use_qualifying_earnings:
            max_workspace_ee_contribution = min(
                personal_details.take_home_salary - qualifying_earnings.qualifying_lower,
                qualifying_earnings.qualifying_earnings,
                unused_allowance / tax_relief_rate,
            )
        else:
            max_workspace_ee_contribution = min(
                personal_details.take_home_salary,
                unused_allowance / tax_relief_rate,
            )
        workplace_employee_contribution = st.number_input(
            "Net Workplace Pension (Employee) (£)",
            min_value=0.0,
            max_value=max_workspace_ee_contribution,
            value=0.0,
            step=100.0,
            key="workplace_employee_contribution",
            help="Employee contributions to workplace pension, excluding tax relief.",
        )
        workplace_employee_rate = workplace_employee_contribution / personal_details.salary if personal_details.salary > 0 else 0.0
    st.write(f"**Workplace (EE) Pension:** £{workplace_employee_contribution:,.0f} ({workplace_employee_rate*100:,.4}%)")
    return workplace_employee_rate, workplace_employee_contribution


def sipp_contribution_rate(tax_year: int, personal_details: "PersonalDetails", total_workplace_contribution: float, total_contribution: float, use_exact_amount: bool = False) -> Tuple[float, float]:
    """
    Subsection of _contribution_rates_section to handle SIPP contributions.

    Parameters
    ----------

    Returns
    -------
    Tuple[float, float]
        A tuple containing the SIPP contribution rate and the actual contribution amount.
    """
    pension_allowance = pw.LIMITS_DB[str(tax_year)]["pension_annual_allowance"]
    unused_allowance = pension_allowance - total_workplace_contribution
    unused_salary = personal_details.take_home_salary - total_contribution
    tax_relief_rate = 1.25  # 25% tax relief on pension contributions
    if not use_exact_amount:
        max_sipp_rate = min(
            unused_salary / personal_details.take_home_salary,
            unused_allowance / (pension_allowance * tax_relief_rate),
            1.0
        )
        sipp_rate = st.slider(
            "SIPP contribution %",
            0.0,
            max_sipp_rate,
            0.0,
            step=0.001,
            key="sipp_rate",
            help=f"SIPP contribution limit is £{pension_allowance:,.0f} including workplace contributions."
        )
        sipp_contribution = personal_details.take_home_salary * sipp_rate
    else:
        max_sipp_contribution = min(
            unused_salary,
            unused_allowance / tax_relief_rate,
            pension_allowance
        )
        sipp_contribution = st.number_input(
            "SIPP contribution (£)",
            min_value=0.0,
            max_value=max_sipp_contribution,
            value=0.0,
            step=100.0,
            key="sipp_contribution",
            help=f"SIPP contribution limit is £{pension_allowance:,.0f} including workplace contributions."
        )
        sipp_rate = sipp_contribution / personal_details.take_home_salary if personal_details.take_home_salary > 0 else 0.0
    st.write(f"**SIPP contribution:** £{sipp_contribution:,.0f} ({sipp_rate*100:,.3}%)")
    return sipp_rate, sipp_contribution
