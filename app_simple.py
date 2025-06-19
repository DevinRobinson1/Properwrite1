import os
import logging
from flask import Flask, render_template, request, session, jsonify
from offer_calculator import generate_offer_comparison, get_strategy_recommendation
from wholesale_calculator import calculate_wholesale_offers, calculate_ackerman_sequence, validate_wholesale_deal
from installment_calculator import (
    calculate_installment_offers, validate_installment_deal, get_seller_psychology_framework,
    get_default_installment_fees, validate_installment_fees, get_fee_tooltips
)
from subject_to_calculator import (
    calculate_subject_to_offer, validate_subject_to_deal, get_subject_to_strategies,
    calculate_refinance_scenario
)

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
        
        # Generate offer strategies using ARV and enhanced calculations
        offer_analysis = generate_offer_comparison(
            arv=estimated_value,
            repair_cost=30000,  # Using reference repair cost
            existing_loan=120000,  # Sample existing loan for demo
            monthly_payment=850,  # Sample monthly payment
            interest_rate=0.045,  # Sample interest rate
            asking_price=int(buy_price) if buy_price > 0 else 0
        )
        
        # Get strategy recommendations
        recommendations = get_strategy_recommendation(offer_analysis['offers'])
        
        # Generate wholesale/cash offer analysis with Ackerman Method
        wholesale_analysis = calculate_wholesale_offers(
            arv=estimated_value,
            repairs=30000,
            wholesale_arv_percent=0.70,
            min_acceptable_profit=15000
        )
        
        # Generate Ackerman sequence
        ackerman_offers = calculate_ackerman_sequence(wholesale_analysis['wholesale_mao'])
        
        # Validate wholesale deal
        wholesale_validations = validate_wholesale_deal(wholesale_analysis)
        
        # Generate installment offer analysis
        installment_analysis = calculate_installment_offers(
            arv=estimated_value,
            estimated_repairs=30000,
            discount_to_sell_fast=10000,
            closing_costs=18400,
            min_acceptable_profit=15000,
            wholesale_mao=wholesale_analysis['wholesale_mao']
        )
        
        # Validate installment deal
        installment_validations = validate_installment_deal(installment_analysis)
        
        # Get seller psychology framework for tooltips
        seller_psychology = get_seller_psychology_framework()
        
        # Get default fee structure and tooltips
        default_fees = get_default_installment_fees()
        fee_tooltips = get_fee_tooltips()
        
        # Generate Subject-To offer analysis
        subject_to_analysis = calculate_subject_to_offer(
            arv=estimated_value,
            principal_balance=estimated_value * 0.85,  # Assume 85% LTV existing loan
            purchase_price=estimated_value * 0.85,
            rent_income=estimated_value * 0.007,  # 0.7% rent ratio
            lease_option_income=estimated_value * 0.0075,  # Slightly higher for lease option
            lease_option_sale_price=estimated_value * 1.1  # 10% premium for lease option
        )
        
        # Validate Subject-To deal
        subject_to_validations = validate_subject_to_deal(subject_to_analysis)
        
        # Get Subject-To strategies
        subject_to_strategies = get_subject_to_strategies()
        
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
            'recommendations': recommendations,
            'wholesale_analysis': wholesale_analysis,
            'ackerman_offers': ackerman_offers,
            'wholesale_validations': wholesale_validations,
            'installment_analysis': installment_analysis,
            'installment_validations': installment_validations,
            'seller_psychology': seller_psychology,
            'default_fees': default_fees,
            'fee_tooltips': fee_tooltips
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
                             recommendations=recommendations,
                             wholesale_analysis=wholesale_analysis,
                             ackerman_offers=ackerman_offers,
                             wholesale_validations=wholesale_validations,
                             installment_analysis=installment_analysis,
                             installment_validations=installment_validations,
                             seller_psychology=seller_psychology,
                             default_fees=default_fees,
                             fee_tooltips=fee_tooltips)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return f"<h1>Processing Error</h1><p>Unable to process request: {str(e)}</p>", 500

@app.route('/api/calculate-wholesale', methods=['POST'])
def calculate_wholesale():
    """API endpoint for wholesale/cash offer calculations with Ackerman Method"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        arv = data.get('arv', 0)
        repairs = data.get('repairs', 30000)
        wholesale_percent = data.get('wholesale_percent', 70) / 100
        min_profit = data.get('min_profit', 15000)
        negative_adj = data.get('negative_adjustments', 0)
        positive_adj = data.get('positive_adjustments', 0)
        
        wholesale_analysis = calculate_wholesale_offers(
            arv=arv,
            repairs=repairs,
            wholesale_arv_percent=wholesale_percent,
            negative_adjustments=negative_adj,
            positive_adjustments=positive_adj,
            min_acceptable_profit=min_profit
        )
        
        ackerman_offers = calculate_ackerman_sequence(wholesale_analysis['wholesale_mao'])
        validations = validate_wholesale_deal(wholesale_analysis)
        
        return jsonify({
            'success': True,
            'wholesale_analysis': wholesale_analysis,
            'ackerman_offers': ackerman_offers,
            'validations': validations
        })
        
    except Exception as e:
        logging.error(f"Wholesale calculation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calculate-installment', methods=['POST'])
def calculate_installment():
    """API endpoint for installment offer calculations"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        arv = data.get('arv', 0)
        estimated_repairs = data.get('estimated_repairs', 30000)
        negative_adj = data.get('negative_adjustments', 0)
        positive_adj = data.get('positive_adjustments', 0)
        discount_fast = data.get('discount_to_sell_fast', 10000)
        buyer_bonus = data.get('buyer_over_ask_bonus', 0)
        closing_costs = data.get('closing_costs', 18400)
        min_profit = data.get('min_acceptable_profit', 15000)
        seller_bonus = data.get('split_with_seller_bonus', 0)
        wholesale_mao = data.get('wholesale_mao', 0)
        
        installment_analysis = calculate_installment_offers(
            arv=arv,
            estimated_repairs=estimated_repairs,
            negative_adjustments=negative_adj,
            positive_adjustments=positive_adj,
            discount_to_sell_fast=discount_fast,
            buyer_over_ask_bonus=buyer_bonus,
            closing_costs=closing_costs,
            min_acceptable_profit=min_profit,
            split_with_seller_bonus=seller_bonus,
            wholesale_mao=wholesale_mao
        )
        
        validations = validate_installment_deal(installment_analysis)
        psychology = get_seller_psychology_framework()
        
        return jsonify({
            'success': True,
            'installment_analysis': installment_analysis,
            'validations': validations,
            'seller_psychology': psychology
        })
        
    except Exception as e:
        logging.error(f"Installment calculation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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