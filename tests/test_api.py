"""Basic API tests for Ground Truth."""

from fastapi.testclient import TestClient

from groundtruth.api.main import app

client = TestClient(app)


def test_root():
    """Health check returns correct info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Ground Truth"
    assert data["status"] == "operational"


def test_context_endpoint_exists():
    """Context endpoint returns structured response."""
    response = client.get("/v1/context/test-query")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "sources" in data
    assert "report" in data
    assert "sources_available" in data


def test_timeline_endpoint_exists():
    """Timeline endpoint returns structured response."""
    response = client.get("/v1/timeline/middle-east")
    assert response.status_code == 200
    data = response.json()
    assert "region" in data
    assert "events" in data


def test_briefing_endpoint_exists():
    """Briefing endpoint returns structured response."""
    response = client.get("/v1/briefing/nato-expansion")
    assert response.status_code == 200
    data = response.json()
    assert "topic" in data
    assert "report" in data
    assert "sources_available" in data


def test_compare_endpoint_exists():
    """Compare endpoint returns structured response."""
    response = client.get("/v1/compare/event-a/event-b")
    assert response.status_code == 200
    data = response.json()
    assert "event_a" in data
    assert "event_b" in data
    assert "comparison" in data
    assert "sources_available" in data


def test_country_endpoint_has_sources_available():
    """F-001: /v1/country/{iso} must include sources_available field."""
    response = client.get("/v1/country/UA")
    assert response.status_code == 200
    data = response.json()
    assert "sources_available" in data, "F-001: sources_available missing from country response"
    sa = data["sources_available"]
    assert "cia_factbook" in sa
    assert "worldbank" in sa
    for source in sa.values():
        assert "status" in source
        assert "records" in source


def test_context_endpoint_has_verification_status():
    """Context endpoint must include verification_status from the verification pipeline."""
    response = client.get("/v1/context/test-query")
    assert response.status_code == 200
    data = response.json()
    assert "verification_status" in data, "verification_status missing from context response"
    vs = data["verification_status"]
    assert "overall_status" in vs
    assert vs["overall_status"] in ("pass", "warn", "fail")
    assert "source_validation" in vs
    assert "bias_analysis" in vs
    assert "fact_check" in vs
