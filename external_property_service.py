"""
External Property Data Service
Pulls authentic property data from Zillow, Redfin, and Realtor.com
"""
import requests
import json
import logging
from typing import Dict, Optional, List
import re
from urllib.parse import quote
import time
from bs4 import BeautifulSoup
from requests_html import HTMLSession

class ExternalPropertyService:
    def __init__(self):
        self.session = HTMLSession()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def get_comprehensive_property_data(self, address: str, city: str, state: str, zip_code: str) -> Dict:
        """
        Get comprehensive property data from all available sources
        """
        full_address = f"{address}, {city}, {state} {zip_code}"
        
        # Initialize result structure
        property_data = {
            'address': full_address,
            'image_url': None,
            'bedrooms': None,
            'bathrooms': None,
            'square_feet': None,
            'year_built': None,
            'lot_size_sqft': None,
            'property_type': None,
            'zillow_estimate': None,
            'redfin_estimate': None,
            'realtor_estimate': None,
            'rent_estimate': None,
            'data_sources': [],
            'errors': []
        }
        
        # Try each source independently
        zillow_data = self._get_zillow_data(full_address)
        redfin_data = self._get_redfin_data(full_address)
        realtor_data = self._get_realtor_data(full_address)
        
        # Merge data from all sources
        self._merge_property_data(property_data, zillow_data, 'Zillow')
        self._merge_property_data(property_data, redfin_data, 'Redfin')
        self._merge_property_data(property_data, realtor_data, 'Realtor.com')
        
        logging.info(f"Retrieved property data from {len(property_data['data_sources'])} sources for {full_address}")
        return property_data
    
    def _get_zillow_data(self, address: str) -> Dict:
        """
        Get property data from Zillow using web scraping
        """
        try:
            # Search for property on Zillow
            search_url = "https://www.zillow.com/homes/{}_rb/".format(quote(address))
            
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract property data from the page
                property_data = {}
                
                # Look for Zestimate in text content
                zestimate_elements = soup.find_all(text=re.compile(r'\$[\d,]+'))
                if zestimate_elements:
                    for element in zestimate_elements:
                        element_str = str(element)
                        price_match = re.search(r'\$([0-9,]+)', element_str)
                        if price_match:
                            price_str = price_match.group(1).replace(',', '')
                            if len(price_str) >= 5:  # Reasonable property price
                                property_data['estimate'] = int(price_str)
                                break
                
                # Look for property details in text
                beds_element = soup.find(text=re.compile(r'\d+ bed'))
                if beds_element:
                    beds_match = re.search(r'(\d+) bed', str(beds_element))
                    if beds_match:
                        property_data['bedrooms'] = int(beds_match.group(1))
                
                baths_element = soup.find(text=re.compile(r'\d+\.?\d* bath'))
                if baths_element:
                    baths_match = re.search(r'(\d+\.?\d*) bath', str(baths_element))
                    if baths_match:
                        property_data['bathrooms'] = float(baths_match.group(1))
                
                sqft_element = soup.find(text=re.compile(r'[\d,]+ sqft'))
                if sqft_element:
                    sqft_match = re.search(r'([\d,]+) sqft', str(sqft_element))
                    if sqft_match:
                        property_data['square_feet'] = int(sqft_match.group(1).replace(',', ''))
                
                # Look for property image
                img_elements = soup.find_all('img', {'alt': re.compile(r'property|home|house', re.I)})
                if img_elements and hasattr(img_elements[0], 'get'):
                    property_data['image_url'] = img_elements[0].get('src')
                
                logging.info(f"Zillow data extracted: {property_data}")
                return property_data
            
            return {}
            
        except Exception as e:
            logging.error(f"Error fetching Zillow data: {e}")
            return {'error': str(e)}
    
    def _get_redfin_data(self, address: str) -> Dict:
        """
        Get property data from Redfin using their search API
        """
        try:
            # Try Redfin's search endpoint
            search_url = "https://www.redfin.com/stingray/api/gis"
            params = {
                'al': 1,
                'market': 'charlotte',  # Default market
                'query': address,
                'v': 8
            }
            
            # Add Redfin-specific headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.redfin.com/',
                'Accept': 'application/json'
            }
            
            response = self.session.get(search_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('payload') and data['payload'].get('homes'):
                        home_data = data['payload']['homes'][0]
                        
                        property_data = {}
                        
                        # Extract basic details
                        if 'beds' in home_data:
                            property_data['bedrooms'] = home_data['beds']
                        if 'baths' in home_data:
                            property_data['bathrooms'] = home_data['baths']
                        if 'sqFt' in home_data and home_data['sqFt']:
                            property_data['square_feet'] = home_data['sqFt'].get('value')
                        if 'yearBuilt' in home_data and home_data['yearBuilt']:
                            property_data['year_built'] = home_data['yearBuilt'].get('value')
                        if 'lotSize' in home_data and home_data['lotSize']:
                            property_data['lot_size_sqft'] = home_data['lotSize'].get('value')
                        
                        # Extract price estimate
                        if 'price' in home_data and home_data['price']:
                            property_data['estimate'] = home_data['price'].get('value')
                        
                        logging.info(f"Redfin data extracted: {property_data}")
                        return property_data
                        
                except json.JSONDecodeError:
                    logging.error("Failed to parse Redfin JSON response")
            
            # Fallback: Try scraping Redfin search page
            return self._scrape_redfin_page(address)
                
        except Exception as e:
            logging.error(f"Error fetching Redfin data: {e}")
            return {'error': str(e)}
    
    def _scrape_redfin_page(self, address: str) -> Dict:
        """Scrape Redfin search page as fallback"""
        try:
            search_url = f"https://www.redfin.com/city/30327/NC/Charlotte/filter/include=sold-1yr"
            
            # Add search query
            params = {'q': address}
            
            response = self.session.get(search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                property_data = {}
                
                # Look for price in search results
                price_elements = soup.find_all('span', class_=re.compile(r'price|amount', re.I))
                for element in price_elements:
                    price_text = element.get_text()
                    price_match = re.search(r'\$([0-9,]+)', price_text)
                    if price_match:
                        price_str = price_match.group(1).replace(',', '')
                        if len(price_str) >= 5:  # Reasonable property price
                            property_data['estimate'] = int(price_str)
                            break
                
                # Look for property specs
                spec_elements = soup.find_all('div', class_=re.compile(r'stats|details|spec', re.I))
                for element in spec_elements:
                    text = element.get_text()
                    
                    beds_match = re.search(r'(\d+)\s*bed', text, re.I)
                    if beds_match:
                        property_data['bedrooms'] = int(beds_match.group(1))
                    
                    baths_match = re.search(r'(\d+\.?\d*)\s*bath', text, re.I)
                    if baths_match:
                        property_data['bathrooms'] = float(baths_match.group(1))
                    
                    sqft_match = re.search(r'([\d,]+)\s*sq\.?\s*ft', text, re.I)
                    if sqft_match:
                        property_data['square_feet'] = int(sqft_match.group(1).replace(',', ''))
                
                logging.info(f"Redfin scrape data: {property_data}")
                return property_data
                
        except Exception as e:
            logging.error(f"Error scraping Redfin page: {e}")
            
        return {}
    
    def _get_realtor_data(self, address: str) -> Dict:
        """
        Get property data from Realtor.com using RapidAPI
        """
        try:
            # Use RapidAPI for Realtor.com
            url = "https://realtor.p.rapidapi.com/properties/v3/list"
            
            querystring = {
                "limit": "1",
                "offset": "0",
                "postal_code": "",
                "state_code": "",
                "city": "",
                "sort": "relevance",
                "list_price": "",
                "beds_min": "",
                "baths_min": "",
                "sqft_min": "",
                "query": address
            }
            
            headers = {
                "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY_HERE",  # User will need to provide this
                "X-RapidAPI-Host": "realtor.p.rapidapi.com"
            }
            
            response = self.session.get(url, headers=headers, params=querystring, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                parsed_data = self._parse_realtor_data(data)
                return parsed_data if parsed_data else {}
            
            return {}
                
        except Exception as e:
            logging.error(f"Error fetching Realtor.com data: {e}")
            return {'error': str(e)}
    
    def _parse_zillow_response(self, response_text: str, address: str) -> Dict:
        """Parse Zillow API response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'{"results".*?}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                
                if data.get('results'):
                    property_info = data['results'][0]
                    
                    return {
                        'bedrooms': property_info.get('beds'),
                        'bathrooms': property_info.get('baths'),
                        'square_feet': property_info.get('area'),
                        'year_built': property_info.get('yearBuilt'),
                        'lot_size_sqft': property_info.get('lotAreaValue'),
                        'property_type': property_info.get('propertyType'),
                        'estimate': property_info.get('zestimate'),
                        'rent_estimate': property_info.get('rentZestimate'),
                        'image_url': property_info.get('imgSrc')
                    }
                    
        except Exception as e:
            logging.error(f"Error parsing Zillow response: {e}")
            
        return {}
    
    def _scrape_zillow_page(self, address: str) -> Dict:
        """Scrape Zillow property page directly"""
        try:
            # Format address for URL
            search_address = quote(address)
            url = f"https://www.zillow.com/homes/{search_address}_rb/"
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                # Look for JSON data in page
                json_matches = re.findall(r'"apiCache":\s*({.*?})\s*,\s*"', response.text)
                
                for match in json_matches:
                    try:
                        data = json.loads(match)
                        # Extract property data from cache
                        return self._extract_zillow_cache_data(data)
                    except:
                        continue
                        
        except Exception as e:
            logging.error(f"Error scraping Zillow page: {e}")
            
        return {}
    
    def _parse_redfin_data(self, data: Dict) -> Dict:
        """Parse Redfin API response"""
        try:
            if data.get('payload') and data['payload'].get('homes'):
                home = data['payload']['homes'][0]
                
                return {
                    'bedrooms': home.get('beds'),
                    'bathrooms': home.get('baths'),
                    'square_feet': home.get('sqFt', {}).get('value'),
                    'year_built': home.get('yearBuilt', {}).get('value'),
                    'lot_size_sqft': home.get('lotSize', {}).get('value'),
                    'property_type': home.get('propertyType'),
                    'estimate': home.get('price', {}).get('value'),
                    'image_url': home.get('url')  # Redfin image URL
                }
                
        except Exception as e:
            logging.error(f"Error parsing Redfin data: {e}")
            
        return {}
    
    def _parse_realtor_data(self, data: Dict) -> Dict:
        """Parse Realtor.com API response"""
        try:
            if data.get('data') and data['data'].get('home_search') and data['data']['home_search'].get('results'):
                home = data['data']['home_search']['results'][0]
                
                return {
                    'bedrooms': home.get('description', {}).get('beds'),
                    'bathrooms': home.get('description', {}).get('baths'),
                    'square_feet': home.get('description', {}).get('sqft'),
                    'year_built': home.get('description', {}).get('year_built'),
                    'lot_size_sqft': home.get('description', {}).get('lot_sqft'),
                    'property_type': home.get('description', {}).get('type'),
                    'estimate': home.get('list_price'),
                    'rent_estimate': home.get('community', {}).get('price_range', {}).get('min'),
                    'image_url': home.get('primary_photo', {}).get('href')
                }
                
        except Exception as e:
            logging.error(f"Error parsing Realtor.com data: {e}")
            
        return {}
    
    def _extract_zillow_cache_data(self, cache_data: Dict) -> Dict:
        """Extract property data from Zillow cache"""
        try:
            # Navigate through Zillow's complex cache structure
            for key, value in cache_data.items():
                if isinstance(value, dict) and 'property' in str(value).lower():
                    # Found property data
                    prop_data = value.get('property', {})
                    
                    return {
                        'bedrooms': prop_data.get('bedrooms'),
                        'bathrooms': prop_data.get('bathrooms'),
                        'square_feet': prop_data.get('livingArea'),
                        'year_built': prop_data.get('yearBuilt'),
                        'lot_size_sqft': prop_data.get('lotAreaValue'),
                        'property_type': prop_data.get('propertyType'),
                        'estimate': prop_data.get('zestimate'),
                        'rent_estimate': prop_data.get('rentZestimate'),
                        'image_url': prop_data.get('photoUrl')
                    }
                    
        except Exception as e:
            logging.error(f"Error extracting Zillow cache data: {e}")
            
        return {}
    
    def _merge_property_data(self, main_data: Dict, source_data: Dict, source_name: str):
        """Merge data from a specific source into main property data"""
        if source_data.get('error'):
            main_data['errors'].append(f"{source_name}: {source_data['error']}")
            return
            
        if not source_data:
            return
            
        # Add source to list
        main_data['data_sources'].append(source_name)
        
        # Merge property details (use first available value)
        for field in ['bedrooms', 'bathrooms', 'square_feet', 'year_built', 'lot_size_sqft', 'property_type', 'rent_estimate']:
            if main_data[field] is None and source_data.get(field) is not None:
                main_data[field] = source_data[field]
        
        # Handle estimates specifically by source
        if source_name == 'Zillow' and source_data.get('estimate'):
            main_data['zillow_estimate'] = source_data['estimate']
        elif source_name == 'Redfin' and source_data.get('estimate'):
            main_data['redfin_estimate'] = source_data['estimate']
        elif source_name == 'Realtor.com' and source_data.get('estimate'):
            main_data['realtor_estimate'] = source_data['estimate']
        
        # Use first available image
        if main_data['image_url'] is None and source_data.get('image_url'):
            main_data['image_url'] = source_data['image_url']

# Create global instance
external_property_service = ExternalPropertyService()