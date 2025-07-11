#!/usr/bin/env python3
import os
import requests
import json

rapidapi_key = os.environ.get('RAPIDAPI_KEY')
if not rapidapi_key:
    print("No RapidAPI key found")
    exit(1)

# Test address
test_address = "14303 Evening Flight Lane Charlotte NC 28262"

print("Testing Realtor Search API endpoints for exact property match...")
print("=" * 60)

# Test 1: Try address search endpoint
print("\n1. Testing /properties/search-by-address endpoint")
headers = {
    "X-RapidAPI-Key": rapidapi_key,
    "X-RapidAPI-Host": "realtor-search.p.rapidapi.com"
}

url = "https://realtor-search.p.rapidapi.com/properties/search-by-address"
params = {"address": test_address}

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

# Test 2: Try property details endpoint
print("\n2. Testing /properties/detail endpoint")
url = "https://realtor-search.p.rapidapi.com/properties/detail"
params = {"property_id": "121306547"}  # Using the Zillow property ID as a test

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

# Test 3: Try address autocomplete
print("\n3. Testing /locations/auto-complete endpoint")
url = "https://realtor-search.p.rapidapi.com/locations/auto-complete"
params = {"input": "14303 Evening Flight Lane Charlotte"}

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

# Test 4: Try exact match with search endpoint
print("\n4. Testing /properties/search endpoint")
url = "https://realtor-search.p.rapidapi.com/properties/search"
params = {
    "location": "14303 Evening Flight Lane, Charlotte, NC 28262",
    "status": ["for_sale", "recently_sold"],
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