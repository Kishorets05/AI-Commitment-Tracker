"""
ML Model integration for priority prediction with Hybrid Intelligence.

This module implements a Hybrid AI approach:
- ML model provides a base priority
- Rule-based logic upgrades priority for critical cases
- Rules NEVER downgrade priority (safety guarantee)
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

# --------------------------------------------------
# Configuration
# --------------------------------------------------
DEBUG = False  # Set True only for local debugging

# --------------------------------------------------
# Safe imports
# --------------------------------------------------
try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False

# --------------------------------------------------
# Model loading (absolute-safe path)
# --------------------------------------------------
_MODEL = None
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "priority_model.pkl"


def _log(message: str):
    """Internal logger (controlled by DEBUG flag)."""
    if DEBUG:
        print(message)


def load_model():
    """Load ML model once at application startup."""
    global _MODEL

    if _MODEL is not None:
        return _MODEL

    if not JOBLIB_AVAILABLE:
        _log("[ML] joblib not available")
        return None

    if not MODEL_PATH.exists():
        _log(f"[ML] Model file not found: {MODEL_PATH}")
        return None

    try:
        _MODEL = joblib.load(MODEL_PATH)
        _log(f"[ML] Model loaded from {MODEL_PATH}")
    except Exception as e:
        _log(f"[ML] Failed to load model: {e}")
        _MODEL = None

    return _MODEL


# --------------------------------------------------
# Utility
# --------------------------------------------------
def calculate_hours_left(deadline: datetime) -> float:
    """Calculate remaining hours until deadline."""
    delta = deadline - datetime.now()
    return delta.total_seconds() / 3600.0


# --------------------------------------------------
# Rule-based intelligence layer
# --------------------------------------------------
def apply_priority_rules(
    predicted_priority: str,
    task_text: str,
    hours_left: Optional[float] = None
) -> str:
    """
    Upgrade priority using rule-based intelligence.
    Rules NEVER downgrade priority.
    """

    final_priority = predicted_priority
    text = task_text.lower().strip()

    # Rule 1: Financial tasks → never LOW
    financial_keywords = [
        "pay", "payment", "cash", "settlement", "rent", "bill", "salary"
    ]
    if any(k in text for k in financial_keywords) and final_priority == "Low":
        final_priority = "Medium"

    # Rule 2: Professional / meetings → never LOW
    professional_keywords = [
        "meeting", "discussion", "review", "call", "interview"
    ]
    if any(k in text for k in professional_keywords) and final_priority == "Low":
        final_priority = "Medium"

    # Rule 3: Time-based escalation
    if hours_left is not None:
        if hours_left <= 24:
            final_priority = "High"
        elif hours_left <= 72 and final_priority == "Low":
            final_priority = "Medium"

    # Rule 4: Critical keywords + short deadline
    urgent_keywords = ["exam", "examination", "test", "interview"]
    if (
        any(k in text for k in urgent_keywords)
        and hours_left is not None
        and hours_left <= 12
    ):
        final_priority = "High"

    return final_priority


# --------------------------------------------------
# Main prediction function
# --------------------------------------------------
def predict_priority_with_source(
    commitment_text: str,
    deadline: Optional[datetime] = None
) -> tuple:
    """
    Predict priority using Hybrid Intelligence (ML + Rules) and return (priority, source).
    """
    hours_left = None
    if deadline:
        hours_left = calculate_hours_left(deadline)
        hours_left = max(hours_left, 0)  # avoid negative noise

    model = load_model()

    # Step 1: ML base prediction
    if model is None:
        base_priority = "Medium"
    else:
        try:
            if hours_left is not None:
                model_input = f"{commitment_text} deadline_{int(hours_left)}"
            else:
                model_input = f"{commitment_text} deadline_168"  # default 7 days

            prediction = model.predict([model_input])[0]
            base_priority = prediction if prediction in {"High", "Medium", "Low"} else "Medium"
        except Exception:
            base_priority = "Medium"

    # Step 2: Rule-based upgrade
    final_priority = apply_priority_rules(base_priority, commitment_text, hours_left)

    if final_priority != base_priority:
        source = "Rule"
    else:
        source = "ML"

    return final_priority, source


def predict_priority(
    commitment_text: str,
    deadline: Optional[datetime] = None
) -> str:
    """
    Predict priority using Hybrid Intelligence (ML + Rules).
    """
    priority, _ = predict_priority_with_source(commitment_text, deadline)
    return priority
