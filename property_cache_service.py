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
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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
    
    def _sanitize_url(self, url: str) -> str:
        """Remove API key from URL while preserving other parameters"""
        if not url or 'googleapis.com' not in url:
            return url
        
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Remove the key parameter
            if 'key' in query_params:
                del query_params['key']
            
            # Reconstruct URL without the key
            new_query = urlencode(query_params, doseq=True)
            new_parsed = parsed._replace(query=new_query)
            sanitized_url = urlunparse(new_parsed)
            
            logging.debug(f"Sanitized URL: removed API key from {parsed.netloc}")
            return sanitized_url
        except Exception as e:
            logging.error(f"Error sanitizing URL: {e}")
            return url

    def _sanitize_data_recursive(self, obj):
        """Recursively sanitize data to remove API keys from URLs"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and ('googleapis.com' in value and 'key=' in value):
                    obj[key] = self._sanitize_url(value)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, str) and ('googleapis.com' in item and 'key=' in item):
                            value[i] = self._sanitize_url(item)
                        elif isinstance(item, (dict, list)):
                            self._sanitize_data_recursive(item)
                elif isinstance(value, (dict, list)):
                    self._sanitize_data_recursive(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str) and ('googleapis.com' in item and 'key=' in item):
                    obj[i] = self._sanitize_url(item)
                elif isinstance(item, (dict, list)):
                    self._sanitize_data_recursive(item)

    def cache_property_data(self, address: str, city: str, state: str, zip_code: str, property_data: Dict):
        """Cache property data with timestamp and sanitization"""
        cache_key = self._generate_cache_key(address, city, state, zip_code)
        cache_file = self._get_cache_filepath(cache_key)
        
        try:
            # Deep copy and sanitize the property data to remove API keys
            import copy
            sanitized_property_data = copy.deepcopy(property_data)
            self._sanitize_data_recursive(sanitized_property_data)
            
            cache_entry = {
                'cache_timestamp': time.time(),
                'property_data': sanitized_property_data,
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