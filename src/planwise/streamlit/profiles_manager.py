import streamlit as st

from planwise.profile import delete_profile, list_profiles, load_profile, save_profile

from .default_state import reset_default_state


def _save_temp_profile() -> None:
    prof_name = (st.session_state.get("profile_name") or "").strip()
    if not prof_name:
        st.error("Please enter a profile name before saving.")
    else:
        payload = {
            "tax_year": st.session_state.get("tax_year", 2025),
            "scotland": st.session_state.get("scotland", False),
            "use_qualifying": st.session_state.get("use_qualifying", False),
            "current_age": st.session_state.get("current_age", 25),
            "retirement_age": st.session_state.get("retirement_age", 67),
            "salary": st.session_state.get("salary", 30000.0),
            "use_exact_amounts": st.session_state.get("use_exact_amounts", False),
            "workplace_employer_contribution": st.session_state.get(
                "workplace_employer_contribution", 0.03
            ),
            "workplace_employee_contribution": st.session_state.get(
                "workplace_employee_contribution", 0.05
            ),
            "lisa_contribution": st.session_state.get("lisa_contribution", 0.0),
            "isa_contribution": st.session_state.get("isa_contribution", 0.0),
            "sipp_contribution": st.session_state.get("sipp_contribution", 0.0),
        }
        save_profile(prof_name, payload)
        st.success(f"Saved profile '{prof_name}'")


def _load_temp_profile() -> None:
    sel = st.session_state["profile_name"] = st.session_state.get(
        "selected_profile", ""
    )
    if sel and sel != "—":
        profile_data = load_profile(sel)
        if profile_data:
            for key, value in profile_data.items():
                st.session_state[key] = value
            st.success(f"Loaded profile '{sel}'")
        else:
            st.error(f"Profile '{sel}' not found.")


def render_profiles_manager() -> None:
    """Render the profiles manager page."""
    with st.sidebar:
        st.header("Profiles Manager")

        profiles = list_profiles()
        selected_profile = st.selectbox(
            "Select a profile to manage",
            options=["—"] + profiles,
            key="selected_profile",
            on_change=_load_temp_profile,
        )
        st.text_input(
            "Profile name (used for the JSON filename)",
            value=selected_profile if selected_profile != "—" else "",
            key="profile_name",
            placeholder="e.g. retirement plan",
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button(
                "Save",
                use_container_width=True,
                # disabled=(st.session_state["selected_profile"] == "—"),
                on_click=_save_temp_profile,
            )
        with c2:
            st.button(
                "Reset",
                use_container_width=True,
                # disabled=(st.session_state["selected_profile"] == "—"),
                on_click=_load_temp_profile,
            )
        with c3:
            st.button(
                "Delete",
                type="secondary",
                use_container_width=True,
                # disabled=(st.session_state["selected_profile"] == "—"),
                on_click=reset_default_state,
            )
