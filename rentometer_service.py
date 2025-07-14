"""
Rentometer API Service
Integrates with Rentometer API to fetch accurate rent data for property analysis
"""

import requests
import logging
from typing import Dict, Optional

class RentometerService:
    def __init__(self, api_key: str):
        """Initialize Rentometer service with API key"""
        self.api_key = api_key
        self.base_url = "https://www.rentometer.com/api/v1"
        self.session = requests.Session()
        
    def get_rent_summary(self, address: str, bedrooms: Optional[int] = None, 
                        baths: Optional[str] = None, building_type: Optional[str] = None,
                        latitude: Optional[float] = None, longitude: Optional[float] = None) -> Dict:
        """
        Get rent summary from Rentometer API
        
        Args:
            address: Full property address
            bedrooms: Number of bedrooms (optional)
            baths: Number of bathrooms (e.g., "1.5+") (optional)
            building_type: Type of building - "house", "apartment", etc. (optional)
            latitude: Property latitude (optional)
            longitude: Property longitude (optional)
            
        Returns:
            Dictionary containing rent data or error information
        """
        try:
            # Prepare request parameters
            params = {
                'api_key': self.api_key,
                'address': address
            }
            
            # Add optional parameters if provided
            if bedrooms is not None:
                params['bedrooms'] = bedrooms
            if baths is not None:
                params['baths'] = baths
            if building_type is not None:
                params['building_type'] = building_type
            if latitude is not None:
                params['latitude'] = latitude
            if longitude is not None:
                params['longitude'] = longitude
                
            logging.info(f"🏠 Rentometer API request for address: {address}")
            logging.info(f"🏠 Request parameters: {params}")
            
            # Make API request
            response = self.session.get(
                f"{self.base_url}/summary",
                params=params,
                timeout=10
            )
            
            logging.info(f"🏠 Rentometer API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logging.info(f"🏠 Rentometer API success: {data}")
                return {
                    'success': True,
                    'data': data,
                    'mean_rent': data.get('mean'),
                    'median_rent': data.get('median'),
                    'min_rent': data.get('min'),
                    'max_rent': data.get('max'),
                    'samples': data.get('samples', 0),
                    'radius_miles': data.get('radius_miles', 0.2),
                    'credits_remaining': data.get('credits_remaining')
                }
            else:
                error_msg = f"API returned status {response.status_code}"
                if response.text:
                    error_msg += f": {response.text}"
                logging.error(f"🏠 Rentometer API error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            logging.error("🏠 Rentometer API timeout")
            return {
                'success': False,
                'error': 'Request timeout - API took too long to respond'
            }
        except requests.exceptions.ConnectionError:
            logging.error("🏠 Rentometer API connection error")
            return {
                'success': False,
                'error': 'Connection error - unable to reach Rentometer API'
            }
        except Exception as e:
            logging.error(f"🏠 Rentometer API unexpected error: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def check_auth(self) -> Dict:
        """
        Check API key validity and remaining credits
        
        Returns:
            Dictionary containing auth status and credits information
        """
        try:
            response = self.session.get(
                f"{self.base_url}/auth",
                params={'api_key': self.api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'valid': True,
                    'credits_remaining': data.get('credits_remaining'),
                    'data': data
                }
            else:
                return {
                    'success': False,
                    'valid': False,
                    'error': f"Auth check failed: {response.status_code}"
                }
                
        except Exception as e:
            logging.error(f"🏠 Rentometer auth check error: {str(e)}")
            return {
                'success': False,
                'valid': False,
                'error': f'Auth check error: {str(e)}'
            }
    
    def format_rent_data_for_display(self, rent_data: Dict) -> Dict:
        """
        Format rent data for display in the property analysis interface
        
        Args:
            rent_data: Raw rent data from Rentometer API
            
        Returns:
            Formatted data for UI display
        """
        if not rent_data.get('success'):
            return {
                'rent_estimate': 0,
                'rent_range': 'N/A',
                'data_source': 'Rentometer',
                'error': rent_data.get('error', 'Unknown error')
            }
        
        data = rent_data.get('data', {})
        mean_rent = data.get('mean', 0)
        min_rent = data.get('min', 0)
        max_rent = data.get('max', 0)
        samples = data.get('samples', 0)
        
        return {
            'rent_estimate': mean_rent,
            'rent_range': f"${min_rent:,} - ${max_rent:,}" if min_rent and max_rent else 'N/A',
            'data_source': 'Rentometer',
            'samples': samples,
            'confidence': 'High' if samples >= 10 else 'Medium' if samples >= 5 else 'Low',
            'radius_miles': data.get('radius_miles', 0.2),
            'credits_remaining': data.get('credits_remaining')
        }


# Initialize Rentometer service with API key
def get_rentometer_service():
    """Get initialized Rentometer service"""
    api_key = "g-IP9-b2PTbzVd-ZN6U_Lw"
    return RentometerService(api_key)