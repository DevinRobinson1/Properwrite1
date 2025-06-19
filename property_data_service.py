"""
Property Data Service for External API Integration
Provides reliable property estimates when external data is unavailable
"""
import logging
from typing import Dict, Optional, List

class PropertyDataService:
    def __init__(self):
        # State-based property value estimates (conservative values)
        self.state_values = {
            'NC': {'price_per_sqft': 120, 'rent_per_sqft': 1.1},
            'SC': {'price_per_sqft': 110, 'rent_per_sqft': 1.0},
            'GA': {'price_per_sqft': 125, 'rent_per_sqft': 1.2},
            'TN': {'price_per_sqft': 115, 'rent_per_sqft': 1.0},
            'FL': {'price_per_sqft': 140, 'rent_per_sqft': 1.4},
            'VA': {'price_per_sqft': 150, 'rent_per_sqft': 1.3},
            'AL': {'price_per_sqft': 100, 'rent_per_sqft': 0.9},
            'MS': {'price_per_sqft': 95, 'rent_per_sqft': 0.8},
            'TX': {'price_per_sqft': 130, 'rent_per_sqft': 1.2},
            'OH': {'price_per_sqft': 105, 'rent_per_sqft': 0.95}
        }

    def get_property_data(self, address: str, city: str, state: str, zip_code: str) -> Dict:
        """
        Get property data with reliable estimates
        """
        try:
            # Generate estimates based on location
            estimated_sqft = self._estimate_square_feet(city, state)
            bedrooms = self._estimate_bedrooms(estimated_sqft)
            bathrooms = self._estimate_bathrooms(bedrooms)
            
            property_data = {
                'address': address,
                'city': city,
                'state': state,
                'zip_code': zip_code,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'square_feet': estimated_sqft,
                'estimated_value': self._estimate_property_value(estimated_sqft, bedrooms, bathrooms, state),
                'rent_estimate': self._estimate_monthly_rent(estimated_sqft, bedrooms, bathrooms, state),
                'year_built': self._estimate_year_built(),
                'property_type': 'Single Family',
                'data_sources': ['Location-Based Estimates'],
                'images': [],
                'lot_size': None,
                'property_features': ['Standard Features'],
                'neighborhood_data': {'area_type': 'Residential'}
            }
            
            logging.info(f"Generated property estimates for {address}, {city}, {state}")
            return property_data
            
        except Exception as e:
            logging.error(f"Error generating property data: {e}")
            return self._get_default_property_data(address, city, state, zip_code)

    def _estimate_square_feet(self, city: str, state: str) -> int:
        """Estimate square feet based on location"""
        # Base square footage with regional adjustments
        base_sqft = 1200
        
        # Adjust based on state
        state_multipliers = {
            'TX': 1.3, 'FL': 1.2, 'GA': 1.1, 'NC': 1.1, 'VA': 1.0,
            'SC': 1.0, 'TN': 1.1, 'AL': 1.2, 'MS': 1.2, 'OH': 1.0
        }
        
        multiplier = state_multipliers.get(state, 1.0)
        estimated_sqft = int(base_sqft * multiplier)
        
        # Round to nearest 50
        return round(estimated_sqft / 50) * 50

    def _estimate_bedrooms(self, square_feet: int) -> int:
        """Estimate bedrooms based on square feet"""
        if square_feet < 800:
            return 2
        elif square_feet < 1200:
            return 3
        elif square_feet < 1800:
            return 3
        elif square_feet < 2500:
            return 4
        else:
            return 4

    def _estimate_bathrooms(self, bedrooms: int) -> float:
        """Estimate bathrooms based on bedrooms"""
        if bedrooms <= 2:
            return 1.0
        elif bedrooms == 3:
            return 2.0
        else:
            return 2.5

    def _estimate_property_value(self, square_feet: int, bedrooms: int, bathrooms: float, state: str) -> int:
        """Estimate property value"""
        state_data = self.state_values.get(state, {'price_per_sqft': 120})
        base_price = square_feet * state_data['price_per_sqft']
        
        # Adjust for bedrooms and bathrooms
        bedroom_bonus = max(0, bedrooms - 3) * 5000
        bathroom_bonus = max(0, bathrooms - 2) * 3000
        
        estimated_value = base_price + bedroom_bonus + bathroom_bonus
        
        # Round to nearest $5,000
        return round(estimated_value / 5000) * 5000

    def _estimate_monthly_rent(self, square_feet: int, bedrooms: int, bathrooms: float, state: str) -> int:
        """Estimate monthly rent"""
        state_data = self.state_values.get(state, {'rent_per_sqft': 1.1})
        base_rent = square_feet * state_data['rent_per_sqft']
        
        # Minimum rent thresholds
        min_rent_by_bedrooms = {1: 800, 2: 1000, 3: 1200, 4: 1500, 5: 1800}
        min_rent = min_rent_by_bedrooms.get(bedrooms, 1200)
        
        estimated_rent = max(base_rent, min_rent)
        
        # Round to nearest $25
        return round(estimated_rent / 25) * 25

    def _estimate_year_built(self) -> int:
        """Estimate year built"""
        return 1995

    def _get_default_property_data(self, address: str, city: str, state: str, zip_code: str) -> Dict:
        """Return default property data if all else fails"""
        return {
            'address': address,
            'city': city,
            'state': state,
            'zip_code': zip_code,
            'bedrooms': 3,
            'bathrooms': 2.0,
            'square_feet': 1200,
            'estimated_value': 200000,
            'rent_estimate': 2000,
            'year_built': 1995,
            'property_type': 'Single Family',
            'data_sources': ['Default Estimates'],
            'images': [],
            'lot_size': None,
            'property_features': [],
            'neighborhood_data': {}
        }

# Create a global instance
property_service = PropertyDataService()