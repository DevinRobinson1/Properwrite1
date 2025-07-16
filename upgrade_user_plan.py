#!/usr/bin/env python3
"""
Upgrade user plan from starter to pro for users who should have pro plan
"""

import os
import logging
from billing_service import BillingService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade_user_to_pro_plan(email_address):
    """Upgrade specific user to pro plan"""
    try:
        # Initialize Flask app context
        from app_upgraded import app
        
        with app.app_context():
            billing_service = BillingService()
            
            with billing_service.db_session() as db:
                from billing_models import User, Team, CreditLog, TIER_CONFIG
                
                user = db.query(User).filter_by(email=email_address).first()
                if not user:
                    logger.error(f"User not found: {email_address}")
                    return False
                    
                team = db.query(Team).filter_by(id=user.team_id).first()
                if not team:
                    logger.error(f"Team not found for user: {email_address}")
                    return False
                    
                logger.info(f"User: {user.name} ({user.email})")
                logger.info(f"Team: {team.name}")
                logger.info(f"Current tier: {team.tier}")
                logger.info(f"Current credit balance: {team.credit_balance}")
                
                # Upgrade to pro plan
                old_tier = team.tier
                team.tier = 'pro'
                
                # Set pro plan credits (300 credits per month)
                pro_credits = TIER_CONFIG['pro']['monthly_credits']
                team.credit_balance = pro_credits
                
                # Log the tier change
                credit_log = CreditLog(
                    team_id=user.team_id,
                    user_id=user.id,
                    delta=pro_credits,
                    reason=f'tier-upgrade-{old_tier}-to-pro'
                )
                db.add(credit_log)
                db.commit()
                
                logger.info(f"Successfully upgraded user from '{old_tier}' to 'pro'")
                logger.info(f"New credit balance: {team.credit_balance}")
                return True
                
    except Exception as e:
        logger.error(f"Error upgrading user plan: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Upgrade specific user
    target_email = "drrobinson37@gmail.com"
    success = upgrade_user_to_pro_plan(target_email)
    
    if success:
        print(f"✅ User {target_email} upgraded to Pro plan successfully")
    else:
        print(f"❌ Failed to upgrade user {target_email} to Pro plan")