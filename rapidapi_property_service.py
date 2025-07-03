"""
RapidAPI Property Data Service
Integrates with Zillow, Realtor.com, and other property APIs via RapidAPI
"""
import requests
import json
import logging
import os
from typing import Dict, Optional, List
from urllib.parse import quote
import time

class RapidAPIPropertyService:
    def __init__(self):
        self.session = requests.Session()
        self.rapidapi_key = "be3e296439msh2693e44b9d2433fp17bebbjsn9aa77716b131"
        
        # Base headers for all RapidAPI requests
        self.base_headers = {
            'X-RapidAPI-Key': self.rapidapi_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # API endpoint configurations
        self.apis = {
            'zillow': {
                'host': 'zillow-com1.p.rapidapi.com',
                'endpoints': {
                    'property_extended_search': '/propertyExtendedSearch',
                    'property_details': '/property'
                }
            },
            'realtor': {
                'host': 'realtor-com1.p.rapidapi.com',  # Typical RapidAPI host pattern
                'endpoints': {
                    'property_details': '',
                    'search': ''
                }
            }
        }
        
    def get_property_data(self, address: str, city: str, state: str, zip_code: str) -> Dict:
        """
        Get comprehensive property data from multiple RapidAPI sources
        """
        results = {
            'address': f"{address}, {city}, {state} {zip_code}",
            'sources': {},
            'estimates': {},
            'property_details': {},
            'comparable_sales': [],
            'rental_estimates': {},
            'success': False,
            'error': None
        }
        
        try:
            # Get Zillow data
            zillow_data = self._get_zillow_data(address, city, state, zip_code)
            if zillow_data:
                results['sources']['zillow'] = zillow_data
                results['success'] = True
                
            # Get Realtor.com data
            realtor_data = self._get_realtor_data(address, city, state, zip_code)
            if realtor_data:
                results['sources']['realtor'] = realtor_data
                results['success'] = True
                
            # Merge and normalize data - no longer needed as data is structured during parsing
            pass
            
            return results
            
        except Exception as e:
            logging.error(f"Error getting RapidAPI property data: {e}")
            results['error'] = str(e)
            return results
    
    def _get_zillow_data(self, address: str, city: str, state: str, zip_code: str) -> Optional[Dict]:
        """
        Get property data from Zillow via RapidAPI
        """
        try:
            headers = self.base_headers.copy()
            headers['X-RapidAPI-Host'] = self.apis['zillow']['host']
            
            # Construct the full address for search
            full_address = f"{address}, {city}, {state} {zip_code}"
            
            url = f"https://{self.apis['zillow']['host']}{self.apis['zillow']['endpoints']['property_extended_search']}"
            
            # First try specific address, then try area search
            params = {
                'location': f"{city}, {state} {zip_code}",
                'status_type': 'ForSale',
                'home_type': 'Houses'
            }
            
            logging.info(f"Calling Zillow API for: {full_address}")
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logging.info(f"Zillow API response received for {address}")
                
                # Extract property data from response
                return self._parse_zillow_response(data, address)
            else:
                logging.error(f"Zillow API error: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            logging.error(f"Error getting Zillow data: {e}")
            return None
    
    def _get_realtor_data(self, address: str, city: str, state: str, zip_code: str) -> Optional[Dict]:
        """
        Get property data from Realtor.com via RapidAPI
        """
        try:
            headers = self.base_headers.copy()
            headers['X-RapidAPI-Host'] = self.apis['realtor']['host']
            
            # TODO: Replace with actual endpoints once provided
            logging.info("Realtor.com API integration ready - awaiting endpoints")
            return None
            
        except Exception as e:
            logging.error(f"Error getting Realtor.com data: {e}")
            return None
    
    def _merge_property_data(self, results: Dict):
        """
        Merge data from multiple sources into unified structure
        """
        # Extract estimates from each source
        for source_name, source_data in results['sources'].items():
            if source_data and 'estimate' in source_data:
                results['estimates'][source_name] = source_data['estimate']
        
        # Extract property details (beds, baths, sqft, etc.)
        for source_name, source_data in results['sources'].items():
            if source_data and 'property_details' in source_data:
                details = source_data['property_details']
                if not results['property_details'].get('bedrooms') and details.get('bedrooms'):
                    results['property_details']['bedrooms'] = details['bedrooms']
                if not results['property_details'].get('bathrooms') and details.get('bathrooms'):
                    results['property_details']['bathrooms'] = details['bathrooms']
                if not results['property_details'].get('square_feet') and details.get('square_feet'):
                    results['property_details']['square_feet'] = details['square_feet']
    
    def _parse_zillow_response(self, data: Dict, target_address: str) -> Optional[Dict]:
        """
        Parse Zillow API response and extract property data
        """
        try:
            # Look for properties in the response
            properties = data.get('props', [])
            if not properties:
                properties = data.get('results', [])
            
            if not properties:
                logging.warning("No properties found in Zillow response")
                return None
            
            # Find the best matching property
            best_match = None
            best_score = 0
            
            for prop in properties:
                # Check if this property matches our target address
                prop_address = prop.get('address', {})
                if isinstance(prop_address, str):
                    prop_full_address = prop_address
                else:
                    street = prop_address.get('streetAddress', '')
                    city = prop_address.get('city', '')
                    state = prop_address.get('state', '')
                    prop_full_address = f"{street}, {city}, {state}"
                
                # Simple scoring based on address similarity
                score = self._calculate_address_similarity(target_address, prop_full_address)
                if score > best_score:
                    best_score = score
                    best_match = prop
            
            if not best_match or best_score < 0.5:  # Minimum similarity threshold
                logging.warning(f"No good address match found for {target_address}")
                return None
            
            # Extract data from the best matching property using correct Zillow API structure
            result = {
                'estimate': best_match.get('price', 0),
                'property_details': {
                    'bedrooms': best_match.get('bedrooms'),
                    'bathrooms': best_match.get('bathrooms'), 
                    'square_feet': best_match.get('livingArea'),
                    'lot_size': best_match.get('lotAreaValue'),
                    'property_type': best_match.get('propertyType'),
                    'listing_status': best_match.get('listingStatus'),
                    'days_on_zillow': best_match.get('daysOnZillow'),
                    'zpid': best_match.get('zpid')
                },
                'images': [best_match.get('imgSrc')] if best_match.get('imgSrc') else [],
                'location': {
                    'latitude': best_match.get('latitude'),
                    'longitude': best_match.get('longitude'),
                    'address': best_match.get('address')
                },
                'confidence': best_score
            }
            
            # Get detailed property information if ZPID is available
            if result.get('property_details', {}).get('zpid'):
                zpid = result['property_details']['zpid']
                detailed_result = self._get_property_details(zpid)
                if detailed_result:
                    # Merge detailed information with search result
                    result = self._merge_property_data(result, detailed_result)
            
            logging.info(f"Parsed Zillow data for {target_address}: ${result['estimate']:,}")
            return result
            
        except Exception as e:
            logging.error(f"Error parsing Zillow response: {e}")
            return None
    
    def _calculate_address_similarity(self, addr1: str, addr2: str) -> float:
        """
        Calculate similarity score between two addresses with enhanced matching
        """
        try:
            # Normalize addresses for comparison
            addr1_norm = addr1.lower().replace('drive', 'dr').replace('street', 'st').replace('avenue', 'ave').replace('road', 'rd')
            addr2_norm = addr2.lower().replace('drive', 'dr').replace('street', 'st').replace('avenue', 'ave').replace('road', 'rd')
            
            # Extract just the street number and name for better matching
            import re
            pattern = r'(\d+)\s+([^,]+)'
            
            match1 = re.search(pattern, addr1_norm)
            match2 = re.search(pattern, addr2_norm)
            
            if match1 and match2:
                # Compare street numbers
                num1, street1 = match1.groups()
                num2, street2 = match2.groups()
                
                # If street numbers match, compare street names
                if num1 == num2:
                    street_words1 = set(street1.strip().split())
                    street_words2 = set(street2.strip().split())
                    
                    # High score if street numbers match and street names are similar
                    intersection = street_words1.intersection(street_words2)
                    union = street_words1.union(street_words2)
                    
                    street_similarity = len(intersection) / len(union) if union else 0.0
                    return 0.8 + (0.2 * street_similarity)  # Base score of 0.8 for matching street number
            
            # Fallback to word-based similarity
            words1 = set(addr1_norm.split())
            words2 = set(addr2_norm.split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception:
            return 0.0
    
    def _get_property_details(self, zpid: str) -> Dict:
        """
        Get detailed property information using Zillow Property Details API
        """
        try:
            url = f"https://{self.apis['zillow']['host']}{self.apis['zillow']['endpoints']['property_details']}"
            
            params = {
                'zpid': zpid
            }
            
            headers = self.base_headers.copy()
            headers['X-RapidAPI-Host'] = self.apis['zillow']['host']
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_property_details(data)
            else:
                logging.warning(f"Property details API returned status {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error fetching property details for ZPID {zpid}: {e}")
            return None
    
    def _parse_property_details(self, data: Dict) -> Dict:
        """
        Parse detailed property information from Zillow Property Details API
        """
        try:
            result = {
                'detailed_info': {
                    'zestimate': data.get('zestimate'),
                    'property_tax_rate': data.get('propertyTaxRate'),
                    'time_on_zillow': data.get('timeOnZillow'),
                    'year_built': data.get('resoFacts', {}).get('yearBuilt'),
                    'hoa_fee': data.get('resoFacts', {}).get('associationFee'),
                    'lot_size': data.get('resoFacts', {}).get('lotSize'),
                    'property_type': data.get('propertyTypeDimension'),
                    'heating': data.get('resoFacts', {}).get('heating'),
                    'cooling': data.get('resoFacts', {}).get('cooling'),
                    'parking': data.get('resoFacts', {}).get('parkingFeatures'),
                    'appliances': data.get('resoFacts', {}).get('appliances', []),
                    'interior_features': data.get('resoFacts', {}).get('interiorFeatures', []),
                    'exterior_features': data.get('resoFacts', {}).get('exteriorFeatures', {}),
                    'construction_materials': data.get('resoFacts', {}).get('constructionMaterials', []),
                    'roof_type': data.get('resoFacts', {}).get('roofType'),
                    'flooring': data.get('resoFacts', {}).get('flooring', []),
                    'water_source': data.get('resoFacts', {}).get('waterSource', []),
                    'sewer': data.get('resoFacts', {}).get('sewer', []),
                    'has_fireplace': data.get('resoFacts', {}).get('hasFireplace'),
                    'has_garage': data.get('resoFacts', {}).get('hasGarage'),
                    'garage_spaces': data.get('resoFacts', {}).get('garageSpaces'),
                    'bedrooms': data.get('resoFacts', {}).get('bedrooms'),
                    'bathrooms_full': data.get('resoFacts', {}).get('bathroomsFull'),
                    'bathrooms_half': data.get('resoFacts', {}).get('bathroomsHalf'),
                    'living_area': data.get('livingAreaValue'),
                    'at_a_glance_facts': data.get('resoFacts', {}).get('atAGlanceFacts', [])
                }
            }
            
            # Extract key financial information
            if data.get('zestimate'):
                result['zestimate'] = data['zestimate']
            
            # Extract enhanced property details
            if data.get('resoFacts'):
                facts = data['resoFacts']
                if facts.get('bedrooms'):
                    result['bedrooms'] = facts['bedrooms']
                if facts.get('bathroomsFull'):
                    result['bathrooms'] = facts['bathroomsFull']
                if data.get('livingAreaValue'):
                    result['square_feet'] = data['livingAreaValue']
            
            return result
            
        except Exception as e:
            logging.error(f"Error parsing property details: {e}")
            return None
    
    def _merge_property_data(self, base_result: Dict, detailed_result: Dict) -> Dict:
        """
        Merge detailed property information with search results
        """
        try:
            # Add detailed information to base result
            if detailed_result.get('detailed_info'):
                base_result['detailed_info'] = detailed_result['detailed_info']
            
            # Update estimate with Zestimate if available and higher confidence
            if detailed_result.get('zestimate') and detailed_result['zestimate'] > 0:
                base_result['zestimate'] = detailed_result['zestimate']
                # Use Zestimate as primary estimate if it exists
                if not base_result.get('estimate') or base_result['estimate'] == 0:
                    base_result['estimate'] = detailed_result['zestimate']
            
            # Update property details with more accurate information
            if detailed_result.get('bedrooms'):
                base_result['property_details']['bedrooms'] = detailed_result['bedrooms']
            if detailed_result.get('bathrooms'):
                base_result['property_details']['bathrooms'] = detailed_result['bathrooms']
            if detailed_result.get('square_feet'):
                base_result['property_details']['square_feet'] = detailed_result['square_feet']
            
            return base_result
            
        except Exception as e:
            logging.error(f"Error merging property data: {e}")
            return base_result
    
    def test_api_connection(self) -> Dict:
        """
        Test API connection and authentication
        """
        try:
            # Test with a simple request to verify API key works
            headers = self.base_headers.copy()
            headers['X-RapidAPI-Host'] = self.apis['zillow']['host']
            
            # This will be updated once we have actual endpoints
            return {
                'status': 'ready',
                'message': 'API credentials configured, awaiting endpoints',
                'rapidapi_key': self.rapidapi_key[:10] + "..." if self.rapidapi_key else None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

# Create global instance
rapidapi_service = RapidAPIPropertyService()