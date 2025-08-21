import pytest

from planwise.ni import _get_ni_bands, calculate_ni


class DummyBand:
    def __init__(self, threshold, rate):
        self.threshold = threshold
        self.rate = rate


import planwise.ni

planwise.ni.NI_BANDS_DB = {
    2025: {
        "category_a": [
            DummyBand(threshold=12000, rate=0.0),
            DummyBand(threshold=50000, rate=0.12),
            DummyBand(threshold=float("inf"), rate=0.02),
        ],
        "category_b": [
            DummyBand(threshold=10000, rate=0.0),
            DummyBand(threshold=40000, rate=0.10),
            DummyBand(threshold=float("inf"), rate=0.01),
        ],
    }
}


def test_get_ni_bands_valid():
    bands = _get_ni_bands(2025, "category_a")
    assert isinstance(bands, list)
    assert bands[0].threshold == 12000


def test_get_ni_bands_invalid_year():
    with pytest.raises(ValueError):
        _get_ni_bands(2024, "category_a")


def test_get_ni_bands_invalid_category():
    with pytest.raises(ValueError):
        _get_ni_bands(2025, "category_z")


def test_calculate_ni_zero_income():
    assert calculate_ni(0) == 0.0


def test_calculate_ni_negative_income():
    assert calculate_ni(-1000) == 0.0


def test_calculate_ni_within_first_band():
    assert calculate_ni(10000) == 0.0


def test_calculate_ni_within_second_band():
    # (12000 threshold, 0.0 rate), (50000 threshold, 0.12 rate)
    # income = 20000: (20000-12000)*0.12 = 960.0
    assert calculate_ni(20000) == pytest.approx(960.0)


def test_calculate_ni_across_bands():
    # income = 60000
    # (12000-0)*0.0 = 0
    # (50000-12000)*0.12 = 4560
    # (60000-50000)*0.02 = 200
    # total = 4760
    assert calculate_ni(60000) == pytest.approx(4760.0)


def test_calculate_ni_different_category():
    # category_b: (10000-0)*0.0 = 0
    # (40000-10000)*0.10 = 3000
    # (50000-40000)*0.01 = 100
    # total for income=50000: 3100
    assert calculate_ni(50000, category="category_b") == pytest.approx(3100.0)
