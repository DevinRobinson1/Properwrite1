"""
Property Data Service for External API Integration
Pulls property data from Zillow, Redfin, Realtor.com and other sources
"""
import requests
import logging
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, Optional, List

class PropertyDataService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_property_data(self, address: str, city: str, state: str, zip_code: str) -> Dict:
        """
        Comprehensive property data from multiple sources
        """
        full_address = f"{address}, {city}, {state} {zip_code}"
        
        property_data = {
            'address': address,
            'city': city,
            'state': state,
            'zip_code': zip_code,
            'full_address': full_address,
            'estimated_value': None,
            'rent_estimate': None,
            'bedrooms': None,
            'bathrooms': None,
            'square_feet': None,
            'year_built': None,
            'property_type': None,
            'lot_size': None,
            'images': [],
            'data_sources': {},
            'property_features': [],
            'neighborhood_data': {}
        }

        # Try multiple data sources
        try:
            # Zillow data
            zillow_data = self._get_zillow_data(full_address)
            if zillow_data:
                property_data.update(zillow_data)
                property_data['data_sources']['Zillow'] = 'Success'
        except Exception as e:
            logging.warning(f"Zillow data fetch failed: {e}")
            property_data['data_sources']['Zillow'] = f'Failed: {str(e)}'

        try:
            # Redfin data
            redfin_data = self._get_redfin_data(full_address)
            if redfin_data:
                self._merge_property_data(property_data, redfin_data)
                property_data['data_sources']['Redfin'] = 'Success'
        except Exception as e:
            logging.warning(f"Redfin data fetch failed: {e}")
            property_data['data_sources']['Redfin'] = f'Failed: {str(e)}'

        try:
            # Realtor.com data
            realtor_data = self._get_realtor_data(full_address)
            if realtor_data:
                self._merge_property_data(property_data, realtor_data)
                property_data['data_sources']['Realtor.com'] = 'Success'
        except Exception as e:
            logging.warning(f"Realtor.com data fetch failed: {e}")
            property_data['data_sources']['Realtor.com'] = f'Failed: {str(e)}'

        # Calculate average estimates if multiple sources available
        self._calculate_averaged_estimates(property_data)
        
        return property_data

    def _get_zillow_data(self, address: str) -> Optional[Dict]:
        """
        Extract property data from Zillow
        Note: This uses web scraping which may require API keys for production use
        """
        try:
            # Search URL format for Zillow
            search_url = f"https://www.zillow.com/homes/{address.replace(' ', '-').replace(',', '')}_rb/"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract data from Zillow's page structure
            data = {}
            
            # Look for JSON data in script tags
            scripts = soup.find_all('script', type='application/json')
            for script in scripts:
                if 'InitialReduxState' in script.get('id', ''):
                    try:
                        json_data = json.loads(script.string)
                        # Extract property details from Redux state
                        if 'gdp' in json_data and 'property' in json_data['gdp']:
                            prop = json_data['gdp']['property']
                            data.update({
                                'estimated_value': prop.get('price'),
                                'bedrooms': prop.get('bedrooms'),
                                'bathrooms': prop.get('bathrooms'),
                                'square_feet': prop.get('livingArea'),
                                'year_built': prop.get('yearBuilt'),
                                'property_type': prop.get('homeType'),
                                'lot_size': prop.get('lotAreaValue'),
                                'rent_estimate': prop.get('rentZestimate')
                            })
                            
                            # Extract images
                            if 'photos' in prop:
                                data['images'] = [photo.get('url') for photo in prop['photos'][:5]]
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            return data if data else None
            
        except Exception as e:
            logging.error(f"Zillow scraping error: {e}")
            return None

    def _get_redfin_data(self, address: str) -> Optional[Dict]:
        """
        Extract property data from Redfin
        """
        try:
            # Redfin search API (public endpoints)
            search_url = "https://www.redfin.com/stingray/api/gis"
            params = {
                'al': '1',
                'search_input': address,
                'region_id': '6181',
                'region_type': '6'
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            if response.status_code != 200:
                return None

            data_text = response.text.replace('{}&&', '')
            json_data = json.loads(data_text)
            
            if 'homes' in json_data and json_data['homes']:
                home = json_data['homes'][0]
                return {
                    'estimated_value': home.get('price'),
                    'bedrooms': home.get('beds'),
                    'bathrooms': home.get('baths'),
                    'square_feet': home.get('sqFt'),
                    'year_built': home.get('yearBuilt'),
                    'property_type': home.get('propertyType'),
                    'lot_size': home.get('lotSize')
                }
                
        except Exception as e:
            logging.error(f"Redfin API error: {e}")
            return None

    def _get_realtor_data(self, address: str) -> Optional[Dict]:
        """
        Extract property data from Realtor.com
        """
        try:
            # Realtor.com search
            search_url = f"https://www.realtor.com/realestateandhomes-search/{address.replace(' ', '-')}"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract structured data
            data = {}
            
            # Look for JSON-LD structured data
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, list):
                        json_data = json_data[0]
                    
                    if json_data.get('@type') == 'SingleFamilyResidence':
                        data.update({
                            'estimated_value': self._extract_price(json_data.get('offers', {})),
                            'bedrooms': json_data.get('numberOfRooms'),
                            'bathrooms': json_data.get('numberOfBathroomsTotal'),
                            'square_feet': self._extract_area(json_data.get('floorSize')),
                            'year_built': json_data.get('yearBuilt')
                        })
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return data if data else None
            
        except Exception as e:
            logging.error(f"Realtor.com scraping error: {e}")
            return None

    def _merge_property_data(self, base_data: Dict, new_data: Dict):
        """
        Merge new property data with existing data, preferring non-null values
        """
        for key, value in new_data.items():
            if value is not None and (base_data.get(key) is None or key == 'images'):
                if key == 'images':
                    # Extend images list
                    base_data[key].extend(value)
                else:
                    base_data[key] = value

    def _calculate_averaged_estimates(self, property_data: Dict):
        """
        Calculate averaged estimates from multiple sources
        """
        # For now, keep the first non-null value
        # Could be enhanced to calculate weighted averages
        pass

    def _extract_price(self, offers_data) -> Optional[int]:
        """Extract price from offers data structure"""
        if isinstance(offers_data, dict) and 'price' in offers_data:
            price_str = str(offers_data['price'])
            numbers = re.findall(r'\d+', price_str)
            if numbers:
                return int(''.join(numbers))
        return None

    def _extract_area(self, area_data) -> Optional[int]:
        """Extract square footage from area data structure"""
        if isinstance(area_data, dict) and 'value' in area_data:
            return int(area_data['value'])
        elif isinstance(area_data, (int, float)):
            return int(area_data)
        return None

    def get_rent_estimate(self, address: str, beds: int, baths: int, sqft: int) -> Optional[float]:
        """
        Get rental estimate for property
        """
        try:
            # Use a rental estimation service or algorithm
            # For now, use a basic calculation based on location and size
            base_rent_per_sqft = self._get_area_rent_rate(address)
            if base_rent_per_sqft and sqft:
                estimated_rent = base_rent_per_sqft * sqft
                # Adjust for bedrooms/bathrooms
                bedroom_multiplier = 1 + (beds - 2) * 0.1
                bathroom_multiplier = 1 + (baths - 2) * 0.05
                return estimated_rent * bedroom_multiplier * bathroom_multiplier
        except Exception as e:
            logging.error(f"Rent estimation error: {e}")
        
        return None

    def _get_area_rent_rate(self, address: str) -> Optional[float]:
        """
        Get average rent per square foot for the area
        """
        # This would typically use a rental data API
        # For now, return a reasonable default based on common rates
        return 1.2  # $1.20 per sqft as example

    def get_property_images(self, address: str) -> List[str]:
        """
        Get property images from various sources
        """
        images = []
        
        try:
            # Try to get images from real estate sites
            # This would be enhanced with proper API access
            pass
        except Exception as e:
            logging.error(f"Image fetch error: {e}")
        
        return images

# Singleton instance
property_service = PropertyDataService()