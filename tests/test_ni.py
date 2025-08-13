"""
Tests for National Insurance (NI) calculations in Planwise.

These tests cover NI band retrieval, error handling, and NI calculation logic.
"""

import pytest

from planwise import ni


class DummyBand:
    def __init__(self, threshold, rate):
        self.threshold = threshold
        self.rate = rate


def test_get_ni_bands_valid(monkeypatch):
    """
    Test NI band retrieval for a valid year and category.
    """
    # Patch NI_BANDS_DB to a known value
    monkeypatch.setattr(
        ni,
        "NI_BANDS_DB",
        {
            2025: {
                "category_a": [
                    ni.NIBand(threshold=10000, rate=0.1),
                    ni.NIBand(threshold=float("inf"), rate=0.2),
                ]
            }
        },
    )
    bands = ni._get_ni_bands(2025, "category_a")
    assert isinstance(bands, list)
    assert bands[0].threshold == 10000
    assert bands[1].rate == 0.2


def test_get_ni_bands_invalid_year(monkeypatch):
    """
    Test ValueError is raised for an invalid year.
    """
    monkeypatch.setattr(ni, "NI_BANDS_DB", {2025: {}})
    with pytest.raises(ValueError):
        ni._get_ni_bands(2024, "category_a")


def test_get_ni_bands_invalid_category(monkeypatch):
    """
    Test ValueError is raised for an invalid category.
    """
    monkeypatch.setattr(ni, "NI_BANDS_DB", {2025: {"category_b": []}})
    with pytest.raises(ValueError):
        ni._get_ni_bands(2025, "category_a")


def test_calculate_ni_single_band(monkeypatch):
    """
    Test NI calculation for a single band and at threshold.
    """
    monkeypatch.setattr(
        ni,
        "get_ni_bands",
        lambda year, category: [DummyBand(10000, 0.1), DummyBand(float("inf"), 0.2)],
    )
    # Income below first threshold
    assert ni.calculate_ni(5000) == 5000 * 0.1
    # Income at first threshold
    assert ni.calculate_ni(10000) == 10000 * 0.1


def test_calculate_ni_multiple_bands(monkeypatch):
    """
    Test NI calculation for multiple bands and income in each band.
    """
    monkeypatch.setattr(
        ni,
        "get_ni_bands",
        lambda year, category: [
            DummyBand(10000, 0.1),
            DummyBand(20000, 0.2),
            DummyBand(float("inf"), 0.3),
        ],
    )
    # Income in second band
    assert ni.calculate_ni(15000) == (10000 * 0.1) + (5000 * 0.2)
    # Income in third band
    assert ni.calculate_ni(25000) == (10000 * 0.1) + (10000 * 0.2) + (5000 * 0.3)


def test_calculate_ni_zero_income(monkeypatch):
    """
    Test NI calculation returns 0 for zero income.
    """
    monkeypatch.setattr(
        ni,
        "get_ni_bands",
        lambda year, category: [DummyBand(10000, 0.1), DummyBand(float("inf"), 0.2)],
    )
    assert ni.calculate_ni(0) == 0.0


def test_calculate_ni_exact_band_thresholds(monkeypatch):
    """
    Test NI calculation at exact band thresholds.
    """
    monkeypatch.setattr(
        ni,
        "get_ni_bands",
        lambda year, category: [
            DummyBand(10000, 0.1),
            DummyBand(20000, 0.2),
            DummyBand(float("inf"), 0.3),
        ],
    )
    # Exactly at second threshold
    assert ni.calculate_ni(20000) == (10000 * 0.1) + (10000 * 0.2)


def test_calculate_ni_negative_income(monkeypatch):
    """
    Test NI calculation returns 0 for negative income.
    """
    monkeypatch.setattr(
        ni,
        "get_ni_bands",
        lambda year, category: [DummyBand(10000, 0.1), DummyBand(float("inf"), 0.2)],
    )
    assert ni.calculate_ni(-5000) == 0.0
