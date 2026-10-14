"""Tests for catalogue image metadata, uniqueness, and fallback behavior."""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_DB_PATH", os.path.join(ROOT, "data", "test_app.db"))

from fastapi.testclient import TestClient

from api import catalogue_service as svc
from api.catalogue_data import CROPS
from api.main import app

client = TestClient(app)

FREE_LICENSE_PREFIXES = ("CC0", "CC-BY", "CC BY", "CC-BY-SA", "CC BY-SA")


def _manifest_records():
    path = ROOT / "frontend" / "public" / "images" / "crops" / "manifest.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def test_image_status_is_only_verified_or_pending():
    r = client.get("/api/catalogue")
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert item["image_status"] in ("verified", "pending"), item["id"]
        # Verified MUST carry a URL; pending MUST NOT (no fabricated URLs).
        if item["image_status"] == "verified":
            assert item["image"], item["id"]
            assert item["image"].startswith("/images/crops/"), item["id"]
            assert item["image_attribution"], item["id"]
        else:
            assert item["image"] is None, item["id"]


def test_no_duplicate_image_files():
    r = client.get("/api/catalogue")
    urls = [x["image"] for x in r.json()["items"] if x["image"]]
    assert len(urls) == len(set(urls)), "each crop must map to a distinct photo"


def test_verified_images_have_real_attribution_and_license():
    r = client.get("/api/catalogue")
    verified = [x for x in r.json()["items"] if x["image_status"] == "verified"]
    for item in verified:
        attr = item["image_attribution"]
        assert attr.get("author"), item["id"]
        assert attr.get("source_url", "").startswith("https://commons.wikimedia.org/wiki/"), item["id"]
        lic = attr.get("license", "")
        assert any(lic.replace(" ", "").lower().startswith(p.replace(" ", "").lower()) for p in FREE_LICENSE_PREFIXES), (item["id"], lic)
    # Honest alt text in both states.
    for item in r.json()["items"]:
        assert item["alt_text"], item["id"]
        if item["image_status"] == "verified":
            assert "hotograph" in item["alt_text"], item["id"]
        else:
            assert "placeholder" in item["alt_text"].lower() or "pending" in item["alt_text"].lower(), item["id"]


def test_manifest_matches_bundled_files():
    records = _manifest_records()
    img_dir = ROOT / "frontend" / "public" / "images" / "crops"
    for rec in records:
        assert rec.get("verified") is True, rec.get("crop_id")
        assert rec.get("source_url", "").startswith("https://commons.wikimedia.org/wiki/"), rec.get("crop_id")
        assert rec.get("author") and rec.get("license"), rec.get("crop_id")
        assert (img_dir / f"{rec['crop_id']}.jpg").exists(), rec.get("crop_id")
    # Every manifest crop id must be a real stable catalogue id.
    valid_ids = {c["id"] for c in CROPS}
    for rec in records:
        assert rec["crop_id"] in valid_ids, rec["crop_id"]


def test_meta_image_coverage_adds_up():
    r = client.get("/api/catalogue/meta")
    cov = r.json()["image_coverage"]
    assert cov["verified"] + cov["pending"] == 137
    lic = r.json().get("image_licenses", {})
    assert sum(lic.values()) == cov["verified"]
