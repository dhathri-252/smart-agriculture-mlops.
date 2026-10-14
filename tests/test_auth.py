"""Auth flow tests: register, login, tokens, profile, history scoping."""

import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_DB_PATH", os.path.join(ROOT, "data", "test_app.db"))

from fastapi.testclient import TestClient

from api.main import app

PAYLOAD = {
    "N": 90, "P": 42, "K": 43, "temperature": 20.87,
    "humidity": 82, "ph": 6.5, "rainfall": 202.93,
}


def _unique_username() -> str:
    return f"farmer_{uuid.uuid4().hex[:10]}"


def test_register_login_me_flow():
    c = TestClient(app)
    username = _unique_username()
    r = c.post("/api/auth/register", json={
        "username": username, "password": "securepass123",
        "farm_name": "Green Farm", "location": "Guntur",
    })
    assert r.status_code == 201, r.text
    token = r.json()["token"]
    assert r.json()["user"]["username"] == username
    assert "password" not in str(r.json()).lower() or "password" not in r.json()["user"]

    # duplicate username -> 409
    r2 = c.post("/api/auth/register", json={
        "username": username, "password": "securepass123"})
    assert r2.status_code == 409

    # wrong password -> 401
    r2 = c.post("/api/auth/login", json={"username": username, "password": "wrong-pass"})
    assert r2.status_code == 401

    # correct login -> token works
    r2 = c.post("/api/auth/login", json={"username": username, "password": "securepass123"})
    assert r2.status_code == 200
    token = r2.json()["token"]
    r3 = c.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200 and r3.json()["username"] == username

    # anonymous / invalid token -> 401
    assert c.get("/api/auth/me").status_code == 401
    assert c.get(
        "/api/auth/me", headers={"Authorization": "Bearer bogus.token.here"}
    ).status_code == 401

    # profile update
    r4 = c.put("/api/auth/profile", json={"farm_name": "New Farm", "location": "Vijayawada"},
               headers={"Authorization": f"Bearer {token}"})
    assert r4.status_code == 200 and r4.json()["farm_name"] == "New Farm"


def test_register_validation():
    c = TestClient(app)
    # short password -> 422
    r = c.post("/api/auth/register", json={"username": "abc", "password": "short"})
    assert r.status_code == 422
    # invalid username characters -> 422
    r = c.post("/api/auth/register", json={"username": "bad user!", "password": "securepass123"})
    assert r.status_code == 422


def test_history_scoped_to_user():
    c = TestClient(app)
    username = _unique_username()
    r = c.post("/api/auth/register", json={"username": username, "password": "securepass123"})
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # anonymous personal history -> 401
    assert c.get("/api/history", params={"mine": True}).status_code == 401
    # logged-in personal history -> 200
    r2 = c.get("/api/history", params={"mine": True}, headers=headers)
    assert r2.status_code == 200 and r2.json()["total"] == 0

    # a prediction made while logged in appears in personal history
    c.post("/predict", json=PAYLOAD, headers=headers)
    r3 = c.get("/api/history", params={"mine": True}, headers=headers)
    assert r3.status_code == 200 and r3.json()["total"] >= 1

    # clearing personal history
    r4 = c.delete("/api/history", params={"mine": True}, headers=headers)
    assert r4.status_code == 200 and r4.json()["deleted"] >= 1
    r5 = c.get("/api/history", params={"mine": True}, headers=headers)
    assert r5.json()["total"] == 0
