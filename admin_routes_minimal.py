"""
Minimal Admin Dashboard Routes
Basic admin interface for platform management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func, desc, or_, String, cast
from models import User, CreditPurchase, CompingCredit, GuestUsage
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

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
    if request.method == 'POST':
        password = request.form.get('password')
        # Simple admin authentication - in production, use proper admin user management
        if password == 'admin123':  # Replace with secure authentication
            session['is_admin'] = True
            session['admin_role'] = 'super_admin'
            session['admin_user_id'] = 'admin_1'
            return redirect(url_for('admin.dashboard'))
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
    """Main admin dashboard"""
    # Basic statistics - will be enhanced once proper models are implemented
    stats = {
        'total_users': 0,
        'active_subscriptions': 0,
        'total_teams': 0,
        'pending_jv_deals': 0,
        'total_revenue': 0,
        'properties_analyzed_today': 0,
        'api_errors_today': 0,
        'open_tickets': 0
    }
    
    # Recent activity placeholders
    recent_users = []
    recent_deals = []
    recent_errors = []
    
    return render_template('admin_dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_deals=recent_deals,
                         recent_errors=recent_errors)

@admin_bp.route('/users')
@require_admin
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_query = request.args.get('search', '')
    filter_type = request.args.get('filter', 'all')
    
    # Build query
    query = User.query
    
    # Apply search filter
    if search_query:
        query = query.filter(or_(
            User.email.ilike(f'%{search_query}%'),
            cast(User.id, String).ilike(f'%{search_query}%')
        ))
    
    # Apply filter
    if filter_type == 'subscribed':
        query = query.filter(User.subscription_tier != 'free')
    elif filter_type == 'free':
        query = query.filter(User.subscription_tier == 'free')
    
    # Order by creation date, newest first
    query = query.order_by(desc(User.created_at))
    
    # Paginate results
    users = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin_users.html', 
                         users=users, 
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
    
    return jsonify({
        'success': True,
        'credit_code': credit_code_data,
        'message': f'Credit code {code} created successfully'
    })

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
    # Placeholder data - in real implementation, this would query the database
    credit_codes = []
    return jsonify({
        'success': True,
        'credit_codes': credit_codes
    })