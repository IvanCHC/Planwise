"""
Configuration management utilities for Planwise Streamlit app.
Handles saving, loading, deleting, and listing user session profiles as JSON files.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .databases import LIMITS_DB

PROFILES_DIR = Path(".profiles")
PROFILES_DIR.mkdir(exist_ok=True)
SAFE_CHARS = re.compile(r"[^A-Za-z0-9 _.-]")


def safe_filename(name: str) -> str:
    name = name.strip()
    name = SAFE_CHARS.sub("_", name)
    name = re.sub(r"\s+", " ", name)
    return name[:80]


def profile_path(name: str) -> Path:
    return PROFILES_DIR / f"{safe_filename(name)}.json"


def list_profiles() -> list[str]:
    return sorted(p.stem for p in PROFILES_DIR.glob("*.json"))


def save_profile(name: str, data: dict) -> None:
    profile_path(name).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_profile(name: str) -> dict | None:
    p = profile_path(name)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def delete_profile(name: str) -> None:
    p = profile_path(name)
    if p.exists():
        p.unlink()


def get_qualifying_earnings_info(
    use_qualifying: bool, tax_year: int
) -> "QualifyingEarnings":
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
    limits_db = LIMITS_DB[str(tax_year)]
    qualifying_upper = limits_db["qualifying_upper"]
    qualifying_lower = limits_db["qualifying_lower"]
    qualifying_earnings = qualifying_upper - qualifying_lower
    return QualifyingEarnings(
        use_qualifying, qualifying_earnings, qualifying_upper, qualifying_lower
    )


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
class AccountBalances:
    """Data class to hold account balances.

    Attributes
    ----------
    lisa_balance: float
        The current balance in the Lifetime ISA (LISA).
    isa_balance: float
        The current balance in the Individual Savings Account (ISA).
    sipp_balance: float
        The current balance in the Self-Invested Personal Pension (SIPP).
    workplace_pension_balance: float
        The current balance in the workplace pension.
    """

    lisa_balance: float
    isa_balance: float
    sipp_balance: float
    workplace_pension_balance: float


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
    postret_taxfree_pension_withdrawal_age: int
        The age at which the user plans to start withdrawing tax-free from the pension account.
    postret_taxfree_pension_targeted_withdrawal_percentage: float
        The targeted percentage of the pension account to withdraw tax-free after retirement.
    postret_taxable_pension_withdrawal_age: int
        The age at which the user plans to start withdrawing taxable from the pension account.
    postret_taxable_pension_targeted_withdrawal_percentage: float
        The targeted percentage of the pension account to withdraw taxable after retirement.
    """

    withdrawal_today_amount: float
    expected_post_retirement_lisa_annual_return: float
    expected_post_retirement_isa_annual_return: float
    expected_post_retirement_pension_annual_return: float
    postret_lisa_withdrawal_age: int
    postret_lisa_targeted_withdrawal_percentage: float
    postret_isa_withdrawal_age: int
    postret_isa_targeted_withdrawal_percentage: float
    postret_taxfree_pension_withdrawal_age: int
    postret_taxfree_pension_targeted_withdrawal_percentage: float
    postret_taxable_pension_withdrawal_age: int
    postret_taxable_pension_targeted_withdrawal_percentage: float


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
    account_balances : AccountBalances
        The current balances of the user's accounts, including LISA, ISA, SIPP, and
        workplace pension.
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
    account_balances: "AccountBalances"
    post_50_contribution_settings: "Post50ContributionSettings"
    expected_returns_and_inflation: "ExpectedReturnsAndInflation"
    post_retirement_settings: "PostRetirementSettings"
