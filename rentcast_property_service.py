"""
Rentcast Property Service - Main Data Provider
Replaces rapid APIs with authentic Rentcast data for property estimates and comparables
"""

import logging
from typing import Dict
from datetime import datetime
from address_validation_service import address_validator
from property_cache_service import property_cache
from rentcast_service import rentcast_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RentcastPropertyService:
    def __init__(self):
        """Initialize Rentcast property service"""
        pass
    
    def get_comprehensive_property_data(self, address: str, city: str, state: str, zip_code: str) -> Dict:
        """
        Get comprehensive property data using Rentcast API with address validation and caching
        """
        try:
            # Check cache first
            cached_data = property_cache.get_cached_property_data(address, city, state, zip_code)
            if cached_data:
                logger.info(f"Using cached Rentcast data for: {address}")
                return cached_data
            
            # Validate and normalize address
            validated_address = address_validator.validate_and_normalize_address(address, city, state, zip_code)
            
            if validated_address['status'] == 'error':
                return self._create_error_response(f"Address validation failed: {validated_address['error']}")
            
            logger.info(f"Validated address: {validated_address['full_address']}")
            
            # Get comprehensive data from Rentcast
            rentcast_data = rentcast_service.get_comprehensive_property_data(
                validated_address.get('street', address),
                validated_address.get('city', city),
                validated_address.get('state', state),
                validated_address.get('zip', zip_code)
            )
            
            if rentcast_data['status'] == 'error':
                logger.warning(f"Rentcast API error: {rentcast_data['error']}")
                return self._create_fallback_response(validated_address, rentcast_data['error'])
            
            # Structure property data for platform compatibility
            property_data = {
                'status': 'success',
                'address': validated_address['full_address'],
                'validated_address': validated_address,
                'source': 'Rentcast API',
                'data_retrieved_at': datetime.now().isoformat(),
                'estimate': rentcast_data.get('estimate', 0),
                'rent_estimate': rentcast_data.get('rent_estimate', 0),
                'confidence': rentcast_data.get('confidence', 'medium'),
                'data_quality': rentcast_data.get('data_quality', 'medium'),
                'comparable_sales': rentcast_data.get('comparable_sales', []),
                'market_analysis': rentcast_data.get('market_analysis', {}),
                'bedrooms': self._extract_bedrooms_from_comps(rentcast_data.get('comparable_sales', [])),
                'bathrooms': self._extract_bathrooms_from_comps(rentcast_data.get('comparable_sales', [])),
                'square_feet': self._extract_sqft_from_comps(rentcast_data.get('comparable_sales', [])),
                'year_built': self._extract_year_built_from_comps(rentcast_data.get('comparable_sales', [])),
                'property_type': 'Single Family Home',
                'comps_count': len(rentcast_data.get('comparable_sales', [])),
                'avg_price_per_sqft': rentcast_data.get('market_analysis', {}).get('avg_price_per_sqft', 0)
            }
            
            # Cache the results
            property_cache.cache_property_data(address, city, state, zip_code, property_data)
            logger.info(f"Rentcast data cached for: {address}")
            
            logger.info(f"Retrieved Rentcast data: Estimate ${property_data['estimate']:,}, Rent ${property_data['rent_estimate']:,}, {len(property_data['comparable_sales'])} comps")
            
            return property_data
            
        except Exception as e:
            logger.error(f"Error in get_comprehensive_property_data: {e}")
            return self._create_error_response(f"Failed to retrieve property data: {str(e)}")
    
    def _extract_bedrooms_from_comps(self, comps):
        """Extract typical bedrooms from comparable sales"""
        if not comps:
            return 3
        
        bedrooms_list = [c.get('bedrooms', 0) for c in comps if c.get('bedrooms', 0) > 0]
        if bedrooms_list:
            return int(sum(bedrooms_list) / len(bedrooms_list))
        return 3
    
    def _extract_bathrooms_from_comps(self, comps):
        """Extract typical bathrooms from comparable sales"""
        if not comps:
            return 2.0
        
        bathrooms_list = [c.get('bathrooms', 0) for c in comps if c.get('bathrooms', 0) > 0]
        if bathrooms_list:
            return round(sum(bathrooms_list) / len(bathrooms_list), 1)
        return 2.0
    
    def _extract_sqft_from_comps(self, comps):
        """Extract typical square footage from comparable sales"""
        if not comps:
            return 1200
        
        sqft_list = [c.get('square_feet', 0) for c in comps if c.get('square_feet', 0) > 0]
        if sqft_list:
            return int(sum(sqft_list) / len(sqft_list))
        return 1200
    
    def _extract_year_built_from_comps(self, comps):
        """Extract typical year built from comparable sales"""
        if not comps:
            return 1990
        
        year_list = [c.get('year_built', 0) for c in comps if c.get('year_built', 0) > 1900]
        if year_list:
            return int(sum(year_list) / len(year_list))
        return 1990
    
    def _create_fallback_response(self, validated_address: Dict, error_message: str) -> Dict:
        """Create fallback response when Rentcast data is unavailable"""
        return {
            'status': 'partial',
            'address': validated_address['full_address'],
            'validated_address': validated_address,
            'source': 'Address Validation Only',
            'data_retrieved_at': datetime.now().isoformat(),
            'estimate': 0,
            'rent_estimate': 0,
            'confidence': 'low',
            'data_quality': 'low',
            'comparable_sales': [],
            'market_analysis': {'avg_price_per_sqft': 0, 'sales_count': 0, 'price_range': {'min': 0, 'max': 0, 'avg': 0}},
            'bedrooms': 3,
            'bathrooms': 2.0,
            'square_feet': 1200,
            'year_built': 1990,
            'property_type': 'Single Family Home',
            'comps_count': 0,
            'avg_price_per_sqft': 0,
            'error': error_message
        }
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create standardized error response"""
        return {
            'status': 'error',
            'error': error_message,
            'source': 'Rentcast Property Service',
            'estimate': 0,
            'rent_estimate': 0,
            'confidence': 'low',
            'data_quality': 'low',
            'comparable_sales': [],
            'market_analysis': {'avg_price_per_sqft': 0, 'sales_count': 0, 'price_range': {'min': 0, 'max': 0, 'avg': 0}},
            'bedrooms': 3,
            'bathrooms': 2.0,
            'square_feet': 1200,
            'year_built': 1990,
            'property_type': 'Single Family Home',
            'comps_count': 0,
            'avg_price_per_sqft': 0
        }

# Create global instance
rentcast_property_service = RentcastPropertyService()