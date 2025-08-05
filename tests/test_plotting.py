"""
Tests for plotting functionality in Planwise.

These tests cover the creation and structure of Altair charts for contributions and pot growth,
as well as integration with real projection data.
"""

import pandas as pd
import pytest

from planwise.plotting import (
    make_combined_plot,
    make_contribution_plot,
    make_growth_plot,
)


@pytest.fixture
def sample_projection_data():
    """
    Create sample projection data for testing plotting functions.
    Returns:
        pd.DataFrame: Sample projection data.
    """
    data = {
        "Age": [30, 31, 32],
        "Salary": [40000, 40800, 41616],
        "LISA Net": [2000, 2040, 2081],
        "LISA Bonus": [500, 510, 520],
        "ISA Net": [2000, 2040, 2081],
        "SIPP Employee Net": [2000, 2040, 2081],
        "SIPP Employee Gross": [2500, 2550, 2601],
        "SIPP Employer": [0, 0, 0],
        "Workplace Employee Net": [2000, 2040, 2081],
        "Workplace Employee Gross": [2500, 2550, 2601],
        "Workplace Employer": [1200, 1224, 1248],
        "Tax Relief (total)": [1000, 1020, 1040],
        "Tax Refund": [200, 204, 208],
        "Net Contribution Cost": [7800, 7956, 8115],
        "Pot LISA": [2500, 5125, 7856],
        "Pot ISA": [2000, 4100, 6302],
        "Pot SIPP": [2500, 5125, 7856],
        "Pot Workplace": [3700, 7585, 11680],
    }
    return pd.DataFrame(data)


class TestMakeContributionPlot:
    """
    Test the contribution plotting function.
    """

    def test_contribution_plot_creation(self, sample_projection_data):
        """
        Test that contribution plot is created successfully and is an Altair chart.
        """
        chart = make_contribution_plot(sample_projection_data)

        # Check it's an Altair chart
        assert hasattr(chart, "to_dict")

        # Check the chart configuration
        chart_dict = chart.to_dict()
        assert chart_dict["mark"]["type"] == "bar"
        assert "encoding" in chart_dict

    def test_contribution_plot_with_custom_title(self, sample_projection_data):
        """
        Test contribution plot with a custom title.
        """
        custom_title = "Custom Contribution Analysis"
        chart = make_contribution_plot(sample_projection_data, title=custom_title)

        chart_dict = chart.to_dict()
        assert chart_dict["title"] == custom_title

    def test_contribution_plot_data_structure(self, sample_projection_data):
        """
        Test that the plot uses the correct data structure and encodings.
        """
        chart = make_contribution_plot(sample_projection_data)
        chart_dict = chart.to_dict()

        # Check encoding uses the right fields
        assert "x" in chart_dict["encoding"]
        assert "y" in chart_dict["encoding"]
        assert "color" in chart_dict["encoding"]


class TestMakeGrowthPlot:
    """
    Test the growth plotting function.
    """

    def test_growth_plot_creation(self, sample_projection_data):
        """
        Test that growth plot is created successfully and is an Altair chart.
        """
        chart = make_growth_plot(sample_projection_data)

        # Check it's an Altair chart
        assert hasattr(chart, "to_dict")

        # Check the chart configuration
        chart_dict = chart.to_dict()
        assert chart_dict["mark"]["type"] == "line"
        assert "encoding" in chart_dict

    def test_growth_plot_with_custom_title(self, sample_projection_data):
        """
        Test growth plot with a custom title.
        """
        custom_title = "Custom Growth Analysis"
        chart = make_growth_plot(sample_projection_data, title=custom_title)

        chart_dict = chart.to_dict()
        assert chart_dict["title"] == custom_title

    def test_growth_plot_data_structure(self, sample_projection_data):
        """
        Test that the plot uses the correct data structure and encodings.
        """
        chart = make_growth_plot(sample_projection_data)
        chart_dict = chart.to_dict()

        # Check encoding uses the right fields
        assert "x" in chart_dict["encoding"]
        assert "y" in chart_dict["encoding"]
        assert "color" in chart_dict["encoding"]


class TestMakeCombinedPlot:
    """
    Test the combined plotting function.
    """

    def test_combined_plot_creation(self, sample_projection_data):
        """
        Test that combined plot is created successfully and is an Altair chart.
        """
        chart = make_combined_plot(sample_projection_data)

        # Check it's an Altair chart
        assert hasattr(chart, "to_dict")

        # Should be a horizontal concatenation
        chart_dict = chart.to_dict()
        assert "hconcat" in chart_dict


@pytest.mark.integration
class TestPlottingIntegration:
    """
    Integration tests for plotting with real projection data.
    """

    def test_plotting_with_real_projection(self):
        """
        Test plotting functions work with real projection data from the core module.
        """
        # This would require importing core module
        # Skip if altair not available
        try:
            import altair as alt
        except ImportError:
            pytest.skip("Altair not available")

        from planwise.core import (
            ContributionRates,
            InvestmentReturns,
            UserProfile,
            project_retirement,
        )

        # Run a small projection using the new dataclass-based interface
        user = UserProfile(
            current_age=30,
            retirement_age=33,
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

        # Test all plotting functions work
        contrib_chart = make_contribution_plot(result)
        growth_chart = make_growth_plot(result)
        combined_chart = make_combined_plot(result)

        # All should be valid Altair charts
        for chart in [contrib_chart, growth_chart, combined_chart]:
            assert hasattr(chart, "to_dict")
            chart_dict = chart.to_dict()
            assert isinstance(chart_dict, dict)
