"""
Check the actual structure of the users table
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

with engine.connect() as conn:
    # Get table structure
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """))
    
    print("Users table structure:")
    print("-" * 80)
    print(f"{'Column':<20} {'Type':<20} {'Nullable':<10} {'Default':<20}")
    print("-" * 80)
    for row in result:
        print(f"{row[0]:<20} {row[1]:<20} {row[2]:<10} {str(row[3] or ''):<20}")
    
    # Check if there are any users
    print("\nExisting users:")
    result = conn.execute(text("SELECT id, email, name, role FROM users LIMIT 10"))
    for row in result:
        print(f"- ID: {row[0]}, Email: {row[1]}, Name: {row[2]}, Role: {row[3]}")