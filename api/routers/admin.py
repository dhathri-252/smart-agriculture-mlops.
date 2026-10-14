"""Admin/monitoring endpoints — protected by the ADMIN_TOKEN environment variable.

No sensitive information is exposed publicly:
- Without ADMIN_TOKEN configured: the endpoint reports that monitoring is not
  configured (503).
- With a wrong/missing token: 401.
"""

import platform
import sys
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from api import db
from api.config import get_admin_token
from api.routers.system import APP_VERSION, _START_TIME
from src.predict import get_model_info

router = APIRouter(prefix="/api/admin")


async def _require_admin(
    x_admin_token: Optional[str] = Header(default=None),
) -> None:
    configured = get_admin_token()
    if not configured:
        raise HTTPException(
            status_code=503,
            detail="Admin monitoring is not configured. Set the ADMIN_TOKEN "
                   "environment variable to enable it.",
        )
    if not x_admin_token or x_admin_token != configured:
        raise HTTPException(status_code=401, detail="Invalid admin token.")


@router.get(
    "/stats",
    tags=["Admin"],
    summary="Admin statistics (requires X-Admin-Token)",
    description=(
        "Prediction counts, recent activity, model information, application "
        "health and basic system statistics. Requires the ADMIN_TOKEN header."
    ),
)
def stats(_: None = Depends(_require_admin)):
    try:
        model_info = get_model_info()
    except Exception as exc:  # noqa: BLE001
        model_info = {"error": f"Model unavailable: {exc}"}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "predictions": {
            "total": db.count_predictions(),
            "by_crop": db.crop_frequency(limit=10),
            "daily_last_7_days": db.daily_prediction_counts(days=7),
            "recent": db.recent_activity(limit=10),
        },
        "users": {"total": db.count_users()},
        "model": model_info,
        "health": {
            "status": "healthy",
            "app_version": APP_VERSION,
            "uptime_seconds": int(time.time() - _START_TIME),
            "database_bytes": db.db_size_bytes(),
        },
        "system": {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
        },
    }
