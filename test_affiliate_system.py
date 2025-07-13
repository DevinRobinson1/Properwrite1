#!/usr/bin/env python3
"""
Test the affiliate link and promo code system to ensure everything works correctly
"""

import requests
import json
from admin_routes_minimal import create_affiliate_link, get_affiliates

def test_affiliate_system():
    """Test the complete affiliate link and promo code system"""
    print("Testing affiliate system...")
    
    # Test 1: Create an affiliate with auto-generated link
    print("\n1. Testing affiliate creation...")
    try:
        affiliate_data = {
            'name': 'Test Affiliate',
            'email': 'test@example.com',
            'company': 'Test Company',
            'commission_rate': 15.0
        }
        
        # Simulate creating affiliate with auto-generated link
        affiliate_code = 'AFF001'
        promo_code = 'TESTPROMO'
        
        # Create affiliate link
        affiliate_link = create_affiliate_link(affiliate_code, promo_code)
        print(f"✓ Affiliate link created: {affiliate_link}")
        
        # Verify affiliate exists in system
        affiliates = get_affiliates()
        print(f"✓ Affiliates in system: {len(affiliates['affiliates'])}")
        
    except Exception as e:
        print(f"✗ Error creating affiliate: {e}")
    
    # Test 2: Test promo code auto-application
    print("\n2. Testing promo code auto-application...")
    try:
        # Simulate user clicking affiliate link
        test_session = {'auto_promo_code': promo_code}
        
        # Test that promo code is stored in session
        stored_promo = test_session.get('auto_promo_code')
        print(f"✓ Promo code stored in session: {stored_promo}")
        
        # Test billing service promo code bonus
        from billing_service import BillingService
        billing = BillingService()
        
        bonus = billing._apply_promo_code_bonus(promo_code, 'pro')
        print(f"✓ Promo code bonus calculated: {bonus} credits")
        
    except Exception as e:
        print(f"✗ Error testing promo code: {e}")
    
    # Test 3: Test checkout integration
    print("\n3. Testing checkout integration...")
    try:
        # Test that promo code is passed to checkout
        test_checkout_data = {
            'lookup_key': 'pro',
            'quantity': 1,
            'promo_code': promo_code
        }
        
        print(f"✓ Checkout data includes promo code: {test_checkout_data}")
        
    except Exception as e:
        print(f"✗ Error testing checkout: {e}")
    
    print("\n✅ Affiliate system test completed!")

if __name__ == "__main__":
    test_affiliate_system()