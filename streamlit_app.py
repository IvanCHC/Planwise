"""
Streamlit web application for UK Investment & Retirement Planning.

This app provides an interactive interface to the planwise library,
allowing users to model their retirement savings across various UK tax wrappers.

This module defines a Streamlit application that models UK investment and
retirement planning. The original implementation packed most of the UI logic
into a single function. To improve readability and maintainability, the
application has been refactored into smaller helper functions, each
responsible for a logical section of the user interface. Detailed comments
explain the purpose of each section and important calculations.

The high–level flow is:

1. The sidebar collects user inputs: personal details, tax settings,
   contribution rates, post‑50 LISA redirection, and expected returns.
2. These values are combined to instantiate planwise objects that model
   retirement growth.
3. The main area displays summary metrics, a breakdown of final pot values,
   a detailed data table, charts and a download button.

Keep in mind that this model is a simplification. It does not account for
carry forward of unused allowances and assumes relief at source for pension
contributions.
"""

from typing import Any, Tuple

import pandas as pd
import streamlit as st

# Import from our library
import planwise as pw

# -----------------------------------------------------------------------------
# Sidebar helper functions
#
# The sidebar in this application is broken down into discrete sections for
# collecting user input. Each helper function below is responsible for
# rendering a specific section of the sidebar and returning the relevant
# values. Splitting the UI in this way makes the code easier to follow and
# modify.


def select_tax_year() -> Any:
    """Let the user choose the tax year used for calculations.

    Returns
    -------
    int
        The selected tax year as an integer (e.g. 2024 for the 2024/25 year).

    Notes
    -----
    Planwise stores tax bands and limits keyed by the starting year of the
    fiscal year. The selectbox displays years in the format "YYYY/YY" for
    clarity.
    """
    tax_band_db = pw.tax.load_tax_bands_db()
    available_years = sorted(tax_band_db.keys())
    default_year = max(available_years)
    return st.sidebar.selectbox(
        "Tax year for calculations",
        options=available_years,
        index=available_years.index(default_year),
        format_func=lambda y: f"{y}/{str(y+1)[-2:]}",
    )


def personal_details_section(
    scotland: bool,
) -> Tuple[int, int, float, float, float, float]:
    """Collect personal details such as age and salary from the user, and show take-home pay.

    Returns
    -------
    Tuple[int, int, float, float]
        A tuple containing the current age, retirement age, annual salary, and take-home salary.
    """
    with st.sidebar.expander("Personal Details", expanded=False):
        current_age: int = st.number_input(
            "Current age",
            min_value=18,
            max_value=74,
            value=30,
            step=1,
            key="current_age",
        )
        retirement_age: int = st.number_input(
            "Retirement age",
            min_value=current_age + 1,
            max_value=90,
            value=67,
            step=1,
            key="retirement_age",
        )
        salary: float = st.number_input(
            "Annual salary (£)",
            min_value=1_000.0,
            max_value=1_000_000.0,
            value=40_000.0,
            step=1_000.0,
            key="salary",
        )

        # --- Calculate NI and Tax ---
        # Import here to avoid circular import if planwise uses this app
        tax_year = None
        # Try to get the selected tax year from session state if available
        if "tax_year" in st.session_state:
            tax_year = st.session_state["tax_year"]
        else:
            # Fallback: use latest year in DB
            tax_band_db = pw.tax.load_tax_bands_db()
            tax_year = max(tax_band_db.keys())

        # Assume category A for NI and not Scottish by default
        ni_due = pw.calculate_ni(salary, year=tax_year, category="category_a")
        # Use planwise tax calculation for income tax (not including pension relief)
        # Assume standard personal allowance, not Scottish
        income_tax = pw.calculate_income_tax(salary, year=tax_year, scotland=scotland)

        take_home_salary = salary - ni_due - income_tax
        take_home_pct = take_home_salary / salary if salary > 0 else 0

        st.write(f"**Estimated take-home salary:** £{take_home_salary:,.0f}")
        st.progress(
            min(take_home_pct, 1.0),
            text=f"Take-home: {take_home_pct:.0%} of gross salary",
        )

    return current_age, retirement_age, salary, take_home_salary, ni_due, income_tax


def tax_settings_section(tax_year: int) -> Tuple[bool, bool, float, float, float]:
    """Collect tax‑related settings.

    Parameters
    ----------
    tax_year : int
        The start year of the tax year (e.g. 2024 for 2024/25) used to look up
        qualifying earnings thresholds.

    Returns
    -------
    Tuple[bool, bool, float, float, float]
        A tuple containing:
        - `scotland`: whether the taxpayer is Scottish (affects income tax bands).
        - `use_qualifying`: whether workplace pension contributions use qualifying
          earnings instead of total salary.
        - `qualifying_earnings`: difference between qualifying upper and lower
          bounds.
        - `qualifying_upper`: upper bound for qualifying earnings.
        - `qualifying_lower`: lower bound for qualifying earnings.
    """
    with st.sidebar.expander("Tax Settings", expanded=False):
        scotland: bool = st.checkbox(
            "Scottish taxpayer?",
            value=False,
            key="scotland",
        )
        use_qualifying: bool = st.checkbox(
            "Calculate workplace contributions using qualifying earnings band?",
            value=False,
            help=(
                "If checked, workplace pension contributions are calculated "
                "on qualifying earnings (£6,240–£50,270). Otherwise "
                "contributions are based on total salary."
            ),
            key="use_qualifying",
        )
        # Fetch qualifying thresholds from the limits database for the selected
        # tax year. These are used to compute pension contributions when the
        # qualifying earnings option is selected.
        qualifying_upper = pw.core.LIMITS_DB[str(tax_year)]["qualifying_upper"]
        qualifying_lower = pw.core.LIMITS_DB[str(tax_year)]["qualifying_lower"]
        qualifying_earnings = qualifying_upper - qualifying_lower
    return (
        scotland,
        use_qualifying,
        qualifying_earnings,
        qualifying_upper,
        qualifying_lower,
    )


def contribution_rates_section(
    tax_year: int,
    salary: float,
    use_qualifying: bool,
    qualifying_earnings: float,
    qualifying_upper: float,
    qualifying_lower: float,
) -> Tuple[float, float, float, float, float, float, float, float, float, float,]:
    """Collect contribution rates for each tax wrapper.

    This function handles the complex logic of enforcing annual allowances and
    computing maximum contribution rates for Lifetime ISA (LISA), Stocks & Shares
    ISA, Self‑Invested Personal Pension (SIPP) and workplace pension (employee
    and employer). It returns the chosen rates along with information needed
    for downstream calculations (e.g. unused salary and allowance).

    Parameters
    ----------
    tax_year : int
        The start year of the tax year for looking up contribution limits.
    salary : float
        Annual salary in pounds.
    use_qualifying : bool
        Whether to base workplace pension contributions on qualifying earnings.
    qualifying_earnings : float
        Difference between qualifying upper and lower bounds.
    qualifying_upper : float
        Upper bound of qualifying earnings.
    qualifying_lower : float
        Lower bound of qualifying earnings.

    Returns
    -------
    Tuple
        A tuple containing (in order):
        - `lisa_rate`: fraction of salary contributed to LISA.
        - `isa_rate`: fraction of salary contributed to ISA (after LISA).
        - `sipp_employee_rate`: employee contribution to SIPP (salary %).
        - `sipp_employer_rate`: employer contribution to SIPP (salary %).
        - `workplace_employee_rate`: employee contribution to workplace pension.
        - `workplace_employer_rate`: employer contribution to workplace pension.
        - `unused_allowance`: remaining pension annual allowance after all contributions.
        - `unused_salary`: remaining take‑home salary not allocated to ISA/LISA/pensions.
        - `total_lisa`: actual pound amount contributed to LISA (salary × rate).
        - `total_contrib_rate`: combined contribution rate used to display a progress
          bar in the sidebar.
    """
    with st.sidebar.expander(
        "Contribution rates (as % of take home salary)", expanded=False
    ):
        # --------- LISA contributions ---------
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

        # --------- ISA contributions ---------
        isa_limit = pw.core.LIMITS_DB[str(tax_year)]["isa_limit"]
        # Amount contributed to LISA in pounds
        total_lisa = salary * lisa_rate
        # Remaining ISA allowance after LISA contributions
        remaining_isa_allowance = max(isa_limit - total_lisa, 0.0)
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
        # Keep track of unallocated salary for subsequent pension contributions
        total_lisa_isa = total_lisa + isa_rate * salary
        unused_salary = salary - total_lisa_isa

        # --------- Pension contributions ---------
        pension_annual_allowance = pw.core.LIMITS_DB[str(tax_year)][
            "pension_annual_allowance"
        ]
        # Employer contribution to workplace pension (always allowed on full salary)
        workplace_employer_rate = st.slider(
            "Workplace pension (employer) %",
            0.0,
            1.0,
            0.03,
            step=0.01,
            key="workplace_employer_rate",
            help=f"Max allowed by pension annual allowance (£{pension_annual_allowance:,.0f})",
        )
        # Determine the allowance remaining after employer contributions
        if use_qualifying:
            # Only the portion of salary between qualifying_lower and qualifying_upper is subject to workplace contributions
            salary_factor = (
                salary - qualifying_lower
                if salary < qualifying_upper
                else qualifying_earnings
            )
            unused_allowance = (
                pension_annual_allowance - workplace_employer_rate * salary_factor
            )
        else:
            unused_allowance = (
                pension_annual_allowance - workplace_employer_rate * salary
            )

        warning_flag = False
        # Default values for optional contributions
        sipp_employer_rate = 0.0
        workplace_employee_rate = 0.0
        sipp_employee_rate = 0.0

        # Employer contributions to SIPP (if any)
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
            # Update allowance after employer SIPP contributions
            unused_allowance -= sipp_employer_rate * salary

        # Employee contributions to workplace pension
        if unused_allowance <= 0:
            if not warning_flag:
                st.warning(
                    f"⚠️ The maximum pension contribution is capped by the annual allowance (£{pension_annual_allowance:,.0f}). "
                )
                warning_flag = True
            workplace_employee_rate = 0.0
        else:
            if use_qualifying:
                max_workplace_employee_rate = min(
                    unused_allowance
                    / qualifying_earnings
                    / 1.25,  # Tax relief on workplace contributions
                    unused_salary / salary,
                )
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
            if use_qualifying:
                salary_factor = (
                    salary - qualifying_lower
                    if salary < qualifying_upper
                    else qualifying_earnings
                )
                unused_salary -= workplace_employee_rate * salary_factor
                unused_allowance -= (
                    workplace_employee_rate * salary_factor * 1.25
                )  # Tax relief on workplace contributions
            else:
                unused_salary -= workplace_employee_rate * salary
                unused_allowance -= workplace_employee_rate * salary * 1.25

        # Employee contributions to SIPP
        if unused_allowance <= 0:
            if not warning_flag:
                st.warning(
                    f"⚠️ The maximum pension contribution is capped by the annual allowance (£{pension_annual_allowance:,.0f}). "
                )
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
            # Update unused salary and allowance after SIPP contributions
            unused_salary -= sipp_employee_rate * salary
            unused_allowance -= (
                sipp_employee_rate * salary * 1.25
            )  # Tax relief on SIPP contributions

        # --------- Total contribution progress ---------
        # When using qualifying earnings, the effective contribution rate of
        # workplace employee contributions is scaled down to reflect only the
        # portion of salary above the qualifying lower band. Otherwise use the
        # nominal rate directly.
        if use_qualifying:
            real_workplace_employee_rate = (
                workplace_employee_rate * qualifying_earnings / salary
            )
        else:
            real_workplace_employee_rate = workplace_employee_rate
        total_contrib_rate = (
            lisa_rate + isa_rate + sipp_employee_rate + real_workplace_employee_rate
        )
        st.progress(
            min(total_contrib_rate, 1.0),
            text=f"Total: {total_contrib_rate:.0%} of salary (£{salary:,.0f})",
        )

    # Return all calculated values for further processing in the sidebar
    return (
        lisa_rate,
        isa_rate,
        sipp_employee_rate,
        sipp_employer_rate,
        workplace_employee_rate,
        workplace_employer_rate,
        unused_allowance,
        unused_salary,
        total_lisa,
        total_contrib_rate,
    )


def post50_lisa_section(
    total_lisa: float, unused_allowance: float
) -> Tuple[float, float]:
    """Collect post‑50 redirection preferences for LISA contributions.

    Lifetime ISA contributions are only allowed until the age of 50. When the user
    reaches this age, they may choose to divert those contributions into their
    ISA or SIPP. This function captures that preference.

    Parameters
    ----------
    total_lisa : float
        The total LISA contribution in pounds (salary × lisa_rate).
    unused_allowance : float
        Remaining pension annual allowance after contributions, used to
        determine if the user must redirect their entire LISA contribution to
        the ISA.

    Returns
    -------
    Tuple[float, float]
        A tuple containing (shift_lisa_to_isa, shift_lisa_to_sipp), where
        shift_lisa_to_isa is the fraction of the LISA contribution redirected
        to an ISA once the user turns 50, and shift_lisa_to_sipp is the
        remainder redirected to a SIPP.
    """
    with st.sidebar.expander("Post-50 LISA redirection", expanded=False):
        # Determine the minimum portion of LISA that must be directed to ISA to
        # avoid exceeding the pension annual allowance
        if unused_allowance < total_lisa:
            minimum_directable_lisa = (total_lisa - unused_allowance) / total_lisa
        else:
            minimum_directable_lisa = 0.0
        st.markdown(
            "*When you reach 50, you can no longer contribute to a LISA. "
            "Specify how to redirect those contributions:*"
        )
        if minimum_directable_lisa == 1.0:
            # User must redirect the entire LISA contribution to ISA
            st.warning(
                "⚠️ You must redirect 100% of LISA contributions to ISA, maximum pension contribution is capped by the annual allowance."
            )
            shift_lisa_to_isa = 1.0
        else:
            shift_lisa_to_isa = st.slider(
                "% of LISA contribution redirected to ISA",
                minimum_directable_lisa,
                1.0,
                1.0,
                step=0.05,
                key="shift_lisa_to_isa",
            )
        shift_lisa_to_sipp = 1.0 - shift_lisa_to_isa
        st.write(f"% redirected to SIPP: {shift_lisa_to_sipp:.0%}")
    return shift_lisa_to_isa, shift_lisa_to_sipp


def returns_section() -> Tuple[float, float, float, float, float]:
    """Collect expected annual return rates and inflation.

    Returns
    -------
    Tuple[float, float, float, float, float]
        A tuple containing ROI for LISA, ISA, SIPP, workplace pension and
        inflation (all nominal).
    """
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
    return roi_lisa, roi_isa, roi_sipp, roi_workplace, inflation


def sidebar_inputs() -> (
    Tuple[
        "pw.core.UserProfile",
        "pw.core.ContributionRates",
        "pw.core.InvestmentReturns",
        "pw.core.IncomeBreakdown",
        float,
        bool,
        int,
        int,
        int,
    ]
):
    """Gather all user inputs from the sidebar.

    This orchestrates calls to the helper functions defined above. It
    constructs the planwise UserProfile, ContributionRates and InvestmentReturns
    objects, and returns them along with inflation and other values needed for
    downstream projections.
    """
    # Step 1: tax year selection
    tax_year = select_tax_year()
    # Step 2: tax settings
    (
        scotland,
        use_qualifying,
        qualifying_earnings,
        qualifying_upper,
        qualifying_lower,
    ) = tax_settings_section(tax_year)
    # Step 3: personal details
    (
        current_age,
        retirement_age,
        salary,
        take_home_salary,
        ni_due,
        income_tax,
    ) = personal_details_section(scotland)
    # Step 4: contribution rates
    (
        lisa_rate,
        isa_rate,
        sipp_employee_rate,
        sipp_employer_rate,
        workplace_employee_rate,
        workplace_employer_rate,
        unused_allowance,
        unused_salary,
        total_lisa,
        _total_contrib_rate,
    ) = contribution_rates_section(
        tax_year,
        take_home_salary,
        use_qualifying,
        qualifying_earnings,
        qualifying_upper,
        qualifying_lower,
    )
    # Step 5: post‑50 LISA redirection
    shift_lisa_to_isa, shift_lisa_to_sipp = post50_lisa_section(
        total_lisa, unused_allowance
    )
    # Step 6: expected returns & inflation
    roi_lisa, roi_isa, roi_sipp, roi_workplace, inflation = returns_section()

    # Construct planwise objects based on the collected values
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
    income = pw.core.IncomeBreakdown(
        salary=salary,
        take_home_salary=take_home_salary,
        ni_due=ni_due,
        income_tax=income_tax,
    )

    return (
        user,
        contrib,
        returns,
        income,
        inflation,
        use_qualifying,
        tax_year,
        current_age,
        retirement_age,
    )


def show_summary_metrics(df: pd.DataFrame) -> Tuple[pd.Series, float]:
    """Display high‑level summary metrics in the main area.

    Given the projection dataframe produced by planwise, this function
    calculates the final value of each pot, total contributions made and
    displays these as Streamlit metrics. It returns the final row of the
    dataframe (containing end balances) and the aggregate final value for
    further use.

    Parameters
    ----------
    df : pd.DataFrame
        The retirement projection dataframe returned by planwise.

    Returns
    -------
    Tuple[pd.Series, float]
        The final row of the dataframe and the total final pot value.
    """
    final_row = df.iloc[-1]
    total_final = (
        final_row["Pot LISA"]
        + final_row["Pot ISA"]
        + final_row["Pot SIPP"]
        + final_row["Pot Workplace"]
    )
    total_contributions = df["Net Contribution Cost"].sum()

    # Display key metrics in four columns
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
    """Show a detailed breakdown of final pot values and percentages.

    Parameters
    ----------
    final_row : pd.Series
        The last row of the projection dataframe containing pot balances.
    total_final : float
        The sum of all pots at the end of the projection period.
    """
    st.subheader("Final Pot Breakdown")
    breakdown_col1, breakdown_col2, breakdown_col3, breakdown_col4 = st.columns(4)

    with breakdown_col1:
        st.write("**Final Values:**")
        st.write(f"💰 LISA: £{final_row['Pot LISA']:,.0f}")
        st.write(f"💳 ISA: £{final_row['Pot ISA']:,.0f}")
        st.write(f"🏦 SIPP: £{final_row['Pot SIPP']:,.0f}")
        st.write(f"🏢 Workplace: £{final_row['Pot Workplace']:,.0f}")

    with breakdown_col2:
        # Calculate percentages relative to the total final value. Guard against
        # division by zero if total_final is zero (though this scenario is unlikely).
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

    with breakdown_col3:
        st.write("**Total Gross Contribution:**")
        st.write(f"💰 LISA: £{final_row['Accumulated LISA Gross']:,.0f}")
        st.write(f"💳 ISA: £{final_row['Accumulated ISA Gross']:,.0f}")
        st.write(f"🏦 SIPP: £{final_row['Accumulated SIPP Gross']:,.0f}")
        st.write(f"🏢 Workplace: £{final_row['Accumulated Workplace Gross']:,.0f}")

    with breakdown_col4:
        st.write("**Total Net Contribution:**")
        st.write(f"💰 LISA: £{final_row['Accumulated LISA Net']:,.0f}")
        st.write(f"💳 ISA: £{final_row['Accumulated ISA Net']:,.0f}")
        st.write(f"🏦 SIPP: £{final_row['Accumulated SIPP Net']:,.0f}")
        st.write(f"🏢 Workplace: £{final_row['Accumulated Workplace Net']:,.0f}")


def show_data_table(df: pd.DataFrame) -> None:
    """Display the projection dataframe in an expandable table.

    Each monetary column is formatted with pound signs and commas for readability.
    The table is placed inside an expander to avoid overwhelming the user
    interface unless they wish to explore the year‑by‑year details.

    Parameters
    ----------
    df : pd.DataFrame
        Projection results from planwise.
    """
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
                    # New accumulated columns
                    "Accumulated LISA Net": "£{:,.0f}",
                    "Accumulated LISA Gross": "£{:,.0f}",
                    "Accumulated ISA Net": "£{:,.0f}",
                    "Accumulated ISA Gross": "£{:,.0f}",
                    "Accumulated SIPP Net": "£{:,.0f}",
                    "Accumulated SIPP Gross": "£{:,.0f}",
                    "Accumulated Workplace Net": "£{:,.0f}",
                    "Accumulated Workplace Gross": "£{:,.0f}",
                }
            ),
            use_container_width=True,
        )


def show_visualizations(df: pd.DataFrame) -> None:
    """Render contribution and growth charts.

    If the optional 'altair' dependency is available (as part of
    planwise[plotting]), this function uses planwise helper functions to create
    Altair charts for annual contributions and pot growth over time. Otherwise,
    it displays a warning instructing the user how to enable charting.

    Parameters
    ----------
    df : pd.DataFrame
        Projection results from planwise.
    """
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
    """Offer a download button for the projection data.

    Parameters
    ----------
    df : pd.DataFrame
        Projection results to be exported.
    current_age : int
        User's current age used in the filename.
    retirement_age : int
        User's retirement age used in the filename.
    """
    st.subheader("Export Data")
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download projection as CSV",
        data=csv,
        file_name=f"retirement_projection_{current_age}_to_{retirement_age}.csv",
        mime="text/csv",
    )


def show_sidebar_footer() -> None:
    """Display informational text at the bottom of the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.markdown(
        """
        This tool models UK retirement savings.

        **Key assumptions:**
        - No carry-forward of unused allowances
        - Relief-at-source for pension contributions
        - Government LISA bonus of 25% (max £1,000/year)
        """
    )


def main() -> None:
    """Entry point for the Streamlit app.

    This function sets up the page configuration, renders the introductory
    explanatory text, collects user inputs via the sidebar and then runs the
    retirement projection. Results are displayed using helper functions. Any
    errors during projection are caught and displayed to the user.
    """
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
        income,
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
