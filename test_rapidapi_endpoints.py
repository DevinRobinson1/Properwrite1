#!/usr/bin/env python3
"""
Test script to identify working RapidAPI endpoints for property data
"""
import os
import requests
import json
from typing import Dict, List

def test_rapidapi_endpoint(url: str, host: str, params: Dict, description: str) -> Dict:
    """Test a specific RapidAPI endpoint"""
    rapidapi_key = os.environ.get('RAPIDAPI_KEY')
    if not rapidapi_key:
        return {"error": "No RapidAPI key found"}
    
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": host
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        result = {
            "description": description,
            "url": url,
            "host": host,
            "status_code": response.status_code,
            "success": response.status_code == 200
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                result["response_keys"] = list(data.keys()) if isinstance(data, dict) else "Not a dict"
                result["has_data"] = bool(data)
                # Sample a small part of the response
                result["sample"] = str(data)[:300] if data else "Empty response"
            except:
                result["response_type"] = "Non-JSON response"
        else:
            result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
            
        return result
        
    except Exception as e:
        return {
            "description": description,
            "url": url,
            "host": host,
            "error": str(e),
            "success": False
        }

def test_all_endpoints():
    """Test various RapidAPI real estate endpoints"""
    
    # Test coordinates for Kannapolis, NC (from Google Places)
    test_address = "5208 Teakwood Drive"
    test_city = "Kannapolis"
    test_state = "NC"
    
    endpoints_to_test = [
        # Realty API endpoints
        {
            "url": "https://realty-in-us.p.rapidapi.com/properties/list-for-sale",
            "host": "realty-in-us.p.rapidapi.com",
            "params": {"city": test_city, "state_code": test_state, "limit": "5"},
            "description": "Realty-in-US: List for Sale"
        },
        
        # Realtor API alternatives
        {
            "url": "https://realtor16.p.rapidapi.com/properties/list-for-sale",
            "host": "realtor16.p.rapidapi.com", 
            "params": {"city": test_city, "state_code": test_state, "limit": 5},
            "description": "Realtor16: List for Sale"
        },
        
        # Alternative Redfin APIs
        {
            "url": "https://unofficial-redfin.p.rapidapi.com/properties/list-for-sale",
            "host": "unofficial-redfin.p.rapidapi.com",
            "params": {"location": f"{test_city}, {test_state}", "limit": 5},
            "description": "Unofficial Redfin: List for Sale"
        },
        
        # Alternative property APIs
        {
            "url": "https://us-real-estate.p.rapidapi.com/for-sale",
            "host": "us-real-estate.p.rapidapi.com",
            "params": {"location": f"{test_city}, {test_state}", "limit": 5},
            "description": "US Real Estate: For Sale"
        },
        
        # Check if these are subscription-based
        {
            "url": "https://redfin-com-data.p.rapidapi.com/properties/search-sale",
            "host": "redfin-com-data.p.rapidapi.com",
            "params": {"location": f"{test_city}, {test_state}"},
            "description": "Redfin.com Data: Search Sale"
        },
        
        {
            "url": "https://realtor-search.p.rapidapi.com/properties/search",
            "host": "realtor-search.p.rapidapi.com",
            "params": {"location": f"{test_city}, {test_state}", "limit": 10},
            "description": "Realtor Search: Properties Search"
        }
    ]
    
    print("Testing RapidAPI Real Estate Endpoints")
    print("=" * 50)
    
    working_endpoints = []
    failed_endpoints = []
    
    for endpoint in endpoints_to_test:
        print(f"\nTesting: {endpoint['description']}")
        print(f"URL: {endpoint['url']}")
        
        result = test_rapidapi_endpoint(
            endpoint['url'], 
            endpoint['host'], 
            endpoint['params'], 
            endpoint['description']
        )
        
        if result['success']:
            print(f"✅ SUCCESS - Status: {result['status_code']}")
            if 'response_keys' in result:
                print(f"   Response keys: {result['response_keys']}")
            if 'sample' in result:
                print(f"   Sample data: {result['sample']}")
            working_endpoints.append(result)
        else:
            print(f"❌ FAILED - {result.get('error', 'Unknown error')}")
            failed_endpoints.append(result)
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    print(f"\n✅ WORKING ENDPOINTS ({len(working_endpoints)}):")
    for endpoint in working_endpoints:
        print(f"  - {endpoint['description']}")
        print(f"    URL: {endpoint['url']}")
        print(f"    Host: {endpoint['host']}")
    
    print(f"\n❌ FAILED ENDPOINTS ({len(failed_endpoints)}):")
    for endpoint in failed_endpoints:
        print(f"  - {endpoint['description']}")
        print(f"    Error: {endpoint.get('error', 'Unknown')}")
    
    # Create a report
    report = {
        "working_endpoints": working_endpoints,
        "failed_endpoints": failed_endpoints,
        "test_location": f"{test_city}, {test_state}",
        "total_tested": len(endpoints_to_test)
    }
    
    with open('rapidapi_endpoint_test_results.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed results saved to: rapidapi_endpoint_test_results.json")
    return report

if __name__ == "__main__":
    test_all_endpoints()