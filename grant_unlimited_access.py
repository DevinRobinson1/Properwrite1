#!/usr/bin/env python3
"""
Grant unlimited access to devin@pfpsolutions.us
Creates user with unlimited credits and team access
"""

import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def grant_unlimited_access():
    """Grant unlimited access to devin@pfpsolutions.us"""
    try:
        # Database connection
        DATABASE_URL = os.environ.get("DATABASE_URL")
        if not DATABASE_URL:
            logger.error("DATABASE_URL environment variable not set")
            return
        
        engine = create_engine(DATABASE_URL)
        
        # Generate UUIDs for team and user
        team_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Check if user already exists
                existing_user = conn.execute(
                    text("SELECT id, email, name, team_id FROM users WHERE email = :email"),
                    {"email": "devin@pfpsolutions.us"}
                ).first()
                
                if existing_user:
                    logger.info("User devin@pfpsolutions.us already exists, updating team to unlimited access")
                    
                    # Update existing user's team to unlimited
                    conn.execute(
                        text("UPDATE teams SET tier = 'growth10', seats_max = 999999, credit_balance = 999999 WHERE id = :team_id"),
                        {"team_id": existing_user.team_id}
                    )
                    
                    # Update user info
                    conn.execute(
                        text("UPDATE users SET name = :name, is_active = true WHERE id = :user_id"),
                        {"name": "Devin (PFP Solutions)", "user_id": existing_user.id}
                    )
                    
                    logger.info("✓ Updated existing user with unlimited access")
                    
                else:
                    logger.info("Creating new user devin@pfpsolutions.us with unlimited access")
                    
                    # Create unlimited team
                    conn.execute(
                        text("""
                            INSERT INTO teams (id, name, tier, seats_max, credit_balance, created_at) 
                            VALUES (:team_id, :name, :tier, :seats_max, :credit_balance, :created_at)
                        """),
                        {
                            "team_id": team_id,
                            "name": "Devin's Unlimited Team",
                            "tier": "growth10",
                            "seats_max": 999999,
                            "credit_balance": 999999,
                            "created_at": datetime.utcnow()
                        }
                    )
                    
                    # Create user with unlimited access
                    conn.execute(
                        text("""
                            INSERT INTO users (id, email, name, team_id, role, is_active, created_at) 
                            VALUES (:user_id, :email, :name, :team_id, :role, :is_active, :created_at)
                        """),
                        {
                            "user_id": user_id,
                            "email": "devin@pfpsolutions.us",
                            "name": "Devin (PFP Solutions)",
                            "team_id": team_id,
                            "role": "owner",
                            "is_active": True,
                            "created_at": datetime.utcnow()
                        }
                    )
                    
                    logger.info("✓ Created new user with unlimited access")
                
                # Commit transaction
                trans.commit()
                
                # Verify the user was created/updated
                user = conn.execute(
                    text("SELECT u.id, u.email, u.name, u.role, t.tier, t.seats_max, t.credit_balance FROM users u JOIN teams t ON u.team_id = t.id WHERE u.email = :email"),
                    {"email": "devin@pfpsolutions.us"}
                ).first()
                
                if user:
                    logger.info(f"✓ User verified: {user.email}")
                    logger.info(f"  - Name: {user.name}")
                    logger.info(f"  - Role: {user.role}")
                    logger.info(f"  - Team Tier: {user.tier}")
                    logger.info(f"  - Max Seats: {user.seats_max}")
                    logger.info(f"  - Credit Balance: {user.credit_balance}")
                else:
                    logger.error("❌ User verification failed")
                    
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        logger.error(f"Error granting unlimited access: {str(e)}")
        raise

if __name__ == "__main__":
    grant_unlimited_access()