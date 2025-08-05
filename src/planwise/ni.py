"""
National Insurance (NI) calculations for UK employees.

This module loads NI band data and provides functions to compute employee NI contributions
for a given year and category.
"""

import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass
class NICBand:
    """
    Represents a single National Insurance band.
    Attributes:
        threshold (float): Lower threshold of the band.
        rate (float): NI rate as a decimal.
    """

    threshold: float
    rate: float


def load_ni_bands_db() -> dict:
    """
    Load NI band data from a JSON file and construct a nested dictionary of NI bands by year and category.
    Returns:
        dict: NI bands by year and category.
    """
    json_path = os.path.join(os.path.dirname(__file__), "data", "ni_bands.json")
    with open(json_path, "r") as f:
        raw_db = json.load(f)
    db: dict = {}
    for year, categories in raw_db.items():
        db[int(year)] = {}
        for category, data in categories.items():
            bands = []
            for band in data["bands"]:
                threshold = band["threshold"]
                if isinstance(threshold, str) and threshold == "inf":
                    threshold = float("inf")
                bands.append(NICBand(threshold=threshold, rate=band["rate"]))
            db[int(year)][category] = bands
    return db


NI_BANDS_DB = load_ni_bands_db()


def get_ni_bands(year: int = 2025, category: str = "category_a") -> Any:
    """
    Return the National Insurance bands for the given year and category.
    Args:
        year (int): Tax year.
        category (str): NI category (e.g., 'category_a').
    Returns:
        list[NICBand]: List of NI bands for the year and category.
    Raises:
        ValueError: If year or category is not found.
    """
    db = NI_BANDS_DB.get(year)
    if db is None:
        raise ValueError(f"No NI band data for year {year}")
    bands = db.get(category)
    if bands is None:
        raise ValueError(f"No NI band data for category {category} in year {year}")
    return bands


def calculate_ni(
    income: float, year: int = 2025, category: str = "category_a"
) -> float:
    """
    Compute employee National Insurance contributions for the given category.

    Args:
        income (float): Gross annual income.
        year (int): Tax year (default 2025).
        category (str): NI category (default 'category_a').
    Returns:
        float: National Insurance contribution due.
    """
    if income <= 0:
        return 0.0
    bands = get_ni_bands(year, category)
    ni_due = 0.0
    previous_threshold = 0.0

    for band in bands:
        if income <= band.threshold:
            ni_due += max(0.0, income - previous_threshold) * band.rate
            break
        else:
            ni_due += (band.threshold - previous_threshold) * band.rate
            previous_threshold = band.threshold

    return ni_due
