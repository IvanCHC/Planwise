"""
Tax calculations for UK income tax and pension relief.

This module handles income tax calculations for both Scottish and rest-of-UK
tax bands, including the calculation of tax relief on pension contributions.
"""

import json
import os
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class TaxBand:
    """Represents a single tax band."""

    threshold: float  # lower threshold of the band
    rate: float  # marginal tax rate in decimal


def load_tax_bands_db() -> dict:
    """
    Loads tax band data from a JSON file and constructs a nested dictionary of tax bands by year and region.

    The function reads the 'tax_bands.json' file located in the 'data' directory relative to the current file.
    It parses the JSON content and converts each tax band entry into a TaxBand object.
    The resulting dictionary is structured as follows:
        {
            year (int): {
                region (str): {
                    "personal_allowance": value,
                    "bands": [TaxBand, ...]
                },
                ...
            },
            ...

    Returns:
        dict: A nested dictionary containing tax band information by year and region.
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


def get_tax_bands(scotland: bool, year: int = 2025) -> Tuple[List[TaxBand], float]:
    """Return income tax bands and personal allowance for the selected region and year.

    Parameters
    ----------
    scotland : bool
        True for Scottish tax bands; False for rest of UK.
    year : int, optional
        Tax year (e.g., 2025 for 2025/26). Defaults to 2025.

    Returns
    -------
    Tuple[List[TaxBand], float]
        A tuple of (list of TaxBand, personal allowance)
    """
    db = TAX_BANDS_DB.get(year)
    if db is None:
        raise ValueError(f"No tax band data for year {year}")
    region = "scotland" if scotland else "rest_of_uk"
    region_data = db.get(region)
    return region_data["bands"], region_data["personal_allowance"]


def calculate_income_tax(income: float, scotland: bool, year: int = 2025) -> float:
    """Compute income tax payable on taxable income.

    Parameters
    ----------
    income : float
        Taxable income (after personal allowance and before relief adjustments).
    scotland : bool
        Use Scottish tax bands if True.
    year : int, optional
        Tax year (e.g., 2025 for 2025/26). Defaults to 2025.

    Returns
    -------
    float
        Tax payable in pounds.
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
