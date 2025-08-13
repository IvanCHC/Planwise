"""
Tax calculations for UK income tax and pension relief in Planwise.

This module loads tax band data and provides functions to compute income tax for both
Scottish and rest-of-UK tax bands, including the calculation of tax relief on pension contributions.
"""

from typing import Tuple

from .databases import TAX_BANDS_DB


def _get_tax_bands(scotland: bool, year: int = 2025) -> Tuple[list, float]:
    """
    Return income tax bands and personal allowance for the selected region and year.
    Args:
        scotland (bool): True for Scottish tax bands; False for rest of UK.
        year (int): Tax year (e.g., 2025 for 2025/26). Defaults to 2025.
    Returns:
        tuple: (list of TaxBand, personal allowance)
    Raises:
        ValueError: If year is not found.
    """
    db = TAX_BANDS_DB.get(year)
    if db is None:
        raise ValueError(f"No tax band data for year {year}")
    region = "scotland" if scotland else "rest_of_uk"
    region_data = db.get(region)
    return region_data["bands"], region_data["personal_allowance"]


def calculate_income_tax(income: float, scotland: bool, year: int = 2025) -> float:
    """
    Compute income tax payable on taxable income.
    Args:
        income (float): Taxable income (after personal allowance and before relief adjustments).
        scotland (bool): Use Scottish tax bands if True.
        year (int): Tax year (e.g., 2025 for 2025/26). Defaults to 2025.
    Returns:
        float: Tax payable in pounds.
    """
    bands, personal_allowance = _get_tax_bands(scotland, year)
    # Remove personal allowance from income
    taxable = max(income - personal_allowance, 0)
    tax_due = 0.0
    previous_threshold = personal_allowance

    for band in bands:
        # For the last band, assume rate applies to all income above the threshold
        if taxable <= 0:
            break
        band_income = min(taxable, band.threshold - previous_threshold)
        tax_due += band_income * band.rate
        taxable -= band_income
        previous_threshold = band.threshold

    return tax_due


from functools import lru_cache


@lru_cache(maxsize=None)
def calculate_gross_from_take_home(
    take_home: float, scotland: bool, year: int = 2025, state_pension: float = 0
) -> float:
    """
    Calculate the gross income required to achieve a specific take-home amount.

    Args:
        take_home (float): Desired take-home income after tax.
        scotland (bool): Use Scottish tax bands if True.
        year (int): Tax year (e.g., 2025 for 2025/26). Defaults to 2025.
        state_pension (float): Annual state pension amount to reduce personal allowance.

    Returns:
        float: Gross income required to achieve the take-home amount.
    """
    bands, personal_allowance = _get_tax_bands(scotland, year)

    # Reduce personal allowance by state pension amount
    effective_personal_allowance = max(personal_allowance - state_pension, 0)

    # Binary search approach for more accurate calculation
    low, high = 0.0, take_home * 2  # Upper bound estimate
    tolerance = 0.001

    iter = 0
    while high - low > tolerance and iter < 20:
        mid = (low + high) / 2
        calculated_tax = calculate_income_tax(mid, scotland, year)

        # Adjust tax calculation for state pension impact on personal allowance
        if state_pension > 0:
            # Recalculate tax with reduced personal allowance
            taxable = max(mid - effective_personal_allowance, 0)
            calculated_tax = 0.0
            previous_threshold = effective_personal_allowance

            for band in bands:
                if taxable <= 0:
                    break
                band_income = min(taxable, band.threshold - previous_threshold)
                calculated_tax += band_income * band.rate
                taxable -= band_income
                previous_threshold = band.threshold

        net_income = mid - calculated_tax

        if net_income < take_home:
            low = mid
        else:
            high = mid
        iter += 1

    return (low + high) / 2
