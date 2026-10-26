"""Daily farming intelligence — rules-based crop suitability recommendations.

Strictly separate from ML prediction. Every entry is ``rules_based_guidance``
(general educational information from Indian season cycles) — never a substitute
for the 22-crop Random Forest model at ``POST /api/predict`` or
``POST /api/recommendations``.

Honesty contract:
- Live weather only when a provider is configured and a real observation is
  returned. Weather is never fabricated.
- Farmer-provided soil/water honored when given; missing inputs degrade the
  score honestly, never guessed from weather.
- No invented citations, timestamps, or measurements.
"""

import threading
import time
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.services.crop_suitability import (
    all_suitability,
    category_is_valid,
    crops_by_category,
    get_suitability,
    rank_crops,
    season_for,
    seasons_for_month,
)
from api.services.weather import get_weather_provider_instance

router = APIRouter(prefix="/api", tags=["Daily Recommendations"])

_cache: dict[str, tuple[float, object]] = {}
_cache_lock = threading.Lock()
CACHE_TTL_SECONDS = 300


def _cache_get(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        expiry, value = entry
        if time.time() > expiry:
            del _cache[key]
            return None
        return value


def _cache_set(key: str, value: object, ttl: int = CACHE_TTL_SECONDS) -> None:
    with _cache_lock:
        _cache[key] = (time.time() + ttl, value)


def _current_month() -> int:
    return date.today().month


_VALID_CATEGORIES_LIST = (
    "vegetables, fruits, cereals_millets, pulses_legumes, oilseeds, "
    "fibre_sugar_commercial, spices_condiments, plantation_beverage, "
    "fodder_forage, medicinal_aromatic"
)


def _season_in_season(crop, season: str) -> bool:
    season_months = {
        "kharif": {6, 7, 8, 9},
        "rabi": {10, 11, 12, 1, 2, 3},
        "zaid": {3, 4, 5, 6},
    }.get(season, set())
    return any(m in season_months for m in crop.planting_months)


def _suitability_to_dict(crop, score: int, season: str) -> dict:
    return {
        "id": crop.id,
        "name_en": crop.name_en,
        "category": crop.category,
        "emoji": crop.emoji,
        "guidance_type": "rules_based_guidance",
        "suitability_score": score,
        "season_match": _season_in_season(crop, season),
        "planting_months": crop.planting_months,
        "water_need": crop.water,
        "soil_types": crop.soil_types,
        "temp_range_c": [
            crop.temp_min_c, crop.temp_max_c
        ] if (crop.temp_min_c is not None or crop.temp_max_c is not None) else None,
        "duration_days": crop.duration_days,
        "risks": crop.risks,
        "precautions": crop.precautions,
        "data_source": crop.data_source,
        "last_updated": crop.last_updated,
    }


def _score_crop(
    crop, season: str, temperature_c, condition, farmer_soil, water_available
) -> int:
    _WEIGHT_SEASON = 40
    _WEIGHT_WEATHER = 30
    _WEIGHT_SOIL = 20
    _WEIGHT_WATER = 10
    score = 0
    season_months = {
        "kharif": {6, 7, 8, 9},
        "rabi": {10, 11, 12, 1, 2, 3},
        "zaid": {3, 4, 5, 6},
    }.get(season, set())
    overlap = sum(1 for m in crop.planting_months if m in season_months)
    if overlap >= len(crop.planting_months) // 2:
        score += _WEIGHT_SEASON
    elif overlap > 0:
        score += _WEIGHT_SEASON // 2
    if temperature_c is None:
        score += _WEIGHT_WEATHER // 2
    else:
        tmin = crop.temp_min_c or 0
        tmax = crop.temp_max_c or 50
        if tmin <= temperature_c <= tmax:
            score += _WEIGHT_WEATHER
        elif (tmin - 5) <= temperature_c <= (tmax + 5):
            score += _WEIGHT_WEATHER // 2
    if not farmer_soil:
        score += _WEIGHT_SOIL // 2
    else:
        soil_lower = farmer_soil.lower()
        matched = any(soil_lower in st or st in soil_lower for st in crop.soil_types)
        score += _WEIGHT_SOIL if matched else 0
    if not water_available:
        score += _WEIGHT_WATER // 2
    else:
        order = {"low": 0, "medium": 1, "high": 2}
        crop_level = order.get(crop.water, 1)
        farmer_level = order.get(water_available.lower(), 1)
        diff = abs(crop_level - farmer_level)
        if diff == 0:
            score += _WEIGHT_WATER
        elif diff == 1:
            score += _WEIGHT_WATER // 2
    return score


@router.get(
    "/daily-recommendations",
    tags=["Daily Recommendations"],
    summary="Daily crop suitability recommendations",
    description=(
        "Returns rules-based crop suitability guidance for the current season. "
        "Uses real weather data only when a provider is configured and reachable. "
        "Farmer-provided soil and water information is optional and never guessed. "
        "Clearly distinct from ML predictions (POST /api/predict)."
    ),
)
def daily_recommendations(
    location: Optional[str] = Query(
        None, min_length=2, max_length=80,
        description="Place name for live weather lookup (e.g. 'Hyderabad').",
    ),
    soil: Optional[str] = Query(
        None, max_length=40,
        description="Farmer-provided soil type (e.g. 'loamy', 'clay loam').",
    ),
    water: Optional[str] = Query(
        None, description="Water availability: low / medium / high.",
    ),
    month: Optional[int] = Query(
        None, ge=1, le=12,
        description="Override calendar month (1-12). Defaults to current month.",
    ),
    limit: Optional[int] = Query(
        10, ge=1, le=50,
        description="Maximum number of recommendations to return.",
    ),
    forecast: Optional[bool] = Query(
        False, description="Include a 3-month seasonal outlook.",
    ),
    category: Optional[str] = Query(
        None, description="Filter to one catalogue-approved category id.",
    ),
):
    use_month = month if month is not None else _current_month()
    season = season_for(use_month)

    if category is not None:
        if not category_is_valid(category):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Unknown category '{category}'. Approved: "
                    + _VALID_CATEGORIES_LIST
                ),
            )
        candidate_crops = crops_by_category(category)
    else:
        candidate_crops = all_suitability()

    weather_data = None
    weather_used = False
    weather_error = None
    if location and location.strip():
        try:
            provider = get_weather_provider_instance()
            weather_data = provider.fetch(location.strip())
            if weather_data.get("configured") and weather_data.get("found"):
                weather_used = True
            elif weather_data.get("configured") is False:
                weather_error = "not_configured"
            else:
                weather_error = "not_found"
        except Exception:
            weather_error = "provider_error"

    temperature = None
    condition = None
    if weather_data and weather_data.get("found"):
        temperature = weather_data.get("temperature")
        condition = weather_data.get("condition")

    ranked = rank_crops(
        candidate_crops,
        season=season,
        temperature_c=temperature,
        condition=condition,
        farmer_soil=soil,
        water_available=water,
    )
    top = ranked[:limit]

    recommendations = [
        _suitability_to_dict(
            c, _score_crop(c, season, temperature, condition, soil, water), season
        )
        for c in top
    ]

    forecast_outlook = None
    if forecast:
        outlook = []
        for offset in (0, 1, 2):
            m = ((use_month - 1 + offset) % 12) + 1
            s = season_for(m)
            monthly = rank_crops(
                candidate_crops, season=s, temperature_c=None, condition=None,
                farmer_soil=None, water_available=None,
            )[: max(1, limit // 3)]
            outlook.append({
                "month": m,
                "season": s,
                "top_crops": [
                    {
                        "id": c.id,
                        "name_en": c.name_en,
                        "category": c.category,
                        "emoji": c.emoji,
                        "suitability_score": _score_crop(c, s, None, None, None, None),
                    }
                    for c in monthly
                ],
            })
        forecast_outlook = outlook

    return {
        "guidance_type": "rules_based_guidance",
        "season": season,
        "month": use_month,
        "date": date.today().isoformat(),
        "weather": weather_data,
        "weather_used": weather_used,
        "weather_error": weather_error,
        "soil_provided": bool(soil),
        "water_provided": bool(water),
        "category_filter": category,
        "forecast": forecast_outlook,
        "recommendations": recommendations,
        "total": len(candidate_crops),
        "returned": len(recommendations),
        "disclaimer": (
            "General educational guidance only — not verified against a cited "
            "publication. Confirm variety, season and practices with ICAR "
            "guidance or your state agricultural extension service. "
            "This is not a substitute for the ML prediction model."
        ),
    }


@router.get(
    "/daily-recommendations/{crop_id}",
    tags=["Daily Recommendations"],
    summary="Suitability details for one crop",
    description="Returns the rules-based suitability profile for a single crop.",
)
def daily_recommendation_detail(crop_id: str):
    crop = get_suitability(crop_id)
    if crop is None:
        raise HTTPException(status_code=404, detail="Crop not found in suitability table.")
    return {
        "guidance_type": "rules_based_guidance",
        "id": crop.id,
        "name_en": crop.name_en,
        "category": crop.category,
        "emoji": crop.emoji,
        "planting_months": crop.planting_months,
        "season": season_for(crop.planting_months[0]) if crop.planting_months else "rabi",
        "water_need": crop.water,
        "soil_types": crop.soil_types,
        "temp_range_c": [
            crop.temp_min_c, crop.temp_max_c
        ] if (crop.temp_min_c is not None or crop.temp_max_c is not None) else None,
        "duration_days": crop.duration_days,
        "risks": crop.risks,
        "precautions": crop.precautions,
        "data_source": crop.data_source,
        "last_updated": crop.last_updated,
    }