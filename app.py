import os
import random
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, url_for
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# API Configuration
RENTCAST_API_KEY = os.environ.get("RENTCAST_API_KEY")
RENTCAST_BASE_URL = "https://api.rentcast.io/v1"

# RapidAPI Configuration
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
RAPIDAPI_HEADERS = {
    'x-rapidapi-key': RAPIDAPI_KEY,
    'Content-Type': 'application/json'
}

# Mock data for property analysis
MOCK_NEIGHBORHOODS = {
    'charlotte': ['Noda Arts District', 'South End', 'Dilworth', 'Myers Park', 'Plaza Midwood'],
    'raleigh': ['Downtown', 'North Hills', 'Glenwood South', 'Five Points', 'Cameron Village'],
    'atlanta': ['Midtown', 'Buckhead', 'Virginia Highland', 'Inman Park', 'Little Five Points'],
    'nashville': ['Music Row', 'The Gulch', 'East Nashville', 'Green Hills', 'Belle Meade']
}

MOCK_SCHOOLS = [
    {'name': 'West Charlotte High', 'distance': '0.4 mi', 'rating': '7/10'},
    {'name': 'Eastway Elementary', 'distance': '0.8 mi', 'rating': '8/10'},
    {'name': 'Northeast Middle', 'distance': '1.2 mi', 'rating': '6/10'}
]

MOCK_AMENITIES = [
    {'name': 'Northlake Mall', 'distance': '8 min drive', 'type': 'shopping'},
    {'name': 'Blue Line Light Rail', 'distance': '5 min walk', 'type': 'transport'},
    {'name': 'Camp North End', 'distance': '6 min drive', 'type': 'entertainment'},
    {'name': 'Whole Foods Market', 'distance': '4 min drive', 'type': 'grocery'},
    {'name': 'Presbyterian Hospital', 'distance': '12 min drive', 'type': 'medical'}
]

# Rentcast API Functions
def get_rentcast_property_data(address, city, state, zip_code):
    """Fetch property data from Rentcast API"""
    headers = {
        'X-Api-Key': RENTCAST_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Format address for API
    full_address = f"{address}, {city}, {state} {zip_code}"
    
    try:
        # Get property details
        property_url = f"{RENTCAST_BASE_URL}/properties"
        property_params = {
            'address': full_address
        }
        
        property_response = requests.get(property_url, headers=headers, params=property_params, timeout=10)
        logging.debug(f"Rentcast property API response: {property_response.status_code}")
        
        if property_response.status_code == 200:
            property_data = property_response.json()
            logging.debug(f"Rentcast property data: {property_data}")
            return property_data
        else:
            logging.error(f"Rentcast property API error: {property_response.status_code} - {property_response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Rentcast API request failed: {str(e)}")
        return None

def get_rentcast_market_data(address, city, state, zip_code, property_data):
    """Get market data including rent and value estimates from existing property data"""
    # Since we have property data, we can derive market information from it
    rent_estimate = None
    market_data = {}
    
    if property_data:
        # Use property characteristics to estimate rent (will be more accurate when we get other APIs)
        beds = property_data.get('bedrooms', 3)
        baths = property_data.get('bathrooms', 2)
        sqft = property_data.get('squareFootage', 1400)
        
        # Conservative rent estimate based on property value and characteristics
        if property_data.get('lastSalePrice'):
            # Use 1% rule as baseline
            estimated_monthly_rent = int(property_data['lastSalePrice'] * 0.01)
        else:
            # Fallback based on square footage and location
            rent_per_sqft = 1.2 if city.lower() in ['charlotte', 'raleigh', 'atlanta'] else 1.0
            estimated_monthly_rent = int(sqft * rent_per_sqft)
        
        market_data = {
            'rent_estimate': estimated_monthly_rent,
            'last_sale_price': property_data.get('lastSalePrice'),
            'last_sale_date': property_data.get('lastSaleDate'),
            'assessed_value': property_data.get('taxAssessments', {}).get('2024', {}).get('value') if property_data.get('taxAssessments') else None
        }
    
    return market_data

def search_comparable_properties(city, state, beds, baths, sqft):
    """Search for comparable properties in the same area"""
    headers = {
        'X-Api-Key': RENTCAST_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        # Search for properties in the same city with similar characteristics
        search_url = f"{RENTCAST_BASE_URL}/properties"
        search_params = {
            'city': city,
            'state': state,
            'bedrooms': beds,
            'bathrooms': baths,
            'limit': 20  # Get more properties to filter through
        }
        
        search_response = requests.get(search_url, headers=headers, params=search_params, timeout=15)
        logging.debug(f"Rentcast search API response: {search_response.status_code}")
        
        if search_response.status_code == 200:
            properties_data = search_response.json()
            logging.debug(f"Found {len(properties_data)} properties in search")
            return properties_data
        else:
            logging.warning(f"Rentcast search API returned: {search_response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Rentcast search API request failed: {str(e)}")
        return []

# RapidAPI Integration Functions
def get_zillow_property_data(address, city, state, zip_code):
    """Get property data from Zillow via RapidAPI"""
    headers = {**RAPIDAPI_HEADERS, 'x-rapidapi-host': 'zillow-com1.p.rapidapi.com'}
    
    try:
        # Search for property by address
        search_url = "https://zillow-com1.p.rapidapi.com/propertySearch"
        search_params = {
            'address': f"{address}, {city}, {state} {zip_code}",
            'status_type': 'ForSale'
        }
        
        response = requests.get(search_url, headers=headers, params=search_params, timeout=15)
        logging.debug(f"Zillow API response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Zillow data received: {len(data.get('results', []))} properties")
            return data
        else:
            logging.warning(f"Zillow API returned: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Zillow API request failed: {str(e)}")
        return None

def get_redfin_property_data(city, state):
    """Get property data from Redfin via RapidAPI"""
    headers = {**RAPIDAPI_HEADERS, 'x-rapidapi-host': 'redfin-com-data.p.rapidapi.com'}
    
    try:
        # Search for region ID first
        region_url = "https://redfin-com-data.p.rapidapi.com/properties/search-rent"
        region_params = {
            'regionId': f"{city}_{state}",  # This may need adjustment based on API docs
        }
        
        response = requests.get(region_url, headers=headers, params=region_params, timeout=15)
        logging.debug(f"Redfin API response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Redfin data received")
            return data
        else:
            logging.warning(f"Redfin API returned: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Redfin API request failed: {str(e)}")
        return None

def get_realtor_property_data(latitude, longitude):
    """Get property data from Realtor.com via RapidAPI"""
    headers = {**RAPIDAPI_HEADERS, 'x-rapidapi-host': 'realtor-search.p.rapidapi.com'}
    
    try:
        # Get nearby home values
        nearby_url = "https://realtor-search.p.rapidapi.com/properties/nearby-home-values"
        nearby_params = {
            'lat': latitude,
            'lon': longitude
        }
        
        response = requests.get(nearby_url, headers=headers, params=nearby_params, timeout=15)
        logging.debug(f"Realtor API response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Realtor data received")
            return data
        else:
            logging.warning(f"Realtor API returned: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Realtor API request failed: {str(e)}")
        return None

def get_airdna_data(city, state):
    """Get short-term rental data from AirDNA via RapidAPI"""
    headers = {**RAPIDAPI_HEADERS, 'x-rapidapi-host': 'airdna1.p.rapidapi.com'}
    
    try:
        # Get properties data
        airdna_url = "https://airdna1.p.rapidapi.com/properties"
        airdna_params = {
            'location': f"{city}, {state}",
            'currency': 'native'
        }
        
        response = requests.get(airdna_url, headers=headers, params=airdna_params, timeout=15)
        logging.debug(f"AirDNA API response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"AirDNA data received")
            return data
        else:
            logging.warning(f"AirDNA API returned: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"AirDNA API request failed: {str(e)}")
        return None

def get_comprehensive_property_data(address, city, state, zip_code, latitude=None, longitude=None):
    """Fetch comprehensive property data from all available APIs"""
    logging.info(f"Fetching comprehensive data for: {address}, {city}, {state} {zip_code}")
    
    # Fetch from all APIs concurrently
    property_data = {}
    
    # Rentcast data (already working)
    rentcast_data = get_rentcast_property_data(address, city, state, zip_code)
    if rentcast_data:
        property_data['rentcast'] = rentcast_data[0] if isinstance(rentcast_data, list) and rentcast_data else rentcast_data
    
    # Zillow data
    zillow_data = get_zillow_property_data(address, city, state, zip_code)
    if zillow_data:
        property_data['zillow'] = zillow_data
    
    # Redfin data
    redfin_data = get_redfin_property_data(city, state)
    if redfin_data:
        property_data['redfin'] = redfin_data
    
    # Use coordinates from Google Places or fallback to Rentcast
    if not latitude or not longitude:
        if rentcast_data and isinstance(rentcast_data, list) and rentcast_data:
            latitude = rentcast_data[0].get('latitude')
            longitude = rentcast_data[0].get('longitude')
    
    # Realtor data (needs coordinates)
    if latitude and longitude:
        try:
            lat_float = float(latitude)
            lng_float = float(longitude)
            realtor_data = get_realtor_property_data(lat_float, lng_float)
            if realtor_data:
                property_data['realtor'] = realtor_data
        except (ValueError, TypeError):
            logging.warning(f"Invalid coordinates provided: {latitude}, {longitude}")
    
    # AirDNA data
    airdna_data = get_airdna_data(city, state)
    if airdna_data:
        property_data['airdna'] = airdna_data
    
    return property_data

def generate_multi_source_valuations(comprehensive_data):
    """Generate property valuations from all available data sources"""
    valuations = {}
    
    # Rentcast valuation
    rentcast_data = comprehensive_data.get('rentcast', {})
    if rentcast_data:
        if rentcast_data.get('lastSalePrice'):
            valuations['Rentcast Last Sale'] = f"${rentcast_data['lastSalePrice']:,} ({rentcast_data.get('lastSaleDate', 'Unknown date')})"
        
        # Get latest tax assessment
        tax_assessments = rentcast_data.get('taxAssessments', {})
        if tax_assessments:
            latest_year = max(tax_assessments.keys()) if tax_assessments else None
            if latest_year:
                assessed_value = tax_assessments[latest_year].get('value')
                if assessed_value:
                    valuations['County Assessed Value'] = f"${assessed_value:,} ({latest_year})"
    
    # Zillow valuation
    zillow_data = comprehensive_data.get('zillow', {})
    if zillow_data and zillow_data.get('results'):
        for result in zillow_data['results'][:1]:  # Take first result
            if result.get('zestimate'):
                valuations['Zillow Zestimate'] = f"${result['zestimate']:,}"
            if result.get('price'):
                valuations['Zillow Listed Price'] = f"${result['price']:,}"
    
    # Redfin valuation
    redfin_data = comprehensive_data.get('redfin', {})
    if redfin_data and redfin_data.get('homes'):
        for home in redfin_data['homes'][:1]:  # Take first result
            if home.get('price'):
                valuations['Redfin Estimate'] = f"${home['price']:,}"
    
    # Realtor valuation
    realtor_data = comprehensive_data.get('realtor', {})
    if realtor_data and realtor_data.get('properties'):
        for prop in realtor_data['properties'][:1]:  # Take first result
            if prop.get('estimate'):
                valuations['Realtor.com Estimate'] = f"${prop['estimate']:,}"
    
    return valuations

def compile_market_data(comprehensive_data, city, state):
    """Compile market data from all sources including rent estimates"""
    market_data = {}
    
    # Rentcast data
    rentcast_data = comprehensive_data.get('rentcast', {})
    if rentcast_data:
        beds = rentcast_data.get('bedrooms', 3)
        baths = rentcast_data.get('bathrooms', 2)
        sqft = rentcast_data.get('squareFootage', 1400)
        
        # Calculate rent estimate from sale price
        if rentcast_data.get('lastSalePrice'):
            estimated_monthly_rent = int(rentcast_data['lastSalePrice'] * 0.01)
            market_data['rent_estimate'] = estimated_monthly_rent
            market_data['rent_source'] = 'Calculated from Rentcast sale data'
        
        market_data['last_sale_price'] = rentcast_data.get('lastSalePrice')
        market_data['last_sale_date'] = rentcast_data.get('lastSaleDate')
        
        # Tax assessment data
        tax_assessments = rentcast_data.get('taxAssessments', {})
        if tax_assessments:
            latest_year = max(tax_assessments.keys()) if tax_assessments else None
            if latest_year:
                market_data['assessed_value'] = tax_assessments[latest_year].get('value')
    
    # AirDNA short-term rental data
    airdna_data = comprehensive_data.get('airdna', {})
    if airdna_data and airdna_data.get('data'):
        properties = airdna_data['data']
        if properties:
            # Calculate average nightly rate and occupancy
            total_revenue = sum(prop.get('revenue', 0) for prop in properties[:10])
            avg_nightly_rate = sum(prop.get('adr', 0) for prop in properties[:10]) / min(len(properties), 10)
            avg_occupancy = sum(prop.get('occupancy', 0) for prop in properties[:10]) / min(len(properties), 10)
            
            market_data['airbnb_nightly_rate'] = int(avg_nightly_rate) if avg_nightly_rate > 0 else None
            market_data['airbnb_occupancy'] = round(avg_occupancy, 1) if avg_occupancy > 0 else None
            market_data['airbnb_monthly_estimate'] = int(avg_nightly_rate * 30 * (avg_occupancy / 100)) if avg_nightly_rate > 0 and avg_occupancy > 0 else None
    
    return market_data

def generate_property_title(address, city, beds, baths):
    """Generate an engaging property title"""
    emojis = ['🔥', '💎', '⭐', '🏆', '💰']
    descriptors = ['Flip This', 'Hot Deal', 'Prime Investment', 'Investor Special', 'Cash Cow']
    locations = ['Near Downtown', 'Prime Location', 'Great Neighborhood', 'Upcoming Area']
    
    emoji = random.choice(emojis)
    descriptor = random.choice(descriptors)
    location = random.choice(locations)
    
    return f"{emoji} {descriptor} {beds}/{baths} {location} {city.title()}!"

def calculate_financials(buy_price, sqft, beds, baths, comparables):
    """Calculate property financials with ARV based on comparable sales"""
    if not buy_price:
        buy_price = random.randint(180000, 350000)
    
    # Calculate ARV based on adjusted comparable sales
    if comparables and len(comparables) >= 3:
        # Use adjusted prices from comparables to calculate ARV
        adjusted_prices = [comp['adjusted_price'] for comp in comparables]
        arv = int(sum(adjusted_prices) / len(adjusted_prices))
        
        # Apply slight adjustment for subject property condition
        condition_adjustment = random.uniform(0.95, 1.05)  # ±5% for condition
        arv = int(arv * condition_adjustment)
    else:
        # Fallback calculation if insufficient comps
        arv_multiplier = random.uniform(1.25, 1.4)
        arv = int(buy_price * arv_multiplier)
    
    # Rehab estimate (typically $20-60 per sqft for light-medium rehab)
    rehab_per_sqft = random.randint(25, 50)
    rehab_cost = int(sqft * rehab_per_sqft)
    
    # Net profit calculation
    holding_costs = int(buy_price * 0.02)  # 2% for holding costs
    closing_costs = int(arv * 0.06)  # 6% for selling costs
    net_profit = arv - buy_price - rehab_cost - holding_costs - closing_costs
    
    # Rent estimate (typically 0.8-1.2% of ARV monthly)
    monthly_rent = int(arv * random.uniform(0.008, 0.012))
    
    return {
        'buy_price': buy_price,
        'arv': arv,
        'rehab_cost': rehab_cost,
        'holding_costs': holding_costs,
        'closing_costs': closing_costs,
        'net_profit': net_profit,
        'monthly_rent': monthly_rent,
        'profit_margin': round((net_profit / buy_price) * 100, 1),
        'arv_source': 'comparable_sales' if comparables and len(comparables) >= 3 else 'estimated'
    }

def generate_comparables(beds, baths, sqft, city):
    """Generate realistic comparable sales data following strict underwriting rules"""
    comparables = []
    base_price_per_sqft = random.randint(200, 280)
    
    # Follow strict underwriting rules for comp generation
    time_periods = [90, 180, 210, 240, 270, 300, 330, 365]  # Days, expanding as needed
    distance_ranges = [0.25, 0.5, 1.0]  # Miles
    
    comp_count = 0
    for time_limit in time_periods:
        if comp_count >= 5:  # Maximum 5 comps
            break
            
        for distance in distance_ranges:
            if comp_count >= 5:
                break
                
            # Generate comps within current time and distance parameters
            attempts = 0
            while comp_count < 5 and attempts < 10:
                attempts += 1
                
                # Days sold (within current time limit, prioritizing recent sales)
                if time_limit <= 90:
                    days_ago = random.randint(1, 90)
                elif time_limit <= 180:
                    days_ago = random.randint(1, 180)
                else:
                    days_ago = random.randint(1, time_limit)
                
                # Property characteristics matching rules
                # Match same property type and style
                comp_beds = beds
                comp_baths = baths
                
                # Slight variations allowed but prefer exact matches
                if random.random() < 0.3:  # 30% chance of slight variation
                    comp_beds = max(1, beds + random.choice([-1, 1]))
                if random.random() < 0.2:  # 20% chance of slight variation
                    comp_baths = max(1, baths + random.choice([-0.5, 0.5]))
                
                # Square footage within reasonable range
                sqft_variation = min(500, sqft * 0.15)  # Max 15% or 500 sqft
                comp_sqft = sqft + random.randint(-int(sqft_variation), int(sqft_variation))
                comp_sqft = max(800, comp_sqft)  # Minimum reasonable size
                
                # Calculate adjustments based on differences
                raw_price_per_sqft = base_price_per_sqft + random.randint(-15, 15)
                raw_price = comp_sqft * raw_price_per_sqft
                
                # Apply adjustment calculations
                adjustments = calculate_comp_adjustments(beds, baths, sqft, comp_beds, comp_baths, comp_sqft)
                adjusted_price = raw_price + adjustments['total_adjustment']
                
                # Generate address with distance consideration
                street_num = random.randint(100, 9999)
                street_names = ['Elm St', 'Oak Ave', 'Pine Dr', 'Maple Ln', 'Cedar Way', 'Birch Ct', 'Willow Dr', 'Ash Ln']
                address = f"{street_num} {random.choice(street_names)}"
                
                # Format sold date
                sold_date = (datetime.now() - timedelta(days=days_ago)).strftime('%b %Y')
                
                # Distance in miles (simulated)
                comp_distance = round(random.uniform(0.1, distance), 2)
                
                comparable = {
                    'address': address,
                    'beds': comp_beds,
                    'baths': comp_baths,
                    'sqft': comp_sqft,
                    'raw_price': raw_price,
                    'adjusted_price': adjusted_price,
                    'price_per_sqft': int(adjusted_price / comp_sqft),
                    'sold_date': sold_date,
                    'days_ago': days_ago,
                    'distance_miles': comp_distance,
                    'adjustments': adjustments,
                    'time_period': f"Within {time_limit} days",
                    'distance_range': f"Within {distance} mile(s)"
                }
                
                comparables.append(comparable)
                comp_count += 1
        
        # If we have at least 3 comps, we can stop
        if comp_count >= 3:
            break
    
    # Sort by most recent sales first, then by distance
    comparables.sort(key=lambda x: (x['days_ago'], x['distance_miles']))
    
    # Return top 5 comps maximum
    return comparables[:5]

def calculate_comp_adjustments(subject_beds, subject_baths, subject_sqft, comp_beds, comp_baths, comp_sqft):
    """Calculate monetary adjustments for comparable properties"""
    adjustments = {
        'bedroom_adj': 0,
        'bathroom_adj': 0,
        'sqft_adj': 0,
        'total_adjustment': 0,
        'notes': []
    }
    
    # Bedroom adjustment: ±$10K to $25K per bedroom difference
    bed_diff = subject_beds - comp_beds
    if bed_diff != 0:
        bed_adjustment = bed_diff * random.randint(15000, 20000)
        adjustments['bedroom_adj'] = bed_adjustment
        adjustments['notes'].append(f"Bedroom difference: {'+' if bed_diff > 0 else ''}{bed_diff} bed(s), ${bed_adjustment:+,}")
    
    # Bathroom adjustment: ±$10K to $15K per full bath, ±$5K to $10K per half bath
    bath_diff = subject_baths - comp_baths
    if bath_diff != 0:
        if bath_diff == int(bath_diff):  # Full bathroom difference
            bath_adjustment = bath_diff * random.randint(10000, 15000)
        else:  # Half bathroom difference
            bath_adjustment = bath_diff * random.randint(5000, 10000)
        adjustments['bathroom_adj'] = int(bath_adjustment)
        adjustments['notes'].append(f"Bathroom difference: {'+' if bath_diff > 0 else ''}{bath_diff} bath(s), ${int(bath_adjustment):+,}")
    
    # Square footage adjustment (if significant difference)
    sqft_diff = subject_sqft - comp_sqft
    if abs(sqft_diff) > 100:  # Only adjust if difference > 100 sqft
        # Approximate $50-80 per sqft difference
        price_per_sqft_adj = random.randint(50, 80)
        sqft_adjustment = sqft_diff * price_per_sqft_adj
        adjustments['sqft_adj'] = sqft_adjustment
        adjustments['notes'].append(f"Size difference: {'+' if sqft_diff > 0 else ''}{sqft_diff} sqft, ${sqft_adjustment:+,}")
    
    # Calculate total adjustment
    adjustments['total_adjustment'] = (
        adjustments['bedroom_adj'] + 
        adjustments['bathroom_adj'] + 
        adjustments['sqft_adj']
    )
    
    return adjustments

def process_rentcast_comparables(rentcast_comps, subject_beds, subject_baths, subject_sqft):
    """Process Rentcast comparable sales with strict underwriting rules"""
    if not rentcast_comps:
        return []
    
    valid_comps = []
    current_date = datetime.now()
    
    for comp in rentcast_comps:
        try:
            # Extract comp data
            comp_address = comp.get('address', 'Unknown Address')
            comp_beds = comp.get('bedrooms', 0)
            comp_baths = comp.get('bathrooms', 0)
            comp_sqft = comp.get('squareFootage', 0)
            comp_price = comp.get('price', 0)
            comp_sale_date = comp.get('saleDate', '')
            
            # Skip if missing essential data
            if not comp_price or not comp_sqft:
                continue
            
            # Parse sale date and check time limits
            try:
                sale_date = datetime.fromisoformat(comp_sale_date.replace('Z', '+00:00'))
                days_ago = (current_date - sale_date).days
            except:
                continue
            
            # Apply strict time filtering (max 365 days, prefer < 180)
            if days_ago > 365:
                continue
            
            # Apply strict property matching rules
            bed_diff = abs(subject_beds - comp_beds)
            bath_diff = abs(subject_baths - comp_baths)
            sqft_diff = abs(subject_sqft - comp_sqft)
            
            # Skip if too different (strict matching)
            if bed_diff > 1 or bath_diff > 1 or sqft_diff > 500:
                continue
            
            # Calculate adjustments
            adjustments = calculate_comp_adjustments(
                subject_beds, subject_baths, subject_sqft,
                comp_beds, comp_baths, comp_sqft
            )
            
            adjusted_price = comp_price + adjustments['total_adjustment']
            
            # Calculate distance (mock for now, will be real when we get geocoding)
            distance = round(random.uniform(0.1, 1.0), 2)
            
            valid_comp = {
                'address': comp_address,
                'beds': comp_beds,
                'baths': comp_baths,
                'sqft': comp_sqft,
                'raw_price': int(comp_price),
                'adjusted_price': int(adjusted_price),
                'price_per_sqft': int(adjusted_price / comp_sqft) if comp_sqft > 0 else 0,
                'sold_date': sale_date.strftime('%b %Y'),
                'days_ago': days_ago,
                'distance_miles': distance,
                'adjustments': adjustments,
                'time_period': f"Within {min(days_ago, 365)} days",
                'distance_range': f"Within {distance} mile(s)"
            }
            
            valid_comps.append(valid_comp)
            
        except Exception as e:
            logging.error(f"Error processing comp: {str(e)}")
            continue
    
    # Sort by most recent sales first, then by distance
    valid_comps.sort(key=lambda x: (x['days_ago'], x['distance_miles']))
    
    # Return top 5 comps maximum
    return valid_comps[:5]

def calculate_financials_from_api_data(property_data, market_data, comparables, sqft, beds, baths):
    """Calculate property financials using real API data"""
    
    # Estimate buy price from property data or market data
    if property_data and property_data.get('lastSalePrice'):
        buy_price = int(property_data['lastSalePrice'])
    elif market_data and market_data.get('assessed_value'):
        buy_price = int(market_data['assessed_value'] * 0.9)  # Assume 10% below assessed value
    elif comparables:
        # Use average of comparables as estimated market value
        comp_prices = [comp['adjusted_price'] for comp in comparables]
        buy_price = int(sum(comp_prices) / len(comp_prices)) if comp_prices else 250000
    else:
        buy_price = 250000  # Conservative fallback
    
    # Calculate ARV based on comparable sales
    if comparables and len(comparables) >= 3:
        adjusted_prices = [comp['adjusted_price'] for comp in comparables]
        arv = int(sum(adjusted_prices) / len(adjusted_prices))
        arv_source = 'comparable_sales'
    else:
        # Conservative ARV estimate without comps
        arv = int(buy_price * 1.15)  # Conservative 15% appreciation
        arv_source = 'estimated'
    
    # Rehab estimate based on property condition and age
    if property_data and property_data.get('yearBuilt'):
        property_age = datetime.now().year - property_data['yearBuilt']
        if property_age > 30:
            rehab_per_sqft = random.randint(40, 60)
        elif property_age > 15:
            rehab_per_sqft = random.randint(25, 40)
        else:
            rehab_per_sqft = random.randint(15, 25)
    else:
        rehab_per_sqft = random.randint(30, 50)
    
    rehab_cost = int(sqft * rehab_per_sqft)
    
    # Calculate costs
    holding_costs = int(buy_price * 0.02)  # 2% for holding costs
    closing_costs = int(arv * 0.06)  # 6% for selling costs
    
    # Net profit calculation
    net_profit = arv - buy_price - rehab_cost - holding_costs - closing_costs
    
    # Real rent estimate from market data
    if market_data and market_data.get('rent_estimate'):
        monthly_rent = int(market_data['rent_estimate'])
    else:
        # Conservative rent estimate using 1% rule
        monthly_rent = int(arv * 0.01)
    
    return {
        'buy_price': buy_price,
        'arv': arv,
        'rehab_cost': rehab_cost,
        'holding_costs': holding_costs,
        'closing_costs': closing_costs,
        'net_profit': net_profit,
        'monthly_rent': monthly_rent,
        'profit_margin': round((net_profit / buy_price) * 100, 1) if buy_price > 0 else 0,
        'arv_source': arv_source
    }

def generate_comprehensive_data_sources_summary(comprehensive_data):
    """Generate summary of all data sources used"""
    sources = {}
    
    # Check each API source
    if comprehensive_data.get('rentcast'):
        sources['Rentcast'] = 'Connected - Property details available'
    else:
        sources['Rentcast'] = 'No data retrieved'
    
    if comprehensive_data.get('zillow'):
        zillow_results = comprehensive_data['zillow'].get('results', [])
        sources['Zillow'] = f'Connected - {len(zillow_results)} properties found'
    else:
        sources['Zillow'] = 'No data retrieved'
    
    if comprehensive_data.get('redfin'):
        sources['Redfin'] = 'Connected - Market data available'
    else:
        sources['Redfin'] = 'No data retrieved'
    
    if comprehensive_data.get('realtor'):
        sources['Realtor.com'] = 'Connected - Property valuations available'
    else:
        sources['Realtor.com'] = 'No data retrieved'
    
    if comprehensive_data.get('airdna'):
        sources['AirDNA'] = 'Connected - Short-term rental data available'
    else:
        sources['AirDNA'] = 'No data retrieved'
    
    return sources

def generate_property_summary(address, city, financials):
    """Generate a friendly summary paragraph"""
    neighborhood = random.choice(MOCK_NEIGHBORHOODS.get(city.lower(), ['Downtown Area']))
    profit_desc = "healthy" if financials['net_profit'] > 40000 else "solid"
    spread_amount = f"${financials['net_profit']:,}"
    
    summaries = [
        f"Investor special just minutes from the {neighborhood}. This property has strong comps, light rehab needs, and a {profit_desc} {spread_amount} spread.",
        f"Prime investment opportunity in {neighborhood}. Great bones, excellent location, and projected {spread_amount} profit potential.",
        f"Turn-key flip opportunity near {neighborhood}. Strong rental market with {spread_amount} upside and growing neighborhood demand."
    ]
    
    return random.choice(summaries)

@app.route('/')
def index():
    return render_template('index.html', google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY'))

@app.route('/generate', methods=['POST'])
def generate_presentation():
    try:
        # Get form data including coordinates from Google Places
        data = request.form
        address = data.get('address', '').strip()
        city = data.get('city', '').strip()
        state = data.get('state', '').strip()
        zip_code = data.get('zip', '').strip()
        
        # Extract coordinates if available from Google Places
        latitude = data.get('latitude', '').strip()
        longitude = data.get('longitude', '').strip()
        
        logging.info(f"Processing property: {address}, {city}, {state} {zip_code}")
        if latitude and longitude:
            logging.info(f"Coordinates provided: {latitude}, {longitude}")
        
        # Fetch comprehensive property data from all APIs
        logging.info(f"Fetching comprehensive property data for: {address}, {city}, {state} {zip_code}")
        comprehensive_data = get_comprehensive_property_data(address, city, state, zip_code, latitude, longitude)
        
        # Extract property details from comprehensive data
        rentcast_property = comprehensive_data.get('rentcast', {})
        
        # Handle optional property details with defaults or API data
        if rentcast_property and 'bedrooms' in rentcast_property:
            beds = int(data.get('beds') or rentcast_property.get('bedrooms', 3))
            baths = float(data.get('baths') or rentcast_property.get('bathrooms', 2))
            sqft = int(data.get('sqft') or rentcast_property.get('squareFootage', 1400))
        else:
            beds = int(data.get('beds') or 3)
            baths = float(data.get('baths') or 2)
            sqft = int(data.get('sqft') or 1400)
        
        # Generate multi-source property valuations
        property_valuations = generate_multi_source_valuations(comprehensive_data)
        
        # Get market data and rent estimates from all sources
        market_data = compile_market_data(comprehensive_data, city, state)
        
        # Search for comparable properties
        comparable_properties = search_comparable_properties(city, state, beds, baths, sqft)
        
        # Process comparable sales with strict underwriting rules
        if comparable_properties:
            comparables = process_rentcast_comparables(comparable_properties, beds, baths, sqft)
        else:
            logging.warning("No comparable sales data available from Rentcast API")
            comparables = []
        
        # Calculate financials based on real data
        financials = calculate_financials_from_api_data(
            rentcast_property, market_data, comparables, sqft, beds, baths
        )
        
        # Generate property analysis
        title = generate_property_title(address, city, beds, baths)
        summary = generate_property_summary(address, city, financials)
        
        # Compile comprehensive property data
        property_data = {
            'address': address,
            'city': city,
            'state': state,
            'zip': zip_code,
            'beds': beds,
            'baths': baths,
            'sqft': sqft,
            'title': title,
            'summary': summary,
            'financials': financials,
            'comparables': comparables,
            'property_valuations': property_valuations,
            'comprehensive_data': comprehensive_data,
            'rent_estimates': market_data,
            'data_sources': generate_comprehensive_data_sources_summary(comprehensive_data),
            'schools': MOCK_SCHOOLS,  # Will be replaced with real data when other APIs are added
            'amenities': random.sample(MOCK_AMENITIES, 4),  # Will be replaced with real data
            'year_built': rentcast_property.get('yearBuilt') if rentcast_property else 2000,
            'lot_size': rentcast_property.get('lotSize') if rentcast_property else 'Unknown',
            'condition': rentcast_property.get('condition') if rentcast_property else 'Unknown',
            'property_type': rentcast_property.get('propertyType') if rentcast_property else 'Single Family Residential'
        }
        
        return render_template('presentation.html', property=property_data)
    
    except Exception as e:
        logging.error(f"Error generating presentation: {str(e)}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        return render_template('index.html', error="Unable to fetch property data. Please verify the address and try again.")

@app.route('/api/share/<path:data>')
def share_link(data):
    """Generate shareable link for property presentation"""
    try:
        # In a real app, you'd store this in a database
        # For now, we'll just return the data as JSON
        return jsonify({'success': True, 'share_url': request.url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
