#!/usr/bin/env python3
"""
Check user credits and apply missing promo code credits if needed
"""

import os
import logging
from billing_service import BillingService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_fix_user_credits(email_address, expected_promo_code="subto25", expected_credits=25):
    """Check user credits and apply missing promo code credits"""
    try:
        # Initialize Flask app context
        from app_upgraded import app
        
        with app.app_context():
            billing_service = BillingService()
            
            # Get user and team info
            with billing_service.db_session() as db:
                from billing_models import User, Team
                
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
                logger.info(f"Current credit balance: {team.credit_balance}")
                logger.info(f"Plan tier: {team.tier}")
                
                # Check if user should have promo code credits
                if expected_promo_code == "subto25":
                    # Check if user already has the bonus credits applied
                    from billing_models import CreditLog
                    promo_log = db.query(CreditLog).filter_by(
                        team_id=user.team_id,
                        reason=f'promo-{expected_promo_code}'
                    ).first()
                    
                    if promo_log:
                        logger.info(f"Promo code '{expected_promo_code}' already applied - {promo_log.delta} credits added on {promo_log.created_at}")
                        return True
                    else:
                        logger.warning(f"Promo code '{expected_promo_code}' not found in credit logs - applying missing credits")
                        
                        # Add missing credits
                        team.credit_balance = (team.credit_balance or 0) + expected_credits
                        
                        # Log the credit addition
                        credit_log = CreditLog(
                            team_id=user.team_id,
                            user_id=user.id,
                            delta=expected_credits,
                            reason=f'promo-{expected_promo_code}-manual-fix'
                        )
                        db.add(credit_log)
                        db.commit()
                        
                        logger.info(f"Successfully added {expected_credits} credits for promo code '{expected_promo_code}'")
                        logger.info(f"New credit balance: {team.credit_balance}")
                        return True
                
    except Exception as e:
        logger.error(f"Error checking user credits: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Check and fix credits for specific user
    target_email = "drrobinson37@gmail.com"
    success = check_and_fix_user_credits(target_email, "subto25", 25)
    
    if success:
        print(f"✅ Credits checked and fixed for {target_email}")
    else:
        print(f"❌ Failed to check/fix credits for {target_email}")