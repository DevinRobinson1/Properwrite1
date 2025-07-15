"""
Unified Property Data Service - Central cache-aware wrapper for all property data APIs
Handles all external API calls through a single interface with intelligent caching
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from utils.cache_utils import (
    generate_cache_key, 
    normalize_address, 
    validate_cache_payload,
    merge_property_data,
    should_refresh_cache,
    create_cache_metadata
)
from services.cache_storage_service import get_cache_service

logger = logging.getLogger(__name__)


class UnifiedPropertyDataService:
    """
    Central service for all property data with intelligent caching
    """
    
    def __init__(self):
        self.cache_service = get_cache_service()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Import existing services lazily to avoid circular imports
        self._enhanced_property_service = None
        self._comprehensive_valuation_service = None
        self._google_places_service = None
        self._enhanced_comps_service = None
        self._simple_comps_service = None
        self._rentcast_service = None
        
        # Background refresh queue
        self._refresh_queue = set()
    
    def get_property_data(self, address: str, city: str = "", state: str = "", 
                         zip_code: str = "", place_id: str = "", 
                         latitude: float = None, longitude: float = None,
                         force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive property data with intelligent caching
        
        Args:
            address: Property address
            city: City name
            state: State abbreviation
            zip_code: ZIP code
            place_id: Google Places place_id
            latitude: Property latitude
            longitude: Property longitude
            force_refresh: Force refresh cache
            
        Returns:
            Comprehensive property data
        """
        # Generate cache key
        full_address = self._build_full_address(address, city, state, zip_code)
        cache_key = generate_cache_key(full_address, 'property')
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_data = self.cache_service.get(cache_key)
            if cached_data and cached_data.get('payload'):
                logger.info(f"Cache hit for property: {address}")
                
                # Check if we should refresh in background
                if should_refresh_cache(cached_data, ttl_hours=12):
                    self._queue_background_refresh(cache_key, full_address, city, state, zip_code, place_id, latitude, longitude)
                
                return cached_data['payload']
        
        # Cache miss or force refresh - fetch fresh data
        logger.info(f"Cache miss for property: {address}, fetching fresh data")
        
        # Use distributed lock to prevent concurrent API calls
        fresh_data = self._fetch_fresh_property_data_with_lock(
            cache_key, full_address, city, state, zip_code, place_id, latitude, longitude
        )
        
        return fresh_data
    
    def get_comparable_properties(self, address: str, beds: int, baths: float, 
                                 sqft: int, lat: float = None, lng: float = None,
                                 force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get comparable properties with caching
        
        Args:
            address: Subject property address
            beds: Number of bedrooms
            baths: Number of bathrooms
            sqft: Square footage
            lat: Latitude
            lng: Longitude
            force_refresh: Force refresh cache
            
        Returns:
            Comparable properties data
        """
        # Generate cache key including property characteristics
        cache_key = generate_cache_key(f"{address}_{beds}_{baths}_{sqft}", 'comps')
        
        # Check cache first
        if not force_refresh:
            cached_data = self.cache_service.get(cache_key)
            if cached_data and cached_data.get('payload'):
                logger.info(f"Cache hit for comps: {address}")
                return cached_data['payload']
        
        # Cache miss - fetch fresh data
        logger.info(f"Cache miss for comps: {address}, fetching fresh data")
        
        # Use distributed lock
        fresh_data = self._fetch_fresh_comps_with_lock(
            cache_key, address, beds, baths, sqft, lat, lng
        )
        
        return fresh_data
    
    def get_google_places_data(self, place_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get Google Places data with caching
        
        Args:
            place_id: Google Places place_id
            force_refresh: Force refresh cache
            
        Returns:
            Google Places data
        """
        cache_key = generate_cache_key(place_id, 'google_places')
        
        # Check cache first
        if not force_refresh:
            cached_data = self.cache_service.get(cache_key)
            if cached_data and cached_data.get('payload'):
                logger.info(f"Cache hit for Google Places: {place_id}")
                return cached_data['payload']
        
        # Cache miss - fetch fresh data
        logger.info(f"Cache miss for Google Places: {place_id}, fetching fresh data")
        
        fresh_data = self._fetch_fresh_google_places_with_lock(cache_key, place_id)
        return fresh_data
    
    def validate_address(self, street: str, city: str, state: str, zip_code: str,
                        force_refresh: bool = False) -> Dict[str, Any]:
        """
        Validate address with caching
        
        Args:
            street: Street address
            city: City
            state: State
            zip_code: ZIP code
            force_refresh: Force refresh cache
            
        Returns:
            Address validation result
        """
        full_address = self._build_full_address(street, city, state, zip_code)
        cache_key = generate_cache_key(full_address, 'address_validation')
        
        # Check cache first
        if not force_refresh:
            cached_data = self.cache_service.get(cache_key)
            if cached_data and cached_data.get('payload'):
                logger.info(f"Cache hit for address validation: {street}")
                return cached_data['payload']
        
        # Cache miss - fetch fresh data
        logger.info(f"Cache miss for address validation: {street}, fetching fresh data")
        
        fresh_data = self._fetch_fresh_address_validation_with_lock(
            cache_key, street, city, state, zip_code
        )
        return fresh_data
    
    def get_rent_estimate(self, address: str, city: str = "", state: str = "",
                         bedrooms: int = None, bathrooms: str = None,
                         force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get rent estimate with caching
        
        Args:
            address: Property address
            city: City
            state: State
            bedrooms: Number of bedrooms
            bathrooms: Number of bathrooms
            force_refresh: Force refresh cache
            
        Returns:
            Rent estimate data
        """
        full_address = self._build_full_address(address, city, state)
        cache_key = generate_cache_key(f"{full_address}_{bedrooms}_{bathrooms}", 'rent_estimate')
        
        # Check cache first
        if not force_refresh:
            cached_data = self.cache_service.get(cache_key)
            if cached_data and cached_data.get('payload'):
                logger.info(f"Cache hit for rent estimate: {address}")
                return cached_data['payload']
        
        # Cache miss - fetch fresh data
        logger.info(f"Cache miss for rent estimate: {address}, fetching fresh data")
        
        fresh_data = self._fetch_fresh_rent_estimate_with_lock(
            cache_key, address, city, state, bedrooms, bathrooms
        )
        return fresh_data
    
    def _fetch_fresh_property_data_with_lock(self, cache_key: str, address: str, 
                                           city: str, state: str, zip_code: str,
                                           place_id: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """Fetch fresh property data with distributed lock"""
        
        # Try to acquire lock
        if self.cache_service.set_with_lock(cache_key, {'status': 'fetching'}, lock_timeout=60):
            try:
                # Fetch data from multiple sources in parallel
                fresh_data = self._fetch_property_data_parallel(
                    address, city, state, zip_code, place_id, latitude, longitude
                )
                
                # Cache the fresh data
                self.cache_service.set(cache_key, fresh_data)
                
                return fresh_data
                
            except Exception as e:
                logger.error(f"Failed to fetch property data: {e}")
                # Return stale data if available
                stale_data = self.cache_service.get_stale_data(cache_key)
                if stale_data:
                    logger.info("Returning stale data due to fetch failure")
                    return stale_data.get('payload', {})
                raise
        else:
            # Lock already exists, wait and try to get cached result
            time.sleep(1)
            for _ in range(30):  # Wait up to 30 seconds
                cached_data = self.cache_service.get(cache_key)
                if cached_data and cached_data.get('payload'):
                    if cached_data['payload'].get('status') != 'fetching':
                        return cached_data['payload']
                time.sleep(1)
            
            # Fallback to stale data
            stale_data = self.cache_service.get_stale_data(cache_key)
            if stale_data:
                return stale_data.get('payload', {})
            
            # Final fallback - fetch without lock
            return self._fetch_property_data_parallel(
                address, city, state, zip_code, place_id, latitude, longitude
            )
    
    def _fetch_property_data_parallel(self, address: str, city: str, state: str,
                                    zip_code: str, place_id: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """Fetch property data from multiple sources in parallel"""
        
        # Initialize services
        enhanced_service = self._get_enhanced_property_service()
        comprehensive_service = self._get_comprehensive_valuation_service()
        
        # Prepare tasks
        tasks = []
        
        # Task 1: Enhanced property service
        if enhanced_service:
            tasks.append(('enhanced', self._call_enhanced_property_service, 
                         (address, city, state, zip_code)))
        
        # Task 2: Comprehensive valuation service
        if comprehensive_service:
            tasks.append(('comprehensive', self._call_comprehensive_valuation_service,
                         (place_id, address, city, state, zip_code, latitude, longitude)))
        
        # Execute tasks in parallel
        results = {}
        futures = {}
        
        for task_name, func, args in tasks:
            future = self.executor.submit(func, *args)
            futures[future] = task_name
        
        # Collect results
        for future in as_completed(futures, timeout=30):
            task_name = futures[future]
            try:
                result = future.result()
                results[task_name] = result
            except Exception as e:
                logger.warning(f"Task {task_name} failed: {e}")
                results[task_name] = None
        
        # Merge results
        merged_data = self._merge_property_results(results)
        
        # Add metadata
        merged_data.update(create_cache_metadata(address, list(results.keys())))
        
        return merged_data
    
    def _fetch_fresh_comps_with_lock(self, cache_key: str, address: str, beds: int,
                                   baths: float, sqft: int, lat: float, lng: float) -> Dict[str, Any]:
        """Fetch fresh comparable properties with distributed lock"""
        
        if self.cache_service.set_with_lock(cache_key, {'status': 'fetching'}, lock_timeout=60):
            try:
                # Get comp services
                enhanced_comps = self._get_enhanced_comps_service()
                simple_comps = self._get_simple_comps_service()
                
                # Try enhanced service first
                if enhanced_comps:
                    from enhanced_comps_service import SearchParams
                    search_params = SearchParams(
                        address=address,
                        beds=beds,
                        baths=baths,
                        sqft=sqft,
                        lat=lat,
                        lng=lng
                    )
                    
                    fresh_data = enhanced_comps.search_comparable_sales(search_params)
                    
                    # Fallback to simple service if enhanced fails
                    if not fresh_data.get('success') and simple_comps:
                        fresh_data = simple_comps.search_comparable_sales(
                            address, beds, baths, sqft, lat, lng
                        )
                else:
                    # Use simple service only
                    fresh_data = simple_comps.search_comparable_sales(
                        address, beds, baths, sqft, lat, lng
                    )
                
                # Cache the result
                self.cache_service.set(cache_key, fresh_data)
                
                return fresh_data
                
            except Exception as e:
                logger.error(f"Failed to fetch comps: {e}")
                stale_data = self.cache_service.get_stale_data(cache_key)
                if stale_data:
                    return stale_data.get('payload', {})
                raise
        else:
            # Wait for lock to be released
            time.sleep(1)
            for _ in range(30):
                cached_data = self.cache_service.get(cache_key)
                if cached_data and cached_data.get('payload'):
                    if cached_data['payload'].get('status') != 'fetching':
                        return cached_data['payload']
                time.sleep(1)
            
            # Fallback to stale data
            stale_data = self.cache_service.get_stale_data(cache_key)
            if stale_data:
                return stale_data.get('payload', {})
            
            # Final fallback - fetch without lock
            return {'success': False, 'error': 'Timeout waiting for cache lock'}
    
    def _fetch_fresh_google_places_with_lock(self, cache_key: str, place_id: str) -> Dict[str, Any]:
        """Fetch fresh Google Places data with distributed lock"""
        
        if self.cache_service.set_with_lock(cache_key, {'status': 'fetching'}, lock_timeout=30):
            try:
                google_service = self._get_google_places_service()
                if google_service:
                    fresh_data = google_service.get_canonical_address(place_id)
                    self.cache_service.set(cache_key, fresh_data)
                    return fresh_data
                else:
                    return {'error': 'Google Places service not available'}
                    
            except Exception as e:
                logger.error(f"Failed to fetch Google Places data: {e}")
                stale_data = self.cache_service.get_stale_data(cache_key)
                if stale_data:
                    return stale_data.get('payload', {})
                raise
        else:
            # Wait for existing request
            time.sleep(1)
            for _ in range(15):
                cached_data = self.cache_service.get(cache_key)
                if cached_data and cached_data.get('payload'):
                    if cached_data['payload'].get('status') != 'fetching':
                        return cached_data['payload']
                time.sleep(1)
            
            return {'error': 'Timeout waiting for Google Places data'}
    
    def _fetch_fresh_address_validation_with_lock(self, cache_key: str, street: str,
                                                city: str, state: str, zip_code: str) -> Dict[str, Any]:
        """Fetch fresh address validation with distributed lock"""
        
        if self.cache_service.set_with_lock(cache_key, {'status': 'fetching'}, lock_timeout=30):
            try:
                google_service = self._get_google_places_service()
                if google_service:
                    fresh_data = google_service.validate_address(street, city, state, zip_code)
                    self.cache_service.set(cache_key, fresh_data)
                    return fresh_data
                else:
                    return {'error': 'Google Places service not available'}
                    
            except Exception as e:
                logger.error(f"Failed to validate address: {e}")
                stale_data = self.cache_service.get_stale_data(cache_key)
                if stale_data:
                    return stale_data.get('payload', {})
                raise
        else:
            # Wait for existing request
            time.sleep(1)
            for _ in range(15):
                cached_data = self.cache_service.get(cache_key)
                if cached_data and cached_data.get('payload'):
                    if cached_data['payload'].get('status') != 'fetching':
                        return cached_data['payload']
                time.sleep(1)
            
            return {'error': 'Timeout waiting for address validation'}
    
    def _fetch_fresh_rent_estimate_with_lock(self, cache_key: str, address: str,
                                           city: str, state: str, bedrooms: int, bathrooms: str) -> Dict[str, Any]:
        """Fetch fresh rent estimate with distributed lock"""
        
        if self.cache_service.set_with_lock(cache_key, {'status': 'fetching'}, lock_timeout=30):
            try:
                rentcast_service = self._get_rentcast_service()
                if rentcast_service:
                    fresh_data = rentcast_service.get_rental_estimate(address, city, state)
                    self.cache_service.set(cache_key, fresh_data)
                    return fresh_data
                else:
                    return {'error': 'RentCast service not available'}
                    
            except Exception as e:
                logger.error(f"Failed to fetch rent estimate: {e}")
                stale_data = self.cache_service.get_stale_data(cache_key)
                if stale_data:
                    return stale_data.get('payload', {})
                raise
        else:
            # Wait for existing request
            time.sleep(1)
            for _ in range(15):
                cached_data = self.cache_service.get(cache_key)
                if cached_data and cached_data.get('payload'):
                    if cached_data['payload'].get('status') != 'fetching':
                        return cached_data['payload']
                time.sleep(1)
            
            return {'error': 'Timeout waiting for rent estimate'}
    
    def _queue_background_refresh(self, cache_key: str, address: str, city: str,
                                state: str, zip_code: str, place_id: str, 
                                latitude: float, longitude: float):
        """Queue background refresh for stale-while-revalidate"""
        if cache_key not in self._refresh_queue:
            self._refresh_queue.add(cache_key)
            
            # Submit background task
            def background_refresh():
                try:
                    fresh_data = self._fetch_property_data_parallel(
                        address, city, state, zip_code, place_id, latitude, longitude
                    )
                    self.cache_service.set(cache_key, fresh_data)
                    self._refresh_queue.discard(cache_key)
                except Exception as e:
                    logger.warning(f"Background refresh failed for {cache_key}: {e}")
                    self._refresh_queue.discard(cache_key)
            
            self.executor.submit(background_refresh)
    
    def _merge_property_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Merge property data from multiple sources"""
        merged = {
            'address': '',
            'bedrooms': None,
            'bathrooms': None,
            'square_feet': None,
            'year_built': None,
            'lot_size_sqft': None,
            'property_type': None,
            'zillow_estimate': None,
            'redfin_estimate': None,
            'realtor_estimate': None,
            'rentcast_estimate': None,
            'rent_estimate': None,
            'image_url': None,
            'data_sources': [],
            'data_errors': [],
            'confidence_scores': {}
        }
        
        # Merge data from all sources
        for source, data in results.items():
            if data:
                merged = merge_property_data(merged, data)
                if source not in merged['data_sources']:
                    merged['data_sources'].append(source)
        
        # Calculate average estimate
        estimates = [est for est in [
            merged['zillow_estimate'], merged['redfin_estimate'], 
            merged['realtor_estimate'], merged['rentcast_estimate']
        ] if est]
        
        if estimates:
            merged['average_estimate'] = sum(estimates) // len(estimates)
            merged['estimate_range'] = {
                'min': min(estimates),
                'max': max(estimates),
                'count': len(estimates)
            }
        
        return merged
    
    def _build_full_address(self, address: str, city: str = "", state: str = "", zip_code: str = "") -> str:
        """Build full address string"""
        parts = [address]
        if city:
            parts.append(city)
        if state:
            parts.append(state)
        if zip_code:
            parts.append(zip_code)
        return ", ".join(parts)
    
    # Service getters with lazy initialization
    def _get_enhanced_property_service(self):
        if self._enhanced_property_service is None:
            try:
                from enhanced_property_service import EnhancedPropertyService
                self._enhanced_property_service = EnhancedPropertyService()
            except ImportError:
                logger.warning("Enhanced property service not available")
        return self._enhanced_property_service
    
    def _get_comprehensive_valuation_service(self):
        if self._comprehensive_valuation_service is None:
            try:
                from comprehensive_valuation_service import ComprehensiveValuationService
                self._comprehensive_valuation_service = ComprehensiveValuationService()
            except ImportError:
                logger.warning("Comprehensive valuation service not available")
        return self._comprehensive_valuation_service
    
    def _get_google_places_service(self):
        if self._google_places_service is None:
            try:
                from google_places_service import GooglePlacesService
                self._google_places_service = GooglePlacesService()
            except ImportError:
                logger.warning("Google Places service not available")
        return self._google_places_service
    
    def _get_enhanced_comps_service(self):
        if self._enhanced_comps_service is None:
            try:
                from enhanced_comps_service import EnhancedCompsService
                self._enhanced_comps_service = EnhancedCompsService()
            except ImportError:
                logger.warning("Enhanced comps service not available")
        return self._enhanced_comps_service
    
    def _get_simple_comps_service(self):
        if self._simple_comps_service is None:
            try:
                from simple_comps_service import SimpleCompsService
                self._simple_comps_service = SimpleCompsService()
            except ImportError:
                logger.warning("Simple comps service not available")
        return self._simple_comps_service
    
    def _get_rentcast_service(self):
        if self._rentcast_service is None:
            try:
                from rentcast_api_service import RentCastAPIService
                self._rentcast_service = RentCastAPIService()
            except ImportError:
                logger.warning("RentCast service not available")
        return self._rentcast_service
    
    def _call_enhanced_property_service(self, address: str, city: str, state: str, zip_code: str):
        """Call enhanced property service"""
        service = self._get_enhanced_property_service()
        if service:
            return service.get_comprehensive_property_data(address, city, state, zip_code)
        return None
    
    def _call_comprehensive_valuation_service(self, place_id: str, address: str, city: str, 
                                            state: str, zip_code: str, latitude: float, longitude: float):
        """Call comprehensive valuation service"""
        service = self._get_comprehensive_valuation_service()
        if service:
            return service.get_comprehensive_valuation(place_id, address, city, state, zip_code, latitude, longitude)
        return None
    
    def clear_cache(self, address: str = None):
        """Clear cache for specific address or all cache"""
        if address:
            cache_key = generate_cache_key(address, 'property')
            self.cache_service.delete(cache_key)
        else:
            self.cache_service.clear_all()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache_service.get_cache_stats()


# Global instance
_unified_service = None


def get_unified_property_service() -> UnifiedPropertyDataService:
    """Get global unified property service instance"""
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedPropertyDataService()
    return _unified_service