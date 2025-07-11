#!/usr/bin/env python3
"""
Initialize test user data for dashboard functionality
"""
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from billing_models import User, Team, CreditLog

# Load environment variables
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment variables")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

def init_test_user():
    """Initialize test user and team data"""
    try:
        with Session(engine) as db:
            # Test user data from the session
            test_user_id = 'bfac25c4-7081-4eb6-8895-5dc09bb56d0a'
            test_email = 'devin@pfpsolutions.us'
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.id == test_user_id).first()
            if existing_user:
                print(f"User {test_email} already exists")
                return
            
            # Create a team first
            team = Team(
                name="PFP Solutions Team",
                tier="pro",
                seats_max=5,
                credit_balance=1000,
                is_active=True
            )
            db.add(team)
            db.flush()  # Get the team ID
            
            # Create the test user
            user = User(
                id=test_user_id,
                email=test_email,
                name="Devin Robinson",
                role="owner",
                team_id=team.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(user)
            
            # Add some initial credit log entries
            credit_log = CreditLog(
                team_id=team.id,
                user_id=test_user_id,
                delta=1000,
                reason="Initial credits",
                created_at=datetime.utcnow()
            )
            db.add(credit_log)
            
            db.commit()
            print(f"Successfully created test user: {test_email}")
            print(f"Team: {team.name} (ID: {team.id})")
            print(f"Credits: {team.credit_balance}")
            
    except Exception as e:
        print(f"Error creating test user: {e}")
        raise

if __name__ == "__main__":
    init_test_user()