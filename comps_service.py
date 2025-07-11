"""
Comparable Properties Service
Fetches and analyzes comparable sales using Zillow API and OpenAI
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from math import radians, cos, sin, asin, sqrt
import openai
import time

logger = logging.getLogger(__name__)

class CompsService:
    def __init__(self):
        self.rapidapi_key = os.environ.get('RAPIDAPI_KEY')
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        self.zillow_headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com"
        }
        
        # Appraisal adjustment rules
        self.adjustments = {
            'bedroom': 15000,  # $15k per bedroom
            'full_bath': 12500,  # $12.5k per full bath
            'half_bath': 7500,  # $7.5k per half bath
            'garage': 10000,  # $10k for garage
            'pool': 10000,  # $10k for pool
            'lot_size_per_sqft': 2,  # $2 per sqft difference
            'main_road_penalty': 0.15,  # 15% reduction
            'commercial_adjacent_penalty': 0.10  # 10% reduction
        }
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in miles"""
        R = 3959  # Earth radius in miles
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    def search_comparable_properties(self, address: str, beds: int, baths: float, sqft: int, 
                                   lat: float = None, lng: float = None) -> Dict:
        """Search for comparable properties using Zillow API"""
        
        if not self.rapidapi_key:
            return {'error': 'RapidAPI key not configured', 'comps': []}
        
        try:
            # Start with 90 days, expand if needed
            days_ranges = [90, 180, 365]
            radius_ranges = [0.25, 0.5, 1.0]  # miles
            
            all_comps = []
            
            for days in days_ranges:
                for radius in radius_ranges:
                    # Search for recently sold properties
                    search_url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
                    
                    params = {
                        "location": address,
                        "status_type": "RecentlySold",
                        "home_type": "Houses",
                        "minBeds": max(1, beds - 2),  # Expanded range
                        "maxBeds": beds + 2,          # Expanded range
                        "minBaths": max(1, baths - 1),
                        "maxBaths": baths + 2,        # Expanded range
                        "minSqft": max(500, sqft - 1000),  # Expanded range
                        "maxSqft": sqft + 1000,            # Expanded range
                        "daysOnZillow": days
                    }
                    
                    response = requests.get(search_url, headers=self.zillow_headers, params=params)
                    
                    if response.status_code == 429:
                        logger.warning(f"Rate limit hit for search, waiting before retry...")
                        time.sleep(1)  # Wait 1 second before continuing
                        continue
                    elif response.status_code == 200:
                        data = response.json()
                        # Handle both list and dict responses
                        if isinstance(data, list):
                            properties = data
                        else:
                            properties = data.get('props', [])
                        
                        # Log search response for debugging
                        if len(all_comps) == 0 and len(properties) > 0:
                            logger.info(f"First search property fields: {list(properties[0].keys())[:30] if properties else 'No properties'}")
                            if properties:
                                first_prop = properties[0]
                                logger.info(f"Search property example - address: {first_prop.get('address')}, streetAddress: {first_prop.get('streetAddress')}, addressStreet: {first_prop.get('addressStreet')}, addressCity: {first_prop.get('addressCity')}, addressState: {first_prop.get('addressState')}")
                        
                        # Filter by distance if we have coordinates
                        if lat and lng:
                            filtered_props = []
                            for prop in properties:
                                prop_lat = prop.get('latitude', 0)
                                prop_lng = prop.get('longitude', 0)
                                
                                if prop_lat and prop_lng:
                                    distance = self.haversine_distance(lat, lng, prop_lat, prop_lng)
                                    if distance <= radius:
                                        prop['distance'] = round(distance, 2)
                                        filtered_props.append(prop)
                            
                            properties = filtered_props
                        
                        all_comps.extend(properties)
                        
                        # If we have enough comps, stop searching
                        if len(all_comps) >= 5:
                            break
                
                if len(all_comps) >= 3:
                    break
            
            # Get detailed info for top comps
            detailed_comps = []
            subject_address_clean = address.lower().replace(',', '').replace(' ', '')
            
            for comp in all_comps[:10]:  # Get details for top 10
                zpid = comp.get('zpid')
                if zpid:
                    detail = self._get_property_details(zpid)
                    if detail:
                        # Log first comp details for debugging
                        if len(detailed_comps) == 0:
                            logger.info(f"First comp detail fields: {list(detail.keys())[:20]}")
                            logger.info(f"BEFORE merge - Address fields in comp: address={comp.get('address')}, streetAddress={comp.get('streetAddress')}, city={comp.get('city')}, state={comp.get('state')}")
                            logger.info(f"Detail API response address fields: address={detail.get('address')}, streetAddress={detail.get('streetAddress')}, city={detail.get('city')}, state={detail.get('state')}")
                            if isinstance(detail.get('address'), dict):
                                logger.info(f"Detail address object: {detail.get('address')}")
                        
                        # Save original address info from search before merging
                        original_search_address = comp.get('address')
                        original_street = comp.get('streetAddress') or comp.get('address')
                        original_city = comp.get('city')
                        original_state = comp.get('state')
                        
                        # Merge data
                        comp.update(detail)
                        
                        # Restore address if detail API didn't provide it
                        if not comp.get('streetAddress') and original_street:
                            comp['streetAddress'] = original_street
                        if not comp.get('city') and original_city:
                            comp['city'] = original_city
                        if not comp.get('state') and original_state:
                            comp['state'] = original_state
                        # Ensure we have the correct fields for display
                        # Handle bedrooms - check multiple possible field names
                        if not comp.get('bedrooms'):
                            comp['bedrooms'] = comp.get('beds') or comp.get('resoFacts', {}).get('bedrooms') or 0
                        
                        # Handle bathrooms - check multiple possible field names  
                        if not comp.get('bathrooms'):
                            comp['bathrooms'] = comp.get('baths') or comp.get('bathsFull') or comp.get('resoFacts', {}).get('bathrooms') or 0
                        
                        # Handle price - check multiple possible field names
                        if not comp.get('price'):
                            comp['price'] = (comp.get('soldPrice') or 
                                           comp.get('lastSoldPrice') or 
                                           comp.get('priceHistory', [{}])[0].get('price') if comp.get('priceHistory') else 0)
                        
                        # Handle living area - check multiple possible field names
                        if not comp.get('livingArea'):
                            comp['livingArea'] = (comp.get('livingAreaValue') or 
                                                comp.get('resoFacts', {}).get('livingArea') or 
                                                comp.get('livingAreaSqFt') or 0)
                        
                        # Handle address - check for nested address object first
                        if isinstance(comp.get('address'), dict):
                            # Address is a nested object
                            addr_obj = comp.get('address', {})
                            comp['address'] = f"{addr_obj.get('streetAddress', '')} {addr_obj.get('city', '')} {addr_obj.get('state', '')}"
                        elif not comp.get('address') or comp.get('address') == address:
                            # Build from individual fields if address is missing or same as subject
                            street = comp.get('streetAddress', '') or comp.get('streetLine', '') or original_street or ''
                            city = comp.get('city', '') or comp.get('addressCity', '') or original_city or ''
                            state = comp.get('state', '') or comp.get('addressState', '') or original_state or ''
                            
                            # If we still don't have good address parts, try to extract from original_search_address
                            if not street and original_search_address and isinstance(original_search_address, str):
                                parts = original_search_address.split(',')
                                if len(parts) >= 1:
                                    street = parts[0].strip()
                                if len(parts) >= 2:
                                    city = parts[1].strip()
                                if len(parts) >= 3:
                                    state = parts[2].strip()
                            
                            comp['address'] = f"{street} {city} {state}".strip()
                                
                        # Log address extraction for debugging
                        logger.info(f"Address extraction - Final: {comp.get('address')}, Street: {comp.get('streetAddress')}, City: {comp.get('city')}, State: {comp.get('state')}, Original search: {original_search_address}")
                        
                        # Filter out subject property itself and very similar addresses
                        comp_address = comp.get('address', '')
                        comp_address_clean = comp_address.lower().replace(',', '').replace(' ', '').replace('.', '')
                        
                        # Skip if this is the subject property or very similar address
                        if comp_address_clean == subject_address_clean:
                            logger.info(f"Skipping subject property: {comp_address}")
                            continue
                        
                        # Also skip if addresses are too similar (same street number and name)
                        subject_parts = subject_address_clean.split()
                        comp_parts = comp_address_clean.split()
                        
                        # Check if first part (street number) and second part (street name) are the same
                        if (len(subject_parts) >= 2 and len(comp_parts) >= 2 and 
                            subject_parts[0] == comp_parts[0] and 
                            subject_parts[1] == comp_parts[1]):
                            logger.info(f"Skipping very similar address: {comp_address} (similar to {address})")
                            continue
                        
                        # Get sold date - check multiple sources
                        if not comp.get('dateSold'):
                            # Check price history
                            if comp.get('priceHistory'):
                                for history in comp.get('priceHistory', []):
                                    if history.get('event') == 'Sold':
                                        comp['dateSold'] = history.get('date')
                                        break
                            # Check other date fields
                            if not comp.get('dateSold'):
                                comp['dateSold'] = comp.get('lastSoldDate') or comp.get('soldDate') or comp.get('datePosted')
                        
                        # Calculate days on market
                        if comp.get('dateSold'):
                            try:
                                # Handle different date formats
                                if isinstance(comp['dateSold'], (int, float)):
                                    # Unix timestamp in milliseconds
                                    sold_date = datetime.fromtimestamp(comp['dateSold'] / 1000)
                                elif isinstance(comp['dateSold'], str):
                                    # Try multiple date formats
                                    date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']
                                    sold_date = None
                                    for fmt in date_formats:
                                        try:
                                            sold_date = datetime.strptime(comp['dateSold'], fmt)
                                            break
                                        except:
                                            continue
                                    if not sold_date:
                                        sold_date = datetime.now()
                                else:
                                    sold_date = datetime.now()
                                
                                comp['days_old'] = (datetime.now() - sold_date).days
                                logger.info(f"Calculated days_old for {comp.get('address', 'unknown')}: {comp['days_old']} days (sold: {comp['dateSold']})")
                            except Exception as e:
                                logger.warning(f"Error calculating days_old: {e}")
                                comp['days_old'] = 0
                        else:
                            # If no dateSold, try to calculate from other sources
                            comp['days_old'] = 0
                            # Check if property has timeOnZillow or similar fields
                            if comp.get('timeOnZillow'):
                                comp['days_old'] = comp['timeOnZillow']
                            elif comp.get('daysOnMarket'):
                                comp['days_old'] = comp['daysOnMarket']
                        detailed_comps.append(comp)
            
            # If we don't have enough diverse comps, try a broader search
            if len(detailed_comps) < 3:
                logger.info(f"Only found {len(detailed_comps)} diverse comps, attempting broader search")
                
                # Try a much broader search
                params = {
                    "location": address,
                    "status_type": "RecentlySold",
                    "home_type": "Houses",
                    "minBeds": max(1, beds - 3),
                    "maxBeds": beds + 3,
                    "minBaths": max(1, baths - 2),
                    "maxBaths": baths + 3,
                    "minSqft": max(500, sqft - 1500),
                    "maxSqft": sqft + 1500,
                    "daysOnZillow": 365
                }
                
                response = requests.get(search_url, headers=self.zillow_headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    properties = data.get('props', []) if isinstance(data, dict) else data
                    
                    for comp in properties[:20]:  # Check more properties
                        zpid = comp.get('zpid')
                        if zpid:
                            detail = self._get_property_details(zpid)
                            if detail:
                                comp.update(detail)
                                
                                # Same address handling logic
                                original_address = comp.get('address')
                                if not comp.get('address') or isinstance(comp.get('address'), dict):
                                    if isinstance(comp.get('address'), dict):
                                        addr_obj = comp.get('address', {})
                                        comp['address'] = f"{addr_obj.get('streetAddress', '')} {addr_obj.get('city', '')} {addr_obj.get('state', '')}"
                                    else:
                                        street = comp.get('streetAddress', '') or comp.get('streetLine', '') or ''
                                        city = comp.get('city', '') or comp.get('addressCity', '') or ''
                                        state = comp.get('state', '') or comp.get('addressState', '') or ''
                                        comp['address'] = f"{street} {city} {state}".strip()
                                
                                # Filter out similar addresses
                                comp_address = comp.get('address', '')
                                comp_address_clean = comp_address.lower().replace(',', '').replace(' ', '').replace('.', '')
                                
                                # Skip if too similar
                                if comp_address_clean == subject_address_clean:
                                    continue
                                
                                # Skip if already in our list
                                if any(existing_comp.get('address', '').lower().replace(',', '').replace(' ', '').replace('.', '') == comp_address_clean 
                                       for existing_comp in detailed_comps):
                                    continue
                                
                                # Add missing fields
                                if not comp.get('bedrooms'):
                                    comp['bedrooms'] = comp.get('beds') or comp.get('resoFacts', {}).get('bedrooms') or 0
                                if not comp.get('bathrooms'):
                                    comp['bathrooms'] = comp.get('baths') or comp.get('bathsFull') or comp.get('resoFacts', {}).get('bathrooms') or 0
                                if not comp.get('price'):
                                    comp['price'] = (comp.get('soldPrice') or comp.get('lastSoldPrice') or 
                                                   comp.get('priceHistory', [{}])[0].get('price') if comp.get('priceHistory') else 0)
                                if not comp.get('livingArea'):
                                    comp['livingArea'] = (comp.get('livingAreaValue') or comp.get('resoFacts', {}).get('livingArea') or 
                                                        comp.get('livingAreaSqFt') or 0)
                                
                                # Calculate days old
                                comp['days_old'] = 0
                                if comp.get('dateSold'):
                                    try:
                                        if isinstance(comp['dateSold'], (int, float)):
                                            sold_date = datetime.fromtimestamp(comp['dateSold'] / 1000)
                                        elif isinstance(comp['dateSold'], str):
                                            date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']
                                            sold_date = None
                                            for fmt in date_formats:
                                                try:
                                                    sold_date = datetime.strptime(comp['dateSold'], fmt)
                                                    break
                                                except:
                                                    continue
                                            if sold_date:
                                                comp['days_old'] = (datetime.now() - sold_date).days
                                    except:
                                        pass
                                
                                detailed_comps.append(comp)
                                
                                # Stop when we have enough
                                if len(detailed_comps) >= 5:
                                    break
            
            return {
                'success': True,
                'comps': detailed_comps,
                'search_params': {
                    'days': days,
                    'radius': radius,
                    'beds': beds,
                    'baths': baths,
                    'sqft': sqft
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching comparables: {str(e)}")
            return {'error': str(e), 'comps': []}
    
    def _get_property_details(self, zpid: str) -> Optional[Dict]:
        """Get detailed property information"""
        try:
            url = "https://zillow-com1.p.rapidapi.com/property"
            params = {"zpid": zpid}
            
            response = requests.get(url, headers=self.zillow_headers, params=params)
            
            if response.status_code == 429:
                logger.warning(f"Rate limit hit for property details {zpid}, waiting...")
                time.sleep(1)  # Wait 1 second
                return None
            elif response.status_code == 200:
                return response.json()
            
        except Exception as e:
            logger.error(f"Error getting property details for zpid {zpid}: {str(e)}")
        
        return None
    
    def calculate_adjustments(self, subject: Dict, comp: Dict) -> Dict:
        """Calculate price adjustments for a comparable property"""
        adjustments = []
        total_adjustment = 0
        
        # Bedroom adjustment
        bed_diff = subject.get('beds', 0) - comp.get('bedrooms', 0)
        if bed_diff != 0:
            adjustment = bed_diff * self.adjustments['bedroom']
            adjustments.append({
                'type': 'Bedroom',
                'difference': bed_diff,
                'adjustment': adjustment,
                'description': f"{'Added' if adjustment > 0 else 'Reduced'} ${abs(adjustment):,} for {abs(bed_diff)} {'more' if bed_diff > 0 else 'fewer'} bedroom{'s' if abs(bed_diff) > 1 else ''}"
            })
            total_adjustment += adjustment
        
        # Bathroom adjustment
        bath_diff = subject.get('baths', 0) - comp.get('bathrooms', 0)
        if bath_diff != 0:
            adjustment = bath_diff * self.adjustments['full_bath']
            adjustments.append({
                'type': 'Bathroom',
                'difference': bath_diff,
                'adjustment': adjustment,
                'description': f"{'Added' if adjustment > 0 else 'Reduced'} ${abs(adjustment):,} for {abs(bath_diff)} {'more' if bath_diff > 0 else 'fewer'} bathroom{'s' if abs(bath_diff) > 1 else ''}"
            })
            total_adjustment += adjustment
        
        # Square footage adjustment
        sqft_diff = subject.get('sqft', 0) - comp.get('livingArea', 0)
        if abs(sqft_diff) > 100:  # Only adjust if difference is significant
            # Calculate price per sqft from comp
            comp_price = comp.get('price', 0)
            comp_sqft = comp.get('livingArea', 1)
            price_per_sqft = comp_price / comp_sqft if comp_sqft > 0 else 100
            
            adjustment = sqft_diff * (price_per_sqft * 0.5)  # Use 50% of price per sqft
            adjustments.append({
                'type': 'Square Footage',
                'difference': sqft_diff,
                'adjustment': adjustment,
                'description': f"{'Added' if adjustment > 0 else 'Reduced'} ${abs(adjustment):,} for {abs(sqft_diff):,} sqft difference"
            })
            total_adjustment += adjustment
        
        # Location adjustments (would need more data in real implementation)
        comp_address = comp.get('address', '') or comp.get('streetAddress', '') or ''
        if isinstance(comp_address, str) and (comp_address.lower().count('main') or comp_address.lower().count('highway')):
            adjustment = -comp.get('price', 0) * self.adjustments['main_road_penalty']
            adjustments.append({
                'type': 'Location',
                'adjustment': adjustment,
                'description': f"Reduced ${abs(adjustment):,} for main road exposure"
            })
            total_adjustment += adjustment
        
        return {
            'adjustments': adjustments,
            'total_adjustment': total_adjustment,
            'adjusted_price': comp.get('price', 0) + total_adjustment
        }
    
    def generate_ai_summary(self, subject: Dict, comps: List[Dict], adjustments: List[Dict]) -> Dict:
        """Generate AI-powered summary and ARV recommendation"""
        
        if not self.openai_api_key:
            return {
                'summary': 'AI summary not available - OpenAI API key not configured',
                'arv_recommendation': None,
                'confidence': 'Low'
            }
        
        try:
            # Prepare comp data for prompt
            comp_details = []
            for i, (comp, adj) in enumerate(zip(comps[:3], adjustments[:3])):
                comp_details.append(f"""
{i+1}. {comp.get('address', 'Unknown')}, Sold: ${comp.get('price', 0):,}, 
   {comp.get('bedrooms', 0)}bd/{comp.get('bathrooms', 0)}ba, {comp.get('livingArea', 0):,} sqft, 
   {comp.get('distance', 0):.1f} mi away, Sold on: {comp.get('dateSold', 'Unknown')}
   Adjusted Price: ${adj.get('adjusted_price', 0):,}
""")
            
            # Calculate average price per sqft
            valid_comps = [c for c in comps if c.get('price', 0) > 0 and c.get('livingArea', 0) > 0]
            avg_ppsf = sum(c['price'] / c['livingArea'] for c in valid_comps) / len(valid_comps) if valid_comps else 100
            
            prompt = f"""
You are a real estate valuation analyst. Given a subject property and a list of comparable properties, provide a natural-language ARV recommendation with reasoning.

Subject Property:
- Address: {subject.get('address', 'Unknown')}
- Beds: {subject.get('beds', 0)}, Baths: {subject.get('baths', 0)}, Sqft: {subject.get('sqft', 0)}

Comparable Properties:
{''.join(comp_details)}

Average Price per Sqft: ${avg_ppsf:.0f}/sqft

Adjustments already made:
- Bedroom difference: +/- $15,000
- Full bath difference: +/- $12,500
- Sqft difference: prorated at 50% of average price per sqft
- Location penalties applied where applicable

Now write a short professional summary:

1. Identify the most accurate 2-3 comps
2. Recommend an ARV range based on the adjusted comp prices
3. Give a confidence rating (High, Medium, Low) and brief reason

Format the response as a brief professional paragraph followed by:
- Recommended ARV: $XXX,XXX
- ARV Range: $XXX,XXX - $XXX,XXX
- Confidence: High/Medium/Low
"""
            
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional real estate appraiser providing conservative, data-driven valuations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse out key values from response
            lines = ai_response.split('\n')
            recommended_arv = None
            arv_range = None
            confidence = 'Medium'
            
            for line in lines:
                if 'recommended arv:' in line.lower():
                    try:
                        recommended_arv = int(''.join(filter(str.isdigit, line.split(':')[1])))
                    except:
                        pass
                elif 'arv range:' in line.lower():
                    try:
                        range_text = line.split(':')[1]
                        numbers = [int(''.join(filter(str.isdigit, n))) for n in range_text.split('-')]
                        if len(numbers) == 2:
                            arv_range = numbers
                    except:
                        pass
                elif 'confidence:' in line.lower():
                    if 'high' in line.lower():
                        confidence = 'High'
                    elif 'low' in line.lower():
                        confidence = 'Low'
            
            return {
                'summary': ai_response,
                'recommended_arv': recommended_arv,
                'arv_range': arv_range,
                'confidence': confidence,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {str(e)}")
            return {
                'summary': f'Error generating AI summary: {str(e)}',
                'recommended_arv': None,
                'confidence': 'Low',
                'error': str(e)
            }
    
    def analyze_comparables(self, subject_address: str, beds: int, baths: float, sqft: int,
                          lat: float = None, lng: float = None) -> Dict:
        """Main method to analyze comparable properties"""
        
        # Search for comparables
        search_result = self.search_comparable_properties(subject_address, beds, baths, sqft, lat, lng)
        
        if 'error' in search_result:
            return search_result
        
        comps = search_result.get('comps', [])
        
        if not comps:
            return {
                'error': 'No comparable properties found',
                'comps': [],
                'adjustments': [],
                'summary': None
            }
        
        # Calculate adjustments for each comp
        subject = {
            'address': subject_address,
            'beds': beds,
            'baths': baths,
            'sqft': sqft
        }
        
        adjustments = []
        for comp in comps:
            adj = self.calculate_adjustments(subject, comp)
            adjustments.append(adj)
        
        # Generate AI summary
        ai_summary = self.generate_ai_summary(subject, comps, adjustments)
        
        return {
            'success': True,
            'subject': subject,
            'comps': comps,
            'adjustments': adjustments,
            'ai_summary': ai_summary,
            'search_params': search_result.get('search_params', {})
        }