"""
Comprehensive Property Valuation Service
Implements robust fallback chain for maximum property data coverage
"""

import requests
import logging
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from address_utils import to_zillow_search_string

# Configure logging
logging.basicConfig(level=logging.INFO)

class ComprehensiveValuationService:
    def __init__(self):
        """Initialize comprehensive valuation service with multiple data sources"""
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        self.google_maps_key = os.getenv('GMAPS_API_KEY')
        self.cache_expiry_hours = 24
        
        if not self.rapidapi_key:
            logging.warning("RAPIDAPI_KEY not found in environment variables")
        if not self.google_maps_key:
            logging.warning("GMAPS_API_KEY not found in environment variables")
    
    def get_comprehensive_valuation(self, place_id: str, address: str, city: str, state: str, zip_code: str, latitude: float = None, longitude: float = None) -> Dict:
        """
        Get property valuation using comprehensive fallback chain
        Returns valuation data with source attribution
        """
        valuation_data = {
            'valuations': {},
            'sources_tried': [],
            'sources_used': [],
            'address_info': {
                'address': address,
                'city': city,
                'state': state,
                'zip_code': zip_code,
                'latitude': latitude,
                'longitude': longitude
            },
            'cache_used': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check cache first
        cache_key = f"valuation_{place_id}_{address}_{city}_{state}_{zip_code}"
        if self._is_cached_valid(cache_key):
            cached_data = self._get_cached_valuation(cache_key)
            if cached_data:
                cached_data['cache_used'] = True
                return cached_data
        
        # Get coordinates if not provided
        if not latitude or not longitude:
            coords = self._get_coordinates_from_place_id(place_id)
            if coords:
                latitude = coords['latitude']
                longitude = coords['longitude']
                valuation_data['address_info']['latitude'] = latitude
                valuation_data['address_info']['longitude'] = longitude
        
        # Try primary sources in order of preference
        self._try_zillow_valuation(valuation_data, address, city, state, zip_code)
        self._try_redfin_valuation(valuation_data, address, city, state, zip_code)
        self._try_realtor_valuation(valuation_data, address, city, state, zip_code)
        
        # Cache the results
        self._cache_valuation(cache_key, valuation_data)
        
        return valuation_data
    
    def _get_coordinates_from_place_id(self, place_id: str) -> Optional[Dict]:
        """Get precise lat/lng from Google Place ID"""
        if not self.google_maps_key or not place_id:
            return None
        
        try:
            url = f"https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                'place_id': place_id,
                'fields': 'geometry',
                'key': self.google_maps_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('result') and data['result'].get('geometry'):
                    location = data['result']['geometry']['location']
                    return {
                        'latitude': location['lat'],
                        'longitude': location['lng']
                    }
        except Exception as e:
            logging.warning(f"Google Geocoding for place_id failed: {e}")
        
        return None
    
    def _try_zillow_valuation(self, valuation_data: Dict, address: str, city: str, state: str, zip_code: str):
        """Try Zillow Deep Search API with enhanced address normalization"""
        if not self.rapidapi_key:
            return
            
        try:
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
            }
            
            # Normalize address to prevent duplicate tokens and remove subdivision noise
            # The address already contains city/state from Google Places, so use it directly
            normalized_location = to_zillow_search_string(address)
            
            # Build search URL with normalized address
            search_url = (
                f"https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
                f"?location={normalized_location}"
                f"&status_type=RecentlySold"
                f"&home_type=Houses"
            )
            
            valuation_data['sources_tried'].append('Zillow')
            logging.info(f"Zillow search with normalized address: {normalized_location}")
            
            search_response = requests.get(search_url, headers=headers, timeout=10)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                logging.info(f"Zillow API response type: {type(search_data)}, length: {len(search_data) if isinstance(search_data, list) else 'N/A'}")
                
                # Handle array response format (free tier)
                if isinstance(search_data, list) and len(search_data) > 0:
                    # Use first match from array response
                    property_match = search_data[0]
                    zpid = property_match.get('zpid')
                    matched_address = property_match.get('address', '')
                    
                    if zpid:
                        logging.info(f"Found ZPID {zpid} for {matched_address}")
                        
                        # Get detailed property information
                        detail_url = "https://zillow-com1.p.rapidapi.com/property"
                        detail_params = {"zpid": zpid}
                        
                        detail_response = requests.get(detail_url, headers=headers, params=detail_params, timeout=10)
                        
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            
                            # Enhanced extraction with multiple fallback methods
                            zestimate = self._extract_zillow_data_with_regex(detail_data)
                            
                            if zestimate:
                                valuation_data['valuations']['zillow'] = {
                                    'zestimate': int(zestimate),
                                    'source': 'Zillow Property Data',
                                    'confidence': 'high',
                                    'zpid': zpid,
                                    'matched_address': matched_address
                                }
                                valuation_data['sources_used'].append('Zillow')
                                logging.info(f"Zillow valuation success: ${zestimate:,}")
                                return
                            else:
                                logging.info(f"No valuation found in Zillow detail data")
                        else:
                            logging.warning(f"Zillow detail API failed: {detail_response.status_code}")
                    else:
                        logging.warning("No ZPID found in Zillow search result")
                else:
                    logging.warning("No properties found in Zillow search or invalid response format")
            else:
                logging.warning(f"Zillow search API failed: {search_response.status_code}")
                if search_response.status_code == 400:
                    logging.warning("Zillow 400 error - address format issue detected")
                    
        except Exception as e:
            logging.warning(f"Zillow valuation failed: {e}")
    
    def _extract_zillow_data_with_regex(self, detail_data: Dict) -> Optional[int]:
        """
        Enhanced Zillow data extraction using multiple patterns and fallbacks
        More resilient to API response variations
        """
        if not detail_data:
            return None
            
        # Try multiple field patterns for zestimate
        for field_name in ['zestimate', 'price', 'priceHistory', 'value', 'estimatedValue']:
            if field_name in detail_data:
                field_value = detail_data[field_name]
                
                # Handle different data types
                if isinstance(field_value, (int, float)) and field_value > 0:
                    return int(field_value)
                elif isinstance(field_value, str) and field_value.replace(',', '').isdigit():
                    return int(field_value.replace(',', ''))
                elif isinstance(field_value, list) and len(field_value) > 0:
                    # Handle price history arrays
                    if isinstance(field_value[0], dict) and 'price' in field_value[0]:
                        return int(field_value[0]['price'])
                elif isinstance(field_value, dict):
                    # Handle nested objects
                    if 'amount' in field_value:
                        return int(field_value['amount'])
                    elif 'value' in field_value:
                        return int(field_value['value'])
        
        # Try regex patterns as final fallback
        import re
        detail_str = str(detail_data).lower()
        
        # Look for price patterns
        price_patterns = [
            r'["\']zestimate["\']:\s*(\d+)',
            r'["\']price["\']:\s*(\d+)',
            r'["\']value["\']:\s*(\d+)',
            r'\$(\d{1,3}(?:,\d{3})*)'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, detail_str)
            if matches:
                try:
                    price = int(matches[0].replace(',', ''))
                    if 50000 <= price <= 10000000:  # Reasonable price range
                        return price
                except ValueError:
                    continue
        
        return None
    
    def _try_redfin_valuation(self, valuation_data: Dict, address: str, city: str, state: str, zip_code: str):
        """Try Redfin valuation via RapidAPI with enhanced error handling"""
        if not self.rapidapi_key:
            return
            
        try:
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "redfin-com-data.p.rapidapi.com"
            }
            
            # Search for property first
            search_url = "https://redfin-com-data.p.rapidapi.com/properties/search"
            search_params = {
                "query": f"{address}, {city}, {state} {zip_code}",
                "limit": 5
            }
            
            valuation_data['sources_tried'].append('Redfin')
            
            search_response = requests.get(search_url, headers=headers, params=search_params, timeout=10)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                
                if search_data and 'properties' in search_data:
                    properties = search_data['properties']
                    if properties and len(properties) > 0:
                        # Find best matching property
                        best_match = None
                        best_score = 0
                        
                        for prop in properties:
                            prop_address = prop.get('address', '').lower()
                            target_address = address.lower()
                            
                            # Simple similarity scoring
                            score = self._calculate_address_similarity(target_address, prop_address)
                            
                            if score > best_score:
                                best_score = score
                                best_match = prop
                        
                        if best_match and best_score > 0.3:  # Minimum similarity threshold
                            estimate = best_match.get('price') or best_match.get('estimate')
                            if estimate:
                                valuation_data['valuations']['redfin'] = {
                                    'estimate': int(estimate),
                                    'source': 'Redfin Property Data',
                                    'confidence': 'medium',
                                    'matched_address': best_match.get('address', ''),
                                    'similarity_score': best_score
                                }
                                valuation_data['sources_used'].append('Redfin')
                                logging.info(f"Redfin valuation success: ${estimate:,}")
                                return
                        else:
                            logging.warning("No matching properties found in Redfin search")
                    else:
                        logging.warning("No properties found in Redfin search")
                else:
                    logging.warning("Invalid Redfin search response format")
            else:
                logging.warning(f"Redfin search API failed: {search_response.status_code}")
                
        except Exception as e:
            logging.warning(f"Redfin valuation failed: {e}")
    
    def _try_realtor_valuation(self, valuation_data: Dict, address: str, city: str, state: str, zip_code: str):
        """Try Realtor.com valuation via RapidAPI"""
        if not self.rapidapi_key:
            return
            
        try:
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "realtor-search.p.rapidapi.com"
            }
            
            # Search for property
            search_url = "https://realtor-search.p.rapidapi.com/properties/search"
            search_params = {
                "query": f"{address}, {city}, {state} {zip_code}",
                "limit": 5
            }
            
            valuation_data['sources_tried'].append('Realtor.com')
            
            search_response = requests.get(search_url, headers=headers, params=search_params, timeout=10)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                
                if search_data and 'properties' in search_data:
                    properties = search_data['properties']
                    if properties and len(properties) > 0:
                        # Find best matching property
                        best_match = None
                        best_score = 0
                        
                        for prop in properties:
                            prop_address = prop.get('address', '').lower()
                            target_address = address.lower()
                            
                            score = self._calculate_address_similarity(target_address, prop_address)
                            
                            if score > best_score:
                                best_score = score
                                best_match = prop
                        
                        if best_match and best_score > 0.3:
                            estimate = best_match.get('price') or best_match.get('list_price')
                            if estimate:
                                valuation_data['valuations']['realtor'] = {
                                    'estimate': int(estimate),
                                    'source': 'Realtor.com Property Data',
                                    'confidence': 'medium',
                                    'matched_address': best_match.get('address', ''),
                                    'similarity_score': best_score
                                }
                                valuation_data['sources_used'].append('Realtor.com')
                                logging.info(f"Realtor.com valuation success: ${estimate:,}")
                                return
                        else:
                            logging.warning("No matching properties found in Realtor.com search")
                    else:
                        logging.warning("No properties found in Realtor.com search")
                else:
                    logging.warning("Invalid Realtor.com search response format")
            else:
                logging.warning(f"Realtor.com search API failed: {search_response.status_code}")
                
        except Exception as e:
            logging.warning(f"Realtor.com valuation failed: {e}")
    
    def _calculate_address_similarity(self, target_address: str, comparison_address: str) -> float:
        """Calculate similarity score between two addresses"""
        if not target_address or not comparison_address:
            return 0.0
        
        # Normalize addresses
        target_words = set(target_address.lower().split())
        comparison_words = set(comparison_address.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(target_words.intersection(comparison_words))
        union = len(target_words.union(comparison_words))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _is_cached_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid (within 24 hours)"""
        cache_file = f"property_cache/{cache_key}.json"
        if not os.path.exists(cache_file):
            return False
        
        try:
            # Check file modification time
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            expiry_time = file_time + timedelta(hours=self.cache_expiry_hours)
            return datetime.now() < expiry_time
        except Exception:
            return False
    
    def _get_cached_valuation(self, cache_key: str) -> Optional[Dict]:
        """Get cached valuation data"""
        cache_file = f"property_cache/{cache_key}.json"
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def _cache_valuation(self, cache_key: str, valuation_data: Dict):
        """Cache valuation data for 24 hours"""
        try:
            os.makedirs("property_cache", exist_ok=True)
            cache_file = f"property_cache/{cache_key}.json"
            with open(cache_file, 'w') as f:
                json.dump(valuation_data, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to cache valuation data: {e}")
    
    def get_best_estimate(self, valuation_data: Dict) -> Optional[Dict]:
        """Get the best available estimate with source priority"""
        valuations = valuation_data.get('valuations', {})
        
        # Priority order: Zillow > Redfin > Realtor.com
        for source in ['zillow', 'redfin', 'realtor']:
            if source in valuations:
                valuation = valuations[source].copy()
                # Standardize the estimate key for consistent access
                if 'zestimate' in valuation:
                    valuation['estimate'] = valuation['zestimate']
                elif 'estimate' not in valuation:
                    # Try other common estimate keys
                    for key in ['price', 'value', 'list_price']:
                        if key in valuation:
                            valuation['estimate'] = valuation[key]
                            break
                return valuation
        
        return None
    
    def format_error_message(self, valuation_data: Dict) -> str:
        """Format comprehensive error message showing all sources tried"""
        sources_tried = valuation_data.get('sources_tried', [])
        if not sources_tried:
            return "No property valuation sources were attempted."
        
        return f"Property valuation attempted from {', '.join(sources_tried)} but no estimates were found. This property may not be listed in external databases."

# Global instance
comprehensive_valuation_service = ComprehensiveValuationService()