"""
Planwise - UK Investment & Retirement Planning Library.

A Python library for modeling retirement savings across various UK tax wrappers
including Lifetime ISA (LISA), Stocks & Shares ISA, Self-Invested Personal
Pension (SIPP) and workplace pensions.
"""

import os

from .core import LIMITS_DB, project_investment, project_retirement
from .ni import NICBand, calculate_ni
from .profile import delete_profile, list_profiles, load_profile, save_profile
from .tax import TAX_BANDS_DB, TaxBand, calculate_income_tax, get_tax_bands

try:
    from .plotting import RetirementPlotter, make_contribution_plot, make_growth_plot

    _PLOTTING_AVAILABLE = True
except Exception:
    _PLOTTING_AVAILABLE = False

PLANWISE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(PLANWISE_DIR)

__version__ = "0.2.0"
__author__ = "Planwise Team"
__all__ = [
    "project_retirement",
    "calculate_income_tax",
    "get_tax_bands",
    "TaxBand",
    "RetirementPlotter",
    "make_contribution_plot",
    "make_growth_plot",
    "make_income_breakdown_pie",
    "plotting",
]
