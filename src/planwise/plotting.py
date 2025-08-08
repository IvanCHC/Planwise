import pandas as pd
import plotly.graph_objs as go


def plot_post_retirement_withdrawals_todays(df: pd.DataFrame) -> go.Figure:
    """
    Plot post-retirement withdrawals and pots using only Today's Money columns.
    """
    fig = go.Figure()
    # Plot Total Pot (Today's Money)
    if "Total Pot (Today's Money)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Total Pot (Today's Money)"],
                mode="lines",
                name="Total Pot (Today's Money)",
                line=dict(color="navy", width=2),
            )
        )
    # Plot Withdrawal (Today's Money)
    if "Withdrawal (Today's Money)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Withdrawal (Today's Money)"],
                mode="lines",
                name="Withdrawal (Today's Money)",
                line=dict(color="darkorange", dash="dot"),
            )
        )
    # Plot Remaining Withdrawal Shortfall
    if (
        "Remaining Withdrawal Shortfall" in df.columns
        and (df["Remaining Withdrawal Shortfall"] > 0).any()
    ):
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Remaining Withdrawal Shortfall"],
                mode="lines",
                name="Withdrawal Shortfall",
                line=dict(color="red", dash="dot"),
            )
        )
    # Plot State Pension (Today's Money)
    if "State Pension (Today's Money)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["State Pension (Today's Money)"],
                mode="lines",
                name="State Pension (Today's Money)",
                line=dict(color="green", dash="dot"),
            )
        )
    return fig


def plot_postretirement_accounts_todays(df: pd.DataFrame) -> go.Figure:
    """
    Plot post-retirement account pots using only Today's Money columns.
    """
    fig = go.Figure()
    # Plot Pension (Today's Money)
    if "Pot SIPP" in df.columns and "Pot Workplace" in df.columns:
        pension_todays = df["Pot SIPP"] + df["Pot Workplace"]
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=pension_todays,
                mode="lines",
                name="Pension (Today's Money)",
                line=dict(color="#1f77b4", width=2),
            )
        )
    elif "Pot SIPP" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Pot SIPP"],
                mode="lines",
                name="Pension (Today's Money)",
                line=dict(color="#1f77b4", width=2),
            )
        )
    elif "Pot Workplace" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Pot Workplace"],
                mode="lines",
                name="Pension (Today's Money)",
                line=dict(color="#1f77b4", width=2),
            )
        )
    # Plot LISA (Today's Money)
    if "Pot LISA" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Pot LISA"],
                mode="lines",
                name="LISA (Today's Money)",
                line=dict(color="#ff7f0e", width=2),
            )
        )
    # Plot ISA (Today's Money)
    if "Pot ISA" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Pot ISA"],
                mode="lines",
                name="ISA (Today's Money)",
                line=dict(color="#2ca02c", width=2),
            )
        )
    # Plot State Pension (Today's Money)
    if "State Pension (Today's Money)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["State Pension (Today's Money)"],
                mode="lines",
                name="State Pension (Today's Money)",
                line=dict(color="green", dash="dot"),
            )
        )
    return fig


def plot_postretirement_accounts(df: pd.DataFrame) -> go.Figure:
    import plotly.graph_objs as go

    fig = go.Figure()
    # Only plot Pension, LISA, ISA, and optionally State Pension columns
    account_cols = []
    if "Pot Pension" in df.columns:
        account_cols.append("Pot Pension")
    else:
        # Fallback for legacy: combine SIPP and Workplace if present
        if "Pot SIPP" in df.columns and "Pot Workplace" in df.columns:
            df["Pot Pension"] = df["Pot SIPP"] + df["Pot Workplace"]
            account_cols.append("Pot Pension")
        elif "Pot SIPP" in df.columns:
            account_cols.append("Pot SIPP")
        elif "Pot Workplace" in df.columns:
            account_cols.append("Pot Workplace")
    if "Pot LISA" in df.columns:
        account_cols.append("Pot LISA")
    if "Pot ISA" in df.columns:
        account_cols.append("Pot ISA")
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    for i, col in enumerate(account_cols):
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df[col],
                mode="lines",
                name=col.replace("Pot ", ""),
                line=dict(color=colors[i % len(colors)], width=2),
            )
        )
    # Optionally plot state pension columns if present
    if "State Pension (Inflation Adjusted)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["State Pension (Inflation Adjusted)"],
                mode="lines",
                name="State Pension (Inflation Adjusted)",
                line=dict(color="#2ca02c", dash="dot", width=2),
            )
        )
    if "State Pension (Today's Money)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["State Pension (Today's Money)"],
                mode="lines",
                name="State Pension (Today's Money)",
                line=dict(color="#17becf", dash="dash", width=2),
            )
        )
    fig.update_layout(
        title="Account Pots Over Time",
        xaxis=dict(title=dict(text="Age", font=dict(size=16)), tickfont=dict(size=14)),
        yaxis=dict(
            title=dict(text="Pot Value (£)", font=dict(size=16)), tickfont=dict(size=14)
        ),
        legend=dict(
            x=1.02,
            y=1,
            xanchor="left",
            yanchor="top",
            font=dict(size=13),
            orientation="v",
        ),
        template="plotly_white",
        hovermode="x unified",
        margin=dict(r=120),
    )
    return fig


def plot_post_retirement_withdrawals(df: pd.DataFrame) -> go.Figure:
    """
    Plot post-retirement withdrawals and pot balances using Plotly.

    Args:
        df (pd.DataFrame): DataFrame from project_post_retirement, must include 'Age', 'Nominal Withdrawal', 'Total Pot', and 'Remaining Withdrawal Shortfall'.

    Returns:
        go.Figure: Plotly Figure object.
    """
    fig = go.Figure()

    # Plot total pot (nominal and today's money if available)
    if "Total Pot" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Total Pot"],
                mode="lines",
                name="Total Pot (Nominal)",
                line=dict(color="royalblue", width=2),
            )
        )
    if "Total Pot (Today's Money)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Total Pot (Today's Money)"],
                mode="lines",
                name="Total Pot (Today's Money)",
                line=dict(color="navy", dash="dot", width=2),
            )
        )

    # Plot withdrawals (inflation adjusted and today's money)
    if "Withdrawal (Inflation Adjusted)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Withdrawal (Inflation Adjusted)"],
                mode="lines",
                name="Withdrawal (Inflation Adjusted)",
                line=dict(color="orange", dash="dash"),
            )
        )
    if "Withdrawal (Today's Money)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Withdrawal (Today's Money)"],
                mode="lines",
                name="Withdrawal (Today's Money)",
                line=dict(color="darkorange", dash="dot"),
            )
        )

    # Plot shortfall if any
    if (
        "Remaining Withdrawal Shortfall" in df.columns
        and (df["Remaining Withdrawal Shortfall"] > 0).any()
    ):
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Remaining Withdrawal Shortfall"],
                mode="lines",
                name="Withdrawal Shortfall",
                line=dict(color="red", dash="dot"),
            )
        )

    # Plot state pension columns if present
    if "State Pension (Inflation Adjusted)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["State Pension (Inflation Adjusted)"],
                mode="lines",
                name="State Pension (Inflation Adjusted)",
                line=dict(color="#2ca02c", dash="dot", width=2),
            )
        )
    if "State Pension (Today's Money)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["State Pension (Today's Money)"],
                mode="lines",
                name="State Pension (Today's Money)",
                line=dict(color="#17becf", dash="dash", width=2),
            )
        )

    fig.update_layout(
        title="Post-Retirement Withdrawals and Pot Balances",
        xaxis=dict(
            title=dict(text="Age", font=dict(size=16)),
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            title=dict(text="Amount (£)", font=dict(size=16)),
            tickfont=dict(size=14),
        ),
        legend=dict(
            x=1.02,
            y=1,
            xanchor="left",
            yanchor="top",
            font=dict(size=13),
            orientation="v",
        ),
        template="plotly_white",
        hovermode="x unified",
        margin=dict(r=120),
    )
    return fig


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
