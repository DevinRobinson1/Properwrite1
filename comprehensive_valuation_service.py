"""
Comprehensive Property Valuation Service
Implements robust fallback chain for maximum property data coverage
"""
import os
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import time

class ComprehensiveValuationService:
    def __init__(self):
        """Initialize comprehensive valuation service with multiple data sources"""
        self.rapidapi_key = os.environ.get('RAPIDAPI_KEY')
        self.google_maps_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        self.cache = {}  # In-memory cache for 24h
        
        # RapidAPI endpoints for property valuation
        self.endpoints = {
            'zillow_deep': 'zillow57.p.rapidapi.com',
            'redfin_search': 'redfin-com-data.p.rapidapi.com',
            'realtor_detail': 'realtor56.p.rapidapi.com',
            'attom_avm': 'attom-property-api.p.rapidapi.com'
        }
        
    def get_comprehensive_valuation(self, place_id: str, address: str, city: str, state: str, zip_code: str) -> Dict:
        """
        Get property valuation using comprehensive fallback chain
        Returns valuation data with source attribution
        """
        try:
            # Check cache first (24h expiry)
            cache_key = f"{place_id}_{address.replace(' ', '_')}"
            if self._is_cached_valid(cache_key):
                logging.info(f"Using cached valuation for: {address}")
                return self.cache[cache_key]['data']
            
            # Step 1: Get precise coordinates from place_id
            coordinates = self._get_coordinates_from_place_id(place_id)
            
            # Step 2: Run primary valuation calls in parallel
            valuation_data = {
                'address': f"{address}, {city}, {state} {zip_code}",
                'place_id': place_id,
                'coordinates': coordinates,
                'valuations': {},
                'sources_tried': [],
                'fetch_timestamp': datetime.now().isoformat()
            }
            
            # Primary sources
            self._try_zillow_valuation(valuation_data, address, zip_code)
            self._try_redfin_valuation(valuation_data, address, city, state)
            self._try_realtor_valuation(valuation_data, coordinates)
            
            # Fallback sources if primary failed
            if not self._has_primary_valuation(valuation_data):
                self._try_attom_valuation(valuation_data, address, city, state, zip_code)
                self._try_estated_valuation(valuation_data, address, city, state, zip_code)
            
            # Cache result for 24 hours
            self._cache_valuation(cache_key, valuation_data)
            
            logging.info(f"Valuation complete for {address}. Sources: {valuation_data['sources_tried']}")
            return valuation_data
            
        except Exception as e:
            logging.error(f"Comprehensive valuation error for {address}: {e}")
            return {
                'address': f"{address}, {city}, {state} {zip_code}",
                'error': str(e),
                'sources_tried': ['error'],
                'valuations': {}
            }
    
    def _get_coordinates_from_place_id(self, place_id: str) -> Optional[Dict]:
        """Get precise lat/lng from Google Place ID"""
        if not place_id or not self.google_maps_key:
            return None
            
        try:
            url = f"https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'place_id': place_id,
                'key': self.google_maps_key
            }
            
            response = requests.get(url, params=params, timeout=4)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    location = data['results'][0]['geometry']['location']
                    return {
                        'latitude': location['lat'],
                        'longitude': location['lng']
                    }
        except Exception as e:
            logging.warning(f"Google Geocoding for place_id failed: {e}")
        
        return None
    
    def _try_zillow_valuation(self, valuation_data: Dict, address: str, zip_code: str):
        """Try Zillow Deep Search API"""
        if not self.rapidapi_key:
            return
            
        try:
            url = "https://zillow57.p.rapidapi.com/property"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "zillow57.p.rapidapi.com"
            }
            params = {
                "address": address,
                "zip": zip_code
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=4)
            valuation_data['sources_tried'].append('Zillow')
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, dict):
                    # Extract Zestimate
                    zestimate = None
                    if 'zestimate' in data:
                        zestimate = data['zestimate']
                    elif 'price' in data:
                        zestimate = data['price']
                    elif 'homeValue' in data:
                        zestimate = data['homeValue']
                    
                    if zestimate:
                        valuation_data['valuations']['zillow'] = {
                            'value': int(zestimate),
                            'source': 'Zillow Zestimate',
                            'confidence': 'high'
                        }
                        logging.info(f"Zillow valuation success: ${zestimate:,}")
        
        except Exception as e:
            logging.warning(f"Zillow valuation failed: {e}")
    
    def _try_redfin_valuation(self, valuation_data: Dict, address: str, city: str, state: str):
        """Try Redfin valuation via RapidAPI"""
        if not self.rapidapi_key:
            return
            
        try:
            # First get region info
            search_url = "https://redfin-com-data.p.rapidapi.com/properties/search"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "redfin-com-data.p.rapidapi.com"
            }
            
            search_params = {
                "query": f"{address}, {city}, {state}",
                "limit": 1
            }
            
            response = requests.get(search_url, headers=headers, params=search_params, timeout=4)
            valuation_data['sources_tried'].append('Redfin')
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, dict) and 'data' in data:
                    properties = data['data']
                    if properties and len(properties) > 0:
                        prop = properties[0]
                        
                        # Extract Redfin estimate
                        estimate = None
                        if 'price' in prop:
                            estimate = prop['price']
                        elif 'listPrice' in prop:
                            estimate = prop['listPrice']
                        elif 'homeValue' in prop:
                            estimate = prop['homeValue']
                        
                        if estimate:
                            valuation_data['valuations']['redfin'] = {
                                'value': int(estimate),
                                'source': 'Redfin Estimate',
                                'confidence': 'high'
                            }
                            logging.info(f"Redfin valuation success: ${estimate:,}")
        
        except Exception as e:
            logging.warning(f"Redfin valuation failed: {e}")
    
    def _try_realtor_valuation(self, valuation_data: Dict, coordinates: Optional[Dict]):
        """Try Realtor.com valuation via RapidAPI"""
        if not self.rapidapi_key or not coordinates:
            return
            
        try:
            url = "https://realtor56.p.rapidapi.com/properties/v3/detail"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "realtor56.p.rapidapi.com"
            }
            params = {
                "lat": coordinates['latitude'],
                "lng": coordinates['longitude']
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=4)
            valuation_data['sources_tried'].append('Realtor.com')
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, dict):
                    # Extract Realtor estimate
                    estimate = None
                    if 'estimate' in data:
                        estimate = data['estimate']
                    elif 'price' in data:
                        estimate = data['price']
                    elif 'homeValue' in data:
                        estimate = data['homeValue']
                    
                    if estimate:
                        valuation_data['valuations']['realtor'] = {
                            'value': int(estimate),
                            'source': 'Realtor.com Estimate',
                            'confidence': 'high'
                        }
                        logging.info(f"Realtor.com valuation success: ${estimate:,}")
        
        except Exception as e:
            logging.warning(f"Realtor.com valuation failed: {e}")
    
    def _try_attom_valuation(self, valuation_data: Dict, address: str, city: str, state: str, zip_code: str):
        """Try ATTOM AVM as fallback"""
        if not self.rapidapi_key:
            return
            
        try:
            url = "https://attom-property-api.p.rapidapi.com/avm"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "attom-property-api.p.rapidapi.com"
            }
            params = {
                "address": address,
                "city": city,
                "state": state,
                "zip": zip_code
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=4)
            valuation_data['sources_tried'].append('ATTOM')
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, dict):
                    # Extract ATTOM AVM
                    avm_value = None
                    if 'avm' in data:
                        avm_value = data['avm']
                    elif 'estimate' in data:
                        avm_value = data['estimate']
                    elif 'value' in data:
                        avm_value = data['value']
                    
                    if avm_value:
                        valuation_data['valuations']['attom'] = {
                            'value': int(avm_value),
                            'source': 'ATTOM AVM',
                            'confidence': 'medium'
                        }
                        logging.info(f"ATTOM AVM success: ${avm_value:,}")
        
        except Exception as e:
            logging.warning(f"ATTOM AVM failed: {e}")
    
    def _try_estated_valuation(self, valuation_data: Dict, address: str, city: str, state: str, zip_code: str):
        """Try Estated API as final fallback"""
        try:
            # Note: Estated requires separate API key setup
            # This is a placeholder for the endpoint structure
            url = "https://api.estated.com/property/v3"
            params = {
                "token": os.environ.get('ESTATED_API_KEY'),
                "address": f"{address}, {city}, {state} {zip_code}"
            }
            
            if not params['token']:
                return
            
            response = requests.get(url, params=params, timeout=4)
            valuation_data['sources_tried'].append('Estated')
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, dict):
                    # Extract Estated AVM
                    avm_value = None
                    if 'valuation' in data:
                        avm_value = data['valuation']
                    elif 'estimate' in data:
                        avm_value = data['estimate']
                    
                    if avm_value:
                        valuation_data['valuations']['estated'] = {
                            'value': int(avm_value),
                            'source': 'Estated AVM',
                            'confidence': 'medium'
                        }
                        logging.info(f"Estated AVM success: ${avm_value:,}")
        
        except Exception as e:
            logging.warning(f"Estated AVM failed: {e}")
    
    def _has_primary_valuation(self, valuation_data: Dict) -> bool:
        """Check if any primary source (Zillow, Redfin, Realtor) provided valuation"""
        primary_sources = ['zillow', 'redfin', 'realtor']
        return any(source in valuation_data['valuations'] for source in primary_sources)
    
    def _is_cached_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid (within 24 hours)"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        return (datetime.now() - cached_time) < timedelta(hours=24)
    
    def _cache_valuation(self, cache_key: str, valuation_data: Dict):
        """Cache valuation data for 24 hours"""
        self.cache[cache_key] = {
            'data': valuation_data,
            'timestamp': datetime.now()
        }
    
    def get_best_estimate(self, valuation_data: Dict) -> Optional[Dict]:
        """Get the best available estimate with source priority"""
        valuations = valuation_data.get('valuations', {})
        
        # Priority order: Zillow > Redfin > Realtor > ATTOM > Estated
        priority_order = ['zillow', 'redfin', 'realtor', 'attom', 'estated']
        
        for source in priority_order:
            if source in valuations:
                return {
                    'estimate': valuations[source]['value'],
                    'source': valuations[source]['source'],
                    'confidence': valuations[source]['confidence']
                }
        
        return None
    
    def format_error_message(self, valuation_data: Dict) -> str:
        """Format comprehensive error message showing all sources tried"""
        sources_tried = valuation_data.get('sources_tried', [])
        if sources_tried:
            return f"Not available (Tried: {', '.join(sources_tried)})"
        else:
            return "Not available (Property may be unlisted)"

# Global instance
comprehensive_valuation_service = ComprehensiveValuationService()