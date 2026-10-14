"""Pytest configuration: make the project importable and isolate the test DB."""

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Use a dedicated database file for tests so the real data/app.db is untouched.
os.environ.setdefault(
    "APP_DB_PATH", os.path.join(tempfile.gettempdir(), "smart_agriculture_test.db")
)
