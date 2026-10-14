"""Fast smoke test for the Smart Agriculture API (also usable via pytest)."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault(
    "APP_DB_PATH", os.path.join(ROOT, "data", "test_app.db")
)

from fastapi.testclient import TestClient

from api.main import app


PAYLOAD = {
    "N": 90, "P": 42, "K": 43, "temperature": 20.87,
    "humidity": 82, "ph": 6.5, "rainfall": 202.93,
}


def test_system_endpoints():
    c = TestClient(app)
    r = c.get("/")
    assert r.status_code == 200 and "message" in r.json()
    r = c.get("/health")
    assert r.status_code == 200 and "model_ready" in r.json()


def test_predict_extended():
    c = TestClient(app)
    r = c.post("/predict", json=PAYLOAD)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["recommended_crop"] == "rice"
    assert isinstance(body["confidence"], float)
    assert len(body["top_predictions"]) == 3
    assert body["crop_info"]["crop"] == "rice"
    assert body["history_id"] is not None


def test_predict_validation():
    c = TestClient(app)
    assert c.post("/predict", json={}).status_code == 422
    bad = {**PAYLOAD, "N": "abc"}
    assert c.post("/predict", json=bad).status_code == 422


def test_history():
    c = TestClient(app)
    c.post("/predict", json=PAYLOAD)
    r = c.get("/api/history")
    assert r.status_code == 200 and r.json()["total"] >= 1


def test_assistant():
    c = TestClient(app)
    r = c.post("/api/assistant", json={"question": "How to manage soil pH?", "language": "en"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "knowledge_base"
    assert "en" in body["answer"] and "te" in body["answer"]


def test_weather_unconfigured():
    c = TestClient(app)
    # Force the unconfigured state regardless of the shell environment so the
    # test is deterministic and never triggers a live provider call.
    saved_key = os.environ.pop("WEATHER_API_KEY", None)
    try:
        r = c.get("/api/weather", params={"location": "Hyderabad"})
        assert r.status_code == 200 and r.json()["configured"] is False
    finally:
        if saved_key is not None:
            os.environ["WEATHER_API_KEY"] = saved_key
    r = c.get("/api/weather", params={"location": "a!@#$"})
    assert r.status_code == 422


def test_recommendations():
    c = TestClient(app)
    r = c.post("/api/recommendations", json=PAYLOAD)
    assert r.status_code == 200 and len(r.json()["recommendations"]) >= 4


def test_admin_guards():
    c = TestClient(app)
    import os

    os.environ.pop("ADMIN_TOKEN", None)
    assert c.get("/api/admin/stats").status_code == 503
    os.environ["ADMIN_TOKEN"] = "smoke-test-token"
    try:
        assert c.get("/api/admin/stats").status_code == 401
        r = c.get("/api/admin/stats", headers={"X-Admin-Token": "smoke-test-token"})
        assert r.status_code == 200 and r.json()["predictions"]["total"] >= 1
    finally:
        os.environ.pop("ADMIN_TOKEN", None)


def main():
    tests = [
        test_system_endpoints, test_predict_extended, test_predict_validation,
        test_history, test_assistant, test_weather_unconfigured,
        test_recommendations, test_admin_guards,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {t.__name__}: {exc}")
    print("ALL PASS" if failed == 0 else f"{failed} FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
