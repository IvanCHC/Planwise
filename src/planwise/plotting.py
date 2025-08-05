"""
Plotting functions for visualizing retirement projections in Planwise.

This module provides functions to create Altair charts for contribution analysis
and growth projections, including combined visualizations.
"""

from typing import Optional

import altair as alt
import pandas as pd


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


def make_growth_plot(df: pd.DataFrame, title: Optional[str] = None) -> alt.Chart:
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

    # Melt the DataFrame to long format for Altair
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
