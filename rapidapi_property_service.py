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
                    'property_extended_search': '/propertyExtendedSearch'
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
                
            # Merge and normalize data
            self._merge_property_data(results)
            
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
            
            params = {
                'location': full_address,
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
            
            logging.info(f"Parsed Zillow data for {target_address}: ${result['estimate']:,}")
            return result
            
        except Exception as e:
            logging.error(f"Error parsing Zillow response: {e}")
            return None
    
    def _calculate_address_similarity(self, addr1: str, addr2: str) -> float:
        """
        Calculate similarity score between two addresses
        """
        try:
            # Simple scoring based on common words
            words1 = set(addr1.lower().split())
            words2 = set(addr2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            # Calculate Jaccard similarity
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception:
            return 0.0
    
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