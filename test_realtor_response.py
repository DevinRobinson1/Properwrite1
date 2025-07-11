#!/usr/bin/env python3
import os
import requests
import json

rapidapi_key = os.environ.get('RAPIDAPI_KEY')
if not rapidapi_key:
    print("No RapidAPI key found")
    exit(1)

# Test with coordinates for Charlotte property
headers = {
    "X-RapidAPI-Key": rapidapi_key,
    "X-RapidAPI-Host": "realtor-search.p.rapidapi.com"
}

url = "https://realtor-search.p.rapidapi.com/properties/nearby-home-values"
params = {
    "lat": "35.3511",
    "lon": "-80.7420"
}

print("Testing Realtor.com nearby-home-values API...")
print(f"URL: {url}")
print(f"Params: {params}")
print("=" * 60)

response = requests.get(url, headers=headers, params=params, timeout=10)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    if 'data' in data and 'home_search' in data['data']:
        home_search = data['data']['home_search']
        print(f"Found {home_search.get('count', 0)} properties")
        
        if 'results' in home_search:
            for i, prop in enumerate(home_search['results'][:3]):  # Show first 3
                print(f"\nProperty {i+1}:")
                print(f"  Address: {prop.get('location', {}).get('address', {}).get('line', 'N/A')}")
                print(f"  Property ID: {prop.get('property_id', 'N/A')}")
                
                # Check description
                desc = prop.get('description', {})
                print(f"  Beds: {desc.get('beds', 'N/A')}")
                print(f"  Baths: {desc.get('baths', 'N/A')}")
                print(f"  Sqft: {desc.get('sqft', 'N/A')}")
                
                # Check for price info
                print(f"  Price per sqft: {prop.get('price_per_sqft', 'N/A')}")
                print(f"  List price: {prop.get('list_price', 'N/A')}")
                
                # Check listing information
                print(f"  Last updated: {prop.get('last_update_date', 'N/A')}")
                print(f"  Property status: {prop.get('status', 'N/A')}")
                
                # Show raw property data
                print(f"  Raw data keys: {list(prop.keys())}")
else:
    print(f"Error: {response.text}")