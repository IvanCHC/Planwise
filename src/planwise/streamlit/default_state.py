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
