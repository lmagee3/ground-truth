from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from groundtruth.models import (
    ApprovedSource,
    Base,
    Country,
    Indicator,
    parse_approved_sources_markdown,
)


def test_model_creation_and_relationship():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        country = Country(
            iso_code="US", name="United States", region="North America", factbook_data={}
        )
        session.add(country)
        session.flush()

        indicator = Indicator(
            country_code="US",
            indicator_id="NY.GDP.MKTP.CD",
            indicator_name="GDP (current USD)",
            year=2024,
            value=27360900000000.0,
            source="worldbank",
            fetched_at=datetime.now(timezone.utc),
        )
        session.add(indicator)
        session.commit()

        refreshed = session.get(Country, "US")
        assert refreshed is not None
        assert len(refreshed.indicators) == 1


def test_approved_source_seeding_parses_markdown():
    approved_sources = Path(__file__).resolve().parents[1] / "docs" / "APPROVED_SOURCES.md"
    parsed = parse_approved_sources_markdown(approved_sources)
    assert parsed
    assert any(item["domain"] == "cia.gov" for item in parsed)


def test_approved_source_insert():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        source = ApprovedSource(
            domain="cia.gov",
            organization="CIA",
            source_type="us_gov",
            reliability_score=10,
            notes="World Factbook",
        )
        session.add(source)
        session.commit()

        result = session.get(ApprovedSource, "cia.gov")
        assert result is not None
