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
from .profile import delete_profile, list_profiles, load_profile, save_profile
from .tax import calculate_income_tax, get_tax_bands

try:
    from .plotting import (
        plot_annual_contribution_chart,
        plot_balances_by_account_chart,
        plot_growth_projection_chart,
        plot_pie_chart_breakdown,
        plot_total_balance_chart,
        plot_total_withdrawals_chart,
        plot_withdrawals_by_account_chart,
    )

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
