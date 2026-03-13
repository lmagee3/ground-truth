import httpx
import pytest

from groundtruth.ingestion.cia_factbook import CIAFactbookIngestor


@pytest.mark.asyncio
async def test_parse_known_country_profile(tmp_path):
    payload = {
        "countries": [
            {
                "name": "China",
                "government": {
                    "government_type": "Communist state",
                    "international_organization_participation": "UN, WTO",
                },
                "military_and_security": {"military_branches": "PLA"},
                "geography": {"area": "9,596,960 sq km"},
                "economy": {"gdp": "$18T"},
                "people_and_society": {"population": "1.4B"},
                "transnational_issues": {"disputes": "South China Sea"},
            }
        ]
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ingestor = CIAFactbookIngestor(cache_path=tmp_path / "factbook.json", http_client=client)

    profile = await ingestor.get_country_profile(country_name="China")
    assert profile.iso_code == "CN"
    assert profile.military["military_branches"] == "PLA"


@pytest.mark.asyncio
async def test_military_fields_extracted(tmp_path):
    payload = {
        "countries": [{"name": "Iran", "military_and_security": {"military_branches": "Artesh"}}]
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ingestor = CIAFactbookIngestor(cache_path=tmp_path / "factbook.json", http_client=client)

    profile = await ingestor.get_country_profile(country_name="Iran")
    assert "military_branches" in profile.military


@pytest.mark.asyncio
async def test_country_cross_reference_to_iso(tmp_path):
    payload = {"countries": [{"name": "Ukraine", "military_and_security": {}}]}

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ingestor = CIAFactbookIngestor(cache_path=tmp_path / "factbook.json", http_client=client)

    profile = await ingestor.get_country_profile(country_name="Ukraine")
    assert profile.iso_code == "UA"
