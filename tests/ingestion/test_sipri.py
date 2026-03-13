from groundtruth.ingestion.sipri import SIPRIIngestor


def test_sipri_csv_parsing_and_filtering(tmp_path):
    data_dir = tmp_path / "sipri"
    data_dir.mkdir()
    (data_dir / "military_expenditure.csv").write_text(
        "country,year,military_expenditure_usd,military_expenditure_pct_gdp\n"
        "United States,2023,916000000000,3.4\n"
        "United States,2024,930000000000,3.5\n",
        encoding="utf-8",
    )
    (data_dir / "arms_transfers.csv").write_text(
        "country,year,exports_tiv,imports_tiv\n" "United States,2023,100,10\n",
        encoding="utf-8",
    )

    ingestor = SIPRIIngestor(data_dir=data_dir)
    result = ingestor.get_country_military_data("US", start_year=2024, end_year=2024)

    assert len(result["military_expenditure"]) == 1
    assert result["military_expenditure"][0]["year"] == 2024
    assert result["arms_transfers"] == []


def test_sipri_country_normalization(tmp_path):
    ingestor = SIPRIIngestor(data_dir=tmp_path)
    assert ingestor.country_to_iso("United States") == "US"
    assert ingestor.country_to_iso("Unknown") is None
