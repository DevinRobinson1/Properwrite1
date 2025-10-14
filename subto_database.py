"""
Subject-To Lead Submission Database Service
Handles submitter accounts and lead tracking
"""
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class SubToDatabase:
    def __init__(self):
        self.database_url = os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Initialize tables on startup
        self.initialize_tables()
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def initialize_tables(self):
        """Initialize database tables for Subject-To leads"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Create submitters table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS subto_submitters (
                            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                            email TEXT UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL,
                            name TEXT NOT NULL,
                            company TEXT,
                            phone TEXT,
                            is_active BOOLEAN DEFAULT true,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_login TIMESTAMP
                        )
                    """)
                    
                    # Create subto_leads table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS subto_leads (
                            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                            submitter_id TEXT NOT NULL REFERENCES subto_submitters(id),
                            seller_name TEXT NOT NULL,
                            property_address TEXT NOT NULL,
                            seller_phone TEXT NOT NULL,
                            loan_balance DECIMAL(12, 2),
                            interest_rate DECIMAL(5, 2),
                            monthly_payment DECIMAL(10, 2),
                            arrears DECIMAL(10, 2) DEFAULT 0,
                            cash_to_seller DECIMAL(10, 2) DEFAULT 0,
                            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'reviewing', 'approved', 'declined', 'closed')),
                            admin_notes TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes for performance
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_subto_submitters_email ON subto_submitters(email)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_subto_leads_submitter_id ON subto_leads(submitter_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_subto_leads_status ON subto_leads(status)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_subto_leads_created_at ON subto_leads(created_at DESC)")
                    
                    logging.info("Subject-To database tables initialized successfully")
                    
        except Exception as e:
            logging.error(f"Error initializing Subject-To tables: {e}")
            raise
    
    def create_submitter(self, email: str, password: str, name: str, company: str = None, phone: str = None) -> Optional[str]:
        """
        Create new submitter account
        Returns submitter_id or None if email already exists
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if email already exists
                    cur.execute("SELECT id FROM subto_submitters WHERE email = %s", (email.lower(),))
                    if cur.fetchone():
                        return None
                    
                    # Create new submitter
                    submitter_id = str(uuid.uuid4())
                    password_hash = generate_password_hash(password)
                    
                    cur.execute("""
                        INSERT INTO subto_submitters (id, email, password_hash, name, company, phone)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (submitter_id, email.lower(), password_hash, name, company or '', phone or ''))
                    
                    logging.info(f"Created new submitter: {email}")
                    return submitter_id
                    
        except Exception as e:
            logging.error(f"Error creating submitter: {e}")
            raise
    
    def authenticate_submitter(self, email: str, password: str) -> Optional[Dict]:
        """
        Authenticate submitter and return submitter data
        Updates last_login on successful auth
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, email, password_hash, name, company, phone, is_active
                        FROM subto_submitters 
                        WHERE email = %s
                    """, (email.lower(),))
                    
                    submitter = cur.fetchone()
                    
                    if not submitter or not submitter['is_active']:
                        return None
                    
                    # Check password
                    if not check_password_hash(submitter['password_hash'], password):
                        return None
                    
                    # Update last login
                    cur.execute("""
                        UPDATE subto_submitters 
                        SET last_login = CURRENT_TIMESTAMP 
                        WHERE id = %s
                    """, (submitter['id'],))
                    
                    # Remove password hash from returned data
                    submitter_data = dict(submitter)
                    del submitter_data['password_hash']
                    
                    logging.info(f"Submitter authenticated: {email}")
                    return submitter_data
                    
        except Exception as e:
            logging.error(f"Error authenticating submitter: {e}")
            return None
    
    def get_submitter_by_id(self, submitter_id: str) -> Optional[Dict]:
        """Get submitter data by ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, email, name, company, phone
                        FROM subto_submitters 
                        WHERE id = %s AND is_active = true
                    """, (submitter_id,))
                    
                    submitter = cur.fetchone()
                    return dict(submitter) if submitter else None
                    
        except Exception as e:
            logging.error(f"Error getting submitter: {e}")
            return None
    
    def create_lead(self, submitter_id: str, lead_data: Dict) -> str:
        """
        Create new Subject-To lead
        Returns lead_id
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    lead_id = str(uuid.uuid4())
                    
                    cur.execute("""
                        INSERT INTO subto_leads (
                            id, submitter_id, seller_name, property_address, seller_phone,
                            loan_balance, interest_rate, monthly_payment, arrears, cash_to_seller
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        lead_id,
                        submitter_id,
                        lead_data.get('seller_name'),
                        lead_data.get('property_address'),
                        lead_data.get('seller_phone'),
                        lead_data.get('loan_balance'),
                        lead_data.get('interest_rate'),
                        lead_data.get('monthly_payment'),
                        lead_data.get('arrears', 0),
                        lead_data.get('cash_to_seller', 0)
                    ))
                    
                    logging.info(f"Created Subject-To lead: {lead_id}")
                    return lead_id
                    
        except Exception as e:
            logging.error(f"Error creating lead: {e}")
            raise
    
    def get_leads_by_submitter(self, submitter_id: str) -> List[Dict]:
        """Get all leads submitted by a specific submitter"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            id, seller_name, property_address, seller_phone,
                            loan_balance, interest_rate, monthly_payment, arrears, cash_to_seller,
                            status, created_at, updated_at
                        FROM subto_leads 
                        WHERE submitter_id = %s
                        ORDER BY created_at DESC
                    """, (submitter_id,))
                    
                    leads = cur.fetchall()
                    return [dict(lead) for lead in leads]
                    
        except Exception as e:
            logging.error(f"Error getting leads for submitter: {e}")
            return []
    
    def get_all_leads(self, status_filter: str = None) -> List[Dict]:
        """
        Get all leads for admin panel
        Optionally filter by status
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if status_filter:
                        cur.execute("""
                            SELECT 
                                l.id, l.seller_name, l.property_address, l.seller_phone,
                                l.loan_balance, l.interest_rate, l.monthly_payment, l.arrears, l.cash_to_seller,
                                l.status, l.admin_notes, l.created_at, l.updated_at,
                                s.name as submitter_name, s.email as submitter_email, s.company as submitter_company
                            FROM subto_leads l
                            JOIN subto_submitters s ON l.submitter_id = s.id
                            WHERE l.status = %s
                            ORDER BY l.created_at DESC
                        """, (status_filter,))
                    else:
                        cur.execute("""
                            SELECT 
                                l.id, l.seller_name, l.property_address, l.seller_phone,
                                l.loan_balance, l.interest_rate, l.monthly_payment, l.arrears, l.cash_to_seller,
                                l.status, l.admin_notes, l.created_at, l.updated_at,
                                s.name as submitter_name, s.email as submitter_email, s.company as submitter_company
                            FROM subto_leads l
                            JOIN subto_submitters s ON l.submitter_id = s.id
                            ORDER BY l.created_at DESC
                        """)
                    
                    leads = cur.fetchall()
                    return [dict(lead) for lead in leads]
                    
        except Exception as e:
            logging.error(f"Error getting all leads: {e}")
            return []
    
    def update_lead_status(self, lead_id: str, status: str, admin_notes: str = None) -> bool:
        """Update lead status and optional admin notes"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE subto_leads 
                        SET status = %s, admin_notes = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (status, admin_notes, lead_id))
                    
                    logging.info(f"Updated lead {lead_id} status to {status}")
                    return True
                    
        except Exception as e:
            logging.error(f"Error updating lead status: {e}")
            return False
    
    def get_lead_by_id(self, lead_id: str) -> Optional[Dict]:
        """Get full lead details by ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            l.*,
                            s.name as submitter_name, s.email as submitter_email, 
                            s.company as submitter_company, s.phone as submitter_phone
                        FROM subto_leads l
                        JOIN subto_submitters s ON l.submitter_id = s.id
                        WHERE l.id = %s
                    """, (lead_id,))
                    
                    lead = cur.fetchone()
                    return dict(lead) if lead else None
                    
        except Exception as e:
            logging.error(f"Error getting lead by ID: {e}")
            return None

# Initialize database on import
subto_db = SubToDatabase()
