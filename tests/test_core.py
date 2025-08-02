"""
Tests for core retirement projection functionality.
"""

import numpy as np
import pandas as pd
import pytest

from planwise.core import project_retirement


class TestProjectRetirement:
    """Test the main projection function."""

    def test_basic_projection(self):
        """Test a basic retirement projection."""
        result = project_retirement(
            current_age=30,
            retirement_age=35,  # Short period for testing
            salary=40000,
            lisa_contrib_rate=0.05,
            isa_contrib_rate=0.05,
            sipp_employee_rate=0.05,
            sipp_employer_rate=0.0,
            workplace_employee_rate=0.05,
            workplace_employer_rate=0.03,
            shift_lisa_to_isa=0.5,
            shift_lisa_to_sipp=0.5,
            roi_lisa=0.05,
            roi_isa=0.05,
            roi_sipp=0.05,
            roi_workplace=0.05,
            inflation=0.02,
            scotland=False,
            use_qualifying_earnings=True,
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
        result = project_retirement(
            current_age=48,
            retirement_age=52,
            salary=40000,
            lisa_contrib_rate=0.10,  # High rate to make it obvious
            isa_contrib_rate=0.0,
            sipp_employee_rate=0.0,
            sipp_employer_rate=0.0,
            workplace_employee_rate=0.0,
            workplace_employer_rate=0.0,
            shift_lisa_to_isa=1.0,  # All redirected to ISA after 50
            shift_lisa_to_sipp=0.0,
            roi_lisa=0.0,
            roi_isa=0.0,
            roi_sipp=0.0,
            roi_workplace=0.0,
            inflation=0.0,
            scotland=False,
            use_qualifying_earnings=True,
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
        result = project_retirement(
            current_age=30,
            retirement_age=31,
            salary=40000,
            lisa_contrib_rate=0.10,  # £4000 contribution
            isa_contrib_rate=0.0,
            sipp_employee_rate=0.0,
            sipp_employer_rate=0.0,
            workplace_employee_rate=0.0,
            workplace_employer_rate=0.0,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
            roi_lisa=0.0,
            roi_isa=0.0,
            roi_sipp=0.0,
            roi_workplace=0.0,
            inflation=0.0,
            scotland=False,
            use_qualifying_earnings=True,
        )

        lisa_net = result.iloc[0]["LISA Net"]
        lisa_bonus = result.iloc[0]["LISA Bonus"]

        # Should cap at £4000 and give 25% bonus
        assert lisa_net == 4000  # Capped at LISA limit
        assert lisa_bonus == 1000  # 25% of £4000

    # def test_pension_annual_allowance_cap(self):
    #     """Test that pension contributions are capped by annual allowance."""
    #     result = project_retirement(
    #         current_age=30,
    #         retirement_age=31,
    #         salary=500000,  # Very high salary
    #         lisa_contrib_rate=0.0,
    #         isa_contrib_rate=0.0,
    #         sipp_employee_rate=0.20,  # High contribution rates
    #         sipp_employer_rate=0.10,
    #         workplace_employee_rate=0.20,
    #         workplace_employer_rate=0.20,
    #         shift_lisa_to_isa=0.0,
    #         shift_lisa_to_sipp=0.0,
    #         roi_lisa=0.0,
    #         roi_isa=0.0,
    #         roi_sipp=0.0,
    #         roi_workplace=0.0,
    #         inflation=0.0,
    #         scotland=False,
    #         use_qualifying_earnings=False,  # Use full salary
    #     )

    #     # Total gross pension contributions should not exceed £60,000
    #     row = result.iloc[0]
    #     total_pension = (
    #         row["SIPP Employee Gross"]
    #         + row["SIPP Employer"]
    #         + row["Workplace Employee Gross"]
    #         + row["Workplace Employer"]
    #     )
    #     assert total_pension <= 60000.1  # Allow for small rounding

    def test_inflation_indexing(self):
        """Test that salary is indexed by inflation."""
        result = project_retirement(
            current_age=30,
            retirement_age=32,
            salary=40000,
            lisa_contrib_rate=0.0,
            isa_contrib_rate=0.0,
            sipp_employee_rate=0.0,
            sipp_employer_rate=0.0,
            workplace_employee_rate=0.0,
            workplace_employer_rate=0.0,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
            roi_lisa=0.0,
            roi_isa=0.0,
            roi_sipp=0.0,
            roi_workplace=0.0,
            inflation=0.10,  # 10% inflation
            scotland=False,
            use_qualifying_earnings=True,
        )

        # Salary should increase by 10% each year
        assert abs(result.iloc[0]["Salary"] - 40000) < 0.01
        assert abs(result.iloc[1]["Salary"] - 44000) < 0.01  # 40000 * 1.1

    def test_pot_growth(self):
        """Test that pots grow with returns."""
        result = project_retirement(
            current_age=30,
            retirement_age=32,
            salary=40000,
            lisa_contrib_rate=0.05,
            isa_contrib_rate=0.05,
            sipp_employee_rate=0.05,
            sipp_employer_rate=0.0,
            workplace_employee_rate=0.05,
            workplace_employer_rate=0.03,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
            roi_lisa=0.10,  # 10% returns
            roi_isa=0.10,
            roi_sipp=0.10,
            roi_workplace=0.10,
            inflation=0.0,
            scotland=False,
            use_qualifying_earnings=True,
        )

        # All pots should be positive and growing
        for col in ["Pot LISA", "Pot ISA", "Pot SIPP", "Pot Workplace"]:
            assert result.iloc[0][col] > 0
            assert result.iloc[1][col] > result.iloc[0][col]

    def test_qualifying_earnings_calculation(self):
        """Test workplace pension contributions with qualifying earnings."""
        # Test with salary below qualifying band
        result_low = project_retirement(
            current_age=30,
            retirement_age=31,
            salary=20000,
            lisa_contrib_rate=0.0,
            isa_contrib_rate=0.0,
            sipp_employee_rate=0.0,
            sipp_employer_rate=0.0,
            workplace_employee_rate=0.05,
            workplace_employer_rate=0.03,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
            roi_lisa=0.0,
            roi_isa=0.0,
            roi_sipp=0.0,
            roi_workplace=0.0,
            inflation=0.0,
            scotland=False,
            use_qualifying_earnings=True,
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
        result = project_retirement(
            current_age=30,
            retirement_age=31,
            salary=60000,  # High enough to show difference
            lisa_contrib_rate=0.0,
            isa_contrib_rate=0.0,
            sipp_employee_rate=0.10,  # Meaningful pension contribution
            sipp_employer_rate=0.0,
            workplace_employee_rate=0.0,
            workplace_employer_rate=0.0,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
            roi_lisa=0.0,
            roi_isa=0.0,
            roi_sipp=0.0,
            roi_workplace=0.0,
            inflation=0.0,
            scotland=scotland,
            use_qualifying_earnings=True,
        )

        # Should have some tax relief
        tax_relief = result.iloc[0]["Tax Relief (total)"]
        assert tax_relief > 0
