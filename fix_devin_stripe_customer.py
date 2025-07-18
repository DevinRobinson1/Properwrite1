#!/usr/bin/env python3
"""
Fix Devin's team to have a proper Stripe customer ID
"""

import os
import sys
from billing_service import BillingService

def main():
    """Fix Devin's team to have a Stripe customer ID"""
    
    # Get Devin's team ID from the database query we ran
    team_id = "a34a5049-70e7-4a87-a315-1b26f0ab6ba1"
    
    print(f"Creating Stripe customer for team {team_id}...")
    
    # Initialize billing service
    billing_service = BillingService()
    
    # Create Stripe customer for the team
    result = billing_service.create_stripe_customer_for_team(team_id)
    
    if result['success']:
        print(f"✅ Successfully created Stripe customer: {result['customer_id']}")
        
        # Test the customer portal session creation
        print("Testing customer portal session creation...")
        portal_result = billing_service.create_customer_portal_session(team_id)
        
        if portal_result['success']:
            print(f"✅ Customer portal session created successfully!")
            print(f"Portal URL: {portal_result['portal_url']}")
        else:
            print(f"❌ Error creating portal session: {portal_result['error']}")
    else:
        print(f"❌ Error creating Stripe customer: {result['error']}")
        
if __name__ == "__main__":
    main()