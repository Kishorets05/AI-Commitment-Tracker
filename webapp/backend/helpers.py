"""
Helper functions for urgency calculations and formatting.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict


def calculate_urgency(deadline: Optional[datetime], status: str) -> Dict[str, any]:
    """
    Calculate urgency indicator for a commitment.
    
    Args:
        deadline: Deadline datetime
        status: Commitment status
        
    Returns:
        Dictionary with urgency level, label, and hours_left
    """
    if not deadline:
        return {
            'level': 'none',
            'label': 'No deadline',
            'hours_left': None,
            'is_urgent': False
        }
    
    now = datetime.now()
    time_diff = deadline - now
    hours_left = time_diff.total_seconds() / 3600.0
    
    # If already completed or overdue status, show accordingly
    if status == 'Completed':
        return {
            'level': 'completed',
            'label': 'Completed',
            'hours_left': hours_left,
            'is_urgent': False
        }
    
    if status == 'Overdue' or hours_left < 0:
        overdue_hours = abs(hours_left)
        if overdue_hours < 24:
            return {
                'level': 'overdue',
                'label': f'⌛ {int(overdue_hours)} hours overdue',
                'hours_left': overdue_hours,
                'is_urgent': True
            }
        else:
            days = int(overdue_hours / 24)
            return {
                'level': 'overdue',
                'label': f'⌛ {days} day{"s" if days != 1 else ""} overdue',
                'hours_left': overdue_hours,
                'is_urgent': True
            }
    
    # Calculate urgency based on hours left - using hourglass format
    if hours_left <= 6:
        if hours_left > 0:
            hours = int(hours_left)
            minutes = int((hours_left - hours) * 60)
            if hours > 0:
                label = f'⌛ {hours} hour{"s" if hours != 1 else ""} left'
            else:
                label = f'⌛ {minutes} minute{"s" if minutes != 1 else ""} left'
        else:
            label = '⌛ Overdue'
        return {
            'level': 'critical',
            'label': label,
            'hours_left': hours_left,
            'is_urgent': True
        }
    elif hours_left <= 24:
        hours = int(hours_left)
        return {
            'level': 'urgent',
            'label': f'⌛ {hours} hour{"s" if hours != 1 else ""} left',
            'hours_left': hours_left,
            'is_urgent': True
        }
    elif hours_left <= 72:  # 3 days
        hours = int(hours_left)
        return {
            'level': 'soon',
            'label': f'⌛ {hours} hours left',
            'hours_left': hours_left,
            'is_urgent': False
        }
    else:
        hours = int(hours_left)
        days = int(hours_left / 24)
        if days > 0:
            return {
                'level': 'normal',
                'label': f'⌛ {days} day{"s" if days != 1 else ""} left',
                'hours_left': hours_left,
                'is_urgent': False
            }
        else:
            return {
                'level': 'normal',
                'label': f'⌛ {hours} hours left',
                'hours_left': hours_left,
                'is_urgent': False
            }

