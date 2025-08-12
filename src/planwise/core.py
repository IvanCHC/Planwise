"""
Core retirement projection calculations for Planwise.

This module contains the main projection function that models retirement
savings across various UK tax wrappers over time. It provides dataclasses for user
profile, contribution rates, and investment returns, as well as helper functions for
calculating contributions and projecting account balances.
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from .tax import calculate_gross_from_take_home, calculate_income_tax


def load_state_pension_db() -> Any:
    json_path = os.path.join(os.path.dirname(__file__), "data", "state_pension.json")
    with open(json_path, "r") as f:
        return json.load(f)


def load_limits_db() -> Any:
    """
    Load annual limits and constants from JSON file.
    Returns:
        dict: Limits for each tax year.
    """
    json_path = os.path.join(os.path.dirname(__file__), "data", "limits.json")
    with open(json_path, "r") as f:
        return json.load(f)


STATE_PENSION_DB = load_state_pension_db()
LIMITS_DB = load_limits_db()


def _find_account_columns_postret(df: pd.DataFrame) -> dict:
    account_map = {}
    for col in df.columns:
        if col.startswith("Pot ") and not col.endswith("(Inflation Adjusted)"):
            acc_name = col[len("Pot ") :].strip()
            # Combine SIPP and Workplace into Pension
            if acc_name in ("SIPP", "Workplace"):
                continue  # skip, will handle below
            account_map[acc_name] = col
    # If both SIPP and Workplace exist, add Pension as their sum
    if "Pot SIPP" in df.columns or "Pot Workplace" in df.columns:
        account_map["Pension"] = None  # Mark for special handling
    return account_map


# def _returns_to_dict_postret(returns) -> dict:
#     return {
#         "LISA": getattr(returns, "lisa", 0.0),
#         "ISA": getattr(returns, "isa", 0.0),
#         "SIPP": getattr(returns, "sipp", 0.0),
#         "Workplace": getattr(returns, "workplace", 0.0),
#     }


import logging
from typing import Optional

from planwise.streamlit.sidebar_utils import ProfileSettings

# def project_post_retirement(
#     df: pd.DataFrame,
#     withdrawal_today: float,
#     returns: dict,
#     withdraw_plan: list,
#     inflation: float = 0.02,
#     end_age: int = 100,
#     current_age: int = 30,
#     year: int = 2025,
#     scotland: bool = False,
#     pension_tax_free_fraction: float = 0.25,
#     state_pension_age: Optional[int] = None,
#     state_pension_amount: Optional[float] = None,
#     uprate_state_pension: Optional[bool] = None,
# ) -> pd.DataFrame:
#     """
#     Project post-retirement account balances and withdrawals using a drawdown strategy.

#     Args:
#         df (pd.DataFrame): DataFrame of historical pots (must include 'Age' and 'Pot <Account>' columns).
#         withdrawal_today (float): Annual withdrawal in today's money.
#         returns (InvestmentReturns): Expected annual rates of return for each account.
#         withdraw_plan (list): List of dicts specifying withdrawal order and eligibility.
#         inflation (float, optional): Annual inflation rate. Default is 0.02.
#         end_age (int, optional): Final age for projection. Default is 100.

#     Returns:
#         pd.DataFrame: DataFrame with projected balances, withdrawals, and shortfall per year.
#     """
#     if df.empty:
#         raise ValueError("Input data frame must not be empty.")
#     if "Age" not in df.columns:
#         raise ValueError("Input data frame must contain an 'Age' column.")

#     df_sorted = df.sort_values("Age")
#     account_columns = _find_account_columns_postret(df_sorted)
#     # Build starting pots, combining SIPP and Workplace into Pension
#     starting_pots: Dict[str, float] = {}
#     for acc, col in account_columns.items():
#         if acc == "Pension":
#             sipp = (
#                 float(df_sorted["Pot SIPP"].iloc[-1])
#                 if "Pot SIPP" in df_sorted.columns
#                 else 0.0
#             )
#             workplace = (
#                 float(df_sorted["Pot Workplace"].iloc[-1])
#                 if "Pot Workplace" in df_sorted.columns
#                 else 0.0
#             )
#             starting_pots["Pension"] = sipp + workplace
#         else:
#             starting_pots[acc] = float(df_sorted[col].iloc[-1])
#     # Build ROIs, combining SIPP and Workplace into Pension
#     account_rois = _returns_to_dict_postret(returns)
#     if "Pension" in starting_pots:
#         sipp_roi = getattr(returns, "sipp", 0.0)
#         workplace_roi = getattr(returns, "workplace", 0.0)
#         sipp = (
#             float(df_sorted["Pot SIPP"].iloc[-1])
#             if "Pot SIPP" in df_sorted.columns
#             else 0.0
#         )
#         workplace = (
#             float(df_sorted["Pot Workplace"].iloc[-1])
#             if "Pot Workplace" in df_sorted.columns
#             else 0.0
#         )
#         total = sipp + workplace
#         if total > 0:
#             pension_roi = (sipp * sipp_roi + workplace * workplace_roi) / total
#         else:
#             pension_roi = max(sipp_roi, workplace_roi)
#         account_rois["Pension"] = pension_roi
#         # remove SIPP and Workplace ROI entries, since they are combined
#         account_rois.pop("SIPP", None)
#         account_rois.pop("Workplace", None)

#     # --- Split Pension into tax-free and taxable accounts ---
#     # If a combined Pension pot exists, divide it into tax-free and tax portions.
#     # The default fraction of the pension that can be withdrawn tax-free (pension_tax_free_fraction)
#     # can be overridden via function parameter. This splitting occurs only at the start
#     # of the post-retirement projection and does not reallocate funds between the sub-accounts
#     # thereafter. Both sub-accounts earn the same ROI as the original Pension.
#     if "Pension" in starting_pots:
#         total_pension = starting_pots.pop("Pension")
#         total_pension = max(total_pension, 0.0)
#         tax_free_balance = min(
#             total_pension * pension_tax_free_fraction, 268275
#         )  # 2025/26 LTA
#         taxable_balance = total_pension - tax_free_balance
#         starting_pots["Pension Tax Free"] = tax_free_balance
#         starting_pots["Pension Tax"] = taxable_balance
#         pension_roi = account_rois.pop("Pension")
#         # The tax-free portion represents a lump sum and does not earn
#         # separate interest; any growth on the pension is added to the
#         # taxable pot.  Therefore the tax-free pot ROI is set to zero,
#         # and the taxable pot uses the full pension ROI.
#         account_rois["Pension Tax Free"] = 0.0
#         account_rois["Pension Tax"] = pension_roi

#     # Preprocess withdrawal plan
#     # Expand references to Pension (or SIPP/Workplace) into separate tax-free and taxable accounts
#     plan: List[Dict[str, Any]] = []
#     for entry in withdraw_plan:
#         if "account" not in entry or "start_age" not in entry:
#             raise ValueError(
#                 "Each withdraw_plan entry must include both 'account' and 'start_age'."
#             )
#         acc_original = entry["account"]
#         start_age = int(entry["start_age"])
#         proportion = entry.get("proportion", None)
#         # Determine if this entry targets the combined Pension or its components
#         if acc_original in ("Pension", "SIPP", "Workplace") and (
#             "Pension Tax Free" in starting_pots or "Pension Tax" in starting_pots
#         ):
#             # If a proportion is provided, allocate it between the tax-free and taxable pots
#             if proportion is not None:
#                 prop_free = proportion * pension_tax_free_fraction
#                 prop_tax = proportion * (1.0 - pension_tax_free_fraction)
#                 if prop_free > 0.0:
#                     plan.append(
#                         {
#                             "account": "Pension Tax Free",
#                             "start_age": start_age,
#                             "proportion": prop_free,
#                         }
#                     )
#                 if prop_tax > 0.0:
#                     plan.append(
#                         {
#                             "account": "Pension Tax",
#                             "start_age": start_age,
#                             "proportion": prop_tax,
#                         }
#                     )
#             else:
#                 # Sequential withdrawals: add both sub-accounts without proportions
#                 plan.append(
#                     {
#                         "account": "Pension Tax Free",
#                         "start_age": start_age,
#                         "proportion": None,
#                     }
#                 )
#                 plan.append(
#                     {
#                         "account": "Pension Tax",
#                         "start_age": start_age,
#                         "proportion": None,
#                     }
#                 )
#         else:
#             acc = acc_original
#             if acc not in starting_pots:
#                 raise ValueError(
#                     f"Account '{acc}' in withdraw_plan not found in input data."
#                 )
#             plan.append(
#                 {
#                     "account": acc,
#                     "start_age": start_age,
#                     "proportion": proportion,
#                 }
#             )

#     # --- State Pension Projection ---
#     # Determine state pension parameters.  Values provided via function
#     # arguments take precedence over the defaults loaded from the database.
#     sp_data = STATE_PENSION_DB.get(str(year), {})
#     sp_age_default = sp_data.get("state_pension_age", 67)
#     sp_amount_default = sp_data.get("state_pension_per_year", 11000.0)
#     uprate_inflation_default = sp_data.get("uprate_inflation", True)
#     # Use overrides if provided, otherwise fall back to defaults
#     sp_age = state_pension_age if state_pension_age is not None else sp_age_default
#     sp_per_year = (
#         state_pension_amount if state_pension_amount is not None else sp_amount_default
#     )
#     uprate_inflation = (
#         uprate_state_pension
#         if uprate_state_pension is not None
#         else uprate_inflation_default
#     )

#     records: List[Dict[str, Any]] = []
#     pots = starting_pots.copy()
#     # Iterate over each year from the first year after retirement to end_age
#     for age in range(int(df_sorted["Age"].iloc[-1]) + 1, end_age + 1):
#         # Grow each pot according to its ROI.  Pension tax-free and
#         # taxable pots are treated specially: growth on the combined
#         # pension is allocated entirely to the taxable pot, and the
#         # tax-free pot does not earn separate interest.
#         # First, update non-pension pots normally
#         for acc, value in list(pots.items()):
#             if acc in ("Pension Tax Free", "Pension Tax"):
#                 continue
#             growth_rate = account_rois.get(acc, 0.0)
#             pots[acc] = value * (1.0 + growth_rate)
#         # Then handle the pension pots, if they exist
#         if "Pension Tax Free" in pots and "Pension Tax" in pots:
#             total_pension_balance = pots["Pension Tax Free"] + pots["Pension Tax"]
#             pension_roi = account_rois.get("Pension Tax", 0.0)
#             growth = total_pension_balance * pension_roi
#             # Allocate all growth to the taxable pot; tax-free pot remains constant
#             pots["Pension Tax"] += growth

#         # Inflation adjustment based on years since current age
#         years_since_current = age - current_age
#         cumulative_inflation = (1.0 + inflation) ** years_since_current
#         # Base withdrawal adjusted for inflation
#         withdrawal_infl_adj = withdrawal_today * cumulative_inflation

#         # Compute state pension for this age
#         if age >= sp_age:
#             if uprate_inflation:
#                 sp_infl_adj = sp_per_year * cumulative_inflation
#                 sp_todays = sp_per_year
#             else:
#                 sp_infl_adj = sp_per_year
#                 sp_todays = sp_per_year / cumulative_inflation
#         else:
#             sp_infl_adj = 0.0
#             sp_todays = 0.0

#         # Determine the net withdrawal required from the pots after accounting for state pension
#         withdrawal_from_pots_infl = max(withdrawal_infl_adj - sp_infl_adj, 0.0)
#         withdrawal_from_pots_today = max(withdrawal_today - sp_todays, 0.0)

#         # Track current taxable income to compute incremental tax on pension withdrawals
#         taxable_income_so_far_today = sp_todays  # <-- use today's money
#         total_tax_paid_today = 0.0
#         remaining_net_to_fund_today = withdrawal_from_pots_today

#         # Track withdrawals from each account in today's money.  This dict will be
#         # populated as net-of-tax amounts are taken from the pots.  Keys are
#         # account names; values are the amounts withdrawn in today's pounds.
#         withdrawals_today: Dict[str, float] = {}

#         # Identify plan entries active at this age
#         active_plan = [p for p in plan if age >= p["start_age"]]
#         # Sum of base proportions for all active entries; used for validation
#         total_prop = sum(
#             p["proportion"] for p in active_plan if p["proportion"] is not None
#         )
#         if total_prop > 1.0 + 1e-9:
#             raise ValueError(
#                 f"Sum of proportions in withdraw_plan entries active at age {age} exceeds 1."
#             )

#         # --- Dynamic reallocation of proportions when pots are depleted ---
#         # Determine proportional entries and free up proportions from empty pots.  Freed
#         # proportions are redistributed evenly across the remaining proportional
#         # accounts with a positive balance.  Sequential (None) entries are
#         # unaffected by this redistribution; any leftover withdrawal beyond the
#         # redistributed proportional allocations is handled in the sequential step
#         # below.
#         active_prop_entries = [p for p in active_plan if p["proportion"] is not None]
#         freed_prop = 0.0
#         active_positive_prop_entries = []
#         for p_entry in active_prop_entries:
#             acc_name = p_entry["account"]
#             base_prop = p_entry["proportion"]
#             # If the account pot is depleted or non‑existent, free up its allocation
#             if pots.get(acc_name, 0.0) <= 0.0:
#                 freed_prop += base_prop
#             else:
#                 active_positive_prop_entries.append(p_entry)
#         effective_props: Dict[str, float] = {}
#         n_remaining = len(active_positive_prop_entries)
#         if n_remaining > 0 and total_prop > 0.0:
#             redistribute = freed_prop / n_remaining
#             for p_entry in active_positive_prop_entries:
#                 acc_name = p_entry["account"]
#                 effective_props[acc_name] = p_entry["proportion"] + redistribute

#         # Helper function to compute gross withdrawal needed to achieve a net-of-tax amount (today's money)
#         def compute_gross_from_net_today(
#             net_required: float, taxable_base: float
#         ) -> float:
#             if net_required <= 0.0:
#                 return 0.0
#             tax_at_base = calculate_income_tax(
#                 income=taxable_base,
#                 scotland=scotland,
#                 year=year,
#             )

#             def f(gross: float) -> float:
#                 tax_total = calculate_income_tax(
#                     income=taxable_base + gross,
#                     scotland=scotland,
#                     year=year,
#                 )
#                 tax_due = tax_total - tax_at_base
#                 return gross - tax_due - net_required

#             low = 0.0
#             high = net_required * 2.0 + 1.0
#             while f(high) < 0.0:
#                 high *= 2.0
#             for _ in range(40):
#                 mid = (low + high) / 2.0
#                 if f(mid) > 0.0:
#                     high = mid
#                 else:
#                     low = mid
#             return high

#         # Proportional withdrawals (net‑of‑tax basis, today's money) using dynamic proportions
#         if total_prop > 0.0 and remaining_net_to_fund_today > 0.0:
#             for p_entry in active_prop_entries:
#                 acc = p_entry["account"]
#                 # Skip accounts with no funds
#                 if pots.get(acc, 0.0) <= 0.0:
#                     continue
#                 # Use the dynamically adjusted proportion if available
#                 prop = effective_props.get(acc, p_entry["proportion"])
#                 alloc_net_today = withdrawal_from_pots_today * prop
#                 if alloc_net_today <= 0.0:
#                     continue
#                 if acc == "Pension Tax":
#                     gross_needed_today = compute_gross_from_net_today(
#                         alloc_net_today, taxable_income_so_far_today
#                     )
#                     gross_taken_today = min(
#                         gross_needed_today, pots.get(acc, 0.0) / cumulative_inflation
#                     )
#                     # Compute tax on this gross withdrawal
#                     # Use named parameters to ensure correct argument order
#                     tax_after = calculate_income_tax(
#                         income=taxable_income_so_far_today + gross_taken_today,
#                         scotland=scotland,
#                         year=year,
#                     )
#                     tax_before = calculate_income_tax(
#                         income=taxable_income_so_far_today,
#                         scotland=scotland,
#                         year=year,
#                     )
#                     tax_due_today = tax_after - tax_before
#                     net_taken_today = gross_taken_today - tax_due_today
#                     pots[acc] -= (
#                         gross_taken_today * cumulative_inflation
#                     )  # convert back to future value
#                     taxable_income_so_far_today += gross_taken_today
#                     total_tax_paid_today += tax_due_today
#                     remaining_net_to_fund_today -= net_taken_today
#                     # Record the net withdrawal from this account (today's money)
#                     withdrawals_today[acc] = (
#                         withdrawals_today.get(acc, 0.0) + net_taken_today
#                     )
#                     if remaining_net_to_fund_today < 0.0:
#                         remaining_net_to_fund_today = 0.0
#                 else:
#                     net_taken_today = min(
#                         alloc_net_today, pots.get(acc, 0.0) / cumulative_inflation
#                     )
#                     pots[acc] -= net_taken_today * cumulative_inflation
#                     remaining_net_to_fund_today -= net_taken_today
#                     # Record the net withdrawal for this account
#                     withdrawals_today[acc] = (
#                         withdrawals_today.get(acc, 0.0) + net_taken_today
#                     )
#                     if remaining_net_to_fund_today < 0.0:
#                         remaining_net_to_fund_today = 0.0

#         # Sequential withdrawals once proportional allocations are handled (today's money)
#         if remaining_net_to_fund_today > 1e-9:
#             for p_entry in active_plan:
#                 if p_entry["proportion"] is not None:
#                     continue
#                 acc = p_entry["account"]
#                 if remaining_net_to_fund_today <= 0.0:
#                     break
#                 if pots.get(acc, 0.0) <= 0.0:
#                     continue
#                 if acc == "Pension Tax":
#                     alloc_net_today = remaining_net_to_fund_today
#                     gross_needed_today = compute_gross_from_net_today(
#                         alloc_net_today, taxable_income_so_far_today
#                     )
#                     gross_taken_today = min(
#                         gross_needed_today, pots.get(acc, 0.0) / cumulative_inflation
#                     )
#                     tax_after = calculate_income_tax(
#                         income=taxable_income_so_far_today + gross_taken_today,
#                         scotland=scotland,
#                         year=year,
#                     )
#                     tax_before = calculate_income_tax(
#                         income=taxable_income_so_far_today,
#                         scotland=scotland,
#                         year=year,
#                     )
#                     tax_due_today = tax_after - tax_before
#                     net_taken_today = gross_taken_today - tax_due_today
#                     pots[acc] -= gross_taken_today * cumulative_inflation
#                     taxable_income_so_far_today += gross_taken_today
#                     total_tax_paid_today += tax_due_today
#                     remaining_net_to_fund_today -= net_taken_today
#                     # Record the net withdrawal for this account
#                     withdrawals_today[acc] = (
#                         withdrawals_today.get(acc, 0.0) + net_taken_today
#                     )
#                     if remaining_net_to_fund_today < 0.0:
#                         remaining_net_to_fund_today = 0.0
#                 else:
#                     net_taken_today = min(
#                         remaining_net_to_fund_today,
#                         pots.get(acc, 0.0) / cumulative_inflation,
#                     )
#                     pots[acc] -= net_taken_today * cumulative_inflation
#                     remaining_net_to_fund_today -= net_taken_today
#                     # Record the net withdrawal for this account
#                     withdrawals_today[acc] = (
#                         withdrawals_today.get(acc, 0.0) + net_taken_today
#                     )
#                     if remaining_net_to_fund_today < 0.0:
#                         remaining_net_to_fund_today = 0.0
#                 if remaining_net_to_fund_today <= 1e-9:
#                     break

#         # ------------------------------------------------------------------
#         # Handle any remaining shortfall by withdrawing from future accounts.
#         #
#         # If there is still a net amount to fund after drawing from all
#         # eligible current accounts (both proportional and sequential), we
#         # attempt to cover this shortfall by pulling forward withdrawals
#         # from accounts whose start_age has not yet been reached.  The
#         # remaining shortfall is distributed evenly across such future
#         # accounts on a net-of-tax basis.  This ensures that additional
#         # withdrawals are spread fairly and that tax is applied where
#         # appropriate (i.e. for the Pension Tax pot).  If an account is
#         # depleted or has zero balance, it is skipped.  Redistribution
#         # continues until either the shortfall is zero or no future
#         # accounts with positive balances remain.
#         if remaining_net_to_fund_today > 1e-9:
#             # Identify accounts with a positive pot balance that are
#             # considered active at this age.  An account is active if its
#             # specified start_age has already been reached (start_age <= age).
#             # Accounts that are not referenced in the withdraw plan at all
#             # are treated as always active.  We only redistribute to
#             # accounts that have become active, ensuring that funds from
#             # future accounts remain untouched until their start age.
#             active_accounts: set[str] = set()
#             # Add accounts whose plan entry start_age has been reached
#             for p_entry in plan:
#                 if p_entry["start_age"] <= age:
#                     active_accounts.add(p_entry["account"])
#             # Accounts not present in the plan are considered always active
#             plan_accounts = {p_entry["account"] for p_entry in plan}
#             for acc in pots.keys():
#                 if acc not in plan_accounts:
#                     active_accounts.add(acc)
#             # Filter to only those active accounts with a positive balance
#             future_accounts = [
#                 acc for acc in active_accounts if pots.get(acc, 0.0) > 0.0
#             ]
#             # Redistribute the shortfall across future accounts
#             # Loop until shortfall resolved or no accounts left
#             while remaining_net_to_fund_today > 1e-9 and future_accounts:
#                 n_future = len(future_accounts)
#                 if n_future == 0:
#                     break
#                 net_share = remaining_net_to_fund_today / n_future
#                 # Track accounts that still have funds after this round
#                 new_future_accounts = []
#                 for acc in future_accounts:
#                     # Skip if pot is zero or negative
#                     pot_balance = pots.get(acc, 0.0)
#                     if pot_balance <= 0.0:
#                         continue
#                     if acc == "Pension Tax":
#                         # Compute gross required to deliver the net share
#                         gross_needed_today = compute_gross_from_net_today(
#                             net_share, taxable_income_so_far_today
#                         )
#                         # Limit withdrawal by pot size (convert pot to today's money)
#                         gross_available_today = pot_balance / cumulative_inflation
#                         gross_taken_today = gross_needed_today
#                         if gross_taken_today > gross_available_today:
#                             gross_taken_today = gross_available_today
#                         # Compute tax due on this withdrawal using named parameters
#                         tax_after = calculate_income_tax(
#                             income=taxable_income_so_far_today + gross_taken_today,
#                             scotland=scotland,
#                             year=year,
#                         )
#                         tax_before = calculate_income_tax(
#                             income=taxable_income_so_far_today,
#                             scotland=scotland,
#                             year=year,
#                         )
#                         tax_due_today = tax_after - tax_before
#                         net_taken_today = gross_taken_today - tax_due_today
#                         # Update pot (convert gross back to future value)
#                         pots[acc] -= gross_taken_today * cumulative_inflation
#                         taxable_income_so_far_today += gross_taken_today
#                         total_tax_paid_today += tax_due_today
#                         remaining_net_to_fund_today -= net_taken_today
#                         # Record withdrawal
#                         withdrawals_today[acc] = (
#                             withdrawals_today.get(acc, 0.0) + net_taken_today
#                         )
#                     else:
#                         # Non-taxable account: take net share or available pot
#                         max_net_today = pot_balance / cumulative_inflation
#                         net_taken_today = net_share
#                         if net_taken_today > max_net_today:
#                             net_taken_today = max_net_today
#                         pots[acc] -= net_taken_today * cumulative_inflation
#                         remaining_net_to_fund_today -= net_taken_today
#                         withdrawals_today[acc] = (
#                             withdrawals_today.get(acc, 0.0) + net_taken_today
#                         )
#                     # If account still has funds, retain for further rounds
#                     if pots.get(acc, 0.0) > 1e-9:
#                         new_future_accounts.append(acc)
#                 # Update the list of future accounts for the next round
#                 future_accounts = new_future_accounts
#                 # Continue looping until remaining_net_to_fund_today is zero or no accounts left
#             # End of redistribution loop

#         # After redistribution, compute any remaining shortfall
#         shortfall_today = (
#             remaining_net_to_fund_today if remaining_net_to_fund_today > 1e-9 else 0.0
#         )
#         shortfall = shortfall_today * cumulative_inflation

#         total_pot = sum(pots.values())
#         total_pot_todays = (
#             total_pot / cumulative_inflation
#             if cumulative_inflation > 0.0
#             else total_pot
#         )

#         record: Dict[str, Any] = {
#             "Age": age,
#             "Withdrawal (Inflation Adjusted)": withdrawal_from_pots_infl,
#             "Withdrawal (Today's Money)": withdrawal_from_pots_today,
#         }
#         for acc, value in pots.items():
#             record[f"Pot {acc}"] = value
#         # Record total pot values
#         record["Total Pot"] = total_pot
#         record["Total Pot (Today's Money)"] = total_pot_todays
#         # Record per-account withdrawals in today's money
#         for acc in pots.keys():
#             record[f"Withdrawal {acc} (Today's Money)"] = withdrawals_today.get(
#                 acc, 0.0
#             )
#         # Record shortfall and tax details
#         record["Remaining Withdrawal Shortfall"] = shortfall
#         record["Tax Paid on Withdrawals (Inflation Adjusted)"] = (
#             total_tax_paid_today * cumulative_inflation
#         )
#         record["Tax Paid on Withdrawals (Today's Money)"] = total_tax_paid_today
#         record["State Pension (Inflation Adjusted)"] = sp_infl_adj
#         record["State Pension (Today's Money)"] = sp_todays
#         records.append(record)

#     result_df = pd.DataFrame(records)
#     return result_df


LOGGER = logging.getLogger(__name__)


class InvestmentSimulator:
    def __init__(self, profile: "ProfileSettings") -> None:
        self.profile = profile
        self.tax_year = profile.tax_year

        self._current_age = profile.personal_details.current_age
        self._retirement_age = profile.personal_details.retirement_age
        self._salary = profile.personal_details.salary
        self._take_home_salary = profile.personal_details.take_home_salary
        self._income_tax = profile.personal_details.income_tax
        self._ni_contribution = profile.personal_details.ni_contribution

        self._lisa_balance = profile.account_balances.lisa_balance
        self._isa_balance = profile.account_balances.isa_balance
        self._sipp_balance = profile.account_balances.sipp_balance
        self._workplace_balance = profile.account_balances.workplace_pension_balance

        self._lisa_net_contribution = 0.0
        self._isa_net_contribution = 0.0
        self._workplace_net_contribution = 0.0
        self._sipp_net_contribution = 0.0

        self._lisa_gross_contribution = 0.0
        self._isa_gross_contribution = 0.0
        self._workplace_gross_contribution = 0.0
        self._sipp_gross_contribution = 0.0

    def simulate(self) -> pd.DataFrame:
        simulation_years = self._retirement_age - self._current_age
        records: list[dict[str, Any]] = []
        for i in range(simulation_years):
            record: dict[str, Any] = {}

            age = self._current_age + i
            record["Age"] = age
            record["Salary"] = self._salary
            record["Take Home Salary"] = self._take_home_salary
            record["Income Tax"] = self._income_tax
            record["NI Contribution"] = self._ni_contribution

            record.update(self._calculate_lisa_contribution(age))
            record.update(self._calculate_isa_contribution(age))
            record.update(self._calculate_workplace_contribution())
            record.update(self._calculate_sipp_contribution(age))
            record.update(self._calculate_tax_relief_and_refund(record))
            record.update(self._aggregate_returns(record))

            records.append(record)
        return pd.DataFrame(records)

    def _calculate_lisa_contribution(self, age: int) -> dict[str, float]:
        lisa_maximum_contribution_age = LIMITS_DB[str(self.tax_year)].get(
            "lisa_maximum_contribution_age", 50
        )
        lisa_contribution = (
            self.profile.contribution_settings.lisa_contribution
            if age < lisa_maximum_contribution_age
            else 0.0
        )
        lisa_bonus = lisa_contribution * 0.25  # 25% bonus
        lisa_gross = lisa_contribution + lisa_bonus
        return {
            "LISA Net": lisa_contribution,
            "LISA Bonus": lisa_bonus,
            "LISA Gross": lisa_gross,
        }

    def _calculate_isa_contribution(self, age: int) -> dict[str, float]:
        isa_contribution = self.profile.contribution_settings.isa_contribution
        lisa_maximum_contribution_age = LIMITS_DB[str(self.tax_year)].get(
            "lisa_maximum_contribution_age", 50
        )
        if age >= lisa_maximum_contribution_age:
            post_50_lisa_to_isa = (
                self.profile.post_50_contribution_settings.post_50_lisa_to_isa_contribution
            )
            isa_contribution += post_50_lisa_to_isa
        return {"ISA Net": isa_contribution, "ISA Gross": isa_contribution}

    def _calculate_workplace_contribution(self) -> dict[str, float]:
        workplace_er_contribution = (
            self.profile.contribution_settings.workplace_er_contribution
        )
        workplace_ee_contribution = (
            self.profile.contribution_settings.workplace_ee_contribution
        )
        workplace_tax_relief = (
            workplace_ee_contribution * 0.25  # Assuming 25% tax relief
        )
        return {
            "Workplace ER": workplace_er_contribution,
            "Workplace EE Net": workplace_ee_contribution,
            "Workplace EE Gross": workplace_ee_contribution + workplace_tax_relief,
            "Workplace Tax Relief": workplace_tax_relief,
        }

    def _calculate_sipp_contribution(self, age: int) -> dict[str, float]:
        sipp_contribution = self.profile.contribution_settings.sipp_contribution
        lisa_maximum_contribution_age = LIMITS_DB[str(self.tax_year)].get(
            "lisa_maximum_contribution_age", 50
        )
        if age >= lisa_maximum_contribution_age:
            post_50_lisa_to_sipp = (
                self.profile.post_50_contribution_settings.post_50_lisa_to_sipp_contribution
            )
            sipp_contribution += post_50_lisa_to_sipp
        sipp_tax_relief = sipp_contribution * 0.25  # Assuming 25% tax relief
        return {
            "SIPP Net": sipp_contribution,
            "SIPP Gross": sipp_contribution + sipp_tax_relief,
            "SIPP Tax Relief": sipp_tax_relief,
        }

    def _calculate_tax_relief_and_refund(
        self, record: dict[str, float]
    ) -> dict[str, float]:
        tax_relief = record.get("Workplace Tax Relief", 0.0) + record.get(
            "SIPP Tax Relief", 0.0
        )
        total_ee_pension = record.get("Workplace EE Gross", 0.0) + record.get(
            "SIPP Gross", 0.0
        )

        pre_tax_salary = self.profile.personal_details.salary
        scotland = self.profile.scotland
        year = self.tax_year

        tax_before = calculate_income_tax(pre_tax_salary, scotland, year)
        tax_after = calculate_income_tax(
            pre_tax_salary - total_ee_pension, scotland, year
        )
        tax_refund = max(tax_before - tax_after - tax_relief, 0.0)
        return {
            "Tax Relief": tax_relief,
            "Tax Refund": tax_refund,
        }

    def _aggregate_returns(self, record: dict[str, Any]) -> dict[str, float]:
        self._lisa_balance += record.get("LISA Gross", 0.0)
        self._lisa_balance *= (
            1 + self.profile.expected_returns_and_inflation.expected_lisa_annual_return
        )
        self._isa_balance += record.get("LISA Gross", 0.0)
        self._isa_balance *= (
            1 + self.profile.expected_returns_and_inflation.expected_isa_annual_return
        )
        self._workplace_balance += record.get("Workplace EE Gross", 0.0) + record.get(
            "Workplace ER", 0.0
        )
        self._workplace_balance *= (
            1
            + self.profile.expected_returns_and_inflation.expected_workplace_annual_return
        )
        self._sipp_balance += record.get("SIPP Gross", 0.0)
        self._sipp_balance *= (
            1 + self.profile.expected_returns_and_inflation.expected_sipp_annual_return
        )

        self._lisa_net_contribution += record.get("LISA Net", 0.0)
        self._isa_net_contribution += record.get("ISA Net", 0.0)
        self._workplace_net_contribution += record.get("Workplace EE Net", 0.0)
        self._sipp_net_contribution += record.get("SIPP Net", 0.0)

        self._lisa_gross_contribution += record.get("LISA Gross", 0.0)
        self._isa_gross_contribution += record.get("ISA Gross", 0.0)
        self._workplace_gross_contribution += record.get(
            "Workplace EE Gross", 0.0
        ) + record.get("Workplace ER", 0.0)
        self._sipp_gross_contribution += record.get("SIPP Gross", 0.0)

        portfilo_balance = (
            self._lisa_balance
            + self._isa_balance
            + self._sipp_balance
            + self._workplace_balance
        )
        portfilo_net_contribution = (
            self._lisa_net_contribution
            + self._isa_net_contribution
            + self._workplace_net_contribution
            + self._sipp_net_contribution
        )
        portfilo_gross_contribution = (
            self._lisa_gross_contribution
            + self._isa_gross_contribution
            + self._workplace_gross_contribution
            + self._sipp_gross_contribution
        )

        annual_net_contribution = (
            record.get("LISA Net", 0.0)
            + record.get("ISA Net", 0.0)
            + record.get("Workplace EE Net", 0.0)
            + record.get("SIPP Net", 0.0)
        )
        annual_gross_contribution = (
            record.get("LISA Gross", 0.0)
            + record.get("ISA Gross", 0.0)
            + record.get("Workplace EE Gross", 0.0)
            + record.get("SIPP Gross", 0.0)
            + record.get("Workplace ER", 0.0)
        )

        return {
            "LISA Balance": self._lisa_balance,
            "ISA Balance": self._isa_balance,
            "Workplace Balance": self._workplace_balance,
            "SIPP Balance": self._sipp_balance,
            "LISA Net Contribution": self._lisa_net_contribution,
            "ISA Net Contribution": self._isa_net_contribution,
            "Workplace Net Contribution": self._workplace_net_contribution,
            "SIPP Net Contribution": self._sipp_net_contribution,
            "LISA Gross Contribution": self._lisa_gross_contribution,
            "ISA Gross Contribution": self._isa_gross_contribution,
            "Workplace Gross Contribution": self._workplace_gross_contribution,
            "SIPP Gross Contribution": self._sipp_gross_contribution,
            "Portfolio Balance": portfilo_balance,
            "Portfolio Net Contribution": portfilo_net_contribution,
            "Portfolio Gross Contribution": portfilo_gross_contribution,
            "Annual Net Contribution": annual_net_contribution,
            "Annual Gross Contribution": annual_gross_contribution,
        }


def project_investment(profile: "ProfileSettings") -> pd.DataFrame:
    simulator = InvestmentSimulator(profile)
    return simulator.simulate()


class RetirementSimulator:
    def __init__(
        self, profile: "ProfileSettings", investment_dataframe: pd.DataFrame
    ) -> None:
        self.profile = profile
        self.investment_dataframe = investment_dataframe
        self.tax_year = profile.tax_year
        self._annual_withdrawal = (
            profile.post_retirement_settings.withdrawal_today_amount
        )
        self._inflation = profile.expected_returns_and_inflation.expected_inflation

        self._current_age = profile.personal_details.current_age
        self._retirement_age = profile.personal_details.retirement_age
        self._simulation_end_age = 100
        self._lump_sum_allowance = LIMITS_DB[str(self.tax_year)].get(
            "lump_sum_allowance", 268275.0
        )
        self._state_pension_age = STATE_PENSION_DB[str(self.tax_year)].get(
            "state_pension_age", 67
        )
        self._state_pension_amount = STATE_PENSION_DB[str(self.tax_year)].get(
            "state_pension_per_year", 11502.0
        )

        retirement_data = investment_dataframe.iloc[-1]
        inflation_adjustment = self._inflation_adjustment(self._retirement_age)
        self._lisa_balance = retirement_data.get("LISA Balance", 0.0)
        self._isa_balance = retirement_data.get("ISA Balance", 0.0)
        self._pension_balance = retirement_data.get(
            "SIPP Balance", 0.0
        ) + retirement_data.get("Workplace Balance", 0.0)
        self._taxfree_pension_balance = min(
            self._pension_balance * 0.25,
            self._lump_sum_allowance * inflation_adjustment,
        )
        self._taxable_pension_balance = (
            self._pension_balance - self._taxfree_pension_balance
        )

        self._lisa_balance_todays = self._lisa_balance / inflation_adjustment
        self._isa_balance_todays = self._isa_balance / inflation_adjustment
        self._pension_balance_todays = self._pension_balance / inflation_adjustment
        self._taxfree_pension_balance_todays = (
            self._taxfree_pension_balance / inflation_adjustment
        )
        self._taxable_pension_balance_todays = (
            self._taxable_pension_balance / inflation_adjustment
        )

        self._accounts: list[str] = [
            "lisa",
            "isa",
            "taxfree_pension",
            "taxable_pension",
        ]

    def simulate(self) -> pd.DataFrame:
        percentage = (
            self.profile.post_retirement_settings.postret_isa_targeted_withdrawal_percentage
            + self.profile.post_retirement_settings.postret_lisa_targeted_withdrawal_percentage
            + self.profile.post_retirement_settings.postret_taxfree_pension_targeted_withdrawal_percentage
            + self.profile.post_retirement_settings.postret_taxable_pension_targeted_withdrawal_percentage
        )
        if percentage != 1.0:
            st.warning(
                f"Targeted withdrawal percentages do not sum to 100%. "
                f"Current sum is {percentage * 100:.2f}%. "
                f"Expected to be 100%."
            )
            return pd.DataFrame()

        simluation_years = self._simulation_end_age - self._retirement_age
        records: list[dict[str, Any]] = []
        for i in range(simluation_years):
            record: dict[str, Any] = {}

            age = self._retirement_age + i
            inflation_adjustment = self._inflation_adjustment(age)
            record["Age"] = age

            record.update(self._calculate_withdrawal_amount(inflation_adjustment))
            record.update(self._calculate_state_pension(age, inflation_adjustment))
            record.update(
                self._calculate_accounts_withdrawal_and_income_tax(
                    age, inflation_adjustment, record
                )
            )

            records.append(record)
        return pd.DataFrame(records)

    def _calculate_withdrawal_amount(
        self, inflation_adjustment: float
    ) -> dict[str, float]:
        return {
            "Withdrawal Today": self._annual_withdrawal,
            "Withdrawal Inflation Adjusted": self._annual_withdrawal
            * inflation_adjustment,
        }

    def _calculate_state_pension(
        self, age: int, inflation_adjustment: float
    ) -> dict[str, float]:
        if age >= self._state_pension_age:
            sp_infl_adj = self._state_pension_amount * inflation_adjustment
            sp_todays = self._state_pension_amount
        else:
            sp_infl_adj = 0.0
            sp_todays = 0.0
        return {
            "State Pension Today": sp_todays,
            "State Pension Inflation Adjusted": sp_infl_adj,
        }

    def _calculate_accounts_withdrawal_and_income_tax(
        self, age: int, inflation_adjustment: float, record: dict[str, float]
    ) -> dict[str, float]:
        targeted_amount = self._annual_withdrawal
        withdraw_plan = self._get_withdraw_plan(age)
        state_pension = record.get("State Pension Today", 0.0)

        targeted_amount_left = targeted_amount - state_pension
        if targeted_amount_left <= 0:
            withdrawal_lisa = 0.0
            withdrawal_isa = 0.0
            withdrawal_taxfree_pension = 0.0
            withdrawal_taxable_pension = 0.0
        else:
            withdrawal_lisa = withdraw_plan["lisa"] * targeted_amount_left
            withdrawal_isa = withdraw_plan["isa"] * targeted_amount_left
            withdrawal_taxfree_pension = (
                withdraw_plan["taxfree_pension"] * targeted_amount_left
            )
            withdrawal_taxable_pension = (
                withdraw_plan["taxable_pension"] * targeted_amount_left
            )
        withdrawal_taxable_pension_tax = calculate_gross_from_take_home(
            withdrawal_taxable_pension,
            self.profile.scotland,
            self.tax_year,
            state_pension,
        )
        income_tax = calculate_income_tax(
            income=withdrawal_taxable_pension_tax + state_pension,
            scotland=self.profile.scotland,
            year=self.tax_year,
        )
        total_withdrawal = (
            withdrawal_lisa
            + withdrawal_isa
            + withdrawal_taxfree_pension
            + withdrawal_taxable_pension
            + state_pension
        )
        total_withdrawal_tax = total_withdrawal + state_pension

        shortfall_today = 0.0
        account_flags = [False] * len(self._accounts)
        if self._lisa_balance_todays >= withdrawal_lisa:
            self._lisa_balance_todays -= withdrawal_lisa
        else:
            shortfall_today -= self._lisa_balance_todays - withdrawal_lisa
            self._lisa_balance_todays = 0.0
            account_flags[0] = True
        if self._isa_balance_todays >= withdrawal_isa:
            self._isa_balance_todays -= withdrawal_isa
        else:
            shortfall_today -= self._isa_balance_todays - withdrawal_isa
            self._isa_balance_todays = 0.0
            account_flags[1] = True
        if self._taxfree_pension_balance_todays >= withdrawal_taxfree_pension:
            self._taxfree_pension_balance_todays -= withdrawal_taxfree_pension
        else:
            shortfall_today -= (
                self._taxfree_pension_balance_todays - withdrawal_taxfree_pension
            )
            self._taxfree_pension_balance_todays = 0.0
            account_flags[2] = True
        if self._taxable_pension_balance_todays >= withdrawal_taxable_pension:
            self._taxable_pension_balance_todays -= withdrawal_taxable_pension
        else:
            shortfall_today -= (
                self._taxable_pension_balance_todays - withdrawal_taxable_pension
            )
            self._taxable_pension_balance_todays = 0.0
            account_flags[3] = True

        available_accounts = len(account_flags) - sum(account_flags)
        iter = 0
        while available_accounts > 0 and shortfall_today > 0 and iter < 3:
            shortfall_today_per_account = shortfall_today / available_accounts
            for f, account in zip(account_flags, self._accounts):
                if account == "lisa":
                    if not f:
                        if self._lisa_balance_todays >= shortfall_today_per_account:
                            self._lisa_balance_todays -= shortfall_today_per_account
                            shortfall_today -= shortfall_today_per_account
                            withdrawal_isa += shortfall_today_per_account
                        else:
                            shortfall_today -= self._lisa_balance_todays
                            withdrawal_isa += self._lisa_balance_todays
                            self._lisa_balance_todays = 0.0
                            account_flags[0] = True
                elif account == "isa":
                    if not f:
                        if self._isa_balance_todays >= shortfall_today_per_account:
                            self._isa_balance_todays -= shortfall_today_per_account
                            shortfall_today -= shortfall_today_per_account
                            withdrawal_isa += shortfall_today_per_account
                        else:
                            shortfall_today -= self._isa_balance_todays
                            withdrawal_isa += self._isa_balance_todays
                            self._isa_balance_todays = 0.0
                            account_flags[1] = True
                elif account == "taxfree_pension":
                    if not f:
                        if (
                            self._taxfree_pension_balance_todays
                            >= shortfall_today_per_account
                        ):
                            self._taxfree_pension_balance_todays -= (
                                shortfall_today_per_account
                            )
                            shortfall_today -= shortfall_today_per_account
                            withdrawal_taxfree_pension += shortfall_today_per_account
                        else:
                            shortfall_today -= self._taxfree_pension_balance_todays
                            withdrawal_taxfree_pension += (
                                self._taxfree_pension_balance_todays
                            )
                            self._taxfree_pension_balance_todays = 0.0
                            account_flags[2] = True
                elif account == "taxable_pension":
                    if not f:
                        if (
                            self._taxable_pension_balance_todays
                            >= shortfall_today_per_account
                        ):
                            self._taxable_pension_balance_todays -= (
                                shortfall_today_per_account
                            )
                            shortfall_today -= shortfall_today_per_account
                            withdrawal_taxable_pension += shortfall_today_per_account
                        else:
                            shortfall_today -= self._taxable_pension_balance_todays
                            withdrawal_taxable_pension += (
                                self._taxable_pension_balance_todays
                            )
                            self._taxable_pension_balance_todays = 0.0
                            account_flags[3] = True
            available_accounts = len(account_flags) - sum(account_flags)
            iter += 1

        self._lisa_balance_todays = self._lisa_balance_todays * (
            1
            + self.profile.post_retirement_settings.expected_post_retirement_lisa_annual_return
        )
        self._isa_balance_todays = self._isa_balance_todays * (
            1
            + self.profile.post_retirement_settings.expected_post_retirement_isa_annual_return
        )
        self._taxfree_pension_balance_todays = self._taxfree_pension_balance_todays * (
            1
            + self.profile.post_retirement_settings.expected_post_retirement_pension_annual_return
        )
        self._taxable_pension_balance_todays = self._taxable_pension_balance_todays * (
            1
            + self.profile.post_retirement_settings.expected_post_retirement_pension_annual_return
        )
        self._pension_balance_todays = (
            self._taxfree_pension_balance_todays + self._taxable_pension_balance_todays
        )

        self._lisa_balance = self._lisa_balance_todays * inflation_adjustment
        self._isa_balance = self._isa_balance_todays * inflation_adjustment
        self._taxfree_pension_balance = (
            self._taxfree_pension_balance_todays * inflation_adjustment
        )
        self._taxable_pension_balance = (
            self._taxable_pension_balance_todays * inflation_adjustment
        )
        self._pension_balance = (
            self._taxfree_pension_balance + self._taxable_pension_balance
        )

        return {
            "Withdrawal LISA Today": withdrawal_lisa,
            "Withdrawal ISA Today": withdrawal_isa,
            "Withdrawal Tax-Free Pension Today": withdrawal_taxfree_pension,
            "Withdrawal Taxable Pension Today": withdrawal_taxable_pension,
            "Withdrawal LISA Inflation Adjusted": withdrawal_lisa
            * inflation_adjustment,
            "Withdrawal ISA Inflation Adjusted": withdrawal_isa * inflation_adjustment,
            "Withdrawal Tax-Free Pension Inflation Adjusted": withdrawal_taxfree_pension
            * inflation_adjustment,
            "Withdrawal Taxable Pension Inflation Adjusted": withdrawal_taxable_pension
            * inflation_adjustment,
            "Income Tax Today": income_tax,
            "Income Tax Inflation Adjusted": income_tax * inflation_adjustment,
            "Toal Withdrawal Today": total_withdrawal,
            "Total Withdrawal Inflation Adjusted": total_withdrawal
            * inflation_adjustment,
            "Total Withdrawal Tax Today": total_withdrawal_tax,
            "Total Withdrawal Tax Inflation Adjusted": total_withdrawal_tax
            * inflation_adjustment,
            "Shortfall Today": shortfall_today,
            "Shortfall Inflation Adjusted": shortfall_today * inflation_adjustment,
            "LISA Balance Today": self._lisa_balance_todays,
            "ISA Balance Today": self._isa_balance_todays,
            "Tax-Free Pension Balance Today": self._taxfree_pension_balance_todays,
            "Taxable Pension Balance Today": self._taxable_pension_balance_todays,
            "LISA Balance Inflation Adjusted": self._lisa_balance,
            "ISA Balance Inflation Adjusted": self._isa_balance,
            "Tax-Free Pension Balance Inflation Adjusted": self._taxfree_pension_balance,
            "Taxable Pension Balance Inflation Adjusted": self._taxable_pension_balance,
            "Pension Balance Today": self._pension_balance_todays,
            "Pension Balance Inflation Adjusted": self._pension_balance,
        }

    def _get_withdraw_plan(self, age: int) -> dict[str, float]:
        retirement_settings = {
            "lisa": {
                "age": self.profile.post_retirement_settings.postret_lisa_withdrawal_age,
                "percentage": self.profile.post_retirement_settings.postret_lisa_targeted_withdrawal_percentage,
                "redistribute": age
                < self.profile.post_retirement_settings.postret_lisa_withdrawal_age,
            },
            "isa": {
                "age": self.profile.post_retirement_settings.postret_isa_withdrawal_age,
                "percentage": self.profile.post_retirement_settings.postret_isa_targeted_withdrawal_percentage,
                "redistribute": age
                < self.profile.post_retirement_settings.postret_isa_withdrawal_age,
            },
            "taxfree_pension": {
                "age": self.profile.post_retirement_settings.postret_taxfree_pension_withdrawal_age,
                "percentage": self.profile.post_retirement_settings.postret_taxfree_pension_targeted_withdrawal_percentage,
                "redistribute": age
                < self.profile.post_retirement_settings.postret_taxfree_pension_withdrawal_age,
            },
            "taxable_pension": {
                "age": self.profile.post_retirement_settings.postret_taxable_pension_withdrawal_age,
                "percentage": self.profile.post_retirement_settings.postret_taxable_pension_targeted_withdrawal_percentage,
                "redistribute": age
                < self.profile.post_retirement_settings.postret_taxable_pension_withdrawal_age,
            },
        }

        account_flags = [False] * len(self._accounts)
        for i, account in enumerate(self._accounts):
            account_flags[i] = bool(retirement_settings[account]["redistribute"])

        plan = {}
        unavailable_accounts = sum(account_flags)
        redistribution_size = 0.0
        for f, account in zip(account_flags, self._accounts):
            if f:
                redistribution_size += retirement_settings[account]["percentage"]
        redistribution_size_per_account = (
            redistribution_size / (len(self._accounts) - unavailable_accounts)
            if unavailable_accounts > 0
            else 0.0
        )

        for f, account in zip(account_flags, self._accounts):
            if not f:
                plan[account] = (
                    retirement_settings[account]["percentage"]
                    + redistribution_size_per_account
                )
            else:
                plan[account] = 0.0
        return plan

    def _inflation_adjustment(self, age: int) -> float:
        years = age - self._current_age
        return (1 + self._inflation) ** years


def project_retirement(
    profile: "ProfileSettings", investment_dataframe: pd.DataFrame
) -> pd.DataFrame:
    simulator = RetirementSimulator(profile, investment_dataframe)
    return simulator.simulate()
