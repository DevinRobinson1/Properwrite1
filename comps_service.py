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
                        "minBeds": max(1, beds - 1),
                        "maxBeds": beds + 1,
                        "minBaths": max(1, baths - 1),
                        "maxBaths": baths + 1,
                        "minSqft": max(500, sqft - 500),
                        "maxSqft": sqft + 500,
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
                            logger.info(f"Address fields in comp: address={comp.get('address')}, streetAddress={comp.get('streetAddress')}, city={comp.get('city')}, state={comp.get('state')}")
                            if isinstance(comp.get('address'), dict):
                                logger.info(f"Address object fields: {comp.get('address')}")
                        # Merge data
                        comp.update(detail)
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
                        if not comp.get('address') or isinstance(comp.get('address'), dict):
                            # Check if address is a nested object
                            if isinstance(comp.get('address'), dict):
                                addr_obj = comp.get('address', {})
                                comp['address'] = f"{addr_obj.get('streetAddress', '')} {addr_obj.get('city', '')} {addr_obj.get('state', '')}"
                            else:
                                # Build from individual fields
                                street = comp.get('streetAddress', '') or comp.get('streetLine', '') or ''
                                city = comp.get('city', '') or comp.get('addressCity', '') or ''
                                state = comp.get('state', '') or comp.get('addressState', '') or ''
                                comp['address'] = f"{street} {city} {state}".strip()
                        
                        # Filter out subject property itself
                        comp_address = comp.get('address', '')
                        comp_address_clean = comp_address.lower().replace(',', '').replace(' ', '')
                        
                        # Skip if this is the subject property
                        if comp_address_clean == subject_address_clean:
                            logger.info(f"Skipping subject property: {comp_address}")
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
                                    # Try parsing string date
                                    sold_date = datetime.strptime(comp['dateSold'], '%Y-%m-%d')
                                else:
                                    sold_date = datetime.now()
                                
                                comp['days_old'] = (datetime.now() - sold_date).days
                            except:
                                comp['days_old'] = 0
                        else:
                            comp['days_old'] = 0
                        detailed_comps.append(comp)
            
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