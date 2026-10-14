"""Catalogue service: enrich raw entries with honest status flags + search.

- Every non-English name is reported as ``unverified`` (never verified).
- Absent languages are reported as ``missing`` — never guessed.
- ``image`` comes from the bundled manifest (frontend/public/images/crops/):
  only entries verified through the Commons fetch pipeline (real file page,
  real author, free license) are ``verified``; everything else stays
  ``pending`` with an emoji placeholder — never a fabricated photo.
- Guides are always ``guide_verified: False`` ("general guidance").
- ``model_supported`` is True only for the 22 RF training labels.
"""

import json
from functools import lru_cache
from pathlib import Path

from api.catalogue_data import (
    CATEGORIES, CATEGORY_IDS, GUIDE_DISCLAIMER_EN, LANGS, LANG_LABELS, LANG_NATIVE, CROPS,
)

MODEL_LABELS = {
    "apple", "banana", "blackgram", "chickpea", "coconut", "coffee", "cotton",
    "grapes", "jute", "kidneybeans", "lentil", "maize", "mango", "mothbeans",
    "mungbean", "muskmelon", "orange", "papaya", "pigeonpeas", "pomegranate",
    "rice", "watermelon",
}

# Catalogue id -> model label (names differ for a few crops).
MODEL_ID_MAP = {
    "blackgram": "blackgram", "chickpea": "chickpea", "coconut": "coconut",
    "coffee": "coffee", "cotton": "cotton", "grapes": "grapes", "jute": "jute",
    "kidneybean": "kidneybeans", "lentil": "lentil", "maize": "maize",
    "mango": "mango", "mothbean": "mothbeans", "greengram": "mungbean",
    "muskmelon": "muskmelon", "orange": "orange", "papaya": "papaya",
    "pigeonpea": "pigeonpeas", "pomegranate": "pomegranate", "rice": "rice",
    "apple": "apple", "banana": "banana", "watermelon": "watermelon",
}

CAT_EMOJI = {c["id"]: c["emoji"] for c in CATEGORIES}
CAT_EN = {c["id"]: c["en"] for c in CATEGORIES}

_IMAGE_MANIFEST_PATHS = [
    Path(__file__).resolve().parent.parent / "frontend" / "public" / "images" / "crops" / "manifest.json",
    Path(__file__).resolve().parent.parent / "api" / "static" / "images" / "crops" / "manifest.json",
]


@lru_cache(maxsize=1)
def _image_manifest() -> dict:
    """Bundled image manifest: crop_id -> record. Empty when not yet fetched."""
    for path in _IMAGE_MANIFEST_PATHS:
        try:
            if path.exists():
                records = json.loads(path.read_text())
                return {r["crop_id"]: r for r in records if r.get("verified")}
        except Exception:
            continue
    return {}


def _image_for(crop_id: str) -> tuple:
    """Return (image_url, status, attribution) for a crop.

    Only manifest-verified entries produce a URL. Everything else is honest
    ``pending`` — the frontend renders the emoji placeholder instead.
    """
    rec = _image_manifest().get(crop_id)
    if not rec:
        return None, "pending", None
    attribution = f"{rec.get('author', 'Unknown')} / {rec.get('source', 'Wikimedia Commons')} / {rec.get('license', '')}".strip(" /")
    return (
        f"/{rec['file']}",
        "verified",
        {
            "author": rec.get("author"),
            "license": rec.get("license"),
            "source": rec.get("source", "Wikimedia Commons"),
            "source_url": rec.get("source_url"),
            "attribution": attribution,
        },
    )


def _name_status(entry_names: dict) -> dict:
    return {lang: ("verified" if lang == "en" else ("unverified" if lang in entry_names else "missing")) for lang in LANGS}


def enrich(entry: dict) -> dict:
    names = {"en": entry["en"], **{k: v for k, v in entry.get("n", {}).items() if v}}
    model_label = MODEL_ID_MAP.get(entry["id"])
    image_url, image_status, attribution = _image_for(entry["id"])
    if image_url:
        alt_text = (
            f"Photograph of {entry['en']} growing in the field "
            f"(source: Wikimedia Commons — see attribution)."
        )
    else:
        alt_text = f"{entry['en']} — illustrative placeholder (verified photograph pending)."
    return {
        "id": entry["id"],
        "name_en": entry["en"],
        "names": names,
        "name_status": _name_status(names),
        "categories": list(entry.get("cat", [])),
        "category_names": {cid: CAT_EN.get(cid, cid) for cid in entry.get("cat", [])},
        "emoji": entry.get("e") or "🌾",
        "category_emoji": CAT_EMOJI.get((entry.get("cat") or [""])[0], "🌾"),
        "image": image_url,
        "image_status": image_status,
        "image_attribution": attribution,
        "alt_text": alt_text,
        "guide": {
            "en": entry.get("g_en") or "",
            "te": entry.get("g_te") or "",
        },
        "guide_verified": False,
        "guide_note": GUIDE_DISCLAIMER_EN,
        "sources": [],
        "sources_status": "pending",
        "model_supported": model_label in MODEL_LABELS,
        "model_label": model_label if model_label in MODEL_LABELS else None,
    }


def list_crops(category: str = "", search: str = "", model_supported: bool = False) -> list:
    q = (search or "").strip().lower()
    out = []
    for entry in CROPS:
        item = enrich(entry)
        if category and category not in item["categories"]:
            continue
        if model_supported and not item["model_supported"]:
            continue
        if q and not any(q in str(v).lower() for v in item["names"].values()):
            continue
        out.append(item)
    return out


def count_crops(category: str = "", search: str = "", model_supported: bool = False) -> int:
    return len(list_crops(category=category, search=search, model_supported=model_supported))


def get_crop(crop_id: str):
    for entry in CROPS:
        if entry["id"] == (crop_id or "").strip().lower():
            return enrich(entry)
    return None


def meta() -> dict:
    items = [enrich(e) for e in CROPS]
    with_names = {lang: sum(1 for i in items if lang in i["names"]) for lang in LANGS}
    return {
        "total": len(items),
        "categories": CATEGORIES,
        "languages": [{"id": l, "label": LANG_LABELS[l], "native": LANG_NATIVE[l]} for l in LANGS],
        "model_labels": sorted(MODEL_LABELS),
        "model_supported_count": sum(1 for i in items if i["model_supported"]),
        "translation_coverage": with_names,
        "image_coverage": {
            "verified": sum(1 for i in items if i["image_status"] == "verified"),
            "pending": sum(1 for i in items if i["image_status"] != "verified"),
        },
        "image_licenses": image_license_breakdown(items),
        "guide_coverage": {"verified": 0, "general_guidance": len(items)},
    }


def image_license_breakdown(items: list) -> dict:
    """Count verified images by license (honest: pending is not a license)."""
    counts: dict = {}
    for item in items:
        attr = item.get("image_attribution") or {}
        lic = attr.get("license")
        if item.get("image_status") == "verified" and lic:
            counts[lic] = counts.get(lic, 0) + 1
    return counts
