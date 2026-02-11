"""
Claim Document Routes Blueprint

This module contains API endpoints for managing claim documents
(receipts, photos, etc.) attached to tickets.

Author: AutoAssistGroup Development Team
"""

from flask import Blueprint, request, jsonify, send_file
import logging
from datetime import datetime
import io
import base64
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

claim_document_bp = Blueprint('claim_document', __name__, url_prefix='/api')


@claim_document_bp.route('/tickets/<ticket_id>/claim-documents', methods=['GET'])
def get_claim_documents(ticket_id):
    """
    Get all claim documents for a specific ticket.
    
    Returns:
        JSON with list of claim documents
    """
    try:
        from database import get_db
        db = get_db()
        # Normalize to string so query matches regardless of how ticket_id was stored
        ticket_id_str = str(ticket_id).strip() if ticket_id is not None else ''
        if not ticket_id_str:
            return jsonify({'success': False, 'message': 'Ticket ID required', 'documents': [], 'count': 0}), 400

        # Get all documents for this ticket (match string ticket_id)
        documents = list(db.claim_documents.find({
            'ticket_id': ticket_id_str,
            'is_deleted': {'$ne': True}
        }))
        
        # Convert ObjectId to string for JSON serialization
        results = []
        for doc in documents:
            doc_data = {
                '_id': str(doc['_id']),
                'ticket_id': doc.get('ticket_id'),
                'file_name': doc.get('file_name', 'Untitled'),
                'file_size': doc.get('file_size', 0),
                'file_type': doc.get('file_type', 'application/octet-stream'),
                'description': doc.get('description', ''),
                'uploaded_by': doc.get('uploaded_by', ''),
                'uploaded_at': doc.get('uploaded_at', datetime.now()).isoformat() if isinstance(doc.get('uploaded_at'), datetime) else str(doc.get('uploaded_at', ''))
            }
            results.append(doc_data)
            
        logger.info(f"Retrieved {len(results)} claim documents for ticket {ticket_id_str}")
        
        return jsonify({
            'success': True,
            'documents': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error getting claim documents for ticket {ticket_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to retrieve claim documents'
        }), 500


@claim_document_bp.route('/tickets/<ticket_id>/claim-documents', methods=['POST'])
def upload_claim_document(ticket_id):
    """
    Upload a new claim document for a ticket.
    File is persisted to disk; only metadata and file_path stored in MongoDB.
    """
    try:
        from database import get_db
        from flask import session
        from config.settings import Config
        from utils.file_utils import save_attachment_bytes_to_disk
        db = get_db()
        ticket_id_str = str(ticket_id).strip() if ticket_id is not None else ''
        if not ticket_id_str:
            return jsonify({'success': False, 'message': 'Ticket ID required'}), 400

        ticket = db.tickets.find_one({'ticket_id': ticket_id_str})
        if not ticket:
            return jsonify({'success': False, 'message': 'Ticket not found'}), 404
        
        file = request.files.get('file')
        if not file or not file.filename:
            return jsonify({'success': False, 'message': 'File is required'}), 400
        
        description = request.form.get('description', '').strip()
        file_bytes = file.read()
        if not file_bytes:
            return jsonify({'success': False, 'message': 'File is empty'}), 400
        
        upload_root = Config.get_upload_folder()
        prefix = f"claim_{ticket_id_str}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        saved = save_attachment_bytes_to_disk(
            upload_root, "claim_docs", prefix, file.filename, file_bytes
        )
        if not saved:
            return jsonify({'success': False, 'message': 'Failed to save file to disk'}), 500
        
        uploaded_by = session.get('member_id') or session.get('member_name') or session.get('user_id') or 'unknown'
        
        doc_data = {
            'ticket_id': ticket_id_str,
            'file_name': saved['filename'],
            'file_size': saved['size'],
            'file_type': saved.get('mime_type', 'application/octet-stream'),
            'file_path': saved['file_path'],
            'description': description,
            'uploaded_by': str(uploaded_by),
            'uploaded_at': datetime.now(),
            'is_deleted': False
        }
        
        result = db.claim_documents.insert_one(doc_data)
        
        logger.info(f"Uploaded claim document '{saved['filename']}' for ticket {ticket_id_str} (ID: {result.inserted_id})")
        
        return jsonify({
            'success': True,
            'message': 'Document uploaded successfully',
            'document': {
                '_id': str(result.inserted_id),
                'file_name': saved['filename'],
                'file_size': saved['size'],
                'file_type': doc_data['file_type'],
                'description': description,
                'uploaded_at': doc_data['uploaded_at'].isoformat()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading claim document for ticket {ticket_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to upload document'
        }), 500


@claim_document_bp.route('/tickets/<ticket_id>/claim-documents/<document_id>', methods=['DELETE'])
def delete_claim_document(ticket_id, document_id):
    """
    Delete a claim document (soft delete).
    
    Returns:
        JSON with success status
    """
    try:
        from database import get_db
        db = get_db()
        ticket_id_str = str(ticket_id).strip() if ticket_id is not None else ''
        doc = db.claim_documents.find_one({
            '_id': ObjectId(document_id),
            'ticket_id': ticket_id_str
        })
        
        if not doc:
            return jsonify({
                'success': False,
                'message': 'Document not found'
            }), 404
        
        # Soft delete
        db.claim_documents.update_one(
            {'_id': ObjectId(document_id)},
            {'$set': {'is_deleted': True, 'deleted_at': datetime.now()}}
        )
        
        logger.info(f"Soft-deleted claim document {document_id} from ticket {ticket_id_str}")
        
        return jsonify({
            'success': True,
            'message': 'Document deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting claim document {document_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to delete document'
        }), 500


@claim_document_bp.route('/tickets/<ticket_id>/claim-documents/<document_id>/download', methods=['GET'])
def download_claim_document(ticket_id, document_id):
    """
    Download a claim document file. Prefer file_path (disk); fall back to file_data (legacy base64).
    """
    try:
        import os
        from database import get_db
        db = get_db()
        ticket_id_str = str(ticket_id).strip() if ticket_id is not None else ''
        doc = db.claim_documents.find_one({
            '_id': ObjectId(document_id),
            'ticket_id': ticket_id_str,
            'is_deleted': {'$ne': True}
        })
        
        if not doc:
            return jsonify({'success': False, 'message': 'Document not found'}), 404
        
        file_name = doc.get('file_name', 'document')
        file_type = doc.get('file_type', 'application/octet-stream')
        file_path = doc.get('file_path')
        file_data_b64 = doc.get('file_data')
        
        if file_path and os.path.exists(file_path):
            return send_file(
                file_path,
                download_name=file_name,
                mimetype=file_type,
                as_attachment=True
            )
        if file_data_b64:
            try:
                binary_data = base64.b64decode(file_data_b64)
                return send_file(
                    io.BytesIO(binary_data),
                    download_name=file_name,
                    mimetype=file_type,
                    as_attachment=True
                )
            except Exception as decode_error:
                logger.error(f"Error decoding file data: {decode_error}")
                return jsonify({'success': False, 'message': 'Error decoding file data'}), 500
        return jsonify({'success': False, 'message': 'No file data available'}), 404
        
    except Exception as e:
        logger.error(f"Error downloading claim document {document_id}: {e}")
        return jsonify({'success': False, 'error': str(e), 'message': 'Failed to download document'}), 500


@claim_document_bp.route('/tickets/<ticket_id>/vehicle-info', methods=['PUT'])
def update_vehicle_info(ticket_id):
    """
    Update vehicle and claim information for a ticket.
    
    Accepts:
        JSON with fields: vehicle_registration, service_date, claim_date, 
                         type_of_claim, technician, vhc_link
    
    Returns:
        JSON with success status
    """
    try:
        from database import get_db
        db = get_db()
        
        # Verify ticket exists
        ticket = db.tickets.find_one({'ticket_id': ticket_id})
        if not ticket:
            return jsonify({
                'success': False,
                'message': 'Ticket not found'
            }), 404
        
        data = request.get_json()
        
        update_data = {
            'updated_at': datetime.now()
        }
        
        # Update only the fields that are provided
        allowed_fields = [
            'vehicle_registration', 'service_date', 'claim_date',
            'type_of_claim', 'technician', 'vhc_link',
            'days_between_service_claim', 'advisories_followed',
            'within_warranty', 'new_fault_codes', 'dpf_light_on', 'eml_light_on'
        ]
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        db.tickets.update_one(
            {'ticket_id': ticket_id},
            {'$set': update_data}
        )
        
        logger.info(f"Updated vehicle info for ticket {ticket_id}")
        
        return jsonify({
            'success': True,
            'message': 'Vehicle information updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating vehicle info for ticket {ticket_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to update vehicle information'
        }), 500
