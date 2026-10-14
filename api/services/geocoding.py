"""Global place search via OpenWeather's Geocoding API (direct geocoding).

- ``/geo/1.0/direct`` resolves place names anywhere in the world (villages,
  towns, districts, cities, postal codes where the provider has data) into
  structured results with latitude/longitude for weather lookups.
- The API key is read server-side from WEATHER_API_KEY and never exposed.
- Successful (including empty) responses are cached in memory for a short TTL
  to limit provider calls while staying privacy-compatible: nothing is
  persisted to disk, and only the typed place query (no coordinates, no user
  identity) is held, in memory only.
- Provider results are never invented or silently substituted; failures are
  reported with bilingual messages so callers can ask the user to retry.
"""

import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from api.config import get_weather_api_key
from api.services.weather import SSL_CONTEXT

logger = logging.getLogger("api.geocoding")

DIRECT_URL = "https://api.openweathermap.org/geo/1.0/direct"
REQUEST_TIMEOUT_SECONDS = 8
CACHE_TTL_SECONDS = 600
CACHE_MAX_ENTRIES = 500

NOT_CONFIGURED_MESSAGE = {
    "en": "Location search is not configured. Set WEATHER_API_KEY on the server "
          "to enable global place search.",
    "te": "ప్రదేశ శోధన కాన్ఫిగర్ చేయబడలేదు. ప్రపంచవ్యాప్త ప్రదేశ శోధనను "
          "ప్రారంభించడానికి సర్వర్‌లో WEATHER_API_KEY సెట్ చేయండి.",
}

_UNAVAILABLE_MESSAGE = {
    "en": "Location search is temporarily unavailable. Please try again shortly.",
    "te": "ప్రదేశ శోధన ప్రస్తుతం అందుబాటులో లేదు. కొద్దిసేపటి తర్వాత మళ్లీ "
          "ప్రయత్నించండి.",
}

_INVALID_KEY_MESSAGE = {
    "en": "The configured weather API key is invalid or not yet active. Update "
          "WEATHER_API_KEY on the server to restore location search.",
    "te": "కాన్ఫిగర్ చేసిన API కీ చెల్లదు లేదా ఇంకా క్రియాశీలంగా లేదు. ప్రదేశ "
          "శోధనను తిరిగి పొందడానికి సర్వర్‌లో WEATHER_API_KEY మార్చండి.",
}

_RATE_LIMIT_MESSAGE = {
    "en": "Location search rate limit exceeded. Please wait a moment and try again.",
    "te": "ప్రదేశ శోధన రేటు పరిమితి దాటింది. కొంత సేపటి తర్వాత మళ్లీ ప్రయత్నించండి.",
}

# In-memory, short-lived cache: normalized query -> (monotonic ts, results).
_cache_lock = threading.Lock()
_search_cache: dict = {}


def _cache_get(normalized: str):
    with _cache_lock:
        entry = _search_cache.get(normalized)
        if entry is None:
            return None
        ts, results = entry
        if time.monotonic() - ts > CACHE_TTL_SECONDS:
            del _search_cache[normalized]
            return None
        return results


def _cache_put(normalized: str, results: list) -> None:
    with _cache_lock:
        if normalized not in _search_cache and len(_search_cache) >= CACHE_MAX_ENTRIES:
            # Evict the oldest entry to bound memory.
            oldest = min(_search_cache, key=lambda k: _search_cache[k][0])
            _search_cache.pop(oldest, None)
        _search_cache[normalized] = (time.monotonic(), results)


def _map_entry(entry: dict) -> dict:
    """Map one provider geocoding entry to a structured, selectable result."""
    name = entry.get("name") or ""
    state = entry.get("state") or ""
    country = entry.get("country") or ""
    label = ", ".join(part for part in (name, state, country) if part)
    return {
        "name": name,
        "state": state,
        "country": country,
        "lat": entry.get("lat"),
        "lon": entry.get("lon"),
        "label": label or name,
    }


def search_places(query: str, limit: int = 5) -> dict:
    """Search places worldwide; returns structured selectable results.

    Result shape: ``{"configured": bool, "query": str, "count": int,
    "results": [...], "message": {...}?}``. A 200 response with an empty
    ``results`` list and no ``message`` means the provider found no match.
    """
    query = (query or "").strip()
    normalized = query.casefold()
    api_key = get_weather_api_key()
    if not api_key:
        return {
            "configured": False,
            "query": query,
            "count": 0,
            "results": [],
            "message": NOT_CONFIGURED_MESSAGE,
        }

    cached = _cache_get(normalized)
    if cached is not None:
        return {
            "configured": True,
            "query": query,
            "count": len(cached),
            "results": [dict(item) for item in cached],
        }

    params = urllib.parse.urlencode(
        {"q": query, "limit": max(1, min(int(limit), 10)), "appid": api_key}
    )
    request = urllib.request.Request(f"{DIRECT_URL}?{params}")
    try:
        with urllib.request.urlopen(
            request, timeout=REQUEST_TIMEOUT_SECONDS, context=SSL_CONTEXT
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Log only the status and the provider's credential-free body snippet —
        # never the request URL, which carries the API key.
        try:
            detail = exc.read().decode("utf-8", "replace")[:200]
        except Exception:
            detail = ""
        if exc.code in (401, 403):
            logger.warning(
                "Geocoding provider rejected the configured key (HTTP %s): %s",
                exc.code,
                detail or exc.reason,
            )
            message = _INVALID_KEY_MESSAGE
        elif exc.code == 429:
            logger.warning(
                "Geocoding provider rate limit exceeded (HTTP 429): %s",
                detail or exc.reason,
            )
            message = _RATE_LIMIT_MESSAGE
        else:
            logger.warning(
                "Geocoding provider HTTP error %s: %s", exc.code, detail or exc
            )
            message = _UNAVAILABLE_MESSAGE
        return {
            "configured": True,
            "query": query,
            "count": 0,
            "results": [],
            "message": message,
        }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.warning(
            "Geocoding provider request failed (%s): %s", type(exc).__name__, exc
        )
        return {
            "configured": True,
            "query": query,
            "count": 0,
            "results": [],
            "message": _UNAVAILABLE_MESSAGE,
        }

    if not isinstance(body, list):
        logger.warning("Geocoding provider returned an unexpected payload shape")
        return {
            "configured": True,
            "query": query,
            "count": 0,
            "results": [],
            "message": _UNAVAILABLE_MESSAGE,
        }

    results = [_map_entry(entry) for entry in body if isinstance(entry, dict)]
    _cache_put(normalized, results)
    return {
        "configured": True,
        "query": query,
        "count": len(results),
        "results": results,
    }
