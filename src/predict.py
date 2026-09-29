"""
Standalone Prediction Module for Smart Agriculture Prediction System.

Loads the trained crop recommendation model and exposes a clean prediction
function with strict input validation.
"""

from pathlib import Path
from typing import Union, Optional
import joblib
import numpy as np
import pandas as pd

FEATURE_NAMES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "crop_recommendation_model.pkl"

# Global model cache to avoid repeated disk I/O
_CACHED_MODEL = None


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


if __name__ == "__main__":
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
