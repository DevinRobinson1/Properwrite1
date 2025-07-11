#!/usr/bin/env python3
import os
import requests
import json

rapidapi_key = os.environ.get('RAPIDAPI_KEY')
if not rapidapi_key:
    print("No RapidAPI key found")
    exit(1)

print("Testing alternative Realtor APIs...")
print("=" * 60)

# Test 1: Try Realtor Data API (different host)
print("\n1. Testing Realtor Data API - property_list endpoint")
headers = {
    "X-RapidAPI-Key": rapidapi_key,
    "X-RapidAPI-Host": "realtor-data1.p.rapidapi.com",
    "Content-Type": "application/json"
}

url = "https://realtor-data1.p.rapidapi.com/property_list/"
payload = {
    "query": {
        "status": ["for_sale", "sold"],
        "postal_code": "28262"
    },
    "limit": 5,
    "offset": 0
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)[:500]}...")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")

# Test 2: Try Realtor16 API
print("\n2. Testing Realtor16 API")
headers = {
    "X-RapidAPI-Key": rapidapi_key,
    "X-RapidAPI-Host": "realtor16.p.rapidapi.com"
}

url = "https://realtor16.p.rapidapi.com/search"
params = {
    "location": "14303 Evening Flight Lane Charlotte NC"
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

# Test 3: Try Realtor.com Property Data API  
print("\n3. Testing realtor-com-property-data API")
headers = {
    "X-RapidAPI-Key": rapidapi_key,
    "X-RapidAPI-Host": "realtor-com-property-data.p.rapidapi.com"
}

url = "https://realtor-com-property-data.p.rapidapi.com/address-search"
params = {
    "address": "14303 Evening Flight Lane",
    "city": "Charlotte",
    "state": "NC",
    "zip": "28262"
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