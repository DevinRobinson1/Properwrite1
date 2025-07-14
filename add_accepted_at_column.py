#!/usr/bin/env python3
"""
Add accepted_at column to team_invites table
"""

import os
import psycopg2
from datetime import datetime

def add_accepted_at_column():
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            print("DATABASE_URL environment variable not set")
            return
        
        # Connect to the database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'team_invites' 
            AND column_name = 'accepted_at'
        """)
        
        existing_column = cursor.fetchone()
        
        if existing_column:
            print("Column 'accepted_at' already exists in team_invites table")
            return
        
        # Add the accepted_at column
        cursor.execute("""
            ALTER TABLE team_invites 
            ADD COLUMN accepted_at TIMESTAMP WITH TIME ZONE
        """)
        
        conn.commit()
        print("Successfully added 'accepted_at' column to team_invites table")
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_accepted_at_column()