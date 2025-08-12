"""
Tax calculations for UK income tax and pension relief in Planwise.

This module loads tax band data and provides functions to compute income tax for both
Scottish and rest-of-UK tax bands, including the calculation of tax relief on pension contributions.
"""

import json
import os
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class TaxBand:
    """
    Represents a single tax band.
    Attributes:
        threshold (float): Lower threshold of the band.
        rate (float): Marginal tax rate in decimal.
    """

    threshold: float
    rate: float


def load_tax_bands_db() -> dict:
    """
    Load tax band data from a JSON file and construct a nested dictionary of tax bands by year and region.
    Returns:
        dict: Tax band information by year and region.
    """
    json_path = os.path.join(os.path.dirname(__file__), "data", "tax_bands.json")
    with open(json_path, "r") as f:
        raw_db = json.load(f)
    db: dict = {}
    for year, regions in raw_db.items():
        db[int(year)] = {}
        for region, data in regions.items():
            bands = []
            for band in data["bands"]:
                threshold = band["threshold"]
                if isinstance(threshold, str) and threshold == "inf":
                    threshold = float("inf")
                bands.append(TaxBand(threshold=threshold, rate=band["rate"]))
            db[int(year)][region] = {
                "personal_allowance": data["personal_allowance"],
                "bands": bands,
            }
    return db


TAX_BANDS_DB = load_tax_bands_db()


def get_tax_bands(scotland: bool, year: int = 2025) -> Tuple[list, float]:
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
    bands, personal_allowance = get_tax_bands(scotland, year)
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
    bands, personal_allowance = get_tax_bands(scotland, year)

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
