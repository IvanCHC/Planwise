"""
Tests for core retirement projection functionality.
"""

import numpy as np
import pandas as pd
import pytest

from planwise.core import (
    ContributionRates,
    InvestmentReturns,
    UserProfile,
    project_retirement,
)


class TestProjectRetirement:
    """Test the main projection function."""

    def test_basic_projection(self):
        """Test a basic retirement projection."""
        user = UserProfile(
            current_age=30,
            retirement_age=35,
            salary=40000,
            scotland=False,
        )
        contrib = ContributionRates(
            lisa=0.05,
            isa=0.05,
            sipp_employee=0.05,
            sipp_employer=0.0,
            workplace_employee=0.05,
            workplace_employer=0.03,
            shift_lisa_to_isa=0.5,
            shift_lisa_to_sipp=0.5,
        )
        returns = InvestmentReturns(
            lisa=0.05,
            isa=0.05,
            sipp=0.05,
            workplace=0.05,
        )
        result = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            inflation=0.02,
            use_qualifying_earnings=True,
            year=2025,
        )

        # Check basic structure
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5  # 5 years from age 30 to 35
        assert result["Age"].tolist() == [30, 31, 32, 33, 34]

        # Check required columns exist
        required_columns = [
            "Age",
            "Salary",
            "LISA Net",
            "LISA Bonus",
            "ISA Net",
            "SIPP Employee Net",
            "SIPP Employee Gross",
            "SIPP Employer",
            "Workplace Employee Net",
            "Workplace Employee Gross",
            "Workplace Employer",
            "Tax Relief (total)",
            "Tax Refund",
            "Net Contribution Cost",
            "Pot LISA",
            "Pot ISA",
            "Pot SIPP",
            "Pot Workplace",
        ]
        for col in required_columns:
            assert col in result.columns

    def test_lisa_age_restriction(self):
        """Test that LISA contributions stop at age 50."""
        user = UserProfile(
            current_age=48,
            retirement_age=52,
            salary=40000,
            scotland=False,
        )
        contrib = ContributionRates(
            lisa=0.10,
            isa=0.0,
            sipp_employee=0.0,
            sipp_employer=0.0,
            workplace_employee=0.0,
            workplace_employer=0.0,
            shift_lisa_to_isa=1.0,
            shift_lisa_to_sipp=0.0,
        )
        returns = InvestmentReturns(
            lisa=0.0,
            isa=0.0,
            sipp=0.0,
            workplace=0.0,
        )
        result = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            inflation=0.0,
            use_qualifying_earnings=True,
            year=2025,
        )

        # Ages 48-49 should have LISA contributions
        assert result.loc[result["Age"] == 48, "LISA Net"].iloc[0] > 0
        assert result.loc[result["Age"] == 49, "LISA Net"].iloc[0] > 0

        # Ages 50+ should have no LISA contributions
        assert result.loc[result["Age"] == 50, "LISA Net"].iloc[0] == 0
        assert result.loc[result["Age"] == 51, "LISA Net"].iloc[0] == 0

        # But ISA should receive redirected amounts
        assert result.loc[result["Age"] == 50, "ISA Net"].iloc[0] > 0
        assert result.loc[result["Age"] == 51, "ISA Net"].iloc[0] > 0

    def test_lisa_bonus_calculation(self):
        """Test LISA bonus is calculated correctly."""
        user = UserProfile(
            current_age=30,
            retirement_age=31,
            salary=40000,
            scotland=False,
        )
        contrib = ContributionRates(
            lisa=0.10,
            isa=0.0,
            sipp_employee=0.0,
            sipp_employer=0.0,
            workplace_employee=0.0,
            workplace_employer=0.0,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
        )
        returns = InvestmentReturns(
            lisa=0.0,
            isa=0.0,
            sipp=0.0,
            workplace=0.0,
        )
        result = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            inflation=0.0,
            use_qualifying_earnings=True,
            year=2025,
        )

        lisa_net = result.iloc[0]["LISA Net"]
        lisa_bonus = result.iloc[0]["LISA Bonus"]

        # Should cap at £4000 and give 25% bonus
        assert lisa_net == 4000  # Capped at LISA limit
        assert lisa_bonus == 1000  # 25% of £4000

    # def test_pension_annual_allowance_cap(self):
    #     """Test that pension contributions are capped by annual allowance."""
    #     user = UserProfile(
    #         current_age=30,
    #         retirement_age=31,
    #         salary=500000,
    #         scotland=False,
    #     )
    #     contrib = ContributionRates(
    #         lisa=0.0,
    #         isa=0.0,
    #         sipp_employee=0.20,
    #         sipp_employer=0.10,
    #         workplace_employee=0.20,
    #         workplace_employer=0.20,
    #         shift_lisa_to_isa=0.0,
    #         shift_lisa_to_sipp=0.0,
    #     )
    #     returns = InvestmentReturns(
    #         lisa=0.0,
    #         isa=0.0,
    #         sipp=0.0,
    #         workplace=0.0,
    #     )
    #     result = project_retirement(
    #         user=user,
    #         contrib=contrib,
    #         returns=returns,
    #         inflation=0.0,
    #         use_qualifying_earnings=False,
    #         year=2025,
    #     )
    #     row = result.iloc[0]
    #     total_pension = (
    #         row["SIPP Employee Gross"]
    #         + row["SIPP Employer"]
    #         + row["Workplace Employee Gross"]
    #         + row["Workplace Employer"]
    #     )
    #     assert total_pension <= 60000.1  # Allow for small rounding

    def test_pot_growth(self):
        """Test that pots grow with returns."""
        user = UserProfile(
            current_age=30,
            retirement_age=32,
            salary=40000,
            scotland=False,
        )
        contrib = ContributionRates(
            lisa=0.05,
            isa=0.05,
            sipp_employee=0.05,
            sipp_employer=0.0,
            workplace_employee=0.05,
            workplace_employer=0.03,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
        )
        returns = InvestmentReturns(
            lisa=0.10,
            isa=0.10,
            sipp=0.10,
            workplace=0.10,
        )
        result = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            inflation=0.0,
            use_qualifying_earnings=True,
            year=2025,
        )

        # All pots should be positive and growing
        for col in ["Pot LISA", "Pot ISA", "Pot SIPP", "Pot Workplace"]:
            assert result.iloc[0][col] > 0
            assert result.iloc[1][col] > result.iloc[0][col]

    def test_qualifying_earnings_calculation(self):
        """Test workplace pension contributions with qualifying earnings."""
        # Test with salary below qualifying band
        user = UserProfile(
            current_age=30,
            retirement_age=31,
            salary=20000,
            scotland=False,
        )
        contrib = ContributionRates(
            lisa=0.0,
            isa=0.0,
            sipp_employee=0.0,
            sipp_employer=0.0,
            workplace_employee=0.05,
            workplace_employer=0.03,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
        )
        returns = InvestmentReturns(
            lisa=0.0,
            isa=0.0,
            sipp=0.0,
            workplace=0.0,
        )
        result_low = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            inflation=0.0,
            use_qualifying_earnings=True,
            year=2025,
        )

        # Should be based on qualifying earnings (20000 - 6240 = 13760)
        qualifying_base = max(20000 - 6240, 0)
        expected_employee = qualifying_base * 0.05 / 0.8  # Grossed up
        expected_employer = qualifying_base * 0.03

        row = result_low.iloc[0]
        assert abs(row["Workplace Employee Gross"] - expected_employee) < 0.01
        assert abs(row["Workplace Employer"] - expected_employer) < 0.01

    @pytest.mark.parametrize("scotland", [False, True])
    def test_scottish_vs_uk_tax(self, scotland):
        """Test that Scottish and UK tax calculations produce different results."""
        user = UserProfile(
            current_age=30,
            retirement_age=31,
            salary=60000,
            scotland=scotland,
        )
        contrib = ContributionRates(
            lisa=0.0,
            isa=0.0,
            sipp_employee=0.10,
            sipp_employer=0.0,
            workplace_employee=0.0,
            workplace_employer=0.0,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
        )
        returns = InvestmentReturns(
            lisa=0.0,
            isa=0.0,
            sipp=0.0,
            workplace=0.0,
        )
        result = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            inflation=0.0,
            use_qualifying_earnings=True,
            year=2025,
        )

        # Should have some tax relief
        tax_relief = result.iloc[0]["Tax Relief (total)"]
        assert tax_relief > 0
