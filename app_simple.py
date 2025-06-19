import os
import logging
from flask import Flask, render_template, request, session, jsonify
from offer_calculator import generate_offer_comparison, get_strategy_recommendation

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-12345")

# Simple property analyzer without external APIs

@app.route('/')
def index():
    return render_template('index.html', google_maps_api_key=os.environ.get('GOOGLE_API_KEY'))

@app.route('/generate', methods=['POST'])
def generate_presentation():
    try:
        # Get form data
        data = request.form
        address = data.get('address', '').strip()
        city = data.get('city', '').strip()
        state = data.get('state', '').strip()
        zip_code = data.get('zip', '').strip()
        
        # Validate required fields
        if not all([address, city, state, zip_code]):
            return "<h1>Missing Information</h1><p>Please provide address, city, state, and ZIP code.</p>", 400
        
        # Get property details with defaults
        try:
            beds = int(data.get('beds') or 3)
            baths = float(data.get('baths') or 2.0)
            sqft = int(data.get('sqft') or 1400)
            buy_price = float(data.get('buy_price', 0) or 0)
        except (ValueError, TypeError):
            beds, baths, sqft, buy_price = 3, 2.0, 1400, 0
        
        logging.info(f"Processing: {address}, {city}, {state} {zip_code}")
        
        # Property data structure with user inputs only
        property_data = {
            'formattedAddress': f"{address}, {city}, {state} {zip_code}",
            'bedrooms': beds,
            'bathrooms': baths,
            'squareFootage': sqft,
            'propertyType': 'Property Analysis'
        }
        
        # Market data based on property characteristics
        market_data = {
            'rent_estimate': sqft * 1.2,
            'property_value_estimate': sqft * 150,
            'neighborhood': f"{city}, {state}"
        }
        
        # Financial calculations based on property specs
        estimated_value = sqft * 150
        monthly_rent = sqft * 1.2
        
        financials = {
            'arv': estimated_value,
            'monthly_rent': monthly_rent,
            'annual_rent': monthly_rent * 12,
            'estimated_value': estimated_value
        }
        
        if buy_price > 0:
            financials.update({
                'buy_price': buy_price,
                'cap_rate': (monthly_rent * 12) / buy_price * 100 if buy_price > 0 else 0,
                'cash_flow': monthly_rent * 0.7 - (buy_price * 0.005),
                'roi': ((monthly_rent * 12 * 0.7) / (buy_price * 0.25)) * 100 if buy_price > 0 else 0
            })
        
        # Simple comparable data
        comparables = []
        
        # Analysis methods used
        data_sources = {
            'Property Analysis': 'Based on user-provided specifications',
            'Market Calculations': 'Using standard real estate formulas',
            'Investment Metrics': 'Calculated from property characteristics'
        }
        
        # Generate presentation content
        property_title = f"🏠 {beds}BR/{baths}BA Property in {city}"
        property_summary = f"Property analysis for {address} in {city}, {state}. {beds} bedrooms, {baths} bathrooms, {sqft:,} square feet."
        
        # Generate offer strategies using ARV
        offer_analysis = generate_offer_comparison(
            arv=estimated_value,
            repair_cost=20000,  # Default repair estimate
            existing_loan=0,    # Can be updated if provided
            monthly_payment=0,  # Can be updated if provided
            asking_price=int(buy_price) if buy_price > 0 else 0
        )
        
        # Get strategy recommendations
        recommendations = get_strategy_recommendation(offer_analysis['offers'])
        
        # Store in session
        session['property_data'] = {
            'address': address,
            'city': city,
            'state': state,
            'zip': zip_code,
            'beds': beds,
            'baths': baths,
            'sqft': sqft,
            'property_title': property_title,
            'property_summary': property_summary,
            'property_data': property_data,
            'financials': financials,
            'comparables': comparables,
            'market_data': market_data,
            'data_sources': data_sources,
            'offer_analysis': offer_analysis,
            'recommendations': recommendations
        }
        
        return render_template('presentation_simple.html',
                             address=address,
                             city=city,
                             state=state,
                             zip=zip_code,
                             beds=beds,
                             baths=baths,
                             sqft=sqft,
                             property_title=property_title,
                             property_summary=property_summary,
                             property_data=property_data,
                             financials=financials,
                             comparables=comparables,
                             market_data=market_data,
                             data_sources=data_sources,
                             offer_analysis=offer_analysis,
                             recommendations=recommendations)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return f"<h1>Processing Error</h1><p>Unable to process request: {str(e)}</p>", 500

@app.route('/api/calculate-offers', methods=['POST'])
def calculate_offers():
    """API endpoint for calculating offer strategies"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        arv = data.get('arv', 0)
        repair_cost = data.get('repair_cost', 20000)
        existing_loan = data.get('existing_loan', 0)
        monthly_payment = data.get('monthly_payment', 0)
        
        offer_analysis = generate_offer_comparison(
            arv=arv,
            repair_cost=repair_cost,
            existing_loan=existing_loan,
            monthly_payment=monthly_payment
        )
        
        recommendations = get_strategy_recommendation(offer_analysis['offers'])
        
        return jsonify({
            'success': True,
            'offers': offer_analysis['offers'],
            'recommendations': recommendations,
            'summary': offer_analysis['summary']
        })
        
    except Exception as e:
        logging.error(f"Offer calculation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/share/<data>')
def share_link(data):
    """Generate shareable link for property presentation"""
    try:
        import base64
        import json
        
        # Decode the shared data
        decoded_data = json.loads(base64.b64decode(data.encode()).decode())
        
        return render_template('presentation_simple.html', **decoded_data)
        
    except Exception as e:
        return f"<h1>Invalid Share Link</h1><p>Unable to load shared presentation.</p>", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)