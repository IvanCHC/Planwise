"""
Planwise - UK Investment & Retirement Planning Library.

A Python library for modeling retirement savings across various UK tax wrappers
including Lifetime ISA (LISA), Stocks & Shares ISA, Self-Invested Personal
Pension (SIPP) and workplace pensions.
"""

from .core import project_retirement
from .plotting import make_contribution_plot, make_growth_plot
from .tax import TaxBand, calculate_income_tax, get_tax_bands

__version__ = "0.1.0"
__author__ = "Planwise Team"
__all__ = [
    "project_retirement",
    "calculate_income_tax",
    "get_tax_bands",
    "TaxBand",
    "make_contribution_plot",
    "make_growth_plot",
]
