"""
Standalone Prediction Module for Smart Agriculture Prediction System.

Loads the trained crop recommendation model and exposes a clean prediction
function with strict input validation.
"""

from pathlib import Path
from typing import Union, Optional
from datetime import datetime
import joblib
import numpy as np
import pandas as pd

FEATURE_NAMES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "crop_recommendation_model.pkl"
TRAINING_STATS_PATH = Path(__file__).resolve().parent.parent / "models" / "training_stats.json"

# Global model cache to avoid repeated disk I/O
_CACHED_MODEL = None
_CACHED_STATS = None



def load_model(model_path: Optional[Union[str, Path]] = None):
    """Load and cache the trained classification model."""
    global _CACHED_MODEL
    if _CACHED_MODEL is not None and model_path is None:
        return _CACHED_MODEL

    path = Path(model_path) if model_path else MODEL_PATH
    if not path.exists():
        raise FileNotFoundError(f"Trained model not found at: {path}")

    _CACHED_MODEL = joblib.load(path)
    return _CACHED_MODEL


def validate_input(inputs: dict) -> None:
    """Validate that all features are present, non-null, and numeric."""
    for feature_name, value in inputs.items():
        if value is None:
            raise ValueError(f"Feature '{feature_name}' cannot be None or missing.")

        # In Python, bool is a subclass of int, so explicitly exclude booleans
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"Feature '{feature_name}' must be numeric (int or float). Got type: {type(value).__name__} (value: {value})"
            )

        if np.isnan(value):
            raise ValueError(f"Feature '{feature_name}' cannot be NaN.")


def predict_crop(
    N: Union[int, float],
    P: Union[int, float],
    K: Union[int, float],
    temperature: Union[int, float],
    humidity: Union[int, float],
    ph: Union[int, float],
    rainfall: Union[int, float],
    model_path: Optional[Union[str, Path]] = None,
) -> str:
    """
    Predict the most suitable crop given soil and environmental conditions.

    Parameters:
        N: Nitrogen content in soil (numeric)
        P: Phosphorus content in soil (numeric)
        K: Potassium content in soil (numeric)
        temperature: Temperature in degrees Celsius (numeric)
        humidity: Relative humidity percentage (numeric)
        ph: Soil pH value (numeric)
        rainfall: Rainfall in mm (numeric)
        model_path: Optional path to serialized model file

    Returns:
        str: Recommended crop label
    """
    raw_inputs = {
        "N": N,
        "P": P,
        "K": K,
        "temperature": temperature,
        "humidity": humidity,
        "ph": ph,
        "rainfall": rainfall,
    }

    # Validate inputs
    validate_input(raw_inputs)

    # Format into pandas DataFrame with exact expected schema
    input_df = pd.DataFrame([raw_inputs], columns=FEATURE_NAMES)

    # Load model and predict
    model = load_model(model_path)
    prediction = model.predict(input_df)[0]

    return str(prediction)


def load_training_stats() -> Optional[dict]:
    """Load dataset-derived feature ranges (models/training_stats.json), if present."""
    global _CACHED_STATS
    if _CACHED_STATS is not None:
        return _CACHED_STATS
    if not TRAINING_STATS_PATH.exists():
        return None
    import json

    with open(TRAINING_STATS_PATH, "r", encoding="utf-8") as fh:
        _CACHED_STATS = json.load(fh)
    return _CACHED_STATS


def input_range_warnings(inputs: dict) -> list:
    """Flag inputs that fall outside the observed training-data ranges.

    This is a lightweight data-drift / out-of-distribution check. It never
    blocks a prediction — it only informs the user that the model is being
    asked about conditions it has not seen during training.
    """
    stats = load_training_stats()
    if not stats:
        return []
    warnings = []
    for name, value in inputs.items():
        bounds = stats.get("features", {}).get(name)
        if not bounds:
            continue
        lo, hi = bounds.get("min"), bounds.get("max")
        if lo is None or hi is None:
            continue
        if value < lo:
            warnings.append(
                f"'{name}' ({value}) is below the training-data range ({lo}–{hi})."
            )
        elif value > hi:
            warnings.append(
                f"'{name}' ({value}) is above the training-data range ({lo}–{hi})."
            )
    if warnings:
        warnings.append(
            "The recommendation may be less reliable for conditions outside the training data."
        )
    return warnings


def get_model_info() -> dict:
    """Non-sensitive metadata about the loaded model (used by health/admin APIs)."""
    model = load_model()
    info = {
        "model_type": type(model).__name__,
        "n_features": int(getattr(model, "n_features_in_", len(FEATURE_NAMES))),
        "feature_names": list(FEATURE_NAMES),
        "classes": [str(c) for c in getattr(model, "classes_", [])],
        "probabilities_supported": hasattr(model, "predict_proba"),
        "model_file": str(MODEL_PATH.name),
    }
    if MODEL_PATH.exists():
        stat = MODEL_PATH.stat()
        info["model_file_bytes"] = stat.st_size
        info["model_trained_at"] = datetime.fromtimestamp(stat.st_mtime).isoformat(
            timespec="seconds"
        )
    return info


def predict_crop_detailed(
    N: Union[int, float],
    P: Union[int, float],
    K: Union[int, float],
    temperature: Union[int, float],
    humidity: Union[int, float],
    ph: Union[int, float],
    rainfall: Union[int, float],
    top_n: int = 3,
    model_path: Optional[Union[str, Path]] = None,
) -> dict:
    """Predict crops with real model probabilities (no fabricated confidence).

    Returns a dict with the recommended crop, the model's own probability as
    confidence, the top-N alternatives, and any input-range warnings.
    If the model does not expose ``predict_proba``, confidence is ``None``
    rather than an invented number.
    """
    raw_inputs = {
        "N": N,
        "P": P,
        "K": K,
        "temperature": temperature,
        "humidity": humidity,
        "ph": ph,
        "rainfall": rainfall,
    }
    validate_input(raw_inputs)
    input_df = pd.DataFrame([raw_inputs], columns=FEATURE_NAMES)
    model = load_model(model_path)

    result = {
        "recommended_crop": "",
        "confidence": None,
        "top_predictions": [],
        "probabilities_available": bool(hasattr(model, "predict_proba")),
        "input_warnings": input_range_warnings(raw_inputs),
    }

    if result["probabilities_available"]:
        proba = model.predict_proba(input_df)[0]
        classes = [str(c) for c in model.classes_]
        ranked = sorted(zip(classes, proba), key=lambda pair: pair[1], reverse=True)
        top = ranked[: max(1, top_n)]
        result["recommended_crop"] = top[0][0]
        result["confidence"] = round(float(top[0][1]), 4)
        result["top_predictions"] = [
            {"crop": crop, "probability": round(float(prob), 4)}
            for crop, prob in top
        ]
    else:
        prediction = str(model.predict(input_df)[0])
        result["recommended_crop"] = prediction
        result["top_predictions"] = [{"crop": prediction, "probability": None}]

    return result



    print("=" * 60)
    print("RUNNING PREDICTION MODULE VERIFICATION")
    print("=" * 60)

    # 1. Valid test case (Expected: 'rice')
    test_n = 90
    test_p = 42
    test_k = 43
    test_temp = 20.87
    test_humidity = 82.00
    test_ph = 6.50
    test_rainfall = 202.93

    print(
        f"Input: N={test_n}, P={test_p}, K={test_k}, "
        f"temp={test_temp}, humidity={test_humidity}, ph={test_ph}, rainfall={test_rainfall}"
    )
    predicted = predict_crop(
        N=test_n,
        P=test_p,
        K=test_k,
        temperature=test_temp,
        humidity=test_humidity,
        ph=test_ph,
        rainfall=test_rainfall,
    )
    print(f"Predicted Crop: {predicted}")
    assert predicted == "rice", f"Expected 'rice', got '{predicted}'"
    print("[SUCCESS] Valid prediction test passed (Result: rice)\n")

    # 2. Invalid input test case (Non-numeric value)
    print("Testing invalid input validation (non-numeric value)...")
    try:
        predict_crop(
            N="invalid_nitrogen",
            P=42,
            K=43,
            temperature=20.87,
            humidity=82.00,
            ph=6.50,
            rainfall=202.93,
        )
        raise AssertionError("Validation failed to raise ValueError on string input.")
    except ValueError as e:
        print(f"[SUCCESS] Caught expected ValueError: {e}\n")

    # 3. Invalid input test case (None value)
    print("Testing invalid input validation (None value)...")
    try:
        predict_crop(
            N=90,
            P=None,
            K=43,
            temperature=20.87,
            humidity=82.00,
            ph=6.50,
            rainfall=202.93,
        )
        raise AssertionError("Validation failed to raise ValueError on None input.")
    except ValueError as e:
        print(f"[SUCCESS] Caught expected ValueError: {e}\n")

    print("=" * 60)
    print("ALL PREDICTION MODULE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
