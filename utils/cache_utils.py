"""
Cache utilities for global property data caching
Provides address normalization and key generation for consistent cache keys
"""

import hashlib
import re
from typing import Dict, Any


def normalize_address(address: str) -> str:
    """
    Normalize address for consistent cache key generation
    
    Args:
        address: Raw address string
        
    Returns:
        Normalized address string
    """
    if not address:
        return ""
    
    # Convert to lowercase and remove extra whitespace
    normalized = address.strip().lower()
    
    # Replace multiple spaces with single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove common punctuation and abbreviations for consistency
    normalized = re.sub(r'[.,#]', '', normalized)
    
    # Standardize common abbreviations
    abbreviations = {
        'street': 'st',
        'avenue': 'ave',
        'boulevard': 'blvd',
        'drive': 'dr',
        'lane': 'ln',
        'road': 'rd',
        'circle': 'cir',
        'court': 'ct',
        'place': 'pl',
        'north': 'n',
        'south': 's',
        'east': 'e',
        'west': 'w',
        'northeast': 'ne',
        'northwest': 'nw',
        'southeast': 'se',
        'southwest': 'sw'
    }
    
    # Replace abbreviations for consistency
    for full, abbrev in abbreviations.items():
        normalized = re.sub(rf'\b{full}\b', abbrev, normalized)
        normalized = re.sub(rf'\b{abbrev}\b', abbrev, normalized)
    
    return normalized


def generate_cache_key(address: str, key_type: str = 'property') -> str:
    """
    Generate SHA256 cache key for given address
    
    Args:
        address: Address string to generate key for
        key_type: Type of cache key (property, comps, etc.)
        
    Returns:
        SHA256 hash as hex string
    """
    normalized = normalize_address(address)
    key_string = f"{key_type}:{normalized}"
    return hashlib.sha256(key_string.encode('utf-8')).hexdigest()


def extract_address_components(address: str) -> Dict[str, str]:
    """
    Extract components from a formatted address
    
    Args:
        address: Formatted address string
        
    Returns:
        Dictionary with address components
    """
    components = {
        'street': '',
        'city': '',
        'state': '',
        'zip_code': '',
        'country': ''
    }
    
    # Split by comma and process
    parts = [part.strip() for part in address.split(',')]
    
    if len(parts) >= 1:
        components['street'] = parts[0]
    
    if len(parts) >= 2:
        components['city'] = parts[1]
    
    if len(parts) >= 3:
        # Handle "State ZIP" format
        state_zip = parts[2].strip()
        state_zip_match = re.match(r'^([A-Za-z\s]+)\s+(\d{5}(?:-\d{4})?)$', state_zip)
        if state_zip_match:
            components['state'] = state_zip_match.group(1).strip()
            components['zip_code'] = state_zip_match.group(2).strip()
        else:
            components['state'] = state_zip
    
    if len(parts) >= 4:
        components['country'] = parts[3]
    
    return components


def is_address_similar(addr1: str, addr2: str, threshold: float = 0.8) -> bool:
    """
    Check if two addresses are similar enough to be considered the same
    
    Args:
        addr1: First address
        addr2: Second address
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        True if addresses are similar enough
    """
    norm1 = normalize_address(addr1)
    norm2 = normalize_address(addr2)
    
    if not norm1 or not norm2:
        return False
    
    # Simple similarity check using normalized addresses
    if norm1 == norm2:
        return True
    
    # Check if one is a substring of the other (for different formatting)
    if norm1 in norm2 or norm2 in norm1:
        return True
    
    # Calculate basic similarity score
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return False
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    similarity = len(intersection) / len(union)
    return similarity >= threshold


def validate_cache_payload(payload: Dict[str, Any]) -> bool:
    """
    Validate that cache payload contains required fields
    
    Args:
        payload: Cache payload to validate
        
    Returns:
        True if payload is valid
    """
    required_fields = ['address', 'fetched_at']
    
    for field in required_fields:
        if field not in payload:
            return False
    
    # Check that fetched_at is a number (timestamp)
    if not isinstance(payload['fetched_at'], (int, float)):
        return False
    
    return True


def merge_property_data(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge new property data with existing cached data
    
    Args:
        existing: Existing cached property data
        new: New property data to merge
        
    Returns:
        Merged property data
    """
    merged = existing.copy()
    
    # Update with new data, preserving existing values where new is None/empty
    for key, value in new.items():
        if value is not None and value != '':
            merged[key] = value
        elif key not in merged:
            merged[key] = value
    
    return merged


def should_refresh_cache(cached_data: Dict[str, Any], ttl_hours: int = 24) -> bool:
    """
    Check if cached data should be refreshed based on TTL
    
    Args:
        cached_data: Cached data with fetched_at timestamp
        ttl_hours: TTL in hours
        
    Returns:
        True if cache should be refreshed
    """
    import time
    
    if not cached_data or 'fetched_at' not in cached_data:
        return True
    
    current_time = time.time()
    cache_time = cached_data['fetched_at']
    
    # Convert hours to seconds
    ttl_seconds = ttl_hours * 3600
    
    return (current_time - cache_time) > ttl_seconds


def create_cache_metadata(address: str, sources_used: list = None) -> Dict[str, Any]:
    """
    Create metadata for cache entry
    
    Args:
        address: Address for this cache entry
        sources_used: List of data sources used
        
    Returns:
        Cache metadata dictionary
    """
    import time
    
    return {
        'address': address,
        'normalized_address': normalize_address(address),
        'sources_used': sources_used or [],
        'fetched_at': time.time(),
        'cache_version': '1.0'
    }