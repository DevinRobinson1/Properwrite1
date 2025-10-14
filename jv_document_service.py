"""
JV Document Management Service
Handles secure document upload, storage, sharing, and access control for JV agreements
"""
import os
import uuid
import logging
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import psycopg2
import psycopg2.extras

# Allowed document types and their extensions
ALLOWED_EXTENSIONS = {
    'pdf': ['application/pdf'],
    'doc': ['application/msword'],
    'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    'xls': ['application/vnd.ms-excel'],
    'jpg': ['image/jpeg'],
    'jpeg': ['image/jpeg'],
    'png': ['image/png'],
    'txt': ['text/plain']
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class JVDocumentService:
    def __init__(self, database_url: str, upload_folder: str = 'jv_documents'):
        self.database_url = database_url
        self.upload_folder = upload_folder
        
        # Create upload folder if it doesn't exist
        os.makedirs(self.upload_folder, exist_ok=True)
        
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def is_allowed_file(self, filename: str, content_type: str) -> bool:
        """Check if file type is allowed"""
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        return ext in ALLOWED_EXTENSIONS and content_type in ALLOWED_EXTENSIONS[ext]
    
    def generate_secure_filename(self, original_filename: str, deal_id: str) -> str:
        """Generate a secure unique filename"""
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_id = str(uuid.uuid4())
        return f"{deal_id}_{unique_id}.{ext}"
    
    def save_file(self, file: FileStorage, deal_id: str) -> Tuple[str, str]:
        """
        Save uploaded file securely
        Returns (file_path, secure_filename)
        """
        try:
            # Generate secure filename
            secure_fname = self.generate_secure_filename(file.filename, deal_id)
            file_path = os.path.join(self.upload_folder, secure_fname)
            
            # Save file
            file.save(file_path)
            
            return file_path, secure_fname
            
        except Exception as e:
            logging.error(f"Error saving file: {e}")
            raise
    
    def upload_document(
        self,
        file: FileStorage,
        deal_id: str,
        partner_id: str,
        document_type: str,
        uploaded_by: str,
        description: str = None,
        requires_signature: bool = False,
        share_with_partner: bool = False
    ) -> Optional[str]:
        """
        Upload a document and create database record with proper versioning
        Returns document_id or None on failure
        """
        try:
            # Validate file
            if not file or not file.filename:
                raise ValueError("No file provided")
            
            if not self.is_allowed_file(file.filename, file.content_type):
                raise ValueError(f"File type not allowed: {file.content_type}")
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                raise ValueError(f"File size exceeds maximum of {MAX_FILE_SIZE / 1024 / 1024}MB")
            
            # Save file
            file_path, secure_fname = self.save_file(file, deal_id)
            
            # Create database record with versioning
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # CRITICAL FIX: Verify partner_id matches the deal
                    cur.execute("SELECT partner_id FROM jv_deals WHERE id = %s", (deal_id,))
                    result = cur.fetchone()
                    if not result:
                        raise ValueError("Deal not found")
                    if result[0] != partner_id:
                        raise ValueError("Partner ID does not match the deal")
                    
                    # VERSIONING FIX: Get the next version number for this deal/document_type
                    cur.execute("""
                        SELECT COALESCE(MAX(version), 0) + 1 as next_version
                        FROM jv_documents
                        WHERE deal_id = %s AND document_type = %s
                    """, (deal_id, document_type))
                    next_version = cur.fetchone()[0]
                    
                    # Mark all previous versions of this document type as not current
                    cur.execute("""
                        UPDATE jv_documents
                        SET is_current_version = false
                        WHERE deal_id = %s AND document_type = %s AND is_current_version = true
                    """, (deal_id, document_type))
                    
                    document_id = str(uuid.uuid4())
                    signature_status = 'pending' if requires_signature else 'not_required'
                    
                    # Insert new document with correct version
                    cur.execute("""
                        INSERT INTO jv_documents (
                            id, deal_id, partner_id, filename, original_filename,
                            file_type, file_size, file_path, document_type,
                            description, version, is_current_version, uploaded_by, 
                            shared_with_partner, requires_signature, signature_status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        document_id, deal_id, partner_id, secure_fname, file.filename,
                        file.content_type, file_size, file_path, document_type,
                        description, next_version, True, uploaded_by, share_with_partner,
                        requires_signature, signature_status
                    ))
                    
                    # Log upload action
                    self._log_access(document_id, uploaded_by, 'admin', 'uploaded', conn)
                    
                    conn.commit()
                    logging.info(f"Document uploaded: {document_id} (version {next_version})")
                    return document_id
                    
        except Exception as e:
            logging.error(f"Error uploading document: {e}")
            # Clean up file if database insert fails
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            raise
    
    def get_deal_documents(self, deal_id: str, partner_id: str = None, partner_view: bool = False) -> List[Dict]:
        """
        Get all documents for a deal
        If partner_view=True, only return documents shared with partner
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    if partner_view:
                        # Partner view - only shared documents
                        cur.execute("""
                            SELECT 
                                id, deal_id, partner_id, original_filename, file_type,
                                file_size, document_type, description, version,
                                is_current_version, uploaded_at, shared_with_partner,
                                partner_viewed_at, partner_signed_at, requires_signature,
                                signature_status, created_at
                            FROM jv_documents
                            WHERE deal_id = %s AND partner_id = %s 
                            AND shared_with_partner = true
                            AND is_current_version = true
                            ORDER BY uploaded_at DESC
                        """, (deal_id, partner_id))
                    else:
                        # Admin view - all documents
                        cur.execute("""
                            SELECT *
                            FROM jv_documents
                            WHERE deal_id = %s AND is_current_version = true
                            ORDER BY uploaded_at DESC
                        """, (deal_id,))
                    
                    documents = []
                    for row in cur.fetchall():
                        doc = dict(row)
                        # Format dates
                        for date_field in ['uploaded_at', 'partner_viewed_at', 'partner_signed_at', 'created_at', 'updated_at']:
                            if doc.get(date_field):
                                doc[date_field] = doc[date_field].isoformat()
                        documents.append(doc)
                    
                    return documents
                    
        except Exception as e:
            logging.error(f"Error getting deal documents: {e}")
            return []
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict]:
        """Get document by ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("SELECT * FROM jv_documents WHERE id = %s", (document_id,))
                    result = cur.fetchone()
                    
                    if result:
                        doc = dict(result)
                        # Format dates
                        for date_field in ['uploaded_at', 'partner_viewed_at', 'partner_signed_at', 'created_at', 'updated_at']:
                            if doc.get(date_field):
                                doc[date_field] = doc[date_field].isoformat()
                        return doc
                    return None
                    
        except Exception as e:
            logging.error(f"Error getting document by ID: {e}")
            return None
    
    def share_document_with_partner(self, document_id: str, admin_email: str, ip_address: str = None, user_agent: str = None) -> bool:
        """Share a document with the partner"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE jv_documents
                        SET shared_with_partner = true, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (document_id,))
                    
                    # AUDIT FIX: Log share action with full context
                    self._log_access(document_id, admin_email, 'admin', 'shared', conn, ip_address, user_agent)
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logging.error(f"Error sharing document: {e}")
            return False
    
    def mark_document_viewed(self, document_id: str, partner_email: str, ip_address: str = None, user_agent: str = None) -> bool:
        """Mark document as viewed by partner"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE jv_documents
                        SET partner_viewed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND partner_viewed_at IS NULL
                    """, (document_id,))
                    
                    # Log view action
                    self._log_access(document_id, partner_email, 'partner', 'viewed', conn, ip_address, user_agent)
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logging.error(f"Error marking document viewed: {e}")
            return False
    
    def mark_document_signed(self, document_id: str, partner_email: str, ip_address: str = None) -> bool:
        """Mark document as signed by partner"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE jv_documents
                        SET 
                            partner_signed_at = CURRENT_TIMESTAMP,
                            signature_status = 'signed',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (document_id,))
                    
                    # Log sign action
                    self._log_access(document_id, partner_email, 'partner', 'signed', conn, ip_address)
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logging.error(f"Error marking document signed: {e}")
            return False
    
    def delete_document(self, document_id: str, admin_email: str, ip_address: str = None, user_agent: str = None) -> bool:
        """Delete a document (soft delete by marking as not current)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get file path before deletion
                    cur.execute("SELECT file_path FROM jv_documents WHERE id = %s", (document_id,))
                    result = cur.fetchone()
                    
                    if result:
                        file_path = result[0]
                        
                        # Mark as not current version (soft delete)
                        cur.execute("""
                            UPDATE jv_documents
                            SET is_current_version = false, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (document_id,))
                        
                        # AUDIT FIX: Log delete action with full context
                        self._log_access(document_id, admin_email, 'admin', 'deleted', conn, ip_address, user_agent)
                        
                        # Delete physical file
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        
                        conn.commit()
                        return True
                    return False
                    
        except Exception as e:
            logging.error(f"Error deleting document: {e}")
            return False
    
    def get_document_access_log(self, document_id: str, limit: int = 50) -> List[Dict]:
        """Get access log for a document"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT *
                        FROM document_access_log
                        WHERE document_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (document_id, limit))
                    
                    logs = []
                    for row in cur.fetchall():
                        log = dict(row)
                        if log.get('created_at'):
                            log['created_at'] = log['created_at'].isoformat()
                        logs.append(log)
                    
                    return logs
                    
        except Exception as e:
            logging.error(f"Error getting document access log: {e}")
            return []
    
    def _log_access(
        self,
        document_id: str,
        user_email: str,
        user_type: str,
        action: str,
        conn,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Internal method to log document access"""
        try:
            with conn.cursor() as cur:
                log_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO document_access_log (
                        id, document_id, user_email, user_type, action,
                        ip_address, user_agent
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (log_id, document_id, user_email, user_type, action, ip_address, user_agent))
                
        except Exception as e:
            logging.error(f"Error logging document access: {e}")
            # Don't raise - access logging shouldn't break the main operation

# Initialize service
jv_doc_service = JVDocumentService(
    database_url=os.environ.get('DATABASE_URL'),
    upload_folder=os.path.join(os.getcwd(), 'jv_documents')
)
