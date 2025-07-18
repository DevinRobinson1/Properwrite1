"""
Smart Comps 2.0 - Rule-Adaptive Comparable Search Service
Implements progressive rule relaxation with scoring system
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchParams:
    """Parameters for comparable search"""
    address: str
    beds: int
    baths: float
    sqft: int
    lat: Optional[float] = None
    lng: Optional[float] = None
    zip_code: Optional[str] = None
    property_type: str = 'SingleFamily'
    want_count: int = 10

@dataclass
class CompProperty:
    """Comparable property data structure"""
    mls_id: str
    address: str
    price: float
    beds: int
    baths: float
    sqft: int
    close_date: str
    property_type: str
    zip_code: str
    lat: float
    lng: float
    score: float = 0.0
    distance_mi: float = 0.0
    rules_broken: List[str] = None
    accuracy_badge: str = 'green'  # green, yellow, red
    
    def __post_init__(self):
        if self.rules_broken is None:
            self.rules_broken = []

class SmartCompsService:
    """Smart Comps 2.0 Service with Rule-Adaptive Search"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Rule definitions with penalties
        self.rules = {
            'zip_code': {
                'penalty': 30,
                'description': 'Same ZIP code'
            },
            'property_type': {
                'penalty': 30,
                'description': 'Same property type'
            },
            'sqft_range': {
                'penalty': 20,
                'description': 'Square footage within ±20%'
            },
            'recent_sale': {
                'penalty': 15,
                'description': 'Sold within 6 months'
            },
            'distance': {
                'penalty': 5,
                'description': 'Distance penalty (max 5 pts)'
            }
        }
        
        # Rule relaxation sequence
        self.relaxation_sequence = [
            'recent_sale',    # First relax: allow 6-12 month sales
            'sqft_range',     # Second: widen to ±30% sqft
            'zip_code',       # Third: allow adjacent ZIP codes
            'property_type'   # Fourth: allow similar property types
        ]
    
    def search_comparable_properties(self, subject_address: str, subject_beds: int, 
                                   subject_baths: float, subject_sqft: int,
                                   subject_lat: float = None, subject_lng: float = None,
                                   **kwargs) -> Dict[str, Any]:
        """
        Main entry point for Smart Comps 2.0 search
        
        Args:
            subject_address: Subject property address
            subject_beds: Number of bedrooms
            subject_baths: Number of bathrooms
            subject_sqft: Square footage
            subject_lat: Latitude
            subject_lng: Longitude
            **kwargs: Additional search parameters
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Extract ZIP code from address
            zip_code = self._extract_zip_code(subject_address)
            
            # Create search parameters
            search_params = SearchParams(
                address=subject_address,
                beds=subject_beds,
                baths=subject_baths,
                sqft=subject_sqft,
                lat=subject_lat,
                lng=subject_lng,
                zip_code=zip_code
            )
            
            self.logger.info(f"🔍 Starting Smart Comps 2.0 search for: {subject_address}")
            self.logger.info(f"📏 Subject specs: {subject_beds} bed, {subject_baths} bath, {subject_sqft} sqft")
            
            # Perform adaptive search
            comps = self._find_comps_adaptive(search_params)
            
            # Calculate overall accuracy score
            overall_score = self._calculate_overall_score(comps)
            
            # Calculate recommended ARV
            recommended_arv = self._calculate_recommended_arv(comps)
            
            # Create response
            result = {
                'success': True,
                'comps': [self._format_comp_for_response(comp) for comp in comps],
                'found_count': len(comps),
                'overall_score': overall_score,
                'recommended_arv': recommended_arv,
                'search_metadata': {
                    'address': subject_address,
                    'beds': subject_beds,
                    'baths': subject_baths,
                    'sqft': subject_sqft,
                    'zip_code': zip_code,
                    'algorithm': 'Smart Comps 2.0'
                },
                'analysis': {
                    'summary': f"Found {len(comps)} comparable properties with {overall_score:.1f}% average accuracy",
                    'recommended_arv': recommended_arv,
                    'confidence_level': self._get_confidence_level(overall_score)
                }
            }
            
            self.logger.info(f"✅ Smart Comps 2.0 search completed: {len(comps)} properties, {overall_score:.1f}% accuracy")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Smart Comps 2.0 search error: {e}")
            return {
                'success': False,
                'error': str(e),
                'comps': [],
                'found_count': 0
            }
    
    def _find_comps_adaptive(self, search_params: SearchParams) -> List[CompProperty]:
        """
        Adaptive search with progressive rule relaxation
        """
        # Get property dataset for the area
        dataset = self._get_property_dataset(search_params)
        
        if not dataset:
            self.logger.warning("No property dataset available for search")
            return []
        
        comps = []
        relax_level = 0
        
        # Progressive rule relaxation
        while len(comps) < search_params.want_count and relax_level <= len(self.relaxation_sequence):
            self.logger.info(f"🔄 Search iteration {relax_level + 1}: looking for {search_params.want_count - len(comps)} more properties")
            
            # Get properties that pass current relaxation level
            candidates = []
            for prop in dataset:
                if self._passes_rules(prop, search_params, relax_level):
                    scored_prop = self._score_property(prop, search_params, relax_level)
                    candidates.append(scored_prop)
            
            # Sort by score (descending) and distance (ascending)
            candidates.sort(key=lambda x: (-x.score, x.distance_mi))
            
            # Take best candidates up to our want count
            remaining_needed = search_params.want_count - len(comps)
            new_comps = candidates[:remaining_needed]
            comps.extend(new_comps)
            
            self.logger.info(f"Found {len(new_comps)} properties at relax level {relax_level}")
            
            # If we have enough comps, break
            if len(comps) >= search_params.want_count:
                break
                
            relax_level += 1
        
        return comps[:search_params.want_count]
    
    def _passes_rules(self, prop: Dict, search_params: SearchParams, relax_level: int) -> bool:
        """
        Check if property passes rules at current relaxation level
        """
        # Rules that are still enforced at this level
        enforced_rules = set(['zip_code', 'property_type', 'sqft_range', 'recent_sale'])
        
        # Remove relaxed rules
        for i in range(relax_level):
            if i < len(self.relaxation_sequence):
                rule_to_relax = self.relaxation_sequence[i]
                enforced_rules.discard(rule_to_relax)
        
        # Check each enforced rule
        if 'zip_code' in enforced_rules:
            if not self._check_zip_code_rule(prop, search_params):
                return False
        
        if 'property_type' in enforced_rules:
            if not self._check_property_type_rule(prop, search_params):
                return False
        
        if 'sqft_range' in enforced_rules:
            if not self._check_sqft_rule(prop, search_params, strict=True):
                return False
        
        if 'recent_sale' in enforced_rules:
            if not self._check_date_rule(prop, search_params, strict=True):
                return False
        
        return True
    
    def _score_property(self, prop: Dict, search_params: SearchParams, relax_level: int) -> CompProperty:
        """
        Score property based on broken rules and distance
        """
        # Convert to CompProperty object
        comp = CompProperty(
            mls_id=prop.get('mls_id', f"prop_{hash(prop.get('address', ''))}"),
            address=prop.get('address', ''),
            price=float(prop.get('price', 0)),
            beds=int(prop.get('beds', 0)),
            baths=float(prop.get('baths', 0)),
            sqft=int(prop.get('sqft', 0)),
            close_date=prop.get('close_date', ''),
            property_type=prop.get('property_type', 'SingleFamily'),
            zip_code=prop.get('zip_code', ''),
            lat=float(prop.get('lat', 0)),
            lng=float(prop.get('lng', 0))
        )
        
        # Calculate distance
        if search_params.lat and search_params.lng:
            comp.distance_mi = self._calculate_distance(
                search_params.lat, search_params.lng,
                comp.lat, comp.lng
            )
        
        # Start with perfect score
        score = 100.0
        broken_rules = []
        
        # Check each rule and apply penalties
        if not self._check_zip_code_rule(prop, search_params):
            score -= self.rules['zip_code']['penalty']
            broken_rules.append('zip_code')
        
        if not self._check_property_type_rule(prop, search_params):
            score -= self.rules['property_type']['penalty']
            broken_rules.append('property_type')
        
        if not self._check_sqft_rule(prop, search_params, strict=False):
            score -= self.rules['sqft_range']['penalty']
            broken_rules.append('sqft_range')
        
        if not self._check_date_rule(prop, search_params, strict=False):
            score -= self.rules['recent_sale']['penalty']
            broken_rules.append('recent_sale')
        
        # Distance penalty (max 5 points)
        distance_penalty = min(5, int(comp.distance_mi / 0.5))
        score -= distance_penalty
        
        # Set final score and metadata
        comp.score = max(0, score)  # Don't go below 0
        comp.rules_broken = broken_rules
        comp.accuracy_badge = self._get_accuracy_badge(comp.score)
        
        return comp
    
    def _check_zip_code_rule(self, prop: Dict, search_params: SearchParams) -> bool:
        """Check if property is in same ZIP code"""
        if not search_params.zip_code:
            return True
        return prop.get('zip_code') == search_params.zip_code
    
    def _check_property_type_rule(self, prop: Dict, search_params: SearchParams) -> bool:
        """Check if property is same type"""
        return prop.get('property_type', 'SingleFamily') == search_params.property_type
    
    def _check_sqft_rule(self, prop: Dict, search_params: SearchParams, strict: bool = True) -> bool:
        """Check if property square footage is within range"""
        prop_sqft = int(prop.get('sqft', 0))
        if prop_sqft == 0:
            return False
        
        # Strict: ±20%, Relaxed: ±30%
        tolerance = 0.2 if strict else 0.3
        min_sqft = search_params.sqft * (1 - tolerance)
        max_sqft = search_params.sqft * (1 + tolerance)
        
        return min_sqft <= prop_sqft <= max_sqft
    
    def _check_date_rule(self, prop: Dict, search_params: SearchParams, strict: bool = True) -> bool:
        """Check if property was sold recently"""
        try:
            close_date = datetime.strptime(prop.get('close_date', ''), '%Y-%m-%d')
            today = datetime.now()
            
            # Strict: 6 months, Relaxed: 12 months
            months_back = 6 if strict else 12
            cutoff_date = today - timedelta(days=months_back * 30)
            
            return close_date >= cutoff_date
        except:
            return False
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        if not all([lat1, lng1, lat2, lng2]):
            return 0.0
        
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in miles
        return 3959 * c
    
    def _get_property_dataset(self, search_params: SearchParams) -> List[Dict]:
        """
        Get property dataset for the search area
        This should be replaced with actual API calls to property data providers
        """
        # For now, return mock data - in production, this would call external APIs
        # like Zillow, Redfin, etc.
        
        # Try to get data from existing services
        try:
            from simple_comps_service import SimpleCompsService
            service = SimpleCompsService()
            result = service.search_comparable_properties(
                search_params.address,
                search_params.beds,
                search_params.baths,
                search_params.sqft
            )
            
            if result.get('success') and result.get('comps'):
                # Convert to our format
                dataset = []
                for comp in result['comps']:
                    dataset.append({
                        'mls_id': comp.get('mls_id', ''),
                        'address': comp.get('address', ''),
                        'price': comp.get('price', 0),
                        'beds': comp.get('bedrooms', 0),
                        'baths': comp.get('bathrooms', 0),
                        'sqft': comp.get('square_footage', 0),
                        'close_date': comp.get('date_sold', '2024-01-01'),
                        'property_type': 'SingleFamily',
                        'zip_code': self._extract_zip_code(comp.get('address', '')),
                        'lat': comp.get('latitude', 0),
                        'lng': comp.get('longitude', 0)
                    })
                return dataset
        except Exception as e:
            self.logger.error(f"Error getting property dataset: {e}")
        
        return []
    
    def _extract_zip_code(self, address: str) -> str:
        """Extract ZIP code from address"""
        if not address:
            return ''
        
        # Look for 5-digit ZIP code
        zip_match = re.search(r'\b(\d{5})\b', address)
        return zip_match.group(1) if zip_match else ''
    
    def _calculate_overall_score(self, comps: List[CompProperty]) -> float:
        """Calculate overall accuracy score"""
        if not comps:
            return 0.0
        return sum(comp.score for comp in comps) / len(comps)
    
    def _calculate_recommended_arv(self, comps: List[CompProperty]) -> float:
        """Calculate recommended ARV based on comparable properties"""
        if not comps:
            return 0.0
        
        # Weight by score and recency
        weighted_prices = []
        total_weight = 0
        
        for comp in comps:
            # Higher score = higher weight
            score_weight = comp.score / 100.0
            
            # More recent sales get higher weight
            try:
                days_ago = (datetime.now() - datetime.strptime(comp.close_date, '%Y-%m-%d')).days
                recency_weight = max(0.1, 1.0 - (days_ago / 365.0))
            except:
                recency_weight = 0.5
            
            weight = score_weight * recency_weight
            weighted_prices.append(comp.price * weight)
            total_weight += weight
        
        if total_weight == 0:
            return sum(comp.price for comp in comps) / len(comps)
        
        return sum(weighted_prices) / total_weight
    
    def _get_accuracy_badge(self, score: float) -> str:
        """Get accuracy badge color based on score"""
        if score >= 90:
            return 'green'
        elif score >= 70:
            return 'yellow'
        else:
            return 'red'
    
    def _get_confidence_level(self, score: float) -> str:
        """Get confidence level description"""
        if score >= 90:
            return 'High Confidence'
        elif score >= 70:
            return 'Medium Confidence'
        else:
            return 'Low Confidence'
    
    def _format_comp_for_response(self, comp: CompProperty) -> Dict[str, Any]:
        """Format comparable property for API response"""
        return {
            'mls_id': comp.mls_id,
            'address': comp.address,
            'price': comp.price,
            'bedrooms': comp.beds,
            'bathrooms': comp.baths,
            'square_footage': comp.sqft,
            'date_sold': comp.close_date,
            'property_type': comp.property_type,
            'zip_code': comp.zip_code,
            'latitude': comp.lat,
            'longitude': comp.lng,
            'distance_miles': round(comp.distance_mi, 2),
            'accuracy_score': round(comp.score, 1),
            'accuracy_badge': comp.accuracy_badge,
            'rules_broken': comp.rules_broken,
            'rules_broken_descriptions': [
                self.rules[rule]['description'] for rule in comp.rules_broken
            ]
        }

# Global instance
smart_comps_service = SmartCompsService()