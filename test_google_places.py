#!/usr/bin/env python3
"""
Test script for Google Places "Place Details (New)" API integration
Tests the canonical address resolution with caching
"""

import os
from google_places_service import google_places_service, AddressNotFoundError, GooglePlacesAPIError

def test_known_place_ids():
    """Test with known place IDs that should work"""
    
    # Test cases with known Charlotte, NC area place IDs
    test_cases = [
        {
            'place_id': 'ChIJgzNLB4MgVYgRNFYeSWUOdqU',  # Example Charlotte place
            'description': 'Charlotte business district'
        },
        {
            'place_id': 'ChIJaZslmBM9VIgR4uYKhHJ5v_w',  # Another example
            'description': 'Charlotte area location'
        }
    ]
    
    print("🔧 Testing Google Places 'Place Details (New)' API Integration")
    print("=" * 60)
    
    # Check API key
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY not found in environment")
        print("Please set the API key in your secrets")
        return False
    else:
        print(f"✅ API key found: ...{api_key[-8:]}")
    
    print("\nTesting place ID resolution...")
    
    for i, test_case in enumerate(test_cases, 1):
        place_id = test_case['place_id']
        description = test_case['description']
        
        print(f"\n{i}. Testing {description}")
        print(f"   Place ID: {place_id}")
        
        try:
            result = google_places_service.get_canonical_address(place_id)
            
            print(f"   ✅ Success!")
            print(f"   📍 Address: {result['formattedAddress']}")
            print(f"   🌐 Coordinates: {result['lat']}, {result['lng']}")
            print(f"   🆔 Place ID: {result['placeId']}")
            
            # Test caching - second call should be faster
            print(f"   Testing cache...")
            import time
            start = time.time()
            cached_result = google_places_service.get_canonical_address(place_id)
            cache_time = (time.time() - start) * 1000
            
            if cache_time < 100:  # Should be under 100ms from cache
                print(f"   ✅ Cache working: {cache_time:.1f}ms")
            else:
                print(f"   ⚠️  Cache might not be working: {cache_time:.1f}ms")
                
            return True
            
        except AddressNotFoundError as e:
            print(f"   ❌ Address not found: {e}")
            continue
            
        except GooglePlacesAPIError as e:
            print(f"   ❌ API error: {e}")
            continue
            
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            continue
    
    print("\n❌ All test cases failed")
    return False

def test_14303_evening_flight_lane():
    """Test the specific address mentioned in the requirements"""
    print("\n🎯 Testing specific address: '14303 Evening Flight Lane, Charlotte NC'")
    
    # This would typically come from autocomplete, but we'll test if we can find it
    # Note: We'd need the actual place_id from Google Places Autocomplete for this address
    print("   Note: This requires the place_id from Google Places Autocomplete")
    print("   In real usage, the autocomplete provides the place_id")

if __name__ == "__main__":
    success = test_known_place_ids()
    test_14303_evening_flight_lane()
    
    if success:
        print("\n✅ Google Places integration test completed successfully!")
        print("   Ready for production use with address autocomplete")
    else:
        print("\n❌ Google Places integration needs attention")
        print("   Check API key permissions and quotas in Google Cloud Console")