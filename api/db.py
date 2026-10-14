"""SQLite persistence layer (stdlib only — no external database dependency).

Stores prediction history and user accounts. The database file lives at
APP_DB_PATH (default: data/app.db) and is created on first use.

Connections are created per-operation (short-lived) so the module is safe to
call from FastAPI's thread pool without sharing a single connection across
threads.
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from api.config import get_db_path

_init_lock = threading.Lock()
_initialized_for: Optional[str] = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    input_json TEXT NOT NULL,
    crop TEXT NOT NULL,
    confidence REAL,
    top_json TEXT NOT NULL DEFAULT '[]',
    warnings_json TEXT NOT NULL DEFAULT '[]',
    user_id INTEGER
);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_crop ON predictions(crop);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    farm_name TEXT DEFAULT '',
    location TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def get_conn():
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not exist (idempotent)."""
    global _initialized_for
    path = str(get_db_path())
    with _init_lock:
        if _initialized_for == path:
            return
        with get_conn() as conn:
            conn.executescript(_SCHEMA)
        _initialized_for = path


def reset_init_cache() -> None:
    """Allow tests that switch APP_DB_PATH to re-run init_db."""
    global _initialized_for
    with _init_lock:
        _initialized_for = None


# --------------------------------------------------------------------------- #
# Predictions (history)
# --------------------------------------------------------------------------- #

def record_prediction(
    inputs: dict,
    crop: str,
    confidence: Optional[float],
    top_predictions: list,
    warnings: list,
    user_id: Optional[int] = None,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO predictions "
            "(created_at, input_json, crop, confidence, top_json, warnings_json, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                _utc_now(),
                json.dumps(inputs),
                str(crop),
                confidence,
                json.dumps(top_predictions),
                json.dumps(warnings),
                user_id,
            ),
        )
        return int(cur.lastrowid)


def list_predictions(limit: int = 50, user_id: Optional[int] = None) -> list:
    limit = max(1, min(int(limit), 500))
    query = (
        "SELECT id, created_at, input_json, crop, confidence, top_json, warnings_json "
        "FROM predictions"
    )
    params: tuple = ()
    if user_id is not None:
        query += " WHERE user_id = ?"
        params = (user_id,)
    query += " ORDER BY id DESC LIMIT ?"
    params = params + (limit,)
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    items = []
    for row in rows:
        items.append(
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "inputs": json.loads(row["input_json"]),
                "crop": row["crop"],
                "confidence": row["confidence"],
                "top_predictions": json.loads(row["top_json"]),
                "warnings": json.loads(row["warnings_json"]),
            }
        )
    return items


def count_predictions(user_id: Optional[int] = None) -> int:
    with get_conn() as conn:
        if user_id is None:
            row = conn.execute("SELECT COUNT(*) AS c FROM predictions").fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM predictions WHERE user_id = ?", (user_id,)
            ).fetchone()
    return int(row["c"])


def crop_frequency(limit: int = 10) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT crop, COUNT(*) AS count FROM predictions "
            "GROUP BY crop ORDER BY count DESC, crop ASC LIMIT ?",
            (max(1, min(int(limit), 50)),),
        ).fetchall()
    return [{"crop": row["crop"], "count": row["count"]} for row in rows]


def recent_activity(limit: int = 10) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, created_at, crop, confidence FROM predictions "
            "ORDER BY id DESC LIMIT ?",
            (max(1, min(int(limit), 100)),),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "crop": row["crop"],
            "confidence": row["confidence"],
        }
        for row in rows
    ]


def daily_prediction_counts(days: int = 7) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count "
            "FROM predictions GROUP BY day ORDER BY day DESC LIMIT ?",
            (max(1, min(int(days), 90)),),
        ).fetchall()
    return [{"day": row["day"], "count": row["count"]} for row in rows]


def clear_predictions(user_id: Optional[int] = None) -> int:
    with get_conn() as conn:
        if user_id is None:
            cur = conn.execute("DELETE FROM predictions")
        else:
            cur = conn.execute("DELETE FROM predictions WHERE user_id = ?", (user_id,))
    return int(cur.rowcount)


# --------------------------------------------------------------------------- #
# Users (auth + basic farmer profile)
# --------------------------------------------------------------------------- #

def create_user(username: str, password_hash: str) -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, _utc_now()),
        )
        user_id = int(cur.lastrowid)
    return {"id": user_id, "username": username, "farm_name": "", "location": ""}


def get_user_by_username(username: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, farm_name, location, created_at "
            "FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def get_user_by_id(user_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, farm_name, location, created_at "
            "FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def update_profile(user_id: int, farm_name: str, location: str) -> Optional[dict]:
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET farm_name = ?, location = ? WHERE id = ?",
            (farm_name, location, user_id),
        )
        row = conn.execute(
            "SELECT id, username, farm_name, location, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def count_users() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
    return int(row["c"])


def db_size_bytes() -> int:
    path = get_db_path()
    return path.stat().st_size if path.exists() else 0
