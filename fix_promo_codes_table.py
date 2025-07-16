#!/usr/bin/env python3
"""
Fix promo codes table UUID default issue
"""

import os
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def fix_promo_codes_table():
    """Fix the promo codes table to auto-generate UUIDs"""
    
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        print("DATABASE_URL not found")
        return
    
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Add UUID default to existing table
            conn.execute(text("ALTER TABLE promo_codes ALTER COLUMN id SET DEFAULT gen_random_uuid();"))
            print("✓ Fixed promo_codes table - UUID default added")
            
            # Also fix affiliates table if needed
            conn.execute(text("ALTER TABLE affiliates ALTER COLUMN id SET DEFAULT gen_random_uuid();"))
            print("✓ Fixed affiliates table - UUID default added")
            
            conn.commit()
            print("✓ Database fixes committed successfully")
            
    except Exception as e:
        print(f"Error fixing database: {e}")

if __name__ == "__main__":
    fix_promo_codes_table()