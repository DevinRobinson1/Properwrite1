"""
Rentcast API Service for Property Comparables and Market Data
Provides authentic property estimates and comparable sales data
"""

import requests
import os
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RentcastService:
    def __init__(self):
        """Initialize Rentcast service with API key"""
        self.api_key = os.environ.get('RENTCAST_API_KEY')
        self.base_url = 'https://api.rentcast.io/v1'
        self.headers = {
            'Accept': 'application/json',
            'X-Api-Key': self.api_key if self.api_key else ''
        }
    
    def get_property_estimate(self, address: str, city: str = '', state: str = '', zip_code: str = '') -> Dict:
        """
        Get property estimate from Rentcast API
        """
        if not self.api_key:
            logger.warning("Rentcast API key not found")
            return self._create_error_response("API key required")
        
        # Format address for API
        full_address = self._format_address(address, city, state, zip_code)
        
        try:
            # Get property details and estimate
            url = f"{self.base_url}/avm/value"
            params = {
                'address': full_address,
                'propertyType': 'Single Family'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_rentcast_estimate(data, full_address)
            else:
                logger.error(f"Rentcast API error: {response.status_code} - {response.text}")
                return self._create_error_response(f"API error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Rentcast request error: {e}")
            return self._create_error_response(f"Request failed: {str(e)}")
    
    def get_property_comparables(self, address: str, city: str = '', state: str = '', zip_code: str = '') -> Dict:
        """
        Get comparable sales from Rentcast API
        """
        if not self.api_key:
            logger.warning("Rentcast API key not found")
            return self._create_error_response("API key required")
        
        # Format address for API
        full_address = self._format_address(address, city, state, zip_code)
        
        try:
            # Get comparable sales
            url = f"{self.base_url}/avm/comps"
            params = {
                'address': full_address,
                'radius': 0.5,  # 0.5 mile radius
                'count': 10,    # Get up to 10 comps
                'daysBack': 365  # Within last year
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_rentcast_comps(data, full_address)
            else:
                logger.error(f"Rentcast comps API error: {response.status_code} - {response.text}")
                return self._create_error_response(f"Comps API error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Rentcast comps request error: {e}")
            return self._create_error_response(f"Comps request failed: {str(e)}")
    
    def get_rent_estimate(self, address: str, city: str = '', state: str = '', zip_code: str = '') -> Dict:
        """
        Get rental estimate from Rentcast API
        """
        if not self.api_key:
            logger.warning("Rentcast API key not found")
            return self._create_error_response("API key required")
        
        # Format address for API
        full_address = self._format_address(address, city, state, zip_code)
        
        try:
            # Get rental estimate
            url = f"{self.base_url}/avm/rent"
            params = {
                'address': full_address,
                'propertyType': 'Single Family'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_rentcast_rent(data, full_address)
            else:
                logger.error(f"Rentcast rent API error: {response.status_code} - {response.text}")
                return self._create_error_response(f"Rent API error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Rentcast rent request error: {e}")
            return self._create_error_response(f"Rent request failed: {str(e)}")
    
    def get_comprehensive_property_data(self, address: str, city: str = '', state: str = '', zip_code: str = '') -> Dict:
        """
        Get comprehensive property data from Rentcast including estimates, comps, and rent
        """
        logger.info(f"Getting comprehensive Rentcast data for: {address}")
        
        # Get all data types
        estimate_data = self.get_property_estimate(address, city, state, zip_code)
        comps_data = self.get_property_comparables(address, city, state, zip_code)
        rent_data = self.get_rent_estimate(address, city, state, zip_code)
        
        # Merge all data
        comprehensive_data = {
            'status': 'success',
            'source': 'Rentcast API',
            'address': self._format_address(address, city, state, zip_code),
            'estimate': estimate_data.get('estimate', 0),
            'confidence': estimate_data.get('confidence', 'medium'),
            'rent_estimate': rent_data.get('rent_estimate', 0),
            'comparable_sales': comps_data.get('comparables', []),
            'market_analysis': {
                'avg_price_per_sqft': self._calculate_avg_price_per_sqft(comps_data.get('comparables', [])),
                'sales_count': len(comps_data.get('comparables', [])),
                'price_range': self._calculate_price_range(comps_data.get('comparables', []))
            },
            'data_quality': self._assess_data_quality(estimate_data, comps_data, rent_data)
        }
        
        logger.info(f"Rentcast data retrieved: Estimate ${estimate_data.get('estimate', 0):,}, Rent ${rent_data.get('rent_estimate', 0):,}, {len(comps_data.get('comparables', []))} comps")
        
        return comprehensive_data
    
    def _format_address(self, address: str, city: str = '', state: str = '', zip_code: str = '') -> str:
        """Format address for API call"""
        parts = [address.strip()]
        if city:
            parts.append(city.strip())
        if state:
            parts.append(state.strip())
        if zip_code:
            parts.append(zip_code.strip())
        return ', '.join(parts)
    
    def _parse_rentcast_estimate(self, data: Dict, address: str) -> Dict:
        """Parse Rentcast estimate response"""
        try:
            estimate = data.get('price', 0)
            confidence = data.get('confidence', 0.5)
            
            # Convert confidence to readable format
            confidence_level = 'high' if confidence > 0.8 else 'medium' if confidence > 0.5 else 'low'
            
            return {
                'estimate': int(estimate),
                'confidence': confidence_level,
                'confidence_score': confidence,
                'source': 'Rentcast AVM',
                'address': address,
                'details': data
            }
        except Exception as e:
            logger.error(f"Error parsing Rentcast estimate: {e}")
            return self._create_error_response("Failed to parse estimate data")
    
    def _parse_rentcast_comps(self, data: Dict, address: str) -> Dict:
        """Parse Rentcast comparables response"""
        try:
            comps = data.get('comps', [])
            parsed_comps = []
            
            for comp in comps:
                parsed_comp = {
                    'address': comp.get('address', ''),
                    'sale_price': int(comp.get('price', 0)),
                    'sale_date': comp.get('saleDate', ''),
                    'bedrooms': comp.get('bedrooms', 0),
                    'bathrooms': comp.get('bathrooms', 0),
                    'square_feet': comp.get('squareFootage', 0),
                    'price_per_sqft': round(comp.get('price', 0) / max(comp.get('squareFootage', 1), 1), 2),
                    'distance_miles': round(comp.get('distance', 0), 2),
                    'year_built': comp.get('yearBuilt', 0)
                }
                parsed_comps.append(parsed_comp)
            
            return {
                'comparables': parsed_comps,
                'count': len(parsed_comps),
                'source': 'Rentcast Comps',
                'address': address
            }
        except Exception as e:
            logger.error(f"Error parsing Rentcast comps: {e}")
            return self._create_error_response("Failed to parse comparables data")
    
    def _parse_rentcast_rent(self, data: Dict, address: str) -> Dict:
        """Parse Rentcast rent estimate response"""
        try:
            rent = data.get('rent', 0)
            confidence = data.get('confidence', 0.5)
            
            # Convert confidence to readable format
            confidence_level = 'high' if confidence > 0.8 else 'medium' if confidence > 0.5 else 'low'
            
            return {
                'rent_estimate': int(rent),
                'confidence': confidence_level,
                'confidence_score': confidence,
                'source': 'Rentcast Rent',
                'address': address,
                'details': data
            }
        except Exception as e:
            logger.error(f"Error parsing Rentcast rent: {e}")
            return self._create_error_response("Failed to parse rent data")
    
    def _calculate_avg_price_per_sqft(self, comps: List[Dict]) -> float:
        """Calculate average price per square foot from comparables"""
        if not comps:
            return 0.0
        
        valid_comps = [c for c in comps if c.get('square_feet', 0) > 0 and c.get('sale_price', 0) > 0]
        if not valid_comps:
            return 0.0
        
        total_price_per_sqft = sum(c['sale_price'] / c['square_feet'] for c in valid_comps)
        return round(total_price_per_sqft / len(valid_comps), 2)
    
    def _calculate_price_range(self, comps: List[Dict]) -> Dict:
        """Calculate price range from comparables"""
        if not comps:
            return {'min': 0, 'max': 0, 'avg': 0}
        
        prices = [c.get('sale_price', 0) for c in comps if c.get('sale_price', 0) > 0]
        if not prices:
            return {'min': 0, 'max': 0, 'avg': 0}
        
        return {
            'min': min(prices),
            'max': max(prices),
            'avg': round(sum(prices) / len(prices))
        }
    
    def _assess_data_quality(self, estimate_data: Dict, comps_data: Dict, rent_data: Dict) -> str:
        """Assess overall data quality from Rentcast"""
        quality_scores = []
        
        # Check estimate quality
        if estimate_data.get('estimate', 0) > 0:
            confidence = estimate_data.get('confidence_score', 0)
            if confidence > 0.8:
                quality_scores.append('high')
            elif confidence > 0.5:
                quality_scores.append('medium')
            else:
                quality_scores.append('low')
        
        # Check comps quality
        comps_count = len(comps_data.get('comparables', []))
        if comps_count >= 5:
            quality_scores.append('high')
        elif comps_count >= 2:
            quality_scores.append('medium')
        else:
            quality_scores.append('low')
        
        # Check rent quality
        if rent_data.get('rent_estimate', 0) > 0:
            quality_scores.append('medium')
        
        # Calculate overall quality
        if not quality_scores:
            return 'low'
        
        high_count = quality_scores.count('high')
        medium_count = quality_scores.count('medium')
        
        if high_count >= 2:
            return 'high'
        elif high_count >= 1 or medium_count >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create standardized error response"""
        return {
            'status': 'error',
            'error': error_message,
            'source': 'Rentcast API',
            'estimate': 0,
            'confidence': 'low',
            'rent_estimate': 0,
            'comparable_sales': [],
            'market_analysis': {
                'avg_price_per_sqft': 0,
                'sales_count': 0,
                'price_range': {'min': 0, 'max': 0, 'avg': 0}
            },
            'data_quality': 'low'
        }

# Create global instance
rentcast_service = RentcastService()