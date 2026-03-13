import httpx
import pytest

from groundtruth.ingestion.acled import ACLEDIngestor


@pytest.mark.asyncio
async def test_acled_missing_credentials_skips(tmp_path):
    ingestor = ACLEDIngestor(cache_dir=tmp_path, username=None, password=None)
    events = await ingestor.fetch_events(country="Ukraine")
    assert events == []


@pytest.mark.asyncio
async def test_acled_oauth_and_event_parse(tmp_path):
    token_payload = {
        "access_token": "abc",
        "refresh_token": "refresh1",
        "expires_in": 86400,
    }
    data_payload = {
        "data": [
            {
                "event_id_cnty": "123",
                "event_date": "2026-03-10",
                "event_type": "Battles",
                "country": "Ukraine",
                "latitude": "50.45",
                "longitude": "30.52",
                "notes": "Clashes near city",
                "assoc_actor_1": "Actor A",
                "assoc_actor_2": "Actor B",
            }
        ]
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth/token"):
            return httpx.Response(200, json=token_payload)
        return httpx.Response(200, json=data_payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ingestor = ACLEDIngestor(
        cache_dir=tmp_path,
        http_client=client,
        username="a@b.com",
        password="secret",
        request_interval_seconds=0,
    )

    events = await ingestor.fetch_events(country="Ukraine", limit=50, max_pages=1)
    assert len(events) == 1
    assert events[0]["country_code"] == "UA"
    assert events[0]["event_type"] == "Battles"


@pytest.mark.asyncio
async def test_acled_refresh_token_flow(tmp_path):
    refresh_payload = {
        "access_token": "refreshed",
        "refresh_token": "refresh2",
        "expires_in": 86400,
    }
    data_payload = {"data": []}

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth/token"):
            return httpx.Response(200, json=refresh_payload)
        return httpx.Response(200, json=data_payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ingestor = ACLEDIngestor(
        cache_dir=tmp_path,
        http_client=client,
        username="a@b.com",
        password="secret",
        request_interval_seconds=0,
    )
    ingestor._refresh_token = "r1"  # pylint: disable=protected-access
    ingestor._expires_at = None  # pylint: disable=protected-access

    token = await ingestor._get_access_token(force_refresh=True)  # pylint: disable=protected-access
    assert token == "refreshed"
