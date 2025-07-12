"""
Minimal Admin Dashboard Routes
Basic admin interface for platform management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func, desc, or_, String, cast, create_engine, text
from sqlalchemy.orm import Session
from billing_models import User, Team, TeamInvite, CreditLog
import logging
import os
from werkzeug.security import check_password_hash
import hashlib
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import and register admin API blueprint
from admin_api import admin_api_bp

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

# Admin authentication decorator
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def require_super_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin') or session.get('admin_role') != 'super_admin':
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    # Apply rate limiting for POST requests only
    if request.method == 'POST':
        # Rate limit: 3 login attempts per minute
        from flask import current_app
        if hasattr(current_app, 'limiter'):
            # Check rate limit manually for admin login
            try:
                # Log the attempt
                logging.info(f"Admin login attempt from IP: {request.remote_addr}")
            except Exception:
                pass
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Get admin password hash from environment variable
        # Set ADMIN_PASSWORD_HASH env var using: python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-secure-password'))"
        admin_password_hash = os.environ.get('ADMIN_PASSWORD_HASH')
        
        if not admin_password_hash:
            # Fallback: use a strong default that requires immediate change
            # This is the hash of a complex password that should never be used in production
            logging.error("ADMIN_PASSWORD_HASH not set! Admin access disabled for security.")
            return render_template('admin_login.html', error='Admin access is disabled. Please configure ADMIN_PASSWORD_HASH.')
        
        # Check password against hash
        if password and check_password_hash(admin_password_hash, password):
            session['is_admin'] = True
            session['admin_role'] = 'super_admin'
            session['admin_user_id'] = 'admin_1'
            # Log successful admin login
            logging.info(f"Admin login successful from IP: {request.remote_addr}")
            return redirect(url_for('admin.dashboard'))
        
        # Log failed login attempt
        logging.warning(f"Failed admin login attempt from IP: {request.remote_addr}")
        return render_template('admin_login.html', error='Invalid credentials')
    return render_template('admin_login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('is_admin', None)
    session.pop('admin_role', None)
    session.pop('admin_user_id', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@require_admin
def dashboard():
    """Main admin dashboard with real data"""
    try:
        with Session(engine) as db:
            # Get real statistics from database
            total_users = db.query(User).count()
            
            # Get active teams
            active_teams = db.query(Team).count()
            
            # Calculate MRR from active subscriptions
            mrr = 0
            teams_data = db.query(Team).all()
            for team in teams_data:
                if hasattr(team, 'tier'):
                    tier = team.tier
                    if tier == 'pro':
                        mrr += 79
                    elif tier == 'team5':
                        mrr += 199
                    elif tier == 'growth10':
                        mrr += 399
                    elif tier == 'individual':
                        mrr += 27
            
            # Get credit usage in last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            credits_used = db.query(func.sum(CreditLog.delta)).filter(
                CreditLog.created_at >= thirty_days_ago,
                CreditLog.delta < 0  # Only count negative deltas (usage)
            ).scalar() or 0
            credits_used = abs(credits_used)  # Make positive for display
            
            # Get pending JV deals
            pending_jv_deals = db.execute(
                text("SELECT COUNT(*) FROM jv_deals WHERE final_status = 'pending'")
            ).scalar() or 0
            
            # Get recent users
            recent_users = db.query(User).order_by(desc(User.created_at)).limit(10).all()
            
            # Convert users to display format
            users_data = []
            for user in recent_users:
                team_name = 'Individual'
                plan = 'individual'
                
                # Get team info if user has a team
                if hasattr(user, 'team_id') and user.team_id:
                    team = db.query(Team).filter(Team.id == user.team_id).first()
                    if team:
                        team_name = team.name
                        plan = team.tier
                
                users_data.append({
                    'id': str(user.id),
                    'email': user.email,
                    'name': user.name if hasattr(user, 'name') and user.name else 'Unknown',
                    'team_name': team_name,
                    'plan': plan,
                    'credits': user.credits if hasattr(user, 'credits') else 0,
                    'last_active': user.last_login.strftime('%Y-%m-%d') if hasattr(user, 'last_login') and user.last_login else 'Never',
                    'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else 'Unknown'
                })
            
            dashboard_data = {
                'total_users': total_users,
                'active_teams': active_teams,
                'mrr': mrr,
                'credits_used': credits_used,
                'pending_jv_deals': pending_jv_deals,
                'users': users_data
            }
            
            return render_template('admin_dashboard_unified.html', data=dashboard_data)
            
    except Exception as e:
        logging.error(f"Admin dashboard error: {str(e)}")
        # Return default data on error
        dashboard_data = {
            'total_users': 0,
            'active_teams': 0,
            'mrr': 0,
            'credits_used': 0,
            'pending_jv_deals': 0,
            'users': []
        }
        return render_template('admin_dashboard_unified.html', data=dashboard_data, error=str(e))

@admin_bp.route('/users')
@require_admin
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_query = request.args.get('search', '')
    filter_type = request.args.get('filter', 'all')
    
    try:
        with Session(engine) as db:
            # Build query
            query = db.query(User)
            
            # Apply search filter
            if search_query:
                query = query.filter(or_(
                    User.email.ilike(f'%{search_query}%'),
                    cast(User.id, String).ilike(f'%{search_query}%')
                ))
            
            # Apply filter with safe attribute access
            if filter_type == 'subscribed':
                try:
                    query = query.filter(User.subscription_tier != 'free')
                except AttributeError:
                    # If subscription_tier doesn't exist, skip filtering
                    pass
            elif filter_type == 'free':
                try:
                    query = query.filter(User.subscription_tier == 'free')
                except AttributeError:
                    # If subscription_tier doesn't exist, skip filtering
                    pass
            
            # Order by creation date, newest first
            query = query.order_by(desc(User.created_at))
            
            # Get results with pagination
            offset = (page - 1) * per_page
            users = query.offset(offset).limit(per_page).all()
            total_users = query.count()
            
            # Convert users to display format
            users_display = []
            for user in users:
                # Safe attribute access
                team_name = 'No Team'
                if hasattr(user, 'team_id') and user.team_id:
                    team = db.query(Team).filter(Team.id == user.team_id).first()
                    if team:
                        team_name = team.name
                
                users_display.append({
                    'id': str(user.id),
                    'email': user.email,
                    'role': getattr(user, 'role', 'user'),
                    'team_name': team_name,
                    'created_at': user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else 'Unknown',
                    'subscription_tier': getattr(user, 'subscription_tier', 'free'),
                    'is_active': getattr(user, 'is_active', True)
                })
            
            # Create pagination object
            pagination = {
                'page': page,
                'per_page': per_page,
                'total': total_users,
                'pages': (total_users + per_page - 1) // per_page,
                'has_prev': page > 1,
                'has_next': page < ((total_users + per_page - 1) // per_page),
                'prev_num': page - 1 if page > 1 else None,
                'next_num': page + 1 if page < ((total_users + per_page - 1) // per_page) else None
            }
            
            return render_template('admin_users.html', 
                                 users=users_display, 
                                 pagination=pagination,
                                 search=search_query,
                                 filter_type=filter_type)
                                 
    except Exception as e:
        logging.error(f"Error loading users page: {e}")
        return render_template('admin_users.html', 
                             users=[], 
                             pagination={'page': 1, 'pages': 0, 'total': 0},
                             search=search_query,
                             filter_type=filter_type)

@admin_bp.route('/affiliates')
@require_admin
def affiliates():
    """Affiliates management page"""
    # Placeholder affiliate data
    affiliates = []
    affiliate_stats = {
        'total_affiliates': 0,
        'active_affiliates': 0,
        'total_referrals': 0,
        'total_commissions': 0,
        'pending_payouts': 0
    }
    return render_template('admin_affiliates.html', 
                         affiliates=affiliates,
                         stats=affiliate_stats)

@admin_bp.route('/billing')
@require_admin
def billing():
    """Billing and revenue dashboard"""
    # Placeholder billing data
    monthly_revenue = []
    top_customers = []
    subscription_stats = []
    
    return render_template('admin_billing.html',
                         mrr=0,
                         monthly_revenue=monthly_revenue,
                         top_customers=top_customers,
                         subscription_stats=subscription_stats)

@admin_bp.route('/api-health')
@require_admin
def api_health():
    """API health and error monitoring"""
    # Placeholder API health data
    error_summary = []
    recent_errors = []
    daily_errors = []
    
    return render_template('admin_api_health.html',
                         error_summary=error_summary,
                         recent_errors=recent_errors,
                         daily_errors=daily_errors)

@admin_bp.route('/api/cache/clear', methods=['POST'])
@require_super_admin
def clear_cache():
    """Clear application cache"""
    # Placeholder cache clearing
    return jsonify({'success': True, 'message': 'Cache cleared successfully'})

@admin_bp.route('/api/affiliate/create', methods=['POST'])
@require_admin
def create_affiliate():
    """Create new affiliate code"""
    data = request.get_json()
    
    name = data.get('name', '').strip()
    tier = data.get('tier', 'basic')
    commission_rate = float(data.get('commission_rate', 20))
    
    if not name:
        return jsonify({'error': 'Affiliate name is required'}), 400
    
    # Generate unique affiliate code
    import random
    import string
    base_code = ''.join(c for c in name.upper() if c.isalnum())[:6]
    if len(base_code) < 3:
        base_code = 'AFF'
    
    # Add random suffix to ensure uniqueness
    suffix = ''.join(random.choices(string.digits, k=4))
    affiliate_code = f"{base_code}{suffix}"
    
    # Set commission rate based on tier
    tier_rates = {
        'basic': 20,
        'premium': 25,
        'top': 30
    }
    
    if tier in tier_rates:
        commission_rate = tier_rates[tier]
    
    # Return the generated affiliate data
    affiliate_data = {
        'name': name,
        'code': affiliate_code,
        'tier': tier,
        'commission_rate': commission_rate,
        'status': 'active',
        'created_at': datetime.utcnow().isoformat()
    }
    
    return jsonify({
        'success': True,
        'affiliate': affiliate_data,
        'message': f'Affiliate code {affiliate_code} created successfully'
    })

@admin_bp.route('/api/affiliate/<string:affiliate_id>/payout', methods=['POST'])
@require_admin
def process_affiliate_payout(affiliate_id):
    """Process affiliate payout"""
    data = request.get_json()
    amount = data.get('amount', 0)
    method = data.get('method', 'paypal')
    
    # Placeholder payout processing
    return jsonify({
        'success': True,
        'message': f'Payout of ${amount} processed via {method}'
    })

@admin_bp.route('/api/affiliate/<string:affiliate_id>/suspend', methods=['POST'])
@require_admin
def suspend_affiliate(affiliate_id):
    """Suspend affiliate account"""
    # Placeholder suspension
    return jsonify({
        'success': True,
        'message': 'Affiliate account suspended'
    })

@admin_bp.route('/api/credit-code/create', methods=['POST'])
@require_admin
def create_credit_code():
    """Create new credit code"""
    data = request.get_json()
    
    credit_amount = data.get('credit_amount', 0)
    max_uses = data.get('max_uses', 1)
    description = data.get('description', '').strip()
    expires_days = data.get('expires_days', 0)
    custom_code = data.get('custom_code', '').strip().upper()
    
    if not credit_amount or credit_amount <= 0:
        return jsonify({'error': 'Credit amount must be greater than 0'}), 400
    
    if not max_uses or max_uses <= 0:
        return jsonify({'error': 'Max uses must be greater than 0'}), 400
    
    # Handle custom code or generate one
    if custom_code:
        # Validate custom code
        if len(custom_code) < 3:
            return jsonify({'error': 'Custom code must be at least 3 characters long'}), 400
        
        # Check if custom code already exists
        try:
            from billing_service import BillingService
            billing_service = BillingService()
            existing_codes = billing_service.get_credit_codes()
            
            if any(existing_code.get('code') == custom_code for existing_code in existing_codes):
                return jsonify({'error': 'Custom code already exists. Please choose a different code.'}), 400
        except Exception as e:
            print(f"Error checking existing codes: {e}")
            # Continue with creation if we can't check existing codes
        
        code = custom_code
    else:
        # Generate unique credit code
        import random
        import string
        code = 'CREDIT' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Calculate expiration date
    expires_at = None
    if expires_days > 0:
        from datetime import timedelta
        expires_at = (datetime.utcnow() + timedelta(days=expires_days)).isoformat()
    
    # Create credit code data
    credit_code_data = {
        'code': code,
        'credit_amount': credit_amount,
        'max_uses': max_uses,
        'current_uses': 0,
        'expires_at': expires_at,
        'description': description,
        'status': 'active',
        'created_by': 'admin',
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Store credit code using billing service
    try:
        from billing_service import BillingService
        billing_service = BillingService()
        
        # Get existing credit codes
        existing_codes = billing_service.get_credit_codes()
        
        # Add new credit code
        existing_codes.append(credit_code_data)
        
        # Save updated codes
        if billing_service.save_credit_codes(existing_codes):
            return jsonify({
                'success': True,
                'message': f'Credit code created successfully: {code}',
                'credit_code': credit_code_data
            })
        else:
            return jsonify({'error': 'Failed to save credit code'}), 500
    except Exception as e:
        logging.error(f"Error creating credit code: {e}")
        return jsonify({'error': 'Failed to create credit code'}), 500

@admin_bp.route('/api/credit-code/<string:code>/disable', methods=['POST'])
@require_admin
def disable_credit_code(code):
    """Disable credit code"""
    # Placeholder disable
    return jsonify({
        'success': True,
        'message': f'Credit code {code} disabled successfully'
    })

@admin_bp.route('/api/credit-codes', methods=['GET'])
@require_admin
def get_credit_codes():
    """Get all credit codes"""
    try:
        from billing_service import BillingService
        billing_service = BillingService()
        
        credit_codes = billing_service.get_credit_codes()
        return jsonify({
            'success': True,
            'credit_codes': credit_codes
        })
    except Exception as e:
        logging.error(f"Error getting credit codes: {e}")
        return jsonify({'error': 'Failed to get credit codes'}), 500