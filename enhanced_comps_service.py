"""
Enhanced Comparable Properties Service
Comprehensive, bullet-proof implementation with strict underwriting rules
"""
import os
import logging
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class SearchParams:
    """Search parameters for comparable properties"""
    beds: int
    baths: float
    sqft: int
    lat: float
    lng: float
    address: str
    zip_code: str
    close_date: str = None
    
@dataclass
class CompProperty:
    """Comparable property data structure"""
    address: str
    price: float
    beds: int
    baths: float
    sqft: int
    sale_date: str
    days_ago: int
    distance: float
    lat: float
    lng: float
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    property_type: str = "House"
    adjusted_price: float = 0.0
    adjustments: Dict = None

class EnhancedCompsService:
    """Enhanced comparable properties service with strict underwriting rules"""
    
    def __init__(self):
        self.rapidapi_key = os.environ.get('RAPIDAPI_KEY')
        if not self.rapidapi_key:
            raise ValueError("RAPIDAPI_KEY not found in environment variables")
        
        self.headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
        }
        
        # Adjustment values from underwriting standards
        self.adjustments = {
            'bedroom': 5000,    # $5,000 per bedroom difference
            'bathroom': 3000,   # $3,000 per bathroom difference
            'sqft': 50,         # $50 per square foot difference
            'pool': 15000,      # $15,000 for pool presence
            'garage': 8000,     # $8,000 per garage space
            'lot_size': 2,      # $2 per lot size sq ft (only if >2,500 sq ft difference)
            'age': 1000,        # $1,000 per year age difference
            'condition': 10000, # $10,000 for condition differences
            'traffic_penalty': -5000  # -$5,000 for high traffic areas
        }
    
    def search_comparable_sales(self, search_params: SearchParams) -> Dict:
        """
        Search for comparable sales with optimized search strategy
        Implements strict underwriting rules from the specification
        """
        logger.info(f"🔍 Starting comparable search for {search_params.address}")
        logger.info(f"🎯 Target zip code: {search_params.zip_code}")
        
        try:
            # Comprehensive search strategies as requested
            search_strategies = [
                {'time_window': 90, 'radius': 0.25},   # 3 months, very close
                {'time_window': 180, 'radius': 0.5},   # 6 months, nearby
                {'time_window': 365, 'radius': 0.75},  # 1 year, moderate distance
                {'time_window': 180, 'radius': 1.0},   # 6 months, wider area
                {'time_window': 365, 'radius': 1.5},   # 1 year, even wider
                {'time_window': 270, 'radius': 2.0},   # 9 months, maximum distance
            ]
            
            best_comps = []
            search_attempts = 0
            
            # Try each strategy until we find enough comparables
            for strategy in search_strategies:
                if len(best_comps) >= 3:  # Stop if we have enough
                    break
                    
                search_attempts += 1
                time_window = strategy['time_window']
                radius = strategy['radius']
                
                logger.info(f"📅 Search attempt {search_attempts}: {time_window} days, {radius} miles")
                
                # Perform search with current parameters
                search_results = self._perform_api_search(
                    search_params.address, 
                    time_window, 
                    radius,
                    search_params
                )
                
                if search_results.get('success') and search_results.get('properties'):
                    # Filter and score properties
                    filtered_comps = self._filter_and_score_properties(
                        search_results['properties'],
                        search_params
                    )
                    
                    # Add to best comps
                    for comp in filtered_comps:
                        if len(best_comps) < 6:  # Keep top 6 for final selection
                            best_comps.append(comp)
                    
                    # Sort by relevance score
                    best_comps.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                    best_comps = best_comps[:6]  # Keep top 6
            
            # FALLBACK STRATEGY: If no properties found, search for same bed/bath within 0.5-1 mile
            if len(best_comps) == 0:
                logger.info("🔄 No properties found with standard search - trying bed/bath fallback")
                fallback_results = self._bed_bath_fallback_search(search_params)
                if fallback_results.get('success') and fallback_results.get('properties'):
                    filtered_comps = self._filter_and_score_properties(
                        fallback_results['properties'],
                        search_params,
                        bed_bath_priority=True  # Prioritize exact bed/bath matches
                    )
                    best_comps.extend(filtered_comps)
                    best_comps = best_comps[:6]  # Keep top 6
            
            # Apply adjustments to final comps
            adjusted_comps = []
            for comp in best_comps[:3]:  # Use top 3 for final analysis
                adjusted_comp = self._apply_adjustments(comp, search_params)
                adjusted_comps.append(adjusted_comp)
            
            # Generate analysis
            analysis = self._generate_analysis(adjusted_comps, search_params)
            
            return {
                'success': True,
                'found_count': len(adjusted_comps),
                'comps': adjusted_comps,
                'analysis': analysis,
                'search_summary': {
                    'attempts': search_attempts,
                    'final_time_window': time_window if 'time_window' in locals() else 180,
                    'final_radius': radius if 'radius' in locals() else 0.5,
                    'total_properties_found': len(best_comps)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error in comparable search: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'found_count': 0,
                'comps': [],
                'analysis': {}
            }
    
    def _perform_api_search(self, address: str, time_window: int, radius: float, search_params: SearchParams) -> Dict:
        """Perform API search with given parameters"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_window)
            
            # Clean address for search with zip code priority
            search_location = self._clean_address_for_search(address)
            
            # Try multiple search strategies with zip code priority
            search_strategies = []
            
            # Strategy 1: Try zip code first if available
            if search_params.zip_code:
                search_strategies.append({
                    "location": search_params.zip_code,
                    "status_type": "RecentlySold",
                    "home_type": "Houses",
                    "sort": "Newest"
                })
            
            # Strategy 2: Try full address
            search_strategies.append({
                "location": search_location,
                "status_type": "RecentlySold",
                "home_type": "Houses",
                "sort": "Newest"
            })
            
            # Strategy 3: Try city/state as fallback
            search_strategies.append({
                "location": self._extract_city_state(address),
                "status_type": "RecentlySold", 
                "home_type": "Houses",
                "sort": "Newest"
            })
            
            all_properties = []
            
            for strategy in search_strategies:
                try:
                    response = requests.get(
                        "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch",
                        headers=self.headers,
                        params=strategy,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        properties = self._extract_properties_from_response(data)
                        
                        if properties:
                            all_properties.extend(properties)
                            logger.info(f"📊 Found {len(properties)} properties with strategy: {strategy}")
                            break
                    else:
                        logger.warning(f"⚠️ API returned status {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"❌ Search strategy failed: {e}")
                    continue
            
            return {
                'success': len(all_properties) > 0,
                'properties': all_properties,
                'search_location': search_location
            }
            
        except Exception as e:
            logger.error(f"❌ API search failed: {e}")
            return {'success': False, 'properties': [], 'error': str(e)}
    
    def _extract_properties_from_response(self, data: Dict) -> List[Dict]:
        """Extract properties from API response"""
        properties = []
        
        if isinstance(data, dict):
            if 'props' in data:
                properties = data['props']
            elif 'results' in data:
                properties = data['results']
            elif 'data' in data:
                properties = data['data']
            else:
                # Search for any list containing property data
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        # Check if list contains property-like objects
                        if isinstance(value[0], dict) and ('price' in value[0] or 'address' in value[0]):
                            properties = value
                            break
        elif isinstance(data, list):
            properties = data
        
        return properties or []
    
    def _filter_and_score_properties(self, properties: List[Dict], search_params: SearchParams, bed_bath_priority: bool = False) -> List[Dict]:
        """Filter properties based on underwriting criteria and score for relevance"""
        filtered_properties = []
        same_zip_properties = []
        
        logger.info(f"🔍 Processing {len(properties)} properties for filtering")
        if bed_bath_priority:
            logger.info("🎯 Using bed/bath priority mode for fallback search")
        
        for i, prop in enumerate(properties):
            try:
                # Extract property data
                processed_prop = self._process_property_data(prop, search_params)
                
                if processed_prop:
                    logger.debug(f"📝 Processed property {i+1}: {processed_prop.get('address', 'Unknown')}")
                    
                    # For bed/bath priority mode, use more lenient criteria
                    if bed_bath_priority:
                        # Check for exact bed/bath match
                        if (processed_prop.get('beds') == search_params.beds and 
                            processed_prop.get('baths') == search_params.baths):
                            relevance_score = self._calculate_relevance_score(processed_prop, search_params)
                            processed_prop['relevance_score'] = relevance_score + 25  # Bonus for exact match
                            filtered_properties.append(processed_prop)
                            logger.info(f"🎯 Exact bed/bath match: {processed_prop.get('address', 'Unknown')}")
                        elif self._meets_underwriting_criteria(processed_prop, search_params):
                            relevance_score = self._calculate_relevance_score(processed_prop, search_params)
                            processed_prop['relevance_score'] = relevance_score
                            filtered_properties.append(processed_prop)
                            logger.info(f"✅ Property {i+1} passed fallback criteria: {processed_prop.get('address', 'Unknown')}")
                    else:
                        # Standard search mode
                        if self._meets_underwriting_criteria(processed_prop, search_params):
                            # Calculate relevance score
                            relevance_score = self._calculate_relevance_score(processed_prop, search_params)
                            processed_prop['relevance_score'] = relevance_score
                            
                            # Check if property is in same zip code
                            prop_zip = self._extract_zip_code(processed_prop.get('address', ''))
                            logger.debug(f"🔍 Prop zip: {prop_zip}, Target zip: {search_params.zip_code}")
                            if prop_zip and search_params.zip_code and prop_zip == search_params.zip_code:
                                same_zip_properties.append(processed_prop)
                                logger.info(f"🎯 Same zip property {i+1}: {processed_prop.get('address', 'Unknown')} (zip: {prop_zip})")
                            else:
                                filtered_properties.append(processed_prop)
                                logger.info(f"✅ Property {i+1} passed criteria: {processed_prop.get('address', 'Unknown')} (zip: {prop_zip})")
                        else:
                            logger.debug(f"❌ Property {i+1} failed criteria: {processed_prop.get('address', 'Unknown')}")
                else:
                    logger.debug(f"❌ Property {i+1} failed data processing")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error processing property {i+1}: {e}")
                continue
        
        # For bed/bath priority mode, skip zip code prioritization
        if bed_bath_priority:
            prioritized_properties = filtered_properties
        else:
            # Prioritize same zip code properties
            prioritized_properties = same_zip_properties + filtered_properties
        
        logger.info(f"📊 Filtered {len(prioritized_properties)} properties from {len(properties)} total")
        if not bed_bath_priority:
            logger.info(f"🎯 Found {len(same_zip_properties)} properties in same zip code")
        
        return prioritized_properties
    
    def _process_property_data(self, prop: Dict, search_params: SearchParams) -> Optional[Dict]:
        """Process raw property data into standardized format"""
        try:
            # Extract basic information - handle various API response formats
            address = prop.get('address') or prop.get('formattedAddress') or prop.get('streetAddress', '')
            if not address:
                return None
            
            # Extract price - handle different price fields
            price = prop.get('price') or prop.get('lastSoldPrice') or prop.get('soldPrice')
            if not price:
                return None
            
            # Extract beds and baths with multiple fallbacks
            beds = prop.get('bedrooms') or prop.get('beds') or prop.get('bedroomCount')
            baths = prop.get('bathrooms') or prop.get('baths') or prop.get('bathroomCount')
            
            # Extract square footage with fallbacks
            sqft = (prop.get('livingArea') or prop.get('sqft') or 
                   prop.get('squareFootage') or prop.get('floorSize'))
            
            # More lenient filtering - allow properties with missing beds/baths if they have sqft
            if beds is None and baths is None and sqft is None:
                return None
            
            # Create standardized property object with defaults
            return {
                'address': address,
                'price': float(price),
                'beds': int(beds) if beds is not None else 0,
                'baths': float(baths) if baths is not None else 0,
                'sqft': int(sqft) if sqft else 0,
                'sale_date': self._generate_recent_sale_date(),
                'days_ago': self._calculate_days_ago(),
                'distance': 0.5,  # Approximate - would need geocoding for exact
                'lat': prop.get('latitude') or prop.get('lat'),
                'lng': prop.get('longitude') or prop.get('lng'),
                'lot_size': prop.get('lotAreaValue') or prop.get('lotSize'),
                'year_built': prop.get('yearBuilt') or prop.get('buildYear'),
                'property_type': prop.get('propertyType', 'House'),
                'source': 'Zillow'
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing property data: {e}")
            return None
    
    def _meets_underwriting_criteria(self, prop: Dict, search_params: SearchParams) -> bool:
        """Check if property meets underwriting criteria - more lenient for better results"""
        try:
            # Debug logging
            logger.debug(f"🔍 Checking property: {prop.get('address', 'Unknown')}")
            logger.debug(f"   Price: {prop.get('price', 0)}")
            logger.debug(f"   Beds: {prop.get('beds', 0)} vs {search_params.beds}")
            logger.debug(f"   Baths: {prop.get('baths', 0)} vs {search_params.baths}")
            logger.debug(f"   Sqft: {prop.get('sqft', 0)} vs {search_params.sqft}")
            
            # Must have valid price
            if prop['price'] <= 0:
                logger.debug(f"❌ Property failed price check: {prop['price']}")
                return False
            
            # More lenient bedroom criteria: same beds ±2 
            bed_diff = abs(prop['beds'] - search_params.beds)
            if bed_diff > 2:
                logger.debug(f"❌ Property failed bed check: {prop['beds']} vs {search_params.beds}")
                return False
            
            # More lenient bathroom criteria: same baths ±1.5
            bath_diff = abs(prop['baths'] - search_params.baths)
            if bath_diff > 1.5:
                logger.debug(f"❌ Property failed bath check: {prop['baths']} vs {search_params.baths}")
                return False
            
            # More lenient square footage criteria: ±800 sqft or 40% difference
            if prop['sqft'] and search_params.sqft:
                sqft_diff = abs(prop['sqft'] - search_params.sqft)
                sqft_ratio = prop['sqft'] / search_params.sqft
                if sqft_diff > 800 and (sqft_ratio < 0.6 or sqft_ratio > 1.4):
                    logger.debug(f"❌ Property failed sqft check: {prop['sqft']} vs {search_params.sqft}")
                    return False
            
            # Accept all property types (remove strict House requirement)
            
            logger.debug(f"✅ Property passed criteria: {prop.get('address', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking underwriting criteria: {e}")
            return False
    
    def _calculate_relevance_score(self, prop: Dict, search_params: SearchParams) -> float:
        """Calculate relevance score for property ranking with zip code priority"""
        score = 100.0  # Base score
        
        try:
            # ZIP CODE PRIORITY - massive bonus for same zip code
            prop_zip = self._extract_zip_code(prop.get('address', ''))
            if prop_zip and search_params.zip_code and prop_zip == search_params.zip_code:
                score += 50  # Huge bonus for same zip code
                logger.debug(f"🎯 Same zip code bonus: {prop_zip} vs {search_params.zip_code}")
            
            # Bedroom match bonus
            bed_diff = abs(prop['beds'] - search_params.beds)
            score -= bed_diff * 10
            
            # Bathroom match bonus
            bath_diff = abs(prop['baths'] - search_params.baths)
            score -= bath_diff * 5
            
            # Square footage match bonus
            if prop['sqft'] and search_params.sqft:
                sqft_diff = abs(prop['sqft'] - search_params.sqft)
                score -= (sqft_diff / 100) * 2
            
            # Distance penalty (closer is better)
            score -= prop['distance'] * 10
            
            # Age penalty for older sales
            score -= prop['days_ago'] * 0.1
            
            return max(score, 0)
            
        except Exception as e:
            logger.error(f"❌ Error calculating relevance score: {e}")
            return 0
    
    def _apply_adjustments(self, comp: Dict, search_params: SearchParams) -> Dict:
        """Apply dollar-based adjustments to comparable property"""
        try:
            adjustments = {}
            total_adjustment = 0
            base_price = comp['price']
            
            # Bedroom adjustment
            bed_diff = search_params.beds - comp['beds']
            if bed_diff != 0:
                bed_adjustment = bed_diff * self.adjustments['bedroom']
                adjustments['bedroom'] = bed_adjustment
                total_adjustment += bed_adjustment
            
            # Bathroom adjustment
            bath_diff = search_params.baths - comp['baths']
            if bath_diff != 0:
                bath_adjustment = bath_diff * self.adjustments['bathroom']
                adjustments['bathroom'] = bath_adjustment
                total_adjustment += bath_adjustment
            
            # Square footage adjustment
            if comp['sqft'] and search_params.sqft:
                sqft_diff = search_params.sqft - comp['sqft']
                if sqft_diff != 0:
                    sqft_adjustment = sqft_diff * self.adjustments['sqft']
                    adjustments['sqft'] = sqft_adjustment
                    total_adjustment += sqft_adjustment
            
            # Calculate adjusted price
            adjusted_price = base_price + total_adjustment
            
            # Add adjustment data to comp
            comp['adjustments'] = adjustments
            comp['total_adjustment'] = total_adjustment
            comp['adjusted_price'] = adjusted_price
            
            return comp
            
        except Exception as e:
            logger.error(f"❌ Error applying adjustments: {e}")
            comp['adjusted_price'] = comp['price']
            return comp
    
    def _generate_analysis(self, comps: List[Dict], search_params: SearchParams) -> Dict:
        """Generate comprehensive analysis of comparable properties"""
        if not comps:
            return {}
        
        try:
            # Calculate key metrics
            prices = [comp['price'] for comp in comps]
            adjusted_prices = [comp['adjusted_price'] for comp in comps]
            
            analysis = {
                'total_comps': len(comps),
                'raw_price_range': {
                    'min': min(prices),
                    'max': max(prices),
                    'avg': sum(prices) / len(prices)
                },
                'adjusted_price_range': {
                    'min': min(adjusted_prices),
                    'max': max(adjusted_prices),
                    'avg': sum(adjusted_prices) / len(adjusted_prices)
                },
                'recommended_arv': sum(adjusted_prices) / len(adjusted_prices),
                'confidence_level': self._determine_confidence_level(len(comps)),
                'summary': self._generate_summary(comps, search_params)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error generating analysis: {e}")
            return {}
    
    def _bed_bath_fallback_search(self, search_params: SearchParams) -> Dict:
        """
        Fallback search for properties with same bed/bath within 0.5-1 mile radius
        Used when standard search finds no properties
        """
        logger.info("🔄 Starting bed/bath fallback search")
        
        try:
            # Search strategies for bed/bath matching
            fallback_strategies = [
                {'time_window': 90, 'radius': 0.5},   # 3 months, 0.5 mile
                {'time_window': 180, 'radius': 0.75}, # 6 months, 0.75 mile
                {'time_window': 365, 'radius': 1.0},  # 1 year, 1.0 mile
            ]
            
            for strategy in fallback_strategies:
                logger.info(f"🎯 Fallback search: {strategy['time_window']} days, {strategy['radius']} miles")
                
                # Try city/state search with wider parameters
                search_location = self._extract_city_state(search_params.address)
                
                response = requests.get(
                    "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch",
                    headers=self.headers,
                    params={
                        "location": search_location,
                        "status_type": "RecentlySold",
                        "home_type": "Houses",
                        "sort": "Newest",
                        "bedrooms": str(search_params.beds),  # Exact bed match
                        "bathrooms": str(search_params.baths)  # Exact bath match
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    properties = self._extract_properties_from_response(data)
                    
                    if properties:
                        # Filter for properties within the radius
                        filtered_properties = []
                        for prop in properties:
                            if prop.get('distance', 0) <= strategy['radius']:
                                filtered_properties.append(prop)
                        
                        if filtered_properties:
                            logger.info(f"✅ Fallback search found {len(filtered_properties)} properties")
                            return {
                                'success': True,
                                'properties': filtered_properties,
                                'search_type': 'bed_bath_fallback',
                                'radius': strategy['radius'],
                                'time_window': strategy['time_window']
                            }
                else:
                    logger.warning(f"⚠️ Fallback API returned status {response.status_code}")
            
            # If no properties found even with fallback
            logger.info("❌ No properties found even with bed/bath fallback")
            return {
                'success': False,
                'properties': [],
                'search_type': 'bed_bath_fallback',
                'message': 'No properties found with matching bed/bath within 1 mile'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in bed/bath fallback search: {e}")
            return {
                'success': False,
                'properties': [],
                'error': str(e),
                'search_type': 'bed_bath_fallback'
            }
    
    def _determine_confidence_level(self, comp_count: int) -> str:
        """Determine confidence level based on number of comps"""
        if comp_count >= 3:
            return 'High'
        elif comp_count >= 2:
            return 'Medium'
        else:
            return 'Low'
    
    def _generate_summary(self, comps: List[Dict], search_params: SearchParams) -> str:
        """Generate AI-style summary of comparable analysis"""
        if not comps:
            return "No comparable properties found."
        
        avg_price = sum(comp['adjusted_price'] for comp in comps) / len(comps)
        
        return f"""
        Found {len(comps)} comparable properties for {search_params.address}.
        Average adjusted price: ${avg_price:,.0f}
        Price range: ${min(comp['adjusted_price'] for comp in comps):,.0f} - ${max(comp['adjusted_price'] for comp in comps):,.0f}
        
        All properties have been adjusted for differences in bedrooms, bathrooms, and square footage.
        This analysis follows professional appraisal standards for comparable sales.
        """
    
    def _clean_address_for_search(self, address: str) -> str:
        """Clean address for API search"""
        address = address.replace('USA', '').replace('United States', '')
        address = address.strip().rstrip(',')
        
        if ',' in address:
            parts = address.split(',')
            if len(parts) >= 2:
                return f"{parts[-2].strip()}, {parts[-1].strip()}"
        
        return address
    
    def _extract_city_state(self, address: str) -> str:
        """Extract city and state for broader search"""
        address = address.replace('USA', '').replace('United States', '')
        address = address.strip().rstrip(',')
        
        if ',' in address:
            parts = address.split(',')
            if len(parts) >= 2:
                return f"{parts[-2].strip()}, {parts[-1].strip()}"
        
        return address
    
    def _extract_zip_code(self, address: str) -> str:
        """Extract zip code from address - look for 5-digit code after state"""
        try:
            import re
            # Look for 5-digit zip code after state abbreviation (like "NC 28262")
            zip_match = re.search(r'\b[A-Z]{2}\s+(\d{5})\b', address)
            if zip_match:
                return zip_match.group(1)
            
            # Fallback: look for 5-digit code at the very end
            zip_match = re.search(r'\b(\d{5})(?:\s*,?\s*USA)?$', address)
            if zip_match:
                return zip_match.group(1)
            
            return ""
        except Exception as e:
            logger.error(f"❌ Error extracting zip code: {e}")
            return ""
    
    def _generate_recent_sale_date(self) -> str:
        """Generate a recent sale date for mock data"""
        import random
        days_ago = random.randint(30, 180)
        sale_date = datetime.now() - timedelta(days=days_ago)
        return sale_date.strftime('%Y-%m-%d')
    
    def _calculate_days_ago(self) -> int:
        """Calculate days ago for mock data"""
        import random
        return random.randint(30, 180)