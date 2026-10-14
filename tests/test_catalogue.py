"""Tests for the multilingual crop catalogue API.

Covers: category filtering, crop selection/detail, multilingual search,
duplicate-ID handling, and missing-data honesty flags.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_DB_PATH", os.path.join(ROOT, "data", "test_app.db"))

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_catalogue_meta_counts():
    r = client.get("/api/catalogue/meta")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 137
    assert len(body["categories"]) == 10
    assert body["model_supported_count"] == 22
    assert [c["id"] for c in body["categories"]] == [
        "vegetables", "fruits", "cereals_millets", "pulses_legumes",
        "oilseeds", "fibre_sugar_commercial", "spices_condiments",
        "plantation_beverage", "fodder_forage", "medicinal_aromatic",
    ]
    # Translation coverage: every crop has all 7 local names (flagged unverified).
    for lang in ("te", "hi", "ta", "kn", "ml", "mr", "bn"):
        assert body["translation_coverage"][lang] == 137
    # Image coverage: verified + pending must add up; licenses add up to verified.
    cov = body["image_coverage"]
    assert cov["verified"] + cov["pending"] == 137
    assert sum(body.get("image_licenses", {}).values()) == cov["verified"]
    assert body["guide_coverage"] == {"verified": 0, "general_guidance": 137}


def test_catalogue_no_duplicate_ids():
    r = client.get("/api/catalogue")
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()["items"]]
    assert len(ids) == len(set(ids)) == 137


def test_category_filtering():
    r = client.get("/api/catalogue", params={"category": "vegetables"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 30
    assert all("vegetables" in x["categories"] for x in body["items"])
    r = client.get("/api/catalogue", params={"category": "fruits"})
    assert r.json()["total"] == 27


def test_duplicate_crop_appears_in_multiple_filters():
    # Coconut is both a fruit and a plantation crop; chilli is vegetable + spice.
    for crop_id, cats in (("coconut", {"fruits", "plantation_beverage"}),
                          ("chilli", {"vegetables", "spices_condiments"})):
        r = client.get(f"/api/catalogue/{crop_id}")
        assert r.status_code == 200, crop_id
        assert cats <= set(r.json()["categories"]), crop_id
    # Maize is a cereal and a fodder crop.
    r = client.get("/api/catalogue/maize")
    assert {"cereals_millets", "fodder_forage"} <= set(r.json()["categories"])


def test_multilingual_search():
    # English
    r = client.get("/api/catalogue", params={"search": "mango"})
    assert r.json()["total"] >= 1
    assert any(x["id"] == "mango" for x in r.json()["items"])
    # Telugu (native script)
    r = client.get("/api/catalogue", params={"search": "మామిడి"})
    assert any(x["id"] == "mango" for x in r.json()["items"])
    # Hindi (native script)
    r = client.get("/api/catalogue", params={"search": "गेहूँ"})
    assert any(x["id"] == "wheat" for x in r.json()["items"])
    # No match
    r = client.get("/api/catalogue", params={"search": "zzz-no-such-crop"})
    assert r.json()["total"] == 0


def test_crop_detail_and_missing_data_flags():
    r = client.get("/api/catalogue/rice")
    assert r.status_code == 200
    body = r.json()
    assert body["name_en"] == "Rice"
    assert body["model_supported"] is True
    assert body["model_label"] == "rice"
    assert body["image_status"] in ("verified", "pending")
    if body["image_status"] == "verified":
        assert body["image"] and body["image"].startswith("/images/crops/")
        assert "hotograph" in body["alt_text"]
    else:
        assert body["image"] is None
        assert "placeholder" in body["alt_text"].lower() or "pending" in body["alt_text"].lower()
    assert body["guide_verified"] is False
    assert body["name_status"]["en"] == "verified"
    assert body["name_status"]["te"] == "unverified"
    if body["image_status"] == "pending":
        assert "placeholder" in body["alt_text"].lower()

    # A catalogue-only crop is honestly flagged as NOT model-supported.
    r = client.get("/api/catalogue/tomato")
    assert r.json()["model_supported"] is False
    assert r.json()["model_label"] is None


def test_crop_detail_404():
    assert client.get("/api/catalogue/not-a-crop").status_code == 404


def test_model_only_filter_matches_training_labels():
    r = client.get("/api/catalogue", params={"model_supported": "true"})
    assert r.status_code == 200
    assert r.json()["total"] == 22
    labels = {x["model_label"] for x in r.json()["items"]}
    assert labels == {
        "apple", "banana", "blackgram", "chickpea", "coconut", "coffee",
        "cotton", "grapes", "jute", "kidneybeans", "lentil", "maize",
        "mango", "mothbeans", "mungbean", "muskmelon", "orange", "papaya",
        "pigeonpeas", "pomegranate", "rice", "watermelon",
    }
