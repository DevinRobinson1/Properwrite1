import os
import random
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, url_for
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

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
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_presentation():
    try:
        # Get form data
        data = request.form
        address = data.get('address', '').strip()
        city = data.get('city', '').strip()
        state = data.get('state', '').strip()
        zip_code = data.get('zip', '').strip()
        beds = int(data.get('beds', 3))
        baths = int(data.get('baths', 2))
        sqft = int(data.get('sqft', 1400))
        buy_price = data.get('buy_price', '').strip()
        
        # Convert buy_price to int if provided
        if buy_price:
            buy_price = int(buy_price.replace(',', '').replace('$', ''))
        else:
            buy_price = None
            
        # Generate property analysis
        title = generate_property_title(address, city, beds, baths)
        comparables = generate_comparables(beds, baths, sqft, city)
        financials = calculate_financials(buy_price, sqft, beds, baths, comparables)
        summary = generate_property_summary(address, city, financials)
        
        # Property details
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
            'schools': MOCK_SCHOOLS,
            'amenities': random.sample(MOCK_AMENITIES, 4),
            'year_built': random.randint(1980, 2015),
            'lot_size': f"{random.uniform(0.15, 0.35):.2f} acres",
            'condition': random.choice(['Good', 'Fair', 'Needs Updates']),
            'property_type': 'Single Family Residential'
        }
        
        return render_template('presentation.html', property=property_data)
    
    except Exception as e:
        logging.error(f"Error generating presentation: {str(e)}")
        return render_template('index.html', error="Please fill in all required fields with valid values.")

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
