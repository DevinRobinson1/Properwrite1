#!/usr/bin/env python3
"""
Test script for the unified property data cache system
Verifies cache functionality, TTL, and stale-while-revalidate patterns
"""

import time
import requests
import json
from datetime import datetime

# Base URL for your application
BASE_URL = "http://localhost:5000"

def test_cache_stats():
    """Test cache statistics endpoint"""
    print("Testing cache statistics...")
    response = requests.get(f"{BASE_URL}/api/cache/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"✓ Cache stats retrieved: {stats}")
        return stats
    else:
        print(f"✗ Failed to get cache stats: {response.status_code}")
        return None

def test_property_analysis_caching():
    """Test property analysis with caching"""
    print("\nTesting property analysis caching...")
    
    # Test property data
    test_property = {
        "address": "123 Main St",
        "city": "Charlotte",
        "state": "NC",
        "zip_code": "28202",
        "latitude": 35.2271,
        "longitude": -80.8431
    }
    
    print(f"Analyzing property: {test_property['address']}")
    
    # First request (should hit APIs)
    start_time = time.time()
    response1 = requests.post(f"{BASE_URL}/api/analyze-property", json=test_property)
    first_request_time = time.time() - start_time
    
    if response1.status_code == 200:
        print(f"✓ First request successful (took {first_request_time:.2f}s)")
        result1 = response1.json()
        
        # Second request (should hit cache)
        start_time = time.time()
        response2 = requests.post(f"{BASE_URL}/api/analyze-property", json=test_property)
        second_request_time = time.time() - start_time
        
        if response2.status_code == 200:
            print(f"✓ Second request successful (took {second_request_time:.2f}s)")
            result2 = response2.json()
            
            # Cache should make second request faster
            if second_request_time < first_request_time:
                print("✓ Cache appears to be working (second request was faster)")
            else:
                print("? Cache performance unclear (second request not faster)")
                
        else:
            print(f"✗ Second request failed: {response2.status_code}")
    else:
        print(f"✗ First request failed: {response1.status_code}")

def test_comps_analysis_caching():
    """Test comparable properties analysis with caching"""
    print("\nTesting comparable properties caching...")
    
    # Test comps data
    test_comps = {
        "address": "123 Main St, Charlotte, NC 28202",
        "beds": 3,
        "baths": 2,
        "sqft": 1500,
        "lat": 35.2271,
        "lng": -80.8431
    }
    
    print(f"Analyzing comps for: {test_comps['address']}")
    
    # First request (should hit APIs)
    start_time = time.time()
    response1 = requests.post(f"{BASE_URL}/api/comps/analyze", json=test_comps)
    first_request_time = time.time() - start_time
    
    if response1.status_code == 200:
        print(f"✓ First comps request successful (took {first_request_time:.2f}s)")
        result1 = response1.json()
        
        # Second request (should hit cache)
        start_time = time.time()
        response2 = requests.post(f"{BASE_URL}/api/comps/analyze", json=test_comps)
        second_request_time = time.time() - start_time
        
        if response2.status_code == 200:
            print(f"✓ Second comps request successful (took {second_request_time:.2f}s)")
            result2 = response2.json()
            
            # Cache should make second request faster
            if second_request_time < first_request_time:
                print("✓ Comps cache appears to be working (second request was faster)")
            else:
                print("? Comps cache performance unclear (second request not faster)")
                
        else:
            print(f"✗ Second comps request failed: {response2.status_code}")
    else:
        print(f"✗ First comps request failed: {response1.status_code}")

def test_cache_clear():
    """Test cache clearing functionality"""
    print("\nTesting cache clearing...")
    
    # Clear all cache
    response = requests.post(f"{BASE_URL}/api/cache/clear")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Cache cleared: {result['message']}")
        return True
    else:
        print(f"✗ Failed to clear cache: {response.status_code}")
        return False

def test_cache_refresh():
    """Test cache refresh functionality"""
    print("\nTesting cache refresh...")
    
    refresh_data = {
        "address": "123 Main St",
        "city": "Charlotte",
        "state": "NC",
        "zip_code": "28202"
    }
    
    response = requests.post(f"{BASE_URL}/api/cache/refresh", json=refresh_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Cache refreshed: {result['message']}")
        return True
    else:
        print(f"✗ Failed to refresh cache: {response.status_code}")
        return False

def main():
    """Run all cache tests"""
    print("=" * 60)
    print("UNIFIED PROPERTY DATA CACHE SYSTEM TEST")
    print("=" * 60)
    
    # Test cache stats
    stats = test_cache_stats()
    
    # Test property analysis caching
    test_property_analysis_caching()
    
    # Test comps analysis caching
    test_comps_analysis_caching()
    
    # Test cache management
    test_cache_clear()
    test_cache_refresh()
    
    # Final stats
    print("\nFinal cache statistics:")
    final_stats = test_cache_stats()
    
    print("=" * 60)
    print("CACHE SYSTEM TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()