"""
Comprehensive Property Valuation Service
Implements robust fallback chain for maximum property data coverage
"""
import os
import logging
import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import time
from bs4 import BeautifulSoup
from urllib.parse import quote

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
            
            # Primary sources (based on available RapidAPI subscriptions)
            self._try_zillow_valuation(valuation_data, address, city, state, zip_code)
            
            # Skip scraping fallback to avoid browser security errors
                
            self._try_redfin_valuation(valuation_data, address, city, state)
            # Note: Realtor.com API requires separate subscription
            self._add_subscription_note(valuation_data, 'Realtor.com')
            
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
    
    def _to_single_line(self, address: str) -> str:
        """Strip duplicate city/state tokens returned from Google Places"""
        parts = [x.strip() for x in address.split(',')]
        deduped = []
        for p in parts:
            if p.lower() not in [d.lower() for d in deduped]:
                deduped.append(p)
        return ', '.join(deduped)
    
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
            # Clean up address components to avoid duplication
            clean_address = address.split(',')[0].strip()  # Take only street address
            clean_city = city.split(',')[0].strip() if city else ""
            clean_state = state.split(',')[0].strip() if state else ""
            clean_zip = zip_code.strip() if zip_code else ""
            
            # Try multiple search strategies for better property matching
            search_strategies = [
                # Strategy 1: Clean street address with city, state
                {
                    "location": f"{clean_address}, {clean_city}, {clean_state}",
                    "status_type": "RecentlySold",
                    "home_type": "Houses"
                },
                # Strategy 2: Same format but for sale
                {
                    "location": f"{clean_address}, {clean_city}, {clean_state}",
                    "status_type": "ForSale",
                    "home_type": "Houses"
                },
                # Strategy 3: With ZIP code for recently sold
                {
                    "location": f"{clean_address}, {clean_city}, {clean_state} {clean_zip}".strip(),
                    "status_type": "RecentlySold", 
                    "home_type": "Houses"
                },
                # Strategy 4: Just street and city for broader search
                {
                    "location": f"{clean_address}, {clean_city}",
                    "status_type": "RecentlySold", 
                    "home_type": "Houses"
                }
            ]
            
            valuation_data['sources_tried'].append('Zillow')
            
            for strategy_idx, search_params in enumerate(search_strategies):
                search_response = requests.get(search_url, headers=headers, params=search_params, timeout=10)
                logging.info(f"Zillow search strategy {strategy_idx + 1}: {search_params}")
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    logging.info(f"Zillow API response: {search_data}")
                
                    # Check if we got property results array
                    if isinstance(search_data, list) and len(search_data) > 0:
                        # Find exact address match in results
                        best_match = None
                        target_address_lower = clean_address.lower().strip()
                        
                        # Look for exact street number and name match
                        import re
                        street_number_match = re.search(r'^(\d+)', clean_address)
                        target_street_number = street_number_match.group(1) if street_number_match else None
                        
                        for prop in search_data:
                            prop_address = prop.get('address', '').lower().strip()
                            
                            # Check if street number matches
                            if target_street_number:
                                prop_street_number_match = re.search(r'^(\d+)', prop_address)
                                if prop_street_number_match and prop_street_number_match.group(1) == target_street_number:
                                    # Also check if street name is similar
                                    if any(word in prop_address for word in target_address_lower.split()[1:]):  # Skip street number
                                        best_match = prop
                                        break
                        
                        # Use best match or first property if no exact match
                        selected_property = best_match or search_data[0]
                        zpid = selected_property.get('zpid')
                        
                        if zpid:
                            logging.info(f"Found property match: {selected_property.get('address')} (ZPID: {zpid})")
                            
                            # Initialize sources_used if not exists
                            if 'sources_used' not in valuation_data:
                                valuation_data['sources_used'] = []
                            
                            # Try to get detailed property information using the ZPID
                            details_url = "https://zillow-com1.p.rapidapi.com/property"
                            details_params = {"zpid": zpid}
                            
                            try:
                                details_response = requests.get(details_url, headers=headers, params=details_params, timeout=10)
                                
                                if details_response.status_code == 200:
                                    details_data = details_response.json()
                                    
                                    # Extract property valuation data if subscription allows
                                    if details_data and not details_data.get('message'):  # No error message
                                        logging.info(f"Zillow property details: {details_data}")
                                        
                                        # Try to extract Zestimate or current value
                                        zestimate = details_data.get('zestimate')
                                        if zestimate:
                                            valuation_data['zillow_estimate'] = zestimate
                                            valuation_data['sources_used'].append('Zillow')
                                            logging.info(f"Zillow Zestimate: ${zestimate:,}")
                                            
                                        # Also try tax history for recent value
                                        tax_history = details_data.get('taxHistory', [])
                                        if tax_history and len(tax_history) > 0:
                                            recent_tax_value = tax_history[0].get('value')
                                            if recent_tax_value:
                                                valuation_data['zillow_tax_value'] = recent_tax_value
                                                logging.info(f"Zillow Tax Value: ${recent_tax_value:,}")
                                                
                                        # Store complete property details for reference
                                        valuation_data['zillow_details'] = {
                                            'zpid': zpid,
                                            'address': details_data.get('streetAddress', ''),
                                            'living_area': details_data.get('livingAreaValue'),
                                            'county': details_data.get('county', ''),
                                            'tax_history': tax_history[:3] if tax_history else []  # Keep recent 3 years
                                        }
                                        
                                        # If we have any valuation data, mark Zillow as successful
                                        if zestimate or (tax_history and len(tax_history) > 0):
                                            if 'Zillow' not in valuation_data['sources_used']:
                                                valuation_data['sources_used'].append('Zillow')
                                        
                                        return  # Success - exit early
                                    else:
                                        # Subscription not available for property details, but we found the property
                                        error_msg = details_data.get('message', 'Unknown error') if details_data else 'No response'
                                        logging.warning(f"Zillow property details subscription required: {error_msg}")
                                        
                                        # Use search data to indicate property was found
                                        valuation_data['zillow_property_found'] = {
                                            'zpid': zpid,
                                            'address': selected_property.get('address'),
                                            'address_type': selected_property.get('addressType'),
                                            'subscription_note': 'Property details API requires RapidAPI subscription upgrade'
                                        }
                                        
                                        # Mark as partial success
                                        valuation_data['sources_used'].append('Zillow (search only)')
                                        logging.info(f"Zillow: Found property but details require subscription upgrade")
                                        return
                                else:
                                    logging.warning(f"Failed to get property details for ZPID {zpid}: {details_response.status_code}")
                                    
                            except Exception as e:
                                logging.warning(f"Error accessing Zillow property details: {e}")
                                
                            # Fallback: Use search result data as indication property exists
                            valuation_data['zillow_property_found'] = {
                                'zpid': zpid,
                                'address': selected_property.get('address'),
                                'address_type': selected_property.get('addressType'),
                                'note': 'Property found in Zillow database'
                            }
                            valuation_data['sources_used'].append('Zillow (search only)')
                            logging.info(f"Zillow: Property found in database but detailed valuation unavailable")
                    
                    # Fallback: Check old format for backward compatibility  
                    elif 'zpid' in search_data:
                        zpid = search_data['zpid']
                        logging.info(f"Found direct ZPID match: {zpid}")
                        # ... (existing code for single ZPID match)
                    
                    # Legacy format with props array
                    elif search_data and 'props' in search_data:
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
                                
                                # Use enhanced extraction method
                                zestimate = None
                                if detail_data:
                                    zestimate = self._extract_zillow_data_with_regex(detail_data)
                                    
                                    if zestimate:
                                        valuation_data['valuations']['zillow'] = {
                                            'zestimate': int(zestimate),
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
                    
                    # Try fallback search with just city, state
                    fallback_params = {
                        "location": f"{city}, {state}",
                        "status_type": "ForSale", 
                        "home_type": "Houses"
                    }
                    
                    fallback_response = requests.get(search_url, headers=headers, params=fallback_params, timeout=5)
                    if fallback_response.status_code == 200:
                        fallback_data = fallback_response.json()
                        if fallback_data and 'props' in fallback_data:
                            props = fallback_data['props']
                            if props and len(props) > 0:
                                # Use the first property as a general area estimate
                                zpid = props[0].get('zpid')
                                if zpid:
                                    detail_url = "https://zillow-com1.p.rapidapi.com/property"
                                    detail_params = {"zpid": zpid}
                                    detail_response = requests.get(detail_url, headers=headers, params=detail_params, timeout=5)
                                    
                                    if detail_response.status_code == 200:
                                        detail_data = detail_response.json()
                                        zestimate = self._extract_zillow_data_with_regex(detail_data)
                                        
                                        if zestimate:
                                            valuation_data['valuations']['zillow'] = {
                                                'zestimate': int(zestimate),
                                                'source': 'Zillow Property Data (Area Estimate)',
                                                'confidence': 'medium'
                                            }
                                            logging.info(f"Zillow fallback valuation success: ${zestimate:,}")
            else:
                logging.warning(f"Zillow search API failed: {search_response.status_code}")
        
        except Exception as e:
            logging.warning(f"Zillow valuation failed: {e}")
            
    def _extract_zillow_data_with_regex(self, detail_data: Dict) -> Optional[int]:
        """
        Enhanced Zillow data extraction using multiple patterns and fallbacks
        More resilient to API response variations
        """
        try:
            # Primary extraction paths
            zestimate_paths = [
                'zestimate',
                'price', 
                'homeValue',
                'listPrice',
                'lastSoldPrice'
            ]
            
            # Try direct extraction first
            for path in zestimate_paths:
                if path in detail_data and detail_data[path]:
                    return int(detail_data[path])
            
            # Try nested extraction in common locations
            nested_locations = [
                ('resoFacts', zestimate_paths),
                ('homeFacts', zestimate_paths),
                ('listingDataSource', zestimate_paths),
                ('priceHistory', ['price', 'amount']),
                ('homeInsights', ['priceInsights', 'listPrice'])
            ]
            
            for location, paths in nested_locations:
                if location in detail_data and isinstance(detail_data[location], dict):
                    nested_data = detail_data[location]
                    for path in paths:
                        if path in nested_data and nested_data[path]:
                            return int(nested_data[path])
                            
            # Try regex extraction from stringified data if available
            if 'description' in detail_data:
                price_match = re.search(r'\$([0-9,]+)', str(detail_data['description']))
                if price_match:
                    return int(price_match.group(1).replace(',', ''))
                    
            return None
            
        except (ValueError, TypeError) as e:
            logging.warning(f"Error extracting Zillow price data: {e}")
            return None
    
    def _try_redfin_valuation(self, valuation_data: Dict, address: str, city: str, state: str):
        """Try Redfin valuation via RapidAPI with enhanced error handling"""
        if not self.rapidapi_key:
            return
            
        try:
            # Use the working Redfin.com Data API 
            search_url = "https://redfin-com-data.p.rapidapi.com/properties/search-sale"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "redfin-com-data.p.rapidapi.com"
            }
            
            # Map cities to Redfin region IDs (required parameter)
            region_map = {
                'charlotte': '11997',
                'kannapolis': '11997',  # Near Charlotte
                'raleigh': '41593',
                'durham': '41593',
                'atlanta': '30756',
                'nashville': '39593'
            }
            
            city_key = city.lower()
            region_id = region_map.get(city_key, '11997')  # Default to Charlotte
            
            search_params = {
                "regionId": region_id,
                "limit": 20
            }
            
            search_response = requests.get(search_url, headers=headers, params=search_params, timeout=5)
            valuation_data['sources_tried'].append('Redfin')
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                logging.info(f"Redfin API response: {search_data}")
                
                if search_data and search_data.get('status') and search_data.get('data'):
                    properties = search_data['data']
                    
                    # Find best address match
                    best_match = None
                    best_score = 0
                    
                    for prop in properties:
                        if 'address' in prop:
                            prop_address = prop['address']
                            score = self._calculate_address_similarity(address, prop_address)
                            if score > best_score:
                                best_score = score
                                best_match = prop
                    
                    # If we found a good match, extract valuation
                    if best_match and best_score > 30:
                        logging.info(f"Found Redfin property match (score: {best_score}): {best_match.get('address', 'N/A')}")
                        
                        # Extract valuation from property data
                        estimate = None
                        if 'price' in best_match:
                            estimate = best_match['price']
                        elif 'homeValue' in best_match:
                            estimate = best_match['homeValue']
                        elif 'listPrice' in best_match:
                            estimate = best_match['listPrice']
                        
                        if estimate:
                            valuation_data['valuations']['redfin'] = {
                                'value': int(estimate),
                                'source': 'Redfin Property Data',
                                'confidence': 'high'
                            }
                            logging.info(f"Redfin valuation success: ${estimate:,}")
                        else:
                            logging.info(f"No price found in Redfin property data")
                    else:
                        logging.info(f"No good Redfin match found. Best score: {best_score}")
                else:
                    error_message = search_data.get('message', 'No data returned')
                    logging.warning(f"Redfin API error: {error_message}")
                    
                    # If regionId error, try with different region as fallback
                    if 'regionId' in error_message:
                        fallback_regions = ['11997', '41593', '30756', '39593']  # Charlotte, Raleigh, Atlanta, Nashville
                        for fallback_region in fallback_regions:
                            if fallback_region != region_id:
                                try:
                                    fallback_params = {
                                        "regionId": fallback_region,
                                        "limit": 20
                                    }
                                    fallback_response = requests.get(search_url, headers=headers, params=fallback_params, timeout=5)
                                    if fallback_response.status_code == 200:
                                        fallback_data = fallback_response.json()
                                        if fallback_data and fallback_data.get('status') and fallback_data.get('data'):
                                            properties = fallback_data['data']
                                            if properties and len(properties) > 0:
                                                # Use first property as area estimate
                                                prop = properties[0]
                                                if 'price' in prop and prop['price']:
                                                    valuation_data['valuations']['redfin'] = {
                                                        'value': int(prop['price']),
                                                        'source': 'Redfin Property Data (Area Estimate)',
                                                        'confidence': 'medium'
                                                    }
                                                    logging.info(f"Redfin fallback valuation success: ${prop['price']:,}")
                                                    return
                                except:
                                    continue
            else:
                logging.warning(f"Redfin search API failed: {search_response.status_code}")
        
        except Exception as e:
            logging.warning(f"Redfin valuation failed: {e}")
    
    def _try_realtor_valuation(self, valuation_data: Dict, address: str, city: str, state: str):
        """Realtor.com API requires separate RapidAPI subscription"""
        self._add_subscription_note(valuation_data, 'Realtor.com')
    
    def _calculate_address_similarity(self, target_address: str, comparison_address: str) -> float:
        """Calculate similarity score between two addresses"""
        target = target_address.lower().strip()
        comparison = comparison_address.lower().strip()
        
        # Extract street numbers for exact matching
        import re
        target_num = re.findall(r'^\d+', target)
        comp_num = re.findall(r'^\d+', comparison)
        
        # If street numbers don't match, low score
        if target_num and comp_num and target_num[0] != comp_num[0]:
            return 0
        
        # Calculate word overlap
        target_words = set(target.replace(',', '').split())
        comp_words = set(comparison.replace(',', '').split())
        
        if not target_words or not comp_words:
            return 0
        
        overlap = len(target_words & comp_words)
        total = len(target_words | comp_words)
        
        similarity = (overlap / total) * 100 if total > 0 else 0
        
        return similarity
    
    def _add_subscription_note(self, valuation_data: Dict, source: str):
        """Add note about subscription requirement for API source"""
        valuation_data['sources_tried'].append(f'{source} (subscription required)')
        logging.info(f"{source} API requires separate RapidAPI subscription")
    
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
        
        # Check for direct Zillow estimates first (from new property details API)
        if valuation_data.get('zillow_estimate'):
            return {
                'estimate': valuation_data['zillow_estimate'],
                'source': 'Zillow Zestimate',
                'confidence': 'high'
            }
        
        if valuation_data.get('zillow_tax_value'):
            return {
                'estimate': valuation_data['zillow_tax_value'],
                'source': 'Zillow Tax Record',
                'confidence': 'medium'
            }
        
        # Check structured valuations
        valuations = valuation_data.get('valuations', {})
        priority_order = ['zillow', 'redfin', 'realtor', 'attom', 'estated']
        
        for source in priority_order:
            if source in valuations:
                # Handle different key names: Zillow uses 'zestimate', others use 'value'
                estimate_value = valuations[source].get('zestimate') or valuations[source].get('value')
                return {
                    'estimate': estimate_value,
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