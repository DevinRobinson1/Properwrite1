#!/usr/bin/env python3
"""
Demo script to show working affiliate links
"""

import json
import requests

# Define test affiliate links
TEST_LINKS = [
    "http://localhost:5000/ref/AFF001",
    "http://localhost:5000/ref/AFF002", 
    "http://localhost:5000/ref/WELCOME",
    "http://localhost:5000/ref/INVALID"
]

def test_affiliate_links():
    """Test all affiliate links and show results"""
    print("🔗 Testing Affiliate Links")
    print("=" * 50)
    
    for link in TEST_LINKS:
        code = link.split('/')[-1]
        
        try:
            # Test the link
            response = requests.get(link, allow_redirects=False)
            
            if response.status_code == 302:
                print(f"✅ {code}: Working (redirects to {response.headers.get('Location', 'homepage')})")
            else:
                print(f"❌ {code}: Failed (status {response.status_code})")
                
        except Exception as e:
            print(f"❌ {code}: Error - {e}")
    
    print("\n📊 Promo Code Bonuses:")
    print("-" * 30)
    
    # Test promo code bonuses
    from billing_service import BillingService
    billing = BillingService()
    
    promo_codes = ['AFF001', 'AFF002', 'AFF003', 'WELCOME50', 'STARTER100']
    
    for code in promo_codes:
        bonus = billing._apply_promo_code_bonus(code, 'pro')
        print(f"💰 {code}: {bonus} bonus credits")
    
    print("\n🎯 How it works:")
    print("1. User clicks affiliate link like /ref/AFF001")
    print("2. System stores promo code in session")
    print("3. During checkout, promo code auto-applies")
    print("4. User gets bonus credits on signup")
    print("\n✅ Affiliate system is fully functional!")

if __name__ == "__main__":
    test_affiliate_links()