import pytest

from planwise import tax


class DummyBand:
    def __init__(self, threshold, rate):
        self.threshold = threshold
        self.rate = rate


@pytest.fixture(autouse=True)
def patch_tax_bands_db(monkeypatch):
    dummy_db = {
        2025: {
            "rest_of_uk": {
                "bands": [
                    DummyBand(12570, 0.0),
                    DummyBand(50270, 0.2),
                    DummyBand(150000, 0.4),
                ],
                "personal_allowance": 12570,
            },
            "scotland": {
                "bands": [
                    DummyBand(12570, 0.0),
                    DummyBand(25000, 0.19),
                    DummyBand(43462, 0.20),
                ],
                "personal_allowance": 12570,
            },
        }
    }
    monkeypatch.setattr(tax, "TAX_BANDS_DB", dummy_db)


def test_get_tax_bands_rest_of_uk():
    bands, pa = tax._get_tax_bands(False, 2025)
    assert isinstance(bands, list)
    assert pa == 12570
    assert bands[1].rate == 0.2


def test_get_tax_bands_scotland():
    bands, pa = tax._get_tax_bands(True, 2025)
    assert isinstance(bands, list)
    assert pa == 12570
    assert bands[1].rate == 0.19


def test_get_tax_bands_invalid_year():
    with pytest.raises(ValueError):
        tax._get_tax_bands(False, 1900)


def test_calculate_income_tax_basic():
    # Income below personal allowance
    assert tax.calculate_income_tax(12000, False, 2025) == 0
    # Income just above personal allowance
    val = tax.calculate_income_tax(13000, False, 2025)
    assert val > 0
    # Income in higher band
    val2 = tax.calculate_income_tax(60000, False, 2025)
    assert val2 > 0


def test_calculate_income_tax_scotland():
    val = tax.calculate_income_tax(30000, True, 2025)
    assert val > 0


# Test calculate_gross_from_take_home


def test_calculate_gross_from_take_home_basic():
    gross = tax.calculate_gross_from_take_home(30000, False, 2025)
    assert isinstance(gross, float)
    assert gross > 30000


def test_calculate_gross_from_take_home_with_state_pension():
    gross = tax.calculate_gross_from_take_home(20000, False, 2025, state_pension=10000)
    assert isinstance(gross, float)
    assert gross > 20000
