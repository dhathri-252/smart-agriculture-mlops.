"""Shared request/response schemas for the Smart Agriculture API."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class CropInput(BaseModel):
    N: float = Field(
        ..., description="Nitrogen (N) — nitrogen content in the soil.",
        json_schema_extra={"example": 90},
    )
    P: float = Field(
        ..., description="Phosphorus (P) — phosphorus content in the soil.",
        json_schema_extra={"example": 42},
    )
    K: float = Field(
        ..., description="Potassium (K) — potassium content in the soil.",
        json_schema_extra={"example": 43},
    )
    temperature: float = Field(
        ..., description="Temperature — ambient temperature in degrees Celsius (°C).",
        json_schema_extra={"example": 20.87},
    )
    humidity: float = Field(
        ..., description="Humidity — relative humidity as a percentage (%).",
        json_schema_extra={"example": 82.0},
    )
    ph: float = Field(
        ..., description="Soil pH — soil acidity/alkalinity value (pH scale).",
        json_schema_extra={"example": 6.5},
    )
    rainfall: float = Field(
        ..., description="Rainfall — rainfall in millimeters (mm).",
        json_schema_extra={"example": 202.93},
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "N": 90, "P": 42, "K": 43, "temperature": 20.87,
                "humidity": 82.0, "ph": 6.5, "rainfall": 202.93,
            }
        }
    }


class WeatherHint(BaseModel):
    """Optional live weather context supplied by the client's weather lookup."""

    location: Optional[str] = Field(None, max_length=80)
    temperature: Optional[float] = Field(None, description="Air temperature °C.")
    humidity: Optional[float] = Field(None, description="Relative humidity %.")
    condition: Optional[str] = Field(None, max_length=60, description="e.g. Rain, Clear, Clouds")
    rainfall_mm: Optional[float] = Field(
        None, description="Precipitation in mm (last hour) when the provider reports it."
    )


class TopPrediction(BaseModel):
    crop: str
    probability: Optional[float] = Field(
        None, description="Model probability from predict_proba (null if unsupported)."
    )


class BilingualText(BaseModel):
    en: str
    te: str


class CropInfo(BaseModel):
    """Farmer-friendly information card for the recommended crop."""

    crop: str
    name: str
    emoji: str
    ranges: dict = Field(
        default_factory=dict,
        description="Dataset-derived per-feature ranges (temperature, humidity, rainfall, ph, N, P, K).",
    )
    soil: BilingualText
    irrigation: BilingualText
    fertilizer: BilingualText
    cultivation: BilingualText
    disclaimer: BilingualText


class CropPredictionResponse(BaseModel):
    recommended_crop: str = Field(
        ..., description="Crop recommended by the trained Random Forest model.",
        json_schema_extra={"example": "rice"},
    )
    confidence: Optional[float] = Field(
        None, description="Model probability of the top crop (real predict_proba value).",
    )
    top_predictions: list[TopPrediction] = Field(
        default_factory=list, description="Top-N crops ranked by model probability."
    )
    probabilities_available: bool = True
    input_warnings: list[str] = Field(
        default_factory=list,
        description="Warnings when inputs fall outside the training-data ranges.",
    )
    crop_info: Optional[CropInfo] = None
    model_type: Optional[str] = None
    history_id: Optional[int] = None
    predicted_at: Optional[str] = None


class HistoryItem(BaseModel):
    id: int
    created_at: str
    inputs: dict
    crop: str
    confidence: Optional[float] = None
    top_predictions: list[TopPrediction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int


class RecommendationCard(BaseModel):
    icon: str
    title: BilingualText
    body: BilingualText


class RecommendRequest(CropInput):
    weather: Optional[WeatherHint] = None


class RecommendResponse(BaseModel):
    crop: str
    confidence: Optional[float] = None
    recommendations: list[RecommendationCard]
    weather_used: bool = False


class ChatTurn(BaseModel):
    """One prior conversation turn supplied by the client for follow-ups."""

    role: Literal["user", "assistant"]
    text: str = Field(..., min_length=1, max_length=1000)


class AssistantRequest(BaseModel):
    question: str = Field(
        ..., min_length=2, max_length=1000,
        description="Free-text farming question.",
        json_schema_extra={"example": "How often should I irrigate rice?"},
    )
    language: Literal["en", "te"] = "en"
    weather: Optional[WeatherHint] = Field(
        None,
        description=(
            "Optional live-weather summary from the app's Weather page "
            "(place name and metrics only — never coordinates or API keys)."
        ),
    )
    history: Optional[List[ChatTurn]] = Field(
        None, max_length=8,
        description=(
            "Optional recent conversation turns (user/assistant) so follow-up "
            "questions have context. Oldest first; at most 8 turns."
        ),
    )


class AssistantResponse(BaseModel):
    answer: dict = Field(
        ..., description="Bilingual answer text keyed by language (en/te)."
    )
    provider: str = Field(..., description="knowledge_base or openai")
    language: Literal["en", "te"]
    disclaimer: BilingualText


class RegisterRequest(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=32,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description="Alphanumeric username (3–32 chars).",
    )
    password: str = Field(..., min_length=8, max_length=128)
    farm_name: str = Field("", max_length=60)
    location: str = Field("", max_length=60)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=32)
    password: str = Field(..., min_length=1, max_length=128)


class ProfileUpdateRequest(BaseModel):
    farm_name: str = Field("", max_length=60)
    location: str = Field("", max_length=60)


class UserOut(BaseModel):
    id: int
    username: str
    farm_name: str = ""
    location: str = ""
    created_at: Optional[str] = None


class AuthResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserOut
