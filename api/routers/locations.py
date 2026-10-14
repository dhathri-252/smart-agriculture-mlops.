"""Location search endpoints (global geocoding)."""

from fastapi import APIRouter, Query

from api.services import geocoding as geocoding_service

router = APIRouter(prefix="/api")


@router.get(
    "/locations/search",
    tags=["Locations"],
    summary="Search Places Worldwide",
    description=(
        "Geocodes a free-text place query (village, town, district, city, "
        "state, country, or postal code where the provider has data) into "
        "structured, selectable results with latitude/longitude for weather "
        "lookups. Coverage depends on the geocoding provider's available data. "
        "The provider key stays server-side."
    ),
)
def search_locations(
    q: str = Query(
        ..., min_length=2, max_length=100,
        description="Place query, e.g. 'Tokyo', 'London, UK' or 'Peddaparimi'.",
        json_schema_extra={"example": "Tokyo"},
    ),
    limit: int = Query(
        5, ge=1, le=10, description="Maximum number of results (1-10)."
    ),
):
    return geocoding_service.search_places(q.strip(), limit=limit)