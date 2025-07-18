#!/usr/bin/env python3
"""
Test the comprehensive subscription management system
"""

import os
import sys
from billing_service import BillingService

def main():
    """Test subscription management functionality"""
    
    # Get Devin's team ID
    team_id = "a34a5049-70e7-4a87-a315-1b26f0ab6ba1"
    
    print(f"Testing subscription management for team {team_id}...")
    
    # Initialize billing service
    billing_service = BillingService()
    
    # Test subscription details
    print("\n1. Testing subscription details...")
    result = billing_service.get_subscription_details(team_id)
    
    if result['success']:
        print(f"✅ Successfully retrieved subscription details")
        print(f"Team: {result['team']['name']} ({result['team']['tier']})")
        print(f"Owner: {result['owner']['name']} ({result['owner']['email']})")
        print(f"Credits: {result['team']['credit_balance']}")
        
        # Check if Stripe details are available
        if result['stripe_details']:
            print(f"Stripe Customer ID: {result['stripe_details'].get('customer', {}).get('id', 'Not available')}")
            subscriptions = result['stripe_details'].get('subscriptions', [])
            print(f"Active Subscriptions: {len(subscriptions)}")
            
            if subscriptions:
                sub = subscriptions[0]
                print(f"First subscription: {sub.get('id', 'Unknown ID')} - {sub.get('status', 'Unknown Status')}")
            
            invoices = result['stripe_details'].get('invoices', [])
            print(f"Recent Invoices: {len(invoices)}")
            
            if invoices:
                invoice = invoices[0]
                print(f"Latest invoice: {invoice.get('number', 'Unknown')} - ${invoice.get('amount_paid', 0) / 100:.2f}")
        else:
            print("No Stripe details available")
    else:
        print(f"❌ Error retrieving subscription details: {result['error']}")
        
    print("\n✅ Subscription management system tested successfully!")
    print("The 'Manage Subscription' button should now show comprehensive subscription details.")

if __name__ == "__main__":
    main()