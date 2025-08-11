from typing import Any, Tuple

import pandas as pd
import streamlit as st

import planwise as pw


def _render_portfilio_statistics(dataframe: pd.DataFrame) -> None:
    final_year = dataframe.iloc[-1]
    portfilio_balance = final_year["Portfolio Balance"]
    net_contribution = final_year["Portfolio Net Contribution"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Account Balance", f"£{portfilio_balance:,.0f}")
    with col2:
        st.metric("Total Net Contribution", f"£{net_contribution:,.0f}")
    with col3:
        st.metric("Total Growth", f"£{portfilio_balance - net_contribution:,.0f}")
    with col4:
        st.metric(
            "Growth Multiple", f"{portfilio_balance / max(net_contribution, 1):.1f}x"
        )


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
        }
    )


def _render_investment_dataframe(dataframe: pd.DataFrame.style) -> None:
    st.subheader("Investment year-by-year projection & breakdown")
    with st.expander("View full investment projection"):
        st.dataframe(dataframe, use_container_width=True)


def _render_portfolio_breakdown(dataframe: pd.DataFrame) -> None:
    st.subheader("Portfolio Breakdown")
    final_values, precentage_plot, net_values, stack_bar_plot = st.columns([1, 1, 1, 1])
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
        st.write("**Government Bonus & Tax Relief:**")
        st.write("LISA Bonus:", f"£{dataframe['LISA Bonus'].iloc[0]:.2f}")
        st.write("Pension Tax Relief:", f"£{dataframe['Tax Relief'].iloc[0]:.2f}")
        st.write("Pension Tax Refund:", f"£{dataframe['Tax Refund'].iloc[0]:.2f}")

    with precentage_plot:
        st.write("**Portfolio Breakdown:**")
        breakdown = {
            "LISA": dataframe["LISA Balance"].iloc[-1],
            "ISA": dataframe["ISA Balance"].iloc[-1],
            "Workplace": dataframe["Workplace Balance"].iloc[-1],
            "SIPP": dataframe["SIPP Balance"].iloc[-1],
        }
        st.altair_chart(
            pw.plotting.plot_portfolio_breakdown(breakdown), use_container_width=True
        )


def render_pre_retirement_analysis(dataframe: pd.DataFrame) -> None:
    _render_portfilio_statistics(dataframe)
    _render_portfolio_breakdown(dataframe)
    dataframe_styled = _style_dataframe(dataframe)
    _render_investment_dataframe(dataframe_styled)
