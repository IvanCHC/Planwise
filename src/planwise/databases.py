import json
import os
from dataclasses import dataclass
from typing import Any

PLANWISE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_json_db(database_name: str) -> Any:
    json_path = os.path.join(PLANWISE_DIR, "data", f"{database_name}.json")
    with open(json_path, "r") as f:
        return json.load(f)


@dataclass
class NIBand:
    """
    Represents a single National Insurance band.
    Attributes:
        threshold (float): Lower threshold of the band.
        rate (float): NI rate as a decimal.
    """

    threshold: float
    rate: float


@dataclass
class TaxBand:
    """
    Represents a single tax band.
    Attributes:
        threshold (float): Lower threshold of the band.
        rate (float): Marginal tax rate in decimal.
    """

    threshold: float
    rate: float


def load_ni_bands_db() -> dict:
    """
    Load NI band data from a JSON file and construct a nested dictionary of NI bands by year and category.
    Returns:
        dict: NI bands by year and category.
    """
    raw_db = _load_json_db("ni_bands")
    db: dict = {}
    for year, categories in raw_db.items():
        db[int(year)] = {}
        for category, data in categories.items():
            bands = []
            for band in data["bands"]:
                threshold = band["threshold"]
                if isinstance(threshold, str) and threshold == "inf":
                    threshold = float("inf")
                bands.append(NIBand(threshold=threshold, rate=band["rate"]))
            db[int(year)][category] = bands
    return db


def load_tax_bands_db() -> dict:
    """
    Load tax band data from a JSON file and construct a nested dictionary of tax bands by year and region.
    Returns:
        dict: Tax band information by year and region.
    """
    raw_db = _load_json_db("tax_bands")
    db: dict = {}
    for year, regions in raw_db.items():
        db[int(year)] = {}
        for region, data in regions.items():
            bands = []
            for band in data["bands"]:
                threshold = band["threshold"]
                if isinstance(threshold, str) and threshold == "inf":
                    threshold = float("inf")
                bands.append(TaxBand(threshold=threshold, rate=band["rate"]))
            db[int(year)][region] = {
                "personal_allowance": data["personal_allowance"],
                "bands": bands,
            }
    return db


STATE_PENSION_DB = _load_json_db("state_pension")
LIMITS_DB = _load_json_db("limits")
TAX_BANDS_DB = load_tax_bands_db()
NI_BANDS_DB = load_ni_bands_db()
