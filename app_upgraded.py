"""
Upgraded Real Estate Investment Analyzer
Enhanced with external data pulling, cleaner UI, and comprehensive strategy comparison
"""
import os
import logging
from flask import Flask, render_template, request, jsonify, session
from property_data_service import property_service
from wholesale_calculator import calculate_wholesale_offers
from installment_calculator import calculate_installment_offers
from subject_to_calculator import calculate_subject_to_offer
from seller_finance_calculator import calculate_seller_finance_offer

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-2024")

@app.route('/')
def index():
    """Enhanced property input form with external data integration"""
    return render_template('index_upgraded.html')

@app.route('/api/analyze-property', methods=['POST'])
def analyze_property():
    """
    Analyze property with external data enrichment from multiple sources
    Pulls data from Zillow, Redfin, Realtor.com and other sources
    """
    try:
        data = request.get_json()
        address = data.get('address', '').strip()
        city = data.get('city', '').strip()
        state = data.get('state', '').strip()
        zip_code = data.get('zip', '').strip()
        
        if not all([address, city, state, zip_code]):
            return jsonify({
                'success': False,
                'error': 'Please provide complete address information'
            }), 400
        
        # Initialize property data with defaults
        property_data = {
            'address': address,
            'city': city,
            'state': state,
            'zip': zip_code,
            'bedrooms': 3,
            'bathrooms': 2.0,
            'square_feet': 1200,
            'year_built': 1995,
            'property_type': 'Single Family',
            'data_sources': ['Manual Input'],
            'images': []
        }
        
        # Try to get external data but don't fail if unavailable
        try:
            external_data = property_service.get_property_data(address, city, state, zip_code)
            if external_data:
                # Only update with non-None values
                for key, value in external_data.items():
                    if value is not None and value != '':
                        property_data[key] = value
        except Exception as e:
            logging.warning(f"External data unavailable: {e}")
        
        # Generate estimates for missing values
        if not property_data.get('estimated_value'):
            property_data['estimated_value'] = estimate_property_value(
                property_data.get('square_feet', 1200),
                property_data.get('bedrooms', 3),
                property_data.get('bathrooms', 2),
                city, state
            )
        
        if not property_data.get('rent_estimate'):
            property_data['rent_estimate'] = estimate_monthly_rent(
                property_data.get('square_feet', 1200),
                property_data.get('bedrooms', 3),
                property_data.get('bathrooms', 2),
                city, state
            )
        
        # Store in session for later use
        session['current_property'] = property_data
        
        return jsonify({
            'success': True,
            **property_data
        })
        
    except Exception as e:
        logging.error(f"Property analysis error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze property. Please check the address and try again.'
        }), 500

@app.route('/api/calculate-strategies', methods=['POST'])
def calculate_strategies():
    """
    Calculate all offer strategies with current property inputs
    Returns comprehensive analysis for all four strategies
    """
    try:
        data = request.get_json()
        
        # Extract property inputs
        arv = float(data.get('arv', 200000))
        repairs = float(data.get('repairs', 30000))
        bedrooms = int(data.get('bedrooms', 3))
        bathrooms = float(data.get('bathrooms', 2))
        square_feet = int(data.get('square_feet', 1200))
        monthly_rent = float(data.get('rent', 2000))
        
        # Validate inputs
        if arv < 50000 or arv > 5000000:
            return jsonify({'error': 'ARV must be between $50,000 and $5,000,000'}), 400
        
        if repairs < 0 or repairs > arv * 0.5:
            return jsonify({'error': 'Repairs cannot exceed 50% of ARV'}), 400
        
        # Calculate wholesale strategy
        wholesale_analysis = calculate_wholesale_offers(
            arv=arv,
            repairs=repairs,
            wholesale_arv_percent=0.70,
            min_acceptable_profit=int(15000)
        )
        
        # Calculate installment strategy  
        installment_analysis = calculate_installment_offers(
            arv=arv,
            estimated_repairs=repairs,
            discount_to_sell_fast=int(10000),
            buyer_over_ask_bonus=int(5000),
            min_acceptable_profit=int(25000)
        )
        
        # Calculate subject-to strategy
        estimated_loan_balance = arv * 0.75  # Assume 75% LTV
        subject_to_analysis = calculate_subject_to_offer(
            arv=arv,
            principal_balance=int(estimated_loan_balance),
            purchase_price=4000,  # Cash to seller
            cash_to_seller=4000,
            monthly_pi=int(estimated_loan_balance * 0.006),  # Estimate monthly payment
            rent_income=int(monthly_rent),
            rehab=int(repairs)
        )
        
        # Calculate seller finance strategy
        seller_finance_analysis = calculate_seller_finance_offer(
            arv=arv,
            seller_finance_purchase_price=arv * 0.95,  # 95% of ARV
            down_payment=15000,
            interest_rate=6.5,
            monthly_rent=int(monthly_rent),
            rehab_budget=int(repairs)
        )
        
        # Compile comprehensive results
        results = {
            'wholesale': {
                'wholesale_mao': wholesale_analysis.get('wholesale_mao', 0),
                'assignment_profit': wholesale_analysis.get('assignment_profit', 0),
                'ackerman_offers': wholesale_analysis.get('ackerman_offers', []),
                'all_in_amount': wholesale_analysis.get('all_in_amount', 0),
                'strategy_type': 'Cash Acquisition'
            },
            'installment': {
                'installment_mao': installment_analysis.get('installment_mao', 0),
                'net_profit': installment_analysis.get('net_profit', 0),
                'final_sales_price': installment_analysis.get('final_sales_price', 0),
                'installment_vs_wholesale_gap': installment_analysis.get('installment_vs_wholesale_gap', 0),
                'strategy_type': 'Payment Plan'
            },
            'subject_to': {
                'equity_position': subject_to_analysis.get('immediate_equity', 0),
                'monthly_payment': subject_to_analysis.get('monthly_pi', 0),
                'monthly_cash_flow': subject_to_analysis.get('monthly_cash_flow', 0),
                'total_cash_needed': subject_to_analysis.get('total_cash_needed', 0),
                'strategy_type': 'Creative Financing'
            },
            'seller_finance': {
                'purchase_price': seller_finance_analysis.get('purchase_price', 0),
                'down_payment': seller_finance_analysis.get('down_payment', 0),
                'monthly_payment': seller_finance_analysis.get('monthly_payment', 0),
                'monthly_cash_flow': seller_finance_analysis.get('monthly_cash_flow', 0),
                'interest_rate': seller_finance_analysis.get('interest_rate', 6.5),
                'strategy_type': 'Owner Financing'
            }
        }
        
        # Store results in session
        session['calculation_results'] = results
        
        return jsonify(results)
        
    except Exception as e:
        logging.error(f"Strategy calculation error: {e}")
        return jsonify({
            'error': 'Failed to calculate strategies. Please check your inputs and try again.'
        }), 500

@app.route('/api/update-strategy', methods=['POST'])
def update_strategy():
    """
    Update specific strategy calculations with new parameters
    """
    try:
        data = request.get_json()
        strategy_type = data.get('strategy', '')
        
        current_property = session.get('current_property', {})
        if not current_property:
            return jsonify({'error': 'No property data found. Please analyze a property first.'}), 400
        
        arv = float(data.get('arv', current_property.get('estimated_value', 200000)))
        repairs = float(data.get('repairs', 30000))
        
        if strategy_type == 'wholesale':
            wholesale_percent = float(data.get('wholesale_percentage', 0.70))
            min_profit = float(data.get('min_profit', 15000))
            
            result = calculate_wholesale_offers(
                arv=arv,
                repairs=repairs,
                wholesale_arv_percent=wholesale_percent,
                min_acceptable_profit=int(min_profit)
            )
            
        elif strategy_type == 'installment':
            discount_fast = float(data.get('discount_to_sell_fast', 10000))
            buyer_bonus = float(data.get('buyer_over_ask_bonus', 5000))
            
            result = calculate_installment_offers(
                arv=arv,
                estimated_repairs=repairs,
                discount_to_sell_fast=int(discount_fast),
                buyer_over_ask_bonus=int(buyer_bonus)
            )
            
        else:
            return jsonify({'error': 'Invalid strategy type'}), 400
        
        return jsonify({
            'success': True,
            'strategy': strategy_type,
            'results': result
        })
        
    except Exception as e:
        logging.error(f"Strategy update error: {e}")
        return jsonify({'error': 'Failed to update strategy calculations'}), 500

def estimate_property_value(square_feet, bedrooms, bathrooms, city, state):
    """
    Estimate property value based on size and location when external data unavailable
    """
    # Base price per square foot by state (conservative estimates)
    state_rates = {
        'NC': 120, 'SC': 110, 'GA': 125, 'TN': 115, 'FL': 140, 'VA': 150
    }
    
    base_rate = state_rates.get(state, 120)
    
    # Adjust for bedrooms and bathrooms
    bedroom_multiplier = 1 + (bedrooms - 3) * 0.05
    bathroom_multiplier = 1 + (bathrooms - 2) * 0.03
    
    estimated_value = square_feet * base_rate * bedroom_multiplier * bathroom_multiplier
    
    # Round to nearest $5,000
    return round(estimated_value / 5000) * 5000

def estimate_monthly_rent(square_feet, bedrooms, bathrooms, city, state):
    """
    Estimate monthly rent based on property characteristics and location
    """
    # Base rent per square foot by state
    state_rent_rates = {
        'NC': 1.1, 'SC': 1.0, 'GA': 1.2, 'TN': 1.0, 'FL': 1.4, 'VA': 1.3
    }
    
    base_rate = state_rent_rates.get(state, 1.1)
    
    # Calculate base rent
    base_rent = square_feet * base_rate
    
    # Adjust for bedrooms (minimum rent thresholds)
    min_rent_by_bedrooms = {1: 800, 2: 1000, 3: 1200, 4: 1500, 5: 1800}
    min_rent = min_rent_by_bedrooms.get(bedrooms, 1200)
    
    estimated_rent = max(base_rent, min_rent)
    
    # Round to nearest $25
    return round(estimated_rent / 25) * 25

@app.route('/presentation/<share_id>')
def view_shared_presentation(share_id):
    """
    View shared property presentation
    """
    try:
        # In a production app, this would fetch from database
        # For now, return to main page
        return render_template('index_upgraded.html')
    except Exception as e:
        logging.error(f"Shared presentation error: {e}")
        return "Presentation not found", 404

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index_upgraded.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)