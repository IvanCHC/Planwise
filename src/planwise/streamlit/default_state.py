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
    ProfileSettings,
    get_personal_details,
    get_qualifying_earnings_info,
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
