#!/usr/bin/env python3
"""
Fix plan display inconsistencies system-wide
"""

import os
import logging
from billing_service import BillingService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_plan_display_system_wide():
    """Fix plan display for all users"""
    try:
        # Initialize Flask app context
        from app_upgraded import app
        
        with app.app_context():
            billing_service = BillingService()
            
            with billing_service.db_session() as db:
                from billing_models import Team, User
                
                # Get all teams
                teams = db.query(Team).all()
                
                logger.info(f"Found {len(teams)} teams to check")
                
                for team in teams:
                    # Check current tier
                    current_tier = team.tier
                    logger.info(f"Team: {team.name}, Current tier: {current_tier}")
                    
                    # Get team members
                    members = db.query(User).filter_by(team_id=team.id).all()
                    for member in members:
                        logger.info(f"  Member: {member.name} ({member.email})")
                    
                    # Fix common plan naming issues
                    if current_tier and current_tier.lower() in ['starter', 'free']:
                        # Check if team actually has more credits indicating higher plan
                        if team.credit_balance and team.credit_balance >= 300:
                            logger.warning(f"Team {team.name} has {team.credit_balance} credits but tier is '{current_tier}' - likely should be 'pro'")
                            team.tier = 'pro'
                            db.commit()
                            logger.info(f"Updated team {team.name} from '{current_tier}' to 'pro'")
                        elif team.credit_balance and team.credit_balance >= 100:
                            logger.warning(f"Team {team.name} has {team.credit_balance} credits but tier is '{current_tier}' - likely should be 'individual'")
                            team.tier = 'individual'
                            db.commit()
                            logger.info(f"Updated team {team.name} from '{current_tier}' to 'individual'")
                
                logger.info("Plan display fix completed")
                return True
                
    except Exception as e:
        logger.error(f"Error fixing plan display: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def check_specific_user_plan(email_address):
    """Check and fix plan for specific user"""
    try:
        # Initialize Flask app context
        from app_upgraded import app
        
        with app.app_context():
            billing_service = BillingService()
            
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
                logger.info(f"Current tier: {team.tier}")
                logger.info(f"Credit balance: {team.credit_balance}")
                
                # Check if plan needs to be corrected
                if team.credit_balance >= 300 and team.tier != 'pro':
                    logger.warning(f"Team has {team.credit_balance} credits but tier is '{team.tier}' - updating to 'pro'")
                    team.tier = 'pro'
                    db.commit()
                    logger.info(f"Updated team tier to 'pro'")
                    
                return True
                
    except Exception as e:
        logger.error(f"Error checking user plan: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Check specific user first
    target_email = "drrobinson37@gmail.com"
    logger.info(f"Checking plan for {target_email}")
    check_specific_user_plan(target_email)
    
    print("\n" + "="*50)
    print("FIXING PLAN DISPLAY SYSTEM-WIDE")
    print("="*50)
    
    # Fix system-wide
    success = fix_plan_display_system_wide()
    
    if success:
        print("✅ Plan display fixed system-wide")
    else:
        print("❌ Failed to fix plan display system-wide")