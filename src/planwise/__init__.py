"""
Planwise - UK Investment & Retirement Planning Library.

A Python library for modeling retirement savings across various UK tax wrappers
including Lifetime ISA (LISA), Stocks & Shares ISA, Self-Invested Personal
Pension (SIPP) and workplace pensions.
"""

from .core import IncomeBreakdown, project_post_retirement, project_retirement
from .ni import NICBand, calculate_ni
from .plotting import (
    RetirementPlotter,
    make_contribution_plot,
    make_growth_plot,
    make_income_breakdown_pie,
)
from .tax import TaxBand, calculate_income_tax, get_tax_bands

__version__ = "0.1.0"
__author__ = "Planwise Team"
__all__ = [
    "project_retirement",
    "calculate_income_tax",
    "get_tax_bands",
    "TaxBand",
    "RetirementPlotter",
    "make_contribution_plot",
    "make_growth_plot",
]
