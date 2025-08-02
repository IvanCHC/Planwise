"""
Tax calculations for UK income tax and pension relief.

This module handles income tax calculations for both Scottish and rest-of-UK
tax bands, including the calculation of tax relief on pension contributions.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class TaxBand:
    """Represents a single tax band."""

    threshold: float  # lower threshold of the band
    rate: float  # marginal tax rate in decimal


def get_tax_bands(scotland: bool) -> Tuple[List[TaxBand], float]:
    """Return income tax bands and personal allowance for the selected region.

    Parameters
    ----------
    scotland : bool
        True for Scottish tax bands; False for rest of UK.

    Returns
    -------
    Tuple[List[TaxBand], float]
        A tuple of (list of TaxBand, personal allowance)
    """
    personal_allowance = 12_570.0
    if scotland:
        # Scottish bands for 2025/26: thresholds include personal allowance
        bands = [
            TaxBand(threshold=12_570, rate=0.0),
            TaxBand(threshold=15_397, rate=0.19),
            TaxBand(threshold=27_491, rate=0.20),
            TaxBand(threshold=43_662, rate=0.21),
            TaxBand(threshold=75_000, rate=0.42),
            TaxBand(threshold=125_140, rate=0.45),
            TaxBand(threshold=float("inf"), rate=0.48),
        ]
    else:
        # Rest of UK bands for 2025/26
        bands = [
            TaxBand(threshold=12_570, rate=0.0),
            TaxBand(threshold=50_270, rate=0.20),
            TaxBand(threshold=125_140, rate=0.40),
            TaxBand(threshold=float("inf"), rate=0.45),
        ]
    return bands, personal_allowance


def calculate_income_tax(income: float, scotland: bool) -> float:
    """Compute income tax payable on taxable income.

    Parameters
    ----------
    income : float
        Taxable income (after personal allowance and before relief adjustments).
    scotland : bool
        Use Scottish tax bands if True.

    Returns
    -------
    float
        Tax payable in pounds.
    """
    bands, personal_allowance = get_tax_bands(scotland)
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

    # If income exceeds the last threshold, apply the last rate
    if taxable > 0:
        tax_due += taxable * bands[-1].rate

    return tax_due
