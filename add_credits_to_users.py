#!/usr/bin/env python3
"""
Script to add credits to specific users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from billing_service import BillingService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_credits_to_user(email: str, credits: int, reason: str = "Admin credit grant"):
    """Add credits to a user's account"""
    try:
        billing_service = BillingService()
        
        # Use the billing service's add_credits method
        result = billing_service.add_credits(email, credits, reason)
        
        if result['success']:
            logger.info(f"✅ Successfully added {credits} credits to {email}")
            logger.info(f"   New balance: {result['new_balance']}")
            return True
        else:
            logger.error(f"❌ Failed to add credits to {email}: {result['error']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error adding credits to {email}: {e}")
        return False

def main():
    """Main function to add credits to both users"""
    
    # User credit assignments
    users_to_credit = [
        {
            "email": "brandon@sharperprocess.com",
            "credits": 100,
            "reason": "Admin credit grant - 100 credits"
        },
        {
            "email": "brandon@simplestephomes.com", 
            "credits": 40,
            "reason": "Admin credit grant - 40 credits"
        }
    ]
    
    logger.info("🚀 Starting credit addition process...")
    
    success_count = 0
    total_count = len(users_to_credit)
    
    for user_info in users_to_credit:
        logger.info(f"Processing {user_info['email']}...")
        
        if add_credits_to_user(user_info['email'], user_info['credits'], user_info['reason']):
            success_count += 1
        
        print("-" * 50)
    
    # Summary
    logger.info(f"📊 Summary: {success_count}/{total_count} users successfully credited")
    
    if success_count == total_count:
        logger.info("🎉 All credit additions completed successfully!")
    else:
        logger.warning(f"⚠️  {total_count - success_count} credit additions failed")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)