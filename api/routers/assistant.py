"""Agriculture assistant endpoint."""

from fastapi import APIRouter

from api.schemas import AssistantRequest, AssistantResponse
from api.services import assistant as assistant_service

router = APIRouter(prefix="/api")


@router.post(
    "/assistant",
    response_model=AssistantResponse,
    tags=["Assistant"],
    summary="Ask the Agriculture Assistant",
    description=(
        "Answers general farming questions (crops, soil, irrigation, fertilizers, "
        "cultivation, basic pest awareness, farming practices). Uses the configured "
        "AI provider when available, otherwise a built-in knowledge base. Answers "
        "are informational and do not replace expert agricultural advice."
    ),
    responses={
        200: {
            "description": "Assistant answer (keyed by language).",
            "content": {
                "application/json": {
                    "example": {
                        "answer": {
                            "en": "Water early morning or late evening to reduce evaporation.",
                            "te": "ఆవిరి తగ్గడానికి ఉదయం నీరు పెట్టండి.",
                        },
                        "provider": "knowledge_base",
                        "language": "en",
                    }
                }
            },
        },
        422: {"description": "Validation error: question missing or too long."},
    },
)
def ask_assistant(payload: AssistantRequest):
    answer, provider = assistant_service.answer_question(
        payload.question, payload.language, payload.weather, payload.history
    )
    return {
        "answer": answer,
        "provider": provider,
        "language": payload.language,
        "disclaimer": assistant_service.DISCLAIMER,
    }
