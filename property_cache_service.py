"""
Property Data Caching Service
Optimizes external API calls and improves response times
"""
import json
import hashlib
import time
import os
from typing import Dict, Optional
import logging

class PropertyCacheService:
    def __init__(self, cache_dir='property_cache', cache_ttl=3600):
        """Initialize cache service with TTL of 1 hour by default"""
        self.cache_dir = cache_dir
        self.cache_ttl = cache_ttl
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _generate_cache_key(self, address: str, city: str, state: str, zip_code: str) -> str:
        """Generate unique cache key for property"""
        combined = f"{address.lower().strip()},{city.lower().strip()},{state.upper().strip()},{zip_code.strip()}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_cache_filepath(self, cache_key: str) -> str:
        """Get full path to cache file"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get_cached_property_data(self, address: str, city: str, state: str, zip_code: str) -> Optional[Dict]:
        """Retrieve cached property data if valid"""
        cache_key = self._generate_cache_key(address, city, state, zip_code)
        cache_file = self._get_cache_filepath(cache_key)
        
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is still valid
                cache_time = cached_data.get('cache_timestamp', 0)
                if time.time() - cache_time < self.cache_ttl:
                    logging.info(f"Cache hit for property: {address}")
                    return cached_data.get('property_data')
                else:
                    # Cache expired, remove file
                    os.remove(cache_file)
                    logging.info(f"Cache expired for property: {address}")
        
        except Exception as e:
            logging.warning(f"Cache read error: {e}")
        
        return None
    
    def cache_property_data(self, address: str, city: str, state: str, zip_code: str, property_data: Dict):
        """Cache property data with timestamp"""
        cache_key = self._generate_cache_key(address, city, state, zip_code)
        cache_file = self._get_cache_filepath(cache_key)
        
        try:
            cache_entry = {
                'cache_timestamp': time.time(),
                'property_data': property_data,
                'address_normalized': f"{address}, {city}, {state} {zip_code}"
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_entry, f, indent=2)
            
            logging.info(f"Property data cached for: {address}")
            
        except Exception as e:
            logging.error(f"Cache write error: {e}")
    
    def clear_expired_cache(self):
        """Remove all expired cache entries"""
        if not os.path.exists(self.cache_dir):
            return
        
        current_time = time.time()
        removed_count = 0
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.cache_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        cached_data = json.load(f)
                    
                    cache_time = cached_data.get('cache_timestamp', 0)
                    if current_time - cache_time >= self.cache_ttl:
                        os.remove(filepath)
                        removed_count += 1
                
                except Exception as e:
                    logging.warning(f"Error checking cache file {filename}: {e}")
        
        if removed_count > 0:
            logging.info(f"Removed {removed_count} expired cache entries")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        if not os.path.exists(self.cache_dir):
            return {'total_entries': 0, 'cache_size_mb': 0}
        
        cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
        total_size = 0
        
        for filename in cache_files:
            filepath = os.path.join(self.cache_dir, filename)
            total_size += os.path.getsize(filepath)
        
        return {
            'total_entries': len(cache_files),
            'cache_size_mb': round(total_size / (1024 * 1024), 2)
        }

# Global cache instance
property_cache = PropertyCacheService()