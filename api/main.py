"""Smart Agriculture Prediction API — application entrypoint.

Preserves the original ``api.main:app`` module path used by Docker/uvicorn,
the custom documentation pages, and the original endpoints (``/``, ``/health``,
``POST /predict``). Feature endpoints are organised into ``api.routers``.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api import db
from api.config import get_cors_origins
from api.docs import redoc_html, swagger_ui_html
from api.routers import (
    admin,
    assistant,
    auth,
    catalogue,
    daily,
    history,
    locations,
    predict,
    recommend,
    system,
    weather,
)
from api.routers.system import APP_VERSION

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("api")

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
    {
        "name": "Catalogue",
        "description": "Multilingual educational crop catalogue (search, filter, guides). Separate from ML predictions.",
    },
    {
        "name": "History",
        "description": "Stored prediction history (list and clear).",
    },
    {
        "name": "Recommendations",
        "description": "Smart farming recommendations combining prediction, soil and weather.",
    },
    {
        "name": "Daily Recommendations",
        "description": "Rules-based daily crop suitability guidance (seasonal, weather-aware). Separate from ML predictions.",
    },
    {
        "name": "Assistant",
        "description": "AI agriculture assistant (provider abstraction with safe fallback).",
    },
    {
        "name": "Weather",
        "description": "Live weather lookup when a provider is configured.",
    },
    {
        "name": "Locations",
        "description": "Global place search (geocoding) for weather lookups.",
    },
    {
        "name": "Auth",
        "description": "Registration, login and farmer profile (hashed passwords, signed tokens).",
    },
    {
        "name": "Admin",
        "description": "Admin/monitoring statistics, protected by ADMIN_TOKEN.",
    },
]

app = FastAPI(
    title="Smart Agriculture Prediction API",
    description=(
        "AI-powered crop recommendation API for the Smart Agriculture Prediction System."
    ),
    version=APP_VERSION,
    openapi_tags=openapi_tags,
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
)

ALLOWED_ORIGINS = get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def access_log(request: Request, call_next):
    """Basic request logging (method, path, status, duration)."""
    import time

    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# Create tables on import (idempotent) so the API works even when lifespan
# events are not triggered (e.g. some test harnesses).
db.init_db()

app.include_router(system.router)
app.include_router(predict.router)
app.include_router(catalogue.router)
app.include_router(history.router)
app.include_router(recommend.router)
app.include_router(daily.router)
app.include_router(assistant.router)
app.include_router(weather.router)
app.include_router(locations.router)
app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/api-docs", include_in_schema=False)
def api_docs():
    return swagger_ui_html()


@app.get("/redoc", include_in_schema=False)
def redoc_docs():
    return redoc_html()
