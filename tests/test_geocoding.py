"""Global location-search tests — every provider HTTP call is mocked.

Covers worldwide place queries, duplicate place names, empty results,
provider errors, rate limiting, caching, and key non-exposure. No real API
key or network access is required.
"""

import io
import json
import os
import sys
import urllib.error
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_DB_PATH", os.path.join(ROOT, "data", "test_app.db"))

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402
from api.services import geocoding  # noqa: E402

TEST_KEY = "unit-test-key-not-a-secret"

GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"

TOKYO = {"name": "Tokyo", "state": "Tokyo", "country": "JP", "lat": 35.6895, "lon": 139.6917}
LONDON = {"name": "London", "state": "England", "country": "GB", "lat": 51.5085, "lon": -0.1257}
NEW_YORK = {"name": "New York", "state": "New York", "country": "US", "lat": 40.7143, "lon": -74.006}
SYDNEY = {"name": "Sydney", "state": "New South Wales", "country": "AU", "lat": -33.8679, "lon": 151.2073}
SAO_PAULO = {"name": "São Paulo", "state": "São Paulo", "country": "BR", "lat": -23.5475, "lon": -46.6361}
TORONTO = {"name": "Toronto", "state": "Ontario", "country": "CA", "lat": 43.7001, "lon": -79.4203}
NAIROBI = {"name": "Nairobi", "state": "Nairobi", "country": "KE", "lat": -1.2833, "lon": 36.8167}
PEDDAPARIMI = {"name": "Peddaparimi", "state": "Andhra Pradesh", "country": "IN", "lat": 16.5204, "lon": 80.7708}


class _FakeResponse:
    def __init__(self, payload, status: int = 200):
        self._data = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(code: int, body: dict) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        GEO_URL, code, "error", {}, io.BytesIO(json.dumps(body).encode("utf-8"))
    )


def _search(q: str, limit: int = 5):
    return TestClient(app).get("/api/locations/search", params={"q": q, "limit": limit})


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def clear_geocode_cache():
    geocoding._search_cache.clear()
    yield
    geocoding._search_cache.clear()


@pytest.mark.parametrize(
    "query,entry",
    [
        ("Peddaparimi", PEDDAPARIMI),  # Asia / India — village
        ("Hyderabad", TOKYO),          # any provider match is fine (mocked)
        ("Tokyo", TOKYO),              # Asia / Japan
        ("London", LONDON),            # Europe / United Kingdom
        ("New York", NEW_YORK),        # North America / United States
        ("Toronto", TORONTO),          # North America / Canada
        ("Sydney", SYDNEY),            # Australia
        ("Nairobi", NAIROBI),          # Africa / Kenya
        ("São Paulo", SAO_PAULO),      # South America / Brazil
    ],
)
def test_global_place_searches_return_structured_results(query, entry):
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.geocoding.urllib.request.urlopen",
            return_value=_FakeResponse([entry]),
        ) as fake:
            r = _search(query)
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["count"] == 1
    result = body["results"][0]
    assert result["name"] == entry["name"]
    assert result["state"] == entry.get("state", "")
    assert result["country"] == entry["country"]
    assert result["lat"] == entry["lat"]
    assert result["lon"] == entry["lon"]
    assert entry["name"] in result["label"]
    # Global: no country is pinned in the request.
    requested = urllib.parse.urlparse(fake.call_args[0][0].full_url)
    assert requested.netloc == "api.openweathermap.org"
    assert requested.path == "/geo/1.0/direct"
    q_param = urllib.parse.parse_qs(requested.query)["q"][0]
    assert q_param == query


def test_duplicate_place_names_return_all_matches_for_disambiguation():
    springfield_il = {"name": "Springfield", "state": "Illinois", "country": "US", "lat": 39.7817, "lon": -89.6501}
    springfield_mo = {"name": "Springfield", "state": "Missouri", "country": "US", "lat": 37.209, "lon": -93.2923}
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.geocoding.urllib.request.urlopen",
            return_value=_FakeResponse([springfield_il, springfield_mo]),
        ):
            r = _search("Springfield")
    body = r.json()
    assert body["count"] == 2
    labels = [item["label"] for item in body["results"]]
    assert labels[0] == "Springfield, Illinois, US"
    assert labels[1] == "Springfield, Missouri, US"
    assert labels[0] != labels[1]  # user can disambiguate explicitly


def test_empty_results_return_no_match_state():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.geocoding.urllib.request.urlopen",
            return_value=_FakeResponse([]),
        ):
            r = _search("Zzyzx Nowhere Land")
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["count"] == 0
    assert body["results"] == []
    assert "message" not in body  # distinct from provider failure


def test_provider_invalid_key_returns_clear_message():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.geocoding.urllib.request.urlopen",
            side_effect=_http_error(401, {"cod": 401, "message": "Invalid API key"}),
        ):
            r = _search("Tokyo")
    body = r.json()
    assert body["configured"] is True
    assert body["count"] == 0 and body["results"] == []
    assert "WEATHER_API_KEY" in body["message"]["en"]
    assert body["message"]["te"]


def test_provider_rate_limit_returns_clear_message():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.geocoding.urllib.request.urlopen",
            side_effect=_http_error(429, {"cod": "429", "message": "limit"}),
        ):
            r = _search("London")
    body = r.json()
    assert body["count"] == 0 and body["results"] == []
    assert "rate limit" in body["message"]["en"].lower()
    assert body["message"]["te"]


def test_provider_network_error_returns_graceful_message():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.geocoding.urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            r = _search("Sydney")
    body = r.json()
    assert body["count"] == 0 and body["results"] == []
    assert "unavailable" in body["message"]["en"].lower()


def test_provider_unexpected_payload_returns_graceful_message():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.geocoding.urllib.request.urlopen",
            return_value=_FakeResponse({"unexpected": "shape"}),
        ):
            r = _search("Toronto")
    body = r.json()
    assert body["count"] == 0 and body["results"] == []
    assert "unavailable" in body["message"]["en"].lower()


def test_unconfigured_without_key_makes_no_provider_call():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": ""}):
        with mock.patch(
            "api.services.geocoding.urllib.request.urlopen"
        ) as fake:
            r = _search("Nairobi")
    body = r.json()
    assert body["configured"] is False
    assert body["results"] == []
    assert body["message"]["te"]
    fake.assert_not_called()


def test_repeated_queries_are_cached_in_memory():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.geocoding.urllib.request.urlopen",
            return_value=_FakeResponse([TOKYO]),
        ) as fake:
            first = _search("Tokyo")
            second = _search("TOKYO")  # case-insensitive cache hit
    assert fake.call_count == 1  # short-lived cache avoids a second provider call
    assert first.json()["results"] == second.json()["results"]


def test_api_key_never_appears_in_response_or_results():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.geocoding.urllib.request.urlopen",
            return_value=_FakeResponse([LONDON]),
        ):
            r = _search("London")
    assert TEST_KEY not in r.text
    assert "appid" not in r.text


def test_search_validation_rejects_bad_input():
    assert _search("a").status_code == 422            # too short
    assert _search("x" * 101).status_code == 422      # too long
    assert TestClient(app).get("/api/locations/search").status_code == 422  # missing
    assert _search("Tokyo", limit=0).status_code == 422
    assert _search("Tokyo", limit=11).status_code == 422


def test_existing_weather_name_endpoint_still_backward_compatible():
    """Global search must not break the original city-name weather route."""
    from tests.test_weather import SUCCESS_BODY, _FakeResponse as WXResponse

    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            return_value=WXResponse(SUCCESS_BODY),
        ):
            r = TestClient(app).get("/api/weather", params={"location": "Hyderabad"})
    assert r.status_code == 200
    assert r.json()["found"] is True
