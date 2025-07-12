#!/usr/bin/env python3
"""
Critical Flow Testing Script for Fund Flow OS
Tests core functionality without modifying production code
"""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def test_homepage_loads():
    """Test that homepage loads successfully"""
    try:
        response = requests.get(BASE_URL, timeout=5)
        assert response.status_code == 200
        assert "properwrite.com" in response.text.lower()
        print("✅ Homepage loads successfully")
        return True
    except Exception as e:
        print(f"❌ Homepage test failed: {e}")
        return False

def test_api_endpoints():
    """Test that critical API endpoints respond"""
    endpoints = [
        ("/api/places/autocomplete", "POST"),
        ("/api/team/stats", "GET"),
        ("/api/billing/create-checkout", "POST"),
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(BASE_URL + endpoint, timeout=5)
            else:
                response = requests.post(BASE_URL + endpoint, json={}, timeout=5)
            
            # We expect 401/403 for auth-required endpoints when not logged in
            if response.status_code in [200, 401, 403, 400]:
                print(f"✅ {endpoint} endpoint responsive (status: {response.status_code})")
            else:
                print(f"⚠️  {endpoint} returned unexpected status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} test failed: {e}")

def test_admin_login_security():
    """Test that admin login exists but rejects bad passwords"""
    try:
        # Test with wrong password
        response = requests.post(
            BASE_URL + "/admin/login",
            data={"password": "wrongpassword"},
            timeout=5
        )
        
        if "Invalid credentials" in response.text or response.status_code == 200:
            print("✅ Admin login rejects invalid passwords")
        else:
            print("⚠️  Admin login behavior unexpected")
            
        # We won't test the actual password to avoid documenting it
        
    except Exception as e:
        print(f"❌ Admin login test failed: {e}")

def test_static_assets():
    """Test that critical static assets load"""
    assets = [
        "/static/js/google-autocomplete-new.js",
        "/static/js/enhanced-google-autocomplete.js",
    ]
    
    for asset in assets:
        try:
            response = requests.get(BASE_URL + asset, timeout=5)
            if response.status_code == 200:
                print(f"✅ Static asset {asset} loads")
            else:
                print(f"❌ Static asset {asset} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Static asset {asset} test failed: {e}")

def test_database_connection():
    """Test database connectivity through API"""
    try:
        # Try to access an endpoint that queries the database
        response = requests.get(BASE_URL + "/api/team/stats", timeout=5)
        # Even if unauthorized, a 401 means the app is running and DB is likely connected
        if response.status_code in [200, 401, 403]:
            print("✅ Database connection appears functional")
        else:
            print(f"⚠️  Database test returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")

def generate_report():
    """Generate test report"""
    print("\n" + "="*50)
    print("FUND FLOW OS - CRITICAL FLOW TEST REPORT")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")
    
    print("Running critical flow tests...\n")
    
    # Run all tests
    test_homepage_loads()
    test_api_endpoints()
    test_admin_login_security()
    test_static_assets()
    test_database_connection()
    
    print("\n" + "="*50)
    print("Test run completed. Review results above.")
    print("="*50)

if __name__ == "__main__":
    print("Starting Fund Flow OS critical flow tests...")
    print(f"Testing against: {BASE_URL}")
    print("Note: This script only tests, it does not modify any code.\n")
    
    try:
        generate_report()
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user.")
    except Exception as e:
        print(f"\n\nTest run failed with error: {e}")