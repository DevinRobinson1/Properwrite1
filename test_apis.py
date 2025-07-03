#!/usr/bin/env python3
"""
Test script to verify API functionality with known properties
"""
from rapidapi_property_service import RapidAPIPropertyService
import logging

logging.basicConfig(level=logging.INFO)

def test_known_properties():
    service = RapidAPIPropertyService()
    
    # Test with well-known Charlotte residential addresses
    test_addresses = [
        ('1234 Queens Road West', 'Charlotte', 'NC', '28207'),
        ('100 N Tryon St', 'Charlotte', 'NC', '28202'),
        ('5200 Park Rd', 'Charlotte', 'NC', '28209'),
    ]
    
    print("Testing API integration with known Charlotte properties:")
    print("=" * 60)
    
    for addr, city, state, zip_code in test_addresses:
        print(f"\nTesting: {addr}, {city}, {state} {zip_code}")
        
        # Test Zillow
        zillow_result = service._get_zillow_data(addr, city, state, zip_code)
        if zillow_result:
            print(f"✓ Zillow found: ${zillow_result.get('estimate', 'N/A')}")
        else:
            print(f"✗ Zillow: No data")
        
        # Test Realtor.com
        realtor_result = service._get_realtor_data(addr, city, state, zip_code)
        if realtor_result:
            print(f"✓ Realtor found: ${realtor_result.get('estimate', 'N/A')}")
        else:
            print(f"✗ Realtor: No data")
        
        # Test Redfin
        redfin_result = service._get_redfin_data(addr, city, state, zip_code)
        if redfin_result:
            print(f"✓ Redfin found: ${redfin_result.get('estimate', 'N/A')}")
        else:
            print(f"✗ Redfin: No data")
    
    print("\n" + "=" * 60)
    print("Testing original problem address:")
    
    # Test the original problem address
    original_addr = '14303 Evening Flight Lane'
    original_city = 'Charlotte'
    original_state = 'NC'
    original_zip = '28262'
    
    print(f"Testing: {original_addr}, {original_city}, {original_state} {original_zip}")
    
    zillow_result = service._get_zillow_data(original_addr, original_city, original_state, original_zip)
    realtor_result = service._get_realtor_data(original_addr, original_city, original_state, original_zip)
    redfin_result = service._get_redfin_data(original_addr, original_city, original_state, original_zip)
    
    if not any([zillow_result, realtor_result, redfin_result]):
        print("✗ No data found from any API for this property")
        print("This property may not exist in the API databases")
    else:
        print("✓ Found data from at least one API")

if __name__ == "__main__":
    test_known_properties()