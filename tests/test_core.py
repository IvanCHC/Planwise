from unittest.mock import MagicMock

import pandas as pd
import pytest

from planwise.core import (
    InvestmentSimulator,
    RetirementSimulator,
    project_investment,
    project_retirement,
)


@pytest.fixture
def mock_profile():
    profile = MagicMock()
    profile.tax_year = 2025
    profile.scotland = False
    profile.personal_details.current_age = 30
    profile.personal_details.retirement_age = 65
    profile.personal_details.salary = 50000
    profile.personal_details.take_home_salary = 35000
    profile.personal_details.income_tax = 5000
    profile.personal_details.ni_contribution = 3000
    profile.account_balances.lisa_balance = 10000
    profile.account_balances.isa_balance = 5000
    profile.account_balances.sipp_balance = 20000
    profile.account_balances.workplace_pension_balance = 15000
    profile.contribution_settings.lisa_contribution = 4000
    profile.contribution_settings.isa_contribution = 2000
    profile.contribution_settings.workplace_er_contribution = 1000
    profile.contribution_settings.workplace_ee_contribution = 2000
    profile.contribution_settings.sipp_contribution = 3000
    profile.post_50_contribution_settings.post_50_lisa_to_isa_contribution = 1000
    profile.post_50_contribution_settings.post_50_lisa_to_sipp_contribution = 500
    profile.expected_returns_and_inflation.expected_lisa_annual_return = 0.05
    profile.expected_returns_and_inflation.expected_isa_annual_return = 0.04
    profile.expected_returns_and_inflation.expected_workplace_annual_return = 0.03
    profile.expected_returns_and_inflation.expected_sipp_annual_return = 0.06
    profile.expected_returns_and_inflation.expected_inflation = 0.02
    profile.post_retirement_settings.withdrawal_today_amount = 25000
    profile.post_retirement_settings.postret_isa_targeted_withdrawal_percentage = 0.25
    profile.post_retirement_settings.postret_lisa_targeted_withdrawal_percentage = 0.25
    profile.post_retirement_settings.postret_taxfree_pension_targeted_withdrawal_percentage = (
        0.25
    )
    profile.post_retirement_settings.postret_taxable_pension_targeted_withdrawal_percentage = (
        0.25
    )
    profile.post_retirement_settings.postret_lisa_withdrawal_age = 65
    profile.post_retirement_settings.postret_isa_withdrawal_age = 65
    profile.post_retirement_settings.postret_taxfree_pension_withdrawal_age = 65
    profile.post_retirement_settings.postret_taxable_pension_withdrawal_age = 65
    profile.post_retirement_settings.expected_post_retirement_lisa_annual_return = 0.03
    profile.post_retirement_settings.expected_post_retirement_isa_annual_return = 0.03
    profile.post_retirement_settings.expected_post_retirement_pension_annual_return = (
        0.03
    )
    return profile


def test_investment_simulator_simulate_returns_dataframe(mock_profile):
    sim = InvestmentSimulator(mock_profile)
    df = sim.simulate()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "Age" in df.columns
    assert "LISA Balance" in df.columns
    assert "ISA Balance" in df.columns
    assert "SIPP Balance" in df.columns
    assert "Workplace Balance" in df.columns


def test_project_investment_returns_dataframe(mock_profile):
    df = project_investment(mock_profile)
    assert isinstance(df, pd.DataFrame)
    assert "Portfolio Balance" in df.columns


def test_retirement_simulator_simulate_returns_dataframe(mock_profile):
    invest_df = project_investment(mock_profile)
    sim = RetirementSimulator(mock_profile, invest_df)
    df = sim.simulate()
    assert isinstance(df, pd.DataFrame)
    assert "Age" in df.columns
    assert "Withdrawal Today" in df.columns
    assert "Total Withdrawal Today" in df.columns


def test_project_retirement_returns_dataframe(mock_profile):
    invest_df = project_investment(mock_profile)
    df = project_retirement(mock_profile, invest_df)
    assert isinstance(df, pd.DataFrame)
    assert "Total Balance Today" in df.columns


def test_lisa_contribution_under_50(mock_profile):
    sim = InvestmentSimulator(mock_profile)
    result = sim._calculate_lisa_contribution(age=40)
    assert result["LISA Net"] == mock_profile.contribution_settings.lisa_contribution
    assert (
        result["LISA Bonus"]
        == mock_profile.contribution_settings.lisa_contribution * 0.25
    )


def test_lisa_contribution_over_50(mock_profile):
    sim = InvestmentSimulator(mock_profile)
    result = sim._calculate_lisa_contribution(age=55)
    assert result["LISA Net"] == 0.0
    assert result["LISA Bonus"] == 0.0


def test_isa_contribution_post_50(mock_profile):
    sim = InvestmentSimulator(mock_profile)
    result = sim._calculate_isa_contribution(age=55)
    expected = (
        mock_profile.contribution_settings.isa_contribution
        + mock_profile.post_50_contribution_settings.post_50_lisa_to_isa_contribution
    )
    assert result["ISA Net"] == expected
    assert result["ISA Gross"] == expected


def test_sipp_contribution_post_50(mock_profile):
    sim = InvestmentSimulator(mock_profile)
    result = sim._calculate_sipp_contribution(age=55)
    expected = (
        mock_profile.contribution_settings.sipp_contribution
        + mock_profile.post_50_contribution_settings.post_50_lisa_to_sipp_contribution
    )
    assert result["SIPP Net"] == expected
    assert result["SIPP Gross"] == expected * 1.25 / 1.0  # 25% tax relief


def test_inflation_adjustment(mock_profile):
    sim = RetirementSimulator(mock_profile, project_investment(mock_profile))
    adj = sim._inflation_adjustment(35)
    assert adj == pytest.approx(
        (1 + mock_profile.expected_returns_and_inflation.expected_inflation) ** 5
    )
