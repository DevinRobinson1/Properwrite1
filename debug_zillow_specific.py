"""
Debug Zillow API with specific address
"""
import requests
import json
import os

rapidapi_key = os.environ.get('RAPIDAPI_KEY')
if not rapidapi_key:
    raise ValueError("RAPIDAPI_KEY environment variable is required")

def test_zillow_with_specific_address():
    """Test Zillow API with the failing address"""
    print("\n=== Testing Zillow API with 1431 Sumner Avenue ===")
    
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
    }
    
    # Test the exact search that's failing
    search_url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
    search_params = {
        "location": "1431 Sumner Avenue, North Charleston, SC, USA, 29406",
        "status_type": "RecentlySold,ForSale", 
        "home_type": "Houses,Townhomes,Condos"
    }
    
    print(f"URL: {search_url}")
    print(f"Headers: {headers}")
    print(f"Params: {search_params}")
    
    try:
        response = requests.get(search_url, headers=headers, params=search_params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Found {len(data.get('props', []))} properties")
            if data.get('props'):
                print(f"First property: {json.dumps(data['props'][0], indent=2)[:300]}...")
        else:
            print(f"Error Response: {response.text}")
            
        # Try simpler location format
        print("\n--- Trying simpler location format ---")
        simple_params = {
            "location": "North Charleston, SC",
            "status_type": "ForSale",
            "home_type": "Houses"
        }
        
        response2 = requests.get(search_url, headers=headers, params=simple_params, timeout=10)
        print(f"Simple search status: {response2.status_code}")
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"Simple search found {len(data2.get('props', []))} properties")
            
            # Test property details call with first property
            if data2.get('props'):
                first_prop = data2['props'][0]
                zpid = first_prop.get('zpid')
                print(f"\n--- Testing property details for zpid: {zpid} ---")
                print(f"Property address: {first_prop.get('address')}")
                
                detail_url = "https://zillow-com1.p.rapidapi.com/property"
                detail_params = {"zpid": zpid}
                
                detail_response = requests.get(detail_url, headers=headers, params=detail_params, timeout=10)
                print(f"Details API status: {detail_response.status_code}")
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    print(f"Detail response keys: {list(detail_data.keys()) if detail_data else 'None'}")
                    
                    # Check for possible zestimate fields
                    zestimate_fields = ['zestimate', 'price', 'homeValue', 'listPrice']
                    for field in zestimate_fields:
                        value = detail_data.get(field)
                        if value:
                            print(f"Found {field}: {value}")
                    
                    # Check nested structures
                    if 'resoFacts' in detail_data:
                        reso = detail_data['resoFacts']
                        print(f"ResoFacts keys: {list(reso.keys())}")
                        for field in zestimate_fields + ['lastSoldPrice']:
                            value = reso.get(field)
                            if value:
                                print(f"ResoFacts.{field}: {value}")
                                
                else:
                    print(f"Details API error: {detail_response.text[:300]}")
        else:
            print(f"Simple search error: {response2.text[:200]}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_zillow_with_specific_address()