"""Crop catalogue endpoints — strictly separate from ML predictions.

Serves the educational multilingual catalogue (search, filter, detail).
Never claims catalogue crops are supported by the Random Forest model:
each item carries an explicit ``model_supported`` flag derived from the
model's actual training labels.
"""

from fastapi import APIRouter, HTTPException, Query

from api import catalogue_service as svc

router = APIRouter(prefix="/api/catalogue", tags=["Catalogue"])


@router.get(
    "",
    summary="List catalogue crops",
    description=(
        "Searchable, filterable list of catalogue crops. `search` matches "
        "English and any provided local-language names. `model_supported` "
        "flags the subset the Random Forest model can actually predict."
    ),
)
def list_crops(
    category: str = Query("", description="Category id, e.g. 'vegetables'."),
    search: str = Query("", description="Free text matched across all names."),
    model_supported: bool = Query(False, description="Only ML-predictable crops."),
):
    return {
        "items": svc.list_crops(category=category, search=search, model_supported=model_supported),
        "total": svc.count_crops(category=category, search=search, model_supported=model_supported),
    }


@router.get(
    "/meta",
    summary="Catalogue metadata",
    description="Categories, languages, model labels and coverage statistics.",
)
def catalogue_meta():
    return svc.meta()


@router.get(
    "/{crop_id}",
    summary="Crop detail",
    description="Full multilingual names (with missing/unverified flags), guide and sources.",
)
def crop_detail(crop_id: str):
    item = svc.get_crop(crop_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Crop not found in the catalogue.")
    return item
