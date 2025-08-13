"""
Core retirement projection calculations for Planwise.

This module contains the main projection function that models retirement
savings across various UK tax wrappers over time. It provides dataclasses for user
profile, contribution rates, and investment returns, as well as helper functions for
calculating contributions and projecting account balances.
"""

from typing import Any

import pandas as pd
import streamlit as st

from planwise.streamlit.sidebar_utils import ProfileSettings

from .databases import LIMITS_DB, STATE_PENSION_DB
from .tax import calculate_gross_from_take_home, calculate_income_tax


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
        self._isa_balance += record.get("ISA Gross", 0.0)
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
            "Withdrawal State Pension Today": sp_todays,
            "Withdrawal State Pension Inflation Adjusted": sp_infl_adj,
        }

    def _calculate_accounts_withdrawal_and_income_tax(
        self, age: int, inflation_adjustment: float, record: dict[str, float]
    ) -> dict[str, float]:
        targeted_amount = self._annual_withdrawal
        withdraw_plan = self._get_withdraw_plan(age)
        state_pension = record.get("Withdrawal State Pension Today", 0.0)
        shortfall_today = 0.0

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
            if withdrawal_taxable_pension > self._taxable_pension_balance_todays:
                shortfall_today = (
                    withdrawal_taxable_pension - self._taxable_pension_balance_todays
                )
                withdrawal_taxable_pension = self._taxable_pension_balance_todays
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

        account_flags = [False] * len(self._accounts)
        if self._lisa_balance_todays >= withdrawal_lisa:
            self._lisa_balance_todays -= withdrawal_lisa
        else:
            shortfall_today -= self._lisa_balance_todays - withdrawal_lisa
            withdrawal_lisa = self._lisa_balance_todays
            self._lisa_balance_todays = 0.0
            account_flags[0] = True
        if self._isa_balance_todays >= withdrawal_isa:
            self._isa_balance_todays -= withdrawal_isa
        else:
            shortfall_today -= self._isa_balance_todays - withdrawal_isa
            withdrawal_isa = self._isa_balance_todays
            self._isa_balance_todays = 0.0
            account_flags[1] = True
        if self._taxfree_pension_balance_todays >= withdrawal_taxfree_pension:
            self._taxfree_pension_balance_todays -= withdrawal_taxfree_pension
        else:
            shortfall_today -= (
                self._taxfree_pension_balance_todays - withdrawal_taxfree_pension
            )
            withdrawal_taxfree_pension = self._taxfree_pension_balance_todays
            self._taxfree_pension_balance_todays = 0.0
            account_flags[2] = True
        if withdrawal_taxfree_pension > 61000:
            st.write(
                f"Withdrawal from tax-free pension exceeds £61,000: {withdrawal_taxfree_pension}."
            )
        if self._taxable_pension_balance_todays >= withdrawal_taxable_pension_tax:
            self._taxable_pension_balance_todays -= withdrawal_taxable_pension_tax
        else:
            shortfall_today -= (
                self._taxable_pension_balance_todays - withdrawal_taxable_pension_tax
            )
            withdrawal_taxable_pension = self._taxable_pension_balance_todays
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
                            withdrawal_lisa += shortfall_today_per_account
                        else:
                            shortfall_today -= self._lisa_balance_todays
                            withdrawal_lisa += self._lisa_balance_todays
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

        self._lisa_balance = self._lisa_balance_todays * inflation_adjustment
        self._isa_balance = self._isa_balance_todays * inflation_adjustment
        self._taxfree_pension_balance = (
            self._taxfree_pension_balance_todays * inflation_adjustment
        )
        self._taxable_pension_balance = (
            self._taxable_pension_balance_todays * inflation_adjustment
        )

        self._lisa_balance *= (
            1
            + self.profile.post_retirement_settings.expected_post_retirement_lisa_annual_return
        )
        self._isa_balance *= (
            1
            + self.profile.post_retirement_settings.expected_post_retirement_isa_annual_return
        )
        self._taxable_pension_balance *= (
            1
            + self.profile.post_retirement_settings.expected_post_retirement_pension_annual_return
        )
        self._taxable_pension_balance += self._taxfree_pension_balance * (
            self.profile.post_retirement_settings.expected_post_retirement_pension_annual_return
        )
        self._pension_balance = (
            self._taxfree_pension_balance + self._taxable_pension_balance
        )
        total_balance = self._lisa_balance + self._isa_balance + self._pension_balance

        self._lisa_balance_todays = self._lisa_balance / inflation_adjustment
        self._isa_balance_todays = self._isa_balance / inflation_adjustment
        self._taxfree_pension_balance_todays = (
            self._taxfree_pension_balance / inflation_adjustment
        )
        self._taxable_pension_balance_todays = (
            self._taxable_pension_balance / inflation_adjustment
        )
        self._pension_balance_todays = (
            self._taxfree_pension_balance_todays + self._taxable_pension_balance_todays
        )
        total_balance_today = (
            self._lisa_balance_todays
            + self._isa_balance_todays
            + self._pension_balance_todays
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
            "Total Withdrawal Today": total_withdrawal,
            "Total Withdrawal Inflation Adjusted": total_withdrawal
            * inflation_adjustment,
            "Total Withdrawal After Tax Today": total_withdrawal_tax,
            "Total Withdrawal After Tax Inflation Adjusted": total_withdrawal_tax
            * inflation_adjustment,
            "Withdrawal Shortfall Today": shortfall_today,
            "Withdrawal Shortfall Inflation Adjusted": shortfall_today
            * inflation_adjustment,
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
            "Total Balance Today": total_balance_today,
            "Total Balance Inflation Adjusted": total_balance,
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


def project_investment(profile: "ProfileSettings") -> pd.DataFrame:
    simulator = InvestmentSimulator(profile)
    return simulator.simulate()


def project_retirement(
    profile: "ProfileSettings", investment_dataframe: pd.DataFrame
) -> pd.DataFrame:
    simulator = RetirementSimulator(profile, investment_dataframe)
    return simulator.simulate()
