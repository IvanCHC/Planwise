import pandas as pd
import streamlit as st

import planwise as pw
from planwise.profile import ProfileSettings


def _render_portfilio_statistics(
    dataframe: pd.DataFrame, total_initial_balance: float
) -> None:
    final_year = dataframe.iloc[-1]
    portfilio_balance = final_year["Portfolio Balance"]
    net_contribution = final_year["Portfolio Net Contribution"]
    growth = portfilio_balance - net_contribution - total_initial_balance

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Account Balance", f"£{portfilio_balance:,.0f}")
    with col2:
        st.metric("Total Net Contribution", f"£{net_contribution:,.0f}")
    with col3:
        st.metric("Total Growth", f"£{growth:,.0f}")
    with col4:
        st.metric(
            "Total Initial Balance",
            f"£{total_initial_balance:,.0f}",
        )
    with col5:
        multipler = max(
            (portfilio_balance - total_initial_balance) / net_contribution, 1
        )
        if multipler == float("inf"):
            multipler = "inf"
        elif multipler == float("nan"):
            multipler = "NaN"
        else:
            multipler = f"{multipler:.2f}x"
        st.metric("Growth Multiple", f"{multipler}")


def _style_dataframe(df: pd.DataFrame) -> pd.DataFrame.style:
    return df.style.format(
        {
            "Salary": "£{:,.0f}",
            "Take Home Salary": "£{:,.0f}",
            "Income Tax": "£{:,.0f}",
            "NI Contribution": "£{:,.0f}",
            "LISA Net": "£{:,.0f}",
            "LISA Bonus": "£{:,.0f}",
            "LISA Gross": "£{:,.0f}",
            "ISA Net": "£{:,.0f}",
            "ISA Gross": "£{:,.0f}",
            "Workplace ER": "£{:,.0f}",
            "Workplace EE Net": "£{:,.0f}",
            "Workplace EE Gross": "£{:,.0f}",
            "Workplace Tax Relief": "£{:,.0f}",
            "SIPP Net": "£{:,.0f}",
            "SIPP Gross": "£{:,.0f}",
            "SIPP Tax Relief": "£{:,.0f}",
            "Tax Relief": "£{:,.0f}",
            "Tax Refund": "£{:,.0f}",
            "LISA Balance": "£{:,.0f}",
            "ISA Balance": "£{:,.0f}",
            "Workplace Balance": "£{:,.0f}",
            "SIPP Balance": "£{:,.0f}",
            "LISA Net Contribution": "£{:,.0f}",
            "ISA Net Contribution": "£{:,.0f}",
            "Workplace Net Contribution": "£{:,.0f}",
            "SIPP Net Contribution": "£{:,.0f}",
            "LISA Gross Contribution": "£{:,.0f}",
            "ISA Gross Contribution": "£{:,.0f}",
            "Workplace Gross Contribution": "£{:,.0f}",
            "SIPP Gross Contribution": "£{:,.0f}",
            "Portfolio Balance": "£{:,.0f}",
            "Portfolio Net Contribution": "£{:,.0f}",
            "Portfolio Gross Contribution": "£{:,.0f}",
            "Annual Net Contribution": "£{:,.0f}",
            "Annual Gross Contribution": "£{:,.0f}",
        }
    )


def _render_investment_dataframe(dataframe: pd.DataFrame.style) -> None:
    st.subheader("Investment year-by-year projection & breakdown")
    with st.expander("View full investment projection"):
        st.dataframe(dataframe, use_container_width=True)


def _render_portfolio_breakdown(dataframe: pd.DataFrame) -> None:
    st.subheader("Portfolio Breakdown")
    final_values, net_values, portfolio_breakdown, contributions_breakdown = st.columns(
        [1, 1, 1, 1]
    )

    lisa_balance = dataframe["LISA Balance"].iloc[-1]
    isa_balance = dataframe["ISA Balance"].iloc[-1]
    sipp_balance = dataframe["SIPP Balance"].iloc[-1]
    workplace_balance = dataframe["Workplace Balance"].iloc[-1]
    total_balance = lisa_balance + isa_balance + sipp_balance + workplace_balance

    with final_values:
        st.write("**Final Balances:**")
        st.write("💰 LISA:", f"£{lisa_balance:,.0f} ({lisa_balance/total_balance:.2%})")
        st.write("💳 ISA:", f"£{isa_balance:,.0f} ({isa_balance/total_balance:.2%})")
        st.write("🏦 SIPP:", f"£{sipp_balance:,.0f} ({sipp_balance/total_balance:,.2%})")
        st.write(
            "🏢 Workplace:",
            f"£{workplace_balance:,.0f} ({workplace_balance/total_balance:,.2%})",
        )

    lisa_net = dataframe["LISA Net Contribution"].iloc[-1]
    isa_net = dataframe["ISA Net Contribution"].iloc[-1]
    sipp_net = dataframe["SIPP Net Contribution"].iloc[-1]
    workplace_net = dataframe["Workplace Net Contribution"].iloc[-1]
    total_net = lisa_net + isa_net + sipp_net + workplace_net
    with net_values:
        st.write("**Net Contributions:**")
        st.write("💰 LISA:", f"£{lisa_net:,.0f} ({lisa_net/total_net:.2%})")
        st.write("💳 ISA:", f"£{isa_net:,.0f} ({isa_net/total_net:.2%})")
        st.write("🏦 SIPP:", f"£{sipp_net:,.0f} ({sipp_net/total_net:.2%})")
        st.write(
            "🏢 Workplace:", f"£{workplace_net:,.0f} ({workplace_net/total_net:.2%})"
        )

    with portfolio_breakdown:
        st.write("**Portfolio Breakdown:**")
        breakdown = {
            "LISA": dataframe["LISA Balance"].iloc[-1],
            "ISA": dataframe["ISA Balance"].iloc[-1],
            "Workplace": dataframe["Workplace Balance"].iloc[-1],
            "SIPP": dataframe["SIPP Balance"].iloc[-1],
        }
        st.altair_chart(
            pw.plotting.plot_pie_chart_breakdown(breakdown), use_container_width=True
        )

    with contributions_breakdown:
        st.write("**Net Contributions Breakdown:**")
        breakdown = {
            "LISA": dataframe["LISA Net Contribution"].iloc[-1],
            "ISA": dataframe["ISA Net Contribution"].iloc[-1],
            "Workplace": dataframe["Workplace Net Contribution"].iloc[-1],
            "SIPP": dataframe["SIPP Net Contribution"].iloc[-1],
        }
        st.altair_chart(
            pw.plotting.plot_pie_chart_breakdown(breakdown), use_container_width=True
        )


def _render_annual_salary_and_contributions(dataframe: pd.DataFrame) -> None:
    st.subheader("Annual Salary & Contribution Breakdown")

    option = st.selectbox(
        "Select breakdown year:",
        ("Pre-50 Breakdown", "Post-50 Breakdown"),
        key="breakdown_year_selectbox",
    )

    if option == "Pre-50 Breakdown":
        row = dataframe.iloc[0]
    else:
        post50_rows = dataframe[dataframe["Age"] >= 50]
        if not post50_rows.empty:
            row = post50_rows.iloc[0]
        else:
            row = dataframe.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.write("**Salary Breakdown:**")
        st.write(f"Gross Salary: £{row.get('Salary', 0):,.0f}")
        st.write(f"Take-home: £{row.get('Take Home Salary', 0):,.0f}")
        st.write(f"Income Tax: £{row.get('Income Tax', 0):,.0f}")
        st.write(f"NI Contribution: £{row.get('NI Contribution', 0):,.0f}")
    with col2:
        st.write("**Net Contributions Breakdown:**")
        st.write(f"LISA Net: £{row.get('LISA Net', 0):,.0f}")
        st.write(f"ISA Net: £{row.get('ISA Net', 0):,.0f}")
        st.write(f"SIPP Net: £{row.get('SIPP Net', 0):,.0f}")
        st.write(f"Workplace Net: £{row.get('Workplace EE Net', 0):,.0f}")
        st.write(
            f"Total Net Contribution: £{row.get('Annual Net Contribution', 0):,.0f}"
        )
    with col3:
        st.write("**Others:**")
        st.write(f"LISA Bonus: £{row.get('LISA Bonus', 0):,.0f}")
        st.write(f"Tax Relief £{row.get('Tax Relief', 0):,.0f}")
        st.write(f"Tax Refund: £{row.get('Tax Refund', 0):,.0f}")
        st.write(
            f"Total Gross Contribution: £{row.get('Annual Gross Contribution', 0):,.0f}"
        )
        st.write(
            f"Actual Contribution Cost: £{row.get('Annual Gross Contribution', 0) - row.get('Tax Refund', 0.0):,.0f}"
        )
    with col4:
        breakdown = {
            "Take-home": row.get("Take Home Salary", 0),
            "Income Tax": row.get("Income Tax", 0),
            "NI Contribution": row.get("NI Contribution", 0),
        }
        st.altair_chart(
            pw.plotting.plot_pie_chart_breakdown(breakdown), use_container_width=True
        )


def _render_growth_breakdown(dataframe: pd.DataFrame) -> None:
    st.subheader("Growth Breakdown and Visualisation")
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(
            pw.plotting.plot_annual_contribution_chart(dataframe),
            use_container_width=True,
        )
    with col2:
        st.altair_chart(
            pw.plotting.plot_growth_projection_chart(dataframe),
            use_container_width=True,
        )


def render_pre_retirement_analysis(
    profile_settings: "ProfileSettings", dataframe: pd.DataFrame
) -> None:
    total_initial_balance = (
        profile_settings.account_balances.isa_balance
        + profile_settings.account_balances.lisa_balance
        + profile_settings.account_balances.sipp_balance
        + profile_settings.account_balances.workplace_pension_balance
    )
    _render_portfilio_statistics(dataframe, total_initial_balance)
    _render_annual_salary_and_contributions(dataframe)
    _render_portfolio_breakdown(dataframe)
    dataframe_styled = _style_dataframe(dataframe)
    _render_investment_dataframe(dataframe_styled)
    _render_growth_breakdown(dataframe)
