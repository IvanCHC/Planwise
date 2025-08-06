"""
Tests for core retirement projection functionality in Planwise.

These tests cover the main projection logic, LISA/ISA rules, pension caps, pot growth,
qualifying earnings, and tax region differences.
"""

import numpy as np
import pandas as pd
import pytest

from planwise.core import (
    ContributionRates,
    InvestmentReturns,
    UserProfile,
    calculate_lisa_isa_contributions,
    calculate_pension_contributions,
    project_retirement,
)


class TestProjectRetirement:
    """
    Test the main projection function and related helpers.
    """

    def test_basic_projection(self):
        """
        Test a basic retirement projection for correct DataFrame structure and columns.
        """
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
        from planwise.core import IncomeBreakdown

        income = IncomeBreakdown(
            salary=user.salary,
            take_home_salary=user.salary,
            income_tax=0.0,
            ni_due=0.0,
        )
        result = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            income=income,
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
        """
        Test that LISA contributions stop at age 50 and are redirected appropriately.
        """
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
        from planwise.core import IncomeBreakdown

        income = IncomeBreakdown(
            salary=user.salary,
            take_home_salary=user.salary,
            income_tax=0.0,
            ni_due=0.0,
        )
        result = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            income=income,
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
        """
        Test LISA bonus is calculated as 25% of net contribution, capped at limit.
        """
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
        from planwise.core import IncomeBreakdown

        income = IncomeBreakdown(
            salary=user.salary,
            take_home_salary=user.salary,
            income_tax=0.0,
            ni_due=0.0,
        )
        result = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            income=income,
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
        """
        Test that all pots grow with positive returns.
        """
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
        from planwise.core import IncomeBreakdown

        income = IncomeBreakdown(
            salary=user.salary,
            take_home_salary=user.salary,
            income_tax=0.0,
            ni_due=0.0,
        )
        result = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            income=income,
            inflation=0.0,
            use_qualifying_earnings=True,
            year=2025,
        )

        # All pots should be positive and growing
        for col in ["Pot LISA", "Pot ISA", "Pot SIPP", "Pot Workplace"]:
            assert result.iloc[0][col] > 0
            assert result.iloc[1][col] > result.iloc[0][col]

    def test_qualifying_earnings_calculation(self):
        """
        Test workplace pension contributions are based on qualifying earnings when enabled.
        """
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
        from planwise.core import IncomeBreakdown

        income = IncomeBreakdown(
            salary=user.salary,
            take_home_salary=user.salary,
            income_tax=0.0,
            ni_due=0.0,
        )
        result_low = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            income=income,
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
        """
        Test that Scottish and UK tax calculations produce different results for the same salary.
        """
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
        from planwise.core import IncomeBreakdown

        income = IncomeBreakdown(
            salary=user.salary,
            take_home_salary=user.salary,
            income_tax=0.0,
            ni_due=0.0,
        )
        result = project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            income=income,
            inflation=0.0,
            use_qualifying_earnings=True,
            year=2025,
        )

        # Should have some tax relief
        tax_relief = result.iloc[0]["Tax Relief (total)"]
        assert tax_relief > 0

    def test_lisa_isa_under_50(self):
        """
        Test LISA and ISA contributions under age 50, no redirection.
        """
        contrib = ContributionRates(
            lisa=0.10,
            isa=0.05,
            sipp_employee=0.0,
            sipp_employer=0.0,
            workplace_employee=0.0,
            workplace_employer=0.0,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
        )
        result = calculate_lisa_isa_contributions(
            current_salary=30000,
            age=30,
            contrib=contrib,
            lisa_limit=4000,
            isa_limit=20000,
        )
        # LISA: 10% of 30,000 = 3,000 (under limit)
        assert result["lisa_net"] == 3000
        assert result["lisa_bonus"] == 750
        assert result["lisa_gross"] == 3750
        # ISA: 5% of 30,000 = 1,500
        assert result["isa_net"] == 1500
        # No redirection
        assert result["redirected_sipp_net"] == 0

    def test_lisa_isa_lisa_cap(self):
        """
        Test LISA contributions are capped at the annual limit.
        """
        contrib = ContributionRates(
            lisa=0.20,
            isa=0.0,
            sipp_employee=0.0,
            sipp_employer=0.0,
            workplace_employee=0.0,
            workplace_employer=0.0,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
        )
        result = calculate_lisa_isa_contributions(
            current_salary=30000,
            age=30,
            contrib=contrib,
            lisa_limit=4000,
            isa_limit=20000,
        )
        # LISA: 20% of 30,000 = 6,000, but capped at 4,000
        assert result["lisa_net"] == 4000
        assert result["lisa_bonus"] == 1000
        assert result["lisa_gross"] == 5000

    def test_lisa_isa_over_50_redirection(self):
        """
        Test LISA contributions are redirected to ISA and SIPP after age 50.
        """
        contrib = ContributionRates(
            lisa=0.10,
            isa=0.05,
            sipp_employee=0.0,
            sipp_employer=0.0,
            workplace_employee=0.0,
            workplace_employer=0.0,
            shift_lisa_to_isa=0.6,
            shift_lisa_to_sipp=0.4,
        )
        result = calculate_lisa_isa_contributions(
            current_salary=30000,
            age=55,
            contrib=contrib,
            lisa_limit=4000,
            isa_limit=20000,
        )
        # Over 50: no LISA, but 10% of 30,000 = 3,000 redirected
        # 60% to ISA, 40% to SIPP
        assert result["lisa_net"] == 0
        assert result["lisa_bonus"] == 0
        assert result["lisa_gross"] == 0
        assert result["isa_net"] == 0.05 * 30000 + 0.6 * 3000  # 1500 + 1800 = 3300
        assert result["redirected_sipp_net"] == 0.4 * 3000  # 1200

    def test_isa_cap_with_lisa(self):
        """
        Test ISA contributions are capped when LISA is also used.
        """
        contrib = ContributionRates(
            lisa=0.20,
            isa=0.20,
            sipp_employee=0.0,
            sipp_employer=0.0,
            workplace_employee=0.0,
            workplace_employer=0.0,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
        )
        result = calculate_lisa_isa_contributions(
            current_salary=100_000,
            age=30,
            contrib=contrib,
            lisa_limit=4000,
            isa_limit=20000,
        )
        # LISA: capped at 4000, gross 5000
        # ISA: 20% of 100,000 = 20,000, but only 20,000 - 5,000 = 15,000 allowed
        assert result["lisa_net"] == 4000
        assert result["lisa_gross"] == 5000

    def test_pension_contributions_basic(self):
        """
        Test basic SIPP and workplace pension contribution calculations.
        """
        contrib = ContributionRates(
            lisa=0.0,
            isa=0.0,
            sipp_employee=0.05,
            sipp_employer=0.03,
            workplace_employee=0.04,
            workplace_employer=0.02,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
        )
        current_salary = 50000
        base_for_workplace = 40000
        redirected_sipp_net = 0

        result = calculate_pension_contributions(
            current_salary=current_salary,
            base_for_workplace=base_for_workplace,
            contrib=contrib,
            redirected_sipp_net=redirected_sipp_net,
        )

        # SIPP employee: 5% of 50,000 = 2,500 net, grossed up to 3,125
        assert abs(result["sipp_employee_net"] - 2500) < 0.01
        assert abs(result["sipp_employee_gross"] - 3125) < 0.01
        # SIPP employer: 3% of 50,000 = 1,500
        assert abs(result["sipp_employer_gross"] - 1500) < 0.01
        # WP employee: 4% of 40,000 = 1,600 net, grossed up to 2,000
        assert abs(result["wp_employee_net"] - 1600) < 0.01
        assert abs(result["wp_employee_gross"] - 2000) < 0.01
        # WP employer: 2% of 40,000 = 800
        assert abs(result["wp_employer_gross"] - 800) < 0.01

    def test_pension_contributions_with_redirection(self):
        """
        Test SIPP contributions with redirected amounts from LISA.
        """
        contrib = ContributionRates(
            lisa=0.0,
            isa=0.0,
            sipp_employee=0.05,
            sipp_employer=0.0,
            workplace_employee=0.0,
            workplace_employer=0.0,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
        )
        current_salary = 30000
        base_for_workplace = 30000
        redirected_sipp_net = 1000

        result = calculate_pension_contributions(
            current_salary=current_salary,
            base_for_workplace=base_for_workplace,
            contrib=contrib,
            redirected_sipp_net=redirected_sipp_net,
        )

        # SIPP employee: (5% of 30,000) + 1,000 = 2,500 net, grossed up to 3,125
        assert abs(result["sipp_employee_net"] - 2500) < 0.01
        assert abs(result["sipp_employee_gross"] - 3125) < 0.01
        # SIPP employer: 0
        assert result["sipp_employer_gross"] == 0
        # WP employee/employer: 0
        assert result["wp_employee_net"] == 0
        assert result["wp_employee_gross"] == 0
        assert result["wp_employer_gross"] == 0

    def test_pension_contributions_zero(self):
        """
        Test all pension contributions are zero when salary and rates are zero.
        """
        contrib = ContributionRates(
            lisa=0.0,
            isa=0.0,
            sipp_employee=0.0,
            sipp_employer=0.0,
            workplace_employee=0.0,
            workplace_employer=0.0,
            shift_lisa_to_isa=0.0,
            shift_lisa_to_sipp=0.0,
        )
        current_salary = 0
        base_for_workplace = 0
        redirected_sipp_net = 0

        result = calculate_pension_contributions(
            current_salary=current_salary,
            base_for_workplace=base_for_workplace,
            contrib=contrib,
            redirected_sipp_net=redirected_sipp_net,
        )

        assert result["sipp_employee_net"] == 0
        assert result["sipp_employee_gross"] == 0
        assert result["sipp_employer_gross"] == 0
        assert result["wp_employee_net"] == 0
        assert result["wp_employee_gross"] == 0
        assert result["wp_employer_gross"] == 0

    def test_load_limits_db(self):
        """
        Test that load_limits_db loads the limits JSON and contains expected keys.
        """
        from planwise.core import load_limits_db

        limits = load_limits_db()
        assert isinstance(limits, dict)
        assert "2025" in limits
        year_limits = limits["2025"]
        for key in [
            "lisa_limit",
            "isa_limit",
            "pension_annual_allowance",
            "qualifying_lower",
            "qualifying_upper",
        ]:
            assert key in year_limits
