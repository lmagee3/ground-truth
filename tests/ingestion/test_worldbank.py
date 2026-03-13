import httpx
import pytest

from groundtruth.ingestion.worldbank import WorldBankIngestor


@pytest.mark.asyncio
async def test_fetch_gdp_known_country(tmp_path):
    payload = [
        {"page": 1},
        [
            {
                "country": {"value": "United States"},
                "countryiso3code": "USA",
                "indicator": {"value": "GDP (current US$)"},
                "date": "2024",
                "value": 27360900000000,
            }
        ],
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ingestor = WorldBankIngestor(cache_dir=tmp_path, http_client=client)

    result = await ingestor.fetch_indicator("US", "NY.GDP.MKTP.CD", 2020, 2024)
    assert result
    assert result[0].country_name == "United States"


@pytest.mark.asyncio
async def test_date_range_and_cache(tmp_path):
    payload = [
        {"page": 1},
        [
            {
                "country": {"value": "China"},
                "countryiso3code": "CHN",
                "indicator": {"value": "GDP"},
                "date": "2024",
                "value": 1.0,
            },
            {
                "country": {"value": "China"},
                "countryiso3code": "CHN",
                "indicator": {"value": "GDP"},
                "date": "2023",
                "value": 2.0,
            },
        ],
    ]
    calls = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ingestor = WorldBankIngestor(cache_dir=tmp_path, http_client=client)

    first = await ingestor.fetch_indicator("CN", "NY.GDP.MKTP.CD", 2023, 2024)
    second = await ingestor.fetch_indicator("CN", "NY.GDP.MKTP.CD", 2023, 2024)

    assert [p.year for p in first] == [2023, 2024]
    assert [p.year for p in second] == [2023, 2024]
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_invalid_country_code(tmp_path):
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ingestor = WorldBankIngestor(cache_dir=tmp_path, http_client=client)

    with pytest.raises(ValueError):
        await ingestor.fetch_indicator("ZZ", "NY.GDP.MKTP.CD", 2020, 2024)
