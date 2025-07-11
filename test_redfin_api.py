#!/usr/bin/env python3
import os
import requests
import json
import time

rapidapi_key = os.environ.get('RAPIDAPI_KEY')
if not rapidapi_key:
    print("No RapidAPI key found")
    exit(1)

print("Testing Redfin.com Data API endpoints...")
print("=" * 60)

headers = {
    "X-RapidAPI-Key": rapidapi_key,
    "X-RapidAPI-Host": "redfin-com-data.p.rapidapi.com"
}

# Test 1: Try search-sale with regionId
print("\n1. Testing properties/search-sale with regionId")
url = "https://redfin-com-data.p.rapidapi.com/properties/search-sale"
params = {
    "regionId": "11053",  # Charlotte, NC region ID
    "limit": "5"
}

try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)[:500]}...")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")

# Wait a bit to avoid rate limiting
time.sleep(2)

# Test 2: Try auto-complete to get regionId
print("\n2. Testing auto-complete to find Charlotte regionId")
url = "https://redfin-com-data.p.rapidapi.com/auto-complete"
params = {
    "query": "Charlotte NC"
}

try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)[:500]}...")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")

# Wait a bit to avoid rate limiting
time.sleep(2)

# Test 3: Try property details with a specific URL
print("\n3. Testing properties/details with URL")
url = "https://redfin-com-data.p.rapidapi.com/properties/details"
params = {
    "url": "https://www.redfin.com/NC/Charlotte/14303-Evening-Flight-Ln-28262/home/47435141"
}

try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)[:500]}...")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")