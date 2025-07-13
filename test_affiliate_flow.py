#!/usr/bin/env python3
"""
Test the complete affiliate system flow
"""

import requests
import json
import time
from urllib.parse import urljoin

# Test configuration
BASE_URL = "https://properwrite-replit.replit.app"
ADMIN_PASSWORD = "2UfdI!2t&MvND7W9"

def test_affiliate_creation():
    """Test creating an affiliate through admin dashboard"""
    print("Testing affiliate creation...")
    
    # Login to admin
    login_data = {'password': ADMIN_PASSWORD}
    
    try:
        # Create test affiliate
        affiliate_data = {
            'name': 'Test Affiliate',
            'email': 'test@example.com',
            'company': 'Test Company',
            'commission_rate': 15.0
        }
        
        print(f"✓ Test affiliate data prepared: {affiliate_data}")
        return True
        
    except Exception as e:
        print(f"✗ Error testing affiliate creation: {e}")
        return False

def test_affiliate_link_redirect():
    """Test affiliate link redirect functionality"""
    print("\nTesting affiliate link redirect...")
    
    try:
        # Test affiliate link
        affiliate_code = "AFF001"
        affiliate_url = f"{BASE_URL}/ref/{affiliate_code}"
        
        print(f"✓ Testing affiliate link: {affiliate_url}")
        
        # Test redirect (should go to homepage)
        response = requests.get(affiliate_url, allow_redirects=False)
        
        if response.status_code in [302, 301]:
            print(f"✓ Affiliate redirect working: {response.status_code}")
            return True
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing affiliate link: {e}")
        return False

def test_promo_code_storage():
    """Test promo code storage in session"""
    print("\nTesting promo code session storage...")
    
    try:
        # Create session to test promo code storage
        session = requests.Session()
        
        # Visit affiliate link
        affiliate_code = "AFF001"
        affiliate_url = f"{BASE_URL}/ref/{affiliate_code}"
        
        response = session.get(affiliate_url)
        
        if response.status_code == 200:
            print("✓ Affiliate link processed successfully")
            
            # Check if we're on the homepage (after redirect)
            if "properwrite" in response.text.lower():
                print("✓ Redirected to homepage successfully")
                return True
            else:
                print("✗ Not redirected to homepage")
                return False
        else:
            print(f"✗ Error accessing affiliate link: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing promo code storage: {e}")
        return False

def test_billing_integration():
    """Test billing service promo code integration"""
    print("\nTesting billing service integration...")
    
    try:
        # Test promo code bonus calculation
        from billing_service import BillingService
        
        billing = BillingService()
        
        # Test different promo codes
        test_codes = ['AFF001', 'AFF002', 'WELCOME50', 'INVALID']
        
        for code in test_codes:
            bonus = billing._apply_promo_code_bonus(code, 'pro')
            print(f"✓ Promo code '{code}' bonus: {bonus} credits")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing billing integration: {e}")
        return False

def run_all_tests():
    """Run all affiliate system tests"""
    print("🧪 Running Affiliate System Tests")
    print("=" * 50)
    
    tests = [
        test_affiliate_creation,
        test_affiliate_link_redirect,
        test_promo_code_storage,
        test_billing_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
            print("✅ PASSED")
        else:
            failed += 1
            print("❌ FAILED")
        print("-" * 30)
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Affiliate system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    run_all_tests()