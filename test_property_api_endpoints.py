#!/usr/bin/env python3
"""
Test script to find working property API endpoints
"""
import os
import requests
import json

def test_endpoint(url, host, params, method="GET", data=None):
    """Test an endpoint and print results"""
    rapidapi_key = os.environ.get('RAPIDAPI_KEY')
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": host
    }
    
    print(f"\nTesting: {url}")
    print(f"Method: {method}")
    print(f"Params: {params}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        else:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Response preview: {json.dumps(data, indent=2)[:500]}...")
            return True
        else:
            print(f"Error: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

print("Testing Realtor Search API endpoints...")
print("=" * 60)

# Test different Realtor Search endpoints
test_endpoint(
    "https://realtor-search.p.rapidapi.com/properties/search",
    "realtor-search.p.rapidapi.com",
    {"query": "14303 Evening Flight Lane Charlotte NC"}
)

test_endpoint(
    "https://realtor-search.p.rapidapi.com/properties/list",
    "realtor-search.p.rapidapi.com",
    {"city": "Charlotte", "state": "NC", "limit": "5"}
)

# Test with lat/lon
test_endpoint(
    "https://realtor-search.p.rapidapi.com/properties/nearby-home-values",
    "realtor-search.p.rapidapi.com",
    {"lat": "35.3511", "lon": "-80.7420"}
)

print("\n\nTesting Redfin.com Data API endpoints...")
print("=" * 60)

# Test different Redfin endpoints
test_endpoint(
    "https://redfin-com-data.p.rapidapi.com/properties/search",
    "redfin-com-data.p.rapidapi.com",
    {"query": "Charlotte NC", "limit": "5"}
)

test_endpoint(
    "https://redfin-com-data.p.rapidapi.com/properties/search-by-address",
    "redfin-com-data.p.rapidapi.com",
    {"address": "14303 Evening Flight Lane Charlotte NC"}
)

# Try to get regionId for Charlotte
test_endpoint(
    "https://redfin-com-data.p.rapidapi.com/regions/search",
    "redfin-com-data.p.rapidapi.com",
    {"query": "Charlotte NC"}
)