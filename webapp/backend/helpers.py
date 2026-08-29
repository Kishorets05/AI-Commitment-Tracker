"""
Helper functions for urgency calculations and formatting.
"""

from datetime import datetime
from typing import Optional, Dict, Any

# --------------------------------------------------
# Urgency thresholds (hours)
# --------------------------------------------------
CRITICAL_HOURS = 6
URGENT_HOURS = 24
SOON_HOURS = 72


def calculate_urgency(deadline: Optional[datetime], status: str) -> Dict[str, Any]:
    """
    Calculate urgency indicator for a commitment.

    Args:
        deadline: Deadline datetime
        status: Commitment status

    Returns:
        Dictionary with urgency level, label, hours_left, and is_urgent flag
    """

    if not deadline:
        return {
            "level": "none",
            "label": "No deadline",
            "hours_left": None,
            "is_urgent": False,
        }

    now = datetime.now()
    time_diff = deadline - now
    hours_left = time_diff.total_seconds() / 3600.0

    # --------------------------------------------------
    # Completed tasks
    # --------------------------------------------------
    if status == "Completed":
        return {
            "level": "completed",
            "label": "Completed",
            "hours_left": max(hours_left, 0),
            "is_urgent": False,
        }

    # --------------------------------------------------
    # Overdue tasks
    # --------------------------------------------------
    if status == "Overdue" or hours_left < 0:
        overdue_hours = abs(hours_left)

        if overdue_hours < URGENT_HOURS:
            label = f"⌛ {int(overdue_hours)} hour{'s' if overdue_hours != 1 else ''} overdue"
        else:
            days = int(overdue_hours / 24)
            label = f"⌛ {days} day{'s' if days != 1 else ''} overdue"

        return {
            "level": "overdue",
            "label": label,
            "hours_left": overdue_hours,
            "is_urgent": True,
        }

    # --------------------------------------------------
    # Critical urgency (<= 6 hours)
    # --------------------------------------------------
    if hours_left <= CRITICAL_HOURS:
        hours = int(hours_left)
        minutes = int((hours_left - hours) * 60)

        if hours > 0:
            label = f"⌛ {hours} hour{'s' if hours != 1 else ''} left"
        else:
            label = f"⌛ {minutes} minute{'s' if minutes != 1 else ''} left"

        return {
            "level": "critical",
            "label": label,
            "hours_left": hours_left,
            "is_urgent": True,
        }

    # --------------------------------------------------
    # Urgent (<= 24 hours)
    # --------------------------------------------------
    if hours_left <= URGENT_HOURS:
        hours = int(hours_left)
        return {
            "level": "urgent",
            "label": f"⌛ {hours} hour{'s' if hours != 1 else ''} left",
            "hours_left": hours_left,
            "is_urgent": True,
        }

    # --------------------------------------------------
    # Soon (<= 3 days)
    # --------------------------------------------------
    if hours_left <= SOON_HOURS:
        hours = int(hours_left)
        return {
            "level": "soon",
            "label": f"⌛ {hours} hours left",
            "hours_left": hours_left,
            "is_urgent": False,
        }

    # --------------------------------------------------
    # Normal
    # --------------------------------------------------
    days = int(hours_left / 24)
    if days > 0:
        label = f"⌛ {days} day{'s' if days != 1 else ''} left"
    else:
        hours = int(hours_left)
        label = f"⌛ {hours} hours left"

    return {
        "level": "normal",
        "label": label,
        "hours_left": hours_left,
        "is_urgent": False,
    }
