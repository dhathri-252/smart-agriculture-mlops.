"""Weather service with a provider abstraction and a clean fallback state.

- ``openweathermap``: uses OpenWeatherMap's current-weather API. The key is
  read server-side from WEATHER_API_KEY and is never exposed to the frontend.
- ``none``: returns a clear "not configured" state so the app keeps working
  without ever fabricating live weather data.

Farming suggestions are derived only from real provider data (when available)
and are phrased as general guidance, never as guarantees.
"""

import json
import logging
import ssl
import urllib.error
import urllib.parse
import urllib.request

from api.config import get_weather_api_key, get_weather_provider

logger = logging.getLogger("api.weather")


def _build_ssl_context() -> ssl.SSLContext:
    """TLS context for outbound provider calls.

    The python.org macOS build of Python ships without a configured CA bundle
    (``ssl.get_default_verify_paths()`` points at nothing), which makes plain
    ``urllib`` fail every HTTPS request with ``CERTIFICATE_VERIFY_FAILED``.
    Prefer certifi's maintained Mozilla bundle when available and fall back to
    the system default trust store otherwise. Credentials are never involved
    here and never logged.
    """
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception as exc:  # degrade gracefully; never block app startup
        logger.warning(
            "Could not load the certifi CA bundle (%s); falling back to the "
            "system trust store. HTTPS provider calls may fail if this Python "
            "has no CA bundle configured.",
            type(exc).__name__,
        )
        return ssl.create_default_context()


# Shared context passed to every provider request (no key material inside).
SSL_CONTEXT = _build_ssl_context()

NOT_CONFIGURED_MESSAGE = {
    "en": "Live weather is not configured. Set WEATHER_API_KEY on the server to enable it. "
          "Until then, no live weather data is shown.",
    "te": "ప్రస్తుతం వాతావరణ సేవ కాన్ఫిగర్ చేయబడలేదు. దీన్ని ప్రారంభించడానికి "
          "సర్వర్‌లో WEATHER_API_KEY సెట్ చేయండి. అప్పటి వరకు ఎటువంటి ప్రత్యక్ష "
          "వాతావరణ సమాచారం చూపబడదు.",
}


class UnconfiguredProvider:
    """Clean configuration/fallback state — never invents weather data."""

    name = "none"

    def fetch(self, location: str = None, lat: float = None, lon: float = None) -> dict:
        return {
            "configured": False,
            "location": location or _coords_label(lat, lon),
            "message": NOT_CONFIGURED_MESSAGE,
        }


def _coords_label(lat: float, lon: float) -> str:
    """Display fallback for coordinate lookups — the real coordinates, never an
    invented place name."""
    return f"{lat:.4f}, {lon:.4f}"


class OpenWeatherMapProvider:
    name = "openweathermap"

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    GEO_URL = "https://api.openweathermap.org/geo/1.0/reverse"

    def fetch(self, location: str = None, lat: float = None, lon: float = None) -> dict:
        api_key = get_weather_api_key()
        label = location if location is not None else _coords_label(lat, lon)
        if not api_key:
            return UnconfiguredProvider().fetch(label)
        if lat is not None:
            # Supported coordinate-based lookup on the same provider.
            params = {
                "lat": f"{lat:.4f}",
                "lon": f"{lon:.4f}",
                "appid": api_key,
                "units": "metric",
            }
        else:
            params = {"q": location, "appid": api_key, "units": "metric"}
        query = urllib.parse.urlencode(params)
        request = urllib.request.Request(f"{self.BASE_URL}?{query}")
        try:
            with urllib.request.urlopen(
                request, timeout=10, context=SSL_CONTEXT
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # Log only the status and the provider's credential-free body
            # snippet — never the request URL, which carries the API key.
            try:
                detail = exc.read().decode("utf-8", "replace")[:200]
            except Exception:
                detail = ""
            if exc.code in (404, 400):
                return {
                    "configured": True,
                    "found": False,
                    "location": label,
                    "message": {
                        "en": f"Location '{label}' was not found. Check the spelling "
                              "or try a nearby city name.",
                        "te": f"'{label}' ప్రదేశం కనబడలేదు. వర్తనాన్ని తనిఖీ చేయండి "
                              "లేదా సమీపంలోని నగరం పేరు ప్రయత్నించండి.",
                    },
                }
            if exc.code in (401, 403):
                logger.warning(
                    "Weather provider rejected the configured key (HTTP %s): %s",
                    exc.code,
                    detail or exc.reason,
                )
                return {
                    "configured": True,
                    "found": False,
                    "location": label,
                    "message": {
                        "en": "The configured weather API key is invalid or not "
                              "yet active. Update WEATHER_API_KEY on the server "
                              "to restore live weather.",
                        "te": "కాన్ఫిగర్ చేసిన వాతావరణ API కీ చెల్లదు లేదా ఇంకా "
                              "క్రియాశీలంగా లేదు. ప్రత్యక్ష వాతావరణ సమాచారం తిరిగి "
                              "పొందడానికి సర్వర్‌లో WEATHER_API_KEY మార్చండి.",
                    },
                }
            if exc.code == 429:
                logger.warning(
                    "Weather provider rate limit exceeded (HTTP 429): %s",
                    detail or exc.reason,
                )
                return {
                    "configured": True,
                    "found": False,
                    "location": label,
                    "message": {
                        "en": "Weather service rate limit exceeded. Please try "
                              "again after a few minutes.",
                        "te": "వాతావరణ సేవ రేటు పరిమితి దాటింది. కొన్ని నిమిషాల "
                              "తర్వాత మళ్లీ ప్రయత్నించండి.",
                    },
                }
            logger.warning(
                "Weather provider HTTP error %s: %s", exc.code, detail or exc
            )
            return _provider_error(label)
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            ValueError,
            KeyError,
        ) as exc:
            logger.warning(
                "Weather provider request failed (%s): %s",
                type(exc).__name__,
                exc,
            )
            return _provider_error(label)

        data = _map_openweathermap(body, label)
        if lat is not None:
            # Best-effort enrichment only — never blocks or fabricates a name.
            area = self._reverse_geocode_area(lat, lon)
            if area:
                data["location"] = area
        return data

    def _reverse_geocode_area(self, lat: float, lon: float):
        """Best-effort nearest place name for coordinate lookups.

        Uses OpenWeather's supported reverse-geocoding endpoint with the same
        server-side key. Returns None on any failure so callers fall back to
        the weather API's own place name. Coordinates are never logged.
        """
        api_key = get_weather_api_key()
        if not api_key:
            return None
        query = urllib.parse.urlencode(
            {
                "lat": f"{lat:.4f}",
                "lon": f"{lon:.4f}",
                "limit": 1,
                "appid": api_key,
            }
        )
        request = urllib.request.Request(f"{self.GEO_URL}?{query}")
        try:
            with urllib.request.urlopen(
                request, timeout=5, context=SSL_CONTEXT
            ) as response:
                entries = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # best-effort: any failure is non-fatal
            logger.info(
                "Reverse geocoding unavailable (%s); using provider place name",
                type(exc).__name__,
            )
            return None
        if not isinstance(entries, list) or not entries:
            return None
        entry = entries[0] or {}
        parts = [entry.get("name"), entry.get("state"), entry.get("country")]
        parts = [p for p in parts if p]
        return ", ".join(parts) or None


def _provider_error(location: str) -> dict:
    return {
        "configured": True,
        "found": False,
        "location": location,
        "message": {
            "en": "Weather service is currently unavailable. Please try again later.",
            "te": "వాతావరణ సేవ ప్రస్తుతం అందుబాటులో లేదు. కొద్దిసేపటి తర్వాత "
                  "మళ్లీ ప్రయత్నించండి.",
        },
    }


def _map_openweathermap(body: dict, location: str) -> dict:
    weather = (body.get("weather") or [{}])[0]
    main = body.get("main") or {}
    wind = body.get("wind") or {}
    rain = body.get("rain") or {}
    snow = body.get("snow") or {}
    precipitation_mm = None
    if "1h" in rain:
        precipitation_mm = rain["1h"]
    elif "1h" in snow:
        precipitation_mm = snow["1h"]
    resolved_name = body.get("name") or location
    country = (body.get("sys") or {}).get("country") or ""
    return {
        "configured": True,
        "found": True,
        "location": f"{resolved_name}{', ' + country if country else ''}",
        "temperature": main.get("temp"),
        "humidity": main.get("humidity"),
        "condition": weather.get("main"),
        "description": weather.get("description"),
        "precipitation_mm": precipitation_mm,
        "wind_speed": wind.get("speed"),
        "observed_at": body.get("dt"),
        "source": "openweathermap",
    }


def get_weather_provider_instance():
    if get_weather_provider() == "openweathermap" and get_weather_api_key():
        return OpenWeatherMapProvider()
    return UnconfiguredProvider()


def weather_farming_suggestions(weather: dict) -> list:
    """General, hedged farming suggestions derived from real weather data."""
    suggestions = []
    temp = weather.get("temperature")
    humidity = weather.get("humidity")
    condition = (weather.get("condition") or "").lower()
    precip = weather.get("precipitation_mm")

    if precip is not None and precip >= 1.0:
        suggestions.append({
            "icon": "🌧️",
            "en": "Rain is reported — consider postponing spraying or fertiliser "
                  "application and check field drainage.",
            "te": "వర్షం ఉందని తెలుస్తోంది — పిచికారీ లేదా ఎరువులు వేయడం వాయిదా "
                  "వేయండి, పొలంలో నీరు పోయే ఏర్పాటు చూడండి.",
        })
    elif condition == "clear":
        suggestions.append({
            "icon": "☀️",
            "en": "Clear skies — if the soil is dry, consider morning irrigation to "
                  "reduce evaporation losses.",
            "te": "మబ్బు లేని వాతావరణం — నేల పొడిగా ఉంటే ఆవిరి తగ్గడానికి ఉదయం "
                  "నీటిపారుదల గురించి ఆలోచించండి.",
        })

    if temp is not None and temp >= 35:
        suggestions.append({
            "icon": "🌡️",
            "en": "High temperature expected — consider protective irrigation and "
                  "avoid heavy field work during peak heat.",
            "te": "అధిక ఉష్ణోగ్రత ఉంది — రక్షణ నీటిపారుదల గురించి ఆలోచించి, "
                  "తీవ్ర వేడి సమయంలో పొలం పనులు తగ్గించండి.",
        })
    elif temp is not None and temp <= 10:
        suggestions.append({
            "icon": "🧊",
            "en": "Cold conditions — young seedlings may be sensitive; keep an eye "
                  "on frost risk in your region.",
            "te": "చలి వాతావరణం — చిన్న మొలకలు ప్రభావితం కావచ్చు; మీ ప్రాంతంలో "
                  "మంచు ప్రమాదాన్ని గమనించండి.",
        })

    if humidity is not None and humidity >= 85 and condition not in ("rain", "drizzle"):
        suggestions.append({
            "icon": "💧",
            "en": "Very humid conditions — may favour fungal issues; inspect crops "
                  "regularly and avoid waterlogging.",
            "te": "అధిక తేమ ఉంది — ఫంగస్ సమస్యలకు అవకాశం ఉంది; పంటలను క్రమం "
                  "తప్పకుండా పరిశీలించి, నీరు చేరకుండా చూడండి.",
        })

    if not suggestions:
        suggestions.append({
            "icon": "🌱",
            "en": "Conditions look moderate — continue your regular irrigation and "
                  "monitoring schedule.",
            "te": "వాతావరణం సాధారణంగా ఉంది — మీ అలవాటు నీటిపారుదల, పరిశీలన "
                  "కొనసాగించండి.",
        })
    return suggestions
