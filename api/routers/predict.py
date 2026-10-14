"""Core crop prediction endpoint (extended with confidence + crop info)."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from api import db
from api.deps import optional_user
from api.schemas import CropInput, CropPredictionResponse
from src.crop_info import get_crop_info
from src.predict import get_model_info, predict_crop_detailed

router = APIRouter()


@router.post(
    "/predict",
    tags=["Crop Prediction"],
    summary="Crop Prediction",
    description=(
        "Uses the trained Random Forest model to recommend a suitable crop based "
        "on soil and environmental conditions. Includes the model's own "
        "probability as confidence, the top-3 candidate crops, a farmer-friendly "
        "information card for the recommended crop, and warnings when inputs fall "
        "outside the training-data range."
    ),
    response_model=CropPredictionResponse,
    responses={
        200: {
            "description": "Crop recommendation with confidence and crop info.",
            "content": {
                "application/json": {
                    "example": {
                        "recommended_crop": "rice",
                        "confidence": 0.9,
                        "top_predictions": [
                            {"crop": "rice", "probability": 0.9},
                            {"crop": "jute", "probability": 0.1},
                        ],
                        "probabilities_available": True,
                        "input_warnings": [],
                        "model_type": "RandomForestClassifier",
                    }
                }
            },
        },
        422: {"description": "Validation error: missing or invalid input fields."},
        503: {"description": "Prediction model is not available."},
    },
)
def predict(data: CropInput, user=Depends(optional_user)):
    try:
        result = predict_crop_detailed(
            N=data.N,
            P=data.P,
            K=data.K,
            temperature=data.temperature,
            humidity=data.humidity,
            ph=data.ph,
            rainfall=data.rainfall,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Prediction model is not available: {exc}",
        )

    crop = result["recommended_crop"]
    try:
        model_type = get_model_info()["model_type"]
    except Exception:  # noqa: BLE001 - model info must not break prediction
        model_type = None

    predicted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    history_id: Optional[int] = None
    try:
        history_id = db.record_prediction(
            inputs=data.model_dump(),
            crop=crop,
            confidence=result["confidence"],
            top_predictions=result["top_predictions"],
            warnings=result["input_warnings"],
            user_id=user["id"] if user else None,
        )
    except Exception:  # noqa: BLE001 - history must not break prediction
        pass

    return {
        "recommended_crop": crop,
        "confidence": result["confidence"],
        "top_predictions": result["top_predictions"],
        "probabilities_available": result["probabilities_available"],
        "input_warnings": result["input_warnings"],
        "crop_info": get_crop_info(crop),
        "model_type": model_type,
        "history_id": history_id,
        "predicted_at": predicted_at,
    }
