
import requests
import os

rapidapi_key = os.environ.get('RAPIDAPI_KEY')
if rapidapi_key:
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
    }
    
    # Test property details endpoint
    url = "https://zillow-com1.p.rapidapi.com/property"
    params = {"zpid": "2025903273"}  # One of the zpids from the screenshot
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        # Look for address fields
        print("Top-level keys:", list(data.keys())[:20])
        if 'address' in data:
            print("
Address field:", data['address'])
        if 'streetAddress' in data:
            print("
streetAddress field:", data['streetAddress'])
        if 'city' in data:
            print("
city field:", data['city'])
        if 'state' in data:
            print("
state field:", data['state'])
        if 'attributionInfo' in data:
            print("
Has attributionInfo")
        # Check nested structures
        for key in ['resoFacts', 'propertyInfo', 'propertyDetails']:
            if key in data and isinstance(data[key], dict):
                if 'address' in data[key] or 'streetAddress' in data[key]:
                    print(f"
Found address in {key}:", data[key].get('address') or data[key].get('streetAddress'))
    else:
        print(f"API request failed with status: {response.status_code}")
else:
    print("RapidAPI key not found")
