"""
ML Model integration for priority prediction with Hybrid Intelligence.

HYBRID INTELLIGENCE APPROACH:
This module implements a hybrid ML + Rules approach for priority prediction.
Why Hybrid Intelligence?
- ML models learn patterns from training data but may miss domain-specific nuances
- Real-world systems need rule-based corrections for critical scenarios
- Financial tasks, meetings, and time-sensitive items require explicit handling
- Rules act as a "safety net" to ensure important tasks are never under-prioritized
- This approach is common in production AI systems (e.g., fraud detection, healthcare)

FLOW:
1. ML Model predicts base priority (High/Medium/Low)
2. Rule-based adjustment layer upgrades priority when needed
3. Rules NEVER downgrade - they only ensure minimum priority levels
4. Final priority is stored and displayed in UI
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    print("Warning: joblib not available. ML predictions will use fallback.")

# Load model at module level
_model = None
_model_path = Path(__file__).parent / 'priority_model.pkl'

def load_model():
    """Load the ML model once at startup."""
    global _model
    if _model is None:
        if not JOBLIB_AVAILABLE:
            print("✗ joblib not available. Cannot load ML model.")
            return None
        try:
            if not _model_path.exists():
                print(f"✗ Model file not found: {_model_path}")
                return None
            _model = joblib.load(_model_path)
            print(f"✓ ML model loaded successfully from {_model_path}")
        except Exception as e:
            print(f"✗ Error loading ML model: {e}")
            _model = None
    return _model

def apply_priority_rules(predicted_priority: str, task_text: str, hours_left: Optional[float] = None) -> str:
    """
    Apply rule-based adjustments to ML-predicted priority.
    
    This function implements a rule-based adjustment layer that upgrades priority
    when certain conditions are met. Rules are applied IN ORDER and only UPGRADE
    priority (never downgrade), ensuring important tasks are never under-prioritized.
    
    Why rules are needed:
    - ML models may not capture domain-specific importance (e.g., financial tasks)
    - Time-sensitive tasks need explicit urgency handling
    - Business rules ensure consistency and reliability
    
    Args:
        predicted_priority: Base priority from ML model ("High", "Medium", or "Low")
        task_text: Full task text (subject + description)
        hours_left: Optional hours remaining until deadline
        
    Returns:
        Adjusted priority: "High", "Medium", or "Low" (never lower than predicted)
    """
    # Start with ML prediction as base
    final_priority = predicted_priority
    task_lower = task_text.lower()
    
    # Rule 1: Financial Tasks
    # Financial obligations should never be LOW priority
    # Keywords: pay, payment, cash, settlement, rent, bill, salary
    financial_keywords = ["pay", "payment", "cash", "settlement", "rent", "bill", "salary"]
    has_financial_keyword = any(keyword in task_lower for keyword in financial_keywords)
    
    if has_financial_keyword and predicted_priority == "Low":
        final_priority = "Medium"
        print(f"  [Rule 1] Financial task detected: Upgraded Low → Medium")
    
    # Rule 2: Meetings / Professional Tasks
    # Professional meetings and discussions should not be LOW priority
    # Keywords: meeting, discussion, review, call, interview
    professional_keywords = ["meeting", "discussion", "review", "call", "interview"]
    has_professional_keyword = any(keyword in task_lower for keyword in professional_keywords)
    
    if has_professional_keyword and final_priority == "Low":
        final_priority = "Medium"
        print(f"  [Rule 2] Professional task detected: Upgraded Low → Medium")
    
    # Rule 3: Urgency Override
    # Time-sensitive tasks need priority escalation based on deadline proximity
    if hours_left is not None:
        # If deadline is within 24 hours, it's HIGH priority regardless of ML prediction
        if hours_left <= 24:
            final_priority = "High"
            print(f"  [Rule 3] Urgent deadline ({hours_left:.1f}h left): Set to High")
        # If deadline is within 72 hours and currently Low, upgrade to Medium
        elif hours_left <= 72 and final_priority == "Low":
            final_priority = "Medium"
            print(f"  [Rule 3] Near deadline ({hours_left:.1f}h left): Upgraded Low → Medium")
    
    # Legacy rule: Urgent keywords + very short deadline (kept for backward compatibility)
    urgent_keywords = ['exam', 'examination', 'interview', 'test']
    has_urgent_keyword = any(keyword in task_lower for keyword in urgent_keywords)
    
    if has_urgent_keyword and hours_left is not None and hours_left <= 12:
        final_priority = "High"
        print(f"  [Legacy Rule] Urgent keyword + short deadline: Set to High")
    
    return final_priority

def predict_priority(commitment_text: str, deadline: Optional[datetime] = None) -> str:
    """
    Predict priority using Hybrid Intelligence (ML + Rules).
    
    This is the main entry point for priority prediction. It follows this flow:
    1. Get ML model prediction as BASE priority
    2. Apply rule-based adjustments (only upgrades, never downgrades)
    3. Return final priority
    
    Args:
        commitment_text: The commitment subject/description text
        deadline: Optional deadline datetime
        
    Returns:
        Priority: "High", "Medium", or "Low"
    """
    # Calculate hours left if deadline is provided
    hours_left = None
    if deadline:
        hours_left = calculate_hours_left(deadline)
    
    # Step 1: Get ML model prediction as BASE priority
    model = load_model()
    if model is None:
        # Fallback if model not loaded - use Medium as base
        base_priority = "Medium"
        print("  [ML] Model not available, using Medium as base priority")
    else:
        try:
            # Format input as expected by model: "commitment_text deadline_<hours_left>"
            if deadline and hours_left is not None:
                model_input = f"{commitment_text} deadline_{hours_left}"
            else:
                # If no deadline, use a default value (e.g., 168 hours = 7 days)
                model_input = f"{commitment_text} deadline_168"
            
            # Predict using the ML model
            prediction = model.predict([model_input])[0]
            
            # Ensure output is one of the expected values
            if prediction in ["High", "Medium", "Low"]:
                base_priority = prediction
                print(f"  [ML] Predicted priority: {base_priority}")
            else:
                base_priority = "Medium"  # Default fallback
                print(f"  [ML] Invalid prediction, using Medium as base")
                
        except Exception as e:
            print(f"  [ML] Error in prediction: {e}, using Medium as base")
            base_priority = "Medium"  # Fallback
    
    # Step 2: Apply rule-based adjustments
    # Rules only UPGRADE priority, never downgrade
    final_priority = apply_priority_rules(base_priority, commitment_text, hours_left)
    
    if final_priority != base_priority:
        print(f"  [Hybrid] Final priority: {base_priority} → {final_priority} (upgraded by rules)")
    else:
        print(f"  [Hybrid] Final priority: {final_priority} (no rule adjustments)")
    
    return final_priority

def calculate_hours_left(deadline: datetime) -> float:
    """
    Calculate hours remaining until deadline.
    
    Args:
        deadline: Deadline datetime
        
    Returns:
        Hours remaining (can be negative if deadline passed)
    """
    now = datetime.now()
    time_diff = deadline - now
    hours_left = time_diff.total_seconds() / 3600.0
    return hours_left
