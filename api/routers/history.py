"""Prediction history endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from api import db
from api.deps import optional_user
from api.schemas import HistoryResponse

router = APIRouter(prefix="/api")


@router.get(
    "/history",
    response_model=HistoryResponse,
    tags=["History"],
    summary="Prediction History",
    description=(
        "Returns stored predictions (most recent first). Use ?mine=true while "
        "logged in to see only your own predictions."
    ),
)
def get_history(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of items."),
    mine: bool = Query(False, description="Only predictions made by the logged-in user."),
    user=Depends(optional_user),
):
    user_id = None
    if mine:
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Log in to view your personal prediction history.",
            )
        user_id = user["id"]
    items = db.list_predictions(limit=limit, user_id=user_id)
    return {"items": items, "total": db.count_predictions(user_id=user_id)}


@router.delete(
    "/history",
    tags=["History"],
    summary="Clear Prediction History",
    description="Deletes stored prediction history. Use ?mine=true to delete only your own.",
)
def clear_history(
    mine: bool = Query(False, description="Only delete the logged-in user's history."),
    user=Depends(optional_user),
):
    user_id = None
    if mine:
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Log in to clear your personal prediction history.",
            )
        user_id = user["id"]
    deleted = db.clear_predictions(user_id=user_id)
    return {"deleted": deleted}
