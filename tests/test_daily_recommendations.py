"""Tests for the daily crop suitability recommendations endpoint.

Every provider HTTP call is mocked — no real API key or network access required.
Follows the same pattern as tests/test_weather.py.
"""

import io
import json
import os
import sys
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_DB_PATH", os.path.join(ROOT, "data", "test_app.db"))

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

TEST_KEY = "unit-test-key-not-a-secret"

WEATHER_SUCCESS = {
    "coord": {"lon": 78.4744, "lat": 17.3753},
    "weather": [{"id": 801, "main": "Clear", "description": "clear sky", "icon": "01d"}],
    "main": {"temp": 32.54, "feels_like": 31.86, "humidity": 33},
    "wind": {"speed": 5.28, "deg": 47},
    "dt": 1791803381,
    "sys": {"country": "IN"},
    "name": "Hyderabad",
    "cod": 200,
}


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
        "https://api.openweathermap.org/data/2.5/weather",
        code,
        "error",
        {},
        io.BytesIO(json.dumps(body).encode("utf-8")),
    )


def _get(params=None):
    return TestClient(app).get("/api/daily-recommendations", params=params or {})


def test_daily_returns_rules_based_guidance():
    r = _get()
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["guidance_type"] == "rules_based_guidance"
    assert body["season"] in ("kharif", "rabi", "zaid", "kharif/zaid overlap")
    assert isinstance(body["month"], int) and 1 <= body["month"] <= 12
    assert body["date"]
    assert isinstance(body["recommendations"], list)
    assert body["returned"] == len(body["recommendations"])
    assert body["total"] == 62
    for rec in body["recommendations"]:
        assert rec["guidance_type"] == "rules_based_guidance"
        assert "id" in rec and "name_en" in rec and "category" in rec
        assert "suitability_score" in rec
        assert isinstance(rec["season_match"], bool)
    assert "disclaimer" in body
    assert "not verified" in body["disclaimer"].lower()
    assert "ICAR" in body["disclaimer"]


def test_daily_uses_live_weather_when_available():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            return_value=_FakeResponse(WEATHER_SUCCESS),
        ):
            r = _get({"location": "Hyderabad"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["weather_used"] is True
    assert body["weather"] is not None
    assert body["weather"]["found"] is True
    assert body["weather"]["temperature"] == 32.54
    assert body["weather"]["condition"] == "Clear"
    assert body["recommendations"][0]["suitability_score"] > 0


def test_daily_weather_not_configured_without_key():
    saved = os.environ.pop("WEATHER_API_KEY", None)
    try:
        r = _get({"location": "Hyderabad"})
    finally:
        if saved is not None:
            os.environ["WEATHER_API_KEY"] = saved
    body = r.json()
    assert body["weather_used"] is False
    assert body["weather_error"] == "not_configured"
    assert len(body["recommendations"]) > 0


def test_daily_soil_and_water_parameters():
    r = _get({"soil": "loamy", "water": "medium", "limit": 5})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["soil_provided"] is True
    assert body["water_provided"] is True
    assert body["returned"] == 5


def test_daily_category_filter():
    r = _get({"category": "vegetables", "limit": 20})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["category_filter"] == "vegetables"
    assert all(rec["category"] == "vegetables" for rec in body["recommendations"])


def test_daily_invalid_category_returns_422():
    r = _get({"category": "not_a_category"})
    assert r.status_code == 422, r.text


def test_daily_month_override():
    r = _get({"month": 7, "limit": 5})  # July = kharif only
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["month"] == 7
    assert body["season"] == "kharif"


def test_daily_forecast():
    r = _get({"forecast": True, "limit": 6})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["forecast"] is not None
    assert len(body["forecast"]) == 3
    for month_entry in body["forecast"]:
        assert "month" in month_entry
        assert "season" in month_entry
        assert "top_crops" in month_entry


def test_daily_detail_endpoint():
    r = TestClient(app).get("/api/daily-recommendations/rice")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["guidance_type"] == "rules_based_guidance"
    assert body["id"] == "rice"
    assert body["name_en"] == "Rice"
    assert body["category"] == "cereals_millets"
    assert "planting_months" in body
    assert "risks" in body
    assert "precautions" in body


def test_daily_detail_404():
    r = TestClient(app).get("/api/daily-recommendations/no-such-crop")
    assert r.status_code == 404, r.text


def test_daily_no_fabricated_data():
    r = _get({"location": "Hyderabad"})
    body = r.json()
    for rec in body["recommendations"]:
        assert "citation" not in rec
        assert "source_url" not in rec
        assert rec["last_updated"] is None or isinstance(rec["last_updated"], str)
        if rec["temp_range_c"] is not None:
            lo, hi = rec["temp_range_c"]
            assert lo is None or isinstance(lo, (int, float))
            assert hi is None or isinstance(hi, (int, float))