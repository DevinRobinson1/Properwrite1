"""
Google Places Service using the official Place Details (New) API
Provides canonical address resolution with 30-day caching
"""

import os
import json
import time
import logging
import requests
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

class GooglePlacesService:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY environment variable is required")
        
        self.base_url = "https://places.googleapis.com/v1/places"
        self.cache = {}  # In-memory cache (consider Redis for production)
        self.cache_ttl = timedelta(days=30)
        
    def get_canonical_address(self, place_id: str) -> Dict[str, Any]:
        """
        Get canonical address using Google Places "Place Details (New)" API
        
        Args:
            place_id: Google Places place_id from autocomplete
            
        Returns:
            Dict containing:
            - formattedAddress: string
            - lat: number  
            - lng: number
            - placeId: string
        """
        if not place_id:
            raise ValueError("place_id is required")
        
        # Check cache first
        cached_result = self._get_cached_result(place_id)
        if cached_result:
            logging.info(f"Using cached result for place_id: {place_id}")
            return cached_result
        
        # Make API call with exponential backoff
        result = self._fetch_place_details_with_retry(place_id)
        
        # Cache the result
        self._cache_result(place_id, result)
        
        return result
    
    def _fetch_place_details_with_retry(self, place_id: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Fetch place details with exponential backoff for rate limiting
        """
        url = f"{self.base_url}/{place_id}"
        headers = {
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'displayName,formattedAddress,location'
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_place_details(data, place_id)
                    
                elif response.status_code == 429:  # Rate limited
                    wait_time = (2 ** attempt) + 1  # Exponential backoff
                    logging.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                    time.sleep(wait_time)
                    continue
                    
                elif response.status_code == 404:
                    raise AddressNotFoundError(f"Place not found: {place_id}")
                    
                else:
                    logging.error(f"Google Places API error: {response.status_code} - {response.text}")
                    raise GooglePlacesAPIError(f"API returned status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise GooglePlacesAPIError(f"Network error after {max_retries} attempts: {str(e)}")
                wait_time = (2 ** attempt) + 1
                logging.warning(f"Network error, retrying in {wait_time}s: {str(e)}")
                time.sleep(wait_time)
        
        raise GooglePlacesAPIError(f"Failed to fetch place details after {max_retries} attempts")
    
    def _parse_place_details(self, data: Dict, place_id: str) -> Dict[str, Any]:
        """
        Parse Google Places API response into canonical format
        """
        try:
            formatted_address = data.get('formattedAddress')
            location = data.get('location', {})
            
            if not formatted_address:
                raise AddressNotFoundError("formattedAddress missing from API response")
            
            if not location.get('latitude') or not location.get('longitude'):
                raise AddressNotFoundError("Location coordinates missing from API response")
            
            return {
                'formattedAddress': formatted_address,
                'lat': float(location['latitude']),
                'lng': float(location['longitude']),
                'placeId': place_id,
                'displayName': data.get('displayName', {}).get('text', ''),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except (KeyError, ValueError, TypeError) as e:
            raise GooglePlacesAPIError(f"Failed to parse API response: {str(e)}")
    
    def _get_cached_result(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result if it exists and hasn't expired
        """
        cache_key = f"places:{place_id}"
        
        if cache_key not in self.cache:
            return None
        
        cached_data = self.cache[cache_key]
        cached_time = datetime.fromisoformat(cached_data['timestamp'])
        
        if datetime.utcnow() - cached_time > self.cache_ttl:
            del self.cache[cache_key]
            return None
        
        return cached_data
    
    def _cache_result(self, place_id: str, result: Dict[str, Any]) -> None:
        """
        Cache the result with 30-day TTL
        """
        cache_key = f"places:{place_id}"
        self.cache[cache_key] = result
        logging.info(f"Cached place details for place_id: {place_id}")
    
    def clear_cache(self, place_id: str = None) -> None:
        """
        Clear cache for specific place_id or all cached data
        """
        if place_id:
            cache_key = f"places:{place_id}"
            self.cache.pop(cache_key, None)
        else:
            self.cache.clear()


class GooglePlacesAPIError(Exception):
    """Raised when Google Places API returns an error"""
    pass


class AddressNotFoundError(Exception):
    """Raised when address cannot be found or resolved"""
    pass


# Global instance
google_places_service = GooglePlacesService()