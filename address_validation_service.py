"""
Address Validation and Normalization Service
Ensures accurate property matching across multiple data sources
"""
import os
import re
import logging
import requests
from typing import Dict, Optional, Tuple, List
from urllib.parse import quote

class AddressValidationService:
    def __init__(self):
        self.google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        self.session = requests.Session()
        
        # Common address abbreviations and their full forms
        self.abbreviation_map = {
            'st': 'street', 'str': 'street', 'st.': 'street',
            'rd': 'road', 'rd.': 'road',
            'ave': 'avenue', 'av': 'avenue', 'ave.': 'avenue',
            'blvd': 'boulevard', 'blv': 'boulevard', 'blvd.': 'boulevard',
            'dr': 'drive', 'dr.': 'drive',
            'ln': 'lane', 'ln.': 'lane',
            'ct': 'court', 'ct.': 'court',
            'cir': 'circle', 'cir.': 'circle',
            'pl': 'place', 'pl.': 'place',
            'way': 'way', 'wy': 'way',
            'pkwy': 'parkway', 'pky': 'parkway',
            'terr': 'terrace', 'ter': 'terrace',
            'flt': 'flight'  # Special case for "Evening Flight Lane"
        }
        
        # State abbreviations
        self.state_map = {
            'north carolina': 'NC', 'n carolina': 'NC', 'n.carolina': 'NC',
            'south carolina': 'SC', 's carolina': 'SC', 's.carolina': 'SC',
            'georgia': 'GA', 'tennessee': 'TN', 'florida': 'FL',
            'virginia': 'VA', 'texas': 'TX', 'california': 'CA'
        }
    
    def validate_and_normalize_address(self, raw_address: str, city: str = "", state: str = "", zip_code: str = "") -> Dict:
        """
        5-Layer Defense: Validate and normalize address using multiple fallback strategies
        """
        logging.info(f"Validating address: {raw_address}")
        
        # Layer 1: Google Places API with autocomplete data
        if hasattr(self, '_autocomplete_data') and self._autocomplete_data:
            return self._process_autocomplete_selection(self._autocomplete_data)
        
        # Layer 2: Google Geocoding API fallback
        geocoded_result = self.geocode_loose(raw_address, city, state, zip_code)
        if geocoded_result:
            return geocoded_result
        
        # Layer 3: Manual normalization with enhanced fuzzy matching
        normalized_input = self._normalize_address_input(raw_address, city, state, zip_code)
        
        # Step 2: Try Google Places API validation
        if self.google_api_key:
            google_result = self._validate_with_google_places(normalized_input['full_address'])
            if google_result and google_result.get('status') == 'success':
                return google_result
        
        # Step 3: Fallback to manual normalization
        fallback_result = self._manual_address_normalization(normalized_input)
        logging.info(f"Using manual normalization: {fallback_result}")
        
        return fallback_result
    
    def _normalize_address_input(self, address: str, city: str, state: str, zip_code: str) -> Dict:
        """
        Initial cleanup and normalization of user input
        """
        # Clean the address string
        clean_address = re.sub(r'\s+', ' ', address.strip().lower())
        clean_city = city.strip().title() if city else ""
        clean_state = state.strip().upper() if state else ""
        clean_zip = re.sub(r'[^\d-]', '', zip_code) if zip_code else ""
        
        # Extract ZIP from address if present
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', clean_address)
        if zip_match and not clean_zip:
            clean_zip = zip_match.group(1)
            clean_address = clean_address.replace(zip_match.group(0), '').strip()
        
        # Extract state from address if present
        state_match = re.search(r'\b([a-z]{2})\b', clean_address)
        if state_match and not clean_state:
            potential_state = state_match.group(1).upper()
            if potential_state in ['NC', 'SC', 'GA', 'TN', 'FL', 'VA', 'TX', 'CA']:
                clean_state = potential_state
                clean_address = clean_address.replace(state_match.group(0), '').strip()
        
        # Extract city if present in address
        if not clean_city:
            # Look for common city patterns before state
            city_pattern = r'([a-z\s]+?)(?:\s+(?:nc|sc|ga|tn|fl|va|tx|ca)|\s+\d{5}|$)'
            city_match = re.search(city_pattern, clean_address)
            if city_match:
                potential_city = city_match.group(1).strip().title()
                if len(potential_city) > 2:  # Reasonable city name length
                    clean_city = potential_city
                    clean_address = clean_address.replace(city_match.group(1), '').strip()
        
        # Normalize street abbreviations
        normalized_street = self._normalize_street_name(clean_address)
        
        # Build full address
        full_address_parts = [normalized_street]
        if clean_city:
            full_address_parts.append(clean_city)
        if clean_state:
            full_address_parts.append(clean_state)
        if clean_zip:
            full_address_parts.append(clean_zip)
        
        return {
            'street': normalized_street,
            'city': clean_city,
            'state': clean_state,
            'zip': clean_zip.split('-')[0] if clean_zip else "",  # Use 5-digit ZIP
            'full_address': ', '.join(full_address_parts)
        }
    
    def _normalize_street_name(self, street: str) -> str:
        """
        Normalize street name abbreviations and formatting
        """
        # Split into words
        words = street.split()
        normalized_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            # Check if it's an abbreviation
            if clean_word in self.abbreviation_map:
                normalized_words.append(self.abbreviation_map[clean_word].title())
            else:
                # Capitalize properly
                normalized_words.append(word.title())
        
        return ' '.join(normalized_words)
    
    def _validate_with_google_places(self, address: str) -> Optional[Dict]:
        """
        Validate address using Google Places API
        """
        try:
            url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            params = {
                'input': address,
                'inputtype': 'textquery',
                'fields': 'place_id,formatted_address,geometry,address_components',
                'key': self.google_api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('candidates'):
                    candidate = data['candidates'][0]
                    
                    # Parse address components
                    parsed_address = self._parse_google_address_components(
                        candidate.get('address_components', [])
                    )
                    
                    return {
                        'status': 'success',
                        'source': 'Google Places API',
                        'street': parsed_address['street'],
                        'city': parsed_address['city'],
                        'state': parsed_address['state'],
                        'zip': parsed_address['zip'],
                        'full_address': candidate.get('formatted_address', ''),
                        'latitude': candidate['geometry']['location']['lat'],
                        'longitude': candidate['geometry']['location']['lng'],
                        'place_id': candidate.get('place_id'),
                        'confidence': 'high'
                    }
            
        except Exception as e:
            logging.error(f"Google Places API error: {e}")
        
        return None
    
    def _parse_google_address_components(self, components: List[Dict]) -> Dict:
        """
        Parse Google Places address components into structured format
        """
        result = {'street': '', 'city': '', 'state': '', 'zip': ''}
        
        street_number = ''
        street_name = ''
        
        for component in components:
            types = component.get('types', [])
            
            if 'street_number' in types:
                street_number = component['long_name']
            elif 'route' in types:
                street_name = component['long_name']
            elif 'locality' in types:
                result['city'] = component['long_name']
            elif 'administrative_area_level_1' in types:
                result['state'] = component['short_name']
            elif 'postal_code' in types:
                result['zip'] = component['long_name']
        
        if street_number and street_name:
            result['street'] = f"{street_number} {street_name}"
        
        return result
    
    def _manual_address_normalization(self, normalized_input: Dict) -> Dict:
        """
        Manual address normalization as fallback
        """
        return {
            'status': 'normalized',
            'source': 'Manual Normalization',
            'street': normalized_input['street'],
            'city': normalized_input['city'],
            'state': normalized_input['state'],
            'zip': normalized_input['zip'],
            'full_address': normalized_input['full_address'],
            'latitude': None,
            'longitude': None,
            'confidence': 'medium'
        }
    
    def generate_search_variations(self, validated_address: Dict) -> List[str]:
        """
        Generate address variations for fuzzy matching across APIs
        """
        variations = []
        
        # Primary full address
        variations.append(validated_address['full_address'])
        
        # Street + City + State
        if all([validated_address['street'], validated_address['city'], validated_address['state']]):
            variations.append(f"{validated_address['street']}, {validated_address['city']}, {validated_address['state']}")
        
        # Street + ZIP
        if validated_address['street'] and validated_address['zip']:
            variations.append(f"{validated_address['street']}, {validated_address['zip']}")
        
        # Full address without ZIP
        if all([validated_address['street'], validated_address['city'], validated_address['state']]):
            variations.append(f"{validated_address['street']}, {validated_address['city']}, {validated_address['state']}")
        
        return variations
    
    def calculate_address_confidence(self, result_address: str, target_address: Dict) -> float:
        """
        Calculate confidence score for address matching
        """
        score = 0.0
        
        # Normalize both addresses for comparison
        result_lower = result_address.lower()
        
        # Check street number match (high importance)
        street_number = re.search(r'^(\d+)', target_address['street'])
        if street_number:
            if street_number.group(1) in result_lower:
                score += 0.4
        
        # Check ZIP code match (high importance)
        if target_address['zip'] and target_address['zip'] in result_lower:
            score += 0.3
        
        # Check city match
        if target_address['city'] and target_address['city'].lower() in result_lower:
            score += 0.2
        
        # Check state match
        if target_address['state'] and target_address['state'].lower() in result_lower:
            score += 0.1
        
        return min(score, 1.0)

    def geocode_loose(self, address: str, city: str = "", state: str = "", zip_code: str = "") -> Optional[Dict]:
        """
        Layer 2: Google Geocoding API fallback for loose address matching
        """
        if not self.google_api_key:
            logging.warning("Google Maps API key not available for geocoding")
            return None
            
        try:
            # Construct full address for geocoding
            full_address = f"{address}"
            if city:
                full_address += f", {city}"
            if state:
                full_address += f", {state}"
            if zip_code:
                full_address += f" {zip_code}"
            
            # Call Google Geocoding API
            url = f"https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': full_address,
                'key': self.google_api_key,
                'components': 'country:US'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                result = data['results'][0]
                
                # Extract address components
                components = self._parse_google_geocoding_components(result['address_components'])
                
                return {
                    'status': 'geocoded',
                    'source': 'Google Geocoding API',
                    'place_id': result.get('place_id'),
                    'formatted_address': result['formatted_address'],
                    'street': components.get('street_number', '') + ' ' + components.get('route', ''),
                    'city': components.get('locality') or components.get('sublocality'),
                    'state': components.get('administrative_area_level_1'),
                    'zip': components.get('postal_code'),
                    'full_address': result['formatted_address'],
                    'latitude': result['geometry']['location']['lat'],
                    'longitude': result['geometry']['location']['lng'],
                    'confidence': 'high' if result['geometry']['location_type'] == 'ROOFTOP' else 'medium'
                }
            else:
                logging.warning(f"Google Geocoding failed: {data.get('status', 'Unknown error')}")
                return None
                
        except Exception as e:
            logging.error(f"Error in Google Geocoding: {e}")
            return None
    
    def _parse_google_geocoding_components(self, components: List[Dict]) -> Dict:
        """
        Parse Google Geocoding API address components
        """
        parsed = {}
        
        for component in components:
            types = component['types']
            long_name = component['long_name']
            short_name = component['short_name']
            
            if 'street_number' in types:
                parsed['street_number'] = long_name
            elif 'route' in types:
                parsed['route'] = long_name
            elif 'locality' in types:
                parsed['locality'] = long_name
            elif 'sublocality' in types:
                parsed['sublocality'] = long_name
            elif 'administrative_area_level_1' in types:
                parsed['administrative_area_level_1'] = short_name
            elif 'postal_code' in types:
                parsed['postal_code'] = long_name
                
        return parsed
    
    def _process_autocomplete_selection(self, autocomplete_data: Dict) -> Dict:
        """
        Layer 1: Process Google Places Autocomplete selection
        """
        return {
            'status': 'autocomplete',
            'source': 'Google Places Autocomplete',
            'place_id': autocomplete_data.get('place_id'),
            'formatted_address': autocomplete_data.get('formatted_address'),
            'confidence': 'high'
        }
    
    def set_autocomplete_data(self, place_id: str, formatted_address: str):
        """
        Set autocomplete data from frontend selection
        """
        self._autocomplete_data = {
            'place_id': place_id,
            'formatted_address': formatted_address
        }
    
    def calculate_fuzzy_similarity(self, addr1: str, addr2: str) -> float:
        """
        Layer 4: Calculate fuzzy similarity between addresses for database matching
        """
        # Normalize both addresses
        norm1 = self._normalize_address_for_comparison(addr1.lower())
        norm2 = self._normalize_address_for_comparison(addr2.lower())
        
        # Simple character-based similarity
        if norm1 == norm2:
            return 1.0
        
        # Calculate Jaccard similarity on words
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _normalize_address_for_comparison(self, address: str) -> str:
        """
        Normalize address for fuzzy comparison
        """
        # Remove common punctuation
        address = re.sub(r'[,\.\-#]', ' ', address)
        
        # Normalize street abbreviations
        words = address.split()
        normalized_words = []
        
        for word in words:
            # Remove trailing periods and normalize
            clean_word = word.strip('.')
            normalized_word = self.abbreviation_map.get(clean_word, clean_word)
            normalized_words.append(normalized_word)
        
        # Remove extra spaces
        return ' '.join(normalized_words).strip()

# Create global instance
address_validator = AddressValidationService()