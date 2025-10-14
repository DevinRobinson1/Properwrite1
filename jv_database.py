"""
JV Partnership Database Models and Setup
PostgreSQL database schema for partner profiles and deal management
"""
import psycopg2
import psycopg2.extras
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import uuid

class JVDatabase:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
        
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Create partners table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS partners (
                            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                            name TEXT NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            phone TEXT NOT NULL,
                            company TEXT,
                            markets TEXT[] NOT NULL DEFAULT '{}',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create jv_deals table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS jv_deals (
                            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                            partner_id TEXT NOT NULL REFERENCES partners(id),
                            deal_json JSONB NOT NULL,
                            auto_status TEXT NOT NULL CHECK (auto_status IN ('approved', 'denied')),
                            final_status TEXT CHECK (final_status IN ('approved', 'denied')),
                            reasons TEXT[] DEFAULT '{}',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes for performance
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_partners_email ON partners(email)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_deals_partner_id ON jv_deals(partner_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_deals_created_at ON jv_deals(created_at)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_deals_auto_status ON jv_deals(auto_status)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_deals_final_status ON jv_deals(final_status)")
                    
                    # Add composite indices for enhanced filtering
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_deals_state ON jv_deals ((deal_json->>'property_state'))")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_deals_city ON jv_deals ((deal_json->>'property_city'))")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_deals_zip ON jv_deals ((deal_json->>'property_zip'))")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_deals_partner_status ON jv_deals(partner_id, final_status)")
                    
                    # Add additional fields to jv_deals for better querying
                    cur.execute("ALTER TABLE jv_deals ADD COLUMN IF NOT EXISTS submitted_by TEXT")
                    cur.execute("ALTER TABLE jv_deals ADD COLUMN IF NOT EXISTS admin_notes TEXT")
                    cur.execute("ALTER TABLE jv_deals ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    
                    # Add contract and buyer tracking fields
                    cur.execute("ALTER TABLE jv_deals ADD COLUMN IF NOT EXISTS has_contract BOOLEAN DEFAULT false")
                    cur.execute("ALTER TABLE jv_deals ADD COLUMN IF NOT EXISTS contract_date DATE")
                    cur.execute("ALTER TABLE jv_deals ADD COLUMN IF NOT EXISTS contract_notes TEXT")
                    cur.execute("ALTER TABLE jv_deals ADD COLUMN IF NOT EXISTS has_buyer BOOLEAN DEFAULT false")
                    cur.execute("ALTER TABLE jv_deals ADD COLUMN IF NOT EXISTS buyer_name TEXT")
                    cur.execute("ALTER TABLE jv_deals ADD COLUMN IF NOT EXISTS down_payment DECIMAL(12,2)")
                    cur.execute("ALTER TABLE jv_deals ADD COLUMN IF NOT EXISTS buyer_notes TEXT")
                    
                    # Ensure phone_number is not nullable in partners table
                    cur.execute("ALTER TABLE partners ALTER COLUMN phone SET NOT NULL")
                    
                    # Create jv_documents table for secure document management
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS jv_documents (
                            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                            deal_id TEXT NOT NULL REFERENCES jv_deals(id) ON DELETE CASCADE,
                            partner_id TEXT NOT NULL REFERENCES partners(id),
                            filename TEXT NOT NULL,
                            original_filename TEXT NOT NULL,
                            file_type TEXT NOT NULL,
                            file_size INTEGER NOT NULL,
                            file_path TEXT NOT NULL,
                            document_type TEXT NOT NULL CHECK (document_type IN (
                                'agreement', 'contract', 'addendum', 'inspection', 
                                'appraisal', 'title', 'insurance', 'other'
                            )),
                            description TEXT,
                            version INTEGER DEFAULT 1,
                            is_current_version BOOLEAN DEFAULT true,
                            uploaded_by TEXT NOT NULL,
                            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            shared_with_partner BOOLEAN DEFAULT false,
                            partner_viewed_at TIMESTAMP,
                            partner_signed_at TIMESTAMP,
                            requires_signature BOOLEAN DEFAULT false,
                            signature_status TEXT CHECK (signature_status IN (
                                'not_required', 'pending', 'signed', 'declined'
                            )) DEFAULT 'not_required',
                            metadata JSONB DEFAULT '{}'::jsonb,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Add notes column for additional context
                    cur.execute("""
                        ALTER TABLE jv_documents 
                        ADD COLUMN IF NOT EXISTS notes TEXT
                    """)
                    
                    # Create document_access_log table for audit trail
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS document_access_log (
                            id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                            document_id TEXT NOT NULL REFERENCES jv_documents(id) ON DELETE CASCADE,
                            user_email TEXT NOT NULL,
                            user_type TEXT NOT NULL CHECK (user_type IN ('admin', 'partner')),
                            action TEXT NOT NULL CHECK (action IN (
                                'uploaded', 'viewed', 'downloaded', 'shared', 
                                'signed', 'deleted', 'updated'
                            )),
                            ip_address TEXT,
                            user_agent TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes for document management
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_documents_deal_id ON jv_documents(deal_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_documents_partner_id ON jv_documents(partner_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_documents_type ON jv_documents(document_type)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_documents_uploaded_at ON jv_documents(uploaded_at)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_jv_documents_version ON jv_documents(deal_id, version, is_current_version)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_document_access_log_document_id ON document_access_log(document_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_document_access_log_created_at ON document_access_log(created_at)")
                    
                    conn.commit()
                    logging.info("Database tables initialized successfully")
                    
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            raise
    
    def create_or_get_partner(self, name: str, email: str, phone: str, company: str = None, markets: List[str] = None) -> str:
        """
        Create new partner or get existing partner ID by email
        Returns partner_id
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if partner exists
                    cur.execute("SELECT id FROM partners WHERE email = %s", (email.lower(),))
                    result = cur.fetchone()
                    
                    if result:
                        partner_id = result[0]
                        # Update existing partner info
                        cur.execute("""
                            UPDATE partners 
                            SET name = %s, phone = %s, company = %s, markets = %s
                            WHERE id = %s
                        """, (name, phone, company or '', markets or [], partner_id))
                        logging.info(f"Updated existing partner: {email}")
                        return partner_id
                    else:
                        # Create new partner
                        partner_id = str(uuid.uuid4())
                        cur.execute("""
                            INSERT INTO partners (id, name, email, phone, company, markets)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (partner_id, name, email.lower(), phone, company or '', markets or []))
                        logging.info(f"Created new partner: {email}")
                        return partner_id
                        
        except Exception as e:
            logging.error(f"Error creating/getting partner: {e}")
            raise
    
    def create_deal_submission(self, partner_id: str, deal_data: Dict, auto_status: str, reasons: List[str] = None) -> str:
        """
        Create new deal submission
        Returns deal_id
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    deal_id = str(uuid.uuid4())
                    cur.execute("""
                        INSERT INTO jv_deals (id, partner_id, deal_json, auto_status, reasons)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (deal_id, partner_id, json.dumps(deal_data), auto_status, reasons or []))
                    
                    logging.info(f"Created deal submission: {deal_id}")
                    return deal_id
                    
        except Exception as e:
            logging.error(f"Error creating deal submission: {e}")
            raise
    
    def get_partner_stats(self, partner_id: str) -> Dict:
        """Get partner statistics"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(*) FILTER (WHERE auto_status='approved') as approved,
                            DATE(MAX(created_at)) as last_date
                        FROM jv_deals
                        WHERE partner_id = %s
                    """, (partner_id,))
                    
                    result = cur.fetchone()
                    if result:
                        total, approved, last_date = result
                        return {
                            'total_deals': total or 0,
                            'approved_deals': approved or 0,
                            'approval_rate': (approved / total * 100) if total > 0 else 0,
                            'last_deal_date': last_date.isoformat() if last_date else None
                        }
                    return {'total_deals': 0, 'approved_deals': 0, 'approval_rate': 0, 'last_deal_date': None}
                    
        except Exception as e:
            logging.error(f"Error getting partner stats: {e}")
            return {'total_deals': 0, 'approved_deals': 0, 'approval_rate': 0, 'last_deal_date': None}
    
    def get_all_partners(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get all partners with their stats"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            p.id, p.name, p.email, p.phone, p.company, p.markets, p.created_at,
                            COUNT(d.id) as total_deals,
                            COUNT(d.id) FILTER (WHERE d.auto_status='approved') as approved_deals,
                            MAX(d.created_at) as last_deal_date
                        FROM partners p
                        LEFT JOIN jv_deals d ON p.id = d.partner_id
                        GROUP BY p.id, p.name, p.email, p.phone, p.company, p.markets, p.created_at
                        ORDER BY p.created_at DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    
                    partners = []
                    for row in cur.fetchall():
                        partner = dict(row)
                        partner['approval_rate'] = (partner['approved_deals'] / partner['total_deals'] * 100) if partner['total_deals'] > 0 else 0
                        partners.append(partner)
                    
                    return partners
                    
        except Exception as e:
            logging.error(f"Error getting all partners: {e}")
            return []
    
    def get_partner_by_id(self, partner_id: str) -> Optional[Dict]:
        """Get partner by ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("SELECT * FROM partners WHERE id = %s", (partner_id,))
                    result = cur.fetchone()
                    return dict(result) if result else None
                    
        except Exception as e:
            logging.error(f"Error getting partner by ID: {e}")
            return None
    
    def get_partner_deals(self, partner_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get deals for a specific partner"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT id, deal_json, auto_status, final_status, reasons, created_at
                        FROM jv_deals
                        WHERE partner_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (partner_id, limit, offset))
                    
                    deals = []
                    for row in cur.fetchall():
                        deal = dict(row)
                        deal['deal_json'] = json.loads(deal['deal_json']) if deal['deal_json'] else {}
                        deals.append(deal)
                    
                    return deals
                    
        except Exception as e:
            logging.error(f"Error getting partner deals: {e}")
            return []
    
    def get_deal_by_id(self, deal_id: str) -> Optional[Dict]:
        """Get deal by ID with partner info"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT d.*, p.name as partner_name, p.email as partner_email
                        FROM jv_deals d
                        JOIN partners p ON d.partner_id = p.id
                        WHERE d.id = %s
                    """, (deal_id,))
                    
                    result = cur.fetchone()
                    if result:
                        deal = dict(result)
                        deal['deal_json'] = json.loads(deal['deal_json']) if deal['deal_json'] else {}
                        return deal
                    return None
                    
        except Exception as e:
            logging.error(f"Error getting deal by ID: {e}")
            return None
    
    def update_deal_final_status(self, deal_id: str, final_status: str) -> bool:
        """Update deal final status (admin approval/denial)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE jv_deals
                        SET final_status = %s
                        WHERE id = %s
                    """, (final_status, deal_id))
                    
                    return cur.rowcount > 0
                    
        except Exception as e:
            logging.error(f"Error updating deal final status: {e}")
            return False
    
    def update_contract_info(self, deal_id: str, has_contract: bool, contract_date: str = None, contract_notes: str = None) -> bool:
        """Update contract information for a deal"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE jv_deals
                        SET has_contract = %s, contract_date = %s, contract_notes = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (has_contract, contract_date, contract_notes, deal_id))
                    
                    return cur.rowcount > 0
                    
        except Exception as e:
            logging.error(f"Error updating contract info: {e}")
            return False
    
    def update_buyer_info(self, deal_id: str, has_buyer: bool, buyer_name: str = None, down_payment: float = None, buyer_notes: str = None) -> bool:
        """Update buyer information for a deal"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE jv_deals
                        SET has_buyer = %s, buyer_name = %s, down_payment = %s, buyer_notes = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (has_buyer, buyer_name, down_payment, buyer_notes, deal_id))
                    
                    return cur.rowcount > 0
                    
        except Exception as e:
            logging.error(f"Error updating buyer info: {e}")
            return False
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard overview statistics"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Total partners
                    cur.execute("SELECT COUNT(*) FROM partners")
                    total_partners = cur.fetchone()[0]
                    
                    # Deals last 30 days
                    cur.execute("""
                        SELECT COUNT(*) FROM jv_deals 
                        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    """)
                    deals_last_30_days = cur.fetchone()[0]
                    
                    # Auto-approval stats
                    cur.execute("""
                        SELECT 
                            COUNT(*) FILTER (WHERE auto_status='approved') as approved,
                            COUNT(*) FILTER (WHERE auto_status='denied') as denied
                        FROM jv_deals
                        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    """)
                    result = cur.fetchone()
                    approved, denied = result if result else (0, 0)
                    
                    return {
                        'total_partners': total_partners,
                        'deals_last_30_days': deals_last_30_days,
                        'auto_approved': approved,
                        'auto_denied': denied,
                        'approval_rate': (approved / (approved + denied) * 100) if (approved + denied) > 0 else 0
                    }
                    
        except Exception as e:
            logging.error(f"Error getting dashboard stats: {e}")
            return {
                'total_partners': 0,
                'deals_last_30_days': 0,
                'auto_approved': 0,
                'auto_denied': 0,
                'approval_rate': 0
            }

# Create global instance
jv_db = JVDatabase()

# Initialize database on import
try:
    jv_db.init_database()
    logging.info("JV Database initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize JV Database: {e}")