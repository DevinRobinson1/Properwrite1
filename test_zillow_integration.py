#!/usr/bin/env python3
"""
Test script for Zillow integration - bypasses frontend
Run in Replit Shell to test end-to-end address→Zillow flow
"""

import requests
import json
import os
from address_utils import to_zillow_search_string

def test_address_normalization():
    """Test the address normalization function"""
    print("=== Testing Address Normalization ===")
    
    test_addresses = [
        "14303 Six Oaks Cir, CARNES CROSSROADS, SC, USA",
        "14303 Evening Flight Lane, Charlotte, NC, USA",
        "9 Catawba Trail, Myrtle Beach, SC, USA"
    ]
    
    for addr in test_addresses:
        normalized = to_zillow_search_string(addr)
        print(f"Original: {addr}")
        print(f"Normalized: {normalized}")
        print("---")

def test_zillow_direct_api():
    """Test Zillow API directly"""
    print("\n=== Testing Zillow API Direct ===")
    
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    if not rapidapi_key:
        print("❌ RAPIDAPI_KEY not found in environment")
        return
    
    # Test with known working address
    test_address = "14303 Evening Flight Lane, Charlotte, NC, USA"
    normalized = to_zillow_search_string(test_address)
    
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
    }
    
    search_url = (
        f"https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
        f"?location={normalized}"
        f"&status_type=RecentlySold"
        f"&home_type=Houses"
    )
    
    print(f"🐛 Testing URL: {search_url}")
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            
            if isinstance(data, list) and len(data) > 0:
                zpid = data[0].get('zpid')
                address = data[0].get('address', 'Unknown')
                print(f"✅ Found ZPID: {zpid} for {address}")
                
                # Test details endpoint
                detail_url = f"https://zillow-com1.p.rapidapi.com/property?zpid={zpid}"
                detail_response = requests.get(detail_url, headers=headers, timeout=10)
                print(f"Details API Status: {detail_response.status_code}")
                
                if detail_response.status_code == 200:
                    print("✅ Details API works - paid tier")
                elif detail_response.status_code == 401:
                    print("⚠️ Details API requires paid tier")
                else:
                    print(f"❌ Details API error: {detail_response.status_code}")
            else:
                print("❌ No properties found in response")
        else:
            print(f"❌ Search API failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")

def test_backend_api():
    """Test our backend API"""
    print("\n=== Testing Backend API ===")
    
    test_payload = {
        "place_id": "ChIJHTYugoEcVIgRbBTaWn4ekKc",
        "address": "14303 Evening Flight Lane",
        "city": "Charlotte",
        "state": "North Carolina",
        "zip_code": "28262",
        "formatted_address": "14303 Evening Flight Lane, Charlotte, NC, USA",
        "latitude": 35.2271,
        "longitude": -80.8431
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/api/analyze-property",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"Backend Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Backend API works")
                print(f"Estimated Value: ${data.get('estimated_value', 0):,}")
                print(f"Data Source: {data.get('data_source', 'Unknown')}")
                print(f"Sources Tried: {data.get('sources_tried', [])}")
            else:
                print("❌ Backend returned success=false")
        else:
            print(f"❌ Backend failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Backend test failed: {e}")

if __name__ == "__main__":
    test_address_normalization()
    test_zillow_direct_api()
    test_backend_api()