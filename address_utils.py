"""
Address Utilities for Real Estate API Integration
Handles address normalization for external property data sources
"""

import re
from urllib.parse import quote_plus

def to_zillow_search_string(gmaps_address: str) -> str:
    """
    Turn Google 'formatted_address' → Zillow-friendly one-liner.
    – Removes "USA" and duplicate city/state tokens
    – Removes HOA / subdivision names in ALL-CAPS
    – Strips apartment / unit suffixes (#, APT, Unit …)
    Returns a URL-escaped string ready to append after
    "…propertyExtendedSearch?location="
    """
    # 1) Strip country
    addr = re.sub(r',?\s+USA$', '', gmaps_address, flags=re.I)

    # 2) De-dup comma-separated tokens
    parts, seen = [], set()
    for p in addr.split(','):
        p = p.strip()
        if p.lower() not in seen:
            parts.append(p)
            seen.add(p.lower())
    addr = ', '.join(parts)

    # 3) Remove ALL-CAPS "phase / subdivision" noise
    addr = re.sub(r',?\s+[A-Z]{3,}(?:\s+[A-Z]{3,})*$', '', addr)

    # 4) Drop "#123", "Unit 4A", etc.
    addr = re.sub(r'\s+#?\s?\w+$', '', addr)

    return quote_plus(addr)

def normalize_address_for_apis(raw_address: str) -> str:
    """
    Normalize Google Places formatted address for general API usage
    Returns clean address string without URL encoding
    """
    # 1) Strip country
    addr = re.sub(r',?\s+USA$', '', raw_address, flags=re.I)

    # 2) De-dup comma-separated tokens
    parts, seen = [], set()
    for p in addr.split(','):
        p = p.strip()
        if p.lower() not in seen:
            parts.append(p)
            seen.add(p.lower())
    addr = ', '.join(parts)

    # 3) Remove ALL-CAPS "phase / subdivision" noise
    addr = re.sub(r',?\s+[A-Z]{3,}(?:\s+[A-Z]{3,})*$', '', addr)

    # 4) Drop "#123", "Unit 4A", etc.
    addr = re.sub(r'\s+#?\s?\w+$', '', addr)

    return addr.strip()