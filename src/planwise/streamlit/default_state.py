import streamlit as st


def get_default_state() -> dict[str, int | float | bool]:
    return {
        "tax_year": 2025,
        "scotland": False,
        "use_qualifying": False,
        "current_age": 25,
        "retirement_age": 67,
        "salary": 30000.0,
        "use_exact_amounts": False,
        "workplace_employer_contribution": 0.03,
        "workplace_employee_contribution": 0.05,
        "lisa_contribution": 0.0,
        "isa_contribution": 0.0,
        "sipp_contribution": 0.0,
        "lisa_balance": 0.0,
        "isa_balance": 0.0,
        "sipp_balance": 0.0,
        "workplace_balance": 0.0,
        "use_exact_amount_post50": False,
        "redirectable_to_isa": 0.0,
        "roi_lisa": 0.05,
        "roi_isa": 0.05,
        "roi_sipp": 0.05,
        "roi_workplace": 0.05,
        "inflation": 0.02,
        "postret_withdrawal_today": 0.0,
        "postret_roi_lisa": 0.05,
        "postret_roi_isa": 0.05,
        "postret_roi_pension": 0.05,
        "postret_lisa_withdrawal_age": 67,
        "postret_lisa_targeted_withdrawal_percentage": 0.0,
        "postret_isa_withdrawal_age": 67,
        "postret_isa_targeted_withdrawal_percentage": 0.0,
        "postret_taxfree_pension_withdrawal_age": 67,
        "postret_taxfree_pension_targeted_withdrawal_percentage": 0.0,
        "postret_taxable_pension_withdrawal_age": 67,
        "postret_taxable_pension_targeted_withdrawal_percentage": 0.0,
    }


def reset_default_state() -> None:
    st.session_state.update(get_default_state())


from planwise.profile import (
    AccountBalances,
    ContributionSettings,
    ProfileSettings,
    get_isa_contribution_rate,
    get_personal_details,
    get_qualifying_earnings_info,
    get_sipp_contribution_rate,
    get_workplace_contribution_rate,
)


def convert_streamlit_state_to_profile() -> None:
    tax_year = st.session_state.get("tax_year", 2025)
    scotland = st.session_state.get("scotland", False)
    use_qualifying = st.session_state.get("use_qualifying", False)
    qualifying_earnings = get_qualifying_earnings_info(use_qualifying, tax_year)

    current_age = st.session_state.get("current_age", 25)
    retirement_age = st.session_state.get("retirement_age", 67)
    salary = st.session_state.get("salary", 30000.0)
    personal_details = get_personal_details(
        current_age, retirement_age, salary, tax_year, scotland
    )

    use_exact_amount = st.session_state.get("use_exact_amount", False)
    workplace_employer_contribution = st.session_state.get(
        "workplace_employer_contribution", 0.03
    )
    workplace_employee_contribution = st.session_state.get(
        "workplace_employee_contribution", 0.05
    )
    workplace_er_rate, workplace_er_contribution = get_workplace_contribution_rate(
        workplace_employer_contribution,
        personal_details,
        qualifying_earnings,
        use_exact_amount,
    )
    workplace_ee_rate, workplace_ee_contribution = get_workplace_contribution_rate(
        workplace_employee_contribution,
        personal_details,
        qualifying_earnings,
        use_exact_amount,
    )
    lisa_contribution = st.session_state.get("lisa_contribution", 0.0)
    isa_contribution = st.session_state.get("isa_contribution", 0.0)
    sipp_contribution = st.session_state.get("sipp_contribution", 0.0)
    lisa_rate, lisa_contribution = get_isa_contribution_rate(
        lisa_contribution, personal_details, use_exact_amount
    )
    isa_rate, isa_contribution = get_isa_contribution_rate(
        isa_contribution, personal_details, use_exact_amount
    )
    sipp_rate, sipp_contribution = get_sipp_contribution_rate(
        sipp_contribution, personal_details, use_exact_amount
    )

    total_net_contribution = (
        workplace_ee_contribution
        + lisa_contribution
        + isa_contribution
        + sipp_contribution
    )
    total_sipp_contribution = sipp_contribution * 1.25
    total_workplace_contribution = (
        workplace_er_contribution + workplace_ee_contribution * 1.25
    )
    total_pension_contribution = total_workplace_contribution + total_sipp_contribution
    total_isa_contribution = lisa_contribution * 1.25 + isa_contribution
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

    lisa_balance = st.session_state.get("lisa_balance", 0.0)
    isa_balance = st.session_state.get("isa_balance", 0.0)
    sipp_balance = st.session_state.get("sipp_balance", 0.0)
    workplace_balance = st.session_state.get("workplace_balance", 0.0)
    account_balances = AccountBalances(
        lisa_balance=lisa_balance,
        isa_balance=isa_balance,
        sipp_balance=sipp_balance,
        workplace_pension_balance=workplace_balance,
    )


def convert_profile_to_streamlit_state(profile_settings: "ProfileSettings") -> None:
    state_data: dict[str, bool | int | float] = {}
    state_data["tax_year"] = profile_settings.tax_year
    state_data["scotland"] = profile_settings.scotland
    state_data[
        "use_qualifying"
    ] = profile_settings.qualifying_earnings.use_qualifying_earnings

    state_data["current_age"] = profile_settings.personal_details.current_age
    state_data["retirement_age"] = profile_settings.personal_details.retirement_age
    state_data["salary"] = profile_settings.personal_details.salary

    state_data["use_exact_amounts"] = False
    state_data[
        "workplace_employer_contribution"
    ] = profile_settings.contribution_settings.workplace_er_contribution
    state_data[
        "workplace_employee_contribution"
    ] = profile_settings.contribution_settings.workplace_ee_contribution
    state_data[
        "lisa_contribution"
    ] = profile_settings.contribution_settings.lisa_contribution
    state_data[
        "isa_contribution"
    ] = profile_settings.contribution_settings.isa_contribution
    state_data[
        "sipp_contribution"
    ] = profile_settings.contribution_settings.sipp_contribution

    state_data["lisa_balance"] = profile_settings.account_balances.lisa_balance
    state_data["isa_balance"] = profile_settings.account_balances.isa_balance
    state_data["sipp_balance"] = profile_settings.account_balances.sipp_balance
    state_data[
        "workplace_balance"
    ] = profile_settings.account_balances.workplace_pension_balance
