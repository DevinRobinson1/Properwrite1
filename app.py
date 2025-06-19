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

def calculate_financials(buy_price, sqft, beds, baths):
    """Calculate property financials with realistic estimates"""
    if not buy_price:
        buy_price = random.randint(180000, 350000)
    
    # ARV calculation (typically 1.2-1.4x of buy price for flips)
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
        'profit_margin': round((net_profit / buy_price) * 100, 1)
    }

def generate_comparables(beds, baths, sqft, city):
    """Generate realistic comparable sales data"""
    comparables = []
    base_price_per_sqft = random.randint(200, 280)
    
    for i in range(4):
        # Vary square footage by ±500
        comp_sqft = sqft + random.randint(-300, 300)
        if comp_sqft < 800:
            comp_sqft = 800
            
        # Calculate price based on sqft with some variation
        price_per_sqft = base_price_per_sqft + random.randint(-20, 20)
        price = comp_sqft * price_per_sqft
        
        # Random address
        street_num = random.randint(100, 9999)
        street_names = ['Elm St', 'Oak Ave', 'Pine Dr', 'Maple Ln', 'Cedar Way', 'Birch Ct']
        address = f"{street_num} {random.choice(street_names)}"
        
        # Sold date within last 6 months
        days_ago = random.randint(30, 180)
        sold_date = (datetime.now() - timedelta(days=days_ago)).strftime('%b %Y')
        
        # Vary beds/baths slightly
        comp_beds = beds + random.randint(-1, 1)
        comp_baths = baths + random.randint(-1, 1)
        if comp_beds < 1:
            comp_beds = 1
        if comp_baths < 1:
            comp_baths = 1
            
        comparables.append({
            'address': address,
            'beds': comp_beds,
            'baths': comp_baths,
            'sqft': comp_sqft,
            'price': price,
            'sold_date': sold_date,
            'price_per_sqft': price_per_sqft
        })
    
    return sorted(comparables, key=lambda x: x['price'], reverse=True)

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
        financials = calculate_financials(buy_price, sqft, beds, baths)
        summary = generate_property_summary(address, city, financials)
        comparables = generate_comparables(beds, baths, sqft, city)
        
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
