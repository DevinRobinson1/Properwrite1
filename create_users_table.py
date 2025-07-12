#!/usr/bin/env python3
"""
Create basic users table for affiliate foreign key relationships
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

def create_users_table():
    """Create basic users table if it doesn't exist"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if users table exists
        result = session.execute(text("SELECT to_regclass('users');"))
        exists = result.scalar()
        
        if not exists:
            print("Creating users table...")
            session.execute(text("""
                CREATE TABLE users (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255),
                    team_id VARCHAR(36),
                    team_role VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT true
                );
            """))
            session.commit()
            print("✓ Users table created successfully")
        else:
            print("Users table already exists")
            
    except Exception as e:
        print(f"Error creating users table: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_users_table()