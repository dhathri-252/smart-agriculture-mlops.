"""
Data Preprocessing Pipeline for Smart Agriculture Prediction System.

This module loads the raw crop recommendation dataset, validates data integrity,
separates features and target, and creates a stratified 80/20 train/test split.
Processed data splits are saved to data/processed/.
"""

from pathlib import Path
from typing import Tuple
import pandas as pd
from sklearn.model_selection import train_test_split

# Expected schema
FEATURE_COLUMNS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET_COLUMN = "label"
ALL_COLUMNS = FEATURE_COLUMNS + [TARGET_COLUMN]


def load_raw_data(data_path: Path) -> pd.DataFrame:
    """Load raw dataset from CSV file."""
    if not data_path.exists():
        raise FileNotFoundError(f"Raw data file not found at: {data_path}")
    
    df = pd.read_csv(data_path)
    return df


def validate_data(df: pd.DataFrame) -> None:
    """Validate data integrity: required columns, missing values, duplicates."""
    # Validate columns
    missing_cols = [col for col in ALL_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")

    # Validate missing values
    null_counts = df[ALL_COLUMNS].isnull().sum()
    if null_counts.any():
        raise ValueError(f"Dataset contains null values:\n{null_counts[null_counts > 0]}")

    # Check duplicate rows
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        print(f"[WARNING] Found {duplicate_count} duplicate rows in dataset.")
    else:
        print("[INFO] Data validation passed: 0 duplicate rows found.")


def split_data(
    df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Separate features and target, then perform stratified train/test split."""
    X = df[FEATURE_COLUMNS]
    y = df[[TARGET_COLUMN]]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y[TARGET_COLUMN],
    )

    return X_train, X_test, y_train, y_test


def save_processed_data(
    output_dir: Path,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.DataFrame,
    y_test: pd.DataFrame,
) -> None:
    """Save processed train and test splits into CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    X_train.to_csv(output_dir / "X_train.csv", index=False)
    X_test.to_csv(output_dir / "X_test.csv", index=False)
    y_train.to_csv(output_dir / "y_train.csv", index=False)
    y_test.to_csv(output_dir / "y_test.csv", index=False)

    print(f"[INFO] Processed datasets successfully saved to: {output_dir}")


def run_preprocessing(
    raw_data_path: str = "data/raw/crop_recommendation.csv",
    output_dir_path: str = "data/processed",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Execute complete data preprocessing and split pipeline."""
    # Resolve project root relative to this file
    project_root = Path(__file__).resolve().parent.parent
    raw_path = (project_root / raw_data_path).resolve()
    processed_dir = (project_root / output_dir_path).resolve()

    print("=" * 60)
    print("STARTING DATA PREPROCESSING & STRATIFIED SPLIT")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Loading raw data from: {raw_data_path}")

    # 1. Load data
    df = load_raw_data(raw_path)
    print(f"Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")

    # 2. Validate data
    validate_data(df)

    # 3. Stratified split
    X_train, X_test, y_train, y_test = split_data(df, test_size=0.2, random_state=42)

    # 4. Display distribution and verification
    print("\n--- Split Summary ---")
    print(f"Training samples: {len(X_train)} (80%)")
    print(f"Testing samples:  {len(X_test)} (20%)")
    print(f"Feature count:    {X_train.shape[1]} features {FEATURE_COLUMNS}")
    print(f"Unique classes:   {y_train[TARGET_COLUMN].nunique()} classes")

    print("\n--- Class Counts in Training Set (Stratified) ---")
    train_counts = y_train[TARGET_COLUMN].value_counts()
    print(train_counts.to_string())

    print("\n--- Class Counts in Testing Set (Stratified) ---")
    test_counts = y_test[TARGET_COLUMN].value_counts()
    print(test_counts.to_string())

    # 5. Save splits
    save_processed_data(processed_dir, X_train, X_test, y_train, y_test)

    print("=" * 60)
    print("PREPROCESSING PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)

    return X_train, X_test, y_train, y_test


if __name__ == "__main__":
    run_preprocessing()
