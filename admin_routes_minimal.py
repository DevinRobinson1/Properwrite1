"""
Minimal Admin Dashboard Routes
Basic admin interface for platform management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from functools import wraps

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
    # Placeholder for user management
    users = []
    return render_template('admin_users.html', users=users)

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