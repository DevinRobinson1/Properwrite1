#!/usr/bin/env python3
"""
Test which property APIs are actually working with our subscription
"""
import os
import requests
import json

rapidapi_key = os.environ.get('RAPIDAPI_KEY')
if not rapidapi_key:
    print("No RapidAPI key found")
    exit(1)

print("Testing property APIs with RapidAPI key...")
print("=" * 60)

# Test 1: Zillow (we know this works)
print("\n1. ZILLOW API TEST")
headers = {
    "X-RapidAPI-Key": rapidapi_key,
    "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
}
url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch?location=Charlotte+NC&status_type=RecentlySold&home_type=Houses"
response = requests.get(url, headers=headers, timeout=10)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ ZILLOW WORKING")
else:
    print("❌ ZILLOW FAILED")

# Test 2: US Real Estate API
print("\n2. US REAL ESTATE API TEST")
headers = {
    "X-RapidAPI-Key": rapidapi_key,
    "X-RapidAPI-Host": "us-real-estate2.p.rapidapi.com"
}
url = "https://us-real-estate2.p.rapidapi.com/v2/for-sale"
params = {"location": "Charlotte, NC", "limit": "5"}
response = requests.get(url, headers=headers, params=params, timeout=10)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ US REAL ESTATE WORKING")
    data = response.json()
    print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'List response'}")
else:
    print(f"❌ US REAL ESTATE FAILED: {response.text[:100]}")

# Test 3: Realty Mole API
print("\n3. REALTY MOLE API TEST")
headers = {
    "X-RapidAPI-Key": rapidapi_key,
    "X-RapidAPI-Host": "realty-mole-property-api.p.rapidapi.com"
}
url = "https://realty-mole-property-api.p.rapidapi.com/properties"
params = {"address": "14303 Evening Flight Lane, Charlotte, NC"}
response = requests.get(url, headers=headers, params=params, timeout=10)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ REALTY MOLE WORKING")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)[:200]}")
else:
    print(f"❌ REALTY MOLE FAILED: {response.text[:100]}")

# Test 4: Home Junction API
print("\n4. HOME JUNCTION API TEST")
headers = {
    "X-RapidAPI-Key": rapidapi_key,
    "X-RapidAPI-Host": "homejunction-properties.p.rapidapi.com"
}
url = "https://homejunction-properties.p.rapidapi.com/properties"
params = {"zipCode": "28262", "limit": "5"}
response = requests.get(url, headers=headers, params=params, timeout=10)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ HOME JUNCTION WORKING")
else:
    print(f"❌ HOME JUNCTION FAILED: {response.text[:100]}")

# Test 5: Real Estate Records API
print("\n5. REAL ESTATE RECORDS API TEST")
headers = {
    "X-RapidAPI-Key": rapidapi_key,
    "X-RapidAPI-Host": "real-estate-records.p.rapidapi.com"
}
url = "https://real-estate-records.p.rapidapi.com/search"
params = {"location": "Charlotte, NC"}
response = requests.get(url, headers=headers, params=params, timeout=10)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ REAL ESTATE RECORDS WORKING")
else:
    print(f"❌ REAL ESTATE RECORDS FAILED: {response.text[:100]}")

print("\n" + "=" * 60)
print("SUMMARY: Test complete. Check which APIs are working above.")