import builtins
import json
import os
from io import StringIO

from planwise import databases


class MockOpen:
    def __init__(self, data):
        self.data = data

    def __call__(self, file, mode):
        return StringIO(json.dumps(self.data))


def test_load_json_db(monkeypatch):
    sample_data = {"key": "value"}
    monkeypatch.setattr(builtins, "open", MockOpen(sample_data))
    json_path = os.path.join("tests", "sample_data.json")
    with open(json_path, "r") as f:
        data = json.load(f)
    assert data == sample_data


def test_load_ni_bands_db(monkeypatch):
    raw_db = {
        "2023": {
            "A": {
                "bands": [
                    {"threshold": 0, "rate": 0.12},
                    {"threshold": "inf", "rate": 0.02},
                ]
            }
        }
    }
    monkeypatch.setattr(databases, "_load_json_db", lambda name: raw_db)
    db = databases.load_ni_bands_db()
    assert 2023 in db
    assert "A" in db[2023]
    assert isinstance(db[2023]["A"][0], databases.NIBand)
    assert db[2023]["A"][1].threshold == float("inf")


def test_load_tax_bands_db(monkeypatch):
    raw_db = {
        "2023": {
            "England": {
                "personal_allowance": 12570,
                "bands": [
                    {"threshold": 0, "rate": 0.2},
                    {"threshold": "inf", "rate": 0.45},
                ],
            }
        }
    }
    monkeypatch.setattr(databases, "_load_json_db", lambda name: raw_db)
    db = databases.load_tax_bands_db()
    assert 2023 in db
    assert "England" in db[2023]
    assert db[2023]["England"]["personal_allowance"] == 12570
    assert isinstance(db[2023]["England"]["bands"][0], databases.TaxBand)
    assert db[2023]["England"]["bands"][1].threshold == float("inf")


def test_NIBand_dataclass():
    band = databases.NIBand(threshold=10000, rate=0.12)
    assert band.threshold == 10000
    assert band.rate == 0.12


def test_TaxBand_dataclass():
    band = databases.TaxBand(threshold=50000, rate=0.4)
    assert band.threshold == 50000
    assert band.rate == 0.4
