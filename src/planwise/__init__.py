"""
Planwise - UK Investment & Retirement Planning Library.

A Python library for modeling retirement savings across various UK tax wrappers
including Lifetime ISA (LISA), Stocks & Shares ISA, Self-Invested Personal
Pension (SIPP) and workplace pensions.
"""

import os

from .core import project_investment, project_retirement
from .databases import LIMITS_DB, NI_BANDS_DB, STATE_PENSION_DB, TAX_BANDS_DB
from .ni import calculate_ni
from .tax import calculate_income_tax

try:
    from .plotting import *

    _PLOTTING_AVAILABLE = True
except Exception:
    _PLOTTING_AVAILABLE = False

PLANWISE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(PLANWISE_DIR)

__version__ = "0.2.0"
__author__ = "Planwise Team"
__all__ = [
    "project_investment",
    "project_retirement",
    "calculate_ni",
    "calculate_income_tax",
    "LIMITS_DB",
    "NI_BANDS_DB",
    "STATE_PENSION_DB",
    "TAX_BANDS_DB",
    "_PLOTTING_AVAILABLE",
]
