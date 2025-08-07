"""
Plotting functions for visualizing retirement projections in Planwise.

This module provides functions to create Altair charts for contribution analysis
and growth projections, including combined visualizations.
"""

from typing import Optional

import altair as alt
import pandas as pd
import plotly
import plotly.express as px

from .core import IncomeBreakdown


def make_contribution_plot(df: pd.DataFrame, title: Optional[str] = None) -> alt.Chart:
    """
    Create a stacked bar chart showing net contributions to each wrapper per year.

    Args:
        df (pd.DataFrame): DataFrame containing projection results from project_retirement.
        title (str, optional): Custom title for the chart. If None, uses default title.
    Returns:
        alt.Chart: Altair chart object showing contribution breakdown.
    """
    if title is None:
        title = "Net contributions by account (share of total)"

    # Melt the DataFrame to long format for Altair
    plot_df = df.melt(
        id_vars=["Age"],
        value_vars=[
            "LISA Net",
            "ISA Net",
            "SIPP Employee Net",
            "Workplace Employee Net",
        ],
        var_name="Account",
        value_name="Net Contribution",
    )
    chart = (
        alt.Chart(plot_df)
        .mark_bar()
        .encode(
            x=alt.X("Age:O", title="Age"),
            y=alt.Y(
                "Net Contribution:Q", stack="normalize", title="Contribution share"
            ),
            color=alt.Color("Account:N", title="Account"),
            tooltip=["Account", "Net Contribution"],
        )
        .properties(title=title)
    )
    return chart


def make_pot_growth_plot(df: pd.DataFrame, title: Optional[str] = None) -> alt.Chart:
    """
    Create a line chart for each pot's nominal value over time.

    Args:
        df (pd.DataFrame): DataFrame containing projection results from project_retirement.
        title (str, optional): Custom title for the chart. If None, uses default title.
    Returns:
        alt.Chart: Altair chart object showing pot growth over time.
    """
    if title is None:
        title = "Pre-retirement nominal growth of each pot"

    plot_df = df.melt(
        id_vars=["Age"],
        value_vars=["Pot LISA", "Pot ISA", "Pot SIPP", "Pot Workplace"],
        var_name="Account",
        value_name="Value",
    )
    chart = (
        alt.Chart(plot_df)
        .mark_line()
        .encode(
            x=alt.X("Age:O", title="Age"),
            y=alt.Y("Value:Q", title="Nominal pot value (£)", stack=None),
            color=alt.Color("Account:N", title="Account"),
            tooltip=["Account", "Value"],
        )
        .properties(title=title)
    )
    return chart


def make_contribution_growth_plot(
    df: pd.DataFrame, title: Optional[str] = None
) -> alt.Chart:
    """
    Create a line chart for net contributions from each account over time.

    Args:
        df (pd.DataFrame): DataFrame containing projection results from project_retirement.
        title (str, optional): Custom title for the chart. If None, uses default title.
    Returns:
        alt.Chart: Altair chart object showing net contributions over time.
    """
    if title is None:
        title = "Net contributions by account over time"

    plot_df = df.melt(
        id_vars=["Age"],
        value_vars=[
            "LISA Net",
            "ISA Net",
            "SIPP Employee Net",
            "Workplace Employee Net",
        ],
        var_name="Account",
        value_name="Net Contribution",
    )
    chart = (
        alt.Chart(plot_df)
        .mark_line(strokeDash=[4, 2])
        .encode(
            x=alt.X("Age:O", title="Age"),
            y=alt.Y("Net Contribution:Q", title="Net contribution (£)", stack=None),
            color=alt.Color("Account:N", title="Account (Net Contribution)"),
            tooltip=["Account", "Net Contribution"],
        )
        .properties(title=title)
    )
    return chart


def make_growth_plot(df: pd.DataFrame, title: Optional[str] = None) -> alt.Chart:
    """
    Create a layered chart showing both pot growth and net contributions over time.

    Args:
        df (pd.DataFrame): DataFrame containing projection results from project_retirement.
        title (str, optional): Custom title for the chart. If None, uses default title.
    Returns:
        alt.Chart: Altair chart object showing both pot growth and net contributions.
    """
    # Prepare pot growth data
    pot_df = df.melt(
        id_vars=["Age"],
        value_vars=["Pot LISA", "Pot ISA", "Pot SIPP", "Pot Workplace"],
        var_name="Account",
        value_name="Value",
    )
    pot_chart = (
        alt.Chart(pot_df)
        .mark_line()
        .encode(
            x=alt.X("Age:O", title="Age"),
            y=alt.Y("Value:Q", title="Amount (£)", stack=None),
            color=alt.Color("Account:N", title="Account"),
            tooltip=["Account", "Value"],
            detail="Account:N",
        )
    )

    # Prepare accumulated net contribution data (dashed lines)
    acc_contrib_df = df.melt(
        id_vars=["Age"],
        value_vars=[
            "Accumulated LISA Net",
            "Accumulated ISA Net",
            "Accumulated SIPP Net",
            "Accumulated Workplace Net",
        ],
        var_name="Account",
        value_name="Accumulated Contribution",
    )
    # Clean up account names for legend
    acc_contrib_df["Account"] = acc_contrib_df["Account"].str.replace(
        "Accumulated ", "", regex=False
    )

    acc_contrib_chart = (
        alt.Chart(acc_contrib_df)
        .mark_line(strokeDash=[4, 2])
        .encode(
            x=alt.X("Age:O", title="Age"),
            y=alt.Y("Accumulated Contribution:Q", title="Amount (£)", stack=None),
            color=alt.Color("Account:N", title="Account (Accumulated)"),
            tooltip=["Account", "Accumulated Contribution"],
            detail="Account:N",
        )
    )

    # Layer both charts
    layered = alt.layer(pot_chart, acc_contrib_chart).resolve_scale(color="independent")
    layered = layered.properties(
        title=title or "Pot values and accumulated contributions by account over time"
    )
    return layered


def make_combined_plot(df: pd.DataFrame) -> alt.Chart:
    """
    Create a combined chart showing both contributions and growth.

    Args:
        df (pd.DataFrame): DataFrame containing projection results from project_retirement.
    Returns:
        alt.Chart: Combined Altair chart with contributions and growth.
    """
    contrib_chart = make_contribution_plot(df, "Annual Contributions by Account")
    growth_chart = make_growth_plot(df, "Pot Growth Over Time")

    # Horizontally concatenate the two charts
    combined = alt.hconcat(contrib_chart, growth_chart).resolve_scale(
        color="independent"
    )

    return combined


def make_income_breakdown_pie(
    income: IncomeBreakdown,
) -> "plotly.graph_objs._figure.Figure":
    """
    Create a pie chart for the income breakdown (Take-home, Income Tax, NI Contribution).

    Args:
        income: An object with attributes salary, take_home_salary, income_tax, ni_due.
    Returns:
        plotly Figure object.
    """
    import pandas as pd

    take_home = getattr(income, "take_home_salary", 0)
    income_tax = getattr(income, "income_tax", 0)
    ni_due = getattr(income, "ni_due", 0)
    pie_data = pd.DataFrame(
        {
            "Component": ["Take-home", "Income Tax", "NI Contribution"],
            "Amount": [take_home, income_tax, ni_due],
        }
    )
    fig = px.pie(
        pie_data,
        names="Component",
        values="Amount",
        title="Income Breakdown",
        color_discrete_sequence=px.colors.sequential.Blues,
    )
    return fig
