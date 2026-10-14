"""Smart farming recommendations combining prediction, soil and weather."""

from fastapi import APIRouter, Depends, HTTPException

from api.deps import optional_user
from api.schemas import RecommendRequest, RecommendResponse
from api.services.weather import weather_farming_suggestions
from src.crop_info import get_crop_info
from src.predict import predict_crop_detailed

router = APIRouter(prefix="/api")


def _build_recommendations(data: RecommendRequest, crop: str, confidence, info) -> list:
    cards = []
    ranges = info["ranges"]

    # 1. Crop care (from dataset-grounded cultivation note)
    cards.append({
        "icon": "🌱",
        "title": {"en": f"Crop care for {info['name']}", "te": f"{info['name']} పంట సంరక్షణ"},
        "body": info["cultivation"],
    })

    # 2. Irrigation guidance
    irrigation = dict(info["irrigation"])
    if data.weather and data.weather.humidity is not None and data.weather.humidity >= 85:
        irrigation["en"] += (
            " Current humidity is high, so consider reducing frequency and always "
            "check soil moisture first."
        )
        irrigation["te"] += (
            " ప్రస్తుతం తేమ ఎక్కువగా ఉంది కాబట్టి తరచుదనం తగ్గించి, "
            "ముందుగా నేల తేమ చూడండి."
        )
    cards.append({
        "icon": "💧",
        "title": {"en": "Irrigation", "te": "నీటిపారుదల"},
        "body": irrigation,
    })

    # 3. Soil & fertiliser guidance
    cards.append({
        "icon": "🧪",
        "title": {"en": "Soil & fertiliser", "te": "నేల & ఎరువులు"},
        "body": info["soil"],
    })
    cards.append({
        "icon": "⚖️",
        "title": {"en": "Nutrient guidance", "te": "పోషక సూచన"},
        "body": info["fertilizer"],
    })

    # 4. Compare the user's inputs with typical dataset ranges for this crop
    comparisons = []
    for key, unit in (("temperature", "°C"), ("humidity", "%"), ("rainfall", "mm")):
        value = data.model_dump().get(key)
        lo, hi = ranges[key]
        if value is None:
            continue
        if lo <= value <= hi:
            comparisons.append(
                {"en": f"Your {key} ({value} {unit}) is within the typical range "
                       f"for {info['name']} ({lo}–{hi} {unit}).",
                 "te": f"మీ {key} ({value} {unit}) {info['name']} కు సాధారణ "
                       f"పరిధి ({lo}–{hi} {unit}) లో ఉంది."}
            )
        else:
            comparisons.append({
                "en": f"Your {key} ({value} {unit}) is outside the typical range "
                      f"for {info['name']} ({lo}–{hi} {unit}) — consider whether "
                      "local conditions differ from the model's training data.",
                "te": f"మీ {key} ({value} {unit}) {info['name']} సాధారణ పరిధి "
                      f"({lo}–{hi} {unit}) వెలుపల ఉంది — మీ స్థానిక పరిస్థితులు "
                      "మోడల్ డేటాకు భిన్నంగా ఉండవచ్చని గమనించండి.",
            })
    if comparisons:
        cards.append({
            "icon": "🌡️",
            "title": {"en": "Your conditions vs. typical", "te": "మీ పరిస్థితులు vs. సాధారణం"},
            "body": {
                "en": " ".join(c["en"] for c in comparisons),
                "te": " ".join(c["te"] for c in comparisons),
            },
        })

    # 5. Weather-based suggestions (only when real weather was supplied)
    if data.weather and (
        data.weather.temperature is not None
        or data.weather.humidity is not None
        or data.weather.condition
    ):
        weather_dict = {
            "temperature": data.weather.temperature,
            "humidity": data.weather.humidity,
            "condition": data.weather.condition,
            "precipitation_mm": data.weather.rainfall_mm,
        }
        for sug in weather_farming_suggestions(weather_dict):
            cards.append({
                "icon": sug["icon"],
                "title": {"en": "Weather note", "te": "వాతావరణ గమనిక"},
                "body": {"en": sug["en"], "te": sug["te"]},
            })

    # 6. Disclaimer (always last)
    cards.append({
        "icon": "ℹ️",
        "title": {"en": "Please note", "te": "గమనిక"},
        "body": info["disclaimer"],
    })
    return cards


@router.post(
    "/recommendations",
    response_model=RecommendResponse,
    tags=["Recommendations"],
    summary="Smart Farming Recommendations",
    description=(
        "Combines the crop prediction, soil inputs and (optionally) weather into "
        "practical, general farming recommendations. Wording is intentionally "
        "hedged ('recommended', 'consider', 'may be suitable') — nothing here is "
        "a guarantee."
    ),
)
def recommend(data: RecommendRequest, user=Depends(optional_user)):
    try:
        result = predict_crop_detailed(
            N=data.N, P=data.P, K=data.K,
            temperature=data.temperature, humidity=data.humidity,
            ph=data.ph, rainfall=data.rainfall,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=f"Prediction model is not available: {exc}")

    crop = result["recommended_crop"]
    info = get_crop_info(crop)
    if info is None:
        raise HTTPException(status_code=500, detail="Crop information unavailable.")

    cards = _build_recommendations(data, crop, result["confidence"], info)
    return {
        "crop": crop,
        "confidence": result["confidence"],
        "recommendations": cards,
        "weather_used": bool(data.weather),
    }
