"""
Tests for tax calculations.
"""

import pytest

from planwise.tax import TaxBand, calculate_income_tax, get_tax_bands, load_tax_bands_db


class TestTaxBand:
    """Test the TaxBand dataclass."""

    def test_tax_band_creation(self):
        """Test creating a TaxBand instance."""
        band = TaxBand(threshold=12570, rate=0.20)
        assert band.threshold == 12570
        assert band.rate == 0.20


class TestGetTaxBands:
    """Test tax band retrieval functions."""

    def test_get_uk_tax_bands(self):
        """Test getting rest-of-UK tax bands."""
        bands, personal_allowance = get_tax_bands(scotland=False, year=2025)

        assert personal_allowance == 12_570.0
        assert len(bands) == 4

        # Check band thresholds and rates
        assert bands[0].threshold == 12_570
        assert bands[0].rate == 0.0
        assert bands[1].threshold == 50_270
        assert bands[1].rate == 0.20
        assert bands[2].threshold == 125_140
        assert bands[2].rate == 0.40
        assert bands[3].threshold == float("inf")
        assert bands[3].rate == 0.45

    def test_get_scottish_tax_bands(self):
        """Test getting Scottish tax bands."""
        bands, personal_allowance = get_tax_bands(scotland=True, year=2025)

        assert personal_allowance == 12_570.0
        assert len(bands) == 7

        # Check first and last bands
        assert bands[0].threshold == 12_570
        assert bands[0].rate == 0
        assert bands[-1].threshold == float("inf")
        assert bands[-1].rate == 0.48

    def test_year_not_found(self):
        """Test ValueError is raised when year is not found."""
        import pytest

        with pytest.raises(ValueError, match="No tax band data for year 2024"):
            get_tax_bands(scotland=False, year=2024)


class TestCalculateIncomeTax:
    """Test income tax calculation functions."""

    def test_no_tax_below_personal_allowance(self):
        """Test no tax is payable below personal allowance."""
        tax = calculate_income_tax(10_000, scotland=False, year=2025)
        assert tax == 0.0

        tax = calculate_income_tax(12_570, scotland=False, year=2025)
        assert tax == 0.0

    def test_basic_rate_tax_uk(self):
        """Test basic rate tax calculation for UK."""
        # £20,000 income: (20,000 - 12,570) * 0.20 = £1,486
        tax = calculate_income_tax(20_000, scotland=False, year=2025)
        expected = (20_000 - 12_570) * 0.20
        assert tax == pytest.approx(expected, rel=0.01)

    def test_higher_rate_tax_uk(self):
        """Test higher rate tax calculation for UK."""
        # £60,000 income
        income = 60_000
        tax = calculate_income_tax(income, scotland=False, year=2025)

        # Basic rate on £12,570 to £50,270
        basic_rate_income = 50_270 - 12_570
        basic_rate_tax = basic_rate_income * 0.20

        # Higher rate on £50,270 to £60,000
        higher_rate_income = income - 50_270
        higher_rate_tax = higher_rate_income * 0.40

        expected = basic_rate_tax + higher_rate_tax
        assert tax == pytest.approx(expected, rel=0.01)

    def test_scottish_tax_calculation(self):
        """Test Scottish tax calculation."""
        # £30,000 income in Scotland
        income = 30_000
        tax = calculate_income_tax(income, scotland=True, year=2025)

        # Calculate expected tax manually
        # Starter rate: (15,397 - 12,570) * 0.19
        starter = (15_397 - 12_570) * 0.19
        # Basic rate: (27,491 - 15,397) * 0.20
        basic = (27_491 - 15_397) * 0.20
        # Intermediate rate: (30,000 - 27,491) * 0.21
        intermediate = (income - 27_491) * 0.21

        expected = starter + basic + intermediate
        assert abs(tax - expected) < 0.01

    def test_additional_rate_tax_uk(self):
        """Test additional rate tax for very high earners."""
        income = 150_000
        tax = calculate_income_tax(income, scotland=False, year=2025)

        # Should include all three rates
        basic_rate_tax = (50_270 - 12_570) * 0.20
        higher_rate_tax = (125_140 - 50_270) * 0.40
        additional_rate_tax = (income - 125_140) * 0.45

        expected = basic_rate_tax + higher_rate_tax + additional_rate_tax
        assert abs(tax - expected) < 0.01

    @pytest.mark.parametrize(
        "income,scotland",
        [
            (0, False),
            (0, True),
            (5000, False),
            (5000, True),
            (25000, False),
            (25000, True),
            (75000, False),
            (75000, True),
            (200000, False),
            (200000, True),
        ],
    )
    def test_tax_is_non_negative(self, income, scotland):
        """Test that tax calculations never return negative values."""
        tax = calculate_income_tax(income, scotland, year=2025)
        assert tax >= 0

    def test_tax_increases_with_income(self):
        """Test that tax generally increases with income."""
        incomes = [10_000, 20_000, 40_000, 60_000, 100_000, 150_000]

        for scotland in [False, True]:
            taxes = [
                calculate_income_tax(income, scotland, year=2025) for income in incomes
            ]

            # Tax should generally increase (allowing for minor calculation differences)
            for i in range(1, len(taxes)):
                assert taxes[i] >= taxes[i - 1] - 0.01


class TestLoadTaxBandsDB:
    """Test loading of tax bands database."""

    def test_load_tax_bands_db_structure(self):
        db = load_tax_bands_db()
        assert isinstance(db, dict)
        assert 2025 in db
        for year, regions in db.items():
            assert isinstance(regions, dict)
            for region, data in regions.items():
                assert "personal_allowance" in data
                assert "bands" in data
                assert isinstance(data["bands"], list)
                for band in data["bands"]:
                    # Each band should be a TaxBand instance
                    assert hasattr(band, "threshold")
                    assert hasattr(band, "rate")
