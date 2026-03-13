import json

from groundtruth.ingestion.fas import FASIngestor


def test_fas_load_and_query(tmp_path):
    data = {
        "US": {
            "total_warheads": 5044,
            "deployed": 1670,
            "source_url": "https://fas.org/issues/nuclear-weapons/status-world-nuclear-forces/",
        }
    }
    path = tmp_path / "fas_nuclear.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    ingestor = FASIngestor(data_path=path)
    loaded = ingestor.load_data()
    us = ingestor.get_country_data("US")

    assert loaded["US"]["total_warheads"] == 5044
    assert us["deployed"] == 1670


def test_fas_missing_file(tmp_path):
    ingestor = FASIngestor(data_path=tmp_path / "missing.json")
    assert ingestor.load_data() == {}
