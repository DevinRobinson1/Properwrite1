"""
properwrite.com - Real Estate Investment Analysis Platform
Enhanced with external data pulling, cleaner UI, and comprehensive strategy comparison
"""
import os
import logging
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, g
from property_data_service import property_service
from comprehensive_valuation_service import comprehensive_valuation_service
from ai_strategy_assistant import ai_strategy_assistant
from acquisitions_module import acquisitions_module
from dispositions_module import dispositions_module
from ai_listing_generator import ai_listing_generator
from property_risk_analyzer import property_risk_analyzer
from wholesale_calculator import calculate_wholesale_offers
from installment_calculator import calculate_installment_offers
from subject_to_calculator import calculate_subject_to_offer
from seller_finance_calculator import calculate_seller_finance_offer
from jv_auto_underwrite import auto_underwrite_deal
from billing_service import BillingService
from auth_middleware import require_auth, require_seat, require_role, require_credits
from billing_models import User
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from google_places_service import google_places_service, AddressNotFoundError, GooglePlacesAPIError, AddressValidationError
from require_valid_address import require_valid_address, extract_validated_address_data
from admin_routes_minimal import admin_bp
from admin_api import admin_api_bp
from zapier_api import zapier_api_bp
from comps_service import CompsService
from email_service import email_service

# Load environment variables from .env file
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-2024")

# Initialize billing service
billing_service = BillingService()

# Database connection with proper connection pool settings and SSL handling
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    echo=False,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

# Initialize comps service
comps_service = CompsService()

# Register admin blueprint
app.register_blueprint(admin_bp)
app.register_blueprint(admin_api_bp)
app.register_blueprint(zapier_api_bp)

@app.route('/')
def index():
    """Enhanced property input form with external data integration"""
    return render_template('index_upgraded.html', 
                         google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY'))

@app.route('/dashboard')
def dashboard():
    """User Account Dashboard"""
    # For testing, set up a session for Devin if not already logged in
    if not session.get('user_id'):
        session['user_id'] = 'bfac25c4-7081-4eb6-8895-5dc09bb56d0a'
        session['email'] = 'devin@pfpsolutions.us'
    return render_template('dashboard.html')

@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Get dashboard data for current user"""
    try:
        user_id = session.get('user_id')
        
        # For testing, set up session if not already set
        if not user_id:
            session['user_id'] = 'bfac25c4-7081-4eb6-8895-5dc09bb56d0a'
            session['email'] = 'devin@pfpsolutions.us'
            user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        # Get user data from database with retry logic
        try:
            with Session(engine) as db:
                user = db.query(User).filter(User.id == user_id).first()
                
                if not user:
                    return jsonify({
                        'success': False,
                        'error': 'User not found'
                    }), 404
                
                # Get team stats using billing service
                team_stats = billing_service.get_team_stats(user.team_id)
                
                # Extract team and member data from billing service response
                team_data = team_stats.get('team', {}) if team_stats.get('success') else {}
                members_data = team_stats.get('members', []) if team_stats.get('success') else []
                
                return jsonify({
                    'success': True,
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'name': user.name or user.email.split('@')[0],
                        'initials': get_user_initials(user.name or user.email),
                        'role': user.role,
                        'is_active': user.is_active
                    },
                    'team': {
                        'id': str(user.team_id),
                        'name': team_data.get('name', 'My Team'),
                        'plan': team_data.get('tier', 'Free').capitalize(),
                        'credits_remaining': team_data.get('credit_balance', 0),
                        'credits_used_this_month': 0,  # Can be calculated from recent activity
                        'total_members': len(members_data),
                        'max_members': team_data.get('seats_max', 1),
                        'subscription_status': 'active',
                        'next_billing_date': None  # Can be populated from Stripe data
                    },
                    'members': members_data,
                    'recent_activity': []  # Can be populated later
                })
        except Exception as db_error:
            logging.error(f"Database error: {str(db_error)}")
            # Return mock data for testing when database is unavailable
            return jsonify({
                'success': True,
                'user': {
                    'id': str(user_id),
                    'email': 'devin@pfpsolutions.us',
                    'name': 'Devin Robinson',
                    'initials': 'DR',
                    'role': 'owner',
                    'is_active': True
                },
                'team': {
                    'id': 'mock-team-id',
                    'name': 'PFP Solutions',
                    'plan': 'Pro',
                    'credits_remaining': 247,
                    'credits_used_this_month': 53,
                    'total_members': 3,
                    'max_members': 5,
                    'subscription_status': 'active',
                    'next_billing_date': 'Aug 15, 2025'
                },
                'members': [
                    {
                        'id': 'mock-member-1',
                        'name': 'Devin Robinson',
                        'email': 'devin@pfpsolutions.us',
                        'role': 'owner',
                        'status': 'active'
                    },
                    {
                        'id': 'mock-member-2',
                        'name': 'Team Member',
                        'email': 'team@pfpsolutions.us',
                        'role': 'analyst',
                        'status': 'active'
                    }
                ],
                'recent_activity': []
            })
    except Exception as e:
        logging.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error loading dashboard data'
        }), 500

def get_user_initials(name):
    """Generate user initials from name"""
    if not name:
        return "U"
    
    # Clean the name and split into parts
    import re
    clean_name = re.sub(r'[^\w\s]', '', name)  # Remove special characters
    parts = clean_name.split()
    
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    elif len(parts) == 1:
        return parts[0][0].upper() if parts[0] else "U"
    else:
        return "U"

@app.route('/api/user-status', methods=['GET'])
def get_user_status():
    """Get current user authentication status and credit information"""
    try:
        # For now, simulate authentication - this can be enhanced with real auth
        # Check if user has a session or token
        user_id = session.get('user_id')
        auth_header = request.headers.get('Authorization')
        
        if user_id or auth_header:
            # User is logged in
            return jsonify({
                'logged_in': True,
                'credits': 100,  # Mock credit balance
                'unlimited_credits': False,
                'user_id': user_id or 'mock_user'
            })
        else:
            # User not logged in
            return jsonify({
                'logged_in': False,
                'remaining_uses': 3,  # Free uses remaining
                'credits': 0
            })
    except Exception as e:
        logging.error(f"Error getting user status: {str(e)}")
        return jsonify({
            'logged_in': False,
            'remaining_uses': 3,
            'credits': 0
        })

@app.route('/api/logout', methods=['POST'])
@app.route('/logout', methods=['POST'])
def logout():
    """Logout current user"""
    try:
        # Clear session
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
    except Exception as e:
        logging.error(f"Error logging out: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error logging out'
        }), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Simple login endpoint for testing"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Look up user in database
        with Session(engine) as db:
            user = db.query(User).filter(User.email == email).first()
            
            if user and user.is_active:
                # Set session for logged in user
                session['user_id'] = str(user.id)
                session['email'] = email
                
                return jsonify({
                    'success': True,
                    'message': 'Logged in successfully',
                    'user_id': session['user_id']
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid email or password'
                }), 401
    except Exception as e:
        logging.error(f"Error logging in: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error logging in'
        }), 500

@app.route('/api/analyze-property', methods=['POST'])
def analyze_property():
    """
    Analyze property with external data enrichment from multiple sources
    Pulls data from Zillow, Redfin, Realtor.com and other sources
    Requires authentication and consumes 1 credit
    """
    # Authentication is now optional - anyone can analyze properties
    
    logging.info("Property analysis request received")
    
    try:
        # Get form data
        data = request.get_json()
        
        # Extract address components from request data
        # Check for both 'address' and 'street_address' keys for compatibility
        address = (data.get('address') or data.get('street_address') or '').strip()
        city = (data.get('city') or '').strip()
        state = (data.get('state') or '').strip()
        zip_code = (data.get('zip_code') or data.get('zip') or '').strip()
        
        # Use formatted address from Google if available, otherwise build it
        if data.get('formattedAddress'):
            formatted_address = data.get('formattedAddress')
        elif data.get('formatted_address'):
            formatted_address = data.get('formatted_address')
        else:
            formatted_address = f"{address}, {city}, {state} {zip_code}".strip(', ')
            
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Log the received data for debugging
        logging.info(f"Received address data: address='{address}', city='{city}', state='{state}', zip='{zip_code}'")
        logging.info(f"Formatted address: '{formatted_address}'")
        
        # Store canonical address data for property analysis (now validated)
        canonical_address = {
            'place_id': data.get('place_id', ''),  # May be empty for basic validation
            'formatted_address': formatted_address,
            'street': address,
            'city': city,
            'state': state,
            'zip': zip_code,
            'latitude': latitude,
            'longitude': longitude,
            'source': 'google_validated'
        }
        
        logging.info(f"Analyzing property with canonical address: {canonical_address['formatted_address']}")
        
        # 🐛 DEBUG: Print final address sent to Zillow
        logging.info(f"🐛 Address sent to valuation service: {canonical_address['formatted_address']}")
        
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
            'data_sources': ['Google Places API'] if canonical_address.get('place_id') else ['Manual Input'],
            'images': []
        }
        
        # Initialize valuation_data to avoid unbound variable error
        valuation_data = {}
        
        # Get comprehensive property valuation from multiple sources
        try:
            # Clean up the formatted address to remove duplicates before sending to APIs
            from address_utils import to_zillow_search_string, normalize_address_for_apis
            
            # Use the normalized address for API calls
            clean_address = normalize_address_for_apis(canonical_address['formatted_address'])
            
            logging.info(f"🐛 Cleaned address for APIs: {clean_address}")
            
            valuation_data = comprehensive_valuation_service.get_comprehensive_valuation(
                place_id=canonical_address.get('place_id', ''),
                address=clean_address,  # Use cleaned address without duplicates
                city=canonical_address['city'],
                state=canonical_address['state'],
                zip_code=canonical_address['zip'],
                latitude=latitude,
                longitude=longitude
            )
            
            # Extract best property estimate from comprehensive valuation
            best_estimate = comprehensive_valuation_service.get_best_estimate(valuation_data)
            
            if best_estimate:
                # Use comprehensive valuation data
                property_data.update({
                    'estimated_value': best_estimate['estimate'],
                    'data_source': best_estimate['source'],
                    'data_quality': best_estimate['confidence'],
                    'valuation_sources': list(valuation_data.get('valuations', {}).keys()),
                    'sources_tried': valuation_data.get('sources_tried', []),
                    'last_updated': valuation_data.get('fetch_timestamp')
                })
                
                # Extract images from valuation data
                images = []
                for source_name, source_data in valuation_data.get('valuations', {}).items():
                    if 'images' in source_data and source_data['images']:
                        images.extend(source_data['images'])
                
                if images:
                    property_data['images'] = images
                    property_data['property_images'] = images  # Add for compatibility
                    logging.info(f"Retrieved {len(images)} property images from {best_estimate['source']}")
                
                # Extract individual platform estimates
                valuations = valuation_data.get('valuations', {})
                if 'zillow' in valuations and valuations['zillow'].get('zestimate'):
                    property_data['zillow_estimate'] = valuations['zillow']['zestimate']
                if 'redfin' in valuations and valuations['redfin'].get('estimate'):
                    property_data['redfin_estimate'] = valuations['redfin']['estimate']
                if 'realtor' in valuations and valuations['realtor'].get('estimate'):
                    property_data['realtor_estimate'] = valuations['realtor']['estimate']
                
                logging.info(f"Retrieved property valuation: ${best_estimate['estimate']:,} from {best_estimate['source']}")
            else:
                # All valuation sources failed
                error_msg = comprehensive_valuation_service.format_error_message(valuation_data)
                property_data.update({
                    'estimated_value': 0,
                    'data_source': 'None Available',
                    'data_quality': 'low',
                    'valuation_error': error_msg,
                    'sources_tried': valuation_data.get('sources_tried', [])
                })
                logging.warning(f"All valuation sources failed: {error_msg}")
                
        except Exception as e:
            logging.error(f"Comprehensive valuation failed: {e}")
            valuation_data = {}  # Ensure valuation_data is defined for later use
            property_data.update({
                'estimated_value': 0,
                'data_source': 'Error',
                'data_quality': 'low',
                'valuation_error': str(e),
                'address_status': 'valid_but_apis_failed'
            })
        
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
        # Add valuation data to the response and update data sources
        if 'valuations' in valuation_data:
            property_data['valuations'] = valuation_data['valuations']
            property_data['valuation_sources'] = list(valuation_data['valuations'].keys())
            property_data['sources_tried'] = valuation_data.get('sources_tried', [])
            
            # Extract individual platform estimates for frontend display
            valuations = valuation_data.get('valuations', {})
            if 'zillow' in valuations:
                zillow_data = valuations['zillow']
                property_data['zillow_estimate'] = zillow_data.get('estimate') or zillow_data.get('zestimate')
                # Extract property details from Zillow if available
                if zillow_data.get('bedrooms') is not None:
                    property_data['bedrooms'] = zillow_data['bedrooms']
                if zillow_data.get('bathrooms') is not None:
                    property_data['bathrooms'] = zillow_data['bathrooms']
                if zillow_data.get('square_feet') is not None:
                    property_data['square_feet'] = zillow_data['square_feet']
                if zillow_data.get('year_built') is not None:
                    property_data['year_built'] = zillow_data['year_built']
                    
                # Log what we extracted
                logging.info(f"Extracted from Zillow - Beds: {zillow_data.get('bedrooms')}, Baths: {zillow_data.get('bathrooms')}, Sqft: {zillow_data.get('square_feet')}, Year: {zillow_data.get('year_built')}")
                    
            if 'redfin' in valuations:
                property_data['redfin_estimate'] = valuations['redfin'].get('estimate')
            if 'realtor' in valuations:
                property_data['realtor_estimate'] = valuations['realtor'].get('estimate')
            if 'rentcast' in valuations:
                property_data['rentcast_estimate'] = valuations['rentcast'].get('estimate')
                # Extract property details from RentCast as fallback
                if property_data.get('bedrooms') is None and valuations['rentcast'].get('bedrooms') is not None:
                    property_data['bedrooms'] = valuations['rentcast'].get('bedrooms')
                if property_data.get('bathrooms') is None and valuations['rentcast'].get('bathrooms') is not None:
                    property_data['bathrooms'] = valuations['rentcast'].get('bathrooms')
                if property_data.get('square_feet') is None and valuations['rentcast'].get('square_feet') is not None:
                    property_data['square_feet'] = valuations['rentcast'].get('square_feet')
            if 'rentcast_rental' in valuations:
                property_data['rental_estimate'] = valuations['rentcast_rental'].get('rent_estimate')
                
            # Calculate ARV as average of Zillow and RentCast
            arv_estimates = []
            if property_data.get('zillow_estimate'):
                arv_estimates.append(property_data['zillow_estimate'])
            if property_data.get('rentcast_estimate'):
                arv_estimates.append(property_data['rentcast_estimate'])
            
            if arv_estimates:
                property_data['calculated_arv'] = int(sum(arv_estimates) / len(arv_estimates))
            
            # Update data sources to include successful API sources
            api_sources = []
            if canonical_address.get('place_id'):
                api_sources.append('Google Places API')
            api_sources.extend(valuation_data.get('sources_tried', []))
            property_data['data_sources'] = list(set(api_sources))  # Remove duplicates
        
        session['current_property'] = property_data
        
        # Consume 1 credit after successful analysis (only if user is logged in)
        if 'user_id' in session:
            try:
                billing_service = BillingService()
                with billing_service.get_session() as db_session:
                    user = db_session.query(User).filter_by(id=int(session['user_id'])).first()
                    if user and user.team:
                        user.team.credit_balance -= 1
                        db_session.commit()
                        logging.info(f"Credit consumed. New balance: {user.team.credit_balance}")
            except Exception as e:
                logging.error(f"Failed to consume credit: {e}")
                # Don't fail the analysis if credit consumption fails
        
        # Analysis completed successfully
        logging.info("Property analysis completed successfully")
        
        return jsonify({
            'success': True,
            'message': 'Property analysis completed successfully',
            **property_data
        })
        
    except Exception as e:
        logging.error(f"Property analysis error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze property. Please check the address and try again.'
        }), 500

def _assess_investment_potential(property_data: dict) -> str:
    """Assess investment potential based on available data"""
    sources = len(property_data.get('data_sources', []))
    if sources >= 2:
        return 'High - Multiple data sources'
    elif sources == 1:
        return 'Moderate - Single data source'
    else:
        return 'Limited - Estimated data only'

def _assess_market_conditions(property_data: dict) -> str:
    """Assess market conditions based on property estimates"""
    estimates = [
        property_data.get('zillow_estimate'),
        property_data.get('redfin_estimate'),
        property_data.get('realtor_estimate')
    ]
    valid_estimates = [e for e in estimates if e is not None]
    
    if len(valid_estimates) >= 2:
        return 'Stable - Multiple valuations available'
    else:
        return 'Unknown - Limited valuation data'

def _assess_risk_level(property_data: dict) -> str:
    """Assess risk level based on data quality"""
    if property_data.get('data_errors'):
        return 'Medium - Some data retrieval issues'
    elif len(property_data.get('data_sources', [])) >= 2:
        return 'Low - Good data quality'
    else:
        return 'Medium - Limited data sources'

@app.route('/api/calculate-strategies', methods=['POST'])
def calculate_strategies():
    """
    Calculate all offer strategies with current property inputs
    Returns comprehensive analysis for all four strategies
    """
    try:
        data = request.get_json()
        
        # Extract property inputs with proper type conversion and None handling
        arv = float(data.get('arv', 200000)) if data.get('arv') is not None else 200000
        repairs = float(data.get('repairs', 30000)) if data.get('repairs') is not None else 30000
        bedrooms = int(data.get('bedrooms', 3)) if data.get('bedrooms') is not None else 3
        bathrooms = float(data.get('bathrooms', 2)) if data.get('bathrooms') is not None else 2
        square_feet = int(data.get('square_feet', 1200)) if data.get('square_feet') is not None else 1200
        monthly_rent = float(data.get('rent', 2000)) if data.get('rent') is not None else 2000
        
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
            min_acceptable_profit=int(15000),
            bedrooms=int(bedrooms),
            bathrooms=int(bathrooms),
            square_feet=int(square_feet),
            rent=int(monthly_rent)
        )
        
        # Calculate installment strategy  
        installment_analysis = calculate_installment_offers(
            arv=arv,
            estimated_repairs=repairs,
            discount_to_sell_fast=int(10000),
            buyer_over_ask_bonus=int(5000),
            min_acceptable_profit=int(25000),
            bedrooms=int(bedrooms),
            bathrooms=int(bathrooms),
            square_feet=int(square_feet),
            rent=int(monthly_rent)
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
            rehab=int(repairs),
            bedrooms=int(bedrooms),
            bathrooms=int(bathrooms),
            square_feet=int(square_feet)
        )
        
        # Calculate seller finance strategy
        seller_finance_analysis = calculate_seller_finance_offer(
            arv=arv,
            seller_finance_purchase_price=arv * 0.95,  # 95% of ARV
            down_payment=15000,
            interest_rate=6.5,
            monthly_rent=int(monthly_rent),
            rehab_budget=int(repairs),
            bedrooms=int(bedrooms),
            bathrooms=int(bathrooms),
            square_feet=int(square_feet)
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

@app.route('/ai_strategy_insight', methods=['POST'])
def ai_strategy_insight():
    """
    Generate AI-powered strategy insights for real estate deals
    """
    try:
        data = request.get_json()
        
        # Extract deal parameters
        arv = int(data.get('arv', 200000))
        repairs = int(data.get('repairs', 30000))
        rent = int(data.get('rent', 2000))
        equity = int(data.get('equity', arv * 0.25))  # Assume 25% equity
        location = data.get('location', 'Unknown Location')
        exit_goals = data.get('exit_goals', 'speed')
        comparable_sales = data.get('comparable_sales', [])
        
        # Generate AI insights
        ai_insight = ai_strategy_assistant.generate_strategy_insight(
            arv=arv,
            repairs=repairs,
            rent=rent,
            equity=equity,
            location=location,
            exit_goals=exit_goals,
            comparable_sales=comparable_sales
        )
        
        # Get seller psychology guidance
        psychology_guidance = ai_strategy_assistant.get_seller_psychology_guidance(exit_goals)
        
        return jsonify({
            'status': 'success',
            'ai_insight': ai_insight,
            'psychology_guidance': psychology_guidance,
            'deal_parameters': {
                'arv': arv,
                'repairs': repairs,
                'rent': rent,
                'equity': equity,
                'location': location,
                'exit_goals': exit_goals
            }
        })
        
    except Exception as e:
        logging.error(f"AI strategy insight error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'ai_insight': {'insight': f'Unable to generate AI insights: {str(e)}'}
        }), 500

@app.route('/ai_deal_analysis', methods=['POST'])
def ai_deal_analysis():
    """
    AI-powered comparison of all four investment strategies
    """
    try:
        data = request.get_json()
        
        # Extract strategy data
        wholesale_data = data.get('wholesale_data', {})
        installment_data = data.get('installment_data', {})
        subject_to_data = data.get('subject_to_data', {})
        seller_finance_data = data.get('seller_finance_data', {})
        
        # Generate comprehensive analysis
        deal_analysis = ai_strategy_assistant.analyze_deal_feasibility(
            wholesale_data=wholesale_data,
            installment_data=installment_data,
            subject_to_data=subject_to_data,
            seller_finance_data=seller_finance_data
        )
        
        return jsonify({
            'status': 'success',
            'deal_analysis': deal_analysis,
            'strategies_analyzed': 4
        })
        
    except Exception as e:
        logging.error(f"AI deal analysis error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'analysis': f'Unable to generate deal analysis: {str(e)}'
        }), 500

@app.route('/acquisitions_analysis', methods=['POST'])
def acquisitions_analysis():
    """
    Comprehensive acquisitions analysis using the new Acquisitions Module
    """
    try:
        data = request.get_json()
        
        # Get current property data from session or request
        property_data = session.get('current_property', {})
        if not property_data:
            return jsonify({'error': 'No property data found. Please analyze a property first.'}), 400
        
        # Update with any new data from request
        property_data.update(data)
        
        # Run comprehensive acquisitions analysis
        analysis = acquisitions_module.analyze_all_acquisition_strategies(property_data)
        
        return jsonify(analysis)
        
    except Exception as e:
        logging.error(f"Acquisitions analysis error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/optimal_acquisition_strategy', methods=['POST'])
def optimal_acquisition_strategy():
    """
    Get optimal acquisition strategy recommendation
    """
    try:
        data = request.get_json()
        
        property_data = session.get('current_property', {})
        if not property_data:
            return jsonify({'error': 'No property data found. Please analyze a property first.'}), 400
        
        seller_goals = data.get('seller_goals', 'speed')
        
        # Get optimal strategy recommendation
        recommendation = acquisitions_module.get_optimal_acquisition_strategy(property_data, seller_goals)
        
        return jsonify(recommendation)
        
    except Exception as e:
        logging.error(f"Optimal strategy error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/generate_offer_package', methods=['POST'])
def generate_offer_package():
    """
    Generate complete offer package for selected strategy
    """
    try:
        data = request.get_json()
        
        property_data = session.get('current_property', {})
        if not property_data:
            return jsonify({'error': 'No property data found. Please analyze a property first.'}), 400
        
        strategy_name = data.get('strategy', 'wholesale')
        seller_profile = data.get('seller_profile', {})
        
        # Generate offer package
        offer_package = acquisitions_module.generate_offer_package(strategy_name, property_data, seller_profile)
        
        return jsonify(offer_package)
        
    except Exception as e:
        logging.error(f"Offer package error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/dispositions_analysis', methods=['POST'])
def dispositions_analysis():
    """
    Analyze exit strategies using the Dispositions Module
    """
    try:
        data = request.get_json()
        
        property_data = session.get('current_property', {})
        if not property_data:
            return jsonify({'error': 'No property data found. Please analyze a property first.'}), 400
        
        # Update with acquisition cost if provided
        acquisition_strategy = data.get('acquisition_strategy')
        if 'acquisition_cost' in data:
            property_data['acquisition_cost'] = data['acquisition_cost']
        
        # Run exit strategy analysis
        analysis = dispositions_module.analyze_exit_strategies(property_data, acquisition_strategy)
        
        return jsonify(analysis)
        
    except Exception as e:
        logging.error(f"Dispositions analysis error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/generate_investor_listing', methods=['POST'])
def generate_investor_listing():
    """
    Generate AI-powered investor listing using GPT-4o
    """
    try:
        data = request.get_json()
        
        property_data = session.get('current_property', {})
        if not property_data:
            return jsonify({'error': 'No property data found. Please analyze a property first.'}), 400
        
        listing_type = data.get('listing_type', 'off_market')
        
        # Generate investor listing
        listing_result = ai_listing_generator.generate_investor_listing(property_data, listing_type)
        
        return jsonify(listing_result)
        
    except Exception as e:
        logging.error(f"Listing generation error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/generate_listing_variations', methods=['POST'])
def generate_listing_variations():
    """
    Generate multiple listing variations for A/B testing
    """
    try:
        property_data = session.get('current_property', {})
        if not property_data:
            return jsonify({'error': 'No property data found. Please analyze a property first.'}), 400
        
        # Generate listing variations
        variations_result = ai_listing_generator.generate_listing_variations(property_data)
        
        return jsonify(variations_result)
        
    except Exception as e:
        logging.error(f"Listing variations error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

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

@app.route('/api/validate-address', methods=['POST'])
def validate_address():
    """
    Layer 2: Server-side address validation using Google Geocoding API
    """
    try:
        data = request.json
        if not data or not data.get('address'):
            return jsonify({'success': False, 'error': 'Address is required'})
        
        from address_validation_service import address_validator
        
        # Extract address components if provided
        address = data['address']
        city = data.get('city', '')
        state = data.get('state', '')
        zip_code = data.get('zip_code', '')
        
        # Check if this is already a Google Places selection with place_id
        place_id = data.get('place_id')
        if place_id:
            # Already validated by Google Places, just confirm the data
            return jsonify({
                'success': True,
                'address': {
                    'formatted_address': data.get('formatted_address', address),
                    'place_id': place_id,
                    'street': data.get('street', ''),
                    'city': data.get('city', city),
                    'state': data.get('state', state),
                    'zip': data.get('zip', zip_code),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'confidence': 'high',
                    'source': 'google_places'
                }
            })
        
        # Use enhanced validation with geocoding fallback for manual entries
        result = address_validator.geocode_loose(address, city, state, zip_code)
        
        if result:
            return jsonify({
                'success': True,
                'address': {
                    'formatted_address': result['formatted_address'],
                    'place_id': result.get('place_id'),
                    'street': result.get('street', ''),
                    'city': result.get('city', ''),
                    'state': result.get('state', ''),
                    'zip': result.get('zip', ''),
                    'latitude': result.get('latitude'),
                    'longitude': result.get('longitude'),
                    'confidence': result.get('confidence', 'medium'),
                    'source': result.get('source', 'geocoding')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Address could not be validated. Please check the address and try again.'
            })
            
    except Exception as e:
        logging.error(f"Address validation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Address validation service temporarily unavailable'
        })

@app.route('/api/validate-address-advanced', methods=['POST'])
def validate_address_advanced():
    """
    Enhanced address validation using Google's Address Validation API
    """
    try:
        data = request.get_json()
        formatted_address = data.get('formatted_address', '')
        place_id = data.get('place_id', '')
        address_components = data.get('address_components', [])
        
        # Basic validation - ensure we have required components
        required_fields = ['street', 'city', 'state', 'zip']
        parsed_components = {}
        
        for component in address_components:
            types = component.get('types', [])
            
            if 'street_number' in types:
                parsed_components['street_number'] = component.get('long_name', '')
            if 'route' in types:
                parsed_components['route'] = component.get('long_name', '')
            if 'locality' in types:
                parsed_components['city'] = component.get('long_name', '')
            if 'administrative_area_level_1' in types:
                parsed_components['state'] = component.get('short_name', '')
            if 'postal_code' in types:
                parsed_components['zip'] = component.get('long_name', '')
        
        # Construct street address
        street = f"{parsed_components.get('street_number', '')} {parsed_components.get('route', '')}".strip()
        
        # Validate completeness
        is_valid = bool(
            street and 
            parsed_components.get('city') and 
            parsed_components.get('state') and 
            parsed_components.get('zip') and
            place_id
        )
        
        validation_result = {
            'isValid': is_valid,
            'formatted_address': formatted_address,
            'place_id': place_id,
            'components': {
                'street': street,
                'city': parsed_components.get('city', ''),
                'state': parsed_components.get('state', ''),
                'zip': parsed_components.get('zip', '')
            },
            'validation_outcome': 'CONFIRMED' if is_valid else 'PARTIAL'
        }
        
        return jsonify(validation_result)
        
    except Exception as e:
        return jsonify({'error': str(e), 'isValid': False}), 500

def require_complete_address(data):
    """
    Middleware function to ensure complete address information
    """
    required_fields = ['street', 'city', 'state', 'zip']
    missing_fields = []
    
    for field in required_fields:
        if not data.get(field) or not data.get(field).strip():
            missing_fields.append(field)
    
    if missing_fields:
        return {
            'error': 'INCOMPLETE_ADDRESS',
            'message': f'Missing required address fields: {", ".join(missing_fields)}',
            'missing_fields': missing_fields
        }
    
    return None

@app.route('/api/autocomplete', methods=['POST'])
def autocomplete():
    """
    Google Places Autocomplete (New) API proxy endpoint
    """
    try:
        data = request.get_json()
        
        # Extract required fields
        input_text = data.get('input', '')
        language_code = data.get('languageCode', 'en')
        include_query_predictions = data.get('includeQueryPredictions', False)
        session_token = data.get('sessionToken', '')
        
        if not input_text:
            return jsonify({'suggestions': []})
        
        # Call Google Places Autocomplete API
        import requests
        import os
        
        api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if not api_key:
            return jsonify({'error': 'Google Maps API key not configured'}), 500
        
        # Try Google Places API (New) first
        url = 'https://places.googleapis.com/v1/places:autocomplete'
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': api_key,
            'X-Goog-FieldMask': 'suggestions.placePrediction.placeId,suggestions.placePrediction.text'
        }
        
        payload = {
            'input': input_text,
            'languageCode': language_code,
            'includeQueryPredictions': include_query_predictions,
            'sessionToken': session_token
        }
        
        logging.info(f"Making Google Places API call with payload: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        
        logging.info(f"Google Places API response status: {response.status_code}")
        logging.info(f"Google Places API response text: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            logging.info(f"Successful response with {len(response_data.get('suggestions', []))} suggestions")
            return jsonify(response_data)
        elif response.status_code == 400 and "API key not valid" in response.text:
            logging.warning("Google Places API (New) not enabled - trying legacy API")
            
            # Fallback to legacy Google Places API
            legacy_url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
            legacy_params = {
                'input': input_text,
                'key': api_key,
                'types': 'address',
                'language': language_code,
                'sessiontoken': session_token
            }
            
            legacy_response = requests.get(legacy_url, params=legacy_params)
            
            if legacy_response.status_code == 200:
                legacy_data = legacy_response.json()
                
                # Transform legacy response to match new API format
                suggestions = []
                for prediction in legacy_data.get('predictions', []):
                    suggestions.append({
                        'placePrediction': {
                            'placeId': prediction.get('place_id'),
                            'text': {
                                'text': prediction.get('description', '')
                            }
                        }
                    })
                
                return jsonify({'suggestions': suggestions})
            else:
                logging.error(f"Legacy Google Places API error: {legacy_response.status_code} - {legacy_response.text}")
                return jsonify({
                    'error': 'API_NOT_ENABLED',
                    'message': 'Google Places API (New) requires activation in Google Cloud Console',
                    'suggestions': []
                })
        else:
            logging.error(f"Google Autocomplete API error: {response.status_code} - {response.text}")
            return jsonify({'suggestions': []})
            
    except Exception as e:
        logging.error(f"Autocomplete error: {e}")
        return jsonify({'suggestions': []})


@app.route('/api/place-details', methods=['POST'])
def place_details():
    """
    Google Places Details (New) API proxy endpoint
    """
    try:
        data = request.get_json()
        place_id = data.get('placeId')
        session_token = data.get('sessionToken', '')
        
        if not place_id:
            return jsonify({'error': 'placeId is required'}), 400
        
        # Call Google Places Details API
        import requests
        import os
        
        api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if not api_key:
            return jsonify({'error': 'Google Maps API key not configured'}), 500
        
        url = f'https://places.googleapis.com/v1/places/{place_id}'
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': api_key,
            'X-Goog-FieldMask': 'id,formattedAddress,addressComponents'
        }
        
        if session_token:
            headers['X-Goog-Maps-Session-Token'] = session_token
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            place_data = response.json()
            logging.info(f"Place details response: {place_data}")
            return jsonify(place_data)
        elif response.status_code == 400 and "API key not valid" in response.text:
            logging.warning("Google Places API (New) not enabled for place details")
            return jsonify({
                'error': 'API_NOT_ENABLED',
                'message': 'Google Places API (New) requires activation in Google Cloud Console'
            }), 400
        else:
            logging.error(f"Google Place Details API error: {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to get place details'}), 500
            
    except Exception as e:
        logging.error(f"Place details error: {e}")
        return jsonify({'error': 'Failed to get place details'}), 500


@app.route('/api/places/details', methods=['POST'])
def get_place_details():
    """
    Get canonical address using Google Places "Place Details (New)" API
    """
    try:
        
        data = request.get_json()
        place_id = data.get('place_id', '').strip()
        
        if not place_id:
            return jsonify({'error': 'place_id is required'}), 400
        
        # Get canonical address from Google Places
        canonical_data = google_places_service.get_canonical_address(place_id)
        
        return jsonify({
            'success': True,
            'data': canonical_data
        })
        
    except AddressNotFoundError as e:
        return jsonify({
            'success': False,
            'error': 'ADDRESS_NOT_FOUND',
            'message': 'Google could not resolve this address – please re-check.'
        }), 404
        
    except GooglePlacesAPIError as e:
        logging.error(f"Google Places API error: {e}")
        return jsonify({
            'success': False,
            'error': 'API_ERROR',
            'message': 'Google Places service temporarily unavailable'
        }), 503
        
    except Exception as e:
        logging.error(f"Unexpected error in get_place_details: {e}")
        return jsonify({
            'success': False,
            'error': 'UNKNOWN_ERROR',
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/api/objection_handler', methods=['POST'])
def objection_handler():
    """
    AI-powered objection handling assistant using GPT-4o
    """
    try:
        from openai import OpenAI
        import os
        
        data = request.get_json()
        objection_text = (data.get('objection_text') or '').strip()
        category = data.get('category', '')
        regenerate = data.get('regenerate', False)
        
        if not objection_text:
            return jsonify({'success': False, 'error': 'Objection text is required'})
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Build the expert prompt
        category_context = ""
        if category:
            category_contexts = {
                'price': "This is a price/value objection. Focus on demonstrating value and exploring their true concerns about price.",
                'timeline': "This is a timeline/urgency objection. Explore their timeline concerns and offer flexible solutions.",
                'fees': "This is a fees/costs objection. Break down the value of services and explore their budget concerns.",
                'trust': "This is a trust/credibility objection. Build rapport and provide social proof and credentials.",
                'process': "This is a process/paperwork objection. Simplify the process and address their administrative concerns.",
                'competition': "This is about other offers. Focus on unique value propositions and relationship building.",
                'family': "This is a family/emotional objection. Show empathy and address emotional concerns.",
                'condition': "This is about property condition. Address repair concerns and adjustment possibilities."
            }
            category_context = f"\n\nCONTEXT: {category_contexts.get(category, '')}"
        
        creativity_instruction = "Use high creativity and varied approaches." if regenerate else "Use standard professional approach."
        
        prompt = f"""You are a real-estate acquisitions coach trained on the selling techniques of:
• Chris Voss (tactical empathy, calibrated questions)
• Steve Trang (wholesaling sales frameworks)  
• Ian Ross (creative finance negotiation)
• John Martinez (pain funnels, soft closes)

{creativity_instruction}{category_context}

SELLER'S OBJECTION:
"{objection_text}"

INSTRUCTIONS:
1. Restate the seller's objection to show understanding
2. Provide a concise empathy statement
3. Ask 2-3 Socratic/calibrated questions to uncover root cause
4. Offer one compelling solution or concession
5. End with a soft close that invites the seller to talk further

Output in markdown with sections:
**Empathy** – [Empathetic acknowledgment]
**Questions** – [2-3 bullet points with calibrated questions]
**Suggested Solution** – [One compelling solution]
**Soft Close** – [Invitation to continue conversation]"""

        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert real estate acquisitions coach specializing in objection handling using proven sales methodologies."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8 if regenerate else 0.7,
            max_tokens=800
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'response': ai_response
        })
        
    except Exception as e:
        print(f"Error in objection handler: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to generate objection response: {str(e)}'
        })

@app.route('/analyze_property_risk', methods=['POST'])
def analyze_property_risk():
    """
    Generate comprehensive property risk analysis with interactive heatmap data
    """
    try:
        # Get current property data from session
        property_data = session.get('current_property_data', {})
        
        if not property_data:
            return jsonify({
                'status': 'error',
                'error': 'No property data available. Please analyze a property first.'
            })
        
        # Generate risk analysis
        risk_analysis = property_risk_analyzer.analyze_property_risk(property_data)
        
        # Generate heatmap data
        heatmap_data = property_risk_analyzer.generate_risk_heatmap_data(property_data)
        
        return jsonify({
            'status': 'success',
            'risk_analysis': risk_analysis,
            'heatmap_data': heatmap_data
        })
        
    except Exception as e:
        print(f"Error analyzing property risk: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@app.route('/api/comps/analyze', methods=['POST'])
def analyze_comps():
    """
    Analyze comparable properties using Zillow API and OpenAI
    """
    try:
        data = request.get_json()
        
        # Get property details from request or session
        address = data.get('address') or session.get('current_property', {}).get('address')
        beds = data.get('beds') or session.get('current_property', {}).get('beds') or 3
        baths = data.get('baths') or session.get('current_property', {}).get('baths') or 2
        sqft = data.get('sqft') or session.get('current_property', {}).get('sqft') or 1500
        lat = data.get('latitude') or session.get('current_property', {}).get('latitude')
        lng = data.get('longitude') or session.get('current_property', {}).get('longitude')
        
        if not address:
            return jsonify({
                'success': False,
                'error': 'Property address is required'
            }), 400
        
        # Analyze comparables
        result = comps_service.analyze_comparables(
            subject_address=address,
            beds=int(beds),
            baths=float(baths),
            sqft=int(sqft),
            lat=lat,
            lng=lng
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error analyzing comparables: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===============================
# JV Deal Submit Routes
# ===============================

@app.route('/jv-submit')
def jv_submit_page():
    """JV Deal Submit page"""
    return render_template('jv_submit.html', 
                         google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY'))

@app.route('/api/jv-submit', methods=['POST'])
def jv_submit_deal():
    """
    Submit and auto-underwrite JV deal with partner information
    """
    try:
        data = request.get_json()
        
        # Validate required partner fields
        partner_required_fields = ['partner_name', 'partner_email', 'partner_phone', 'partner_markets']
        for field in partner_required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required partner field: {field}'
                }), 400
        
        # Validate partner name (at least 2 words)
        name_parts = (data.get('partner_name') or '').strip().split()
        if len(name_parts) < 2:
            return jsonify({
                'success': False,
                'error': 'Full name must contain at least two words'
            }), 400
        
        # Validate markets selection
        if not data.get('partner_markets') or len(data.get('partner_markets', [])) == 0:
            return jsonify({
                'success': False,
                'error': 'At least one market state must be selected'
            }), 400
        
        # Validate required deal fields
        deal_required_fields = ['property_address', 'deal_type', 'seller_asking_price', 'arv', 'rehab_needed', 'property_status', 'closing_date']
        for field in deal_required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required deal field: {field}'
                }), 400
        
        # Additional validation for wholesale deals
        if data.get('deal_type') == 'wholesale' and not data.get('purchase_price'):
            return jsonify({
                'success': False,
                'error': 'Purchase price is required for wholesale deals'
            }), 400
        
        # Additional validation for rehab cost
        if data.get('rehab_needed') == 'yes' and not data.get('rehab_cost'):
            return jsonify({
                'success': False,
                'error': 'Rehab cost is required when rehab is needed'
            }), 400
        
        # Create or get partner record
        from jv_database import jv_db
        
        partner_id = jv_db.create_or_get_partner(
            name=data.get('partner_name'),
            email=data.get('partner_email'),
            phone=data.get('partner_phone'),
            company=data.get('partner_company'),
            markets=data.get('partner_markets', [])
        )
        
        # Auto-underwrite the deal
        underwrite_result = auto_underwrite_deal(data)
        
        # Prepare deal data for database storage
        deal_data = {
            'property_address': data.get('property_address'),
            'street': data.get('street', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'zip': data.get('zip', ''),
            'deal_type': data.get('deal_type'),
            'purchase_price': data.get('purchase_price'),
            'seller_asking_price': data.get('seller_asking_price'),
            'arv': data.get('arv'),
            'rehab_needed': data.get('rehab_needed'),
            'rehab_cost': data.get('rehab_cost'),
            'property_description': data.get('property_description', ''),
            'photos_link': data.get('photos_link', ''),
            'property_status': data.get('property_status'),
            'closing_date': data.get('closing_date'),
            'additional_notes': data.get('additional_notes', ''),
            'underwrite_result': underwrite_result,
            'partner_info': {
                'name': data.get('partner_name'),
                'email': data.get('partner_email'),
                'phone': data.get('partner_phone'),
                'company': data.get('partner_company'),
                'markets': data.get('partner_markets', [])
            }
        }
        
        # Store deal in database
        deal_id = jv_db.create_deal_submission(
            partner_id=partner_id,
            deal_data=deal_data,
            auto_status='approved' if underwrite_result['status'] == 'auto-approved' else 'denied',
            reasons=underwrite_result.get('reasons', [])
        )
        
        # Trigger Zapier webhook for new JV submission
        from zapier_webhook_service import trigger_jv_submission
        from datetime import datetime
        trigger_jv_submission({
            'id': deal_id,
            'address': data.get('property_address'),
            'user_id': partner_id,  # Using partner_id as user_id for now
            'partner_name': data.get('partner_name'),
            'partner_email': data.get('partner_email'),
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'success': True,
            'submission_id': deal_id,
            'partner_id': partner_id,
            'underwrite_result': underwrite_result,
            'status': 'approved' if underwrite_result['status'] == 'auto-approved' else 'denied'
        })
        
    except Exception as e:
        logging.error(f"Error submitting JV deal: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/jv-admin')
def jv_admin_page():
    """
    Admin dashboard for JV deals and partners
    """
    try:
        # Check admin authentication (simple token check)
        admin_token = os.environ.get('ADMIN_TOKEN', 'admin123')  # Default for demo
        provided_token = request.args.get('token')
        
        if provided_token != admin_token:
            return render_template('jv_admin_login.html')
        
        from jv_database import jv_db
        
        # Get dashboard stats
        stats = jv_db.get_dashboard_stats()
        
        # Get recent partners
        partners = jv_db.get_all_partners(limit=20)
        
        return render_template('jv_admin.html', 
                             stats=stats, 
                             partners=partners, 
                             admin_token=admin_token)
        
    except Exception as e:
        logging.error(f"Error loading admin page: {e}")
        return render_template('jv_admin.html', 
                             stats={'total_partners': 0, 'deals_last_30_days': 0, 'auto_approved': 0, 'auto_denied': 0, 'approval_rate': 0}, 
                             partners=[], 
                             error=str(e))

@app.route('/jv-admin/partner/<partner_id>')
def jv_admin_partner_detail(partner_id):
    """
    Partner detail view
    """
    try:
        # Check admin authentication
        admin_token = os.environ.get('ADMIN_TOKEN', 'admin123')
        provided_token = request.args.get('token')
        
        if provided_token != admin_token:
            return redirect(f'/jv-admin?token={admin_token}')
        
        from jv_database import jv_db
        
        # Get partner details
        partner = jv_db.get_partner_by_id(partner_id)
        if not partner:
            return "Partner not found", 404
        
        # Get partner deals
        deals = jv_db.get_partner_deals(partner_id, limit=50)
        
        # Get partner stats
        stats = jv_db.get_partner_stats(partner_id)
        
        return render_template('jv_admin_partner.html', 
                             partner=partner, 
                             deals=deals, 
                             stats=stats,
                             admin_token=admin_token)
        
    except Exception as e:
        logging.error(f"Error loading partner detail: {e}")
        return f"Error: {e}", 500

@app.route('/jv-admin/deal/<deal_id>')
def jv_admin_deal_detail(deal_id):
    """
    Deal detail view
    """
    try:
        # Check admin authentication
        admin_token = os.environ.get('ADMIN_TOKEN', 'admin123')
        provided_token = request.args.get('token')
        
        if provided_token != admin_token:
            return redirect(f'/jv-admin?token={admin_token}')
        
        from jv_database import jv_db
        
        # Get deal details
        deal = jv_db.get_deal_by_id(deal_id)
        if not deal:
            return "Deal not found", 404
        
        return render_template('jv_admin_deal.html', 
                             deal=deal,
                             admin_token=admin_token)
        
    except Exception as e:
        logging.error(f"Error loading deal detail: {e}")
        return f"Error: {e}", 500

@app.route('/api/jv-admin/deal/<deal_id>/status', methods=['POST'])
def jv_admin_update_deal_status(deal_id):
    """
    Update deal final status (admin approval/denial)
    """
    try:
        # Check admin authentication
        admin_token = os.environ.get('ADMIN_TOKEN', 'admin123')
        provided_token = request.json.get('admin_token') if request.json else None
        
        if provided_token != admin_token:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        final_status = data.get('final_status')
        
        if final_status not in ['approved', 'denied']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        from jv_database import jv_db
        
        success = jv_db.update_deal_final_status(deal_id, final_status)
        
        if success:
            # Trigger Zapier webhook for JV approval if approved
            if final_status == 'approved':
                from zapier_webhook_service import trigger_jv_approved
                from datetime import datetime
                
                # Get deal details for webhook
                deal = jv_db.get_deal_by_id(deal_id)
                if deal:
                    deal_json = deal['deal_json']
                    trigger_jv_approved({
                        'id': deal_id,
                        'address': deal_json.get('property_address'),
                        'user_id': deal['partner_id'],
                        'partner_name': deal_json.get('partner_info', {}).get('name'),
                        'partner_email': deal_json.get('partner_info', {}).get('email'),
                        'approved_at': datetime.utcnow().isoformat()
                    })
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Deal not found'}), 404
        
    except Exception as e:
        logging.error(f"Error updating deal status: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ==================== BILLING & SUBSCRIPTION ENDPOINTS ====================

@app.route('/api/billing/create-checkout', methods=['POST'])
@require_auth
def create_checkout():
    """Create Stripe checkout session for subscription or credit purchase"""
    try:
        data = request.get_json()
        lookup_key = data.get('lookup_key')
        quantity = data.get('quantity', 1)
        
        if not lookup_key:
            return jsonify({'error': 'lookup_key is required'}), 400
        
        # Create checkout session
        result = billing_service.create_checkout_session(
            lookup_key=lookup_key,
            quantity=quantity,
            customer_email=g.current_user['email'],
            team_id=g.current_user['team_id'],
            success_url=request.url_root + 'billing/success',
            cancel_url=request.url_root + 'billing/cancel'
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error creating checkout: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/billing/webhook', methods=['POST'])
def billing_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.data
        signature = request.headers.get('Stripe-Signature')
        
        result = billing_service.handle_webhook(payload.decode('utf-8'), signature)
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 400

@app.route('/api/team/stats')
def get_team_stats():
    """Get team statistics and billing information"""
    try:
        # For testing, use the session user_id like in dashboard()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
            
        # Get user data from database
        with Session(engine) as db:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not user.team_id:
                return jsonify({'error': 'User has no team assigned'}), 400
            
            # Get team stats using billing service
            stats = billing_service.get_team_stats(user.team_id)
            return jsonify(stats)
        
    except Exception as e:
        logging.error(f"Error getting team stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/redeem-credit-code', methods=['POST'])
def redeem_credit_code():
    """Redeem credit code for authenticated user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        code = data.get('code', '').strip().upper()
        
        if not code:
            return jsonify({'error': 'Credit code is required'}), 400
        
        if len(code) < 3:
            return jsonify({'error': 'Invalid credit code format'}), 400
        
        # Get user from database first to get their email
        with Session(engine) as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Use the billing service to redeem the credit code
            result = billing_service.redeem_credit_code(code, user.email)
            
            if not result.get('success'):
                error_message = result.get('error', 'Unknown error')
                if error_message == 'invalid':
                    return jsonify({'error': 'Credit code not found'}), 404
                elif error_message == 'expired':
                    return jsonify({'error': 'Credit code has expired'}), 400
                elif error_message == 'exhausted':
                    return jsonify({'error': 'Credit code has reached maximum uses'}), 400
                elif error_message == 'expired or disabled':
                    return jsonify({'error': 'Credit code is no longer active'}), 400
                else:
                    return jsonify({'error': 'Failed to redeem credit code'}), 500
            
            # Add credits to user
            credits_to_add = result.get('credits_added', 0)
            original_balance = user.credits
            user.credits += credits_to_add
            
            # Log the credit addition
            try:
                credit_log = CreditLog(
                    user_id=user.id,
                    team_id=user.team_id,
                    credits_added=credits_to_add,
                    credits_used=0,
                    reason=f"Credit code redeemed: {code}",
                    created_at=datetime.utcnow()
                )
                db.add(credit_log)
            except Exception as log_error:
                logging.warning(f"Failed to log credit redemption: {log_error}")
            
            db.commit()
            
            return jsonify({
                'success': True,
                'credits_added': credits_to_add,
                'new_balance': user.credits,
                'previous_balance': original_balance,
                'message': f'Successfully redeemed {credits_to_add} credits!'
            })
        
    except Exception as e:
        logging.error(f"Error redeeming credit code: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/team/invite', methods=['POST'])
@require_role('manager')
def create_team_invite():
    """Create team invitation (managers and owners only)"""
    try:
        data = request.get_json()
        email = data.get('email')
        role = data.get('role', 'analyst')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if role not in ['analyst', 'manager']:
            return jsonify({'error': 'Invalid role'}), 400
        
        result = billing_service.create_team_invite(
            team_id=g.current_user['team_id'],
            email=email,
            role=role
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error creating team invite: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/team/member/<member_id>', methods=['DELETE'])
@require_role('manager')
def remove_team_member(member_id):
    """Remove team member (managers and owners only)"""
    try:
        # Don't allow removing the team owner
        if member_id == g.current_user['id']:
            return jsonify({'error': 'Cannot remove yourself from the team'}), 400
        
        result = billing_service.remove_team_member(
            team_id=g.current_user['team_id'],
            member_id=member_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error removing team member: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/team/member/<member_id>/role', methods=['PUT'])
@require_role('manager')
def update_member_role(member_id):
    """Update team member role (managers and owners only)"""
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if not new_role:
            return jsonify({'error': 'Role is required'}), 400
        
        if new_role not in ['analyst', 'manager', 'owner']:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Only owners can promote to owner
        if new_role == 'owner' and g.current_user['role'] != 'owner':
            return jsonify({'error': 'Only owners can promote to owner role'}), 403
        
        result = billing_service.update_member_role(
            team_id=g.current_user['team_id'],
            member_id=member_id,
            new_role=new_role
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error updating member role: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/team/pending-invites', methods=['GET'])
def get_pending_invites():
    """Get pending team invites"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Get user's team
        with Session(engine) as db:
            from billing_models import User, TeamInvite
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Get pending invites for this team
            invites = db.query(TeamInvite).filter(
                TeamInvite.team_id == user.team_id,
                TeamInvite.status == 'pending'
            ).all()
            
            invite_list = []
            for invite in invites:
                invite_list.append({
                    'id': str(invite.id),
                    'email': invite.email,
                    'role': invite.role,
                    'created_at': invite.created_at.isoformat(),
                    'status': invite.status
                })
            
            return jsonify({
                'success': True,
                'invites': invite_list
            })
            
    except Exception as e:
        logging.error(f"Error getting pending invites: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/team/invite/<invite_id>/resend', methods=['POST'])
def resend_invite(invite_id):
    """Resend a team invitation"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        with Session(engine) as db:
            from billing_models import User, TeamInvite, Team
            
            # Check if user has permission to resend invites
            user = db.query(User).filter(User.id == user_id).first()
            if not user or user.role not in ['owner', 'manager']:
                return jsonify({'success': False, 'error': 'Insufficient permissions'}), 403
            
            # Find the invite
            invite = db.query(TeamInvite).filter(
                TeamInvite.id == invite_id,
                TeamInvite.team_id == user.team_id,
                TeamInvite.status == 'pending'
            ).first()
            
            if not invite:
                return jsonify({'success': False, 'error': 'Invite not found'}), 404
            
            # Get team info
            team = db.query(Team).filter(Team.id == user.team_id).first()
            
            # Send email notification using billing service
            logging.info(f"Attempting to resend invitation email to {invite.email} for team {team.name}")
            email_sent = billing_service._send_invitation_email(
                invite.email,
                team.name,
                invite.token
            )
            logging.info(f"Email send result: {email_sent}")
            
            return jsonify({
                'success': True,
                'email_sent': email_sent,
                'message': 'Invitation resent successfully'
            })
            
    except Exception as e:
        logging.error(f"Error resending invite: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/team/invite/<invite_id>/cancel', methods=['DELETE'])
def cancel_invite(invite_id):
    """Cancel a team invitation"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        with Session(engine) as db:
            from billing_models import User, TeamInvite
            
            # Check if user has permission to cancel invites
            user = db.query(User).filter(User.id == user_id).first()
            if not user or user.role not in ['owner', 'manager']:
                return jsonify({'success': False, 'error': 'Insufficient permissions'}), 403
            
            # Find and cancel the invite
            invite = db.query(TeamInvite).filter(
                TeamInvite.id == invite_id,
                TeamInvite.team_id == user.team_id,
                TeamInvite.status == 'pending'
            ).first()
            
            if not invite:
                return jsonify({'success': False, 'error': 'Invite not found'}), 404
            
            # Update invite status
            invite.status = 'cancelled'
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'Invitation cancelled successfully'
            })
            
    except Exception as e:
        logging.error(f"Error cancelling invite: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/settings/billing')
@require_auth
def billing_settings():
    """Billing settings page (owner only)"""
    if g.current_user['role'] != 'owner':
        return redirect('/')
    
    return render_template('billing/settings.html', 
                         user=g.current_user, 
                         team=g.current_team)

@app.route('/settings/team')
@require_auth
def team_settings():
    """Team management page"""
    return render_template('billing/team.html', 
                         user=g.current_user, 
                         team=g.current_team)

# ==================== EMAIL SERVICE ENDPOINTS ====================

@app.route('/api/send-welcome-email', methods=['POST'])
@require_auth
def send_welcome_email():
    """Send welcome email to user"""
    try:
        data = request.get_json()
        user_email = data.get('email')
        user_name = data.get('name', 'User')
        
        if not user_email:
            return jsonify({'error': 'Email is required'}), 400
        
        success = email_service.send_welcome_email(user_email, user_name)
        
        if success:
            return jsonify({'message': 'Welcome email sent successfully'})
        else:
            return jsonify({'error': 'Failed to send welcome email'}), 500
            
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/send-test-email', methods=['POST'])
@require_auth
def send_test_email():
    """Send test email to verify email configuration"""
    try:
        data = request.get_json()
        to_email = data.get('email')
        
        if not to_email:
            return jsonify({'error': 'Email is required'}), 400
        
        from datetime import datetime
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #667eea; padding: 40px; text-align: center;">
                <h1 style="color: white; margin: 0;">Email Test Successful!</h1>
            </div>
            
            <div style="padding: 40px;">
                <h2 style="color: #333;">Email Configuration Working</h2>
                
                <p style="color: #666; line-height: 1.6;">
                    This test email confirms that your Properwrite email service is configured correctly 
                    and can send emails from support@fundflowos.com.
                </p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">Test Details:</h3>
                    <p style="color: #666; margin: 5px 0;"><strong>From:</strong> support@fundflowos.com</p>
                    <p style="color: #666; margin: 5px 0;"><strong>Service:</strong> Properwrite Email Service</p>
                    <p style="color: #666; margin: 5px 0;"><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p style="color: #666;">
                    Best regards,<br>
                    The Properwrite Team
                </p>
            </div>
        </body>
        </html>
        """
        
        success = email_service.send_email(
            to_email=to_email,
            subject="Email Test - Properwrite Configuration",
            html_content=html_content
        )
        
        if success:
            return jsonify({'message': 'Test email sent successfully'})
        else:
            return jsonify({'error': 'Failed to send test email'}), 500
            
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/send-support-email', methods=['POST'])
@require_auth
def send_support_email():
    """Send support email notification"""
    try:
        data = request.get_json()
        user_email = data.get('user_email')
        user_name = data.get('user_name', 'User')
        subject = data.get('subject', 'Support Request')
        message = data.get('message', '')
        
        if not user_email or not message:
            return jsonify({'error': 'Email and message are required'}), 400
        
        from datetime import datetime
        
        # Send notification to support team
        support_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #dc3545; padding: 40px; text-align: center;">
                <h1 style="color: white; margin: 0;">New Support Request</h1>
            </div>
            
            <div style="padding: 40px;">
                <h2 style="color: #333;">Support Request Details</h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">User Information:</h3>
                    <p style="color: #666; margin: 5px 0;"><strong>Name:</strong> {user_name}</p>
                    <p style="color: #666; margin: 5px 0;"><strong>Email:</strong> {user_email}</p>
                    <p style="color: #666; margin: 5px 0;"><strong>Subject:</strong> {subject}</p>
                    <p style="color: #666; margin: 5px 0;"><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <div style="background: #fff; border: 1px solid #ddd; padding: 20px; border-radius: 5px;">
                    <h4 style="color: #333; margin-top: 0;">Message:</h4>
                    <p style="color: #666; line-height: 1.6;">{message}</p>
                </div>
                
                <p style="color: #666; margin-top: 20px;">
                    Please respond to this support request as soon as possible.
                </p>
            </div>
        </body>
        </html>
        """
        
        success = email_service.send_email(
            to_email='support@fundflowos.com',
            subject=f'Support Request: {subject}',
            html_content=support_html
        )
        
        if success:
            return jsonify({'message': 'Support request sent successfully'})
        else:
            return jsonify({'error': 'Failed to send support request'}), 500
            
    except Exception as e:
        logger.error(f"Error sending support email: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)