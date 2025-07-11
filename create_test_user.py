"""
Create a test user for admin dashboard verification
"""
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User

# Get database URL
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in environment variables")
    sys.exit(1)

# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Create a test user
    test_user = User(
        email="test@properwrite.com",
        name="Test User",
        credits=50,
        subscription_tier="pro",
        subscription_status="active",
        total_credits_used=25,
        created_at=datetime.utcnow()
    )
    
    # Check if user already exists
    existing_user = session.query(User).filter_by(email="test@properwrite.com").first()
    if existing_user:
        print(f"User already exists: {existing_user.email} (ID: {existing_user.id})")
    else:
        session.add(test_user)
        session.commit()
        print(f"Created test user: {test_user.email} (ID: {test_user.id})")
    
    # List all users
    print("\nAll users in database:")
    users = session.query(User).all()
    for user in users:
        print(f"- {user.email} (ID: {user.id}, Tier: {user.subscription_tier}, Credits: {user.credits})")
    
except Exception as e:
    print(f"Error: {e}")
    session.rollback()
finally:
    session.close()