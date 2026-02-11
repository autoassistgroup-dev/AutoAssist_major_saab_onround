"""
Session Management Middleware

Handles Flask session operations including:
- Session timeout checking
- Session refresh/persistence
- User session restoration from database
- Safe member lookup with auto-restoration

Author: AutoAssistGroup Development Team
"""

import logging
from datetime import datetime
from flask import session, current_app

logger = logging.getLogger(__name__)


def check_session_timeout():
    """
    Check if session has timed out.
    
    Currently disabled - sessions are permanent.
    
    Returns:
        bool: False (sessions never expire)
    """
    # Sessions never expire - always return False
    return False


def refresh_session():
    """
    Lightweight session refresh - only updates periodically to reduce overhead.
    
    PERFORMANCE FIX: Previously modified session on EVERY request (counter was reaching 400+).
    Now only refreshes every 5 minutes to avoid constant session writes.
    
    Returns:
        bool: True if session is valid
    """
    try:
        if 'member_id' in session:
            # Ensure session is permanent (one-time check)
            if not session.get('permanent'):
                session.permanent = True
            
            # Only refresh timestamp every 5 minutes to avoid constant session writes
            last_refresh = session.get('_last_refresh', '')
            now_str = datetime.now().isoformat()
            
            # Compare just the minute portion to avoid parsing overhead
            if not last_refresh or now_str[:16] != last_refresh[:16]:
                # Only update every minute at most
                needs_refresh = True
                if last_refresh:
                    try:
                        last_dt = datetime.fromisoformat(last_refresh)
                        diff = (datetime.now() - last_dt).total_seconds()
                        needs_refresh = diff > 300  # Only refresh every 5 minutes
                    except (ValueError, TypeError):
                        needs_refresh = True
                
                if needs_refresh:
                    session['_last_refresh'] = now_str
                    session.modified = True
            
            return True
        return False
    except Exception as e:
        logger.error(f"Error refreshing session: {e}")
        return False


def restore_user_session():
    """
    Simple session restoration - try to get user from database.
    
    Attempts to restore session data from database using user_id.
    
    Returns:
        bool: True if session was restored successfully
    """
    try:
        # If session already has member_id, no need to restore
        if 'member_id' in session:
            return True
        
        logger.info(f"Attempting session restoration. Session keys: {list(session.keys())}")
        
        # Try to restore from user_id in session
        if 'user_id' in session:
            try:
                from database import get_db
                db = get_db()
                user = db.get_member_by_user_id(session['user_id'])
                if user:
                    # Simple restoration
                    session['member_id'] = str(user['_id'])
                    session['member_name'] = user.get('name', 'Unknown')
                    session['member_role'] = user.get('role', 'Member')
                    session.permanent = True
                    session.modified = True
                    
                    logger.info(f"Session restored for user {user.get('name', 'Unknown')}")
                    return True
                else:
                    logger.warning(f"User {session['user_id']} not found in database")
            except Exception as e:
                logger.error(f"Failed to restore session: {e}")
        
        return False
        
    except Exception as e:
        logger.error(f"Error in session restoration: {e}")
        return False


def check_and_restore_session():
    """
    Check if session is valid and try to restore if needed.
    
    Returns:
        bool: True if session is valid or was restored successfully
    """
    try:
        # If session has member_id, it's valid
        if 'member_id' in session:
            return True
        
        # Try to restore the session
        if restore_user_session():
            return True
        
        # If restoration failed, session is truly invalid
        return False
        
    except Exception as e:
        logger.error(f"Error checking/restoring session: {e}")
        return False


def safe_member_lookup():
    """
    Safely get member data with automatic session restoration.
    
    Returns:
        dict: Member data or None if not found
    """
    try:
        if 'member_id' not in session:
            # Try to restore session first
            if check_and_restore_session():
                logger.info("Session restored during member lookup")
            else:
                return None
        
        # Now try to get member data
        from database import get_db
        db = get_db()
        current_member = db.get_member_by_id(session['member_id'])
        
        if not current_member:
            logger.warning(f"Member {session.get('member_id')} not found in database")
            return None
        
        return current_member
        
    except Exception as e:
        logger.error(f"Error in safe_member_lookup: {e}")
        return None


def get_current_user_id():
    """
    Get current user's member ID from session.
    
    Returns:
        str: Member ID or None
    """
    return session.get('member_id')


def get_current_user_role():
    """
    Get current user's role from session.
    
    Returns:
        str: User role or None
    """
    return session.get('member_role')


def is_authenticated():
    """
    Check if user is authenticated.
    
    Returns:
        bool: True if user has valid session
    """
    return 'member_id' in session


def is_admin():
    """
    Check if current user is an administrator.
    
    Returns:
        bool: True if user is an admin
    """
    role = get_current_user_role()
    return role in ['Administrator', 'Admin', 'admin']


def is_tech_director():
    """
    Check if current user is the Technical Director.
    
    Returns:
        bool: True if user is Technical Director
    """
    role = get_current_user_role()
    return role == 'Technical Director'


def clear_session():
    """Clear all session data for logout."""
    session.clear()


def init_session(user):
    """
    Initialize session for a user after login.
    
    Args:
        user: User document from database
    """
    session.permanent = True
    session['member_id'] = str(user['_id'])
    session['user_id'] = user.get('user_id')
    session['member_name'] = user.get('name', 'Unknown')
    session['member_role'] = user.get('role', 'Member')
    session['_login_time'] = datetime.now().isoformat()
    session.modified = True
