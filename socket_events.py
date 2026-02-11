"""
WebSocket Events Handler for Real-Time Updates

This module provides real-time communication using Flask-SocketIO for:
- New ticket notifications
- Live reply updates  
- Ticket status changes
- Ticket forwarding
- Technician assignment
- Takeover events
- Priority/Status changes
- Bookmark updates

Author: AutoAssistGroup Development Team
"""

import logging
from flask import session
from flask_socketio import SocketIO, emit, join_room, leave_room
# from flask_login import current_user # Removed dependency on flask_login

from middleware.session_manager import is_authenticated

logger = logging.getLogger(__name__)

# Initialize SocketIO (will be configured with app in init_socketio)
socketio = SocketIO()


def init_socketio(app):
    """Initialize SocketIO with Flask app. Use threading on Windows (eventlet has compatibility issues)."""
    import sys
    async_mode = 'threading' if sys.platform == 'win32' else 'eventlet'
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode=async_mode,
        logger=False,
        engineio_logger=False
    )
    logger.info("[SOCKETIO] Initialized with %s async mode", async_mode)
    return socketio


# ============== Connection Events ==============

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("[SOCKETIO] Client connected")
    emit('connected', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("[SOCKETIO] Client disconnected")


# ============== Room Management ==============

@socketio.on('join_ticket')
def handle_join_ticket(data):
    """Join a ticket-specific room for live updates"""
    ticket_id = data.get('ticket_id')
    
    # SECURITY: Ensure user is authenticated
    if not is_authenticated():
        logger.warning(f"[SOCKETIO] Unauthenticated attempt to join ticket_{ticket_id}")
        return
        
    if ticket_id:
        join_room(f'ticket_{ticket_id}')
        user_id = session.get('member_id', 'unknown')
        logger.info(f"[SOCKETIO] Client joined room: ticket_{ticket_id} (User: {user_id})")
        emit('joined_ticket', {'ticket_id': ticket_id})


@socketio.on('leave_ticket')
def handle_leave_ticket(data):
    """Leave a ticket-specific room"""
    ticket_id = data.get('ticket_id')
    if ticket_id:
        leave_room(f'ticket_{ticket_id}')
        logger.info(f"[SOCKETIO] Client left room: ticket_{ticket_id}")


@socketio.on('join_dashboard')
def handle_join_dashboard():
    """Join the dashboard room for new ticket notifications"""
    
    # SECURITY: Ensure user is authenticated
    if not is_authenticated():
        logger.warning("[SOCKETIO] Unauthenticated attempt to join dashboard")
        return

    join_room('dashboard')
    user_id = session.get('member_id', 'unknown')
    logger.info(f"[SOCKETIO] Client joined dashboard room (User: {user_id})")
    emit('joined_dashboard', {'status': 'joined'})


@socketio.on('join_user_room')
def handle_join_user_room(data=None):
    """Join a user-specific room for targeted notifications"""
    
    if not is_authenticated():
        logger.warning("[SOCKETIO] Unauthenticated attempt to join user room")
        return
    
    member_id = session.get('member_id') or (data.get('user_id') if data else None)
    if member_id:
        room_name = f'user_{str(member_id)}'
        join_room(room_name)
        logger.info(f"[SOCKETIO] Client joined user room: {room_name}")
        emit('joined_user_room', {'room': room_name, 'user_id': str(member_id)})


@socketio.on('join_role_room')
def handle_join_role_room(data=None):
    """Join a role-based room for role-specific notifications"""
    
    if not is_authenticated():
        logger.warning("[SOCKETIO] Unauthenticated attempt to join role room")
        return
    
    role = session.get('member_role') or (data.get('role') if data else None)
    if role:
        # Normalize role name for room (replace spaces with underscores)
        room_name = f'role_{role.replace(" ", "_")}'
        join_room(room_name)
        logger.info(f"[SOCKETIO] Client joined role room: {room_name}")
        emit('joined_role_room', {'room': room_name, 'role': role})


@socketio.on('typing')
def handle_typing(data):
    """
    Handle typing start event
    
    Args:
        data: { 'ticket_id': '...', 'user_name': '...' }
    """
    ticket_id = data.get('ticket_id')
    user_name = data.get('user_name')
    if ticket_id and user_name:
        # Broadcast to others in the room
        socketio.emit('typing', {
            'ticket_id': ticket_id,
            'user_name': user_name,
            'user_id': data.get('user_id')
        }, room=f'ticket_{ticket_id}', include_self=False)


@socketio.on('stop_typing')
def handle_stop_typing(data):
    """
    Handle typing stop event
    
    Args:
        data: { 'ticket_id': '...', 'user_name': '...' }
    """
    ticket_id = data.get('ticket_id')
    if ticket_id:
        socketio.emit('stop_typing', {
            'ticket_id': ticket_id,
            'user_id': data.get('user_id')
        }, room=f'ticket_{ticket_id}', include_self=False)


# ============== Broadcast Functions ==============

def emit_new_ticket(ticket_data):
    """
    Broadcast new ticket to all connected clients on dashboard
    
    Args:
        ticket_data: dict containing ticket information
    """
    try:
        logger.info(f"[SOCKETIO] Attempting to emit new_ticket: {ticket_data.get('ticket_id')}")
        socketio.emit('new_ticket', ticket_data, room='dashboard')
        logger.info(f"[SOCKETIO] Successfully emitted new_ticket: {ticket_data.get('ticket_id')}")
    except Exception as e:
        logger.error(f"[SOCKETIO] Error emitting new_ticket: {str(e)}", exc_info=True)


def emit_new_reply(ticket_id, reply_data):
    """
    Broadcast new reply to clients viewing the specific ticket.
    WebSocket only emits; it never persists replies to the DB (see docs/REPLY_ARCHITECTURE.md).
    
    Args:
        ticket_id: The ticket ID
        reply_data: dict containing reply information
    """
    try:
        socketio.emit('new_reply', reply_data, room=f'ticket_{ticket_id}')
        logger.info(f"[SOCKETIO] Emitted new_reply for ticket: {ticket_id}")
    except Exception as e:
        logger.error(f"[SOCKETIO] Error emitting new_reply: {e}")


def emit_ticket_update(ticket_id, update_data):
    """
    Broadcast ticket update (status, priority, etc.) to relevant clients
    
    Args:
        ticket_id: The ticket ID
        update_data: dict containing update information
    """
    try:
        # Emit to ticket room
        socketio.emit('ticket_updated', update_data, room=f'ticket_{ticket_id}')
        # Also emit to dashboard for list updates
        socketio.emit('ticket_updated', update_data, room='dashboard')
        logger.info(f"[SOCKETIO] Emitted ticket_updated for: {ticket_id}")
    except Exception as e:
        logger.error(f"[SOCKETIO] Error emitting ticket_updated: {e}")


def emit_reply_sent(ticket_id, reply_data):
    """
    Confirm reply was sent successfully (for sender's UI update)
    
    Args:
        ticket_id: The ticket ID
        reply_data: dict containing the sent reply
    """
    try:
        socketio.emit('reply_sent', reply_data, room=f'ticket_{ticket_id}')
        logger.info(f"[SOCKETIO] Emitted reply_sent for ticket: {ticket_id}")
    except Exception as e:
        logger.error(f"[SOCKETIO] Error emitting reply_sent: {e}")


# ============== NEW: Ticket Forwarding Events ==============

def emit_ticket_forwarded(ticket_id, forwarded_data):
    """
    Broadcast ticket forwarding event to relevant parties
    
    Args:
        ticket_id: The ticket ID being forwarded
        forwarded_data: dict containing:
            - ticket_id: str
            - subject: str
            - forwarded_from_id: str
            - forwarded_from_name: str
            - forwarded_to_id: str
            - forwarded_to_name: str
            - note: str (optional)
            - timestamp: str (ISO format)
    """
    try:
        # Emit to dashboard (for general list updates)
        socketio.emit('ticket_forwarded', forwarded_data, room='dashboard')
        
        # Emit to specific ticket room
        socketio.emit('ticket_forwarded', forwarded_data, room=f'ticket_{ticket_id}')
        
        # Emit to the recipient's user room for immediate notification
        recipient_id = forwarded_data.get('forwarded_to_id')
        if recipient_id:
            socketio.emit('ticket_forwarded_to_you', forwarded_data, room=f'user_{recipient_id}')
        
        # Emit to Tech Director role room if applicable
        if forwarded_data.get('is_tech_director_referral'):
            socketio.emit('ticket_referred', forwarded_data, room='role_Technical_Director')
        
        logger.info(f"[SOCKETIO] Emitted ticket_forwarded for: {ticket_id} to user {recipient_id}")
    except Exception as e:
        logger.error(f"[SOCKETIO] Error emitting ticket_forwarded: {e}")


def emit_ticket_taken_over(ticket_id, takeover_data):
    """
    Broadcast ticket takeover event
    
    Args:
        ticket_id: The ticket ID
        takeover_data: dict containing:
            - ticket_id: str
            - subject: str
            - taken_by_id: str
            - taken_by_name: str
            - previous_assignee_id: str (optional)
            - timestamp: str
    """
    try:
        # Emit to dashboard
        socketio.emit('ticket_taken_over', takeover_data, room='dashboard')
        
        # Emit to ticket room
        socketio.emit('ticket_taken_over', takeover_data, room=f'ticket_{ticket_id}')
        
        # Notify original assignee if there was one
        previous_id = takeover_data.get('previous_assignee_id')
        if previous_id:
            socketio.emit('ticket_reassigned', takeover_data, room=f'user_{previous_id}')
        
        logger.info(f"[SOCKETIO] Emitted ticket_taken_over for: {ticket_id}")
    except Exception as e:
        logger.error(f"[SOCKETIO] Error emitting ticket_taken_over: {e}")


def emit_technician_assigned(ticket_id, assignment_data):
    """
    Broadcast technician assignment event
    
    Args:
        ticket_id: The ticket ID
        assignment_data: dict containing:
            - ticket_id: str
            - subject: str
            - technician_id: str
            - technician_name: str
            - assigned_by_id: str
            - assigned_by_name: str
            - timestamp: str
    """
    try:
        # Emit to dashboard for badge updates
        socketio.emit('technician_assigned', assignment_data, room='dashboard')
        
        # Emit to ticket room
        socketio.emit('technician_assigned', assignment_data, room=f'ticket_{ticket_id}')
        
        logger.info(f"[SOCKETIO] Emitted technician_assigned for: {ticket_id}, tech: {assignment_data.get('technician_name')}")
    except Exception as e:
        logger.error(f"[SOCKETIO] Error emitting technician_assigned: {e}")


def emit_status_changed(ticket_id, status_data):
    """
    Broadcast ticket status change
    
    Args:
        ticket_id: The ticket ID
        status_data: dict containing:
            - ticket_id: str
            - old_status: str
            - new_status: str
            - changed_by_id: str
            - changed_by_name: str
            - timestamp: str
    """
    try:
        # Emit to dashboard
        socketio.emit('ticket_status_changed', status_data, room='dashboard')
        
        # Emit to ticket room
        socketio.emit('ticket_status_changed', status_data, room=f'ticket_{ticket_id}')
        
        # Also emit generic ticket_updated for backward compatibility
        socketio.emit('ticket_updated', {
            'ticket_id': ticket_id,
            'status': status_data.get('new_status'),
            'update_type': 'status'
        }, room='dashboard')
        
        logger.info(f"[SOCKETIO] Emitted ticket_status_changed for: {ticket_id}, status: {status_data.get('new_status')}")
    except Exception as e:
        logger.error(f"[SOCKETIO] Error emitting ticket_status_changed: {e}")


def emit_priority_changed(ticket_id, priority_data):
    """
    Broadcast ticket priority change
    
    Args:
        ticket_id: The ticket ID
        priority_data: dict containing:
            - ticket_id: str
            - old_priority: str
            - new_priority: str
            - changed_by_id: str
            - changed_by_name: str
            - timestamp: str
    """
    try:
        # Emit to dashboard
        socketio.emit('ticket_priority_changed', priority_data, room='dashboard')
        
        # Emit to ticket room
        socketio.emit('ticket_priority_changed', priority_data, room=f'ticket_{ticket_id}')
        
        # Also emit generic ticket_updated for backward compatibility
        socketio.emit('ticket_updated', {
            'ticket_id': ticket_id,
            'priority': priority_data.get('new_priority'),
            'update_type': 'priority'
        }, room='dashboard')
        
        logger.info(f"[SOCKETIO] Emitted ticket_priority_changed for: {ticket_id}, priority: {priority_data.get('new_priority')}")
    except Exception as e:
        logger.error(f"[SOCKETIO] Error emitting ticket_priority_changed: {e}")


def emit_bookmark_changed(ticket_id, bookmark_data):
    """
    Broadcast ticket bookmark/importance change
    
    Args:
        ticket_id: The ticket ID
        bookmark_data: dict containing:
            - ticket_id: str
            - is_important: bool
            - changed_by_id: str
            - timestamp: str
    """
    try:
        # Emit to dashboard for UI reordering
        socketio.emit('ticket_bookmarked', bookmark_data, room='dashboard')
        
        # Emit to ticket room
        socketio.emit('ticket_bookmarked', bookmark_data, room=f'ticket_{ticket_id}')
        
        logger.info(f"[SOCKETIO] Emitted ticket_bookmarked for: {ticket_id}, important: {bookmark_data.get('is_important')}")
    except Exception as e:
        logger.error(f"[SOCKETIO] Error emitting ticket_bookmarked: {e}")


def emit_tech_director_referral(ticket_id, referral_data):
    """
    Broadcast ticket referral to Tech Director
    
    Args:
        ticket_id: The ticket ID
        referral_data: dict containing:
            - ticket_id: str
            - subject: str
            - referred_by_id: str
            - referred_by_name: str
            - tech_director_id: str
            - timestamp: str
    """
    try:
        # Emit to Tech Director role room
        socketio.emit('ticket_referred_to_director', referral_data, room='role_Technical_Director')
        
        # Also emit to specific tech director user room
        tech_director_id = referral_data.get('tech_director_id')
        if tech_director_id:
            socketio.emit('ticket_referred_to_you', referral_data, room=f'user_{tech_director_id}')
        
        # Emit to dashboard for general awareness
        socketio.emit('ticket_forwarded', {
            **referral_data,
            'forwarded_to_name': 'Technical Director',
            'is_tech_director_referral': True
        }, room='dashboard')
        
        # Emit to ticket room
        socketio.emit('ticket_referred', referral_data, room=f'ticket_{ticket_id}')
        
        logger.info(f"[SOCKETIO] Emitted tech_director_referral for: {ticket_id}")
    except Exception as e:
        logger.error(f"[SOCKETIO] Error emitting tech_director_referral: {e}")
