"""
Model Evaluation Module for Smart Agriculture Prediction System.

Provides metrics calculation and reporting functions for multiclass classification:
- Accuracy
- Macro Precision
- Macro Recall
- Macro F1-Score
- Detailed Classification Report
"""

from typing import Dict, Any
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report


def evaluate_model(y_true: pd.Series, y_pred: Any) -> Dict[str, float]:
    """Calculate key multiclass evaluation metrics."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def format_metrics_table(results: Dict[str, Dict[str, float]]) -> str:
    """Format comparison results into a clean markdown/text table."""
    headers = ["Model", "Accuracy", "Macro Precision", "Macro Recall", "Macro F1-Score"]
    rows = []
    for model_name, metrics in results.items():
        rows.append([
            model_name,
            f"{metrics['accuracy']:.4f}",
            f"{metrics['precision_macro']:.4f}",
            f"{metrics['recall_macro']:.4f}",
            f"{metrics['f1_macro']:.4f}",
        ])
    
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))
    
    line = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    header_str = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, col_widths)) + " |"
    
    row_strs = []
    for row in rows:
        row_strs.append("| " + " | ".join(val.ljust(w) for val, w in zip(row, col_widths)) + " |")
        
    table = "\n".join([line, header_str, line] + row_strs + [line])
    return table


def generate_classification_report(y_true: pd.Series, y_pred: Any) -> str:
    """Return detailed scikit-learn classification report."""
    return classification_report(y_true, y_pred, zero_division=0)
