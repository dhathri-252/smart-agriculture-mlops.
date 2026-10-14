"""System endpoints: root info and health check."""

import time

from fastapi import APIRouter

from src.predict import load_model

router = APIRouter()

APP_VERSION = "1.1.0"
_START_TIME = time.time()


@router.get(
    "/",
    tags=["System"],
    summary="Smart Agriculture API",
    description="Returns basic information confirming that the API is running.",
)
def root():
    return {
        "message": "Smart Agriculture Prediction API is running",
        "version": APP_VERSION,
    }


@router.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Checks whether the Smart Agriculture prediction service is available.",
)
def health():
    model_ready = True
    try:
        load_model()
    except Exception:  # noqa: BLE001 - health must never raise
        model_ready = False
    return {
        "status": "healthy" if model_ready else "degraded",
        "model_ready": model_ready,
        "version": APP_VERSION,
        "uptime_seconds": int(time.time() - _START_TIME),
    }
