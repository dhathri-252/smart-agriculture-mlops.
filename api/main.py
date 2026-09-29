import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.predict import predict_crop

from api.docs import redoc_html, swagger_ui_html


class CropInput(BaseModel):
    N: float = Field(
        ...,
        description="Nitrogen (N) — nitrogen content in the soil.",
        json_schema_extra={"example": 90},
    )
    P: float = Field(
        ...,
        description="Phosphorus (P) — phosphorus content in the soil.",
        json_schema_extra={"example": 42},
    )
    K: float = Field(
        ...,
        description="Potassium (K) — potassium content in the soil.",
        json_schema_extra={"example": 43},
    )
    temperature: float = Field(
        ...,
        description="Temperature — ambient temperature in degrees Celsius (°C).",
        json_schema_extra={"example": 20.87},
    )
    humidity: float = Field(
        ...,
        description="Humidity — relative humidity as a percentage (%).",
        json_schema_extra={"example": 82.0},
    )
    ph: float = Field(
        ...,
        description="Soil pH — soil acidity/alkalinity value (pH scale).",
        json_schema_extra={"example": 6.5},
    )
    rainfall: float = Field(
        ...,
        description="Rainfall — rainfall in millimeters (mm).",
        json_schema_extra={"example": 202.93},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "N": 90,
                "P": 42,
                "K": 43,
                "temperature": 20.87,
                "humidity": 82.0,
                "ph": 6.5,
                "rainfall": 202.93,
            }
        }
    }


class CropPredictionResponse(BaseModel):
    recommended_crop: str = Field(
        ...,
        description="Crop recommended by the trained Random Forest model.",
        json_schema_extra={"example": "rice"},
    )


_DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _get_allowed_origins() -> list:
    raw = os.environ.get("CORS_ALLOW_ORIGINS", "")
    extras = [o.strip() for o in raw.split(",") if o.strip()]
    seen = set()
    origins = []
    for origin in _DEFAULT_ORIGINS + extras:
        if origin not in seen:
            seen.add(origin)
            origins.append(origin)
    return origins


ALLOWED_ORIGINS = _get_allowed_origins()


openapi_tags = [
    {
        "name": "System",
        "description": "Base system endpoint. Confirms the API is running.",
    },
    {
        "name": "Health",
        "description": "Service health check endpoint.",
    },
    {
        "name": "Crop Prediction",
        "description": (
            "Core AI functionality. Uses the trained Random Forest model to "
            "recommend a suitable crop based on soil and environmental conditions."
        ),
    },
]


app = FastAPI(
    title="Smart Agriculture Prediction API",
    description="AI-powered crop recommendation API for the Smart Agriculture Prediction System.",
    version="1.0.0",
    openapi_tags=openapi_tags,
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["System"],
    summary="Smart Agriculture API",
    description="Returns basic information confirming that the API is running.",
)
def root():
    return {"message": "Smart Agriculture Prediction API is running"}


@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Checks whether the Smart Agriculture prediction service is available.",
)
def health():
    return {"status": "healthy"}


@app.post(
    "/predict",
    tags=["Crop Prediction"],
    summary="Crop Prediction",
    description=(
        "Uses the trained Random Forest model to recommend a suitable crop "
        "based on soil and environmental conditions."
    ),
    response_model=CropPredictionResponse,
    responses={
        200: {
            "description": "Crop recommended by the trained Random Forest model.",
            "content": {
                "application/json": {
                    "example": {"recommended_crop": "rice"},
                }
            },
        },
        422: {"description": "Validation error: missing or invalid input fields."},
    },
)
def predict(data: CropInput):
    recommended_crop = predict_crop(
        N=data.N,
        P=data.P,
        K=data.K,
        temperature=data.temperature,
        humidity=data.humidity,
        ph=data.ph,
        rainfall=data.rainfall,
    )
    return {"recommended_crop": recommended_crop}


@app.get("/api-docs", include_in_schema=False)
def api_docs():
    return swagger_ui_html()


@app.get("/redoc", include_in_schema=False)
def redoc_docs():
    return redoc_html()

