"""
This module provides utility functions for configuring the Streamlit sidebar
in the Planwise application.
"""

import os
from typing import Any, Tuple

import streamlit as st

import planwise as pw
from planwise.profile import (
    AccountBalances,
    ContributionSettings,
    ExpectedReturnsAndInflation,
    PersonalDetails,
    Post50ContributionSettings,
    PostRetirementSettings,
    ProfileSettings,
    QualifyingEarnings,
    get_qualifying_earnings_info,
)

from .sidebar_utils import (
    isa_contribution_rate,
    lisa_contribution_rate,
    sipp_contribution_rate,
    workplace_ee_contribution_rate,
    workplace_er_contribution_rate,
)


def _logo_section() -> None:
    """
    Display the Planwise logo at the top of the sidebar.
    """
    logo_path = os.path.join(pw.SRC_DIR, "assets", "logo.png")
    st.sidebar.image(logo_path, use_container_width=True)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown(
            "[<div style='text-align: center;'>View on GitHub</div>]"
            "(https://github.com/IvanCHC/Planwise)",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            "[<div style='text-align: center;'>:coffee: Buy me a Coffee</div>]"
            "(https://planwise.readthedocs.io/en/latest/)",
            unsafe_allow_html=True,
        )


def _tax_year_selectbox() -> Any:
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
    tax_band_db = pw.TAX_BANDS_DB
    available_years = sorted(tax_band_db.keys())
    default_year = max(available_years)
    return st.sidebar.selectbox(
        "Tax Year for Calculations",
        options=available_years,
        index=available_years.index(default_year),
        format_func=lambda y: f"{y}/{str(y+1)[-2:]}",
    )


def _tax_settings_section() -> Tuple[bool, bool]:
    """Configure tax settings in the sidebar, including Scottish taxpayer status
    and whether to use qualifying earnings for workplace pension contributions.

    Returns
    -------
    Tuple[bool, bool, float, float, float]
        A tuple containing:
        - `scotland`: whether the taxpayer is Scottish (affects income tax bands).
        - `use_qualifying`: whether workplace pension contributions use qualifying
          earnings instead of total salary.
    """
    with st.sidebar.expander("Tax Settings", expanded=False):
        scotland: bool = st.checkbox(
            "Scottish taxpayer?",
            value=False,
            help=("Scottish taxpayers have different income tax bands."),
            key="scotland",
        )
        use_qualifying: bool = st.checkbox(
            "Use qualifying earnings for workplace contributions?",
            value=False,
            help="If checked, contributions use qualifying earnings (£6,240–£50,270); otherwise, total salary.",
            key="use_qualifying",
        )
    return (
        scotland,
        use_qualifying,
    )


def _personal_details_section(
    tax_year: int,
    scotland: bool,
) -> "PersonalDetails":
    """Collect personal details such as age and salary from the user, and calculate
    estimated take-home salary, National Insurance contributions, and income tax.

    Parameters
    ----------
    scotland : bool
        Whether the user is a Scottish taxpayer (affects income tax bands).

    Returns
    -------
    PersonalDetails
        A dataclass instance containing the user's personal details and calculated
        financial figures.
    """
    with st.sidebar.expander("Personal Details", expanded=False):
        current_age: int = st.number_input(
            "Current age",
            min_value=18,
            max_value=74,
            value=25,
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

        # Assume category A for NI
        ni_contribution = pw.calculate_ni(salary, year=tax_year, category="category_a")

        income_tax = pw.calculate_income_tax(salary, year=tax_year, scotland=scotland)
        take_home_salary = salary - ni_contribution - income_tax
        take_home_pct = take_home_salary / salary if salary > 0 else 0
        st.write(f"**Estimated take-home salary:** £{take_home_salary:,.0f}")
        st.progress(
            min(take_home_pct, 1.0),
            text=f"Take-home salary: {take_home_pct:.1%} of gross salary",
        )

    personal_details = PersonalDetails(
        current_age=current_age,
        retirement_age=retirement_age,
        salary=salary,
        take_home_salary=take_home_salary,
        ni_contribution=ni_contribution,
        income_tax=income_tax,
    )
    return personal_details


def _contribution_rates_section(
    tax_year: int,
    personal_details: "PersonalDetails",
    qualifying_earnings: "QualifyingEarnings",
) -> "ContributionSettings":
    """Collect contribution rates for each tax wrapper based on user inputs.

    This function handles the complex logic of enforcing annual allowances and
    computing maximum contribution rates for Lifetime ISA (LISA), Stocks & Shares
    ISA, Self-Invested Personal Pension (SIPP) and workplace pension (employee
    and employer). It returns the chosen rates along with information needed
    for downstream calculations (e.g. unused salary and allowance).

    Parameters
    ----------
    tax_year : int
        The start year of the tax year for looking up contribution limits.
    personal_details : PersonalDetails
        A dataclass instance containing the user's personal details and calculated
        financial figures.
    qualifying_earnings : QualifyingEarnings
        A dataclass instance containing qualifying earnings information.

    Returns
    -------
    ContributionSettings
        A dataclass instance containing the contribution rates and other settings.
    """
    with st.sidebar.expander("Contribution Settings", expanded=False):
        with st.container(horizontal_alignment="right"):
            use_exact_amount = st.toggle(
                "Input exact amount?", value=False, key="use_exact_amount"
            )

        total_net_contribution = 0.0

        with st.expander("Step 1. Workplace Contributions", expanded=False):
            if (
                qualifying_earnings.use_qualifying_earnings
                and personal_details.salary <= qualifying_earnings.qualifying_lower
            ):
                st.warning(
                    "⚠️ Your salary is below the qualifying earnings threshold. "
                    "No workplace pension contributions can be made."
                )
                workplace_er_rate, workplace_er_contribution = 0.0, 0.0
                workplace_ee_rate, workplace_ee_contribution = 0.0, 0.0
            else:
                (
                    workplace_er_rate,
                    workplace_er_contribution,
                ) = workplace_er_contribution_rate(
                    tax_year,
                    personal_details,
                    qualifying_earnings,
                    use_exact_amount,
                )
                (
                    workplace_ee_rate,
                    workplace_ee_contribution,
                ) = workplace_ee_contribution_rate(
                    tax_year,
                    personal_details,
                    workplace_er_contribution,
                    qualifying_earnings,
                    use_exact_amount,
                )
                total_workplace_contribution = (
                    workplace_er_contribution + workplace_ee_contribution * 1.25
                )  # 25% tax relief on employee contributions
                allowance_usage = (
                    total_workplace_contribution
                    / pw.LIMITS_DB[str(tax_year)]["pension_annual_allowance"]
                )
                st.progress(
                    allowance_usage,
                    text=f"Pension Allowance Usage: £{total_workplace_contribution:.0f} ({allowance_usage*100:.3f}%)",
                )
                fund_usage = (
                    workplace_ee_contribution / personal_details.take_home_salary
                )
                st.progress(
                    fund_usage,
                    text=f"Fund Usage: £{workplace_ee_contribution:.0f} ({fund_usage*100:.3f}%)",
                )
                total_net_contribution += workplace_ee_contribution

        with st.expander("Step 2. LISA & ISA Contribution", expanded=False):
            if personal_details.take_home_salary - total_net_contribution <= 0:
                st.warning(
                    "⚠️ You have insufficient take-home salary to contribute to LISA or ISA."
                )
                lisa_rate, lisa_contribution = 0.0, 0.0
                isa_rate, isa_contribution = 0.0, 0.0
            else:
                lisa_rate, lisa_contribution = lisa_contribution_rate(
                    tax_year,
                    personal_details.take_home_salary,
                    total_net_contribution,
                    use_exact_amount,
                )
                isa_rate, isa_contribution = isa_contribution_rate(
                    tax_year,
                    personal_details.take_home_salary,
                    lisa_contribution,
                    total_net_contribution,
                    use_exact_amount,
                )
                total_isa_contribution = lisa_contribution + isa_contribution
                total_net_contribution += total_isa_contribution
                allowance_usage = (
                    total_isa_contribution / pw.LIMITS_DB[str(tax_year)]["isa_limit"]
                )
                st.progress(
                    allowance_usage,
                    text=f"ISA/LISA Allowance Usage: {allowance_usage*100:.3f}%",
                )
                fund_usage = total_net_contribution / personal_details.take_home_salary
                st.progress(
                    fund_usage,
                    text=f"Fund Usage: £{total_net_contribution:.0f} ({fund_usage*100:.3f}%)",
                )

        with st.expander("Step 3. SIPP Contributions", expanded=False):
            if personal_details.take_home_salary - total_net_contribution <= 0:
                st.warning(
                    "⚠️ You have insufficient take-home salary to contribute to SIPP."
                )
                sipp_rate, sipp_contribution = 0.0, 0.0
            else:
                sipp_rate, sipp_contribution = sipp_contribution_rate(
                    tax_year,
                    personal_details,
                    total_workplace_contribution,
                    total_net_contribution,
                    use_exact_amount,
                )
                total_sipp_contribution = (
                    sipp_contribution * 1.25
                )  # 25% tax relief on employee contributions
                total_net_contribution += sipp_contribution
                total_pension_contribution = (
                    total_workplace_contribution + total_sipp_contribution
                )
                allowance_usage = (
                    total_pension_contribution
                    / pw.LIMITS_DB[str(tax_year)]["pension_annual_allowance"]
                )
                st.progress(
                    allowance_usage,
                    text=f"Pension Allowance Usage: {allowance_usage*100:.3f}%",
                )
                fund_usage = total_net_contribution / personal_details.take_home_salary
                st.progress(
                    fund_usage,
                    text=f"Fund Usage: £{total_net_contribution:.0f} ({fund_usage*100:.3f}%)",
                )

        contribution_settings = ContributionSettings(
            workplace_er_rate=workplace_er_rate,
            workplace_er_contribution=workplace_er_contribution,
            workplace_ee_rate=workplace_ee_rate,
            workplace_ee_contribution=workplace_ee_contribution,
            lisa_rate=lisa_rate,
            lisa_contribution=lisa_contribution,
            isa_rate=isa_rate,
            isa_contribution=isa_contribution,
            sipp_rate=sipp_rate,
            sipp_contribution=sipp_contribution,
            total_net_contribution=total_net_contribution,
            total_workplace_contribution=total_workplace_contribution,
            total_sipp_contribution=total_sipp_contribution,
            total_isa_contribution=total_isa_contribution,
            total_pension_contribution=total_pension_contribution,
        )
        return contribution_settings


def _account_balances_section() -> "AccountBalances":
    with st.sidebar.expander("Account Balances", expanded=False):
        lisa_balance = st.number_input(
            "LISA Balance (£)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="lisa_balance",
        )
        isa_balance = st.number_input(
            "ISA Balance (£)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="isa_balance",
        )
        sipp_balance = st.number_input(
            "SIPP Balance (£)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="sipp_balance",
        )
        workpace_pension_balance = st.number_input(
            "Workplace Pension Balance (£)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="workplace_balance",
        )
    return AccountBalances(
        lisa_balance=lisa_balance,
        isa_balance=isa_balance,
        sipp_balance=sipp_balance,
        workplace_pension_balance=workpace_pension_balance,
    )


def _post50_lisa_section(
    tax_year: int, contribution_settings: "ContributionSettings"
) -> "Post50ContributionSettings":
    """Collect post-50 redirection preferences for LISA contributions.

    Lifetime ISA contributions are only allowed until the age of 50. When the user
    reaches this age, they may choose to divert those contributions into their
    ISA or SIPP. This function captures that preference.

    Parameters
    ----------
    tax_year : int
        The tax year for which the contribution is being calculated.
    contribution_settings : ContributionSettings
        The current contribution settings including LISA contributions.

    Returns
    -------
    Post50ContributionSettings
        A dataclass instance containing the post-50 LISA redirection settings.
    """
    with st.sidebar.expander("Post-50 LISA Redirection", expanded=False):
        with st.container(horizontal_alignment="right"):
            use_exact_amount = st.toggle(
                "Input exact amount?", value=False, key="use_exact_amount_post50"
            )

        pension_allowance = pw.LIMITS_DB[str(tax_year)]["pension_annual_allowance"]
        if contribution_settings.total_pension_contribution >= pension_allowance:
            st.warning(
                "⚠️ You have already reached the annual pension allowance. "
                "You can only redirect LISA contributions to ISA."
            )
            shift_lisa_to_isa = 1.0
            shift_lisa_to_sipp = 0.0
            redirectable_to_isa = contribution_settings.lisa_contribution
            redirectable_to_sipp = 0.0
        else:
            lisa_contribution = contribution_settings.lisa_contribution
            unused_allowance = (
                pension_allowance - contribution_settings.total_pension_contribution
            )
            if not use_exact_amount:
                minimum_lisa_redirectable = max(
                    (
                        (1 - (unused_allowance / lisa_contribution))
                        if lisa_contribution > unused_allowance
                        else 0.0
                    ),
                    0.0,
                )
                shift_lisa_to_isa = st.slider(
                    "Redirect LISA contribution to ISA (%)",
                    minimum_lisa_redirectable,
                    1.0,
                    1.0,
                    step=0.05,
                    key="shift_lisa_to_isa",
                )
                shift_lisa_to_sipp = 1.0 - shift_lisa_to_isa
                redirectable_to_isa = shift_lisa_to_isa * lisa_contribution
                redirectable_to_sipp = shift_lisa_to_sipp * lisa_contribution
            else:
                minimum_lisa_redirectable = max(
                    lisa_contribution - unused_allowance, 0.0
                )
                redirectable_to_isa = st.number_input(
                    "Redirect LISA contribution to ISA (£)",
                    min_value=minimum_lisa_redirectable,
                    max_value=lisa_contribution,
                    value=lisa_contribution,
                    step=100.0,
                    key="redirectable_to_isa",
                )
                redirectable_to_sipp = lisa_contribution - redirectable_to_isa
                shift_lisa_to_isa = redirectable_to_isa / lisa_contribution
                shift_lisa_to_sipp = redirectable_to_sipp / lisa_contribution
            st.write(
                f"**Redirectable to ISA**: £{redirectable_to_isa:.0f} ({shift_lisa_to_isa:.0%})"
            )
            st.write(
                f"**Redirectable to SIPP**: £{redirectable_to_sipp:.0f} ({shift_lisa_to_sipp:.0%})"
            )

    post50_contribution_settings = Post50ContributionSettings(
        post_50_lisa_to_isa_rate=shift_lisa_to_isa,
        post_50_lisa_to_sipp_rate=shift_lisa_to_sipp,
        post_50_lisa_to_isa_contribution=redirectable_to_isa,
        post_50_lisa_to_sipp_contribution=redirectable_to_sipp,
    )
    return post50_contribution_settings


def _returns_and_inflation_section() -> "ExpectedReturnsAndInflation":
    """Collect expected accounts annual returns and inflation rate from the user.

    Returns
    -------
    ExpectedReturnsAndInflation
        A dataclass instance containing the expected annual returns for LISA, ISA,
        SIPP, and workplace pensions, as well as the expected inflation rate.
    """
    with st.sidebar.expander("Expected Returns & Inflation", expanded=False):
        expected_lisa_annual_return = st.slider(
            "LISA expected annual return (%)",
            0.0,
            0.2,
            0.05,
            step=0.001,
            key="roi_lisa",
        )
        expected_isa_annual_return = st.slider(
            "ISA expected annual return (%)",
            0.0,
            0.2,
            0.05,
            step=0.001,
            key="roi_isa",
        )
        expected_sipp_annual_return = st.slider(
            "SIPP expected annual return (%)",
            0.0,
            0.2,
            0.05,
            step=0.001,
            key="roi_sipp",
        )
        expected_workplace_annual_return = st.slider(
            "Workplace pension expected annual return (%)",
            0.0,
            0.2,
            0.05,
            step=0.001,
            key="roi_workplace",
        )
        expected_inflation = st.slider(
            "Expected inflation rate (%)",
            0.0,
            0.2,
            0.025,
            step=0.001,
            key="inflation",
        )
        return ExpectedReturnsAndInflation(
            expected_lisa_annual_return=expected_lisa_annual_return,
            expected_isa_annual_return=expected_isa_annual_return,
            expected_sipp_annual_return=expected_sipp_annual_return,
            expected_workplace_annual_return=expected_workplace_annual_return,
            expected_inflation=expected_inflation,
        )


def _post_retirement_section(
    tax_year: int,
    personal_details: "PersonalDetails",
    pre_retirement_returns: "ExpectedReturnsAndInflation",
) -> "PostRetirementSettings":
    """Collect post-retirement settings such as annual withdrawal amount in today's money."""
    with st.sidebar.expander("Post-Retirement Settings", expanded=False):
        withdrawal_today_amount = st.number_input(
            "Annual withdrawal in today's money (£)",
            min_value=0.0,
            value=30000.0,
            step=1000.0,
            help="How much you want to withdraw per year in today's money.",
            key="postret_withdrawal_today",
        )

        with st.expander("Expected Post-retirement Returns", expanded=False):
            expected_post_retirement_lisa_annual_return = st.slider(
                "LISA expected annual return (%)",
                0.0,
                0.2,
                pre_retirement_returns.expected_lisa_annual_return,
                step=0.001,
                key="postret_roi_lisa",
            )
            expected_post_retirement_isa_annual_return = st.slider(
                "ISA expected annual return (%)",
                0.0,
                0.2,
                pre_retirement_returns.expected_isa_annual_return,
                step=0.001,
                key="postret_roi_isa",
            )
            expected_post_retirement_pension_annual_return = st.slider(
                "Pension expected annual return (%)",
                0.0,
                0.2,
                pre_retirement_returns.expected_sipp_annual_return,
                step=0.001,
                key="postret_roi_pension",
            )

        with st.expander("Withdrawal Settings", expanded=False):
            st.write(f"**Shortfalls will be evenly covered by other accounts.**")
            lisa_minimum_withdrawal_age = pw.LIMITS_DB[str(tax_year)][
                "lisa_withdrawal_age"
            ]
            lisa_withdrawal_age = st.number_input(
                "LISA withdrawal age",
                min_value=lisa_minimum_withdrawal_age,
                max_value=100,
                value=max(lisa_minimum_withdrawal_age, personal_details.retirement_age),
                step=1,
                help="Age at which you can start withdrawing from LISA.",
                key="postret_lisa_withdrawal_age",
            )
            lisa_targeted_withdrawal_percentage = st.slider(
                "LISA withdrawal percentage (%)",
                0.0,
                1.0,
                0.0,
                step=0.01,
                help="How much you want to withdraw from LISA per year as a percentage of the annual withdrawal amount.",
                key="postret_lisa_targeted_withdrawal_percentage",
            )
            isa_withdrawal_age = st.number_input(
                "ISA withdrawal age",
                min_value=personal_details.retirement_age,
                max_value=100,
                value=personal_details.retirement_age,
                step=1,
                help="Age at which you can start withdrawing from ISA.",
                key="postret_isa_withdrawal_age",
            )
            isa_targeted_withdrawal_percentage = st.slider(
                "ISA withdrawal percentage (%)",
                0.0,
                1.0,
                0.0,
                step=0.01,
                help="How much you want to withdraw from ISA per year as a percentage of the annual withdrawal amount.",
                key="postret_isa_targeted_withdrawal_percentage",
            )
            taxfree_pension_withdrawal_age_minimum = pw.LIMITS_DB[str(tax_year)][
                "pension_withdrawal_age"
            ]
            taxfree_pension_withdrawal_age = st.number_input(
                "Pension Taxfree withdrawal age",
                min_value=taxfree_pension_withdrawal_age_minimum,
                max_value=100,
                value=max(
                    taxfree_pension_withdrawal_age_minimum,
                    personal_details.retirement_age,
                ),
                step=1,
                help="Age at which you can start withdrawing from pension.",
                key="postret_pension_withdrawal_age",
            )
            taxfree_pension_withdrawal_percentage = st.slider(
                "Taxfree Pension withdrawal percentage (%)",
                0.0,
                1.0,
                0.0,
                step=0.01,
                help="How much you want to withdraw from Pension per year as a percentage of the annual withdrawal amount.",
                key="postret_pension_targeted_withdrawal_percentage",
            )

            taxable_pension_withdrawal_age_minimum = pw.LIMITS_DB[str(tax_year)][
                "pension_withdrawal_age"
            ]
            taxable_pension_withdrawal_age = st.number_input(
                "Pension Taxable withdrawal age",
                min_value=taxable_pension_withdrawal_age_minimum,
                max_value=100,
                value=max(
                    taxable_pension_withdrawal_age_minimum,
                    personal_details.retirement_age,
                ),
                step=1,
                help="Age at which you can start withdrawing from pension.",
                key="postret_taxable_pension_withdrawal_age",
            )
            taxable_pension_withdrawal_percentage = st.slider(
                "Taxable Pension withdrawal percentage (%)",
                0.0,
                1.0,
                0.0,
                step=0.01,
                help="How much you want to withdraw from Pension per year as a percentage of the annual withdrawal amount.",
                key="postret_taxable_pension_targeted_withdrawal_percentage",
            )

            total_withdrawal_percentage = (
                lisa_targeted_withdrawal_percentage
                + isa_targeted_withdrawal_percentage
                + taxfree_pension_withdrawal_percentage
                + taxable_pension_withdrawal_percentage
            )
            total_withdrawal_amount = (
                withdrawal_today_amount * total_withdrawal_percentage
            )
            if total_withdrawal_amount > withdrawal_today_amount:
                st.warning(
                    f"⚠️ Total withdrawal amounts exceed the annual withdrawal amount by {total_withdrawal_percentage-1:.2%}. Please adjust."
                )
            elif total_withdrawal_amount <= withdrawal_today_amount:
                st.progress(
                    total_withdrawal_percentage,
                    text=f"Total Withdrawal Amount: £{total_withdrawal_amount:,.0f} ({total_withdrawal_percentage*100:.1f}%)",
                )
                if total_withdrawal_amount < withdrawal_today_amount:
                    st.warning(
                        f"⚠️ Total withdrawal amounts are less than the annual withdrawal amount by {1-total_withdrawal_percentage:.2%}. Please adjust."
                    )

    post_retirement_settings = PostRetirementSettings(
        withdrawal_today_amount=withdrawal_today_amount,
        expected_post_retirement_lisa_annual_return=expected_post_retirement_lisa_annual_return,
        expected_post_retirement_isa_annual_return=expected_post_retirement_isa_annual_return,
        expected_post_retirement_pension_annual_return=expected_post_retirement_pension_annual_return,
        postret_lisa_withdrawal_age=lisa_withdrawal_age,
        postret_lisa_targeted_withdrawal_percentage=lisa_targeted_withdrawal_percentage,
        postret_isa_withdrawal_age=isa_withdrawal_age,
        postret_isa_targeted_withdrawal_percentage=isa_targeted_withdrawal_percentage,
        postret_taxfree_pension_withdrawal_age=taxfree_pension_withdrawal_age,
        postret_taxfree_pension_targeted_withdrawal_percentage=taxfree_pension_withdrawal_percentage,
        postret_taxable_pension_withdrawal_age=taxable_pension_withdrawal_age,
        postret_taxable_pension_targeted_withdrawal_percentage=taxable_pension_withdrawal_percentage,
    )
    return post_retirement_settings


def sidebar_inputs() -> "ProfileSettings":
    """Gather all user inputs from the sidebar.

    This orchestrates calls to the helper functions defined above. It
    constructs the planwise UserProfile, ContributionRates and InvestmentReturns
    objects, and returns them along with inflation and other values needed for
    downstream projections.
    """
    _logo_section()
    tax_year = _tax_year_selectbox()
    scotland, use_qualifying = _tax_settings_section()
    qualifying_earnings = get_qualifying_earnings_info(use_qualifying, tax_year)
    personal_details = _personal_details_section(tax_year, scotland)
    contribution_settings = _contribution_rates_section(
        tax_year, personal_details, qualifying_earnings
    )
    account_balances = _account_balances_section()
    post_50_contribution_settings = _post50_lisa_section(
        tax_year, contribution_settings
    )
    expected_returns_and_inflation = _returns_and_inflation_section()
    post_retirement_settings = _post_retirement_section(
        tax_year, personal_details, expected_returns_and_inflation
    )

    profile_settings = ProfileSettings(
        tax_year=tax_year,
        scotland=scotland,
        personal_details=personal_details,
        qualifying_earnings=qualifying_earnings,
        contribution_settings=contribution_settings,
        account_balances=account_balances,
        post_50_contribution_settings=post_50_contribution_settings,
        expected_returns_and_inflation=expected_returns_and_inflation,
        post_retirement_settings=post_retirement_settings,
    )
    return profile_settings
