#!/usr/bin/env python3
"""
Script to verify user credit balances
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from billing_service import BillingService
from sqlalchemy.orm import Session
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_user_credits(email: str):
    """Check a user's current credit balance"""
    try:
        billing_service = BillingService()
        
        with billing_service.db_session() as db:
            from billing_models import User, Team
            
            # Find the user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                logger.error(f"❌ User not found: {email}")
                return None
            
            # Get the team
            team = db.query(Team).filter(Team.id == user.team_id).first()
            if not team:
                logger.error(f"❌ Team not found for user: {email}")
                return None
                
            logger.info(f"✅ {email}")
            logger.info(f"   Team: {team.name}")
            logger.info(f"   Credits: {team.credit_balance}")
            logger.info(f"   Plan: {team.tier}")
            
            return team.credit_balance
            
    except Exception as e:
        logger.error(f"❌ Error checking credits for {email}: {e}")
        return None

def main():
    """Main function to verify both users' credits"""
    
    users_to_check = [
        "brandon@sharperprocess.com",
        "brandon@simplestephomes.com"
    ]
    
    logger.info("🔍 Verifying user credit balances...")
    
    for email in users_to_check:
        balance = check_user_credits(email)
        print("-" * 50)
    
    logger.info("✅ Verification complete!")

if __name__ == "__main__":
    main()