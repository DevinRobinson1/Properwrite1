"""
Add missing columns to users table
"""
import os
from sqlalchemy import create_engine, text

# Get database URL
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in environment variables")
    exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

# Add missing columns
with engine.connect() as conn:
    try:
        # Check which columns exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """))
        existing_columns = [row[0] for row in result]
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns
        columns_to_add = [
            ("credits", "INTEGER DEFAULT 4"),
            ("subscription_tier", "VARCHAR(50) DEFAULT 'free'"),
            ("subscription_status", "VARCHAR(50) DEFAULT 'active'"),
            ("unlimited_credits", "BOOLEAN DEFAULT FALSE"),
            ("total_credits_used", "INTEGER DEFAULT 0"),
            ("last_login", "TIMESTAMP WITH TIME ZONE"),
            ("is_active", "BOOLEAN DEFAULT TRUE")
        ]
        
        for column_name, column_def in columns_to_add:
            if column_name not in existing_columns:
                print(f"Adding column: {column_name}")
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"))
                conn.commit()
            else:
                print(f"Column already exists: {column_name}")
                
        print("\nAll columns added successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()