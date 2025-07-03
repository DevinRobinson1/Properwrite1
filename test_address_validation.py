#!/usr/bin/env python3
"""
Test script for Google Address Validation API integration
"""

import json
import requests

def test_address_validation():
    """Test the new address validation API endpoint"""
    
    test_cases = [
        {
            'name': 'Valid Charlotte Address',
            'data': {
                'street_address': '14303 Evening Flight Lane',
                'city': 'Charlotte',
                'state': 'NC',
                'zip_code': '28278'
            },
            'should_pass': True
        },
        {
            'name': 'Incomplete Address (missing street)',
            'data': {
                'city': 'Charlotte',
                'state': 'NC',
                'zip_code': '28278'
            },
            'should_pass': False
        },
        {
            'name': 'Invalid Address',
            'data': {
                'street_address': '123 Fake Street',
                'city': 'Nowhere',
                'state': 'XX',
                'zip_code': '00000'
            },
            'should_pass': False
        }
    ]
    
    print("🔧 Testing Google Address Validation Integration")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                'http://localhost:5000/api/analyze-property',
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if test_case['should_pass']:
                if response.status_code == 200:
                    print(f"   ✅ PASS: Valid address accepted")
                    data = response.json()
                    if 'property_data' in data:
                        print(f"   📍 Property analysis completed successfully")
                else:
                    print(f"   ❌ FAIL: Expected success but got {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
            else:
                if response.status_code == 400:
                    print(f"   ✅ PASS: Invalid address properly rejected")
                    data = response.json()
                    error_type = data.get('error', 'Unknown')
                    message = data.get('message', 'No message')
                    print(f"   🚫 Error: {error_type} - {message}")
                else:
                    print(f"   ❌ FAIL: Expected rejection but got {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ FAIL: Network error - {e}")
        except Exception as e:
            print(f"   ❌ FAIL: Unexpected error - {e}")

if __name__ == "__main__":
    test_address_validation()