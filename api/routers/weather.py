"""Weather endpoint with a clean unconfigured state."""

import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.services import weather as weather_service

router = APIRouter(prefix="/api")

_LOCATION_PATTERN = re.compile(r"^[\w\s,'\-\.]{2,80}$", re.UNICODE)


@router.get(
    "/weather",
    tags=["Weather"],
    summary="Current Weather for a Location",
    description=(
        "Returns live weather for the given location when a weather provider is "
        "configured (WEATHER_API_KEY). Provide either a place name (`location`) "
        "or coordinates (`lat` + `lon`) — e.g. from the browser Geolocation API. "
        "When not configured, returns a clear configuration message — live data "
        "is never fabricated."
    ),
)
def get_weather(
    location: Optional[str] = Query(
        None, min_length=2, max_length=80,
        description="City or place name, e.g. 'Hyderabad'.",
        json_schema_extra={"example": "Hyderabad"},
    ),
    lat: Optional[float] = Query(
        None, ge=-90, le=90,
        description="Latitude in decimal degrees (-90..90).",
    ),
    lon: Optional[float] = Query(
        None, ge=-180, le=180,
        description="Longitude in decimal degrees (-180..180).",
    ),
):
    has_name = location is not None and location.strip() != ""
    has_coords = lat is not None or lon is not None
    if has_coords and (lat is None or lon is None):
        raise HTTPException(
            status_code=422,
            detail="Both lat and lon are required for a coordinate lookup.",
        )
    if has_name and has_coords:
        raise HTTPException(
            status_code=422,
            detail="Provide either a location name or lat/lon coordinates, not both.",
        )
    if not has_name and not has_coords:
        raise HTTPException(
            status_code=422,
            detail="Provide a location name or lat/lon coordinates.",
        )
    provider = weather_service.get_weather_provider_instance()
    if has_coords:
        data = provider.fetch(None, lat, lon)
    else:
        location = location.strip()
        if not _LOCATION_PATTERN.match(location):
            raise HTTPException(
                status_code=422,
                detail="Location may only contain letters, numbers, spaces, dots, "
                       "commas, apostrophes and hyphens.",
            )
        data = provider.fetch(location)
    if data.get("configured") and data.get("found"):
        data["suggestions"] = weather_service.weather_farming_suggestions(data)
    return data
