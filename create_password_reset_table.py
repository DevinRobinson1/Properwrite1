"""
Create password reset tokens table
Run this script to create the password_reset_tokens table
"""

from main import app, db
from models import PasswordResetToken

def create_password_reset_table():
    """Create the password_reset_tokens table"""
    try:
        with app.app_context():
            # Create the table
            db.create_all()
            print("✅ Password reset tokens table created successfully!")
            
            # Verify table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'password_reset_tokens' in tables:
                print("✅ Table 'password_reset_tokens' confirmed in database")
                
                # Show table structure
                columns = inspector.get_columns('password_reset_tokens')
                print("\n📋 Table structure:")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            else:
                print("❌ Table 'password_reset_tokens' not found in database")
                
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")

if __name__ == "__main__":
    create_password_reset_table()