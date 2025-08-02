"""
Streamlit web application for UK Investment & Retirement Planning.

This app provides an interactive interface to the planwise library,
allowing users to model their retirement savings across various UK tax wrappers.
"""

import pandas as pd
import streamlit as st

# Import from our library
import planwise as fp


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

    # Sidebar inputs
    st.sidebar.header("Personal Details")
    current_age = st.sidebar.number_input(
        "Current age", min_value=18, max_value=74, value=30, step=1
    )
    retirement_age = st.sidebar.number_input(
        "Retirement age", min_value=current_age + 1, max_value=90, value=67, step=1
    )
    salary = st.sidebar.number_input(
        "Annual salary (£)",
        min_value=1_000.0,
        max_value=1_000_000.0,
        value=40_000.0,
        step=1_000.0,
    )

    st.sidebar.subheader("Contribution rates (as % of salary)")
    lisa_rate = st.sidebar.slider("LISA contribution %", 0.0, 0.20, 0.05, step=0.01)
    isa_rate = st.sidebar.slider("ISA contribution %", 0.0, 0.20, 0.05, step=0.01)
    sipp_employee_rate = st.sidebar.slider(
        "SIPP (employee) %", 0.0, 0.30, 0.05, step=0.01
    )
    sipp_employer_rate = st.sidebar.slider(
        "SIPP (employer) %", 0.0, 0.30, 0.0, step=0.01
    )
    workplace_employee_rate = st.sidebar.slider(
        "Workplace pension (employee) %", 0.0, 0.30, 0.05, step=0.01
    )
    workplace_employer_rate = st.sidebar.slider(
        "Workplace pension (employer) %", 0.0, 0.30, 0.03, step=0.01
    )

    st.sidebar.subheader("Post-50 LISA redirection")
    st.sidebar.markdown(
        "*When you reach 50, you can no longer contribute to a LISA. Specify how to redirect those contributions:*"
    )
    shift_lisa_to_isa = st.sidebar.slider(
        "% of LISA contribution redirected to ISA", 0.0, 1.0, 0.5, step=0.05
    )
    shift_lisa_to_sipp = 1.0 - shift_lisa_to_isa
    st.sidebar.write(f"% redirected to SIPP: {shift_lisa_to_sipp:.0%}")

    st.sidebar.subheader("Expected annual returns (nominal)")
    roi_lisa = st.sidebar.slider("LISA ROI", 0.00, 0.15, 0.05, step=0.01)
    roi_isa = st.sidebar.slider("ISA ROI", 0.00, 0.15, 0.05, step=0.01)
    roi_sipp = st.sidebar.slider("SIPP ROI", 0.00, 0.15, 0.05, step=0.01)
    roi_workplace = st.sidebar.slider(
        "Workplace pension ROI", 0.00, 0.15, 0.05, step=0.01
    )
    inflation = st.sidebar.slider("Inflation", 0.00, 0.10, 0.02, step=0.005)

    st.sidebar.subheader("Tax Settings")
    scotland = st.sidebar.checkbox("Scottish taxpayer?", value=False)
    use_qualifying = st.sidebar.checkbox(
        "Calculate workplace contributions using qualifying earnings band?",
        value=True,
        help="If checked, workplace pension contributions are calculated on qualifying earnings (£6,240–£50,270). Otherwise contributions are based on total salary.",
    )

    # Run model using our library
    try:
        df = fp.project_retirement(
            current_age=current_age,
            retirement_age=retirement_age,
            salary=salary,
            lisa_contrib_rate=lisa_rate,
            isa_contrib_rate=isa_rate,
            sipp_employee_rate=sipp_employee_rate,
            sipp_employer_rate=sipp_employer_rate,
            workplace_employee_rate=workplace_employee_rate,
            workplace_employer_rate=workplace_employer_rate,
            shift_lisa_to_isa=shift_lisa_to_isa,
            shift_lisa_to_sipp=shift_lisa_to_sipp,
            roi_lisa=roi_lisa,
            roi_isa=roi_isa,
            roi_sipp=roi_sipp,
            roi_workplace=roi_workplace,
            inflation=inflation,
            scotland=scotland,
            use_qualifying_earnings=use_qualifying,
        )

        # Summary metrics
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

        # Breakdown by pot type
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
            lisa_pct = (
                final_row["Pot LISA"] / total_final * 100 if total_final > 0 else 0
            )
            isa_pct = final_row["Pot ISA"] / total_final * 100 if total_final > 0 else 0
            sipp_pct = (
                final_row["Pot SIPP"] / total_final * 100 if total_final > 0 else 0
            )
            workplace_pct = (
                final_row["Pot Workplace"] / total_final * 100 if total_final > 0 else 0
            )

            st.write("**Percentages:**")
            st.write(f"💰 LISA: {lisa_pct:.1f}%")
            st.write(f"💳 ISA: {isa_pct:.1f}%")
            st.write(f"🏦 SIPP: {sipp_pct:.1f}%")
            st.write(f"🏢 Workplace: {workplace_pct:.1f}%")

        # Year-by-year data table
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

        # Visualizations
        st.subheader("Visualizations")

        try:
            # Try to create charts if altair is available
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Annual Contributions")
                contrib_chart = fp.make_contribution_plot(df)
                st.altair_chart(contrib_chart, use_container_width=True)

            with col2:
                st.subheader("Pot Growth Over Time")
                growth_chart = fp.make_growth_plot(df)
                st.altair_chart(growth_chart, use_container_width=True)

        except ImportError:
            st.warning(
                "Visualization features require the 'altair' package. Install with: pip install 'financial-planner[plotting]'"
            )
        except Exception as e:
            st.error(f"Error creating visualizations: {e}")

        # Download data
        st.subheader("Export Data")
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download projection as CSV",
            data=csv,
            file_name=f"retirement_projection_{current_age}_to_{retirement_age}.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"Error running projection: {e}")
        st.error("Please check your input parameters and try again.")

    # Information footer
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


if __name__ == "__main__":
    main()
