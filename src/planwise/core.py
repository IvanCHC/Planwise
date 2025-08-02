"""
Core retirement projection calculations.

This module contains the main projection function that models retirement
savings across various UK tax wrappers over time.
"""

from typing import Dict, List

import pandas as pd

from .tax import calculate_income_tax


def project_retirement(
    current_age: int,
    retirement_age: int,
    salary: float,
    lisa_contrib_rate: float,
    isa_contrib_rate: float,
    sipp_employee_rate: float,
    sipp_employer_rate: float,
    workplace_employee_rate: float,
    workplace_employer_rate: float,
    shift_lisa_to_isa: float,
    shift_lisa_to_sipp: float,
    roi_lisa: float,
    roi_isa: float,
    roi_sipp: float,
    roi_workplace: float,
    inflation: float,
    scotland: bool,
    use_qualifying_earnings: bool,
    year: int,
) -> pd.DataFrame:
    """Compute the year‑by‑year contributions, tax relief and account balances.

    Parameters
    ----------
    current_age : int
        The individual's current age.
    retirement_age : int
        Age at which the individual stops contributing.
    salary : float
        Starting salary (annual). This will be indexed by inflation each year.
    lisa_contrib_rate : float
        Proportion of salary contributed to the LISA (percentage as decimal). Applies only up to
        age 50.
    isa_contrib_rate : float
        Proportion of salary contributed to the general ISA.
    sipp_employee_rate : float
        Employee contribution rate to a personal SIPP (as a percentage of salary).
    sipp_employer_rate : float
        Employer contribution rate to personal SIPP (rare; set to 0 if none).
    workplace_employee_rate : float
        Employee contribution rate to the workplace pension.
    workplace_employer_rate : float
        Employer contribution rate to the workplace pension.
    shift_lisa_to_isa : float
        Fraction (0‑1) of LISA contributions that is redirected to the ISA after age 50.
    shift_lisa_to_sipp : float
        Fraction (0‑1) of LISA contributions redirected to the SIPP after age 50 (should sum
        with shift_lisa_to_isa to 1).
    roi_lisa : float
        Expected annual rate of return for the LISA (decimal).
    roi_isa : float
        Expected annual rate of return for the ISA (decimal).
    roi_sipp : float
        Expected annual rate of return for the SIPP (decimal).
    roi_workplace : float
        Expected annual rate of return for the workplace pension (decimal).
    inflation : float
        Annual inflation rate used to index salary and contributions (decimal).
    scotland : bool
        True for Scottish tax calculations; False for rest of UK.
    use_qualifying_earnings : bool
        If True, workplace pension contributions are calculated on qualifying earnings
        (£6,240–£50,270). Otherwise contributions are based on total salary.
    year : int
        Tax year to use for income tax calculations (e.g., 2025 for 2025/26).

    Returns
    -------
    pd.DataFrame
        DataFrame with each year's age and financial metrics.
    """
    years = retirement_age - current_age

    # Constants
    qualifying_lower = 6_240.0
    qualifying_upper = 50_270.0
    lisa_limit = 4_000.0
    isa_limit = 20_000.0
    pension_annual_allowance = 60_000.0
    personal_allowance = 12_570.0

    # Preallocate lists for results
    records: List[Dict] = []

    # Starting pots
    pot_lisa = 0.0
    pot_isa = 0.0
    pot_sipp = 0.0
    pot_workplace = 0.0
    current_salary = salary

    for year_index in range(years):
        age = current_age + year_index

        # Determine LISA contribution rate: active until age < 50
        this_lisa_rate = lisa_contrib_rate if age < 50 else 0.0

        # Determine shift amounts after 50
        lisa_to_isa_rate = shift_lisa_to_isa if age >= 50 else 0.0
        lisa_to_sipp_rate = shift_lisa_to_sipp if age >= 50 else 0.0

        # Determine the contribution bases
        if use_qualifying_earnings:
            qualifying_salary = min(
                max(current_salary - qualifying_lower, 0),
                qualifying_upper - qualifying_lower,
            )
            base_for_workplace = qualifying_salary
        else:
            base_for_workplace = current_salary

        # LISA contributions
        lisa_net = current_salary * this_lisa_rate
        # Cap by LISA annual allowance
        if lisa_net > lisa_limit:
            lisa_net = lisa_limit
        lisa_bonus = lisa_net * 0.25  # 25 % government bonus
        lisa_gross = lisa_net + lisa_bonus

        # If over age 50, redirect LISA contribution amount into ISA and SIPP
        redirected_amount = current_salary * lisa_contrib_rate if age >= 50 else 0.0
        redirected_isa_net = redirected_amount * lisa_to_isa_rate
        redirected_sipp_net = redirected_amount * lisa_to_sipp_rate

        # ISA contributions (net)
        isa_net = current_salary * isa_contrib_rate + redirected_isa_net
        # Cap ISA contributions by remaining allowance after LISA (gross). The LISA gross counts towards the £20k allowance.
        # This model ignores carry forward; if exceed, contributions are simply truncated.
        remaining_isa_allowance = isa_limit - (lisa_gross if this_lisa_rate > 0 else 0)
        if isa_net > remaining_isa_allowance:
            isa_net = remaining_isa_allowance

        # SIPP personal contributions (employee) – relief at source
        sipp_employee_net = current_salary * sipp_employee_rate + redirected_sipp_net
        sipp_employee_gross = sipp_employee_net / 0.8 if sipp_employee_net > 0 else 0.0

        # Employer contributions into SIPP (rare); no tax relief needed
        sipp_employer_gross = current_salary * sipp_employer_rate

        # Workplace pension contributions – relief at source (employee)
        wp_employee_net = base_for_workplace * workplace_employee_rate
        wp_employee_gross = wp_employee_net / 0.8 if wp_employee_net > 0 else 0.0

        # Employer contributions to workplace pension
        wp_employer_gross = base_for_workplace * workplace_employer_rate

        # Total gross pension contributions (employee and employer)
        total_pension_gross = (
            sipp_employee_gross
            + sipp_employer_gross
            + wp_employee_gross
            + wp_employer_gross
        )

        # Ensure we do not exceed annual allowance; cap employee contributions to respect the allowance
        if total_pension_gross > pension_annual_allowance:
            # Adjust the largest employee contribution (SIPP) first
            excess = total_pension_gross - pension_annual_allowance
            if sipp_employee_gross >= excess:
                sipp_employee_gross -= excess
                sipp_employee_net = sipp_employee_gross * 0.8
                excess = 0
            else:
                excess -= sipp_employee_gross
                sipp_employee_gross = 0
                sipp_employee_net = 0
                # Next adjust workplace employee
                if wp_employee_gross >= excess:
                    wp_employee_gross -= excess
                    wp_employee_net = wp_employee_gross * 0.8
                    excess = 0
                else:
                    excess -= wp_employee_gross
                    wp_employee_gross = 0
                    wp_employee_net = 0
            total_pension_gross = pension_annual_allowance

        # Tax calculations
        # Taxable income before relief = salary (contributions paid from net pay do not reduce taxable income)
        tax_before = calculate_income_tax(current_salary, scotland, year=year)
        # Taxable income after relief = salary - total gross personal contributions (employee only). Employer contributions do not reduce taxable income.
        # For relief at source, contributions are grossed up (we subtract the gross personal contributions). This reduces the amount of income taxed at higher rates.
        total_personal_gross = sipp_employee_gross + wp_employee_gross
        tax_after = calculate_income_tax(
            max(current_salary - total_personal_gross, 0), scotland, year=year
        )
        tax_relief_total = tax_before - tax_after

        # 20 % basic relief has already been granted by the pension provider; additional relief is refundable
        basic_relief = total_personal_gross * 0.20
        tax_refund = max(tax_relief_total - basic_relief, 0)

        # Net cost to the individual
        net_contrib_total = sipp_employee_net + wp_employee_net + lisa_net + isa_net
        net_cost_after_refund = net_contrib_total - tax_refund

        # Update pots by adding gross contributions and applying growth
        pot_lisa = pot_lisa * (1 + roi_lisa) + lisa_gross
        pot_isa = (
            pot_isa * (1 + roi_isa) + isa_net
        )  # ISA contributions are net; no extra relief
        pot_sipp = pot_sipp * (1 + roi_sipp) + sipp_employee_gross + sipp_employer_gross
        pot_workplace = (
            pot_workplace * (1 + roi_workplace) + wp_employee_gross + wp_employer_gross
        )

        # Record results
        records.append(
            {
                "Age": age,
                "Salary": current_salary,
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
                "Net Contribution Cost": net_cost_after_refund,
                "Pot LISA": pot_lisa,
                "Pot ISA": pot_isa,
                "Pot SIPP": pot_sipp,
                "Pot Workplace": pot_workplace,
            }
        )

        # Inflate salary for next year
        current_salary *= 1 + inflation

    df = pd.DataFrame(records)
    return df
