"""
Attachment Routes

Handles file attachment operations including:
- Downloading attachments
- Previewing attachments
- Serving uploaded files

Author: AutoAssistGroup Development Team
"""

import os
import base64
import logging
from flask import Blueprint, jsonify, request, send_file, make_response, Response
from io import BytesIO
from bson.objectid import ObjectId

from middleware.session_manager import is_authenticated
from utils.file_utils import get_mime_type

logger = logging.getLogger(__name__)

# Create blueprint
attachment_bp = Blueprint('attachments', __name__, url_prefix='/api/attachments')


@attachment_bp.route('/ticket/<ticket_id>/<int:attachment_index>', methods=['GET'])
def download_attachment(ticket_id, attachment_index):
    """
    Download attachments from multiple sources:
    1. Direct ticket attachments (base64 data)
    2. Reply attachments (webhook files)
    3. Metadata attachments (file uploads)
    """
    try:
        if not is_authenticated():
            return jsonify({'error': 'Authentication required'}), 401
        
        from database import get_db
        db = get_db()
        
        # Get ticket
        ticket = db.get_ticket_by_id(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Get attachments array
        attachments = ticket.get('attachments', [])
        
        if attachment_index < 0 or attachment_index >= len(attachments):
            return jsonify({'error': 'Attachment not found'}), 404
        
        attachment = attachments[attachment_index]
        
        # Get file data
        file_data = None
        filename = attachment.get('filename', attachment.get('fileName', 'download'))
        
        # Try to get base64 data
        if attachment.get('data') or attachment.get('fileData'):
            base64_data = attachment.get('data') or attachment.get('fileData')
            try:
                file_data = base64.b64decode(base64_data)
            except Exception as e:
                logger.error(f"Failed to decode base64: {e}")
        
        # If no data, try file path
        if not file_data and attachment.get('file_path'):
            file_path = attachment.get('file_path')
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_data = f.read()
        
        if not file_data:
            return jsonify({'error': 'Attachment data not available'}), 404
        
        # Determine MIME type
        mime_type = get_mime_type(filename)
        
        # Create response
        response = make_response(file_data)
        response.headers['Content-Type'] = mime_type
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Length'] = len(file_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading attachment: {e}")
        return jsonify({'error': str(e)}), 500


@attachment_bp.route('/preview/<ticket_id>/<int:attachment_index>', methods=['GET'])
def preview_attachment(ticket_id, attachment_index):
    """Preview attachment inline (for images, PDFs, etc.)."""
    try:
        if not is_authenticated():
            return jsonify({'error': 'Authentication required'}), 401
        
        from database import get_db
        db = get_db()
        
        # Get ticket
        ticket = db.get_ticket_by_id(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Get attachments array
        attachments = ticket.get('attachments', [])
        
        if attachment_index < 0 or attachment_index >= len(attachments):
            return jsonify({'error': 'Attachment not found'}), 404
        
        attachment = attachments[attachment_index]
        
        # Get file data (same logic as download)
        file_data = None
        filename = attachment.get('filename', attachment.get('fileName', 'file'))
        
        if attachment.get('data') or attachment.get('fileData'):
            base64_data = attachment.get('data') or attachment.get('fileData')
            try:
                file_data = base64.b64decode(base64_data)
            except Exception:
                pass
        
        if not file_data and attachment.get('file_path'):
            file_path = attachment.get('file_path')
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_data = f.read()
        
        if not file_data:
            return jsonify({'error': 'Attachment data not available'}), 404
        
        # Determine MIME type
        mime_type = get_mime_type(filename)
        
        # Create response for inline display
        response = make_response(file_data)
        response.headers['Content-Type'] = mime_type
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error previewing attachment: {e}")
        return jsonify({'error': str(e)}), 500


@attachment_bp.route('/reply/<reply_id>/<int:attachment_index>', methods=['GET'])
def download_reply_attachment(reply_id, attachment_index):
    """Download attachment from a specific reply."""
    try:
        if not is_authenticated():
            return jsonify({'error': 'Authentication required'}), 401
        
        from database import get_db
        from bson.objectid import ObjectId
        db = get_db()
        
        # Get reply
        logger.info(f"Looking for reply with ID: {reply_id}")
        reply = db.replies.find_one({'_id': ObjectId(reply_id)})
        if not reply:
            logger.error(f"Reply not found: {reply_id}")
            return jsonify({'error': 'Reply not found'}), 404
        logger.info(f"Reply found, has {len(reply.get('attachments', []))} attachments")
        
        # Get attachments
        attachments = reply.get('attachments', [])
        
        if attachment_index < 0 or attachment_index >= len(attachments):
            return jsonify({'error': 'Attachment not found'}), 404
        
        attachment = attachments[attachment_index]
        filename = attachment.get('filename', attachment.get('fileName', 'download'))
        file_data = None
        
        # Common-document ref: redirect or stream from common_documents
        if attachment.get('type') == 'common-document' or attachment.get('document_id'):
            doc_id = attachment.get('ref') or attachment.get('document_id')
            if doc_id:
                doc = db.common_documents.find_one({'_id': ObjectId(doc_id)})
                if doc and doc.get('file_path') and os.path.exists(doc.get('file_path')):
                    return send_file(doc['file_path'], download_name=doc.get('file_name', filename), mimetype=doc.get('file_type', get_mime_type(filename)), as_attachment=True)
                if doc and doc.get('file_data'):
                    try:
                        file_data = base64.b64decode(doc['file_data'])
                        response = make_response(file_data)
                        response.headers['Content-Type'] = doc.get('file_type', get_mime_type(filename))
                        response.headers['Content-Disposition'] = f'attachment; filename="{doc.get("file_name", filename)}"'
                        return response
                    except Exception:
                        pass
        
        # File on disk
        if attachment.get('file_path') and os.path.exists(attachment.get('file_path')):
            with open(attachment['file_path'], 'rb') as f:
                file_data = f.read()
        
        # Base64 (legacy)
        if not file_data and (attachment.get('data') or attachment.get('fileData')):
            base64_data = attachment.get('data') or attachment.get('fileData')
            try:
                file_data = base64.b64decode(base64_data)
            except Exception as e:
                logger.error(f"Failed to decode base64: {e}")
        
        if not file_data:
            return jsonify({'error': 'Attachment data not available'}), 404
        
        mime_type = attachment.get('content_type') or get_mime_type(filename)
        response = make_response(file_data)
        response.headers['Content-Type'] = mime_type
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        logger.error(f"Error downloading reply attachment: {e}")
        return jsonify({'error': str(e)}), 500


@attachment_bp.route('/reply/<reply_id>/<int:attachment_index>/preview', methods=['GET'])
def preview_reply_attachment(reply_id, attachment_index):
    """Preview attachment from a specific reply inline."""
    try:
        if not is_authenticated():
            return jsonify({'error': 'Authentication required'}), 401
        
        from database import get_db
        from bson.objectid import ObjectId
        db = get_db()
        
        # Get reply
        logger.info(f"[PREVIEW] Looking for reply with ID: {reply_id}")
        reply = db.replies.find_one({'_id': ObjectId(reply_id)})
        if not reply:
            logger.error(f"[PREVIEW] Reply not found: {reply_id}")
            return jsonify({'error': 'Reply not found'}), 404
        logger.info(f"[PREVIEW] Reply found, has {len(reply.get('attachments', []))} attachments")
        
        # Get attachments
        attachments = reply.get('attachments', [])
        
        if attachment_index < 0 or attachment_index >= len(attachments):
            return jsonify({'error': 'Attachment not found'}), 404
        
        attachment = attachments[attachment_index]
        filename = attachment.get('filename', attachment.get('fileName', 'preview'))
        file_data = None
        
        if attachment.get('type') == 'common-document' or attachment.get('document_id'):
            doc_id = attachment.get('ref') or attachment.get('document_id')
            if doc_id:
                doc = db.common_documents.find_one({'_id': ObjectId(doc_id)})
                if doc and doc.get('file_path') and os.path.exists(doc.get('file_path')):
                    return send_file(doc['file_path'], download_name=doc.get('file_name', filename), mimetype=doc.get('file_type', get_mime_type(filename)), as_attachment=False)
                if doc and doc.get('file_data'):
                    try:
                        file_data = base64.b64decode(doc['file_data'])
                        response = make_response(file_data)
                        response.headers['Content-Type'] = doc.get('file_type', get_mime_type(filename))
                        response.headers['Content-Disposition'] = f'inline; filename="{doc.get("file_name", filename)}"'
                        return response
                    except Exception:
                        pass
        
        if attachment.get('file_path') and os.path.exists(attachment.get('file_path')):
            with open(attachment['file_path'], 'rb') as f:
                file_data = f.read()
        
        if not file_data and (attachment.get('data') or attachment.get('fileData')):
            base64_data = attachment.get('data') or attachment.get('fileData')
            try:
                file_data = base64.b64decode(base64_data)
            except Exception as e:
                logger.error(f"[PREVIEW] Failed to decode base64: {e}")
        
        if not file_data:
            return jsonify({'error': 'Attachment data not available'}), 404
        
        mime_type = attachment.get('content_type') or get_mime_type(filename)
        response = make_response(file_data)
        response.headers['Content-Type'] = mime_type
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
        
    except Exception as e:
        logger.error(f"Error previewing reply attachment: {e}")
        return jsonify({'error': str(e)}), 500
