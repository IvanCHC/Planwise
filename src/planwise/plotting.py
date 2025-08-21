"""
Plotting utilities for Planwise retirement and investment projections.

This module provides functions to generate Altair charts for visualizing investment breakdowns, annual contributions, growth projections, withdrawals, and balances by account over time.

Functions:
- plot_pie_chart_breakdown: Pie chart for portfolio/account breakdown.
- plot_annual_contribution_chart: Stacked bar chart for annual net contributions by account.
- plot_growth_projection_chart: Line chart for portfolio/account growth over time.
- plot_withdrawals_by_account_chart: Bar chart for withdrawals by account over time.
- plot_total_withdrawals_chart: Line chart for total withdrawals and tax over time.
- plot_balances_by_account_chart: Line chart for balances by account over time.
- plot_total_balance_chart: Line chart for total balance over time.
"""

import altair as alt
import pandas as pd


def plot_pie_chart_breakdown(breakdown: dict[str, float]) -> alt.Chart:
    """
    Generate a pie chart showing the breakdown of portfolio or account values.

    Args:
        breakdown (dict[str, float]): Dictionary of account/type and their values.
    Returns:
        alt.Chart: Altair pie chart.
    """
    if not breakdown:
        return alt.Chart(pd.DataFrame({"Type": [], "Value": []})).mark_arc()

    data = pd.DataFrame(
        {"Type": list(breakdown.keys()), "Value": list(breakdown.values())}
    )
    data["Percent"] = data["Value"] / data["Value"].sum()

    chart = (
        alt.Chart(data)
        .mark_arc(innerRadius=50, outerRadius=100)
        .encode(
            theta=alt.Theta("Value:Q", stack=True, title=""),
            color=alt.Color("Type:N", title="Type", legend=None),
            tooltip=[
                alt.Tooltip("Type:N"),
                alt.Tooltip("Value:Q"),
                alt.Tooltip("Percent:Q", format=".1%"),
            ],
        )
        .properties(width=200, height=250)
    )
    labels = (
        alt.Chart(data)
        .transform_filter("datum.Percent >= 0.03")
        .mark_text(radius=75, radiusOffset=0, fontSize=8)
        .encode(
            theta=alt.Theta("Value:Q", stack=True),
            text=alt.Text("Type:N"),
            color=alt.value("black"),
        )
    )

    return chart + labels


def plot_annual_contribution_chart(dataframe: pd.DataFrame) -> alt.Chart:
    """
    Generate a stacked bar chart of annual net contributions by account.

    Args:
        dataframe (pd.DataFrame): DataFrame with annual contribution data.
    Returns:
        alt.Chart: Altair bar chart.
    """
    data = dataframe.melt(
        id_vars=["Age"],
        value_vars=[
            "LISA Net",
            "ISA Net",
            "SIPP Net",
            "Workplace EE Net",
        ],
        var_name="Account",
        value_name="Net Contribution",
    )
    data["Account"] = data["Account"].str.replace(" Net", "", regex=False)
    data["Account"] = data["Account"].str.replace(" EE", "", regex=False)
    title = "Net contributions by account (share of total)"
    if data.empty:
        return alt.Chart(pd.DataFrame({"Age": [], "Net Contribution": []})).mark_bar()
    chart = (
        alt.Chart(data)
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


def plot_growth_projection_chart(dataframe: pd.DataFrame) -> alt.Chart:
    """
    Generate a line chart showing portfolio and account growth projections over time.

    Args:
        dataframe (pd.DataFrame): DataFrame with growth projection data.
    Returns:
        alt.Chart: Altair line chart.
    """
    data = dataframe.melt(
        id_vars=["Age"],
        value_vars=[
            "Portfolio Balance",
            "LISA Balance",
            "ISA Balance",
            "SIPP Balance",
            "Workplace Balance",
        ],
        var_name="Account",
        value_name="Value",
    )
    data["Account"] = data["Account"].str.replace(" Balance", "", regex=False)
    data["Account"] = data["Account"].str.replace("Portfolio", "Total", regex=False)
    if data.empty:
        return alt.Chart(pd.DataFrame({"Age": [], "Value": []})).mark_line()
    title = "Portfolio growth projection by account over time"
    chart = (
        alt.Chart(data)
        .mark_line()
        .encode(
            x=alt.X("Age:O", title="Age"),
            y=alt.Y("Value:Q", title="Amount (£)", stack=None),
            color=alt.Color("Account:N", title="Account"),
            tooltip=["Account", "Value"],
        )
    ).properties(title=title)
    return chart


def plot_withdrawals_by_account_chart(
    dataframe: pd.DataFrame, sub_text: str = "Today"
) -> alt.Chart:
    """
    Generate a bar chart of withdrawals by account over time.

    Args:
        dataframe (pd.DataFrame): DataFrame with withdrawal data.
        sub_text (str): Suffix for column names (e.g., 'Today', 'Inflation Adjusted').
    Returns:
        alt.Chart: Altair bar chart.
    """
    data = dataframe.melt(
        id_vars=["Age"],
        value_vars=[
            f"Withdrawal LISA {sub_text}",
            f"Withdrawal ISA {sub_text}",
            f"Withdrawal Tax-Free Pension {sub_text}",
            f"Withdrawal Taxable Pension {sub_text}",
            f"Withdrawal State Pension {sub_text}",
            f"Withdrawal Shortfall {sub_text}",
        ],
        var_name="Account",
        value_name="Withdrawal",
    )
    data["Account"] = data["Account"].str.replace("Withdrawal ", "", regex=False)
    data["Account"] = data["Account"].str.replace(f" {sub_text}", "", regex=False)
    if data.empty:
        return alt.Chart(pd.DataFrame({"Age": [], "Withdrawal": []})).mark_bar()
    title_sub_text = "in today's money" if sub_text == "Today" else "inflation adjusted"
    title = f"Withdrawals by account {title_sub_text}"
    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("Age:O", title="Age"),
            y=alt.Y("Withdrawal:Q", title="Withdrawal (£)"),
            color=alt.Color("Account:N", title="Account"),
            tooltip=["Account", "Withdrawal"],
        )
        .properties(title=title)
    )
    return chart


def plot_total_withdrawals_chart(
    dataframe: pd.DataFrame, sub_text: str = "Today"
) -> alt.Chart:
    """
    Generate a line chart of total withdrawals and tax over time.

    Args:
        dataframe (pd.DataFrame): DataFrame with withdrawal and tax data.
        sub_text (str): Suffix for column names (e.g., 'Today', 'Inflation Adjusted').
    Returns:
        alt.Chart: Altair line chart.
    """
    withdrawal_cols = [
        f"Total Withdrawal {sub_text}",
        f"Total Withdrawal After Tax {sub_text}",
        f"Income Tax {sub_text}",
    ]
    available_cols = [col for col in withdrawal_cols if col in dataframe.columns]

    if not available_cols:
        return alt.Chart(pd.DataFrame({"Age": [], "Value": []})).mark_line()

    data = dataframe.melt(
        id_vars=["Age"],
        value_vars=available_cols,
        var_name="Type",
        value_name="Value",
    )
    data["Type"] = data["Type"].str.replace(f" {sub_text}", "", regex=False)

    title_sub_text = "in today's money" if sub_text == "Today" else "inflation adjusted"
    title = f"Total withdrawals over Time ({title_sub_text})"
    chart = (
        alt.Chart(data)
        .mark_line()
        .encode(
            x=alt.X("Age:O", title="Age"),
            y=alt.Y("Value:Q", title="Total Withdrawal (£)"),
            color=alt.Color("Type:N", title="Type"),
            tooltip=["Age", "Type", "Value"],
        )
    ).properties(title=title)

    return chart


def plot_balances_by_account_chart(
    dataframe: pd.DataFrame, sub_text: str = "Today"
) -> alt.Chart:
    """
    Generate a line chart of balances by account over time.

    Args:
        dataframe (pd.DataFrame): DataFrame with account balance data.
        sub_text (str): Suffix for column names (e.g., 'Today', 'Inflation Adjusted').
    Returns:
        alt.Chart: Altair line chart.
    """
    balance_cols = [
        f"LISA Balance {sub_text}",
        f"ISA Balance {sub_text}",
        f"Tax-Free Pension Balance {sub_text}",
        f"Taxable Pension Balance {sub_text}",
    ]
    available_cols = [col for col in balance_cols if col in dataframe.columns]

    if not available_cols:
        return alt.Chart(pd.DataFrame({"Age": [], "Value": []})).mark_line()

    data = dataframe.melt(
        id_vars=["Age"],
        value_vars=available_cols,
        var_name="Account",
        value_name="Value",
    )
    data["Account"] = data["Account"].str.replace(
        f" Balance {sub_text}", "", regex=False
    )

    title_sub_text = "in today's money" if sub_text == "Today" else "inflation adjusted"
    title = f"Balances by account {title_sub_text}"
    chart = (
        alt.Chart(data)
        .mark_line()
        .encode(
            x=alt.X("Age:O", title="Age"),
            y=alt.Y("Value:Q", title="Balance (£)"),
            color=alt.Color("Account:N", title="Account"),
            tooltip=["Age", "Account", "Value"],
        )
    ).properties(title=title)

    return chart


def plot_total_balance_chart(
    dataframe: pd.DataFrame, sub_text: str = "Today"
) -> alt.Chart:
    """
    Generate a line chart of total portfolio balance over time.

    Args:
        dataframe (pd.DataFrame): DataFrame with total balance data.
        sub_text (str): Suffix for column names (e.g., 'Today', 'Inflation Adjusted').
    Returns:
        alt.Chart: Altair line chart.
    """
    total_balance_col = f"Total Balance {sub_text}"

    if total_balance_col not in dataframe.columns:
        return alt.Chart(pd.DataFrame({"Age": [], "Value": []})).mark_line()

    data = dataframe[["Age", total_balance_col]].rename(
        columns={total_balance_col: "Total Balance"}
    )
    title_sub_text = "in today's money" if sub_text == "Today" else "inflation adjusted"
    title = f"Total balance over Time ({title_sub_text})"
    chart = (
        alt.Chart(data)
        .mark_line()
        .encode(
            x=alt.X("Age:O", title="Age"),
            y=alt.Y("Total Balance:Q", title="Total Balance (£)"),
            tooltip=["Age", "Total Balance"],
        )
    ).properties(title=title)

    return chart
