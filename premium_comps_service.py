"""
Premium Comparable Properties Service
Implements strict underwriting logic with enhanced UI and accurate distance calculations
"""
import os
import logging
import requests
import json
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

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
    image_url: Optional[str] = None
    property_type: str = "House"
    has_pool: bool = False
    has_hoa: bool = False
    is_waterfront: bool = False
    lot_size: Optional[float] = None
    year_built: Optional[int] = None

class PremiumCompsService:
    """Premium comparable properties service with strict underwriting rules"""
    
    def __init__(self):
        self.rapidapi_key = os.environ.get('RAPIDAPI_KEY')
        if not self.rapidapi_key:
            raise ValueError("RAPIDAPI_KEY not found in environment variables")
        
        self.headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
        }
        
        # Search strategy parameters
        self.time_windows = [90, 180, 365]  # Days
        self.distance_radii = [0.25, 0.5, 1.0]  # Miles
        self.sqft_tolerance = 500  # ± square feet
        
    def haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth in miles
        """
        # Convert latitude and longitude from degrees to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of Earth in miles
        r = 3956
        
        return c * r
    
    def search_comparable_properties(self, subject_address: str, subject_beds: int, 
                                   subject_baths: float, subject_sqft: int,
                                   subject_lat: float, subject_lng: float,
                                   subject_has_pool: bool = False,
                                   subject_has_hoa: bool = False,
                                   subject_is_waterfront: bool = False) -> Dict:
        """
        Search for comparable properties with strict underwriting criteria
        """
        logger.info(f"🔍 Starting premium comparable search for {subject_address}")
        logger.info(f"🎯 Subject specs: {subject_beds} bed, {subject_baths} bath, {subject_sqft} sqft")
        
        all_comps = []
        
        # Progressive search strategy
        for time_window in self.time_windows:
            for radius in self.distance_radii:
                if len(all_comps) >= 5:  # Stop when we have enough good comps
                    break
                
                logger.info(f"🔄 Searching within {radius} miles, {time_window} days...")
                
                # Search for sold properties
                comps = self._search_sold_properties(
                    subject_address, subject_beds, subject_baths, subject_sqft,
                    subject_lat, subject_lng, time_window, radius,
                    subject_has_pool, subject_has_hoa, subject_is_waterfront
                )
                
                # Add new comps that aren't duplicates
                for comp in comps:
                    if not self._is_duplicate(comp, all_comps):
                        all_comps.append(comp)
                
                # Stop expanding if we have enough good comps
                if len(all_comps) >= 3:
                    break
            
            if len(all_comps) >= 3:
                break
        
        # Sort by proximity first, then recency
        all_comps.sort(key=lambda x: (x.distance, x.days_ago))
        
        # Return top 5 comps
        final_comps = all_comps[:5]
        
        logger.info(f"✅ Found {len(final_comps)} comparable properties")
        
        # Calculate analysis
        analysis = self._calculate_analysis(final_comps, subject_sqft)
        
        return {
            'success': True,
            'comps': [self._format_comp_for_ui(comp) for comp in final_comps],
            'analysis': analysis,
            'found_count': len(final_comps),
            'search_radius': max([comp.distance for comp in final_comps]) if final_comps else 0,
            'search_timeframe': max([comp.days_ago for comp in final_comps]) if final_comps else 0
        }
    
    def _search_sold_properties(self, subject_address: str, subject_beds: int,
                               subject_baths: float, subject_sqft: int,
                               subject_lat: float, subject_lng: float,
                               time_window: int, radius: float,
                               subject_has_pool: bool, subject_has_hoa: bool,
                               subject_is_waterfront: bool) -> List[CompProperty]:
        """
        Search for sold properties within specified criteria
        """
        try:
            # Extract location for search
            location = self._extract_location_for_search(subject_address)
            
            # Search parameters
            search_params = {
                "location": location,
                "status_type": "RecentlySold",
                "home_type": "Houses",
                "maxPrice": str(int(subject_sqft * 400)),  # Max $400/sqft
                "minPrice": str(int(subject_sqft * 50)),   # Min $50/sqft
                "beds": str(subject_beds),
                "baths": str(int(subject_baths)),
                "sqft": f"{subject_sqft - self.sqft_tolerance},{subject_sqft + self.sqft_tolerance}",
                "sortBy": "newest"
            }
            
            logger.info(f"📍 Search params: {search_params}")
            
            # Make API call
            response = requests.get(
                "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch",
                headers=self.headers,
                params=search_params,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"❌ API error: {response.status_code}")
                return []
            
            data = response.json()
            
            # Process results
            comps = []
            properties = data.get('props', [])
            
            cutoff_date = datetime.now() - timedelta(days=time_window)
            
            for prop in properties:
                try:
                    # Extract property data
                    comp = self._extract_property_data(prop)
                    if not comp:
                        continue
                    
                    # Calculate distance
                    if comp.lat and comp.lng:
                        comp.distance = self.haversine_distance(
                            subject_lat, subject_lng, comp.lat, comp.lng
                        )
                    else:
                        comp.distance = 999.0  # Unknown distance
                    
                    # Apply strict filtering criteria
                    if self._meets_strict_criteria(
                        comp, subject_beds, subject_baths, subject_sqft,
                        radius, cutoff_date, subject_has_pool, 
                        subject_has_hoa, subject_is_waterfront
                    ):
                        comps.append(comp)
                        logger.info(f"✅ Added comp: {comp.address} - ${comp.price:,.0f} ({comp.distance:.2f} mi)")
                
                except Exception as e:
                    logger.error(f"❌ Error processing property: {e}")
                    continue
            
            return comps
            
        except Exception as e:
            logger.error(f"❌ Error searching properties: {e}")
            return []
    
    def _extract_property_data(self, prop: Dict) -> Optional[CompProperty]:
        """
        Extract property data from Zillow API response
        """
        try:
            # Basic property info
            address = prop.get('address')
            if not address:
                return None
            
            price = prop.get('price')
            if not price:
                return None
            
            beds = prop.get('bedrooms', 0)
            baths = prop.get('bathrooms', 0)
            sqft = prop.get('livingArea', 0)
            
            # Location data
            lat = prop.get('latitude')
            lng = prop.get('longitude')
            
            # Sale date
            sale_date = prop.get('soldDate')
            if sale_date:
                try:
                    sale_datetime = datetime.strptime(sale_date, '%Y-%m-%d')
                    days_ago = (datetime.now() - sale_datetime).days
                except:
                    days_ago = 0
            else:
                days_ago = 0
            
            # Property features
            has_pool = bool(prop.get('hasPool', False))
            has_hoa = bool(prop.get('homeOwnerAssociation', False))
            is_waterfront = bool(prop.get('waterfront', False))
            
            # Images
            image_url = None
            images = prop.get('imgSrc', [])
            if images and len(images) > 0:
                image_url = images[0]
            
            # Additional info
            lot_size = prop.get('lotSize')
            year_built = prop.get('yearBuilt')
            
            return CompProperty(
                address=address,
                price=float(price),
                beds=int(beds),
                baths=float(baths),
                sqft=int(sqft) if sqft else 0,
                sale_date=sale_date or '',
                days_ago=days_ago,
                distance=0.0,  # Will be calculated later
                lat=float(lat) if lat else 0.0,
                lng=float(lng) if lng else 0.0,
                image_url=image_url,
                has_pool=has_pool,
                has_hoa=has_hoa,
                is_waterfront=is_waterfront,
                lot_size=lot_size,
                year_built=year_built
            )
            
        except Exception as e:
            logger.error(f"❌ Error extracting property data: {e}")
            return None
    
    def _meets_strict_criteria(self, comp: CompProperty, subject_beds: int,
                             subject_baths: float, subject_sqft: int,
                             max_radius: float, cutoff_date: datetime,
                             subject_has_pool: bool, subject_has_hoa: bool,
                             subject_is_waterfront: bool) -> bool:
        """
        Check if property meets strict underwriting criteria
        """
        # Exact bed/bath match
        if comp.beds != subject_beds or comp.baths != subject_baths:
            return False
        
        # Square footage within tolerance
        if abs(comp.sqft - subject_sqft) > self.sqft_tolerance:
            return False
        
        # Distance check
        if comp.distance > max_radius:
            return False
        
        # Feature matching (exclude if subject doesn't have but comp does)
        if comp.has_pool and not subject_has_pool:
            return False
        if comp.has_hoa and not subject_has_hoa:
            return False
        if comp.is_waterfront and not subject_is_waterfront:
            return False
        
        # Sale date check
        if comp.sale_date:
            try:
                sale_date = datetime.strptime(comp.sale_date, '%Y-%m-%d')
                if sale_date < cutoff_date:
                    return False
            except:
                pass
        
        return True
    
    def _is_duplicate(self, comp: CompProperty, existing_comps: List[CompProperty]) -> bool:
        """
        Check if property is a duplicate
        """
        for existing in existing_comps:
            if (abs(comp.lat - existing.lat) < 0.001 and 
                abs(comp.lng - existing.lng) < 0.001):
                return True
        return False
    
    def _extract_location_for_search(self, address: str) -> str:
        """
        Extract location for API search
        """
        # Clean address for search
        address = address.replace(',', ' ')
        address = re.sub(r'\s+', ' ', address)
        return address.strip()
    
    def _calculate_analysis(self, comps: List[CompProperty], subject_sqft: int) -> Dict:
        """
        Calculate analysis metrics
        """
        if not comps:
            return {
                'total_comps': 0,
                'avg_price': 0,
                'price_range': {'min': 0, 'max': 0},
                'avg_price_per_sqft': 0,
                'recommended_arv': 0,
                'confidence': 'No Data'
            }
        
        prices = [comp.price for comp in comps]
        price_per_sqft = [comp.price / comp.sqft for comp in comps if comp.sqft > 0]
        
        avg_price = sum(prices) / len(prices)
        avg_price_per_sqft = sum(price_per_sqft) / len(price_per_sqft) if price_per_sqft else 0
        
        # Calculate recommended ARV
        recommended_arv = avg_price_per_sqft * subject_sqft if avg_price_per_sqft > 0 else avg_price
        
        # Confidence level
        confidence = 'High' if len(comps) >= 3 else 'Limited'
        
        return {
            'total_comps': len(comps),
            'avg_price': avg_price,
            'price_range': {'min': min(prices), 'max': max(prices)},
            'avg_price_per_sqft': avg_price_per_sqft,
            'recommended_arv': recommended_arv,
            'confidence': confidence
        }
    
    def _format_comp_for_ui(self, comp: CompProperty) -> Dict:
        """
        Format comparable property for UI display
        """
        return {
            'address': comp.address,
            'price': comp.price,
            'beds': comp.beds,
            'baths': comp.baths,
            'sqft': comp.sqft,
            'sale_date': comp.sale_date,
            'days_ago': comp.days_ago,
            'distance': comp.distance,
            'image_url': comp.image_url,
            'price_per_sqft': comp.price / comp.sqft if comp.sqft > 0 else 0,
            'formatted_price': f"${comp.price:,.0f}",
            'formatted_distance': f"{comp.distance:.1f} mi away",
            'formatted_specs': f"{comp.beds} bd, {comp.baths} ba, {comp.sqft:,} sqft",
            'formatted_sale_date': f"Sold {comp.days_ago} days ago"
        }

# Global instance
premium_comps_service = PremiumCompsService()