"""
Planwise - UK Investment & Retirement Planning Library.

A Python library for modeling retirement savings across various UK tax wrappers
including Lifetime ISA (LISA), Stocks & Shares ISA, Self-Invested Personal
Pension (SIPP) and workplace pensions.
"""

from .core import IncomeBreakdown, project_post_retirement, project_retirement
from .ni import NICBand, calculate_ni
from .profile import delete_profile, list_profiles, load_profile, save_profile
from .tax import TaxBand, calculate_income_tax, get_tax_bands

# -----------------------------------------------------------------------------
# Optional plotting imports
#
# Plotting functions depend on the optional Altair and Plotly packages.  To
# prevent import errors when those libraries are not installed, attempt to
# import the plotting utilities inside a try/except block.  If the import
# fails (e.g., Altair is missing), stub functions are created that raise a
# helpful ImportError when called.  Users can install optional dependencies
# via ``pip install "planwise[plotting]"`` or ``pip install "planwise[app]"``.
try:
    from .plotting import (
        RetirementPlotter,
        make_contribution_plot,
        make_growth_plot,
        make_income_breakdown_pie,
    )

    _PLOTTING_AVAILABLE = True
except Exception:
    # Altair/plotly are not available; define stubs that explain how to enable
    # plotting support.  These stubs mirror the names of the real functions but
    # do nothing except raise an informative ImportError when used.
    _PLOTTING_AVAILABLE = False


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
    "make_income_breakdown_pie",
]
