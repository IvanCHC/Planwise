"""
Streamlit application for UK investment and retirement planning.

This app provides an interactive interface to the planwise library, enabling
users to model the growth of their retirement savings across key UK tax wrappers
(LISA, ISA, SIPP, workplace pension). Users can input personal details, tax
settings, contribution rates, and expected returns to generate projections
and visualizations.

Features:
- Sidebar for collecting user inputs and assumptions
- Pre- and post-retirement analysis with summary metrics, charts, and tables
- Downloadable investment and retirement projections (CSV/Excel)
- Modular UI for maintainability and clarity

Note: This model is a simplification and does not account for carry forward of unused
allowances or all pension tax relief scenarios. For personalised advice, consult a
financial adviser.
"""

import os
from io import BytesIO

import pandas as pd
import streamlit as st
from PIL import Image

import planwise as pw
from planwise.streamlit.post_retirement_analysis import render_post_retirement_analysis
from planwise.streamlit.pre_retirement_analysis import render_pre_retirement_analysis
from planwise.streamlit.sidebar import sidebar_inputs


def download_investment_projection(
    df: pd.DataFrame, current_age: int, retirement_age: int
) -> None:
    st.subheader("Export Data")
    csv = df.to_csv(index=False)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Projection")
    excel_bytes = buf.getvalue()  # raw XLSX bytes

    st.write("Investment projection:")
    col1, col2, _, _ = st.columns([1, 1, 4, 4])
    with col1:
        st.download_button(
            label="as CSV",
            data=csv,
            file_name=f"investment_projection_{current_age}_to_{retirement_age}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            label="as Excel",
            data=excel_bytes,
            file_name=f"investment_projection_{current_age}_to_{retirement_age}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def download_retirement_projection(
    df: pd.DataFrame, current_age: int, retirement_age: int
) -> None:
    st.subheader("Export Data")
    csv = df.to_csv(index=False)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Projection")
    excel_bytes = buf.getvalue()  # raw XLSX bytes

    st.write("Retirement projection:")
    col1, col2, _, _ = st.columns([1, 1, 4, 4])
    with col1:
        st.download_button(
            label="as CSV",
            data=csv,
            file_name=f"retirement_projection_{current_age}_to_{retirement_age}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            label="as Excel",
            data=excel_bytes,
            file_name=f"retirement_projection_{current_age}_to_{retirement_age}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def main() -> None:
    favicon_path = os.path.join("src", "assets", "favicon.ico")
    favicon = Image.open(favicon_path)
    st.set_page_config(page_title="Planwise", page_icon=favicon, layout="wide")
    st.title("Planewise: UK Investment & Retirement Model")

    st.markdown(
        """
        Project the growth of your LISA, ISA, SIPP, and workplace pension over time,
        including contributions, tax relief, and growth.

        **Note: This is a simplified model. Consult a financial adviser for personalised advice.**
        """
    )

    profile_settings = sidebar_inputs()
    investment_dataframe = pw.project_investment(profile_settings)

    pre_retirement_tab, post_retirement_tab = st.tabs(
        [
            "Pre-Retirement Analysis",
            "Post-Retirement Analysis",
        ]
    )
    with pre_retirement_tab:
        render_pre_retirement_analysis(profile_settings, investment_dataframe)
        download_investment_projection(
            investment_dataframe,
            profile_settings.personal_details.current_age,
            profile_settings.personal_details.retirement_age,
        )

    with post_retirement_tab:
        retirement_dataframe = pw.project_retirement(
            profile_settings, investment_dataframe
        )
        if profile_settings.post_retirement_settings.withdrawal_today_amount > 0:
            percentage = (
                profile_settings.post_retirement_settings.postret_isa_targeted_withdrawal_percentage
                + profile_settings.post_retirement_settings.postret_lisa_targeted_withdrawal_percentage
                + profile_settings.post_retirement_settings.postret_taxfree_pension_targeted_withdrawal_percentage
                + profile_settings.post_retirement_settings.postret_taxable_pension_targeted_withdrawal_percentage
            )
            if percentage != 1.0:
                st.warning(
                    f"Targeted withdrawal percentages do not sum to 100%. "
                    f"Current sum is {percentage * 100:.2f}%. "
                    f"Expected to be 100%."
                )
        if not retirement_dataframe.empty:
            render_post_retirement_analysis(profile_settings, retirement_dataframe)
            download_retirement_projection(
                retirement_dataframe,
                profile_settings.personal_details.current_age,
                profile_settings.personal_details.retirement_age,
            )


if __name__ == "__main__":
    main()
