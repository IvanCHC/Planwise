"""
User profile management and data structures for Planwise.

This module provides functions and dataclasses for creating, saving, loading, and manipulating user
financial profiles, including personal details, account balances, contribution settings, and retirement projections.

Classes:
- QualifyingEarnings: Holds qualifying earnings info for pensions.
- PersonalDetails: Holds user personal and salary details.
- ContributionSettings: Holds contribution rates and amounts.
- AccountBalances: Holds balances for LISA, ISA, SIPP, and workplace pension.
- Post50ContributionSettings: Holds post-50 contribution redirection info.
- ExpectedReturnsAndInflation: Holds expected returns and inflation rates.
- PostRetirementSettings: Holds post-retirement withdrawal and return settings.
- ProfileSettings: Main profile container for all user settings.

Functions:
- safe_filename: Sanitizes profile names for filenames.
- profile_path: Gets the file path for a profile name.
- list_profiles: Lists all saved profiles.
- save_profile: Saves a profile to disk.
- load_profile: Loads a profile from disk.
- delete_profile: Deletes a profile from disk.
- serialise_profile_settings_to_json: Serializes a profile to JSON.
- deserialise_profile_settings_from_json: Deserializes a profile from JSON.
- get_qualifying_earnings_info: Gets qualifying earnings info for a tax year.
- get_personal_details: Calculates and returns personal details.
- get_workplace_contribution_rate: Calculates workplace contribution rate and amount.
- get_isa_contribution_rate: Calculates ISA contribution rate and amount.
- get_sipp_contribution_rate: Calculates SIPP contribution rate and amount.
- get_post_50_contribution_settings: Calculates post-50 contribution settings.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from .databases import LIMITS_DB
from .ni import calculate_ni
from .tax import calculate_income_tax

PROFILES_DIR = Path(".profiles")
PROFILES_DIR.mkdir(exist_ok=True)
SAFE_CHARS = re.compile(r"[^A-Za-z0-9 _.-]")


def safe_filename(name: str) -> str:
    """
    Sanitize a profile name to be safe for use as a filename.

    Args:
        name (str): Profile name.
    Returns:
        str: Sanitized filename string.
    """
    name = name.strip()
    name = SAFE_CHARS.sub("_", name)
    name = re.sub(r"\s+", " ", name)
    return name[:80]


def profile_path(name: str) -> Path:
    """
    Get the file path for a given profile name.

    Args:
        name (str): Profile name.
    Returns:
        Path: Path object for the profile file.
    """
    return PROFILES_DIR / f"{safe_filename(name)}.json"


def list_profiles() -> list[str]:
    """
    List all saved profile names.

    Returns:
        list[str]: List of profile names.
    """
    return sorted(p.stem for p in PROFILES_DIR.glob("*.json"))


def save_profile(name: str, profile_settings: "ProfileSettings") -> None:
    """
    Save a profile to disk as a JSON file.

    Args:
        name (str): Profile name.
        profile_settings (ProfileSettings): Profile settings to save.
    """
    file_path = profile_path(name)
    serialise_profile_settings_to_json(profile_settings, file_path)


def load_profile(name: str) -> Union["ProfileSettings", None]:
    """
    Load a profile from disk.

    Args:
        name (str): Profile name.
    Returns:
        ProfileSettings or None: Loaded profile settings or None if not found.
    """
    p = profile_path(name)
    return deserialise_profile_settings_from_json(p) if p.exists() else None


def delete_profile(name: str) -> None:
    """
    Delete a profile from disk.

    Args:
        name (str): Profile name.
    """
    p = profile_path(name)
    if p.exists():
        p.unlink()


def serialise_profile_settings_to_json(
    profile_settings: "ProfileSettings", file_path: Path
) -> None:
    """
    Serialize profile settings to a JSON file.

    Args:
        profile_settings (ProfileSettings): Profile settings to serialize.
        file_path (Path): Path to save the JSON file.
    """

    data = {
        "tax_year": profile_settings.tax_year,
        "scotland": profile_settings.scotland,
        "qualifying_earnings": profile_settings.qualifying_earnings.__dict__,
        "personal_details": profile_settings.personal_details.__dict__,
        "contribution_settings": profile_settings.contribution_settings.__dict__,
        "account_balances": profile_settings.account_balances.__dict__,
        "post_50_contribution_settings": profile_settings.post_50_contribution_settings.__dict__,
        "expected_returns_and_inflation": profile_settings.expected_returns_and_inflation.__dict__,
        "post_retirement_settings": profile_settings.post_retirement_settings.__dict__,
    }
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=2)


def deserialise_profile_settings_from_json(file_path: Path) -> "ProfileSettings":
    """
    Deserialize profile settings from a JSON file.

    Args:
        file_path (Path): Path to the JSON file.
    Returns:
        ProfileSettings: Deserialized profile settings.
    """

    with open(file_path, "r") as json_file:
        data = json.load(json_file)

    return ProfileSettings(
        tax_year=data["tax_year"],
        scotland=data["scotland"],
        qualifying_earnings=QualifyingEarnings(**data["qualifying_earnings"]),
        personal_details=PersonalDetails(**data["personal_details"]),
        contribution_settings=ContributionSettings(**data["contribution_settings"]),
        account_balances=AccountBalances(**data["account_balances"]),
        post_50_contribution_settings=Post50ContributionSettings(
            **data["post_50_contribution_settings"]
        ),
        expected_returns_and_inflation=ExpectedReturnsAndInflation(
            **data["expected_returns_and_inflation"]
        ),
        post_retirement_settings=PostRetirementSettings(
            **data["post_retirement_settings"]
        ),
    )


def get_qualifying_earnings_info(
    use_qualifying: bool, tax_year: int
) -> "QualifyingEarnings":
    """
    Get qualifying earnings information for a given tax year.

    Args:
        use_qualifying (bool): Whether to use qualifying earnings.
        tax_year (int): Tax year.
    Returns:
        QualifyingEarnings: Qualifying earnings info.
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
    """
    Data class to hold qualifying earnings information for pensions.

    Attributes:
        use_qualifying_earnings (bool): Whether qualifying earnings are used.
        qualifying_earnings (float): Amount of qualifying earnings.
        qualifying_upper (float): Upper threshold for qualifying earnings.
        qualifying_lower (float): Lower threshold for qualifying earnings.
    """

    use_qualifying_earnings: bool
    qualifying_earnings: float
    qualifying_upper: float
    qualifying_lower: float


def get_personal_details(
    current_age: int, retirement_age: int, salary: float, tax_year: int, scotland: bool
) -> "PersonalDetails":
    """
    Calculate and return personal details including salary, NI, and tax.

    Args:
        current_age (int): User's current age.
        retirement_age (int): Retirement age.
        salary (float): Gross annual salary.
        tax_year (int): Tax year.
        scotland (bool): Whether user is in Scotland.
    Returns:
        PersonalDetails: Personal details data class.
    """

    ni_contribution = calculate_ni(salary, year=tax_year, category="category_a")
    income_tax = calculate_income_tax(salary, year=tax_year, scotland=scotland)
    take_home_salary = salary - ni_contribution - income_tax
    return PersonalDetails(
        current_age=current_age,
        retirement_age=retirement_age,
        salary=salary,
        take_home_salary=take_home_salary,
        ni_contribution=ni_contribution,
        income_tax=income_tax,
    )


@dataclass
class PersonalDetails:
    """
    Data class to hold personal details inputs from the user.

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


def get_workplace_contribution_rate(
    workplace_contribution: float,
    personal_details: "PersonalDetails",
    qualifying_earnings: "QualifyingEarnings",
    use_exact_amount: bool = False,
) -> tuple[float, float]:
    """
    Calculate workplace pension contribution rate and amount.

    Args:
        workplace_contribution (float): Contribution rate or amount.
        personal_details (PersonalDetails): User's personal details.
        qualifying_earnings (QualifyingEarnings): Qualifying earnings info.
        use_exact_amount (bool): If True, use exact amount; else use rate.
    Returns:
        tuple[float, float]: (rate, contribution amount)
    """
    if not use_exact_amount:
        if qualifying_earnings.use_qualifying_earnings:
            potential_contribution_amount = (
                personal_details.salary - qualifying_earnings.qualifying_lower
                if personal_details.salary < qualifying_earnings.qualifying_upper
                else qualifying_earnings.qualifying_earnings
            )
            contribution = potential_contribution_amount * workplace_contribution
        else:
            contribution = personal_details.salary * workplace_contribution
        rate = workplace_contribution
    else:
        rate = (
            workplace_contribution / personal_details.salary
            if personal_details.salary > 0
            else 0.0
        )
        contribution = workplace_contribution

    return rate, contribution


def get_isa_contribution_rate(
    isa_contribution: float,
    personal_details: "PersonalDetails",
    use_exact_amount: bool = False,
) -> tuple[float, float]:
    """
    Calculate ISA contribution rate and amount.

    Args:
        isa_contribution (float): Contribution rate or amount.
        personal_details (PersonalDetails): User's personal details.
        use_exact_amount (bool): If True, use exact amount; else use rate.
    Returns:
        tuple[float, float]: (rate, contribution amount)
    """
    if not use_exact_amount:
        contribution = isa_contribution * personal_details.take_home_salary
        rate = isa_contribution
    else:
        rate = (
            isa_contribution / personal_details.take_home_salary
            if personal_details.take_home_salary > 0
            else 0.0
        )
        contribution = isa_contribution

    return rate, contribution


def get_sipp_contribution_rate(
    sipp_contribution: float,
    personal_details: "PersonalDetails",
    use_exact_amount: bool = False,
) -> tuple[float, float]:
    """
    Calculate SIPP contribution rate and amount.

    Args:
        sipp_contribution (float): Contribution rate or amount.
        personal_details (PersonalDetails): User's personal details.
        use_exact_amount (bool): If True, use exact amount; else use rate.
    Returns:
        tuple[float, float]: (rate, contribution amount)
    """
    if not use_exact_amount:
        contribution = sipp_contribution * personal_details.take_home_salary
        rate = sipp_contribution
    else:
        rate = (
            sipp_contribution / personal_details.take_home_salary
            if personal_details.take_home_salary > 0
            else 0.0
        )
        contribution = sipp_contribution

    return rate, contribution


def get_contribution_settings(
    qualifying_earnings: "QualifyingEarnings",
    personal_details: "PersonalDetails",
    use_exact_amount: bool,
    workplace_employer_contribution: float,
    workplace_employee_contribution: float,
    lisa_contribution: float,
    isa_contribution: float,
    sipp_contribution: float,
) -> "ContributionSettings":
    workplace_er_rate, workplace_er_contribution = get_workplace_contribution_rate(
        workplace_employer_contribution,
        personal_details,
        qualifying_earnings,
        use_exact_amount,
    )
    workplace_ee_rate, workplace_ee_contribution = get_workplace_contribution_rate(
        workplace_employee_contribution,
        personal_details,
        qualifying_earnings,
        use_exact_amount,
    )
    lisa_rate, lisa_contribution = get_isa_contribution_rate(
        lisa_contribution, personal_details, use_exact_amount
    )
    isa_rate, isa_contribution = get_isa_contribution_rate(
        isa_contribution, personal_details, use_exact_amount
    )
    sipp_rate, sipp_contribution = get_sipp_contribution_rate(
        sipp_contribution, personal_details, use_exact_amount
    )

    total_net_contribution = (
        workplace_ee_contribution
        + lisa_contribution
        + isa_contribution
        + sipp_contribution
    )
    total_sipp_contribution = sipp_contribution * 1.25
    total_workplace_contribution = (
        workplace_er_contribution + workplace_ee_contribution * 1.25
    )
    total_pension_contribution = total_workplace_contribution + total_sipp_contribution
    total_isa_contribution = lisa_contribution * 1.25 + isa_contribution
    contribution_settings = ContributionSettings(
        workplace_er_rate=workplace_er_rate,
        workplace_er_contribution=workplace_er_contribution,
        workplace_ee_rate=workplace_ee_rate,
        workplace_ee_contribution=workplace_ee_contribution,
        lisa_rate=lisa_rate,
        lisa_contribution=lisa_contribution,
        isa_rate=isa_rate,
        isa_contribution=isa_contribution,
        sipp_rate=sipp_rate,
        sipp_contribution=sipp_contribution,
        total_net_contribution=total_net_contribution,
        total_workplace_contribution=total_workplace_contribution,
        total_sipp_contribution=total_sipp_contribution,
        total_isa_contribution=total_isa_contribution,
        total_pension_contribution=total_pension_contribution,
    )

    return contribution_settings


@dataclass
class ContributionSettings:
    """
    Data class to hold contribution rates and amounts for all accounts.

    Attributes:
        workplace_er_rate (float): Employer rate.
        workplace_er_contribution (float): Employer contribution amount.
        workplace_ee_rate (float): Employee rate.
        workplace_ee_contribution (float): Employee contribution amount.
        lisa_rate (float): LISA rate.
        lisa_contribution (float): LISA contribution amount.
        isa_rate (float): ISA rate.
        isa_contribution (float): ISA contribution amount.
        sipp_rate (float): SIPP rate.
        sipp_contribution (float): SIPP contribution amount.
        total_workplace_contribution (float): Total workplace contribution.
        total_sipp_contribution (float): Total SIPP contribution.
        total_isa_contribution (float): Total ISA contribution.
        total_net_contribution (float): Total net contribution.
        total_pension_contribution (float): Total pension contribution.
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
    """
    Data class to hold account balances.

    Attributes:
        lisa_balance (float): The current balance in the Lifetime ISA (LISA).
        isa_balance (float): The current balance in the Individual Savings Account (ISA).
        sipp_balance (float): The current balance in the Self-Invested Personal Pension (SIPP).
        workplace_pension_balance (float): The current balance in the workplace pension.
    """

    lisa_balance: float
    isa_balance: float
    sipp_balance: float
    workplace_pension_balance: float


def get_post_50_contribution_settings(
    use_exact_amount_post50: bool,
    redirectable_to_isa_contribution: float,
    lisa_contribution: float,
) -> "Post50ContributionSettings":
    """
    Calculate post-50 contribution settings for LISA redirection.

    Args:
        use_exact_amount_post50 (bool): If True, use exact amount; else use rate.
        redirectable_to_isa_contribution (float): Amount or rate to redirect to ISA.
        lisa_contribution (float): LISA contribution amount.
    Returns:
        Post50ContributionSettings: Post-50 contribution settings data class.
    """
    if not use_exact_amount_post50:
        post_50_lisa_to_isa_rate = redirectable_to_isa_contribution
        post_50_lisa_to_isa_contribution = post_50_lisa_to_isa_rate * lisa_contribution
        post_50_lisa_to_sipp_rate = 1.0 - post_50_lisa_to_isa_rate
        post_50_lisa_to_sipp_contribution = (
            post_50_lisa_to_sipp_rate * lisa_contribution
        )
    else:
        post_50_lisa_to_isa_contribution = redirectable_to_isa_contribution
        post_50_lisa_to_isa_rate = (
            post_50_lisa_to_isa_contribution / lisa_contribution
            if lisa_contribution > 0
            else 0.0
        )
        post_50_lisa_to_sipp_contribution = (
            lisa_contribution - post_50_lisa_to_isa_contribution
        )
        post_50_lisa_to_sipp_rate = (
            post_50_lisa_to_sipp_contribution / lisa_contribution
            if lisa_contribution > 0
            else 0.0
        )
    return Post50ContributionSettings(
        post_50_lisa_to_isa_rate=post_50_lisa_to_isa_rate,
        post_50_lisa_to_isa_contribution=post_50_lisa_to_isa_contribution,
        post_50_lisa_to_sipp_rate=post_50_lisa_to_sipp_rate,
        post_50_lisa_to_sipp_contribution=post_50_lisa_to_sipp_contribution,
    )


@dataclass
class Post50ContributionSettings:
    """
    Data class to hold post-50 contribution settings.

    Attributes:
        post_50_lisa_to_isa_rate (float): Rate for LISA to ISA redirection after age 50.
        post_50_lisa_to_isa_contribution (float): Amount redirected from LISA to ISA.
        post_50_lisa_to_sipp_rate (float): Rate for LISA to SIPP redirection after age 50.
        post_50_lisa_to_sipp_contribution (float): Amount redirected from LISA to SIPP.
    """

    post_50_lisa_to_isa_rate: float
    post_50_lisa_to_isa_contribution: float
    post_50_lisa_to_sipp_rate: float
    post_50_lisa_to_sipp_contribution: float


@dataclass
class ExpectedReturnsAndInflation:
    """
    Data class to hold expected returns and inflation rates.

    Attributes:
        expected_lisa_annual_return (float): Expected annual return for LISA.
        expected_isa_annual_return (float): Expected annual return for ISA.
        expected_sipp_annual_return (float): Expected annual return for SIPP.
        expected_workplace_annual_return (float): Expected annual return for workplace pension.
        expected_inflation (float): Expected annual inflation rate.
    """

    expected_lisa_annual_return: float
    expected_isa_annual_return: float
    expected_sipp_annual_return: float
    expected_workplace_annual_return: float
    expected_inflation: float


@dataclass
class PostRetirementSettings:
    """
    Data class to hold post-retirement withdrawal and return settings.

    Attributes:
        withdrawal_today_amount (float): Annual withdrawal amount in today's money.
        expected_post_retirement_lisa_annual_return (float): Expected post-retirement LISA return.
        expected_post_retirement_isa_annual_return (float): Expected post-retirement ISA return.
        expected_post_retirement_pension_annual_return (float): Expected post-retirement pension return.
        postret_lisa_withdrawal_age (int): Age to start LISA withdrawals.
        postret_lisa_targeted_withdrawal_percentage (float): Targeted LISA withdrawal percentage.
        postret_isa_withdrawal_age (int): Age to start ISA withdrawals.
        postret_isa_targeted_withdrawal_percentage (float): Targeted ISA withdrawal percentage.
        postret_taxfree_pension_withdrawal_age (int): Age to start tax-free pension withdrawals.
        postret_taxfree_pension_targeted_withdrawal_percentage (float): Targeted tax-free pension withdrawal percentage.
        postret_taxable_pension_withdrawal_age (int): Age to start taxable pension withdrawals.
        postret_taxable_pension_targeted_withdrawal_percentage (float): Targeted taxable pension withdrawal percentage.
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
    """
    Main data class to hold all user profile settings for Planwise.

    Attributes:
        tax_year (int): Tax year for calculations.
        scotland (bool): Whether user is in Scotland.
        qualifying_earnings (QualifyingEarnings): Qualifying earnings info.
        personal_details (PersonalDetails): User's personal details.
        contribution_settings (ContributionSettings): Contribution settings.
        account_balances (AccountBalances): Account balances.
        post_50_contribution_settings (Post50ContributionSettings): Post-50 contribution settings.
        expected_returns_and_inflation (ExpectedReturnsAndInflation): Expected returns and inflation.
        post_retirement_settings (PostRetirementSettings): Post-retirement settings.
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
