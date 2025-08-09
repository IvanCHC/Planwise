"""
Plotting utilities for Planwise
===============================

This module contains a set of classes and helper functions for visualising the
results produced by the Planwise retirement projection engine.  The previous
version of this module exposed a handful of standalone functions such as
``make_contribution_plot`` and ``make_growth_plot``.  While those functions
remain available as thin wrappers for backwards compatibility, the preferred
interface is now the :class:`RetirementPlotter` class which encapsulates the
preparation of data and construction of Altair charts.

The refactoring into a class makes it easier to customise the plotting logic
and reuse common transformations.  In addition to the Altair‑based plots used
pre‑retirement, the module still provides a number of Plotly functions for
visualising post‑retirement withdrawals and account balances.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import altair as alt
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from .core import IncomeBreakdown


@dataclass
class RetirementPlotter:
    """Helper class for constructing Altair charts from projection data.

    Instances of :class:`RetirementPlotter` hold a pandas DataFrame produced
    by :func:`planwise.core.project_retirement` (or a compatible structure).  The
    methods on this class convert that DataFrame into long‑form tables suitable
    for Altair and build charts showing annual net contributions, pot growth
    (including accumulated contributions) and a combined view of both.  It is
    possible to override the default titles by supplying ``title`` arguments
    to the respective methods.

    Parameters
    ----------
    df : pd.DataFrame
        The projection data.  It should contain at least an ``Age`` column plus
        the relevant contribution and pot columns.
    """

    df: pd.DataFrame

    #: Default column names used for contributions.  Each entry corresponds to
    #: an account.  These names are expected to exist in the input DataFrame.
    CONTRIBUTION_COLUMNS: List[str] = field(
        default_factory=lambda: [
            "LISA Net",
            "ISA Net",
            "SIPP Employee Net",
            "Workplace Employee Net",
        ]
    )

    #: Mapping of logical account names to the names of pot and net contribution
    #: columns.  The keys of this dict are used for labelling series in the
    #: growth plot.  ``pot_col`` is mandatory, ``net_col`` is optional and
    #: used when pre‑computed ``Accumulated <Account> Net`` columns are absent.
    ACCOUNT_MAPPING: Dict[str, Dict[str, str]] = field(
        default_factory=lambda: {
            "LISA": {"pot_col": "Pot LISA", "net_col": "LISA Net"},
            "ISA": {"pot_col": "Pot ISA", "net_col": "ISA Net"},
            "SIPP": {"pot_col": "Pot SIPP", "net_col": "SIPP Employee Net"},
            "Workplace": {
                "pot_col": "Pot Workplace",
                "net_col": "Workplace Employee Net",
            },
        }
    )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _prepare_contribution_data(self) -> pd.DataFrame:
        """Return a long‑form DataFrame of net contributions per account per age.

        The returned DataFrame has the following columns:

        - ``Age`` (as in the source DataFrame)
        - ``Account`` containing the name of the contribution column
        - ``Net Contribution`` containing the numeric values

        If none of the expected contribution columns are present in the source
        DataFrame then an empty DataFrame is returned.
        """
        available_cols = [c for c in self.CONTRIBUTION_COLUMNS if c in self.df.columns]
        if not available_cols:
            return pd.DataFrame(columns=["Age", "Account", "Net Contribution"])
        return self.df.melt(
            id_vars=["Age"],
            value_vars=available_cols,
            var_name="Account",
            value_name="Net Contribution",
        )

    def _prepare_growth_data(self) -> pd.DataFrame:
        """Return a long‑form DataFrame containing pot values and accumulated nets.

        For each account defined in :attr:`ACCOUNT_MAPPING`, this method
        attempts to extract the pot column and either a pre‑computed
        ``Accumulated <Account> Net`` column or computes a cumulative sum of
        the yearly net contributions.  The resulting DataFrame has columns

        - ``Age``
        - ``Account``
        - ``Value``
        - ``Type`` (either ``"Pot"`` or ``"Accumulated"``)

        Accounts missing their pot column are skipped entirely.  If neither
        accumulated nor yearly net contributions are available for an account
        then only its pot values are included.
        """
        df_sorted = self.df.sort_values("Age").reset_index(drop=True)
        records: List[Dict[str, Any]] = []

        for account, mapping in self.ACCOUNT_MAPPING.items():
            pot_col = mapping.get("pot_col")
            net_col = mapping.get("net_col")
            # Skip accounts without a pot column
            if pot_col not in df_sorted.columns:
                continue
            # Add pot values
            for age, val in zip(df_sorted["Age"], df_sorted[pot_col]):
                records.append(
                    {"Age": age, "Account": account, "Value": val, "Type": "Pot"}
                )

            # Decide how to obtain cumulative values
            acc_col_name = f"Accumulated {account} Net"
            if acc_col_name in df_sorted.columns:
                cumulative_series = df_sorted[acc_col_name]
            elif net_col and net_col in df_sorted.columns:
                cumulative_series = df_sorted[net_col].cumsum()
            else:
                # Neither accumulated nor net column exists; skip accumulated series
                continue
            for age, val in zip(df_sorted["Age"], cumulative_series):
                records.append(
                    {
                        "Age": age,
                        "Account": account,
                        "Value": val,
                        "Type": "Accumulated",
                    }
                )

        return pd.DataFrame.from_records(records)

    # ------------------------------------------------------------------
    # Public chart methods
    # ------------------------------------------------------------------
    def contribution_chart(self, title: Optional[str] = None) -> alt.Chart:
        """Build a stacked bar chart of net contributions.

        Parameters
        ----------
        title : str, optional
            A custom title for the chart.  If omitted, a sensible default is used.

        Returns
        -------
        alt.Chart
            An Altair chart showing the share of net contributions by account.
        """
        data = self._prepare_contribution_data()
        if title is None:
            title = "Net contributions by account (share of total)"
        # If there is no data, return an empty chart with a bar mark for consistency
        if data.empty:
            return alt.Chart(
                pd.DataFrame({"Age": [], "Net Contribution": []})
            ).mark_bar()
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

    def growth_chart(self, title: Optional[str] = None) -> alt.Chart:
        """Build a line chart showing pot values and accumulated contributions.

        This chart plots both the nominal pot values and the accumulated net
        contributions for each account.  Solid lines represent pots while dashed
        lines represent accumulated contributions.  If no growth data is
        available, an empty line chart is returned.

        Parameters
        ----------
        title : str, optional
            Custom title; defaults to a descriptive string.

        Returns
        -------
        alt.Chart
            An Altair chart with a single ``line`` mark containing both series.
        """
        data = self._prepare_growth_data()
        if data.empty:
            return alt.Chart(pd.DataFrame({"Age": [], "Value": []})).mark_line()
        if title is None:
            title = "Pot values and accumulated contributions by account over time"
        dash_domain = ["Pot", "Accumulated"]
        dash_range = [[1], [4, 2]]
        chart = (
            alt.Chart(data)
            .mark_line()
            .encode(
                x=alt.X("Age:O", title="Age"),
                y=alt.Y("Value:Q", title="Amount (£)", stack=None),
                color=alt.Color("Account:N", title="Account"),
                strokeDash=alt.StrokeDash(
                    "Type:N",
                    title="",
                    scale=alt.Scale(domain=dash_domain, range=dash_range),
                ),
                tooltip=["Account", "Type", "Value"],
            )
        ).properties(title=title)
        return chart

    def combined_chart(
        self,
        contrib_title: Optional[str] = None,
        growth_title: Optional[str] = None,
    ) -> alt.Chart:
        """Return a horizontally concatenated chart of contributions and growth.

        This combines the results of :meth:`contribution_chart` and
        :meth:`growth_chart` into a single Altair chart.  You can provide
        different titles for each panel using the ``contrib_title`` and
        ``growth_title`` arguments.  Colours are resolved independently for
        each panel.

        Returns
        -------
        alt.Chart
            A horizontally concatenated chart with two panels.
        """
        left = self.contribution_chart(contrib_title)
        right = self.growth_chart(growth_title)
        return alt.hconcat(left, right).resolve_scale(color="independent")


# --------------------------------------------------------------------------
# Convenience functions
#
# The following functions are thin wrappers around the RetirementPlotter.  They
# exist for backwards compatibility with code written against earlier versions
# of Planwise.  New code should instantiate :class:`RetirementPlotter`
# explicitly and call its methods.
# --------------------------------------------------------------------------


def make_contribution_plot(df: pd.DataFrame, title: Optional[str] = None) -> alt.Chart:
    """Backward‑compatible wrapper for :meth:`RetirementPlotter.contribution_chart`."""
    return RetirementPlotter(df).contribution_chart(title)


def make_growth_plot(df: pd.DataFrame, title: Optional[str] = None) -> alt.Chart:
    """Backward‑compatible wrapper for :meth:`RetirementPlotter.growth_chart`."""
    return RetirementPlotter(df).growth_chart(title)


def make_combined_plot(df: pd.DataFrame) -> alt.Chart:
    """Backward‑compatible wrapper for :meth:`RetirementPlotter.combined_chart`."""
    return RetirementPlotter(df).combined_chart(
        "Annual Contributions by Account", "Pot Growth Over Time"
    )


def make_pot_growth_plot(df: pd.DataFrame, title: Optional[str] = None) -> alt.Chart:
    """Deprecated alias for :func:`make_growth_plot`.

    This function exists solely for API compatibility with older versions of
    Planwise.  Internally it forwards to :func:`make_growth_plot`.  You should
    use :func:`make_growth_plot` or better yet instantiate a
    :class:`RetirementPlotter` and call :meth:`RetirementPlotter.growth_chart`.
    """
    return make_growth_plot(df, title)


def make_contribution_growth_plot(
    df: pd.DataFrame, title: Optional[str] = None
) -> alt.Chart:
    """Deprecated alias for :func:`make_growth_plot`.

    Historically this function produced a chart showing net contributions over
    time.  That functionality is now subsumed into :func:`make_growth_plot` and
    :class:`RetirementPlotter`.  It is kept as a no‑op wrapper to avoid
    breaking existing code but will be removed in a future release.
    """
    return make_growth_plot(df, title)


def make_income_breakdown_pie(income: IncomeBreakdown) -> go.Figure:
    """Create a pie chart for the income breakdown (take‑home, tax and NI).

    Parameters
    ----------
    income : planwise.core.IncomeBreakdown
        A dataclass describing the user's income after tax and NI.  Any
        attributes missing on this object will default to zero.

    Returns
    -------
    plotly.graph_objs.Figure
        A Plotly pie chart illustrating the relative proportions of take‑home
        salary, income tax and national insurance.
    """
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


def plot_post_retirement_withdrawals_todays(df: pd.DataFrame) -> go.Figure:
    """Plot post‑retirement withdrawals and pots in today's money.

    This helper produces a simple Plotly figure containing the total pot,
    withdrawals and state pension series, all expressed in today's pounds.  Any
    missing columns are ignored.  The resulting figure has multiple traces with
    sensible colours and line styles.
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
    fig.update_layout(
        title="Post-Retirement Withdrawals and Pot Balances (in Today's Money)",
        xaxis=dict(title=dict(text="Age", font=dict(size=16)), tickfont=dict(size=14)),
        yaxis=dict(
            title=dict(text="Amount (£)", font=dict(size=16)), tickfont=dict(size=14)
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


def plot_postretirement_accounts_todays(df: pd.DataFrame) -> go.Figure:
    """Plot post‑retirement account pots in today's money, including Pension Tax Free/Tax."""
    fig = go.Figure()
    # Pension Tax Free
    if "Pot Pension Tax Free" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Pot Pension Tax Free"],
                mode="lines",
                name="Pension Tax Free (Today's Money)",
                line=dict(color="#1f77b4", width=2, dash="solid"),
            )
        )
    # Pension Tax
    if "Pot Pension Tax" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Pot Pension Tax"],
                mode="lines",
                name="Pension Tax (Today's Money)",
                line=dict(color="#1f77b4", width=2, dash="dash"),
            )
        )
    # Plot SIPP and Workplace pots as Pension (Today's Money)
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


def plot_withdrawals_by_account(
    df: pd.DataFrame, title: Optional[str] = None
) -> go.Figure:
    """Plot a stacked bar chart of withdrawals from each account in today's money.

    This helper scans the DataFrame for columns named ``"Withdrawal <Account> (Today's Money)"``
    and constructs a stacked bar chart showing the amount withdrawn from each
    account by age.  If no such columns are present, an empty figure is
    returned.

    Parameters
    ----------
    df : pd.DataFrame
        The post‑retirement projection DataFrame returned by
        :func:`planwise.core.project_post_retirement`.
    title : str, optional
        Title for the chart.  If omitted a default title is used.

    Returns
    -------
    plotly.graph_objs._figure.Figure
        A stacked bar chart showing withdrawals by account.
    """
    # Find withdrawal columns formatted as "Withdrawal <Account> (Today's Money)"
    withdraw_cols = [
        col
        for col in df.columns
        if col.startswith("Withdrawal ")
        and col.endswith("(Today's Money)")
        and not col.startswith("Withdrawal (Today's Money)")
    ]
    if not withdraw_cols:
        return go.Figure()
    # Extract account names from column names
    accounts: List[str] = []
    for col in withdraw_cols:
        # Strip the prefix and suffix to get the account name
        acc = col[len("Withdrawal ") : -len(" (Today's Money)")]
        accounts.append(acc)
    fig = go.Figure()
    for col, acc in zip(withdraw_cols, accounts):
        fig.add_trace(
            go.Bar(
                x=df["Age"],
                y=df[col],
                name=acc,
            )
        )
    if title is None:
        title = "Withdrawals by Account (Today's Money)"
    fig.update_layout(
        barmode="stack",
        title=title,
        xaxis=dict(title="Age"),
        yaxis=dict(title="Withdrawal (£)"),
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


def plot_postretirement_accounts(df: pd.DataFrame) -> go.Figure:
    """Plot post‑retirement account pots over time, including Pension Tax Free/Tax."""
    fig = go.Figure()
    # Pension Tax Free
    if "Pot Pension Tax Free" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Pot Pension Tax Free"],
                mode="lines",
                name="Pension Tax Free",
                line=dict(color="#1f77b4", width=2, dash="solid"),
            )
        )
    # Pension Tax
    if "Pot Pension Tax" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Pot Pension Tax"],
                mode="lines",
                name="Pension Tax",
                line=dict(color="#1f77b4", width=2, dash="dash"),
            )
        )
    # Determine which account columns to plot
    account_cols: List[str] = []
    if "Pot Pension" in df.columns:
        account_cols.append("Pot Pension")
    else:
        if "Pot SIPP" in df.columns and "Pot Workplace" in df.columns:
            # Combine SIPP and workplace into a pension pot
            df = df.copy()
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
        title="Account Pots Over Time (in Today's Money)",
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
    """Plot post‑retirement withdrawals and pot balances using Plotly, including tax paid."""
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
    # Plot Tax Paid on Withdrawals (Inflation Adjusted)
    if "Tax Paid on Withdrawals (Inflation Adjusted)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Tax Paid on Withdrawals (Inflation Adjusted)"],
                mode="lines",
                name="Tax Paid on Withdrawals (Inflation Adjusted)",
                line=dict(color="crimson", dash="dot"),
            )
        )
    # Plot Tax Paid on Withdrawals (Today's Money)
    if "Tax Paid on Withdrawals (Today's Money)" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=df["Tax Paid on Withdrawals (Today's Money)"],
                mode="lines",
                name="Tax Paid on Withdrawals (Today's Money)",
                line=dict(color="crimson", dash="dash"),
            )
        )
    fig.update_layout(
        title="Post-Retirement Withdrawals and Pot Balances",
        xaxis=dict(title=dict(text="Age", font=dict(size=16)), tickfont=dict(size=14)),
        yaxis=dict(
            title=dict(text="Amount (£)", font=dict(size=16)), tickfont=dict(size=14)
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


def plot_accumulated_tax_paid_postret(df: pd.DataFrame) -> go.Figure:
    """Plot accumulated tax paid on withdrawals post-retirement."""
    fig = go.Figure()
    if "Tax Paid on Withdrawals (Inflation Adjusted)" in df.columns:
        acc_tax_infl = df["Tax Paid on Withdrawals (Inflation Adjusted)"].cumsum()
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=acc_tax_infl,
                mode="lines",
                name="Accumulated Tax Paid (Inflation Adjusted)",
                line=dict(color="crimson", width=2, dash="solid"),
            )
        )
    if "Tax Paid on Withdrawals (Today's Money)" in df.columns:
        acc_tax_today = df["Tax Paid on Withdrawals (Today's Money)"].cumsum()
        fig.add_trace(
            go.Scatter(
                x=df["Age"],
                y=acc_tax_today,
                mode="lines",
                name="Accumulated Tax Paid (Today's Money)",
                line=dict(color="crimson", width=2, dash="dash"),
            )
        )
    fig.update_layout(
        title="Accumulated Tax Paid on Withdrawals (Post-Retirement)",
        xaxis=dict(title=dict(text="Age", font=dict(size=16)), tickfont=dict(size=14)),
        yaxis=dict(
            title=dict(text="Accumulated Tax (£)", font=dict(size=16)),
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
