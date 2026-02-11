"""
Date and Time Utilities

Provides date handling helpers for:
- Safe datetime parsing
- Date formatting with British timezone support
- Date grouping for dashboard

Author: AutoAssistGroup Development Team
"""

from datetime import datetime, timedelta
import pytz

# British timezone (handles BST/GMT automatically)
BRITISH_TZ = pytz.timezone('Europe/London')


def safe_datetime_parse(value):
    """
    Safely parse datetime from either datetime object or string.
    
    Args:
        value: datetime object, ISO string, or None
        
    Returns:
        datetime object or None if parsing fails
    """
    if value is None:
        return None
    
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, str):
        # Try common datetime formats
        formats = [
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    
    return None


def convert_to_british_time(dt):
    """
    Convert a datetime to British timezone (Europe/London).
    
    Handles both naive and timezone-aware datetimes.
    Automatically adjusts for BST/GMT.
    
    Args:
        dt: datetime object
        
    Returns:
        datetime object in British timezone
    """
    if dt is None:
        return None
    
    try:
        # If datetime is naive (no timezone), assume it's UTC
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        
        # Convert to British timezone
        return dt.astimezone(BRITISH_TZ)
    except Exception:
        return dt


def safe_date_format(value, format_str="%b %d, %I:%M %p"):
    """
    Safely format datetime to string in British timezone.
    
    Args:
        value: datetime object or parseable string
        format_str: Output format string
        
    Returns:
        Formatted date string in British time or empty string if formatting fails
    """
    try:
        dt = safe_datetime_parse(value)
        if dt:
            # Convert to British timezone before formatting
            british_dt = convert_to_british_time(dt)
            if british_dt:
                return british_dt.strftime(format_str)
            return dt.strftime(format_str)
        return ""
    except Exception:
        return ""


def group_tickets_by_date(tickets):
    """
    Group tickets by date categories (Today, Yesterday, This Week, etc.) in British timezone.
    
    Args:
        tickets: List of ticket dictionaries with 'created_at' field
        
    Returns:
        dict: Tickets grouped by date category
    """
    if not tickets:
        return {}
    
    # Get current time in British timezone
    now_british = datetime.now(BRITISH_TZ)
    today = now_british.date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    groups = {
        'Today': [],
        'Yesterday': [],
        'This Week': [],
        'This Month': [],
        'Older': []
    }
    
    for ticket in tickets:
        created_at = ticket.get('created_at')
        dt = safe_datetime_parse(created_at)
        
        if not dt:
            groups['Older'].append(ticket)
            continue
        
        # Convert to British timezone before comparing dates
        british_dt = convert_to_british_time(dt)
        if british_dt:
            ticket_date = british_dt.date()
        else:
            ticket_date = dt.date()
        
        if ticket_date == today:
            groups['Today'].append(ticket)
        elif ticket_date == yesterday:
            groups['Yesterday'].append(ticket)
        elif ticket_date > week_ago:
            groups['This Week'].append(ticket)
        elif ticket_date > month_ago:
            groups['This Month'].append(ticket)
        else:
            groups['Older'].append(ticket)
    
    # Remove empty groups
    return {k: v for k, v in groups.items() if v}


def get_relative_time(dt):
    """
    Get relative time string (e.g., "2 hours ago") based on British timezone.
    
    Args:
        dt: datetime object or parseable string
        
    Returns:
        Human-readable relative time string
    """
    if not dt:
        return "Unknown"
    
    parsed = safe_datetime_parse(dt)
    if not parsed:
        return "Unknown"
    
    # Convert both times to British timezone for accurate comparison
    now_british = datetime.now(BRITISH_TZ)
    parsed_british = convert_to_british_time(parsed)
    
    if parsed_british:
        diff = now_british - parsed_british
    else:
        diff = datetime.now() - parsed
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    else:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
