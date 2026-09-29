"""
Model Training and Selection Pipeline for Smart Agriculture Prediction System.

Loads processed datasets, trains Logistic Regression, Decision Tree, and Random Forest,
evaluates all three models on the test set, selects the best model based strictly on
measured test metrics, saves the artifact to models/crop_recommendation_model.pkl,
and runs a verification prediction test.
"""

import os
from pathlib import Path
import sys
import joblib

os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import mlflow
import mlflow.sklearn

# Add project root to sys.path to allow imports from src
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.evaluate import evaluate_model, format_metrics_table, generate_classification_report


def load_processed_data(data_dir: Path):
    """Load train and test datasets from CSV files."""
    X_train = pd.read_csv(data_dir / "X_train.csv")
    X_test = pd.read_csv(data_dir / "X_test.csv")
    y_train = pd.read_csv(data_dir / "y_train.csv")["label"]
    y_test = pd.read_csv(data_dir / "y_test.csv")["label"]
    return X_train, X_test, y_train, y_test


def train_and_evaluate_models(data_dir_path: str = "data/processed", models_dir_path: str = "models"):
    """Train candidates, compare metrics, select and persist best model."""
    root = Path(__file__).resolve().parent.parent
    data_dir = (root / data_dir_path).resolve()
    models_dir = (root / models_dir_path).resolve()
    models_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("STARTING MODEL TRAINING & EVALUATION PIPELINE")
    print("=" * 60)

    # 1. Load data
    print(f"Loading processed data from: {data_dir}")
    X_train, X_test, y_train, y_test = load_processed_data(data_dir)
    print(f"Train shape: {X_train.shape}, Test shape: {X_test.shape}")
    print(f"Input features: {list(X_train.columns)}")

    # 2. Define candidate models
    candidates = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    }

    # 3. Train and evaluate
    results = {}
    fitted_models = {}
    test_predictions = {}

    for name, model in candidates.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        metrics = evaluate_model(y_test, y_pred)
        results[name] = metrics
        fitted_models[name] = model
        test_predictions[name] = y_pred
        print(f"{name} -> Accuracy: {metrics['accuracy']:.4f}, Macro F1: {metrics['f1_macro']:.4f}")

    # 4. Print comparison table
    print("\n" + "=" * 60)
    print("MODEL COMPARISON TABLE (TEST DATASET)")
    print("=" * 60)
    table_str = format_metrics_table(results)
    print(table_str)

    # 5. Select best model based on measured Macro F1-score (and Accuracy)
    best_model_name = max(results, key=lambda k: (results[k]["f1_macro"], results[k]["accuracy"]))
    best_model = fitted_models[best_model_name]
    best_metrics = results[best_model_name]

    print("\n" + "=" * 60)
    print(f"SELECTED MODEL: {best_model_name}")
    print(f"Selection criteria: Highest Macro F1-Score ({best_metrics['f1_macro']:.4f}) and Accuracy ({best_metrics['accuracy']:.4f})")
    print("=" * 60)

    # 6. Detailed classification report for selected model
    print("\n--- Detailed Classification Report ---")
    report = generate_classification_report(y_test, test_predictions[best_model_name])
    print(report)

    # 7. Save model
    model_save_path = models_dir / "crop_recommendation_model.pkl"
    joblib.dump(best_model, model_save_path)
    print(f"[INFO] Successfully saved selected model to: {model_save_path}")

    # 8. MLflow Experiment Tracking
    print("\n" + "=" * 60)
    print("LOGGING EXPERIMENT WITH MLFLOW")
    print("=" * 60)
    mlruns_dir = (root / "mlruns").resolve()
    mlflow.set_tracking_uri(str(mlruns_dir))
    experiment_name = "Smart-Agriculture-Crop-Recommendation"
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name="RandomForest-Training-Run") as run:
        # Log parameters
        mlflow.log_param("model_type", "RandomForestClassifier")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("random_state", 42)
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("test_samples", len(X_test))

        # Log metrics
        mlflow.log_metric("accuracy", best_metrics["accuracy"])
        mlflow.log_metric("precision_macro", best_metrics["precision_macro"])
        mlflow.log_metric("recall_macro", best_metrics["recall_macro"])
        mlflow.log_metric("f1_macro", best_metrics["f1_macro"])

        # Log trained model artifact
        input_example = X_test.iloc[[0]]
        mlflow.sklearn.log_model(
            sk_model=best_model,
            artifact_path="model",
            input_example=input_example,
            skops_trusted_types=["sklearn.tree._tree.Tree"],
        )

        run_id = run.info.run_id
        print(f"[INFO] MLflow Experiment: {experiment_name}")
        print(f"[INFO] MLflow Run ID:     {run_id}")
        print(f"[INFO] MLflow Artifacts:  Logged under 'model' artifact path")

    # 9. Verification: Reload model and perform sample prediction
    print("\n" + "=" * 60)
    print("VERIFICATION & SAMPLE PREDICTION TEST")
    print("=" * 60)
    loaded_model = joblib.load(model_save_path)
    print(f"Model loaded successfully from: {model_save_path}")

    # Take first row from test set
    sample_features = X_test.iloc[[0]]
    expected_crop = y_test.iloc[0]
    predicted_crop = loaded_model.predict(sample_features)[0]

    print(f"Input features sample:\n{sample_features.to_dict(orient='records')[0]}")
    print(f"Actual Crop:    {expected_crop}")
    print(f"Predicted Crop: {predicted_crop}")
    assert predicted_crop == expected_crop, f"Prediction {predicted_crop} did not match expected {expected_crop}"
    print("[SUCCESS] Model inference verification passed!")

    return best_model_name, results


if __name__ == "__main__":
    train_and_evaluate_models()
