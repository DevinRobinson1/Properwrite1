"""
Enhanced Comparable Properties Service
Professional real estate appraisal standards with multiple data sources and robust fallback mechanisms
"""
import os
import logging
import requests
import time
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt
from dataclasses import dataclass, asdict
# Property caching can be added later if needed

logger = logging.getLogger(__name__)

@dataclass
class ComparableProperty:
    """Standardized comparable property data structure"""
    address: str
    street_address: str
    city: str
    state: str
    zip_code: str
    price: float
    bedrooms: int
    bathrooms: float
    square_footage: int
    lot_size: Optional[float]
    year_built: Optional[int]
    sale_date: str
    days_on_market: int
    property_type: str
    latitude: Optional[float]
    longitude: Optional[float]
    distance: Optional[float]
    source: str
    confidence_score: float
    data_quality: str  # 'excellent', 'good', 'fair', 'poor'
    
    def to_dict(self) -> Dict:
        return asdict(self)

class EnhancedCompsService:
    """Enhanced comparable properties service with multiple data sources"""
    
    def __init__(self):
        self.rapidapi_key = os.environ.get('RAPIDAPI_KEY')
        self.rentcast_api_key = os.environ.get('RENTCAST_API_KEY')
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        # Professional appraisal standards
        self.appraisal_standards = {
            'max_distance_miles': 1.0,
            'preferred_distance_miles': 0.5,
            'max_sale_age_days': 180,
            'preferred_sale_age_days': 90,
            'bedroom_variance': 1,
            'bathroom_variance': 1,
            'sqft_variance_percent': 20,
            'minimum_comps_required': 3,
            'preferred_comps_count': 5,
            'price_per_sqft_variance': 0.30  # 30% variance threshold
        }
        
        # Price adjustments per NAR standards
        self.adjustments = {
            'bedroom_diff': 15000,
            'bathroom_diff': 12500,
            'sqft_diff_per_sqft': 100,
            'age_diff_per_year': 500,
            'lot_size_diff_per_sqft': 2,
            'distance_penalty_per_mile': 0.02  # 2% per mile
        }
        
        # API configurations
        self.apis = {
            'zillow': {
                'headers': {
                    "X-RapidAPI-Key": self.rapidapi_key,
                    "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
                },
                'rate_limit_delay': 1,
                'max_retries': 3
            },
            'rentcast': {
                'headers': {
                    "X-Api-Key": self.rentcast_api_key,
                    "accept": "application/json"
                },
                'rate_limit_delay': 2,
                'max_retries': 2
            }
        }
    
    def search_comparable_sales(self, address: str, beds: int, baths: float, sqft: int,
                              lat: float = None, lng: float = None) -> Dict:
        """
        Search for comparable SALES properties using multiple data sources
        Returns only sold properties, not rentals
        """
        logger.info(f"🔍 Starting comprehensive comps search for {address}")
        
        # Progressive search strategy - more permissive
        search_strategies = [
            {'days': 180, 'radius': 1.0, 'bed_variance': 1, 'sqft_variance': 25},
            {'days': 365, 'radius': 1.5, 'bed_variance': 2, 'sqft_variance': 30},
            {'days': 545, 'radius': 2.0, 'bed_variance': 2, 'sqft_variance': 35},
            {'days': 730, 'radius': 3.0, 'bed_variance': 3, 'sqft_variance': 40}
        ]
        
        all_comps = []
        search_summary = []
        
        for i, strategy in enumerate(search_strategies):
            logger.info(f"📊 Search strategy {i+1}: {strategy}")
            
            # Try multiple data sources for each strategy
            strategy_comps = []
            
            # 1. Zillow Sales Data (Primary)
            zillow_results = self._search_zillow_sales(
                address, beds, baths, sqft, lat, lng, strategy
            )
            if zillow_results:
                strategy_comps.extend(zillow_results)
                logger.info(f"✅ Zillow found {len(zillow_results)} comps")
            
            # 2. Try broader location search if no results
            if not strategy_comps and lat and lng:
                broader_results = self._search_by_coordinates(
                    lat, lng, beds, baths, sqft, strategy
                )
                if broader_results:
                    strategy_comps.extend(broader_results)
                    logger.info(f"✅ Coordinate search found {len(broader_results)} comps")
            
            # 3. RentCast Sales Data (Secondary)
            rentcast_results = self._search_rentcast_sales(
                address, beds, baths, sqft, lat, lng, strategy
            )
            if rentcast_results:
                strategy_comps.extend(rentcast_results)
                logger.info(f"✅ RentCast found {len(rentcast_results)} comps")
            
            # Remove duplicates and rank by quality
            strategy_comps = self._deduplicate_and_rank(strategy_comps, lat, lng)
            all_comps.extend(strategy_comps)
            
            search_summary.append({
                'strategy': i+1,
                'parameters': strategy,
                'results_found': len(strategy_comps),
                'total_so_far': len(all_comps)
            })
            
            # Stop if we have enough high-quality comps
            if len(all_comps) >= 5:
                logger.info(f"🎯 Found sufficient comps ({len(all_comps)}), stopping search")
                break
        
        # Final ranking and filtering
        final_comps = self._final_ranking_and_filtering(all_comps, beds, baths, sqft, lat, lng)
        
        if len(final_comps) < 3:
            logger.warning(f"⚠️ Only found {len(final_comps)} comps, below minimum threshold")
            return {
                'error': 'Insufficient comparable properties found',
                'found_count': len(final_comps),
                'minimum_required': 3,
                'comps': [comp.to_dict() for comp in final_comps],
                'search_summary': search_summary,
                'suggestions': self._get_search_suggestions(address, final_comps)
            }
        
        logger.info(f"✅ Successfully found {len(final_comps)} quality comparable properties")
        return {
            'success': True,
            'found_count': len(final_comps),
            'comps': [comp.to_dict() for comp in final_comps],
            'search_summary': search_summary,
            'quality_metrics': self._calculate_quality_metrics(final_comps)
        }
    
    def _search_zillow_sales(self, address: str, beds: int, baths: float, sqft: int,
                           lat: float, lng: float, strategy: Dict) -> List[ComparableProperty]:
        """Search Zillow for sold properties only"""
        if not self.rapidapi_key:
            return []
        
        try:
            url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
            
            # Calculate search parameters - make them more permissive
            min_beds = max(1, beds - 2)  # More permissive
            max_beds = beds + 2
            min_baths = max(1, baths - 1)
            max_baths = baths + 2
            sqft_var = int(sqft * 30 / 100)  # 30% variance
            min_sqft = max(500, sqft - sqft_var)
            max_sqft = sqft + sqft_var
            
            params = {
                "location": address,
                "status_type": "RecentlySold",  # SOLD ONLY
                "home_type": "Houses",
                "minBeds": min_beds,
                "maxBeds": max_beds,
                "minBaths": min_baths,
                "maxBaths": max_baths,
                "minSqft": min_sqft,
                "maxSqft": max_sqft,
                "daysOnZillow": strategy['days']
            }
            
            logger.info(f"🏠 Zillow search: {min_beds}-{max_beds}BR, {min_baths}-{max_baths}BA, {min_sqft}-{max_sqft}sqft, {strategy['days']} days")
            
            response = requests.get(url, headers=self.apis['zillow']['headers'], params=params)
            
            if response.status_code == 429:
                logger.warning("⏰ Zillow rate limit hit, implementing delay...")
                time.sleep(self.apis['zillow']['rate_limit_delay'])
                return []
            
            if response.status_code != 200:
                logger.error(f"❌ Zillow API error: {response.status_code}")
                return []
            
            data = response.json()
            logger.info(f"📊 Zillow API response: {data}")
            
            # Handle different response formats
            properties = []
            if isinstance(data, dict):
                if 'zpid' in data:
                    # Single property response - this is the subject property, not comps
                    logger.info("📍 Zillow returned subject property only, trying broader search")
                    return []
                elif 'props' in data:
                    properties = data['props']
                elif 'results' in data:
                    properties = data['results']
            elif isinstance(data, list):
                properties = data
            
            logger.info(f"📊 Found {len(properties)} properties from Zillow")
            
            # Convert to standardized format
            comps = []
            for prop in properties:
                comp = self._convert_zillow_to_standard(prop, lat, lng)
                if comp and self._validate_comp_quality(comp):
                    comps.append(comp)
            
            return comps
            
        except Exception as e:
            logger.error(f"❌ Zillow search error: {str(e)}")
            return []
    
    def _search_rentcast_sales(self, address: str, beds: int, baths: float, sqft: int,
                             lat: float, lng: float, strategy: Dict) -> List[ComparableProperty]:
        """Search RentCast for sold properties (using the correct endpoint)"""
        if not self.rentcast_api_key:
            return []
        
        try:
            # RentCast properties endpoint with sales filter
            url = "https://api.rentcast.io/v1/properties"
            
            # Extract city and state from address
            parts = address.split(',')
            city = parts[1].strip() if len(parts) > 1 else ""
            state = parts[2].strip().split()[0] if len(parts) > 2 else ""
            
            params = {
                "city": city,
                "state": state,
                "bedrooms": f"{max(1, beds-1)},{beds+1}",
                "bathrooms": f"{max(1, int(baths-1))},{int(baths+2)}",
                "squareFootage": f"{max(500, sqft-500)},{sqft+500}",
                "propertyType": "Single Family",
                "status": "sold",
                "limit": 20
            }
            
            logger.info(f"🏘️ RentCast sales search: {city}, {state}")
            
            response = requests.get(url, headers=self.apis['rentcast']['headers'], params=params)
            
            if response.status_code == 429:
                logger.warning("⏰ RentCast rate limit hit, implementing delay...")
                time.sleep(self.apis['rentcast']['rate_limit_delay'])
                return []
            
            if response.status_code != 200:
                logger.warning(f"⚠️ RentCast API unavailable: {response.status_code}")
                return []
            
            data = response.json()
            properties = data.get('properties', [])
            
            # Convert to standardized format
            comps = []
            for prop in properties:
                comp = self._convert_rentcast_to_standard(prop, lat, lng)
                if comp and self._validate_comp_quality(comp):
                    comps.append(comp)
            
            return comps
            
        except Exception as e:
            logger.warning(f"⚠️ RentCast search unavailable: {str(e)}")
            return []
    
    def _search_by_coordinates(self, lat: float, lng: float, beds: int, baths: float, sqft: int, strategy: Dict) -> List[ComparableProperty]:
        """Search by coordinates with different location strings"""
        if not self.rapidapi_key:
            return []
        
        # Try different location formats
        location_variations = [
            f"{lat},{lng}",
            f"Kannapolis, NC",
            f"Charlotte, NC",  # Nearby major city
            f"Concord, NC",   # Nearby city
            f"NC"             # State-wide search
        ]
        
        for location in location_variations:
            try:
                url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
                
                # Very permissive search parameters
                min_beds = max(1, beds - 2)
                max_beds = beds + 3
                min_baths = max(1, baths - 1)
                max_baths = baths + 2
                sqft_var = int(sqft * 40 / 100)  # 40% variance
                min_sqft = max(500, sqft - sqft_var)
                max_sqft = sqft + sqft_var
                
                params = {
                    "location": location,
                    "status_type": "RecentlySold",
                    "home_type": "Houses",
                    "minBeds": min_beds,
                    "maxBeds": max_beds,
                    "minBaths": min_baths,
                    "maxBaths": max_baths,
                    "minSqft": min_sqft,
                    "maxSqft": max_sqft,
                    "daysOnZillow": strategy['days'],
                    "limit": 20
                }
                
                logger.info(f"🌐 Coordinate search: {location}")
                
                response = requests.get(url, headers=self.apis['zillow']['headers'], params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different response formats
                    properties = []
                    if isinstance(data, dict):
                        if 'props' in data:
                            properties = data['props']
                        elif 'results' in data:
                            properties = data['results']
                    elif isinstance(data, list):
                        properties = data
                    
                    if properties:
                        logger.info(f"📍 Found {len(properties)} properties for {location}")
                        
                        # Convert to standardized format
                        comps = []
                        for prop in properties:
                            comp = self._convert_zillow_to_standard(prop, lat, lng)
                            if comp and self._validate_comp_quality(comp):
                                comps.append(comp)
                        
                        if comps:
                            logger.info(f"✅ Coordinate search successful with {len(comps)} valid comps")
                            return comps
                        
                time.sleep(0.5)  # Small delay between requests
                
            except Exception as e:
                logger.warning(f"⚠️ Coordinate search error for {location}: {str(e)}")
                continue
        
        return []
    
    def _convert_zillow_to_standard(self, prop: Dict, subject_lat: float, subject_lng: float) -> Optional[ComparableProperty]:
        """Convert Zillow data to standardized format"""
        try:
            # Extract address components
            address = prop.get('address', '') or prop.get('streetAddress', '')
            city = prop.get('city', '')
            state = prop.get('state', '')
            zip_code = prop.get('zipcode', '') or prop.get('postalCode', '')
            
            # Price (must be sold price)
            price = prop.get('price', 0) or prop.get('soldPrice', 0)
            if not price or price <= 0:
                return None
            
            # Property details with safe conversion
            beds = prop.get('bedrooms', 0) or prop.get('beds', 0) or 0
            baths = prop.get('bathrooms', 0) or prop.get('baths', 0) or 0
            sqft = prop.get('livingArea', 0) or prop.get('sqft', 0) or 0
            lot_size = prop.get('lotSize', 0) or 0
            year_built = prop.get('yearBuilt', 0) or 0
            days_on_market = prop.get('daysOnMarket', 0) or 0
            
            # Location
            lat = prop.get('latitude', 0) or 0
            lng = prop.get('longitude', 0) or 0
            
            # Calculate distance if we have coordinates
            distance = None
            if lat and lng and subject_lat and subject_lng:
                distance = self._calculate_distance(subject_lat, subject_lng, lat, lng)
            
            # Sale date
            sale_date = prop.get('dateSold', '') or prop.get('listingDateTime', '') or ''
            
            return ComparableProperty(
                address=f"{address}, {city}, {state} {zip_code}".strip(),
                street_address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                price=float(price),
                bedrooms=int(beds) if beds and beds > 0 else 0,
                bathrooms=float(baths) if baths and baths > 0 else 0,
                square_footage=int(sqft) if sqft and sqft > 0 else 0,
                lot_size=float(lot_size) if lot_size and lot_size > 0 else None,
                year_built=int(year_built) if year_built and year_built > 0 else None,
                sale_date=sale_date,
                days_on_market=int(days_on_market) if days_on_market and days_on_market >= 0 else 0,
                property_type=prop.get('propertyType', 'Single Family'),
                latitude=float(lat) if lat and lat != 0 else None,
                longitude=float(lng) if lng and lng != 0 else None,
                distance=distance,
                source='Zillow',
                confidence_score=self._calculate_confidence_score(prop, 'zillow'),
                data_quality=self._assess_data_quality(prop)
            )
            
        except Exception as e:
            logger.error(f"❌ Error converting Zillow data: {str(e)}")
            return None
    
    def _convert_rentcast_to_standard(self, prop: Dict, subject_lat: float, subject_lng: float) -> Optional[ComparableProperty]:
        """Convert RentCast data to standardized format"""
        try:
            # Extract address components
            address_line1 = prop.get('addressLine1', '')
            city = prop.get('city', '')
            state = prop.get('state', '')
            zip_code = prop.get('zipCode', '')
            
            # Price (must be sales price, not rental)
            price = prop.get('lastSalePrice', 0) or prop.get('price', 0)
            if not price or price <= 0:
                return None
            
            # Property details
            beds = prop.get('bedrooms', 0)
            baths = prop.get('bathrooms', 0)
            sqft = prop.get('squareFootage', 0)
            
            # Location
            lat = prop.get('latitude', 0)
            lng = prop.get('longitude', 0)
            
            # Calculate distance
            distance = None
            if lat and lng and subject_lat and subject_lng:
                distance = self._calculate_distance(subject_lat, subject_lng, lat, lng)
            
            # Sale date
            sale_date = prop.get('lastSaleDate', '')
            
            return ComparableProperty(
                address=f"{address_line1}, {city}, {state} {zip_code}".strip(),
                street_address=address_line1,
                city=city,
                state=state,
                zip_code=zip_code,
                price=float(price),
                bedrooms=int(beds),
                bathrooms=float(baths),
                square_footage=int(sqft) if sqft else 0,
                lot_size=prop.get('lotSize', 0),
                year_built=prop.get('yearBuilt', 0),
                sale_date=sale_date,
                days_on_market=prop.get('daysOnMarket', 0),
                property_type=prop.get('propertyType', 'Single Family'),
                latitude=lat,
                longitude=lng,
                distance=distance,
                source='RentCast',
                confidence_score=self._calculate_confidence_score(prop, 'rentcast'),
                data_quality=self._assess_data_quality(prop)
            )
            
        except Exception as e:
            logger.error(f"❌ Error converting RentCast data: {str(e)}")
            return None
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in miles"""
        R = 3959  # Earth radius in miles
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    def _validate_comp_quality(self, comp: ComparableProperty) -> bool:
        """Validate if a comparable property meets quality standards"""
        if not comp:
            return False
        
        # Basic data validation with None checks
        if comp.price is None or comp.price <= 0:
            return False
        
        if comp.bedrooms is None or comp.bedrooms <= 0:
            return False
        
        if comp.bathrooms is None or comp.bathrooms <= 0:
            return False
        
        # Distance validation
        if comp.distance and comp.distance > self.appraisal_standards['max_distance_miles']:
            return False
        
        # Data quality validation
        if comp.data_quality == 'poor':
            return False
        
        return True
    
    def _calculate_confidence_score(self, prop: Dict, source: str) -> float:
        """Calculate confidence score for a property"""
        score = 0.5  # Base score
        
        # Data completeness
        if prop.get('price', 0) > 0:
            score += 0.1
        if prop.get('bedrooms', 0) > 0:
            score += 0.1
        if prop.get('bathrooms', 0) > 0:
            score += 0.1
        if prop.get('livingArea', 0) or prop.get('squareFootage', 0):
            score += 0.1
        if prop.get('yearBuilt', 0):
            score += 0.05
        if prop.get('dateSold') or prop.get('lastSaleDate'):
            score += 0.05
        
        # Source reliability
        if source == 'zillow':
            score += 0.1
        elif source == 'rentcast':
            score += 0.08
        
        return min(1.0, score)
    
    def _assess_data_quality(self, prop: Dict) -> str:
        """Assess overall data quality"""
        required_fields = ['price', 'bedrooms', 'bathrooms']
        optional_fields = ['livingArea', 'squareFootage', 'yearBuilt', 'dateSold', 'lastSaleDate']
        
        required_count = sum(1 for field in required_fields if prop.get(field))
        optional_count = sum(1 for field in optional_fields if prop.get(field))
        
        if required_count == len(required_fields) and optional_count >= 3:
            return 'excellent'
        elif required_count == len(required_fields) and optional_count >= 2:
            return 'good'
        elif required_count == len(required_fields):
            return 'fair'
        else:
            return 'poor'
    
    def _deduplicate_and_rank(self, comps: List[ComparableProperty], lat: float, lng: float) -> List[ComparableProperty]:
        """Remove duplicates and rank by quality"""
        if not comps:
            return []
        
        # Remove duplicates by address
        unique_comps = {}
        for comp in comps:
            key = f"{comp.street_address.lower()}{comp.city.lower()}{comp.state.lower()}"
            if key not in unique_comps or comp.confidence_score > unique_comps[key].confidence_score:
                unique_comps[key] = comp
        
        # Sort by combined score (confidence + proximity + recency)
        sorted_comps = sorted(unique_comps.values(), key=lambda x: (
            x.confidence_score * 0.4 +
            (1 - (x.distance or 0)) * 0.3 +  # Closer is better
            0.3  # Recency would need date parsing
        ), reverse=True)
        
        return sorted_comps
    
    def _final_ranking_and_filtering(self, comps: List[ComparableProperty], beds: int, baths: float, sqft: int, lat: float, lng: float) -> List[ComparableProperty]:
        """Final ranking and filtering of all comparable properties"""
        if not comps:
            return []
        
        # Apply strict filtering
        filtered = []
        for comp in comps:
            # Distance filter
            if comp.distance and comp.distance > self.appraisal_standards['max_distance_miles']:
                continue
            
            # Bedroom variance filter
            if abs(comp.bedrooms - beds) > self.appraisal_standards['bedroom_variance']:
                continue
            
            # Bathroom variance filter
            if abs(comp.bathrooms - baths) > self.appraisal_standards['bathroom_variance']:
                continue
            
            # Square footage variance filter
            if comp.square_footage > 0 and sqft > 0:
                variance = abs(comp.square_footage - sqft) / sqft
                if variance > self.appraisal_standards['sqft_variance_percent'] / 100:
                    continue
            
            filtered.append(comp)
        
        # Sort by comprehensive ranking
        return sorted(filtered, key=lambda x: (
            x.confidence_score * 0.3 +
            (1 - (x.distance or 0.5)) * 0.2 +
            (1 if x.data_quality == 'excellent' else 0.8 if x.data_quality == 'good' else 0.6) * 0.2 +
            (1 if x.source == 'Zillow' else 0.9) * 0.1 +
            (1 if abs(x.bedrooms - beds) == 0 else 0.8) * 0.1 +
            (1 if abs(x.bathrooms - baths) <= 0.5 else 0.8) * 0.1
        ), reverse=True)[:8]  # Top 8 comps
    
    def _calculate_quality_metrics(self, comps: List[ComparableProperty]) -> Dict:
        """Calculate quality metrics for the comp set"""
        if not comps:
            return {}
        
        return {
            'total_comps': len(comps),
            'avg_confidence': sum(c.confidence_score for c in comps) / len(comps),
            'avg_distance': sum(c.distance or 0 for c in comps) / len(comps),
            'data_quality_distribution': {
                'excellent': sum(1 for c in comps if c.data_quality == 'excellent'),
                'good': sum(1 for c in comps if c.data_quality == 'good'),
                'fair': sum(1 for c in comps if c.data_quality == 'fair')
            },
            'source_distribution': {
                'Zillow': sum(1 for c in comps if c.source == 'Zillow'),
                'RentCast': sum(1 for c in comps if c.source == 'RentCast')
            }
        }
    
    def _get_search_suggestions(self, address: str, found_comps: List[ComparableProperty]) -> List[str]:
        """Get suggestions for improving search results"""
        suggestions = []
        
        if len(found_comps) == 0:
            suggestions.extend([
                "Verify the address spelling and format",
                "Check if this is new construction or a very unique property",
                "Try searching a nearby major street address",
                "Consider expanding to a wider geographic area"
            ])
        elif len(found_comps) < 3:
            suggestions.extend([
                "Consider expanding the search radius to 1-2 miles",
                "Extend the time period to 12 months for more results",
                "Include slightly different bedroom/bathroom counts",
                "Check for recently built neighborhoods with limited sales history"
            ])
        
        return suggestions

# Initialize service
enhanced_comps_service = EnhancedCompsService()