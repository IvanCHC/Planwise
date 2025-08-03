"""
Streamlit web application for UK Investment & Retirement Planning.

This app provides an interactive interface to the planwise library,
allowing users to model their retirement savings across various UK tax wrappers.
"""

from typing import Any, Tuple

import pandas as pd
import streamlit as st

# Import from our library
import planwise as pw


def sidebar_inputs() -> (
    Tuple[
        "pw.core.UserProfile",
        "pw.core.ContributionRates",
        "pw.core.InvestmentReturns",
        float,
        bool,
        int,
        int,
        int,
    ]
):
    tax_band_db = pw.tax.load_tax_bands_db()
    available_years = sorted(tax_band_db.keys())
    default_year = max(available_years)
    tax_year = st.sidebar.selectbox(
        "Tax year for calculations",
        options=available_years,
        index=available_years.index(default_year),
        format_func=lambda y: f"{y}/{str(y+1)[-2:]}",
    )

    with st.sidebar.expander("Personal Details", expanded=True):
        current_age = st.number_input(
            "Current age",
            min_value=18,
            max_value=74,
            value=30,
            step=1,
            key="current_age",
        )
        retirement_age = st.number_input(
            "Retirement age",
            min_value=current_age + 1,
            max_value=90,
            value=67,
            step=1,
            key="retirement_age",
        )
        salary = st.number_input(
            "Annual salary (£)",
            min_value=1_000.0,
            max_value=1_000_000.0,
            value=40_000.0,
            step=1_000.0,
            key="salary",
        )

    with st.sidebar.expander("Contribution rates (as % of salary)", expanded=True):
        # LISA contribution rate
        lisa_limit = pw.core.LIMITS_DB[str(tax_year)]["lisa_limit"]
        max_lisa_rate = min(lisa_limit / salary, 1.0)
        lisa_rate = st.slider(
            "LISA contribution %",
            0.0,
            max_lisa_rate,
            min(0.05, max_lisa_rate),
            step=0.001,
            key="lisa_rate",
            help=f"Max allowed by LISA limit (£{lisa_limit:,.0f}) and salary",
        )
        if lisa_rate > max_lisa_rate:
            st.warning(
                f"⚠️ The maximum LISA contribution for your salary is {max_lisa_rate:.0%} (£{lisa_limit:,.0f}). "
                "Any value above this will be capped in calculations."
            )

        # ISA contribution rate
        isa_limit = pw.core.LIMITS_DB[str(tax_year)]["isa_limit"]
        lisa_net = salary * lisa_rate
        remaining_isa_allowance = max(isa_limit - lisa_net, 0.0)
        max_isa_rate = min(remaining_isa_allowance / salary, 1.0)
        isa_rate = st.slider(
            "ISA contribution %",
            0.0,
            max_isa_rate,
            min(0.05, max_isa_rate),
            step=0.001,
            key="isa_rate",
            help=f"Max allowed by ISA limit (£{isa_limit:,.0f}) after LISA contributions",
        )
        total_lisa_isa = lisa_rate * salary + isa_rate * salary
        unused_salary = salary - total_lisa_isa

        # Pension contribution rates
        pension_annual_allowance = pw.core.LIMITS_DB[str(tax_year)][
            "pension_annual_allowance"
        ]
        workplace_employer_rate = st.slider(
            "Workplace pension (employer) %",
            0.0,
            1.0,
            0.03,
            step=0.01,
            key="workplace_employer_rate",
            help=f"Max allowed by pension annual allowance (£{pension_annual_allowance:,.0f})",
        )
        unused_allowance = pension_annual_allowance - workplace_employer_rate * salary

        warning_flag = False

        if unused_allowance <= 0:
            st.warning(
                f"⚠️ The maximum pension contribution is capped by the annual allowance (£{pension_annual_allowance:,.0f}). "
            )
            warning_flag = True
            sipp_employer_rate = 0.0
        else:
            max_sipp_employee_rate = unused_allowance / pension_annual_allowance
            sipp_employer_rate = st.slider(
                "SIPP (employer) %",
                0.0,
                max_sipp_employee_rate,
                0.0,
                step=0.01,
                key="sipp_employer_rate",
                help=f"Max allowed by pension annual allowance (£{pension_annual_allowance:,.0f})",
            )
            unused_allowance -= sipp_employer_rate * salary

        if unused_allowance <= 0:
            if not warning_flag:
                st.warning(
                    f"⚠️ The maximum pension contribution is capped by the annual allowance (£{pension_annual_allowance:,.0f}). "
                )
                warning_flag = True
            workplace_employee_rate = 0.0
        else:
            max_workplace_employee_rate = min(
                unused_allowance
                / salary
                / 1.25,  # Tax relief on workplace contributions
                unused_salary / salary,
            )
            workplace_employee_rate = st.slider(
                "Workplace pension (employee) %",
                0.0,
                max_workplace_employee_rate,
                min(0.05, max_workplace_employee_rate),
                step=0.001,
                key="workplace_employee_rate",
                help=f"Max allowed by pension annual allowance (£{pension_annual_allowance:,.0f})",
            )
            unused_salary -= workplace_employee_rate * salary
            unused_allowance -= (
                workplace_employee_rate * salary * 1.25
            )  # Tax relief on workplace contributions

        if unused_allowance <= 0:
            if not warning_flag:
                st.warning(
                    f"⚠️ The maximum pension contribution is capped by the annual allowance (£{pension_annual_allowance:,.0f}). "
                )
                warning_flag = True
            sipp_employee_rate = 0.0
        elif unused_salary <= 0:
            st.warning(
                "⚠️ You have reached the maximum allowed contributions for your salary. "
                "No further contributions can be made to SIPP."
            )
            sipp_employee_rate = 0.0
        else:
            max_sipp_employee_rate = min(
                unused_allowance / salary / 1.25,  # Tax relief on SIPP contributions
                unused_salary / salary,
            )
            sipp_employee_rate = st.slider(
                "SIPP (employee) %",
                0.0,
                max_sipp_employee_rate,
                0.0,
                step=0.001,
                key="sipp_employee_rate",
                help=f"Max allowed by pension annual allowance (£{pension_annual_allowance:,.0f})",
            )

        # Calculate total contribution rate from salary
        total_contrib_rate = (
            lisa_rate + isa_rate + sipp_employee_rate + workplace_employee_rate
        )
        st.progress(
            min(total_contrib_rate, 1.0),
            text=f"Total: {total_contrib_rate:.0%} of salary",
        )

    with st.sidebar.expander("Post-50 LISA redirection", expanded=False):
        st.markdown(
            "*When you reach 50, you can no longer contribute to a LISA. Specify how to redirect those contributions:*"
        )
        shift_lisa_to_isa = st.slider(
            "% of LISA contribution redirected to ISA",
            0.0,
            1.0,
            0.5,
            step=0.05,
            key="shift_lisa_to_isa",
        )
        shift_lisa_to_sipp = 1.0 - shift_lisa_to_isa
        st.write(f"% redirected to SIPP: {shift_lisa_to_sipp:.0%}")

    with st.sidebar.expander("Expected annual returns (nominal)", expanded=False):
        roi_lisa = st.slider("LISA ROI", 0.00, 0.15, 0.05, step=0.01, key="roi_lisa")
        roi_isa = st.slider("ISA ROI", 0.00, 0.15, 0.05, step=0.01, key="roi_isa")
        roi_sipp = st.slider("SIPP ROI", 0.00, 0.15, 0.05, step=0.01, key="roi_sipp")
        roi_workplace = st.slider(
            "Workplace pension ROI", 0.00, 0.15, 0.05, step=0.01, key="roi_workplace"
        )
        inflation = st.slider(
            "Inflation", 0.00, 0.10, 0.02, step=0.005, key="inflation"
        )

    with st.sidebar.expander("Tax Settings", expanded=False):
        scotland = st.checkbox("Scottish taxpayer?", value=False, key="scotland")
        use_qualifying = st.checkbox(
            "Calculate workplace contributions using qualifying earnings band?",
            value=True,
            help="If checked, workplace pension contributions are calculated on qualifying earnings (£6,240–£50,270). Otherwise contributions are based on total salary.",
            key="use_qualifying",
        )

    user = pw.core.UserProfile(
        current_age=current_age,
        retirement_age=retirement_age,
        salary=salary,
        scotland=scotland,
    )
    contrib = pw.core.ContributionRates(
        lisa=lisa_rate,
        isa=isa_rate,
        sipp_employee=sipp_employee_rate,
        sipp_employer=sipp_employer_rate,
        workplace_employee=workplace_employee_rate,
        workplace_employer=workplace_employer_rate,
        shift_lisa_to_isa=shift_lisa_to_isa,
        shift_lisa_to_sipp=shift_lisa_to_sipp,
    )
    returns = pw.core.InvestmentReturns(
        lisa=roi_lisa,
        isa=roi_isa,
        sipp=roi_sipp,
        workplace=roi_workplace,
    )

    return (
        user,
        contrib,
        returns,
        inflation,
        use_qualifying,
        tax_year,
        current_age,
        retirement_age,
    )


def show_summary_metrics(df: pd.DataFrame) -> Tuple[pd.Series, float]:
    final_row = df.iloc[-1]
    total_final = (
        final_row["Pot LISA"]
        + final_row["Pot ISA"]
        + final_row["Pot SIPP"]
        + final_row["Pot Workplace"]
    )
    total_contributions = df["Net Contribution Cost"].sum()

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Final Value", f"£{total_final:,.0f}")
    with col2:
        st.metric("Total Contributions", f"£{total_contributions:,.0f}")
    with col3:
        st.metric("Total Growth", f"£{total_final - total_contributions:,.0f}")
    with col4:
        st.metric(
            "Growth Multiple", f"{total_final / max(total_contributions, 1):.1f}x"
        )

    return final_row, total_final


def show_final_breakdown(final_row: pd.Series, total_final: float) -> None:
    st.subheader("Final Pot Breakdown")
    breakdown_col1, breakdown_col2 = st.columns(2)

    with breakdown_col1:
        st.write("**Final Values:**")
        st.write(f"💰 LISA: £{final_row['Pot LISA']:,.0f}")
        st.write(f"💳 ISA: £{final_row['Pot ISA']:,.0f}")
        st.write(f"🏦 SIPP: £{final_row['Pot SIPP']:,.0f}")
        st.write(f"🏢 Workplace: £{final_row['Pot Workplace']:,.0f}")

    with breakdown_col2:
        # Calculate percentages
        lisa_pct = final_row["Pot LISA"] / total_final * 100 if total_final > 0 else 0
        isa_pct = final_row["Pot ISA"] / total_final * 100 if total_final > 0 else 0
        sipp_pct = final_row["Pot SIPP"] / total_final * 100 if total_final > 0 else 0
        workplace_pct = (
            final_row["Pot Workplace"] / total_final * 100 if total_final > 0 else 0
        )

        st.write("**Percentages:**")
        st.write(f"💰 LISA: {lisa_pct:.1f}%")
        st.write(f"💳 ISA: {isa_pct:.1f}%")
        st.write(f"🏦 SIPP: {sipp_pct:.1f}%")
        st.write(f"🏢 Workplace: {workplace_pct:.1f}%")


def show_data_table(df: pd.DataFrame) -> None:
    st.subheader("Year-by-year projection")
    with st.expander("Show detailed data table"):
        st.dataframe(
            df.style.format(
                {
                    "Salary": "£{:,.0f}",
                    "LISA Net": "£{:,.0f}",
                    "LISA Bonus": "£{:,.0f}",
                    "ISA Net": "£{:,.0f}",
                    "SIPP Employee Net": "£{:,.0f}",
                    "SIPP Employee Gross": "£{:,.0f}",
                    "SIPP Employer": "£{:,.0f}",
                    "Workplace Employee Net": "£{:,.0f}",
                    "Workplace Employee Gross": "£{:,.0f}",
                    "Workplace Employer": "£{:,.0f}",
                    "Tax Relief (total)": "£{:,.0f}",
                    "Tax Refund": "£{:,.0f}",
                    "Net Contribution Cost": "£{:,.0f}",
                    "Pot LISA": "£{:,.0f}",
                    "Pot ISA": "£{:,.0f}",
                    "Pot SIPP": "£{:,.0f}",
                    "Pot Workplace": "£{:,.0f}",
                }
            ),
            use_container_width=True,
        )


def show_visualizations(df: pd.DataFrame) -> None:
    st.subheader("Visualizations")

    try:
        # Try to create charts if altair is available
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Annual Contributions")
            contrib_chart = pw.make_contribution_plot(df)
            st.altair_chart(contrib_chart, use_container_width=True)

        with col2:
            st.subheader("Pot Growth Over Time")
            growth_chart = pw.make_growth_plot(df)
            st.altair_chart(growth_chart, use_container_width=True)

    except ImportError:
        st.warning(
            "Visualization features require the 'altair' package. Install with: pip install 'planwise[plotting]'"
        )
    except Exception as e:
        st.error(f"Error creating visualizations: {e}")


def show_download(df: pd.DataFrame, current_age: int, retirement_age: int) -> None:
    st.subheader("Export Data")
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download projection as CSV",
        data=csv,
        file_name=f"retirement_projection_{current_age}_to_{retirement_age}.csv",
        mime="text/csv",
    )


def show_sidebar_footer() -> None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.markdown(
        """
        This tool models UK retirement savings for the 2025/26 tax year.

        **Key assumptions:**
        - Tax rules remain constant
        - No carry-forward of unused allowances
        - Relief-at-source for pension contributions
        - Government LISA bonus of 25% (max £1,000/year)

        **Not financial advice.** Consult a professional for personalized guidance.
        """
    )


def main() -> None:
    """Main Streamlit application."""
    st.set_page_config(page_title="UK Retirement & Investment Planner", layout="wide")
    st.title("UK Investment & Retirement Planning Model")

    st.markdown(
        """
        Use this tool to project how your investments in a Lifetime ISA (LISA), Stocks & Shares ISA,
        Self-Invested Personal Pension (SIPP) and workplace pension might grow over time. The
        model calculates net and gross contributions, tax relief and refunds, and the nominal
        growth of each wrapper.

        **Remember that this is a simplification and real tax rules may change.
        You should consult a financial adviser for personalised advice.**
        """
    )

    (
        user,
        contrib,
        returns,
        inflation,
        use_qualifying,
        tax_year,
        current_age,
        retirement_age,
    ) = sidebar_inputs()

    try:
        df = pw.project_retirement(
            user=user,
            contrib=contrib,
            returns=returns,
            inflation=inflation,
            use_qualifying_earnings=use_qualifying,
            year=tax_year,
        )

        final_row, total_final = show_summary_metrics(df)
        show_final_breakdown(final_row, total_final)
        show_data_table(df)
        show_visualizations(df)
        show_download(df, current_age, retirement_age)

    except Exception as e:
        st.error(f"Error running projection: {e}")
        st.error("Please check your input parameters and try again.")

    show_sidebar_footer()


if __name__ == "__main__":
    main()
