"""
RentCast API Service
Provides property valuations and rental estimates using RentCast API
Offers 50 free calls per month with comprehensive property data coverage
"""

import os
import requests
import logging
from typing import Dict, Optional, List
from datetime import datetime

class RentCastAPIService:
    def __init__(self):
        self.base_url = "https://api.rentcast.io/v1"
        self.api_key = os.environ.get('RENTCAST_API_KEY')
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_property_value(self, address: str, city: str = None, state: str = None) -> Optional[Dict]:
        """
        Get property value estimate from RentCast API
        Returns property value, confidence score, and additional details
        """
        if not self.api_key:
            self.logger.warning("RentCast API key not found")
            return None
        
        # Format address for API
        full_address = f"{address}"
        if city:
            full_address += f", {city}"
        if state:
            full_address += f", {state}"
        
        self.logger.info(f"Getting RentCast property value for: {full_address}")
        
        try:
            # RentCast property details endpoint
            url = f"{self.base_url}/properties"
            params = {
                'address': full_address,
                'propertyType': 'Single Family',
                'bedrooms': '',
                'bathrooms': '',
                'squareFootage': ''
            }
            
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            self.logger.info(f"RentCast API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"RentCast API response: {data}")
                
                if data and len(data) > 0:
                    property_data = data[0]  # Take first match
                    
                    # Extract property value
                    value = property_data.get('value')
                    confidence = property_data.get('confidence', 0)
                    
                    if value and value > 0:
                        return {
                            'value': value,
                            'confidence': confidence,
                            'bedrooms': property_data.get('bedrooms'),
                            'bathrooms': property_data.get('bathrooms'),
                            'square_feet': property_data.get('squareFootage'),
                            'property_type': property_data.get('propertyType'),
                            'address': property_data.get('address'),
                            'city': property_data.get('city'),
                            'state': property_data.get('state'),
                            'zip_code': property_data.get('zipCode'),
                            'source': 'RentCast Property Data',
                            'updated': datetime.now().strftime('%Y-%m-%d')
                        }
                    else:
                        self.logger.warning("No value found in RentCast response")
                        return None
                else:
                    self.logger.warning("No properties found in RentCast response")
                    return None
            else:
                self.logger.error(f"RentCast API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calling RentCast API: {str(e)}")
            return None
    
    def get_rental_estimate(self, address: str, city: str = None, state: str = None) -> Optional[Dict]:
        """
        Get rental estimate from RentCast API
        """
        if not self.api_key:
            self.logger.warning("RentCast API key not found")
            return None
        
        # Format address for API
        full_address = f"{address}"
        if city:
            full_address += f", {city}"
        if state:
            full_address += f", {state}"
        
        self.logger.info(f"Getting RentCast rental estimate for: {full_address}")
        
        try:
            # RentCast rental estimate endpoint
            url = f"{self.base_url}/rentals"
            params = {
                'address': full_address,
                'propertyType': 'Single Family',
                'bedrooms': '',
                'bathrooms': '',
                'squareFootage': ''
            }
            
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            self.logger.info(f"RentCast Rental API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"RentCast Rental API response: {data}")
                
                if data and len(data) > 0:
                    rental_data = data[0]  # Take first match
                    
                    # Extract rental estimate
                    rent_estimate = rental_data.get('rent')
                    confidence = rental_data.get('confidence', 0)
                    
                    if rent_estimate and rent_estimate > 0:
                        return {
                            'rent_estimate': rent_estimate,
                            'confidence': confidence,
                            'bedrooms': rental_data.get('bedrooms'),
                            'bathrooms': rental_data.get('bathrooms'),
                            'square_feet': rental_data.get('squareFootage'),
                            'property_type': rental_data.get('propertyType'),
                            'address': rental_data.get('address'),
                            'source': 'RentCast Rental Data',
                            'updated': datetime.now().strftime('%Y-%m-%d')
                        }
                    else:
                        self.logger.warning("No rent estimate found in RentCast response")
                        return None
                else:
                    self.logger.warning("No rental properties found in RentCast response")
                    return None
            else:
                self.logger.error(f"RentCast Rental API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calling RentCast Rental API: {str(e)}")
            return None
    
    def get_comparable_sales(self, address: str, city: str = None, state: str = None, radius: float = 0.5) -> List[Dict]:
        """
        Get comparable sales from RentCast API
        """
        if not self.api_key:
            self.logger.warning("RentCast API key not found")
            return []
        
        # Format address for API
        full_address = f"{address}"
        if city:
            full_address += f", {city}"
        if state:
            full_address += f", {state}"
        
        self.logger.info(f"Getting RentCast comparable sales for: {full_address}")
        
        try:
            # RentCast comparable sales endpoint
            url = f"{self.base_url}/comps"
            params = {
                'address': full_address,
                'radius': radius,
                'limit': 10
            }
            
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            self.logger.info(f"RentCast Comps API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"RentCast Comps API response: Found {len(data)} comparable sales")
                
                comparables = []
                for comp in data:
                    comparable = {
                        'address': comp.get('address'),
                        'sale_price': comp.get('salePrice'),
                        'sale_date': comp.get('saleDate'),
                        'bedrooms': comp.get('bedrooms'),
                        'bathrooms': comp.get('bathrooms'),
                        'square_feet': comp.get('squareFootage'),
                        'lot_size': comp.get('lotSize'),
                        'year_built': comp.get('yearBuilt'),
                        'distance': comp.get('distance'),
                        'source': 'RentCast Comparable Sales'
                    }
                    comparables.append(comparable)
                
                return comparables
            else:
                self.logger.error(f"RentCast Comps API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error calling RentCast Comps API: {str(e)}")
            return []