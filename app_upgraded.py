"""
properwrite.com - Real Estate Investment Analysis Platform
Enhanced with external data pulling, cleaner UI, and comprehensive strategy comparison
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, g, url_for, flash
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
from jv_auto_underwrite import auto_underwrite_deal, auto_underwrite_deal_with_mao
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
from bitcoin_payment_service import bitcoin_service
from simple_comps_service import SimpleCompsService
from enhanced_comps_service import EnhancedCompsService, SearchParams
from email_service import email_service
from affiliate_api import affiliate_api
from construction_service import ConstructionService
from renovation_estimator_backend import RenovationEstimatorService
from services.unified_property_data_service import get_unified_property_service
from werkzeug.security import check_password_hash
from freemium_gate import gate_feature, check_free_use_status, get_feature_access_info, seed_free_credits

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

# Generate a strong random secret key if not set in environment
if not os.environ.get("SESSION_SECRET"):
    # Generate a cryptographically strong random key
    import secrets
    app.secret_key = secrets.token_hex(32)
    logging.warning("SESSION_SECRET not set! Using generated secret key. Set SESSION_SECRET env var in production.")
else:
    app.secret_key = os.environ.get("SESSION_SECRET")

# Configure session to last 30 days for better user experience
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# CSRF exemption for admin API routes will be handled in view functions

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per hour", "50 per minute"],
    storage_uri="memory://"
)

# Initialize billing service
billing_service = BillingService()

# Initialize construction service
construction_service = ConstructionService()
renovation_estimator = RenovationEstimatorService()

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
comps_service = SimpleCompsService()
enhanced_comps_service = EnhancedCompsService()

# Register admin blueprint (unified admin system)
from admin_routes_minimal import admin_bp
app.register_blueprint(admin_bp)

# Make CSRF token available to admin templates
@app.context_processor
def inject_csrf_token():
    """Make CSRF token available to all templates"""
    return dict(csrf_token=generate_csrf)

# Freemium Gate API Endpoints
@app.route('/api/freemium/status', methods=['GET'])
@csrf.exempt
def get_freemium_status():
    """Get current freemium access status"""
    try:
        status = check_free_use_status()
        return jsonify(status)
    except Exception as e:
        logging.error(f"Error getting freemium status: {e}")
        return jsonify({'error': 'Failed to get status'}), 500

@app.route('/api/freemium/feature-access/<feature_name>', methods=['GET'])
@csrf.exempt
def get_feature_access(feature_name):
    """Get access information for a specific feature"""
    try:
        access_info = get_feature_access_info(feature_name)
        return jsonify(access_info)
    except Exception as e:
        logging.error(f"Error getting feature access for {feature_name}: {e}")
        return jsonify({'error': 'Failed to get access info'}), 500

# Register affiliate API blueprint
app.register_blueprint(affiliate_api)

# Admin Routes
@app.route('/admin/affiliates')
def admin_affiliates():
    """Admin affiliate management dashboard"""
    return render_template('admin_affiliate_dashboard.html')

@app.route('/admin/affiliate-login')
def admin_affiliate_login():
    """Admin affiliate login page"""
    return render_template('admin_affiliate_login.html')

# JV Expectations Route
@app.route('/jv-expectations')
def jv_expectations():
    """Joint Venture partnership expectations page"""
    return render_template('jv_expectations.html')

# Bitcoin Payment Routes
@app.route('/bitcoin/subscription/<plan_key>')
def bitcoin_subscription(plan_key):
    """Create Bitcoin payment for subscription plan"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        user_email = session.get('user_email', '')
        team_id = session.get('team_id', '')
        
        charge = bitcoin_service.create_subscription_charge(
            plan_key=plan_key,
            user_email=user_email,
            team_id=team_id
        )
        
        # Redirect to Coinbase Commerce checkout
        return redirect(charge['data']['hosted_url'])
        
    except Exception as e:
        flash(f"Error creating Bitcoin payment: {str(e)}", 'error')
        return redirect(url_for('dashboard'))

@app.route('/bitcoin/credits/<int:credits>')
def bitcoin_credits(credits):
    """Create Bitcoin payment for credit pack"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        user_email = session.get('user_email', '')
        team_id = session.get('team_id', '')
        
        charge = bitcoin_service.create_credit_pack_charge(
            credits=credits,
            user_email=user_email,
            team_id=team_id
        )
        
        # Redirect to Coinbase Commerce checkout
        return redirect(charge['data']['hosted_url'])
        
    except Exception as e:
        flash(f"Error creating Bitcoin payment: {str(e)}", 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/bitcoin/webhook', methods=['POST'])
def bitcoin_webhook():
    """Handle Coinbase Commerce webhook events"""
    try:
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-CC-Webhook-Signature')
        
        if not bitcoin_service.verify_webhook_signature(payload, signature):
            return jsonify({"error": "Invalid signature"}), 401
        
        event_data = json.loads(payload)
        result = bitcoin_service.process_webhook_event(event_data)
        
        if result.get('status') == 'success':
            # Process successful payment
            if result.get('type') == 'subscription':
                # Handle subscription activation
                billing_service.activate_subscription(
                    user_email=result.get('user_email'),
                    plan_key=result.get('plan_key'),
                    payment_method='bitcoin'
                )
            elif result.get('type') == 'credit_pack':
                # Handle credit pack purchase
                billing_service.add_credits(
                    user_email=result.get('user_email'),
                    credits=result.get('credits'),
                    payment_method='bitcoin'
                )
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Bitcoin webhook error: {str(e)}")
        return jsonify({"error": "Webhook processing failed"}), 500

@app.route('/api/billing/create-bitcoin-checkout', methods=['POST'])
@csrf.exempt
def create_bitcoin_checkout():
    """Create Bitcoin checkout for credit packs"""
    try:
        data = request.get_json()
        lookup_key = data.get('lookup_key')
        credits = data.get('credits')
        amount = data.get('amount')
        
        if not lookup_key or not credits or not amount:
            return jsonify({"error": "Missing required fields"}), 400
        
        user_email = session.get('user_email', '')
        team_id = session.get('team_id', '')
        
        # Check if Bitcoin payment is configured
        if not bitcoin_service.api_key:
            return jsonify({"error": "Bitcoin payments are not configured"}), 400
        
        # Create Bitcoin payment charge
        charge = bitcoin_service.create_credit_pack_charge(
            credits=credits,
            user_email=user_email,
            team_id=team_id
        )
        
        return jsonify({
            "success": True,
            "checkout_url": charge['data']['hosted_url']
        })
        
    except Exception as e:
        logging.error(f"Bitcoin checkout error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signup', methods=['POST'])
def api_signup():
    """API endpoint for user signup"""
    try:
        logging.info("Signup request received")
        
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
        logging.info(f"Signup data received: {data.keys()}")
        
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        if not name or not email or not password:
            logging.error(f"Missing required fields: name={bool(name)}, email={bool(email)}, password={bool(password)}")
            return jsonify({"error": "Missing required fields"}), 400
        
        logging.info(f"Creating account for: {email}")
        
        # Check if user already exists
        with Session(engine) as db_session:
            existing_user = db_session.query(User).filter_by(email=email).first()
            if existing_user:
                logging.warning(f"User already exists: {email}")
                return jsonify({"error": "Email already registered"}), 400
        
        # Get invite token from session if present
        invite_token = session.get('team_invite_token')
        
        # Create new user with billing service
        logging.info(f"Creating user with billing service: {email}")
        result = billing_service.create_user({
            'name': name,
            'email': email,
            'password': password,
            'invite_token': invite_token
        })
        
        logging.info(f"Billing service result: {result}")
        
        if result.get('success'):
            # Set consolidated session with permanent flag
            session.permanent = True
            session['user_id'] = result['user_id']
            session['user_email'] = email
            session['email'] = email  # Keep for backward compatibility
            session['user_name'] = name
            session['team_id'] = result.get('team_id')
            session['team_role'] = result.get('role', 'owner')
            session['new_user_welcome'] = True
            
            logging.info(f"Session created for user: {email}")
            
            # Clear invite token if used
            if invite_token:
                session.pop('team_invite_token', None)
            
            # Send welcome email
            try:
                email_service.send_welcome_email(email, name)
                logging.info(f"Welcome email sent to: {email}")
            except Exception as e:
                logging.error(f"Failed to send welcome email: {e}")
            
            return jsonify({
                "success": True,
                "message": "Account created successfully"
            })
        else:
            logging.error(f"Failed to create user: {result.get('error')}")
            return jsonify({"error": result.get('error', 'Failed to create account')}), 400
            
    except Exception as e:
        logging.error(f"Signup error: {str(e)}")
        import traceback
        logging.error(f"Signup traceback: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

app.register_blueprint(admin_api_bp)
app.register_blueprint(zapier_api_bp)

# CSRF exemption for admin API routes will be handled in view functions

@app.route('/')
def index():
    """Enhanced property input form with external data integration"""
    # Check for affiliate referral parameters
    ref_id = request.args.get('ref')
    promo_code = request.args.get('code')
    
    # Auto-apply affiliate promo code if present
    if ref_id and promo_code:
        session['affiliate_ref'] = ref_id
        session['auto_promo_code'] = promo_code
        session['promo_applied'] = True
        flash(f'Promo code {promo_code} has been automatically applied to your account!', 'success')
    
    return render_template('index_upgraded.html', 
                         google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY') or os.environ.get('GOOGLE_API_KEY'))

@app.route('/rei-connect')
def rei_connect_landing():
    """REI Connect landing page with 50 credit offer"""
    # Auto-apply the 50 credit promo code for REI Connect
    session['rei_connect_promo'] = 'REICONNECT50'
    session['rei_connect_credits'] = 50
    session['promo_applied'] = True
    
    # Check if user is already logged in and auto-apply credits
    if session.get('user_id'):
        try:
            billing_service = BillingService()
            result = billing_service.add_credits(
                user_email=session.get('email'),
                credits=50,
                payment_method='promo_code',
                description='REI Connect 50 Credit Welcome Bonus'
            )
            if result.get('success'):
                flash('Welcome! 50 free credits have been added to your account!', 'success')
            else:
                flash('Welcome to REI Connect! Sign up to claim your 50 free credits.', 'info')
        except Exception as e:
            logging.error(f"Error applying REI Connect credits: {e}")
            flash('Welcome to REI Connect! Sign up to claim your 50 free credits.', 'info')
    else:
        flash('Welcome to REI Connect! Sign up now to claim your 50 free credits.', 'info')
    
    return render_template('rei_connect_landing.html',
                         google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY') or os.environ.get('GOOGLE_API_KEY'))

@app.route('/PFP-JV')
@app.route('/pfp-jv')
def pfp_jv_landing():
    """PFP Joint Venture Partnership landing page"""
    return render_template('pfp_jv.html')

@app.route('/dashboard')
def dashboard():
    """User Account Dashboard"""
    # For testing, set up a session for Devin if not already logged in
    if not session.get('user_id'):
        session['user_id'] = 'bfac25c4-7081-4eb6-8895-5dc09bb56d0a'
        session['email'] = 'devin@pfpsolutions.us'
    
    # Show welcome message for new users, then clear it after first visit
    show_welcome = session.get('new_user_welcome', False)
    if show_welcome:
        session.pop('new_user_welcome', None)
    
    return render_template('dashboard.html', show_welcome=show_welcome)

@app.route('/accept-invitation')
def accept_invitation():
    """Handle team invitation acceptance"""
    token = request.args.get('token')
    if not token:
        flash('Invalid invitation link', 'error')
        return redirect(url_for('index'))
    
    # Store the token in session for use after registration
    session['team_invite_token'] = token
    
    # Check if user is already logged in
    if session.get('user_id'):
        # Process the invitation for logged-in user
        billing_service = BillingService()
        result = billing_service.accept_team_invite(token, session.get('user_id'))
        if result.get('success'):
            flash('Successfully joined the team!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(result.get('error', 'Failed to accept invitation'), 'error')
            return redirect(url_for('index'))
    else:
        # Redirect to signup page with the token
        return redirect(url_for('signup', invite_token=token))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page with optional team invite token"""
    if request.method == 'GET':
        invite_token = request.args.get('invite_token')
        
        # If there's an invite token, verify it and get team info
        team_info = None
        if invite_token:
            billing_service = BillingService()
            invite_data = billing_service.get_team_invite_info(invite_token)
            if invite_data.get('success'):
                team_info = invite_data.get('team_info')
                session['team_invite_token'] = invite_token
        
        return render_template('auth/register.html', team_info=team_info)
    
    elif request.method == 'POST':
        # Handle registration
        logging.info("POST signup request received")
        
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        credit_code = request.form.get('credit_code')
        
        logging.info(f"Form data: email={email}, name={name}, credit_code={credit_code}")
        
        if not email:
            logging.error("Email is required")
            flash('Email is required', 'error')
            return render_template('auth/register.html')
        
        try:
            # Create user with billing service
            billing_service = BillingService()
            
            # Get invite token from session if present
            invite_token = session.get('team_invite_token')
            
            logging.info(f"Creating user with billing service: {email}")
            result = billing_service.create_user({
                'email': email,
                'name': name or email.split('@')[0],
                'password': password,
                'credit_code': credit_code,
                'invite_token': invite_token
            })
            
            logging.info(f"User creation result: {result}")
            
            if result.get('success'):
                user_id = result.get('user_id')
                team_name = result.get('team_name')
                
                # Set up consolidated session
                session['user_id'] = user_id
                session['user_email'] = email
                session['email'] = email  # Keep for backward compatibility
                session['team_id'] = result.get('team_id')
                session['team_role'] = result.get('role')
                
                logging.info(f"Session created for user: {email}")
                
                # Send welcome email immediately after successful registration
                try:
                    user_name = name or email.split('@')[0]
                    welcome_email_sent = email_service.send_welcome_email(email, user_name)
                    if welcome_email_sent:
                        logging.info(f"Welcome email sent successfully to {email}")
                    else:
                        logging.warning(f"Failed to send welcome email to {email}")
                except Exception as e:
                    logging.error(f"Error sending welcome email to {email}: {str(e)}")
                
                # Show appropriate welcome message
                if invite_token:
                    flash(f'Welcome! You\'ve successfully joined {team_name} and received analysis credits. Visit your dashboard to start analyzing properties.', 'success')
                    session.pop('team_invite_token', None)
                else:
                    flash('Welcome to Properwrite! Your account has been created and you\'ve received analysis credits. Visit your dashboard to manage your account or start analyzing properties.', 'success')
                
                # Set a flag to show new user welcome message
                session['new_user_welcome'] = True
                
                logging.info(f"Redirecting to dashboard for user: {email}")
                return redirect(url_for('dashboard'))
            else:
                logging.error(f"User creation failed: {result.get('error')}")
                flash(result.get('error', 'Registration failed'), 'error')
                return render_template('auth/register.html')
                
        except Exception as e:
            logging.error(f"Exception during signup: {str(e)}")
            import traceback
            logging.error(f"Signup traceback: {traceback.format_exc()}")
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Login page"""
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    elif request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember_me = request.form.get('remember-me')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
        
        billing_service = BillingService()
        result = billing_service.authenticate_user(email, password)
        
        if result.get('success'):
            # Set up consolidated session
            session['user_id'] = result.get('user_id')
            session['user_email'] = email
            session['email'] = email  # Keep for backward compatibility
            
            # Handle "Remember me" functionality
            if remember_me:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            else:
                session.permanent = False
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
            return render_template('auth/login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page and handler"""
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
@app.route('/api/forgot-password', methods=['POST'])
@limiter.limit("5 per minute")
def api_forgot_password():
    """Handle forgot password API request"""
    try:
        email = request.form.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Generate reset token
        import secrets
        reset_token = secrets.token_urlsafe(32)
        
        # Store reset token in session (in production, use database)
        session[f'reset_token_{email}'] = {
            'token': reset_token,
            'expires': datetime.now() + timedelta(hours=24)
        }
        
        # Send reset email
        try:
            email_sent = email_service.send_password_reset_email(email, reset_token)
            
            if email_sent:
                return jsonify({
                    'success': True,
                    'message': 'Password reset instructions sent to your email'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to send reset email. Please try again.'
                }), 500
                
        except Exception as e:
            logging.error(f"Error sending reset email: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to send reset email. Please try again.'
            }), 500
            
    except Exception as e:
        logging.error(f"Error in forgot password: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }), 500

@app.route('/reset-password/<token>')
def reset_password_page(token):
    """Display password reset page with token"""
    try:
        # Extract email from URL parameters
        email = request.args.get('email')
        
        if not email or not token:
            flash('Invalid reset link. Please request a new password reset.', 'error')
            return redirect(url_for('forgot_password'))
        
        # Verify reset token
        token_key = f'reset_token_{email}'
        stored_token = session.get(token_key)
        
        if not stored_token:
            flash('Reset link has expired. Please request a new password reset.', 'error')
            return redirect(url_for('forgot_password'))
        
        if stored_token['token'] != token:
            flash('Invalid reset link. Please request a new password reset.', 'error')
            return redirect(url_for('forgot_password'))
        
        if datetime.now() > stored_token['expires']:
            flash('Reset link has expired. Please request a new password reset.', 'error')
            return redirect(url_for('forgot_password'))
        
        return render_template('auth/reset_password.html', token=token, email=email)
        
    except Exception as e:
        logging.error(f"Error in reset password page: {str(e)}")
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('forgot_password'))

@app.route('/api/reset-password', methods=['POST'])
@limiter.limit("5 per minute")
def api_reset_password():
    """Handle password reset API request"""
    try:
        token = request.form.get('token')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([token, email, password, confirm_password]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'error': 'Passwords do not match'}), 400
        
        if len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters long'}), 400
        
        # Verify reset token
        token_key = f'reset_token_{email}'
        stored_token = session.get(token_key)
        
        if not stored_token:
            return jsonify({'success': False, 'error': 'Reset link has expired. Please request a new password reset.'}), 400
        
        if stored_token['token'] != token:
            return jsonify({'success': False, 'error': 'Invalid reset link. Please request a new password reset.'}), 400
        
        if datetime.now() > stored_token['expires']:
            return jsonify({'success': False, 'error': 'Reset link has expired. Please request a new password reset.'}), 400
        
        # Update password using billing service
        billing_service = BillingService()
        success = billing_service.update_user_password(email, password)
        
        if success:
            # Clear the reset token
            session.pop(token_key, None)
            
            return jsonify({
                'success': True,
                'message': 'Password updated successfully. You can now login with your new password.'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update password. Please try again.'
            }), 500
            
    except Exception as e:
        logging.error(f"Error in reset password API: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }), 500

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
    """Get current user status for frontend - consolidated session management"""
    try:
        # Check for user_id in session (primary identifier)
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'logged_in': False,
                'credits': 0,
                'unlimited_credits': False,
                'remaining_uses': 3
            })
        
        # Get user info from database
        with Session(engine) as db:
            user = db.query(User).filter(User.id == user_id).first()
            
            if user and user.is_active:
                # Get team info for unlimited credits check
                team_data = user.team
                unlimited_credits = team_data.tier == 'growth10' if team_data else False
                
                return jsonify({
                    'logged_in': True,
                    'user_id': user_id,
                    'email': session.get('user_email', session.get('email')),
                    'credits': team_data.credit_balance if team_data else 0,
                    'unlimited_credits': unlimited_credits,
                    'remaining_uses': 0  # Logged in users don't have use limits
                })
            else:
                # User not found or inactive, clear session completely
                session.clear()
                return jsonify({
                    'logged_in': False,
                    'credits': 0,
                    'unlimited_credits': False,
                    'remaining_uses': 3
                })
            
    except Exception as e:
        logging.error(f"Error getting user status: {str(e)}")
        return jsonify({
            'logged_in': False,
            'remaining_uses': 3,
            'credits': 0
        })

@app.route('/api/logout', methods=['POST'])
@csrf.exempt
def api_logout():
    """API logout endpoint for compatibility"""
    try:
        # Clear session completely
        session.clear()
        
        # Make session non-permanent to ensure it's cleared
        session.permanent = False
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully',
            'redirect': '/'
        })
    except Exception as e:
        logging.error(f"Error logging out: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Logout failed',
            'redirect': '/'
        }), 200  # Return 200 to prevent additional errors

@app.route('/logout', methods=['GET', 'POST'])
@csrf.exempt
def logout():
    """Standard logout route for compatibility"""
    try:
        # Clear session completely
        session.clear()
        
        # Make session non-permanent to ensure it's cleared
        session.permanent = False
        
        # Add success message
        flash('You have been logged out successfully.', 'success')
        
        # Redirect to homepage
        return redirect('/')
    except Exception as e:
        logging.error(f"Error logging out: {str(e)}")
        flash('Logout completed.', 'info')
        return redirect('/')

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
@csrf.exempt
def api_login():
    """Secure API login endpoint with proper password validation"""
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        email = data.get('email')
        password = data.get('password')
        remember_me = data.get('remember_me') == 'true' or data.get('remember_me') == True
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Use billing service for secure authentication
        billing_service = BillingService()
        result = billing_service.authenticate_user(email, password)
        
        if result.get('success'):
            # Set up consolidated session with permanent flag
            session.permanent = True
            session['user_id'] = result.get('user_id')
            session['user_email'] = email
            session['email'] = email  # Keep for backward compatibility
            
            # Handle remember me functionality
            if remember_me:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            else:
                session.permanent = False
            
            return jsonify({
                'success': True,
                'message': 'Logged in successfully',
                'user_id': session['user_id']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Invalid email or password')
            }), 401
            
    except Exception as e:
        logging.error(f"Error in API login: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Authentication error'
        }), 500

@app.route('/api/analyze-property', methods=['POST'])
@gate_feature('propertyAnalysis')
@limiter.limit("10 per minute, 100 per hour")
@csrf.exempt
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
        
        # Get comprehensive property valuation from multiple sources using unified service
        try:
            # Clean up the formatted address to remove duplicates before sending to APIs
            from address_utils import to_zillow_search_string, normalize_address_for_apis
            
            # Use the normalized address for API calls
            clean_address = normalize_address_for_apis(canonical_address['formatted_address'])
            
            logging.info(f"🐛 Cleaned address for APIs: {clean_address}")
            
            # Use unified property service for cache-aware data retrieval
            unified_service = get_unified_property_service()
            
            # Get property data with intelligent caching
            property_response = unified_service.get_property_data(
                address=clean_address,
                city=canonical_address['city'],
                state=canonical_address['state'],
                zip_code=canonical_address['zip'],
                place_id=canonical_address.get('place_id', ''),
                latitude=latitude,
                longitude=longitude
            )
            
            # Extract valuation data from unified response
            valuation_data = property_response.get('valuations', {})
            
            # Format valuation data for backward compatibility
            if not valuation_data:
                valuation_data = {
                    'valuations': {},
                    'sources_tried': property_response.get('data_sources', []),
                    'sources_used': property_response.get('data_sources', [])
                }
            else:
                # Ensure valuation_data has expected structure
                if isinstance(valuation_data, dict) and 'valuations' not in valuation_data:
                    valuation_data = {
                        'valuations': valuation_data,
                        'sources_tried': property_response.get('data_sources', []),
                        'sources_used': property_response.get('data_sources', [])
                    }
            
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
                
            # Extract Rentometer rent data
            if 'rentometer' in valuations:
                rentometer_data = valuations['rentometer']
                property_data['rentometer_estimate'] = rentometer_data.get('rent_estimate')
                property_data['rentometer_median'] = rentometer_data.get('rent_median')
                property_data['rentometer_range'] = rentometer_data.get('rent_range')
                property_data['rentometer_samples'] = rentometer_data.get('samples', 0)
                property_data['rentometer_confidence'] = rentometer_data.get('confidence', 'medium')
                property_data['rentometer_radius'] = rentometer_data.get('radius_miles', 0.2)
                property_data['rentometer_credits'] = rentometer_data.get('credits_remaining')
                
                # Use Rentometer as primary rent estimate if available
                if property_data.get('rentometer_estimate'):
                    property_data['rent_estimate'] = property_data['rentometer_estimate']
                    property_data['rent_data_source'] = 'Rentometer'
                    logging.info(f"Using Rentometer as primary rent source: ${property_data['rentometer_estimate']:,}/month")
                
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
                # Get user's team ID
                db = billing_service.db_session()
                user = db.query(User).filter_by(id=session['user_id']).first()
                if user and user.team_id:
                    result = billing_service.consume_credit(str(user.team_id), 'property_analysis')
                    if result.get('success'):
                        logging.info(f"Credit consumed. Remaining balance: {result.get('remaining_credits')}")
                    else:
                        logging.warning(f"Credit consumption failed: {result.get('error')}")
                db.close()
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

@app.route('/api/cache/stats', methods=['GET'])
@csrf.exempt
def get_cache_stats():
    """Get cache statistics"""
    try:
        unified_service = get_unified_property_service()
        stats = unified_service.get_cache_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logging.error(f"Cache stats error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get cache statistics'
        }), 500

@app.route('/api/cache/clear', methods=['POST'])
@csrf.exempt
def clear_cache():
    """Clear cache for specific address or all cache"""
    try:
        data = request.get_json()
        address = data.get('address') if data else None
        
        unified_service = get_unified_property_service()
        unified_service.clear_cache(address)
        
        return jsonify({
            'success': True,
            'message': f'Cache cleared for {address}' if address else 'All expired cache cleared'
        })
    except Exception as e:
        logging.error(f"Cache clear error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear cache'
        }), 500

@app.route('/api/cache/refresh', methods=['POST'])
@csrf.exempt
def refresh_cache():
    """Force refresh cache for specific address"""
    try:
        data = request.get_json()
        if not data or not data.get('address'):
            return jsonify({
                'success': False,
                'error': 'Address is required'
            }), 400
        
        address = data.get('address')
        city = data.get('city', '')
        state = data.get('state', '')
        zip_code = data.get('zip_code', '')
        
        unified_service = get_unified_property_service()
        property_data = unified_service.get_property_data(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            force_refresh=True
        )
        
        return jsonify({
            'success': True,
            'message': 'Cache refreshed successfully',
            'data': property_data
        })
    except Exception as e:
        logging.error(f"Cache refresh error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to refresh cache'
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
        square_feet = int(data.get('square_feet')) if data.get('square_feet') is not None else None
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
            square_feet=int(square_feet) if square_feet is not None else 1200,  # Only for calculations
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
            square_feet=int(square_feet) if square_feet is not None else 1200,  # Only for calculations
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
            square_feet=int(square_feet) if square_feet is not None else 1200  # Only for calculations
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
            square_feet=int(square_feet) if square_feet is not None else 1200  # Only for calculations
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
@gate_feature('aiAnalysis')
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
@gate_feature('acquisitions')
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
@gate_feature('acquisitions')
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
@csrf.exempt
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
        
        api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
        if not api_key:
            return jsonify({'error': 'Google Places API key not configured'}), 500
        
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
@csrf.exempt
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
        
        api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
        if not api_key:
            return jsonify({'error': 'Google Places API key not configured'}), 500
        
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

@app.route('/api/ai_buyer_persona', methods=['POST'])
def ai_buyer_persona():
    """
    AI-powered buyer persona analysis
    """
    try:
        from openai import OpenAI
        import os
        
        data = request.get_json()
        property_data = data.get('propertyData', {})
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        prompt = f"""You are a real estate investment expert analyzing a deal to identify the best buyer personas.

PROPERTY DATA:
- ARV: ${property_data.get('arv', 0):,}
- Repairs: ${property_data.get('repairs', 0):,}
- Monthly Rent: ${property_data.get('rent', 0):,}
- Bedrooms: {property_data.get('bedrooms', 3)}
- Bathrooms: {property_data.get('bathrooms', 2)}
- Square Feet: {property_data.get('sqft', 1200):,}
- Acquisition Price: ${property_data.get('acquisitionPrice', 0):,}

TASK: Identify and rank the top 3 buyer personas for this deal:

## 1. Primary Buyer Persona
- Type: [e.g., Fix-and-Flip Investor, Buy-and-Hold Landlord, etc.]
- Why They're Interested: [Key motivations]
- Price Range: $[their likely offer range]
- Timeline: [their typical closing timeline]
- Marketing Approach: [how to reach them]

## 2. Secondary Buyer Persona
- Type: [buyer type]
- Why They're Interested: [motivations]
- Price Range: $[offer range]
- Timeline: [closing timeline]
- Marketing Approach: [how to reach]

## 3. Tertiary Buyer Persona
- Type: [buyer type]
- Why They're Interested: [motivations]
- Price Range: $[offer range]
- Timeline: [closing timeline]
- Marketing Approach: [how to reach]

## Quick Action Plan
[3-4 bullet points on immediate next steps to find these buyers]

IMPORTANT: Do not use asterisks (*) in your response. Use regular text formatting only."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        
        return jsonify({
            'status': 'success',
            'analysis': response.choices[0].message.content
        })
        
    except Exception as e:
        logging.error(f"AI buyer persona error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/ai_buyer_pitch', methods=['POST'])
def ai_buyer_pitch():
    """
    AI-powered buyer pitch generator
    """
    try:
        from openai import OpenAI
        import os
        
        data = request.get_json()
        property_data = data.get('propertyData', {})
        strategy = data.get('strategy', 'Cash Sale')
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        prompt = f"""You are a real estate wholesaler creating a compelling buyer pitch.

PROPERTY DATA:
- Address: {property_data.get('address', 'Investment Property')}
- ARV: ${property_data.get('arv', 0):,}
- Repairs: ${property_data.get('repairs', 0):,}
- Monthly Rent: ${property_data.get('rent', 0):,}
- Your Acquisition Price: ${property_data.get('acquisitionPrice', 0):,}
- Exit Strategy: {strategy}

Create a compelling buyer pitch that includes:

## Subject Line
[Attention-grabbing email/text subject]

## Opening Hook
[1-2 sentences that create urgency and interest]

## Property Highlights
[3-4 bullet points showcasing the best features]

## The Numbers
[Present the financial opportunity clearly]

## Call to Action
[Strong closing with next steps]

## SMS/Text Version
[Shorter 2-3 sentence version for text messaging]

Keep the tone professional but exciting. Focus on ROI and profit potential.
IMPORTANT: Do not use asterisks (*) in your response. Use dashes (-) for bullet points."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=600
        )
        
        return jsonify({
            'status': 'success',
            'pitch': response.choices[0].message.content
        })
        
    except Exception as e:
        logging.error(f"AI buyer pitch error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/ai_buyer_objection', methods=['POST'])
def ai_buyer_objection():
    """
    AI-powered buyer objection handler
    """
    try:
        from openai import OpenAI
        import os
        
        data = request.get_json()
        objection = data.get('objection', '')
        objection_type = data.get('type', '')
        property_data = data.get('propertyData', {})
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        context = ""
        if objection_type:
            contexts = {
                'price': "Focus on demonstrating value and ROI.",
                'condition': "Address repair concerns and profit potential after repairs.",
                'location': "Highlight neighborhood strengths and rental demand.",
                'roi': "Break down the numbers and show multiple exit strategies.",
                'timeline': "Emphasize quick closing and easy transaction.",
                'competition': "Differentiate this deal from others on the market."
            }
            context = contexts.get(objection_type, '')
        
        prompt = f"""You are an experienced real estate wholesaler handling a buyer objection.

BUYER'S OBJECTION: "{objection}"

PROPERTY NUMBERS:
- ARV: ${property_data.get('arv', 0):,}
- Repairs: ${property_data.get('repairs', 0):,}
- Your Price: ${property_data.get('acquisitionPrice', 0):,}

{context}

Provide a professional response that:

## Acknowledge
[Show you understand their concern]

## Reframe
[Present a different perspective]

## Provide Evidence
[Use numbers, comparisons, or market data]

## Offer Solution
[Suggest a way forward]

## Close
[End with a question or next step]

Keep the response conversational and focused on moving the deal forward.
IMPORTANT: Do not use asterisks (*) in your response."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        return jsonify({
            'status': 'success',
            'response': response.choices[0].message.content
        })
        
    except Exception as e:
        logging.error(f"AI buyer objection error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
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

Format your response in clear sections with proper paragraph breaks:

EMPATHY:
[Empathetic acknowledgment in 1-2 sentences]

QUESTIONS:
- [First calibrated question]
- [Second calibrated question]  
- [Third calibrated question if needed]

SUGGESTED SOLUTION:
[One compelling solution or concession in 2-3 sentences]

SOFT CLOSE:
[Invitation to continue conversation in 1-2 sentences]

IMPORTANT: Do not use asterisks (*) or markdown headers (###) anywhere in your response. Use simple formatting with clear section labels and dashes (-) for bullet points."""

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

@app.route('/api/renovation/estimate', methods=['POST'])
@csrf.exempt
def renovation_estimate():
    """
    Calculate comprehensive renovation estimate based on property data and renovation scope
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        property_data = data.get('property_data', {})
        renovation_scope = data.get('renovation_scope', {})
        
        if not property_data:
            return jsonify({
                'success': False,
                'error': 'Property data is required'
            }), 400
        
        # Initialize renovation estimator service
        renovation_service = RenovationEstimatorService()
        
        # Calculate estimate
        estimate = renovation_service.calculate_renovation_estimate(
            property_data=property_data,
            renovation_scope=renovation_scope
        )
        
        return jsonify({
            'success': True,
            'estimate': estimate
        })
        
    except Exception as e:
        print(f"Error calculating renovation estimate: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/renovation/save', methods=['POST'])
@csrf.exempt  
def save_renovation_estimate():
    """
    Save renovation project to database
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        project_data = data.get('project_data', {})
        estimate_data = data.get('estimate_data', {})
        
        # Initialize renovation estimator service
        renovation_service = RenovationEstimatorService()
        
        # Save project
        result = renovation_service.save_renovation_project(
            project_data=project_data,
            estimate_data=estimate_data
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error saving renovation project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/comps/analyze', methods=['POST'])
@gate_feature('comps')
@csrf.exempt
def analyze_comps():
    """
    Analyze comparable properties using RapidAPI-Zillow integration
    Retrieves "Recently Sold" properties matching comp-selection rules
    """
    try:
        data = request.get_json()
        
        # Get property details from request or session
        address = data.get('address') or session.get('current_property', {}).get('address')
        beds = data.get('beds') or session.get('current_property', {}).get('beds') or 3
        baths = data.get('baths') or session.get('current_property', {}).get('baths') or 2
        sqft = data.get('sqft') or session.get('current_property', {}).get('sqft') or 1500
        lat = data.get('lat') or data.get('latitude') or session.get('current_property', {}).get('latitude')
        lng = data.get('lng') or data.get('longitude') or session.get('current_property', {}).get('longitude')
        
        # Additional parameters from frontend
        city = data.get('city') or session.get('current_property', {}).get('city') or ""
        state = data.get('state') or session.get('current_property', {}).get('state') or ""
        zip_code = data.get('zip_code') or session.get('current_property', {}).get('zip_code') or ""
        year_built = data.get('year_built') or session.get('current_property', {}).get('year_built') or 1950
        max_distance = data.get('max_distance', 0.5)
        days_filter = data.get('days_filter', 180)
        
        if not address:
            return jsonify({
                'success': False,
                'error': 'Property address is required for comparable analysis'
            }), 400
        
        # Extract zip code from address if not provided
        if not zip_code and address:
            import re
            # Look for 5-digit zip code after state abbreviation
            zip_match = re.search(r'\b[A-Z]{2}\s+(\d{5})\b', address)
            if zip_match:
                zip_code = zip_match.group(1)
            else:
                # Fallback: look for 5-digit code at the very end
                zip_match = re.search(r'\b(\d{5})(?:\s*,?\s*USA)?$', address)
                if zip_match:
                    zip_code = zip_match.group(1)
        
        logging.info(f"🔍 Comps analysis starting for: {address}")
        logging.info(f"🎯 Property specs: {beds} bed, {baths} bath, {sqft} sqft")
        logging.info(f"📅 Search parameters: {days_filter} days, {max_distance} mile radius")
        logging.info(f"🗺️ Location data: {city}, {state} {zip_code}")
        
        # Create search parameters for enhanced service
        # Uses beds/baths/sqft from Subject Property header for matching
        from enhanced_comps_service import SearchParams
        search_params = SearchParams(
            beds=int(beds),
            baths=float(baths),
            sqft=int(sqft),
            lat=lat or 0.0,
            lng=lng or 0.0,
            address=address,
            zip_code=zip_code
        )
        
        # SMART COMPS 2.0 SERVICE INTEGRATION
        # Rule-Adaptive Comparable Search with progressive relaxation
        from smart_comps_service import smart_comps_service
        
        # Search for comparable properties using Smart Comps 2.0
        result = smart_comps_service.search_comparable_properties(
            subject_address=address,
            subject_beds=int(beds),
            subject_baths=float(baths),
            subject_sqft=int(sqft),
            subject_lat=lat or 0.0,
            subject_lng=lng or 0.0,
            max_distance=max_distance,
            days_filter=days_filter
        )
        
        # If Smart Comps 2.0 service fails, fallback to unified service
        if not result.get('success') or not result.get('comps'):
            logging.warning("Smart Comps 2.0 service failed, falling back to unified service")
            
            try:
                unified_service = get_unified_property_service()
                unified_result = unified_service.get_comparable_properties(
                    address=address,
                    beds=int(beds),
                    baths=float(baths),
                    sqft=int(sqft),
                    lat=lat or 0.0,
                    lng=lng or 0.0
                )
                if unified_result.get('success') and unified_result.get('comps'):
                    result = unified_result
                    result['fallback_used'] = True
                    result['message'] = "Found comparable properties using cached data"
            except Exception as e:
                logging.error(f"Unified service fallback failed: {e}")
                
                # Final fallback to enhanced service
                try:
                    # Create search parameters with zip_code as positional argument
                    from enhanced_comps_service import SearchParams
                    enhanced_search_params = SearchParams(
                        beds=int(beds),
                        baths=float(baths),
                        sqft=int(sqft),
                        lat=lat or 0.0,
                        lng=lng or 0.0,
                        address=address,
                        zip_code=zip_code or ""
                    )
                    enhanced_result = enhanced_comps_service.search_comparable_sales(enhanced_search_params)
                    if enhanced_result.get('success') and enhanced_result.get('comps'):
                        result = enhanced_result
                        result['fallback_used'] = True
                        result['message'] = "Found comparable properties using enhanced search"
                except Exception as e:
                    logging.error(f"Enhanced service fallback failed: {e}")
                    
                    # Return a helpful error message with context
                    result = {
                        'success': False,
                        'comps': [],
                        'message': "Comparable properties temporarily unavailable due to API rate limits. Please try again in a few minutes.",
                        'error_type': 'rate_limit',
                        'fallback_used': True
                    }
        
        # Add analysis summary if successful
        if result.get('success') and result.get('comps'):
            result['ai_summary'] = result['analysis'].get('summary', '')
            result['recommended_arv'] = result['analysis'].get('recommended_arv', 0)
            
            # Add search metadata to response
            result['search_metadata'] = {
                'address': address,
                'beds': beds,
                'baths': baths,
                'sqft': sqft,
                'zip_code': zip_code,
                'max_distance': max_distance,
                'days_filter': days_filter,
                'coordinates': {'lat': lat, 'lng': lng} if lat and lng else None
            }
            
            logging.info(f"✅ Comps analysis successful: {result.get('found_count', 0)} properties found")
        else:
            logging.error(f"❌ Comps analysis failed: {result.get('error', 'Unknown error')}")
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error analyzing comparables: {e}")
        return jsonify({
            'success': False,
            'error': f'Comparable analysis failed: {str(e)}'
        }), 500

# Construction API Endpoints
@app.route('/api/construction/catalog', methods=['GET'])
def get_construction_catalog():
    """
    Get construction catalog items for Fix & Flip and New Construction
    """
    try:
        fix_flip_items = construction_service.get_catalog_items('fix_flip')
        new_construction_items = construction_service.get_catalog_items('new_construction')
        
        return jsonify({
            'success': True,
            'fix_flip': fix_flip_items,
            'new_construction': new_construction_items
        })
        
    except Exception as e:
        logging.error(f"Error getting construction catalog: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/construction/save-project', methods=['POST'])
@require_auth
@require_seat
def save_construction_project():
    """
    Save a construction project (Fix & Flip or New Construction)
    """
    try:
        data = request.get_json()
        
        # Get user ID from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Extract project data
        project_name = data.get('project_name', 'Untitled Project')
        project_type = data.get('project_type')
        property_address = data.get('property_address')
        property_sqft = data.get('property_sqft')
        line_items = data.get('line_items', [])
        multipliers = data.get('multipliers', {})
        
        # Calculate estimate
        if project_type == 'fix_flip':
            estimate = construction_service.calculate_fix_flip_estimate(line_items, multipliers)
        elif project_type == 'new_construction':
            land_cost = data.get('land_cost', 0)
            carry_costs = data.get('carry_costs', {})
            estimate = construction_service.calculate_new_construction_estimate(
                line_items, multipliers, land_cost, carry_costs
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid project type'
            }), 400
        
        # Save project
        project_id = construction_service.save_project_estimate(
            user_id=user_id,
            project_name=project_name,
            project_type=project_type,
            estimate_data={
                'line_items': line_items,
                'multipliers': multipliers,
                'estimate': estimate,
                'land_cost': land_cost if project_type == 'new_construction' else 0,
                'carry_costs': carry_costs if project_type == 'new_construction' else {}
            },
            property_address=property_address
        )
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'estimate': estimate
        })
        
    except Exception as e:
        logging.error(f"Error saving construction project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/construction/search', methods=['GET'])
def search_construction_items():
    """
    Search construction catalog items
    """
    try:
        project_type = request.args.get('project_type')
        search_term = request.args.get('search_term', '')
        
        if not project_type:
            return jsonify({
                'success': False,
                'error': 'Project type is required'
            }), 400
        
        items = construction_service.search_catalog_items(project_type, search_term)
        
        return jsonify({
            'success': True,
            'items': items
        })
        
    except Exception as e:
        logging.error(f"Error searching construction items: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/construction/trades', methods=['GET'])
def get_construction_trades():
    """
    Get all trade categories for a project type
    """
    try:
        project_type = request.args.get('project_type')
        
        if not project_type:
            return jsonify({
                'success': False,
                'error': 'Project type is required'
            }), 400
        
        trades = construction_service.get_trade_categories(project_type)
        
        return jsonify({
            'success': True,
            'trades': trades
        })
        
    except Exception as e:
        logging.error(f"Error getting construction trades: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/renovation/estimate', methods=['POST'])
@require_auth
def calculate_renovation_estimate():
    """
    Calculate comprehensive renovation estimate based on professional template
    """
    try:
        data = request.get_json()
        
        # Extract property data
        property_data = data.get('property_data', {})
        
        # Extract renovation scope
        renovation_scope = data.get('renovation_scope', {})
        
        # Calculate comprehensive estimate
        estimate = renovation_estimator.calculate_comprehensive_estimate(
            property_data, renovation_scope
        )
        
        return jsonify({
            'success': True,
            'estimate': estimate
        })
    except Exception as e:
        logging.error(f"Error calculating renovation estimate: {e}")
        return jsonify({'error': 'Failed to calculate renovation estimate'}), 500


@app.route('/api/renovation/save', methods=['POST'])
@require_auth
def save_renovation_project():
    """
    Save renovation project estimate
    """
    try:
        data = request.get_json()
        
        # Extract project data
        project_data = data.get('project_data', {})
        estimate_data = data.get('estimate_data', {})
        
        # Save to database
        result = renovation_estimator.save_renovation_estimate(
            project_data, estimate_data
        )
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error saving renovation project: {e}")
        return jsonify({'error': 'Failed to save renovation project'}), 500


@app.route('/api/renovation/load/<project_id>', methods=['GET'])
@require_auth
def load_renovation_project(project_id):
    """
    Load saved renovation project
    """
    try:
        # Load from database
        project = renovation_estimator.get_renovation_estimate(project_id)
        
        return jsonify({
            'success': True,
            'project': project
        })
    except Exception as e:
        logging.error(f"Error loading renovation project: {e}")
        return jsonify({'error': 'Failed to load renovation project'}), 500

# ===============================
# JV Deal Submit Routes
# ===============================

@app.route('/jv-submit')
def jv_submit_page():
    """JV Deal Submit page"""
    return render_template('jv_submit.html', 
                         google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY') or os.environ.get('GOOGLE_API_KEY'))

@app.route('/api/jv-deals', methods=['POST'])
@limiter.limit("10 per minute")  # Increased limit for testing
@csrf.exempt  # Exempt from CSRF for API endpoint
def jv_deals_submit():
    """
    Submit JV deal with MAO analysis and approval logic
    """
    try:
        # Handle FormData submission
        data = {}
        
        # Extract form data
        for key, value in request.form.items():
            if key != 'csrf_token':
                data[key] = value
        
        # Parse MAO analysis if provided
        mao_analysis_json = request.form.get('mao_analysis')
        mao_analysis = json.loads(mao_analysis_json) if mao_analysis_json else None
        
        # Map form fields to expected format
        mapped_data = {
            'partner_name': data.get('name'),
            'partner_email': data.get('email'),
            'partner_phone': data.get('phone'),
            'partner_company': data.get('company', ''),
            'partner_markets': data.get('markets', '').split(',') if data.get('markets') else [],
            'property_address': data.get('address'),
            'property_city': data.get('city'),
            'property_state': data.get('state'),
            'property_zip': data.get('zip'),
            'deal_type': 'wholesale',  # Default for JV deals
            'seller_asking_price': data.get('asking_price'),
            'arv': data.get('arv'),
            'rehab_needed': 'yes' if data.get('rehab_cost') else 'no',
            'rehab_cost': data.get('rehab_cost', '0'),
            'property_status': data.get('property_status'),
            'closing_date': data.get('closing_date'),
            'property_description': data.get('property_description', ''),
            'photo_link': data.get('photo_link', ''),
            'additional_notes': data.get('additional_notes', ''),
            'mao_analysis': mao_analysis
        }
        
        # Create or get partner record
        from jv_database import jv_db
        
        partner_id = jv_db.create_or_get_partner(
            name=mapped_data.get('partner_name'),
            email=mapped_data.get('partner_email'),
            phone=mapped_data.get('partner_phone'),
            company=mapped_data.get('partner_company'),
            markets=mapped_data.get('partner_markets', [])
        )
        
        # Enhanced auto-underwrite with MAO analysis
        underwrite_result = auto_underwrite_deal_with_mao(mapped_data, mao_analysis)
        
        # Prepare deal data for database storage
        deal_data = {
            'property_address': mapped_data.get('property_address'),
            'street': mapped_data.get('street', ''),
            'city': mapped_data.get('property_city'),
            'state': mapped_data.get('property_state'),
            'zip_code': mapped_data.get('property_zip'),
            'asking_price': float(mapped_data.get('seller_asking_price', 0)),
            'arv': float(mapped_data.get('arv', 0)),
            'repair_estimate': float(mapped_data.get('rehab_cost', 0)),
            'suggested_offer': underwrite_result.get('suggested_offer', 0),
            'status': 'pending',
            'auto_evaluation': underwrite_result.get('recommendation', 'needs_review'),
            'evaluation_reasons': underwrite_result.get('reasons', []),
            'admin_notes': '',
            'submission_data': mapped_data,
            'mao_analysis': mao_analysis
        }
        
        # Submit deal to database
        deal_id = jv_db.create_deal_submission(
            partner_id=partner_id,
            deal_data=deal_data,
            auto_status=underwrite_result.get('recommendation', 'needs_review'),
            reasons=underwrite_result.get('reasons', [])
        )
        
        # Trigger Zapier webhook for new JV submission
        from zapier_webhook_service import trigger_jv_submission
        trigger_jv_submission({
            'id': deal_id,
            'address': deal_data['property_address'],
            'user_id': partner_id,
            'partner_name': mapped_data.get('partner_name'),
            'partner_email': mapped_data.get('partner_email'),
            'asking_price': deal_data['asking_price'],
            'arv': deal_data['arv'],
            'auto_evaluation': deal_data['auto_evaluation'],
            'submitted_at': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'success': True,
            'deal_id': deal_id,
            'analysis': mao_analysis,
            'underwrite_result': underwrite_result,
            'message': 'Deal submitted successfully!'
        })
        
    except Exception as e:
        logging.error(f"Error submitting JV deal: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/jv-submit', methods=['POST'])
@limiter.limit("10 per minute")  # Increased limit for testing
@csrf.exempt  # Exempt from CSRF for API endpoint
def jv_submit_deal():
    """
    Submit and auto-underwrite JV deal with partner information
    """
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Map form fields to expected partner fields
        partner_name = data.get('name') or data.get('partner_name')
        partner_email = data.get('email') or data.get('partner_email')
        partner_phone = data.get('phone') or data.get('partner_phone')
        partner_company = data.get('company') or data.get('partner_company', '')
        partner_markets = data.get('markets') or data.get('partner_markets', [])
        
        # Validate required partner fields
        if not partner_name:
            return jsonify({
                'success': False,
                'error': 'Partner name is required'
            }), 400
            
        if not partner_email:
            return jsonify({
                'success': False,
                'error': 'Partner email is required'
            }), 400
            
        if not partner_phone:
            return jsonify({
                'success': False,
                'error': 'Partner phone is required'
            }), 400
        
        # Validate partner name (at least 2 words)
        name_parts = (partner_name or '').strip().split()
        if len(name_parts) < 2:
            return jsonify({
                'success': False,
                'error': 'Full name must contain at least two words'
            }), 400
        
        # Handle markets - for now, default to NC and SC since form doesn't include markets selection
        if isinstance(partner_markets, str):
            partner_markets = [partner_markets] if partner_markets else ['NC', 'SC']
        elif not partner_markets:
            partner_markets = ['NC', 'SC']  # Default markets for JV deals
        
        # Map and validate deal fields
        property_address = data.get('address') or data.get('property_address')
        asking_price = data.get('asking_price')
        arv = data.get('arv')
        
        if not property_address:
            return jsonify({
                'success': False,
                'error': 'Property address is required'
            }), 400
            
        if not asking_price:
            return jsonify({
                'success': False,
                'error': 'Asking price is required'
            }), 400
            
        if not arv:
            return jsonify({
                'success': False,
                'error': 'ARV (After Repair Value) is required'
            }), 400
        
        # Create or get partner record
        from jv_database import jv_db
        
        partner_id = jv_db.create_or_get_partner(
            name=partner_name,
            email=partner_email,
            phone=partner_phone,
            company=partner_company,
            markets=partner_markets
        )
        
        # Auto-underwrite the deal
        underwrite_result = auto_underwrite_deal(data)
        
        # Prepare deal data for database storage
        deal_data = {
            'property_address': property_address,
            'street': data.get('street', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'zip': data.get('zip', ''),
            'deal_type': data.get('deal_type', 'Cash'),
            'purchase_price': data.get('purchase_price'),
            'seller_asking_price': data.get('asking_price'),  # Form uses 'asking_price'
            'arv': data.get('arv'),
            'rehab_needed': data.get('rehab_needed'),
            'rehab_cost': data.get('rehab_cost'),
            'property_description': data.get('property_description', ''),
            'photos_link': data.get('photos_link', ''),
            'property_status': data.get('property_status', 'Vacant'),
            'closing_date': data.get('closing_date', ''),
            'additional_notes': data.get('additional_notes', ''),
            'underwrite_result': underwrite_result,
            'partner_info': {
                'name': partner_name,
                'email': partner_email,
                'phone': partner_phone,
                'company': partner_company,
                'markets': partner_markets
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
        from zapier_webhook_service import ZapierWebhookService
        from datetime import datetime
        
        webhook_data = {
            'id': deal_id,
            'property_address': property_address,
            'property_city': data.get('city'),
            'property_state': data.get('state'),
            'asking_price': asking_price,
            'suggested_offer': data.get('purchase_price'),
            'arv': arv,
            'repair_estimate': data.get('rehab_cost'),
            'partner_name': partner_name,
            'partner_email': partner_email,
            'partner_phone': partner_phone,
            'partner_company': data.get('partner_company'),
            'partner_markets': partner_markets,
            'created_at': datetime.utcnow().isoformat(),
            'auto_evaluation': underwrite_result.get('status'),
            'evaluation_reasons': underwrite_result.get('reasons', [])
        }
        
        try:
            webhook_service = ZapierWebhookService()
            webhook_service.trigger_new_jv_submission(webhook_data)
        except Exception as webhook_error:
            logging.error(f"Webhook error: {webhook_error}")
            # Don't fail the main operation if webhook fails
        
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

# Old JV admin route removed - replaced by dedicated JV admin system at /jv-admin/login

# Old JV admin partner route removed - replaced by dedicated JV admin system

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
@csrf.exempt
@require_auth
def create_checkout():
    """Create Stripe checkout session for subscription or credit purchase"""
    try:
        data = request.get_json()
        lookup_key = data.get('lookup_key')
        quantity = data.get('quantity', 1)
        
        if not lookup_key:
            return jsonify({'error': 'lookup_key is required'}), 400
        
        # Get promo code from session if available
        promo_code = session.get('auto_promo_code')
        
        # Create checkout session
        result = billing_service.create_checkout_session(
            lookup_key=lookup_key,
            quantity=quantity,
            customer_email=g.current_user['email'],
            team_id=g.current_user['team_id'],
            success_url=request.url_root + 'billing/success',
            cancel_url=request.url_root + 'billing/cancel',
            promo_code=promo_code
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

@app.route('/api/billing/change-plan', methods=['POST'])
@csrf.exempt
@require_auth
def change_plan():
    """Change team's subscription plan"""
    try:
        data = request.get_json()
        new_plan_key = data.get('plan_key')
        
        if not new_plan_key:
            return jsonify({'error': 'plan_key is required'}), 400
        
        result = billing_service.change_plan(
            team_id=g.current_user['team_id'],
            new_plan_key=new_plan_key,
            user_id=g.current_user['id']
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error changing plan: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/billing/history')
@require_auth
def get_billing_history():
    """Get billing history for current user's team"""
    try:
        history = billing_service.get_billing_history(
            team_id=g.current_user['team_id'],
            limit=50
        )
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        logging.error(f"Error getting billing history: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/billing/subscription-details', methods=['GET'])
def get_subscription_details():
    """Get comprehensive subscription details"""
    try:
        # Check for user_id in session (same as user-status endpoint)
        user_id = session.get('user_id')
        logging.info(f"Subscription details - user_id from session: {user_id}")
        if not user_id:
            logging.warning("No user_id found in session for subscription details")
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Get user and team info (same as user-status endpoint)
        with Session(engine) as db:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                return jsonify({'success': False, 'error': 'User not found or inactive'}), 404
            
            team_data = user.team
            if not team_data:
                return jsonify({'success': False, 'error': 'Team not found'}), 404
        
        # Return subscription details (similar to user-status endpoint)
        plan_name = team_data.tier.upper() if team_data.tier else 'STARTER'
        if plan_name == 'GROWTH10':
            plan_name = 'Growth10'
        elif plan_name == 'TEAM5':
            plan_name = 'Team5'
        elif plan_name == 'PRO':
            plan_name = 'Pro'
        
        # Get current team member count
        team_member_count = db.query(User).filter(User.team_id == team_data.id, User.is_active == True).count()
        
        # Calculate renewal date (placeholder - you can implement actual Stripe subscription date logic later)
        from datetime import datetime, timedelta
        renewal_date = datetime.now() + timedelta(days=30)
        
        return jsonify({
            'success': True,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'name': user.name or 'User'
            },
            'team': {
                'id': str(team_data.id),
                'name': team_data.name,
                'plan': plan_name,
                'tier': team_data.tier,
                'credit_balance': team_data.credit_balance,
                'unlimited_credits': team_data.tier == 'growth10',
                'seats_used': team_member_count,
                'seats_max': team_data.seats_max,
                'renewal_date': renewal_date.strftime('%b %d')
            },
            'subscription': {
                'status': 'active',
                'plan_name': plan_name,
                'billing_cycle': 'monthly',
                'next_billing_date': renewal_date.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting subscription details: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/team/members', methods=['GET'])
def get_team_members():
    """Get team members"""
    try:
        # Check for user_id in session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Get user and team info
        with Session(engine) as db:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                return jsonify({'success': False, 'error': 'User not found or inactive'}), 404
            
            team_data = user.team
            if not team_data:
                return jsonify({'success': False, 'error': 'Team not found'}), 404
            
            # Get all team members
            team_members = db.query(User).filter(User.team_id == team_data.id, User.is_active == True).all()
            
            members_data = []
            for member in team_members:
                members_data.append({
                    'id': str(member.id),
                    'name': member.name or 'User',
                    'email': member.email,
                    'role': member.role or 'analyst',
                    'is_active': member.is_active,
                    'last_active': member.created_at.isoformat() if member.created_at else None
                })
            
            return jsonify({
                'success': True,
                'members': members_data
            })
        
    except Exception as e:
        logging.error(f"Error getting team members: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/billing/update-payment-method', methods=['POST'])
@require_auth
def update_payment_method():
    """Update default payment method"""
    try:
        data = request.get_json()
        payment_method_id = data.get('payment_method_id')
        
        if not payment_method_id:
            return jsonify({'error': 'Payment method ID required'}), 400
        
        team_id = g.current_user['team_id']
        
        # Update payment method
        result = billing_service.update_payment_method(team_id, payment_method_id)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error updating payment method: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/billing/cancel-subscription', methods=['POST'])
@require_auth
def cancel_subscription():
    """Cancel subscription"""
    try:
        data = request.get_json()
        subscription_id = data.get('subscription_id')
        
        if not subscription_id:
            return jsonify({'error': 'Subscription ID required'}), 400
        
        team_id = g.current_user['team_id']
        
        # Cancel subscription
        result = billing_service.cancel_subscription(team_id, subscription_id)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error cancelling subscription: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/billing/change-plan', methods=['POST'])
@require_auth
def change_subscription_plan():
    """Change subscription plan"""
    try:
        data = request.get_json()
        new_plan_id = data.get('plan_id')
        
        if not new_plan_id:
            return jsonify({'error': 'Plan ID required'}), 400
        
        team_id = g.current_user['team_id']
        
        # Change plan
        result = billing_service.change_subscription_plan(team_id, new_plan_id)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error changing subscription plan: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/billing/download-invoice', methods=['POST'])
@require_auth
def download_invoice():
    """Get invoice download URL"""
    try:
        data = request.get_json()
        invoice_id = data.get('invoice_id')
        
        if not invoice_id:
            return jsonify({'error': 'Invoice ID required'}), 400
        
        team_id = g.current_user['team_id']
        
        # Get invoice download URL
        result = billing_service.download_invoice(team_id, invoice_id)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error downloading invoice: {e}")
        return jsonify({'error': 'Internal server error'}), 500

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
    """Create team invitation (managers and owners only) - consolidated"""
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
    """Get all team invites (pending, accepted, cancelled)"""
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
            
            # Get all invites for this team (pending, accepted, cancelled)
            invites = db.query(TeamInvite).filter(
                TeamInvite.team_id == user.team_id
            ).order_by(TeamInvite.created_at.desc()).all()
            
            invite_list = []
            for invite in invites:
                invite_data = {
                    'id': str(invite.id),
                    'email': invite.email,
                    'role': invite.role,
                    'created_at': invite.created_at.isoformat(),
                    'status': invite.status
                }
                
                # Add accepted_at timestamp if the invite was accepted
                if invite.accepted_at:
                    invite_data['accepted_at'] = invite.accepted_at.isoformat()
                
                invite_list.append(invite_data)
            
            return jsonify({
                'success': True,
                'invites': invite_list
            })
            
    except Exception as e:
        logging.error(f"Error getting pending invites: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/team/invite/<invite_id>/resend', methods=['POST'])
@csrf.exempt
def resend_invite(invite_id):
    """Resend a team invitation - consolidated with session auth"""
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
@csrf.exempt
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

# ==================== PROFILE UPDATE ENDPOINTS ====================

@app.route('/api/update-profile', methods=['POST'])
@require_auth
def update_profile():
    """Update user profile (name and email)"""
    try:
        data = request.get_json()
        new_name = data.get('name', '').strip()
        new_email = data.get('email', '').strip()
        
        if not new_name or not new_email:
            return jsonify({'success': False, 'error': 'Name and email are required'}), 400
        
        # Basic email validation
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, new_email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Get current user ID from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Update user profile in database
        billing_service = BillingService()
        with billing_service.db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Check if email is already taken by another user
            existing_user = db.query(User).filter(
                User.email == new_email,
                User.id != user_id
            ).first()
            
            if existing_user:
                return jsonify({'success': False, 'error': 'Email address is already in use'}), 409
            
            # Update user fields
            user.name = new_name
            user.email = new_email
            
            # Commit changes
            db.commit()
            
            # Update session information
            session['user_email'] = new_email
            session['email'] = new_email
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'user': {
                    'name': user.name,
                    'email': user.email
                }
            })
            
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Current password and new password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'New password must be at least 6 characters long'}), 400
        
        # Get current user ID from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        # Verify current password and update to new password
        billing_service = BillingService()
        with billing_service.db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Verify current password
            from werkzeug.security import check_password_hash, generate_password_hash
            if not user.password_hash or not check_password_hash(user.password_hash, current_password):
                return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
            
            # Generate new password hash
            new_password_hash = generate_password_hash(new_password)
            
            # Update password
            user.password_hash = new_password_hash
            
            # Commit changes
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'Password changed successfully'
            })
            
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

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

@app.route('/ref/<affiliate_code>')
def affiliate_redirect(affiliate_code):
    """Handle affiliate link clicks and auto-apply promo codes"""
    try:
        # Define affiliate to promo code mapping
        affiliate_promo_map = {
            'AFF001': 'AFF001',
            'AFF002': 'AFF002', 
            'AFF003': 'AFF003',
            'WELCOME': 'WELCOME50',
            'STARTER': 'STARTER100',
            'CG40': 'CG40'
        }
        
        promo_code = affiliate_promo_map.get(affiliate_code)
        
        if promo_code:
            # Store promo code in session for auto-application
            session['auto_promo_code'] = promo_code
            session['affiliate_code'] = affiliate_code
            
            # Log the click for tracking
            logging.info(f"Affiliate link clicked: {affiliate_code}, promo code: {promo_code}")
            
            # Add flash message to show promo code applied
            flash(f'Welcome! Promo code {promo_code} has been applied to your account.', 'success')
            
            # Redirect to homepage
            return redirect(url_for('index'))
        else:
            # Invalid affiliate code, redirect to homepage
            logging.warning(f"Invalid affiliate code: {affiliate_code}")
            flash('Invalid affiliate link. Please try again.', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        logging.error(f"Error handling affiliate link: {e}")
        return redirect(url_for('index'))

@app.route('/affiliate-links')
def affiliate_links():
    """Show affiliate links for easy copying"""
    return render_template('affiliate_links.html')

# ===============================
# JV Deals Admin Panel Routes
# ===============================

@app.route('/jv-admin/login', methods=['GET', 'POST'])
@csrf.exempt
def jv_admin_login():
    """JV Admin Login - Separate from main admin"""
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Get JV admin password hash from environment variable
        jv_admin_password_hash = os.environ.get('JV_ADMIN_PASSWORD_HASH')
        
        if not jv_admin_password_hash:
            # Fallback to main admin password if JV-specific not set
            jv_admin_password_hash = os.environ.get('ADMIN_PASSWORD_HASH')
            
        if not jv_admin_password_hash:
            return render_template('jv_admin_login.html', error='JV admin access is disabled. Please configure password.')
        
        # Check password against hash
        if password and check_password_hash(jv_admin_password_hash, password):
            session['is_jv_admin'] = True
            session['jv_admin_user_id'] = 'jv_admin_1'
            logging.info(f"JV admin login successful from IP: {request.remote_addr}")
            return redirect('/jv-admin/dashboard')
        
        logging.warning(f"Failed JV admin login attempt from IP: {request.remote_addr}")
        return render_template('jv_admin_login.html', error='Invalid password')
    
    return render_template('jv_admin_login.html')

@app.route('/jv-admin/logout')
def jv_admin_logout():
    """JV Admin Logout"""
    session.pop('is_jv_admin', None)
    session.pop('jv_admin_user_id', None)
    flash('You have been logged out of the JV admin panel.', 'info')
    return redirect('/jv-admin/login')

@app.route('/jv-admin/dashboard')
def jv_admin_dashboard():
    """JV Admin Dashboard - Direct access to enhanced JV panel"""
    # Check if user has JV admin permissions
    if not session.get('is_jv_admin'):
        flash('Access denied. JV admin permissions required.', 'error')
        return redirect('/jv-admin/login')
    
    return render_template('admin_jv_deals_enhanced.html')

# Update the existing enhanced JV deals route to use JV admin auth
@app.route('/admin/jv-deals-enhanced')
def admin_jv_deals_enhanced():
    """Enhanced JV Deals Admin Panel - Redirect to dedicated JV admin"""
    # Redirect to dedicated JV admin system
    return redirect('/jv-admin/login')

# ===============================
# Team JV Queue Routes
# ===============================

@app.route('/team/jv-queue')
@require_auth
def team_jv_queue():
    """Team-side JV queue viewer (read-only)"""
    return render_template('team_jv_queue.html')

@app.route('/api/team/jv-deals', methods=['GET'])
@require_auth
def get_team_jv_deals():
    """Get JV deals for current team"""
    try:
        # Get user's team ID
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        # Get user's team information
        billing_service = BillingService()
        user_info = billing_service.get_user_info(user_id)
        if not user_info:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
        team_id = user_info.get('team_id')
        if not team_id:
            return jsonify({'success': False, 'error': 'User not part of any team'}), 400
        
        # Get team deals from database
        from jv_database import JVDatabase
        jv_db = JVDatabase()
        
        # Get team deals
        deals = jv_db.get_team_jv_deals(team_id)
        
        # Get team members for filter
        team_members = jv_db.get_team_members(team_id)
        
        # Calculate metrics
        total_submitted = len(deals)
        pending_count = len([d for d in deals if d.get('status') == 'pending'])
        approved_count = len([d for d in deals if d.get('status') == 'approved'])
        
        return jsonify({
            'success': True,
            'deals': deals,
            'team_members': team_members,
            'metrics': {
                'total_submitted': total_submitted,
                'pending_count': pending_count,
                'approved_count': approved_count
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting team JV deals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/jv-submit')
def jv_submit():
    """Serve the JV submission page"""
    try:
        # Get Google Maps API key for the template (same as working form)
        google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
        return render_template('jv_submit.html', google_maps_api_key=google_maps_api_key)
    except Exception as e:
        logging.error(f"Error serving JV submit page: {e}")
        flash('Error loading JV submission page', 'error')
        return redirect(url_for('index'))

@app.route('/api/jv-deals', methods=['POST'])
def submit_jv_deal():
    """Submit a new JV deal"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'phone', 'address', 'deal_type', 'asking_price', 'arv']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate email format
        import re
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate phone format
        phone_regex = r'^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$'
        if not re.match(phone_regex, data['phone']):
            return jsonify({'error': 'Invalid phone format'}), 400
        
        # Import JV database
        from jv_database import JVDatabase
        jv_db = JVDatabase()
        
        # Check if address is cached for optimization
        cached_address = None
        try:
            from services.unified_property_data_service import get_unified_property_service
            unified_service = get_unified_property_service()
            cached_address = unified_service.get_cached_address_data(data['address'])
        except Exception as e:
            logging.warning(f"Could not check address cache: {e}")
        
        # Auto-underwrite the deal
        try:
            underwriting_result = auto_underwrite_deal({
                'address': data['address'],
                'asking_price': float(data['asking_price']),
                'arv': float(data['arv']),
                'rehab_cost': float(data.get('rehab_cost', 0)),
                'deal_type': data['deal_type']
            })
        except Exception as e:
            logging.warning(f"Auto-underwriting failed: {e}")
            underwriting_result = {'status': 'needs_review', 'reason': 'Auto-underwriting unavailable'}
        
        # Create partner record
        partner_data = {
            'email': data['email'],
            'phone': data['phone'],
            'name': data.get('name', ''),
            'company': data.get('company', ''),
            'markets': data.get('markets', [])
        }
        
        partner_id = jv_db.create_or_update_partner(partner_data)
        
        # Create JV deal record
        deal_data = {
            'partner_id': partner_id,
            'address': data['address'],
            'deal_type': data['deal_type'],
            'asking_price': float(data['asking_price']),
            'arv': float(data['arv']),
            'rehab_cost': float(data.get('rehab_cost', 0)),
            'photo_link': data.get('photo_link', ''),
            'status': underwriting_result.get('status', 'pending'),
            'auto_evaluation': underwriting_result.get('status', 'needs_review'),
            'evaluation_reasons': underwriting_result.get('reasons', []),
            'submission_data': data,
            'cached_address': cached_address
        }
        
        deal_id = jv_db.create_jv_deal(deal_data)
        
        # Send Zapier webhook notification
        try:
            from zapier_webhook_service import zapier_webhook_service
            webhook_data = {
                'deal_id': deal_id,
                'partner_email': data['email'],
                'partner_phone': data['phone'],
                'address': data['address'],
                'deal_type': data['deal_type'],
                'asking_price': data['asking_price'],
                'arv': data['arv'],
                'rehab_cost': data.get('rehab_cost', 0),
                'status': deal_data['status'],
                'auto_evaluation': deal_data['auto_evaluation'],
                'submitted_at': datetime.now().isoformat()
            }
            
            zapier_webhook_service.trigger_new_jv_submission(webhook_data)
            logging.info(f"Zapier webhook sent for deal {deal_id}")
        except Exception as e:
            logging.error(f"Failed to send Zapier webhook: {e}")
        
        # Return success response
        return jsonify({
            'success': True,
            'deal_id': deal_id,
            'status': deal_data['status'],
            'message': 'Deal submitted successfully! We\'ll review it and get back to you soon.'
        })
        
    except Exception as e:
        logging.error(f"Error submitting JV deal: {e}")
        return jsonify({'error': 'Failed to submit deal. Please try again.'}), 500

# Freemium Access Gate API Endpoints
@app.route('/api/freemium/clear-cookie', methods=['POST'])
def clear_freemium_cookie():
    """Clear the free use cookie for testing"""
    response = make_response(jsonify({'success': True, 'message': 'Free use cookie cleared'}))
    # Clear the cookie by setting it to empty with past expiration
    response.set_cookie('free_use', '', expires=0, path='/', samesite='Lax')
    # Also try alternative clearing method
    response.set_cookie('free_use', '', max_age=0, path='/', samesite='Lax')
    return response

@app.route('/api/freemium/status', methods=['GET'])
def api_freemium_status():
    """Get freemium access status"""
    try:
        # Check if user is authenticated
        user_id = session.get('user_id')
        if user_id:
            return jsonify({
                'authenticated': True,
                'free_use_available': False,
                'free_use_used': False
            })
        
        # Get free use status from cookies
        free_use_status = check_free_use_status()
        
        return jsonify({
            'authenticated': False,
            'free_use_available': free_use_status.get('free_use_available', True),
            'free_use_used': free_use_status.get('free_use_used', False)
        })
        
    except Exception as e:
        logging.error(f"Error getting freemium status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/freemium/feature-access/<feature_name>', methods=['GET'])
def api_feature_access(feature_name):
    """Get access information for a specific feature"""
    try:
        # Check if user is authenticated
        user_id = session.get('user_id')
        if user_id:
            return jsonify({
                'accessible': True,
                'reason': 'authenticated',
                'message': 'Access granted for authenticated user'
            })
        
        # Get feature access info
        access_info = get_feature_access_info(feature_name)
        
        return jsonify(access_info)
        
    except Exception as e:
        logging.error(f"Error getting feature access: {e}")
        return jsonify({
            'accessible': False,
            'reason': 'error',
            'message': 'Error checking feature access'
        }), 500

# ========================================
# SUBJECT-TO LEAD SUBMISSION SYSTEM
# ========================================
from subto_database import subto_db

@app.route('/subto-register', methods=['GET', 'POST'])
def subto_register():
    """Subject-To submitter registration"""
    if request.method == 'GET':
        return render_template('subto_register.html')
    
    try:
        # Get form data
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        name = request.form.get('name', '').strip()
        company = request.form.get('company', '').strip()
        phone = request.form.get('phone', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip().upper()
        
        # Validate required fields
        if not all([email, password, name]):
            flash('Email, password, and name are required', 'error')
            return redirect(url_for('subto_register'))
        
        # Create submitter account
        submitter_id = subto_db.create_submitter(email, password, name, company, phone, city, state)
        
        if not submitter_id:
            flash('An account with this email already exists', 'error')
            return redirect(url_for('subto_register'))
        
        # Auto-login after registration
        session['subto_submitter_id'] = submitter_id
        session['subto_submitter_name'] = name
        session.permanent = True
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('subto_dashboard'))
        
    except Exception as e:
        logging.error(f"Error in submitter registration: {e}")
        flash('Registration failed. Please try again.', 'error')
        return redirect(url_for('subto_register'))

@app.route('/subto-login', methods=['GET', 'POST'])
def subto_login():
    """Subject-To submitter login"""
    if request.method == 'GET':
        return render_template('subto_login.html')
    
    try:
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not all([email, password]):
            flash('Email and password are required', 'error')
            return redirect(url_for('subto_login'))
        
        # Authenticate submitter
        submitter = subto_db.authenticate_submitter(email, password)
        
        if not submitter:
            flash('Invalid email or password', 'error')
            return redirect(url_for('subto_login'))
        
        # Set session
        session['subto_submitter_id'] = submitter['id']
        session['subto_submitter_name'] = submitter['name']
        session.permanent = True
        
        flash(f'Welcome back, {submitter["name"]}!', 'success')
        return redirect(url_for('subto_dashboard'))
        
    except Exception as e:
        logging.error(f"Error in submitter login: {e}")
        flash('Login failed. Please try again.', 'error')
        return redirect(url_for('subto_login'))

@app.route('/subto-logout')
def subto_logout():
    """Subject-To submitter logout"""
    session.pop('subto_submitter_id', None)
    session.pop('subto_submitter_name', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('subto_login'))

@app.route('/subto-submit', methods=['GET', 'POST'])
def subto_submit():
    """Subject-To lead submission form"""
    # Check if submitter is logged in
    submitter_id = session.get('subto_submitter_id')
    if not submitter_id:
        flash('Please log in to submit leads', 'error')
        return redirect(url_for('subto_login'))
    
    if request.method == 'GET':
        submitter_name = session.get('subto_submitter_name', 'Submitter')
        return render_template('subto_submit.html', submitter_name=submitter_name)
    
    try:
        # Get form data
        lead_data = {
            'seller_name': request.form.get('seller_name', '').strip(),
            'property_address': request.form.get('property_address', '').strip(),
            'seller_phone': request.form.get('seller_phone', '').strip(),
            'loan_balance': request.form.get('loan_balance', '').strip() or None,
            'interest_rate': request.form.get('interest_rate', '').strip() or None,
            'monthly_payment': request.form.get('monthly_payment', '').strip() or None,
            'arrears': request.form.get('arrears', '').strip() or 0,
            'cash_to_seller': request.form.get('cash_to_seller', '').strip() or 0
        }
        
        # Validate required fields
        if not all([lead_data['seller_name'], lead_data['property_address'], lead_data['seller_phone']]):
            flash('Seller name, property address, and phone number are required', 'error')
            return redirect(url_for('subto_submit'))
        
        # Create lead
        lead_id = subto_db.create_lead(submitter_id, lead_data)
        
        flash('Lead submitted successfully! You can track its status in your dashboard.', 'success')
        return redirect(url_for('subto_dashboard'))
        
    except Exception as e:
        logging.error(f"Error submitting lead: {e}")
        flash('Failed to submit lead. Please try again.', 'error')
        return redirect(url_for('subto_submit'))

@app.route('/subto-dashboard')
def subto_dashboard():
    """Subject-To submitter dashboard - view all their leads"""
    # Check if submitter is logged in
    submitter_id = session.get('subto_submitter_id')
    if not submitter_id:
        flash('Please log in to view your dashboard', 'error')
        return redirect(url_for('subto_login'))
    
    try:
        # Get submitter info
        submitter = subto_db.get_submitter_by_id(submitter_id)
        if not submitter:
            flash('Account not found', 'error')
            return redirect(url_for('subto_login'))
        
        # Get all leads for this submitter
        leads = subto_db.get_leads_by_submitter(submitter_id)
        
        return render_template('subto_dashboard.html', submitter=submitter, leads=leads)
        
    except Exception as e:
        logging.error(f"Error loading dashboard: {e}")
        flash('Failed to load dashboard. Please try again.', 'error')
        return redirect(url_for('subto_login'))

@app.route('/subto-admin')
@require_auth
def subto_admin():
    """Subject-To admin panel - view and manage all leads"""
    try:
        # Get filter from query params
        status_filter = request.args.get('status')
        
        # Get all leads
        leads = subto_db.get_all_leads(status_filter)
        
        return render_template('subto_admin.html', leads=leads, current_filter=status_filter)
        
    except Exception as e:
        logging.error(f"Error loading admin panel: {e}")
        flash('Failed to load admin panel. Please try again.', 'error')
        return redirect(url_for('home'))

@app.route('/api/subto/update-status', methods=['POST'])
@require_auth
@csrf.exempt
def api_subto_update_status():
    """API endpoint to update lead status"""
    try:
        data = request.get_json()
        lead_id = data.get('lead_id')
        status = data.get('status')
        admin_notes = data.get('admin_notes', '')
        
        if not all([lead_id, status]):
            return jsonify({'error': 'Lead ID and status are required'}), 400
        
        # Validate status
        valid_statuses = ['pending', 'reviewing', 'approved', 'declined', 'closed']
        if status not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        # Update status
        success = subto_db.update_lead_status(lead_id, status, admin_notes)
        
        if success:
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        else:
            return jsonify({'error': 'Failed to update status'}), 500
            
    except Exception as e:
        logging.error(f"Error updating lead status: {e}")
        return jsonify({'error': 'Failed to update status'}), 500

@app.route('/subto-quick-submit', methods=['GET', 'POST'])
def subto_quick_submit():
    """Quick Subject-To lead submission with company dropdown"""
    if request.method == 'GET':
        # Get all submitters for dropdown
        submitters = subto_db.get_all_submitters()
        # Add display names with masking
        for submitter in submitters:
            submitter['display_name'] = subto_db.get_display_name(submitter)
        return render_template('subto_quick_submit.html', submitters=submitters)
    
    try:
        # Get submitter ID from dropdown
        submitter_id = request.form.get('submitter_id', '').strip()
        
        if not submitter_id:
            flash('Please select a company', 'error')
            return redirect(url_for('subto_quick_submit'))
        
        # Get form data
        lead_data = {
            'seller_name': request.form.get('seller_name', '').strip(),
            'property_address': request.form.get('property_address', '').strip(),
            'seller_phone': request.form.get('seller_phone', '').strip(),
            'loan_balance': request.form.get('loan_balance', '').strip() or None,
            'interest_rate': request.form.get('interest_rate', '').strip() or None,
            'monthly_payment': request.form.get('monthly_payment', '').strip() or None,
            'arrears': request.form.get('arrears', '').strip() or 0,
            'cash_to_seller': request.form.get('cash_to_seller', '').strip() or 0
        }
        
        # Validate required fields
        if not all([lead_data['seller_name'], lead_data['property_address'], lead_data['seller_phone']]):
            flash('Seller name, property address, and phone number are required', 'error')
            return redirect(url_for('subto_quick_submit'))
        
        # Create lead
        lead_id = subto_db.create_lead(submitter_id, lead_data)
        
        flash('Lead submitted successfully! Thank you for your submission.', 'success')
        return redirect(url_for('subto_quick_submit'))
        
    except Exception as e:
        logging.error(f"Error in quick submit: {e}")
        flash('Failed to submit lead. Please try again.', 'error')
        return redirect(url_for('subto_quick_submit'))

@app.route('/api/subto/generate-script', methods=['POST'])
@csrf.exempt
def api_generate_subto_script():
    """API endpoint to generate custom talking scripts using ChatGPT"""
    try:
        # Check if submitter is logged in
        submitter_id = session.get('subto_submitter_id')
        if not submitter_id:
            return jsonify({'error': 'Please log in to use this feature'}), 401
        
        data = request.get_json()
        situation = data.get('situation', '').strip()
        seller_type = data.get('seller_type', '').strip()
        
        if not situation:
            return jsonify({'error': 'Please describe the situation'}), 400
        
        # Import OpenAI
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Create the prompt for GPT
        prompt = f"""You are a real estate expert helping partners present subject-to deals to sellers. 

Situation: {situation}
Seller Type: {seller_type or 'General'}

Create a professional, empathetic talking script for presenting a subject-to deal. The partner works with People First Property Solutions (Devin). Subject-to means purchasing the property while leaving the existing mortgage in place so the seller can walk away, get some cash, and not worry about the house anymore.

Provide a natural, conversational script (2-3 paragraphs) that:
1. Acknowledges the seller's situation empathetically
2. Introduces the subject-to solution naturally
3. Explains the benefit (walk away, get cash, no more worry)
4. Mentions partnering with Devin from People First Property Solutions
5. Asks if they'd be interested

Keep it concise, warm, and professional. Do not use bullet points or lists - write it as a natural conversation script."""

        # Call GPT-4
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a real estate expert who creates empathetic, professional talking scripts for subject-to deals."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        script = response.choices[0].message.content.strip()
        
        return jsonify({
            'success': True,
            'script': script
        })
        
    except Exception as e:
        logging.error(f"Error generating script: {e}")
        return jsonify({'error': 'Failed to generate script. Please try again.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)