"""Unit tests for the ML prediction layer, crop info and security helpers."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_DB_PATH", os.path.join(ROOT, "data", "test_app.db"))

from api.security import create_token, decode_token, hash_password, verify_password
from src.crop_info import SUPPORTED_CROPS, get_crop_info
from src.predict import input_range_warnings, predict_crop, predict_crop_detailed

RICE_INPUT = dict(
    N=90, P=42, K=43, temperature=20.87, humidity=82, ph=6.5, rainfall=202.93
)


def test_original_predict_crop_still_works():
    assert predict_crop(**RICE_INPUT) == "rice"


def test_detailed_prediction_with_real_probabilities():
    result = predict_crop_detailed(**RICE_INPUT)
    assert result["recommended_crop"] == "rice"
    assert result["probabilities_available"] is True
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0
    assert len(result["top_predictions"]) == 3
    top = result["top_predictions"][0]
    assert top["crop"] == result["recommended_crop"]
    assert abs(top["probability"] - result["confidence"]) < 1e-9
    probs = [p["probability"] for p in result["top_predictions"]]
    assert probs == sorted(probs, reverse=True)


def test_out_of_range_input_warning():
    result = predict_crop_detailed(**{**RICE_INPUT, "temperature": -10})
    assert any("temperature" in w for w in result["input_warnings"])


def test_in_range_input_has_no_warning():
    result = predict_crop_detailed(**RICE_INPUT)
    assert result["input_warnings"] == []


def test_input_range_warnings_helper():
    warnings = input_range_warnings({"N": 9999})
    assert warnings, "expected warnings for N outside training range"
    assert input_range_warnings({"N": 50}) == []


def test_crop_info_complete_for_all_crops():
    assert len(SUPPORTED_CROPS) == 22
    for crop in SUPPORTED_CROPS:
        info = get_crop_info(crop)
        assert info is not None, crop
        for field in ("soil", "irrigation", "fertilizer", "cultivation", "disclaimer"):
            assert "en" in info[field] and "te" in info[field], (crop, field)
        assert set(info["ranges"]) >= {"temperature", "humidity", "rainfall", "ph", "N", "P", "K"}
    assert get_crop_info("not-a-crop") is None


def test_password_hashing_roundtrip():
    stored = hash_password("my-secret-password")
    assert "my-secret-password" not in stored
    assert verify_password("my-secret-password", stored)
    assert not verify_password("wrong-password", stored)
    assert not verify_password("my-secret-password", "garbage")
    # unique salts
    assert hash_password("my-secret-password") != stored


def test_token_sign_and_verify():
    token = create_token({"sub": 1, "username": "tester"}, secret="test-secret")
    claims = decode_token(token, secret="test-secret")
    assert claims is not None and claims["sub"] == 1
    # wrong secret / tampered token rejected
    assert decode_token(token, secret="other-secret") is None
    assert decode_token(token[:-2] + "xx", secret="test-secret") is None
    assert decode_token("not-a-token", secret="test-secret") is None
    # expired token rejected
    expired = create_token({"sub": 1}, secret="test-secret", ttl_seconds=-60)
    assert decode_token(expired, secret="test-secret") is None
