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


def test_compare_endpoint_exists():
    """Compare endpoint returns structured response."""
    response = client.get("/v1/compare/event-a/event-b")
    assert response.status_code == 200
    data = response.json()
    assert "event_a" in data
    assert "event_b" in data
