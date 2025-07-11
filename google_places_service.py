"""
Google Places Service using the official Place Details (New) API
Provides canonical address resolution with 30-day caching
"""

import os
import json
import time
import logging
import requests
import hashlib
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

class GooglePlacesService:
    def __init__(self):
        self.api_key = None
        self.initialized = False
        
    def _ensure_initialized(self):
        """Lazy initialization of API key"""
        if not self.initialized:
            self.api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
            if not self.api_key:
                raise ValueError("GOOGLE_MAPS_API_KEY environment variable is required")
            self.base_url = "https://places.googleapis.com/v1/places"
            self.validation_url = "https://addressvalidation.googleapis.com/v1:validateAddress"
            self.cache = {}  # In-memory cache (consider Redis for production)
            self.cache_ttl = timedelta(days=30)
            self.initialized = True
        
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
        self._ensure_initialized()
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
    
    def validate_address(self, street: str, city: str, state: str, zip_code: str) -> Dict[str, Any]:
        """
        Hard-validate address using Google Address Validation API
        
        Args:
            street: Street address line
            city: City name
            state: State abbreviation
            zip_code: ZIP code
            
        Returns:
            Dict containing validation result and canonical address data
            
        Raises:
            AddressValidationError: If address cannot be confirmed
        """
        self._ensure_initialized()
        # Generate cache key
        address_hash = self._generate_address_hash(street, city, state, zip_code)
        cache_key = f"addrval:{address_hash}"
        
        # Check cache first
        cached_result = self._get_cached_validation(cache_key)
        if cached_result:
            logging.info(f"Using cached address validation for: {street}, {city}, {state} {zip_code}")
            return cached_result
        
        # Make validation API call
        result = self._validate_address_with_api(street, city, state, zip_code)
        
        # Cache the result
        self._cache_validation_result(cache_key, result)
        
        return result
    
    def _validate_address_with_api(self, street: str, city: str, state: str, zip_code: str) -> Dict[str, Any]:
        """
        Call Google Address Validation API with proper payload structure
        """
        payload = {
            "address": {
                "regionCode": "US",
                "languageCode": "en", 
                "postalCode": zip_code,
                "administrativeArea": state,
                "locality": city,
                "addressLines": [street]
            },
            "enableUspsCass": True  # for highest accuracy in US
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key
        }
        
        try:
            response = requests.post(self.validation_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_validation_response(data, street, city, state, zip_code)
            elif response.status_code == 403:
                # Check if it's an API not enabled error
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', '')
                    if "has not been used" in error_message or "is disabled" in error_message:
                        raise AddressValidationError(f"Address Validation API not enabled: {error_message}")
                except json.JSONDecodeError:
                    pass
                logging.error(f"Address validation API permission error: {response.status_code} - {response.text}")
                raise AddressValidationError(f"Address Validation API not enabled or permission denied")
            else:
                logging.error(f"Address validation API error: {response.status_code} - {response.text}")
                raise AddressValidationError(f"Validation API returned status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise AddressValidationError(f"Network error during address validation: {str(e)}")
    
    def _parse_validation_response(self, data: Dict, original_street: str, original_city: str, 
                                 original_state: str, original_zip: str) -> Dict[str, Any]:
        """
        Parse Google Address Validation API response according to success rules
        """
        try:
            verdict = data.get('result', {}).get('verdict', {})
            
            # Apply success rules from specification
            has_unconfirmed = verdict.get('hasUnconfirmedComponents', True)
            has_inferred = verdict.get('hasInferredComponents', True) 
            address_complete = verdict.get('addressComplete', False)
            
            is_valid = (not has_unconfirmed and not has_inferred and address_complete)
            
            if not is_valid:
                logging.warning(f"Address validation failed: unconfirmed={has_unconfirmed}, inferred={has_inferred}, complete={address_complete}")
                raise AddressValidationError("We couldn't confirm that address. Please pick a Google-suggested address.")
            
            # Extract geocode location
            geocode = data.get('result', {}).get('geocode', {})
            location = geocode.get('location', {})
            
            if not location.get('latitude') or not location.get('longitude'):
                raise AddressValidationError("Location coordinates not available for this address")
            
            # Extract corrected address components
            address = data.get('result', {}).get('address', {})
            formatted_address = address.get('formattedAddress', f"{original_street}, {original_city}, {original_state} {original_zip}")
            
            return {
                'isValid': True,
                'formattedAddress': formatted_address,
                'latitude': float(location['latitude']),
                'longitude': float(location['longitude']),
                'components': {
                    'street': original_street,
                    'city': original_city,
                    'state': original_state,
                    'zip': original_zip
                },
                'verdict': verdict,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except (KeyError, ValueError, TypeError) as e:
            raise AddressValidationError(f"Failed to parse validation response: {str(e)}")
    
    def _generate_address_hash(self, street: str, city: str, state: str, zip_code: str) -> str:
        """Generate hash for address caching"""
        address_string = f"{street}|{city}|{state}|{zip_code}".lower().strip()
        return hashlib.md5(address_string.encode()).hexdigest()
    
    def _get_cached_validation(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached validation result if it exists and hasn't expired"""
        if cache_key not in self.cache:
            return None
        
        cached_data = self.cache[cache_key]
        cached_time = datetime.fromisoformat(cached_data['timestamp'])
        
        if datetime.utcnow() - cached_time > self.cache_ttl:
            del self.cache[cache_key]
            return None
        
        return cached_data
    
    def _cache_validation_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache validation result with 30-day TTL"""
        self.cache[cache_key] = result
        logging.info(f"Cached address validation result: {cache_key}")
    
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

class AddressValidationError(Exception):
    """Raised when address validation fails hard validation requirements"""
    pass


# Global instance
google_places_service = GooglePlacesService()