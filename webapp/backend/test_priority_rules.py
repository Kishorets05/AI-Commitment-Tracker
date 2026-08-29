"""
Test script to verify Hybrid Intelligence priority prediction.

This script tests the rule-based adjustments to ensure:
1. Financial tasks are upgraded from Low to Medium
2. Professional tasks are upgraded from Low to Medium
3. Urgency rules properly escalate priority based on time
4. Rules never downgrade priority
"""

from datetime import datetime, timedelta
from priority_predictor import predict_priority, apply_priority_rules

def test_financial_tasks():
    """Test that financial tasks are upgraded from Low to Medium."""
    print("\n=== Testing Financial Tasks ===")
    
    test_cases = [
        ("Pay rent for apartment", "Low", "Medium"),
        ("Payment due for credit card", "Low", "Medium"),
        ("Cash settlement with vendor", "Low", "Medium"),
        ("Salary processing", "Low", "Medium"),
        ("Bill payment reminder", "Low", "Medium"),
    ]
    
    for task_text, ml_prediction, expected in test_cases:
        result = apply_priority_rules(ml_prediction, task_text, None)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{task_text}': {ml_prediction} → {result} (expected: {expected})")

def test_professional_tasks():
    """Test that professional tasks are upgraded from Low to Medium."""
    print("\n=== Testing Professional Tasks ===")
    
    test_cases = [
        ("Team meeting tomorrow", "Low", "Medium"),
        ("Discussion with manager", "Low", "Medium"),
        ("Code review session", "Low", "Medium"),
        ("Client call scheduled", "Low", "Medium"),
        ("Job interview preparation", "Low", "Medium"),
    ]
    
    for task_text, ml_prediction, expected in test_cases:
        result = apply_priority_rules(ml_prediction, task_text, None)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{task_text}': {ml_prediction} → {result} (expected: {expected})")

def test_urgency_rules():
    """Test that urgency rules properly escalate priority."""
    print("\n=== Testing Urgency Rules ===")
    
    # Test: <= 24 hours should be High
    deadline_24h = datetime.now() + timedelta(hours=20)
    hours_24 = (deadline_24h - datetime.now()).total_seconds() / 3600
    
    result_24h = apply_priority_rules("Medium", "Any task", hours_24)
    print(f"{'✓' if result_24h == 'High' else '✗'} 24h deadline: Medium → {result_24h} (expected: High)")
    
    # Test: <= 72 hours and Low should be Medium
    deadline_72h = datetime.now() + timedelta(hours=60)
    hours_72 = (deadline_72h - datetime.now()).total_seconds() / 3600
    
    result_72h = apply_priority_rules("Low", "Any task", hours_72)
    print(f"{'✓' if result_72h == 'Medium' else '✗'} 72h deadline (Low): Low → {result_72h} (expected: Medium)")
    
    # Test: Rules never downgrade
    result_no_downgrade = apply_priority_rules("High", "Any task", hours_72)
    print(f"{'✓' if result_no_downgrade == 'High' else '✗'} No downgrade: High → {result_no_downgrade} (expected: High)")

def test_combined_rules():
    """Test that multiple rules can apply together."""
    print("\n=== Testing Combined Rules ===")
    
    # Financial + Urgent deadline
    deadline_urgent = datetime.now() + timedelta(hours=18)
    hours_urgent = (deadline_urgent - datetime.now()).total_seconds() / 3600
    
    result = apply_priority_rules("Low", "Pay rent immediately", hours_urgent)
    print(f"{'✓' if result == 'High' else '✗'} Financial + Urgent: Low → {result} (expected: High)")
    
    # Professional + Near deadline
    deadline_near = datetime.now() + timedelta(hours=50)
    hours_near = (deadline_near - datetime.now()).total_seconds() / 3600
    
    result = apply_priority_rules("Low", "Team meeting scheduled", hours_near)
    print(f"{'✓' if result == 'Medium' else '✗'} Professional + Near deadline: Low → {result} (expected: Medium)")

if __name__ == "__main__":
    print("=" * 60)
    print("HYBRID INTELLIGENCE PRIORITY PREDICTION - TEST SUITE")
    print("=" * 60)
    
    test_financial_tasks()
    test_professional_tasks()
    test_urgency_rules()
    test_combined_rules()
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)


