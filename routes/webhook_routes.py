"""
Webhook Routes

Handles webhook operations including:
- Tech Director referral webhooks
- Reply webhooks from external systems
- Webhook status and health monitoring
- Reminder scheduling

Author: AutoAssistGroup Development Team
"""

import os
import re
import logging
import threading
import time
import requests
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, session

from middleware.session_manager import is_authenticated, is_admin, safe_member_lookup
from config.settings import WEBHOOK_URL

logger = logging.getLogger(__name__)


def strip_email_quotes(text):
    """
    Strip quoted reply chains from incoming email text.
    
    Removes:
    - "On <date> <name> <email> wrote:" blocks and everything after
    - Gmail-style ">" quoted lines at the end
    - Outlook-style "-----Original Message-----" separators
    - "From: ... Sent: ... To: ... Subject: ..." Outlook headers
    """
    if not text or not isinstance(text, str):
        return text or ''
    
    lines = text.split('\n')
    cut_index = len(lines)
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Gmail/standard: "On <date> ... wrote:" or "On <date> ... wrote :"
        if re.match(r'^On\s+.+wrote\s*:\s*$', stripped, re.IGNORECASE):
            cut_index = i
            break
        
        # Outlook: "-----Original Message-----"
        if re.match(r'^-{3,}\s*Original Message\s*-{3,}$', stripped, re.IGNORECASE):
            cut_index = i
            break
        
        # Outlook: "From: ... " header block
        if re.match(r'^From:\s+.+', stripped) and i + 1 < len(lines):
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
            if re.match(r'^(Sent|Date|To|Subject):', next_line, re.IGNORECASE):
                cut_index = i
                break
        
        # Generic separator line
        if re.match(r'^_{5,}$|^-{5,}$|^={5,}$', stripped):
            cut_index = i
            break
    
    # Take only lines before the quote marker
    result_lines = lines[:cut_index]
    
    # Also strip trailing ">" quoted lines (sometimes mixed into the body)
    while result_lines and result_lines[-1].strip().startswith('>'):
        result_lines.pop()
    
    # Strip trailing blank lines
    while result_lines and not result_lines[-1].strip():
        result_lines.pop()
    
    result = '\n'.join(result_lines).strip()
    
    if result != text.strip():
        logger.info(f"Stripped email quotes: {len(text)} chars → {len(result)} chars")
    
    return result

# Create blueprint
webhook_bp = Blueprint('webhook', __name__, url_prefix='/api/webhook')

# In-memory storage for webhook status tracking
_webhook_status = {}
_webhook_lock = threading.Lock()


@webhook_bp.route('/tech-director/<ticket_id>', methods=['POST'])
def refer_to_tech_director(ticket_id):
    """
    Dedicated endpoint to refer ticket to Tech Director and trigger webhook.
    """
    try:
        if not is_authenticated():
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        from database import get_db
        db = get_db()
        
        # Get ticket
        ticket = db.get_ticket_by_id(ticket_id)
        if not ticket:
            return jsonify({'success': False, 'error': 'Ticket not found'}), 404
        
        # Update ticket status
        db.update_ticket(ticket_id, {
            'status': 'Referred to Tech Director',
            'referred_at': datetime.now(),
            'referred_by': session.get('member_id')
        })
        
        # Trigger webhook asynchronously
        _trigger_tech_director_webhook_async(
            ticket_id, 
            ticket, 
            'referral',
            session.get('member_name')
        )
        
        logger.info(f"Ticket {ticket_id} referred to Tech Director by {session.get('member_name')}")
        
        return jsonify({
            'success': True,
            'message': 'Ticket referred to Technical Director',
            'ticket_id': ticket_id
        })
        
    except Exception as e:
        logger.error(f"Error referring ticket to tech director: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@webhook_bp.route('/status/<ticket_id>', methods=['GET'])
def get_webhook_status(ticket_id):
    """Get real-time status of async webhook for a ticket."""
    with _webhook_lock:
        status = _webhook_status.get(ticket_id, {
            'status': 'unknown',
            'message': 'No webhook data found'
        })
    
    return jsonify({
        'success': True,
        'ticket_id': ticket_id,
        'webhook': status
    })


@webhook_bp.route('/health', methods=['GET'])
def webhook_health():
    """Get overall health status of the webhook system."""
    return jsonify({
        'success': True,
        'status': 'operational',
        'webhook_url': WEBHOOK_URL[:50] + '...' if len(WEBHOOK_URL) > 50 else WEBHOOK_URL,
        'pending_webhooks': len(_webhook_status),
        'timestamp': datetime.now().isoformat()
    })


@webhook_bp.route('/cleanup', methods=['POST'])
def webhook_cleanup():
    """Clean up old webhook metadata (admin only)."""
    if not is_authenticated() or not is_admin():
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        with _webhook_lock:
            count = len(_webhook_status)
            _webhook_status.clear()
        
        logger.info(f"Webhook cleanup: cleared {count} entries")
        
        return jsonify({
            'success': True,
            'message': f'Cleared {count} webhook status entries'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@webhook_bp.route('/reply', methods=['POST'])
def webhook_reply():
    """
    Webhook endpoint for external systems (like n8n) to send ticket replies.
    Use ONLY for incoming customer/external replies. Do NOT call this for
    agent replies that were already saved by POST /api/tickets/<id>/reply.

    Idempotency: If payload includes portal_reply_id (reply already created by
    portal), we skip creating a duplicate and return success.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        ticket_id = data.get('ticket_id', data.get('ticketId'))
        if not ticket_id:
            return jsonify({'success': False, 'error': 'ticket_id required'}), 400
        
        # Accept full customer reply from any common payload key (n8n may send short "message" + full "body")
        message_candidates = [
            data.get('message'),
            data.get('reply'),
            data.get('content'),
            data.get('body'),
            data.get('text'),
            data.get('email_body'),
            data.get('reply_message'),
            data.get('plainText'),
            data.get('html') if isinstance(data.get('html'), str) else None,
        ]
        message = ''
        for c in message_candidates:
            if c is not None and isinstance(c, str):
                c = c.strip()
                if len(c) > len(message):
                    message = c
        if not message:
            return jsonify({'success': False, 'error': 'message required (send body, message, reply, or content)'}), 400
        # Log all candidates for debugging truncation
        candidate_debug = {}
        for k in ['message', 'reply', 'content', 'body', 'text', 'email_body', 'plainText', 'html']:
            val = data.get(k)
            if val and isinstance(val, str):
                candidate_debug[k] = len(val)
        
        logger.info(f"Webhook payload debug - Ticket {ticket_id}: keys_received={list(data.keys())}, candidates_lengths={candidate_debug}")

        message = ''
        for c in message_candidates:
            if c is not None and isinstance(c, str):
                c = c.strip()
                if len(c) > len(message):
                    message = c
        if not message:
            logger.error(f"Webhook error: No message content found in payload. Keys: {list(data.keys())}")
            return jsonify({'success': False, 'error': 'message required (send body, message, reply, or content)'}), 400
            
        logger.info(f"Webhook reply: selected longest message (length={len(message)}) for ticket {ticket_id}")
        
        from database import get_db
        from bson.objectid import ObjectId
        db = get_db()
        
        # Verify ticket exists
        ticket = db.get_ticket_by_id(ticket_id)
        if not ticket:
            return jsonify({'success': False, 'error': 'Ticket not found'}), 404
        
        # Idempotency: if n8n echoes back a reply already saved by the portal, do not duplicate (and do not overwrite username)
        portal_reply_id = data.get('portal_reply_id', data.get('reply_id'))
        if portal_reply_id:
            try:
                if ObjectId.is_valid(portal_reply_id):
                    existing = db.replies.find_one({
                        '_id': ObjectId(portal_reply_id),
                        'ticket_id': ticket_id
                    })
                    if existing:
                        logger.info(f"Webhook reply idempotent: reply {portal_reply_id} already exists for ticket {ticket_id}, skipping create")
                        return jsonify({
                            'success': True,
                            'message': 'Reply already exists (idempotent)',
                            'reply_id': str(existing['_id']),
                            'ticket_id': ticket_id,
                            'idempotent': True
                        })
            except Exception as e:
                logger.warning(f"Idempotency check failed for portal_reply_id {portal_reply_id}: {e}")
        
        # Idempotency by content + time: same message on this ticket in the last 2 minutes = likely echo from n8n (avoid duplicate + wrong "External System" username)
        message_stripped = (message or "").strip()
        if message_stripped:
            cutoff = datetime.now() - timedelta(minutes=2)
            for recent in db.replies.find({
                'ticket_id': ticket_id,
                'created_at': {'$gte': cutoff},
                'sender_type': 'agent'
            }).sort('created_at', -1).limit(5):
                if (recent.get('message') or "").strip() == message_stripped:
                    logger.info(f"Webhook reply idempotent: same message already saved as agent reply for ticket {ticket_id}, skipping create (prevents duplicate + wrong username)")
                    return jsonify({
                        'success': True,
                        'message': 'Reply already exists (idempotent)',
                        'reply_id': str(recent['_id']),
                        'ticket_id': ticket_id,
                        'idempotent': True
                    })
        
        # Normalize attachments (handle strings/malformed data from n8n)
        raw_attachments = data.get('attachments', [])
        normalized_attachments = []
        import base64
        
        for att in raw_attachments:
            if isinstance(att, dict):
                # Ensure filename exists
                if not att.get('filename') and not att.get('fileName'):
                    att['filename'] = 'attachment'
                normalized_attachments.append(att)
            elif isinstance(att, str):
                # Handle string attachments (base64 or keys)
                try:
                    # Try to treat as base64 data first? Or just text content?
                    # If it's short, it's probably a filename or key. If long, base64.
                    # For safety, let's treat it as text content for now unless we know better.
                    # But "attachment1" suggests it might be a key.
                    # We'll validly encode it so it can be downloaded as a text file.
                    encoded = base64.b64encode(att.encode('utf-8')).decode('utf-8')
                    normalized_attachments.append({
                        'filename': 'attachment.txt',
                        'content_type': 'text/plain',
                        'data': encoded,
                        'type': 'file'
                    })
                except Exception as e:
                    logger.warning(f"Failed to normalize string attachment: {e}")
            else:
                logger.warning(f"Skipping invalid attachment type: {type(att)}")

        reply_data = {
            'ticket_id': ticket_id,
            'message': strip_email_quotes(message),
            'sender_name': data.get('sender_name', data.get('from', 'External System')),
            'sender_type': 'webhook',
            'attachments': normalized_attachments,
            'created_at': datetime.now()
        }
        
        reply_id = db.create_reply(reply_data)
        
        # Emit real-time notification for new customer reply
        try:
            from socket_events import emit_new_reply
            emit_new_reply(ticket_id, {
                'reply_id': str(reply_id),
                'ticket_id': ticket_id,
                'message': message,
                'sender_name': reply_data['sender_name'],
                'sender_type': 'customer',
                'attachments': len(data.get('attachments', [])),
                'created_at': datetime.now().isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to emit customer reply event: {e}")
        
        # Update ticket with unread reply flag
        db.update_ticket(ticket_id, {
            'has_unread_reply': True,
            'last_reply_at': datetime.now()
        })
        
        logger.info(f"Webhook reply added to ticket {ticket_id}")
        
        return jsonify({
            'success': True,
            'message': 'Reply added successfully',
            'reply_id': str(reply_id),
            'ticket_id': ticket_id
        })
        
    except Exception as e:
        logger.error(f"Webhook reply error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@webhook_bp.route('/test', methods=['POST'])
def test_webhook():
    """Test the n8n webhook connection directly."""
    try:
        test_data = {
            'test': True,
            'timestamp': datetime.now().isoformat(),
            'message': 'AutoAssistGroup webhook test'
        }
        
        response = requests.post(
            WEBHOOK_URL,
            json=test_data,
            timeout=10
        )
        
        return jsonify({
            'success': True,
            'webhook_status': response.status_code,
            'webhook_response': response.text[:500] if response.text else None
        })
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Webhook timeout'
        }), 504
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _trigger_tech_director_webhook_async(ticket_id, ticket_data, method, referred_by):
    """
    Asynchronous webhook trigger - runs in background thread.
    Does not block user interface.
    """
    def webhook_worker():
        max_retries = 3
        retry_delay = 2
        
        payload = {
            'ticket_id': ticket_id,
            'ticket_data': _serialize_for_webhook(ticket_data),
            'assignment_method': method,
            'referred_by': referred_by,
            'timestamp': datetime.now().isoformat()
        }
        
        with _webhook_lock:
            _webhook_status[ticket_id] = {
                'status': 'pending',
                'started_at': datetime.now().isoformat()
            }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    WEBHOOK_URL,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    with _webhook_lock:
                        _webhook_status[ticket_id] = {
                            'status': 'success',
                            'completed_at': datetime.now().isoformat()
                        }
                    logger.info(f"Webhook success for ticket {ticket_id}")
                    return
                    
            except Exception as e:
                logger.error(f"Webhook attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        with _webhook_lock:
            _webhook_status[ticket_id] = {
                'status': 'failed',
                'failed_at': datetime.now().isoformat()
            }
    
    thread = threading.Thread(target=webhook_worker, daemon=True)
    thread.start()


def _serialize_for_webhook(data):
    """Serialize data for webhook payload."""
    if not data:
        return None
    
    result = {}
    for key, value in data.items():
        if key == '_id':
            result['_id'] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = _serialize_for_webhook(value)
        elif isinstance(value, list):
            result[key] = [_serialize_for_webhook(v) if isinstance(v, dict) else str(v) if hasattr(v, '__str__') and not isinstance(v, (str, int, float, bool)) else v for v in value]
        else:
            result[key] = value
    
    return result
