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

from .tax import calculate_income_tax


def load_state_pension_db() -> Any:
    json_path = os.path.join(os.path.dirname(__file__), "data", "state_pension.json")
    with open(json_path, "r") as f:
        return json.load(f)


STATE_PENSION_DB = load_state_pension_db()


@dataclass
class UserProfile:
    """
    User profile for retirement projection.
    Attributes:
        current_age (int): Current age of the user.
        retirement_age (int): Target retirement age.
        salary (float): Current annual salary.
        scotland (bool): Use Scottish tax bands if True.
    """

    current_age: int
    retirement_age: int
    salary: float
    scotland: bool


@dataclass
class ContributionRates:
    """
    Contribution rates for each account type and post-50 redirection.
    Attributes:
        lisa (float): LISA contribution rate.
        isa (float): ISA contribution rate.
        sipp_employee (float): SIPP employee contribution rate.
        sipp_employer (float): SIPP employer contribution rate.
        workplace_employee (float): Workplace pension employee rate.
        workplace_employer (float): Workplace pension employer rate.
        shift_lisa_to_isa (float): Fraction of LISA redirected to ISA after 50.
        shift_lisa_to_sipp (float): Fraction of LISA redirected to SIPP after 50.
    """

    lisa: float
    isa: float
    sipp_employee: float
    sipp_employer: float
    workplace_employee: float
    workplace_employer: float
    shift_lisa_to_isa: float
    shift_lisa_to_sipp: float


@dataclass
class InvestmentReturns:
    """
    Expected annual rates of return for each account type.
    Attributes:
        lisa (float): LISA annual return.
        isa (float): ISA annual return.
        sipp (float): SIPP annual return.
        workplace (float): Workplace pension annual return.
    """

    lisa: float
    isa: float
    sipp: float
    workplace: float


@dataclass
class IncomeBreakdown:
    """
    Breakdown of income sources for retirement projection.
    Attributes:
        salary (float): Annual salary.
        take_home_salary (float): Net salary after tax and NI.
        income_tax (float): Total income tax due.
        ni_due (float): National Insurance contributions due.
    """

    salary: float
    take_home_salary: float
    income_tax: float
    ni_due: float


def load_limits_db() -> Any:
    """
    Load annual limits and constants from JSON file.
    Returns:
        dict: Limits for each tax year.
    """
    json_path = os.path.join(os.path.dirname(__file__), "data", "limits.json")
    with open(json_path, "r") as f:
        return json.load(f)


def calculate_lisa_isa_contributions(
    current_salary: float,
    age: int,
    contrib: ContributionRates,
    lisa_limit: float,
    isa_limit: float,
) -> dict:
    """
    Calculate LISA and ISA contributions, including redirection after age 50.
    Args:
        current_salary (float): Current annual salary.
        age (int): Current age.
        contrib (ContributionRates): Contribution rates.
        lisa_limit (float): Annual LISA contribution limit.
        isa_limit (float): Annual ISA contribution limit.
    Returns:
        dict: Calculated net/gross contributions and redirections.
    """
    # LISA contributions (only allowed under age 50)
    this_lisa_rate = contrib.lisa if age < 50 else 0.0
    lisa_net = current_salary * this_lisa_rate
    if lisa_net > lisa_limit:
        lisa_net = lisa_limit
    lisa_bonus = lisa_net * 0.25
    lisa_gross = lisa_net + lisa_bonus

    # If over age 50, redirect LISA contribution amount into ISA and SIPP
    lisa_to_isa_rate = contrib.shift_lisa_to_isa if age >= 50 else 0.0
    lisa_to_sipp_rate = contrib.shift_lisa_to_sipp if age >= 50 else 0.0
    redirected_amount = current_salary * contrib.lisa if age >= 50 else 0.0
    redirected_isa_net = redirected_amount * lisa_to_isa_rate

    # ISA contributions (net)
    isa_net = current_salary * contrib.isa + redirected_isa_net
    remaining_isa_allowance = isa_limit - (lisa_net if this_lisa_rate > 0 else 0)
    if isa_net > remaining_isa_allowance:
        isa_net = remaining_isa_allowance

    # For SIPP redirection
    redirected_sipp_net = redirected_amount * lisa_to_sipp_rate

    return {
        "lisa_net": lisa_net,
        "lisa_bonus": lisa_bonus,
        "lisa_gross": lisa_gross,
        "isa_net": isa_net,
        "redirected_sipp_net": redirected_sipp_net,
    }


def calculate_pension_contributions(
    current_salary: float,
    base_for_workplace: float,
    contrib: ContributionRates,
    redirected_sipp_net: float,
) -> dict:
    """
    Calculate SIPP and workplace pension contributions.
    Args:
        current_salary (float): Current annual salary.
        base_for_workplace (float): Salary base for workplace pension (may be qualifying earnings).
        contrib (ContributionRates): Contribution rates.
        redirected_sipp_net (float): Amount redirected to SIPP from LISA after age 50.
    Returns:
        dict: Calculated net/gross contributions for SIPP and workplace pension.
    """
    # SIPP personal contributions (employee) – relief at source
    sipp_employee_net = current_salary * contrib.sipp_employee + redirected_sipp_net
    sipp_employee_gross = sipp_employee_net / 0.8 if sipp_employee_net > 0 else 0.0

    # Employer contributions into SIPP (rare); no tax relief needed
    sipp_employer_gross = current_salary * contrib.sipp_employer

    # Workplace pension contributions – relief at source (employee)
    wp_employee_net = base_for_workplace * contrib.workplace_employee
    wp_employee_gross = wp_employee_net / 0.8 if wp_employee_net > 0 else 0.0

    # Employer contributions to workplace pension
    wp_employer_gross = base_for_workplace * contrib.workplace_employer

    return {
        "sipp_employee_net": sipp_employee_net,
        "sipp_employee_gross": sipp_employee_gross,
        "sipp_employer_gross": sipp_employer_gross,
        "wp_employee_net": wp_employee_net,
        "wp_employee_gross": wp_employee_gross,
        "wp_employer_gross": wp_employer_gross,
    }


LIMITS_DB = load_limits_db()


class RetirementSimulator:
    """Helper class to encapsulate retirement projection logic.

    This class encapsulates the year–by–year simulation of retirement contributions,
    tax relief and pot growth.  Breaking the logic out of the top–level
    :func:`project_retirement` improves readability and makes it easier to
    reason about intermediate calculations.  The public :meth:`simulate` method
    produces a DataFrame identical to the original implementation, so
    existing code and tests that rely on :func:`project_retirement` continue
    to work unchanged.
    """

    def __init__(
        self,
        user: UserProfile,
        contrib: ContributionRates,
        returns: InvestmentReturns,
        income: IncomeBreakdown,
        inflation: float,
        use_qualifying_earnings: bool,
        year: int,
    ) -> None:
        self.user = user
        self.contrib = contrib
        self.returns = returns
        self.income = income
        self.inflation = inflation
        self.use_qualifying = use_qualifying_earnings
        self.year = year

        # Load annual limits for the selected tax year
        limits = LIMITS_DB[str(year)]
        self.qualifying_lower = limits["qualifying_lower"]
        self.qualifying_upper = limits["qualifying_upper"]
        self.lisa_limit = limits["lisa_limit"]
        self.isa_limit = limits["isa_limit"]
        self.pension_annual_allowance = limits["pension_annual_allowance"]

        # Initialise pots and accumulators
        self.pot_lisa: float = 0.0
        self.pot_isa: float = 0.0
        self.pot_sipp: float = 0.0
        self.pot_workplace: float = 0.0

        self.acc_lisa_net: float = 0.0
        self.acc_lisa_gross: float = 0.0
        self.acc_isa_net: float = 0.0
        self.acc_isa_gross: float = 0.0
        self.acc_sipp_net: float = 0.0
        self.acc_sipp_gross: float = 0.0
        self.acc_workplace_net: float = 0.0
        self.acc_workplace_gross: float = 0.0

        # For contributions we base on take–home salary to mirror
        # the original implementation
        self.take_home_salary = income.take_home_salary
        self.current_salary = user.salary

    def _base_for_workplace(self) -> Any:
        """Calculate the earnings base for workplace contributions.

        Returns the qualifying portion of salary when qualifying
        earnings are enabled.  Otherwise returns the full take–home
        salary.
        """
        if self.use_qualifying:
            qualifying_salary = min(
                max(self.take_home_salary - self.qualifying_lower, 0.0),
                self.qualifying_upper - self.qualifying_lower,
            )
            return qualifying_salary
        else:
            return self.take_home_salary

    def _apply_annual_allowance(
        self,
        sipp_employee_net: float,
        sipp_employee_gross: float,
        sipp_employer_gross: float,
        wp_employee_net: float,
        wp_employee_gross: float,
        wp_employer_gross: float,
    ) -> tuple:
        """Apply the pension annual allowance to employee contributions.

        This function caps total gross pension contributions to the annual
        allowance.  Employee gross contributions are reduced first (SIPP
        followed by workplace) while employer contributions are left
        untouched.  The corresponding net amounts are recomputed from the
        adjusted gross values.

        Parameters
        ----------
        sipp_employee_net : float
            Net SIPP contribution by the employee.
        sipp_employee_gross : float
            Gross SIPP contribution by the employee.
        sipp_employer_gross : float
            Employer SIPP contributions (no relief at source).
        wp_employee_net : float
            Net workplace pension contribution by the employee.
        wp_employee_gross : float
            Gross workplace pension contribution by the employee.
        wp_employer_gross : float
            Employer workplace pension contributions.

        Returns
        -------
        tuple
            A tuple containing the potentially reduced employee net/gross
            contributions and the unchanged employer contributions.
        """
        # Total gross pension contributions (employee and employer)
        total_pension_gross = (
            sipp_employee_gross
            + sipp_employer_gross
            + wp_employee_gross
            + wp_employer_gross
        )
        if total_pension_gross > self.pension_annual_allowance:
            excess = total_pension_gross - self.pension_annual_allowance
            # Reduce SIPP employee gross first
            if sipp_employee_gross >= excess:
                sipp_employee_gross -= excess
                sipp_employee_net = sipp_employee_gross * 0.8
                excess = 0.0
            else:
                excess -= sipp_employee_gross
                sipp_employee_gross = 0.0
                sipp_employee_net = 0.0
                # Then reduce workplace employee gross
                if wp_employee_gross >= excess:
                    wp_employee_gross -= excess
                    wp_employee_net = wp_employee_gross * 0.8
                    excess = 0.0
                else:
                    excess -= wp_employee_gross
                    wp_employee_gross = 0.0
                    wp_employee_net = 0.0
            # Employer contributions are not reduced, but we cap the recorded total
        return (
            sipp_employee_net,
            sipp_employee_gross,
            sipp_employer_gross,
            wp_employee_net,
            wp_employee_gross,
            wp_employer_gross,
        )

    def _compute_tax_relief(self, total_personal_gross: float) -> tuple:
        """Compute the tax relief for personal pension contributions.

        The function calculates income tax before and after personal
        contributions and derives the total relief, basic relief at source
        and any additional refund due.  Note that employer contributions
        do not affect tax relief.

        Parameters
        ----------
        total_personal_gross : float
            Sum of gross SIPP and workplace contributions made by the employee.

        Returns
        -------
        tuple
            A tuple ``(tax_relief_total, basic_relief, tax_refund)`` where:

            * ``tax_relief_total`` is the difference in income tax before and after contributions.
            * ``basic_relief`` represents the 20 % relief at source already applied by providers.
            * ``tax_refund`` is any additional refund due back to the individual.
        """
        # Tax before contributions (using gross salary)
        tax_before = calculate_income_tax(
            self.current_salary, self.user.scotland, year=self.year
        )
        # Tax after employee contributions (gross contributions reduce taxable income)
        taxable_income_after = max(self.current_salary - total_personal_gross, 0.0)
        tax_after = calculate_income_tax(
            taxable_income_after, self.user.scotland, year=self.year
        )
        tax_relief_total = tax_before - tax_after
        # Basic 20% relief granted at source
        basic_relief = total_personal_gross * 0.20
        tax_refund = max(tax_relief_total - basic_relief, 0.0)
        return (tax_relief_total, basic_relief, tax_refund)

    def _update_pots(
        self,
        lisa_gross: float,
        lisa_net: float,
        isa_net: float,
        sipp_employee_gross: float,
        sipp_employer_gross: float,
        wp_employee_gross: float,
        wp_employer_gross: float,
    ) -> None:
        """Update pot values and accumulated contributions.

        Applies annual growth to each pot and adds the new contributions.
        Also updates running totals of net and gross contributions for each
        wrapper.  This method mutates the simulator state and has no return.
        """
        # Update accumulated contributions
        self.acc_lisa_net += lisa_net
        self.acc_lisa_gross += lisa_gross
        self.acc_isa_net += isa_net
        self.acc_isa_gross += isa_net  # ISA gross = net
        # Employee SIPP net is recalculated outside this method; we expect caller to
        # pass the correct net amount after any allowance adjustments.
        # The gross amount includes employee and employer contributions here.
        # For net accumulation, we only include the employee net; employers
        # contributions are not a cost to the individual.
        # We intentionally do not accumulate employer net because it is 0 by definition.
        # SIPP net contributions accumulate from outside.
        # Accumulate SIPP nets and grosses
        # (these will be updated in the main loop to include the adjusted net/gross)
        # We do not update them here to avoid double counting.

        # Update pot balances with growth
        self.pot_lisa = self.pot_lisa * (1.0 + self.returns.lisa) + lisa_gross
        self.pot_isa = self.pot_isa * (1.0 + self.returns.isa) + isa_net
        self.pot_sipp = (
            self.pot_sipp * (1.0 + self.returns.sipp)
            + sipp_employee_gross
            + sipp_employer_gross
        )
        self.pot_workplace = (
            self.pot_workplace * (1.0 + self.returns.workplace)
            + wp_employee_gross
            + wp_employer_gross
        )

    def simulate(self) -> pd.DataFrame:
        """Run the simulation and return a DataFrame of results.

        This method iterates from the user's current age up to (but not
        including) their retirement age.  For each year it calculates
        contributions, applies the annual allowance, computes tax relief,
        updates pots and accumulators, and records the results.  Finally it
        returns the accumulated results as a pandas DataFrame with
        inflation–adjusted pot columns added if an inflation rate was
        provided.
        """
        years = self.user.retirement_age - self.user.current_age
        records: List[Dict[str, Any]] = []
        # Local variables for accumulated SIPP and workplace nets/grosses
        acc_sipp_net_local = 0.0
        acc_sipp_gross_local = 0.0
        acc_workplace_net_local = 0.0
        acc_workplace_gross_local = 0.0
        for i in range(years):
            age = self.user.current_age + i
            # Determine base for workplace contributions
            base_for_workplace = self._base_for_workplace()
            # LISA/ISA contributions and redirections
            lisa_isa = calculate_lisa_isa_contributions(
                current_salary=self.take_home_salary,
                age=age,
                contrib=self.contrib,
                lisa_limit=self.lisa_limit,
                isa_limit=self.isa_limit,
            )
            lisa_net = lisa_isa["lisa_net"]
            lisa_bonus = lisa_isa["lisa_bonus"]
            lisa_gross = lisa_isa["lisa_gross"]
            isa_net = lisa_isa["isa_net"]
            redirected_sipp_net = lisa_isa["redirected_sipp_net"]

            # Pension contributions (SIPP + workplace)
            pensions = calculate_pension_contributions(
                current_salary=self.take_home_salary,
                base_for_workplace=base_for_workplace,
                contrib=self.contrib,
                redirected_sipp_net=redirected_sipp_net,
            )
            sipp_employee_net = pensions["sipp_employee_net"]
            sipp_employee_gross = pensions["sipp_employee_gross"]
            sipp_employer_gross = pensions["sipp_employer_gross"]
            wp_employee_net = pensions["wp_employee_net"]
            wp_employee_gross = pensions["wp_employee_gross"]
            wp_employer_gross = pensions["wp_employer_gross"]

            # Apply annual allowance
            (
                sipp_employee_net,
                sipp_employee_gross,
                sipp_employer_gross,
                wp_employee_net,
                wp_employee_gross,
                wp_employer_gross,
            ) = self._apply_annual_allowance(
                sipp_employee_net,
                sipp_employee_gross,
                sipp_employer_gross,
                wp_employee_net,
                wp_employee_gross,
                wp_employer_gross,
            )

            # Tax relief calculation
            total_personal_gross = sipp_employee_gross + wp_employee_gross
            tax_relief_total, basic_relief, tax_refund = self._compute_tax_relief(
                total_personal_gross
            )

            # Net cost to the individual
            net_contrib_total = sipp_employee_net + wp_employee_net + lisa_net + isa_net
            net_cost_after_refund = net_contrib_total - tax_refund

            # Update accumulators for SIPP and workplace nets/grosses (employee + employer for gross)
            acc_sipp_net_local += sipp_employee_net
            acc_sipp_gross_local += sipp_employee_gross + sipp_employer_gross
            acc_workplace_net_local += wp_employee_net
            acc_workplace_gross_local += wp_employee_gross + wp_employer_gross

            # Update pots and global accumulators for LISA/ISA
            self._update_pots(
                lisa_gross=lisa_gross,
                lisa_net=lisa_net,
                isa_net=isa_net,
                sipp_employee_gross=sipp_employee_gross,
                sipp_employer_gross=sipp_employer_gross,
                wp_employee_gross=wp_employee_gross,
                wp_employer_gross=wp_employer_gross,
            )

            # Record results for the year
            record = {
                "Age": age,
                "Salary": self.current_salary,
                "Take-home Salary": self.income.take_home_salary,
                "Income Tax": self.income.income_tax,
                "NI Contribution": self.income.ni_due,
                "LISA Net": lisa_net,
                "LISA Bonus": lisa_bonus,
                "ISA Net": isa_net,
                "SIPP Employee Net": sipp_employee_net,
                "SIPP Employee Gross": sipp_employee_gross,
                "SIPP Employer": sipp_employer_gross,
                "Workplace Employee Net": wp_employee_net,
                "Workplace Employee Gross": wp_employee_gross,
                "Workplace Employer": wp_employer_gross,
                "Tax Relief (total)": tax_relief_total,
                "Tax Refund": tax_refund,
                "Total Contribution Cost": net_contrib_total,
                "Net Contribution Cost": net_cost_after_refund,
                "Pot LISA": self.pot_lisa,
                "Pot ISA": self.pot_isa,
                "Pot SIPP": self.pot_sipp,
                "Pot Workplace": self.pot_workplace,
                "Accumulated LISA Net": self.acc_lisa_net,
                "Accumulated LISA Gross": self.acc_lisa_gross,
                "Accumulated ISA Net": self.acc_isa_net,
                "Accumulated ISA Gross": self.acc_isa_gross,
                "Accumulated SIPP Net": acc_sipp_net_local,
                "Accumulated SIPP Gross": acc_sipp_gross_local,
                "Accumulated Workplace Net": acc_workplace_net_local,
                "Accumulated Workplace Gross": acc_workplace_gross_local,
            }
            records.append(record)

        df = pd.DataFrame(records)
        # Add inflation adjusted values
        if self.inflation is not None and len(df) > 0:
            # Compute cumulative inflation factor for each year
            inflation_rate_col = pd.Series([self.inflation] * len(df))
            cumulative_inflation = (1.0 + inflation_rate_col).cumprod()
            cumulative_inflation.iloc[0] = 1.0
            for pot in ["Pot LISA", "Pot ISA", "Pot SIPP", "Pot Workplace"]:
                if pot in df.columns:
                    df[f"{pot} (Inflation Adjusted)"] = df[pot] / cumulative_inflation
        return df


def project_retirement(
    user: UserProfile,
    contrib: ContributionRates,
    returns: InvestmentReturns,
    income: IncomeBreakdown,
    inflation: float,
    use_qualifying_earnings: bool,
    year: int,
) -> pd.DataFrame:
    """
    Compute the year-by-year contributions, tax relief, and account balances.

    This convenience function wraps the :class:`RetirementSimulator` class.
    It constructs a simulator, runs the projection and returns the result as
    a DataFrame.  The signature is kept for backwards compatibility with
    existing code and tests.

    Parameters
    ----------
    user : UserProfile
        User profile including age, retirement age, salary, and region.
    contrib : ContributionRates
        Contribution rates for each wrapper and shift rates after age 50.
    returns : InvestmentReturns
        Expected annual rates of return for each wrapper.
    income : IncomeBreakdown
        Income breakdown including take-home salary, tax and NI.  The
        take-home salary is used as the base for percentage contributions.
    inflation : float
        Annual inflation rate used to index pot values.
    use_qualifying_earnings : bool
        If ``True``, workplace pension contributions are calculated on
        qualifying earnings (currently £6,240–£50,270).  Otherwise,
        contributions are based on the full salary.
    year : int
        Tax year used for income tax and limit calculations (e.g., 2025
        corresponds to the 2025/26 tax year).

    Returns
    -------
    pd.DataFrame
        A DataFrame with each year's age and financial metrics.  Inflation
        adjusted pot values are appended with ``(Inflation Adjusted)`` if
        an inflation rate is provided.
    """
    simulator = RetirementSimulator(
        user=user,
        contrib=contrib,
        returns=returns,
        income=income,
        inflation=inflation,
        use_qualifying_earnings=use_qualifying_earnings,
        year=year,
    )
    return simulator.simulate()


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


def _returns_to_dict_postret(returns: InvestmentReturns) -> dict:
    return {
        "LISA": getattr(returns, "lisa", 0.0),
        "ISA": getattr(returns, "isa", 0.0),
        "SIPP": getattr(returns, "sipp", 0.0),
        "Workplace": getattr(returns, "workplace", 0.0),
    }


from typing import Optional


def project_post_retirement(
    df: pd.DataFrame,
    withdrawal_today: float,
    returns: InvestmentReturns,
    withdraw_plan: list,
    inflation: float = 0.02,
    end_age: int = 100,
    current_age: int = 30,
    year: int = 2025,
    scotland: bool = False,
    pension_tax_free_fraction: float = 0.25,
    state_pension_age: Optional[int] = None,
    state_pension_amount: Optional[float] = None,
    uprate_state_pension: Optional[bool] = None,
) -> pd.DataFrame:
    """
    Project post-retirement account balances and withdrawals using a drawdown strategy.

    Args:
        df (pd.DataFrame): DataFrame of historical pots (must include 'Age' and 'Pot <Account>' columns).
        withdrawal_today (float): Annual withdrawal in today's money.
        returns (InvestmentReturns): Expected annual rates of return for each account.
        withdraw_plan (list): List of dicts specifying withdrawal order and eligibility.
        inflation (float, optional): Annual inflation rate. Default is 0.02.
        end_age (int, optional): Final age for projection. Default is 100.

    Returns:
        pd.DataFrame: DataFrame with projected balances, withdrawals, and shortfall per year.
    """
    if df.empty:
        raise ValueError("Input data frame must not be empty.")
    if "Age" not in df.columns:
        raise ValueError("Input data frame must contain an 'Age' column.")

    df_sorted = df.sort_values("Age")
    account_columns = _find_account_columns_postret(df_sorted)
    # Build starting pots, combining SIPP and Workplace into Pension
    starting_pots: Dict[str, float] = {}
    for acc, col in account_columns.items():
        if acc == "Pension":
            sipp = (
                float(df_sorted["Pot SIPP"].iloc[-1])
                if "Pot SIPP" in df_sorted.columns
                else 0.0
            )
            workplace = (
                float(df_sorted["Pot Workplace"].iloc[-1])
                if "Pot Workplace" in df_sorted.columns
                else 0.0
            )
            starting_pots["Pension"] = sipp + workplace
        else:
            starting_pots[acc] = float(df_sorted[col].iloc[-1])
    # Build ROIs, combining SIPP and Workplace into Pension
    account_rois = _returns_to_dict_postret(returns)
    if "Pension" in starting_pots:
        sipp_roi = getattr(returns, "sipp", 0.0)
        workplace_roi = getattr(returns, "workplace", 0.0)
        sipp = (
            float(df_sorted["Pot SIPP"].iloc[-1])
            if "Pot SIPP" in df_sorted.columns
            else 0.0
        )
        workplace = (
            float(df_sorted["Pot Workplace"].iloc[-1])
            if "Pot Workplace" in df_sorted.columns
            else 0.0
        )
        total = sipp + workplace
        if total > 0:
            pension_roi = (sipp * sipp_roi + workplace * workplace_roi) / total
        else:
            pension_roi = max(sipp_roi, workplace_roi)
        account_rois["Pension"] = pension_roi
        # remove SIPP and Workplace ROI entries, since they are combined
        account_rois.pop("SIPP", None)
        account_rois.pop("Workplace", None)

    # --- Split Pension into tax-free and taxable accounts ---
    # If a combined Pension pot exists, divide it into tax-free and tax portions.
    # The default fraction of the pension that can be withdrawn tax-free (pension_tax_free_fraction)
    # can be overridden via function parameter. This splitting occurs only at the start
    # of the post-retirement projection and does not reallocate funds between the sub-accounts
    # thereafter. Both sub-accounts earn the same ROI as the original Pension.
    if "Pension" in starting_pots:
        total_pension = starting_pots.pop("Pension")
        total_pension = max(total_pension, 0.0)
        tax_free_balance = min(
            total_pension * pension_tax_free_fraction, 268275
        )  # 2025/26 LTA
        taxable_balance = total_pension - tax_free_balance
        starting_pots["Pension Tax Free"] = tax_free_balance
        starting_pots["Pension Tax"] = taxable_balance
        pension_roi = account_rois.pop("Pension")
        account_rois["Pension Tax Free"] = pension_roi
        account_rois["Pension Tax"] = pension_roi

    # Preprocess withdrawal plan
    # Expand references to Pension (or SIPP/Workplace) into separate tax-free and taxable accounts
    plan: List[Dict[str, Any]] = []
    for entry in withdraw_plan:
        if "account" not in entry or "start_age" not in entry:
            raise ValueError(
                "Each withdraw_plan entry must include both 'account' and 'start_age'."
            )
        acc_original = entry["account"]
        start_age = int(entry["start_age"])
        proportion = entry.get("proportion", None)
        # Determine if this entry targets the combined Pension or its components
        if acc_original in ("Pension", "SIPP", "Workplace") and (
            "Pension Tax Free" in starting_pots or "Pension Tax" in starting_pots
        ):
            # If a proportion is provided, allocate it between the tax-free and taxable pots
            if proportion is not None:
                prop_free = proportion * pension_tax_free_fraction
                prop_tax = proportion * (1.0 - pension_tax_free_fraction)
                if prop_free > 0.0:
                    plan.append(
                        {
                            "account": "Pension Tax Free",
                            "start_age": start_age,
                            "proportion": prop_free,
                        }
                    )
                if prop_tax > 0.0:
                    plan.append(
                        {
                            "account": "Pension Tax",
                            "start_age": start_age,
                            "proportion": prop_tax,
                        }
                    )
            else:
                # Sequential withdrawals: add both sub-accounts without proportions
                plan.append(
                    {
                        "account": "Pension Tax Free",
                        "start_age": start_age,
                        "proportion": None,
                    }
                )
                plan.append(
                    {
                        "account": "Pension Tax",
                        "start_age": start_age,
                        "proportion": None,
                    }
                )
        else:
            acc = acc_original
            if acc not in starting_pots:
                raise ValueError(
                    f"Account '{acc}' in withdraw_plan not found in input data."
                )
            plan.append(
                {
                    "account": acc,
                    "start_age": start_age,
                    "proportion": proportion,
                }
            )

    # --- State Pension Projection ---
    # Determine state pension parameters.  Values provided via function
    # arguments take precedence over the defaults loaded from the database.
    sp_data = STATE_PENSION_DB.get(str(year), {})
    sp_age_default = sp_data.get("state_pension_age", 67)
    sp_amount_default = sp_data.get("state_pension_per_year", 11000.0)
    uprate_inflation_default = sp_data.get("uprate_inflation", True)
    # Use overrides if provided, otherwise fall back to defaults
    sp_age = state_pension_age if state_pension_age is not None else sp_age_default
    sp_per_year = (
        state_pension_amount
        if state_pension_amount is not None
        else sp_amount_default
    )
    uprate_inflation = (
        uprate_state_pension
        if uprate_state_pension is not None
        else uprate_inflation_default
    )

    records: List[Dict[str, Any]] = []
    pots = starting_pots.copy()
    # Iterate over each year from the first year after retirement to end_age
    for age in range(int(df_sorted["Age"].iloc[-1]) + 1, end_age + 1):
        # Grow each pot according to its ROI
        for acc, value in pots.items():
            growth_rate = account_rois.get(acc, 0.0)
            pots[acc] = value * (1.0 + growth_rate)

        # Inflation adjustment based on years since current age
        years_since_current = age - current_age
        cumulative_inflation = (1.0 + inflation) ** years_since_current
        # Base withdrawal adjusted for inflation
        withdrawal_infl_adj = withdrawal_today * cumulative_inflation

        # Compute state pension for this age
        if age >= sp_age:
            if uprate_inflation:
                sp_infl_adj = sp_per_year * cumulative_inflation
                sp_todays = sp_per_year
            else:
                sp_infl_adj = sp_per_year
                sp_todays = sp_per_year / cumulative_inflation
        else:
            sp_infl_adj = 0.0
            sp_todays = 0.0

        # Determine the net withdrawal required from the pots after accounting for state pension
        withdrawal_from_pots_infl = max(withdrawal_infl_adj - sp_infl_adj, 0.0)
        withdrawal_from_pots_today = max(withdrawal_today - sp_todays, 0.0)

        # Track current taxable income to compute incremental tax on pension withdrawals
        taxable_income_so_far_today = sp_todays  # <-- use today's money
        total_tax_paid_today = 0.0
        remaining_net_to_fund_today = withdrawal_from_pots_today

        # Identify plan entries active at this age
        active_plan = [p for p in plan if age >= p["start_age"]]
        total_prop = sum(
            p["proportion"] for p in active_plan if p["proportion"] is not None
        )
        if total_prop > 1.0 + 1e-9:
            raise ValueError(
                f"Sum of proportions in withdraw_plan entries active at age {age} exceeds 1."
            )

        # Helper function to compute gross withdrawal needed to achieve a net-of-tax amount (today's money)
        def compute_gross_from_net_today(
            net_required: float, taxable_base: float
        ) -> float:
            if net_required <= 0.0:
                return 0.0
            tax_at_base = calculate_income_tax(taxable_base, scotland, year)

            def f(gross: float) -> float:
                tax_total = calculate_income_tax(taxable_base + gross, scotland, year)
                tax_due = tax_total - tax_at_base
                return gross - tax_due - net_required

            low = 0.0
            high = net_required * 2.0 + 1.0
            while f(high) < 0.0:
                high *= 2.0
            for _ in range(40):
                mid = (low + high) / 2.0
                if f(mid) > 0.0:
                    high = mid
                else:
                    low = mid
            return high

        # Proportional withdrawals (net-of-tax basis, today's money)
        if total_prop > 0.0 and remaining_net_to_fund_today > 0.0:
            for p_entry in active_plan:
                proportion = p_entry["proportion"]
                acc = p_entry["account"]
                if proportion is None:
                    continue
                alloc_net_today = withdrawal_from_pots_today * proportion
                if alloc_net_today <= 0.0:
                    continue
                if acc == "Pension Tax":
                    gross_needed_today = compute_gross_from_net_today(
                        alloc_net_today, taxable_income_so_far_today
                    )
                    gross_taken_today = min(
                        gross_needed_today, pots.get(acc, 0.0) / cumulative_inflation
                    )
                    # Compute tax on this gross withdrawal
                    tax_after = calculate_income_tax(
                        taxable_income_so_far_today + gross_taken_today, scotland, year
                    )
                    tax_before = calculate_income_tax(
                        taxable_income_so_far_today, scotland, year
                    )
                    tax_due_today = tax_after - tax_before
                    net_taken_today = gross_taken_today - tax_due_today
                    pots[acc] -= (
                        gross_taken_today * cumulative_inflation
                    )  # convert back to future value
                    taxable_income_so_far_today += gross_taken_today
                    total_tax_paid_today += tax_due_today
                    remaining_net_to_fund_today -= net_taken_today
                    if remaining_net_to_fund_today < 0.0:
                        remaining_net_to_fund_today = 0.0
                else:
                    net_taken_today = min(
                        alloc_net_today, pots.get(acc, 0.0) / cumulative_inflation
                    )
                    pots[acc] -= net_taken_today * cumulative_inflation
                    remaining_net_to_fund_today -= net_taken_today
                    if remaining_net_to_fund_today < 0.0:
                        remaining_net_to_fund_today = 0.0

        # Sequential withdrawals once proportional allocations are handled (today's money)
        if remaining_net_to_fund_today > 1e-9:
            for p_entry in active_plan:
                if p_entry["proportion"] is not None:
                    continue
                acc = p_entry["account"]
                if remaining_net_to_fund_today <= 0.0:
                    break
                if pots.get(acc, 0.0) <= 0.0:
                    continue
                if acc == "Pension Tax":
                    alloc_net_today = remaining_net_to_fund_today
                    gross_needed_today = compute_gross_from_net_today(
                        alloc_net_today, taxable_income_so_far_today
                    )
                    gross_taken_today = min(
                        gross_needed_today, pots.get(acc, 0.0) / cumulative_inflation
                    )
                    tax_after = calculate_income_tax(
                        taxable_income_so_far_today + gross_taken_today, scotland, year
                    )
                    tax_before = calculate_income_tax(
                        taxable_income_so_far_today, scotland, year
                    )
                    tax_due_today = tax_after - tax_before
                    net_taken_today = gross_taken_today - tax_due_today
                    pots[acc] -= gross_taken_today * cumulative_inflation
                    taxable_income_so_far_today += gross_taken_today
                    total_tax_paid_today += tax_due_today
                    remaining_net_to_fund_today -= net_taken_today
                    if remaining_net_to_fund_today < 0.0:
                        remaining_net_to_fund_today = 0.0
                else:
                    net_taken_today = min(
                        remaining_net_to_fund_today,
                        pots.get(acc, 0.0) / cumulative_inflation,
                    )
                    pots[acc] -= net_taken_today * cumulative_inflation
                    remaining_net_to_fund_today -= net_taken_today
                    if remaining_net_to_fund_today < 0.0:
                        remaining_net_to_fund_today = 0.0
                if remaining_net_to_fund_today <= 1e-9:
                    break

        shortfall_today = (
            remaining_net_to_fund_today if remaining_net_to_fund_today > 1e-9 else 0.0
        )
        shortfall = shortfall_today * cumulative_inflation

        total_pot = sum(pots.values())
        total_pot_todays = (
            total_pot / cumulative_inflation
            if cumulative_inflation > 0.0
            else total_pot
        )

        record: Dict[str, Any] = {
            "Age": age,
            "Withdrawal (Inflation Adjusted)": withdrawal_from_pots_infl,
            "Withdrawal (Today's Money)": withdrawal_from_pots_today,
        }
        for acc, value in pots.items():
            record[f"Pot {acc}"] = value
        record["Total Pot"] = total_pot
        record["Total Pot (Today's Money)"] = total_pot_todays
        record["Remaining Withdrawal Shortfall"] = shortfall
        record["Tax Paid on Withdrawals (Inflation Adjusted)"] = (
            total_tax_paid_today * cumulative_inflation
        )
        record["Tax Paid on Withdrawals (Today's Money)"] = total_tax_paid_today
        record["State Pension (Inflation Adjusted)"] = sp_infl_adj
        record["State Pension (Today's Money)"] = sp_todays
        records.append(record)

    result_df = pd.DataFrame(records)
    return result_df
