"""
Test script to debug valuation API issues
"""
import requests
import json

rapidapi_key = "be3e296439msh2693e44b9d2433fp17bebbjsn9aa77716b131"

def test_zillow_api():
    """Test Zillow API directly"""
    print("\n=== Testing Zillow API ===")
    
    # Test search endpoint
    search_url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
    }
    
    params = {
        "location": "Charlotte, NC",
        "status_type": "ForSale",
        "home_type": "Houses"
    }
    
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response has 'props': {'props' in data}")
            if 'props' in data and data['props']:
                print(f"Found {len(data['props'])} properties")
                print(f"First property: {json.dumps(data['props'][0], indent=2)[:500]}...")
        else:
            print(f"Response text: {response.text[:500]}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_redfin_api():
    """Test Redfin API directly"""
    print("\n=== Testing Redfin API ===")
    
    search_url = "https://redfin-com-data.p.rapidapi.com/properties/search-sale"
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "redfin-com-data.p.rapidapi.com"
    }
    
    params = {
        "regionId": "11997",  # Charlotte
        "sortBy": "relevance",
        "limit": 5
    }
    
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Response preview: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Response text: {response.text[:500]}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_attom_api():
    """Test ATTOM API directly"""
    print("\n=== Testing ATTOM API ===")
    
    # ATTOM typically requires an API key directly from them
    print("ATTOM API requires separate authentication")

if __name__ == "__main__":
    test_zillow_api()
    test_redfin_api()
    test_attom_api()