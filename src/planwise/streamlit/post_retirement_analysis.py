import pandas as pd
import streamlit as st

import planwise as pw
from planwise.streamlit.sidebar_utils import ProfileSettings


def _render_retirement_summary(dataframe: pd.DataFrame) -> None:
    st.warning(
        "Post-retirement projections use today's money, adjusting withdrawals and contributions for inflation. "
        "State Pension is assumed to rise with inflation (triple lock ignored)."
    )


def _render_retirement_dataframe(dataframe: pd.DataFrame) -> None:
    st.subheader("Retirement year-by-year projection & breakdown")
    with st.expander("View full retirement projection"):
        st.dataframe(_style_dataframe(dataframe), use_container_width=True)


def _style_dataframe(df: pd.DataFrame) -> pd.DataFrame.style:
    return df.style.format(
        {
            "Withdrawal Today": "£{:,.0f}",
            "Withdrawal Inflation Adjusted": "£{:,.0f}",
            "Withdrawal State Pension Today": "£{:,.0f}",
            "Withdrawal State Pension Inflation Adjusted": "£{:,.0f}",
            "Withdrawal LISA Today": "£{:,.0f}",
            "Withdrawal LISA Inflation Adjusted": "£{:,.0f}",
            "Withdrawal ISA Today": "£{:,.0f}",
            "Withdrawal ISA Inflation Adjusted": "£{:,.0f}",
            "Withdrawal Tax-Free Pension Today": "£{:,.0f}",
            "Withdrawal Tax-Free Pension Inflation Adjusted": "£{:,.0f}",
            "Withdrawal Taxable Pension Today": "£{:,.0f}",
            "Withdrawal Taxable Pension Inflation Adjusted": "£{:,.0f}",
            "Income Tax Today": "£{:,.0f}",
            "Income Tax Inflation Adjusted": "£{:,.0f}",
            "Total Withdrawal Today": "£{:,.0f}",
            "Total Withdrawal Inflation Adjusted": "£{:,.0f}",
            "Total Withdrawal After Tax Today": "£{:,.0f}",
            "Total Withdrawal After Tax Inflation Adjusted": "£{:,.0f}",
            "Withdrawal Shortfall Today": "£{:,.0f}",
            "Withdrawal Shortfall Inflation Adjusted": "£{:,.0f}",
            "LISA Balance Today": "£{:,.0f}",
            "LISA Balance Inflation Adjusted": "£{:,.0f}",
            "ISA Balance Today": "£{:,.0f}",
            "ISA Balance Inflation Adjusted": "£{:,.0f}",
            "Tax-Free Pension Balance Today": "£{:,.0f}",
            "Tax-Free Pension Balance Inflation Adjusted": "£{:,.0f}",
            "Taxable Pension Balance Today": "£{:,.0f}",
            "Taxable Pension Balance Inflation Adjusted": "£{:,.0f}",
            "Pension Balance Today": "£{:,.0f}",
            "Pension Balance Inflation Adjusted": "£{:,.0f}",
        }
    )


def _render_withdrawal_breakdown(dataframe: pd.DataFrame) -> None:
    st.subheader("Withdrawal Breakdown")
    todays_tab, inflation_adjusted_tab = st.columns(2)
    with todays_tab:
        st.altair_chart(
            pw.plotting.plot_withdrawals_by_account_chart(dataframe, "Today"),
            use_container_width=True,
        )
        st.altair_chart(
            pw.plotting.plot_total_withdrawals_chart(dataframe, "Today"),
            use_container_width=True,
        )
        st.altair_chart(
            pw.plotting.plot_balances_by_account_chart(dataframe, "Today"),
            use_container_width=True,
        )
        st.altair_chart(
            pw.plotting.plot_total_balance_chart(dataframe, "Today"),
            use_container_width=True,
        )

    with inflation_adjusted_tab:
        st.altair_chart(
            pw.plotting.plot_withdrawals_by_account_chart(
                dataframe, "Inflation Adjusted"
            ),
            use_container_width=True,
        )
        st.altair_chart(
            pw.plotting.plot_total_withdrawals_chart(dataframe, "Inflation Adjusted"),
            use_container_width=True,
        )
        st.altair_chart(
            pw.plotting.plot_balances_by_account_chart(dataframe, "Inflation Adjusted"),
            use_container_width=True,
        )
        st.altair_chart(
            pw.plotting.plot_total_balance_chart(dataframe, "Inflation Adjusted"),
            use_container_width=True,
        )


def render_post_retirement_analysis(
    profile_setting: "ProfileSettings", retirement_dataframe: pd.DataFrame
) -> None:
    _render_retirement_summary(retirement_dataframe)
    _render_retirement_dataframe(retirement_dataframe)
    _render_withdrawal_breakdown(retirement_dataframe)
