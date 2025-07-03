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
        
    def get_comprehensive_valuation(self, place_id: str, address: str, city: str, state: str, zip_code: str, latitude: float = None, longitude: float = None) -> Dict:
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
            
            # Step 1: Use provided coordinates or get from place_id
            if latitude and longitude:
                coordinates = {'latitude': latitude, 'longitude': longitude}
            else:
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
            self._try_zillow_valuation(valuation_data, address, city, state, zip_code)
            self._try_redfin_valuation(valuation_data, address, city, state)
            self._try_realtor_valuation(valuation_data, coordinates)
            
            # Fallback sources if primary failed
            if not self._has_primary_valuation(valuation_data):
                # ATTOM requires separate API key, skipping for now
                # self._try_attom_valuation(valuation_data, address, city, state, zip_code)
                # self._try_estated_valuation(valuation_data, address, city, state, zip_code)
                pass
            
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
    
    def _try_zillow_valuation(self, valuation_data: Dict, address: str, city: str, state: str, zip_code: str):
        """Try Zillow Deep Search API"""
        if not self.rapidapi_key:
            return
            
        try:
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
            }
            # First, search for property to get zpid
            search_url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
            # Try specific address first, then fallback to area search
            search_params = {
                "location": f"{city}, {state}",
                "status_type": "ForSale",
                "home_type": "Houses"
            }
            
            search_response = requests.get(search_url, headers=headers, params=search_params, timeout=5)
            valuation_data['sources_tried'].append('Zillow')
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                
                # Find the property in search results
                if search_data and 'props' in search_data:
                    props = search_data['props']
                    if props and len(props) > 0:
                        # Try to find exact match by address
                        zpid = None
                        target_address_lower = address.lower().strip()
                        
                        # Extract street number for better matching
                        import re
                        street_number_match = re.search(r'^(\d+)', address)
                        target_street_number = street_number_match.group(1) if street_number_match else None
                        
                        best_match = None
                        best_score = 0
                        
                        for prop in props:
                            prop_address = prop.get('address', '').lower().strip()
                            score = 0
                            
                            # Check if street number matches
                            if target_street_number:
                                prop_street_number_match = re.search(r'^(\d+)', prop_address)
                                if prop_street_number_match and prop_street_number_match.group(1) == target_street_number:
                                    score += 50
                            
                            # Check address similarity
                            if target_address_lower in prop_address or prop_address in target_address_lower:
                                score += 30
                            
                            # Check for partial matches
                            target_words = set(target_address_lower.split())
                            prop_words = set(prop_address.split())
                            common_words = target_words.intersection(prop_words)
                            score += len(common_words) * 2
                            
                            if score > best_score:
                                best_score = score
                                best_match = prop
                        
                        if best_match and best_score > 10:
                            zpid = best_match.get('zpid')
                            logging.info(f"Found matching property (score: {best_score}): {best_match.get('address')}")
                        elif props:
                            # Use first property as fallback for area estimates
                            zpid = props[0].get('zpid')
                            logging.info(f"Using first property as area estimate: {props[0].get('address')}")
                            logging.info(f"Available properties in area: {[prop.get('address') for prop in props[:3]]}")
                        
                        if zpid:
                            # Now get detailed property info
                            detail_url = "https://zillow-com1.p.rapidapi.com/property"
                            detail_params = {"zpid": zpid}
                            
                            detail_response = requests.get(detail_url, headers=headers, params=detail_params, timeout=5)
                            
                            if detail_response.status_code == 200:
                                detail_data = detail_response.json()
                                logging.info(f"Zillow detail response keys: {list(detail_data.keys()) if detail_data else 'None'}")
                                
                                # Extract Zestimate from multiple possible locations
                                zestimate = None
                                if detail_data:
                                    # Try different possible zestimate locations
                                    zestimate = (detail_data.get('zestimate') or 
                                               detail_data.get('price') or
                                               detail_data.get('homeValue'))
                                    
                                    # Try nested locations
                                    if not zestimate and 'resoFacts' in detail_data:
                                        reso_facts = detail_data['resoFacts']
                                        zestimate = (reso_facts.get('zestimate') or
                                                   reso_facts.get('lastSoldPrice') or
                                                   reso_facts.get('listPrice'))
                                    
                                    # Try listing info
                                    if not zestimate and 'listingDataSource' in detail_data:
                                        listing = detail_data['listingDataSource']
                                        zestimate = listing.get('lastSoldPrice')
                                    
                                    if zestimate:
                                        valuation_data['valuations']['zillow'] = {
                                            'value': int(zestimate),
                                            'source': 'Zillow Property Data',
                                            'confidence': 'high'
                                        }
                                        logging.info(f"Zillow valuation success: ${zestimate:,}")
                                    else:
                                        logging.info(f"No valuation found in Zillow detail data: {str(detail_data)[:500]}")
                            else:
                                logging.warning(f"Zillow detail API failed: {detail_response.status_code} - {detail_response.text[:200]}")
                    else:
                        logging.warning("No properties found in Zillow search")
                else:
                    logging.warning("Invalid Zillow search response format")
            else:
                logging.warning(f"Zillow search API failed: {search_response.status_code}")
        
        except Exception as e:
            logging.warning(f"Zillow valuation failed: {e}")
    
    def _try_redfin_valuation(self, valuation_data: Dict, address: str, city: str, state: str):
        """Try Redfin valuation via RapidAPI"""
        if not self.rapidapi_key:
            return
            
        try:
            # First get region info for the city
            search_url = "https://redfin-com-data.p.rapidapi.com/properties/search-sale"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "redfin-com-data.p.rapidapi.com"
            }
            
            # Map common cities to region IDs
            region_map = {
                'charlotte': '11997',
                'raleigh': '41593',
                'atlanta': '30756',
                'nashville': '39593'
            }
            
            region_id = region_map.get(city.lower(), '11997')  # Default to Charlotte
            
            search_params = {
                "regionId": region_id,
                "sortBy": "relevance",
                "limit": 20
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