import httpx
import pytest

from groundtruth.ingestion.gdelt import GDELTIngestor


@pytest.mark.asyncio
async def test_gdelt_query_artlist_and_cache(tmp_path):
    payload = {
        "articles": [
            {
                "url": "https://example.com/a",
                "title": "Ukraine update",
                "seendate": "20260313T010101Z",
                "sourcecountry": "UA",
                "domain": "news",
            }
        ]
    }
    calls = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        assert request.url.params.get("mode") == "artlist"
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ingestor = GDELTIngestor(cache_dir=tmp_path, http_client=client, request_interval_seconds=0)

    first = await ingestor.query("ukraine", mode="artlist", maxrecords=10)
    second = await ingestor.query("ukraine", mode="artlist", maxrecords=10)

    assert first["articles"][0]["title"] == "Ukraine update"
    assert second["articles"][0]["title"] == "Ukraine update"
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_gdelt_parse_modes_and_geo_filter(tmp_path):
    payload = {
        "articles": [
            {
                "url": "https://example.com/a",
                "title": "A",
                "seendate": "20260313T010101Z",
                "sourcecountry": "UA",
            },
            {
                "url": "https://example.com/b",
                "title": "B",
                "seendate": "20260313T010101Z",
                "sourcecountry": "RU",
            },
        ],
        "timeline": [{"date": "20260313", "value": 10}],
    }

    ingestor = GDELTIngestor(cache_dir=tmp_path, request_interval_seconds=0)
    events = ingestor.parse_artlist(payload, country_code="UA")
    timeline = ingestor.parse_timeline(payload)
    tone = ingestor.parse_tonechart(payload)

    assert len(events) == 1
    assert events[0].country_code == "UA"
    assert timeline[0]["value"] == 10
    assert tone[0]["value"] == 10


@pytest.mark.asyncio
async def test_gdelt_fetch_events(tmp_path):
    payload = {
        "articles": [
            {
                "url": "https://example.com/c",
                "title": "South China Sea",
                "seendate": "20260313T010101Z",
                "sourcecountry": "CN",
            }
        ]
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ingestor = GDELTIngestor(cache_dir=tmp_path, http_client=client, request_interval_seconds=0)

    events = await ingestor.fetch_events("south china sea", country_code="CN")
    assert events
    assert events[0]["source"] == "gdelt"
