"""Weather endpoint tests — every provider HTTP call is mocked.

No real API key and no network access are required: ``urllib.request.urlopen``
is patched inside ``api.services.weather`` for all live-data scenarios.
"""

import io
import json
import os
import ssl
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
from api.services import weather as weather_service  # noqa: E402

# Placeholder key used only inside mocked tests — never a real credential.
TEST_KEY = "unit-test-key-not-a-secret"

PROVIDER_URL = "https://api.openweathermap.org/data/2.5/weather"

SUCCESS_BODY = {
    "coord": {"lon": 78.4744, "lat": 17.3753},
    "weather": [
        {"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02d"}
    ],
    "main": {"temp": 32.54, "feels_like": 31.86, "humidity": 33},
    "wind": {"speed": 5.28, "deg": 47},
    "rain": {"1h": 0.4},
    "dt": 1791803381,
    "sys": {"country": "IN"},
    "name": "Hyderabad",
    "cod": 200,
}

UNAVAILABLE_EN = "Weather service is currently unavailable. Please try again later."


class _FakeResponse:
    """Minimal context-manager stand-in for urllib's HTTPResponse."""

    def __init__(self, payload: dict, status: int = 200):
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
        PROVIDER_URL,
        code,
        "error",
        {},
        io.BytesIO(json.dumps(body).encode("utf-8")),
    )


def _get_weather(location: str = "Hyderabad"):
    return TestClient(app).get("/api/weather", params={"location": location})


def test_weather_success_returns_live_data():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            return_value=_FakeResponse(SUCCESS_BODY),
        ):
            r = _get_weather()
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["found"] is True
    assert body["location"] == "Hyderabad, IN"
    assert body["temperature"] == 32.54
    assert body["humidity"] == 33
    assert body["condition"] == "Clouds"
    assert body["description"] == "few clouds"
    assert body["precipitation_mm"] == 0.4
    assert body["wind_speed"] == 5.28
    assert body["observed_at"] == 1791803381
    assert body["source"] == "openweathermap"
    assert isinstance(body["suggestions"], list) and body["suggestions"]
    for suggestion in body["suggestions"]:
        assert "en" in suggestion and "te" in suggestion


def test_provider_request_url_params_timeout_and_tls_context():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            return_value=_FakeResponse(SUCCESS_BODY),
        ) as fake_urlopen:
            weather_service.OpenWeatherMapProvider().fetch("Hyderabad")

    assert fake_urlopen.call_count == 1
    args, kwargs = fake_urlopen.call_args
    parsed = urllib.parse.urlparse(args[0].full_url)
    query = urllib.parse.parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "api.openweathermap.org"
    assert parsed.path == "/data/2.5/weather"
    assert query["q"] == ["Hyderabad"]
    assert query["units"] == ["metric"]
    assert query["appid"] == [TEST_KEY]
    assert kwargs["timeout"] == 10
    assert isinstance(kwargs["context"], ssl.SSLContext)


def test_weather_invalid_key_returns_clear_message():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            side_effect=_http_error(401, {"cod": 401, "message": "Invalid API key"}),
        ):
            r = _get_weather()
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["found"] is False
    assert "invalid" in body["message"]["en"].lower()
    assert "WEATHER_API_KEY" in body["message"]["en"]
    assert body["message"]["te"]


def test_weather_rate_limited_returns_clear_message():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            side_effect=_http_error(
                429, {"cod": "429", "message": "rate limit exceeded"}
            ),
        ):
            r = _get_weather()
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["found"] is False
    assert "rate limit" in body["message"]["en"].lower()
    assert body["message"]["te"]


def test_weather_location_not_found():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            side_effect=_http_error(404, {"cod": "404", "message": "city not found"}),
        ):
            r = _get_weather(location="Nowhereville")
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["found"] is False
    assert body["location"] == "Nowhereville"
    assert "was not found" in body["message"]["en"]
    assert body["message"]["te"]


def test_weather_network_error_returns_graceful_message():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            r = _get_weather()
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["found"] is False
    assert body["message"]["en"] == UNAVAILABLE_EN
    assert body["message"]["te"]


def test_weather_timeout_returns_graceful_message():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            side_effect=TimeoutError("timed out"),
        ):
            r = _get_weather()
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["found"] is False
    assert body["message"]["en"] == UNAVAILABLE_EN


def test_weather_unconfigured_without_key():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": ""}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen"
        ) as fake_urlopen:
            r = _get_weather()
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is False
    assert "not configured" in body["message"]["en"]
    fake_urlopen.assert_not_called()  # no HTTP call without a key



def test_weather_invalid_location_rejected():
    r = _get_weather(location="a!@#$")
    assert r.status_code == 422


GEO_BODY = [
    {"name": "Maredpalle", "state": "Telangana", "country": "IN", "lat": 17.385, "lon": 78.4867}
]


def _get_weather_qs(params: dict):
    return TestClient(app).get("/api/weather", params=params)


def test_weather_by_coordinates_returns_live_data_with_area_name():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            side_effect=[_FakeResponse(SUCCESS_BODY), _FakeResponse(GEO_BODY)],
        ) as fake_urlopen:
            r = _get_weather_qs({"lat": 17.385, "lon": 78.4867})
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is True
    assert body["found"] is True
    # Reverse geocoding enriches the display name (village, state, country)
    assert body["location"] == "Maredpalle, Telangana, IN"
    assert body["temperature"] == 32.54
    assert body["source"] == "openweathermap"
    assert isinstance(body["suggestions"], list) and body["suggestions"]

    # First call = weather by coordinates; second = reverse geocoding.
    assert fake_urlopen.call_count == 2
    weather_url = fake_urlopen.call_args_list[0][0][0].full_url
    parsed = urllib.parse.urlparse(weather_url)
    query = urllib.parse.parse_qs(parsed.query)
    assert parsed.netloc == "api.openweathermap.org"
    assert parsed.path == "/data/2.5/weather"
    assert query["lat"] == ["17.3850"]
    assert query["lon"] == ["78.4867"]
    assert "q" not in query
    assert query["units"] == ["metric"]
    assert query["appid"] == [TEST_KEY]
    assert fake_urlopen.call_args_list[0][1]["timeout"] == 10
    assert isinstance(fake_urlopen.call_args_list[0][1]["context"], ssl.SSLContext)

    geo_url = fake_urlopen.call_args_list[1][0][0].full_url
    assert "/geo/1.0/reverse" in geo_url
    geo_query = urllib.parse.parse_qs(urllib.parse.urlparse(geo_url).query)
    assert geo_query["lat"] == ["17.3850"]
    assert geo_query["lon"] == ["78.4867"]
    assert geo_query["limit"] == ["1"]
    assert geo_query["appid"] == [TEST_KEY]


def test_weather_by_coordinates_geocode_failure_falls_back_to_provider_name():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            side_effect=[_FakeResponse(SUCCESS_BODY), urllib.error.URLError("down")],
        ):
            r = _get_weather_qs({"lat": 17.385, "lon": 78.4867})
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is True
    # Falls back to the weather API's own place name — never an invented one.
    assert body["location"] == "Hyderabad, IN"


def test_weather_by_coordinates_empty_geocode_result_falls_back():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": TEST_KEY}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen",
            side_effect=[_FakeResponse(SUCCESS_BODY), _FakeResponse([])],
        ):
            r = _get_weather_qs({"lat": 17.385, "lon": 78.4867})
    assert r.status_code == 200
    assert r.json()["location"] == "Hyderabad, IN"


def test_weather_coordinates_unconfigured_without_key():
    with mock.patch.dict(os.environ, {"WEATHER_API_KEY": ""}):
        with mock.patch(
            "api.services.weather.urllib.request.urlopen"
        ) as fake_urlopen:
            r = _get_weather_qs({"lat": 17.385, "lon": 78.4867})
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is False
    assert "17.3850" in body["location"]  # honest coordinate label, no fake name
    fake_urlopen.assert_not_called()


def test_weather_rejects_name_and_coordinates_together():
    with mock.patch(
        "api.services.weather.urllib.request.urlopen"
    ) as fake_urlopen:
        r = _get_weather_qs({"location": "Hyderabad", "lat": 17.385, "lon": 78.4867})
    assert r.status_code == 422
    fake_urlopen.assert_not_called()


def test_weather_rejects_partial_coordinates():
    with mock.patch(
        "api.services.weather.urllib.request.urlopen"
    ) as fake_urlopen:
        assert _get_weather_qs({"lat": 17.385}).status_code == 422
        assert _get_weather_qs({"lon": 78.4867}).status_code == 422
    fake_urlopen.assert_not_called()


def test_weather_rejects_missing_input():
    r = TestClient(app).get("/api/weather")
    assert r.status_code == 422


def test_weather_rejects_invalid_coordinates():
    with mock.patch(
        "api.services.weather.urllib.request.urlopen"
    ) as fake_urlopen:
        assert _get_weather_qs({"lat": 95, "lon": 0}).status_code == 422
        assert _get_weather_qs({"lat": 0, "lon": -181}).status_code == 422
        assert _get_weather_qs({"lat": "abc", "lon": 0}).status_code == 422
        assert _get_weather_qs({"lat": "", "lon": 0}).status_code == 422
    fake_urlopen.assert_not_called()
