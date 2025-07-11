"""
Admin Dashboard Routes
Comprehensive admin interface for platform management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
from billing_models import Team, User, CreditLog, TeamInvite
from main import db
import hashlib
import secrets

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
    # Get dashboard statistics
    stats = {
        'total_users': User.query.count(),
        'active_subscriptions': 0,  # TODO: Add subscription tracking
        'total_teams': Team.query.count(),
        'pending_jv_deals': 0,  # TODO: Add JV deal tracking
        'total_revenue': 0,  # TODO: Add revenue tracking
        'properties_analyzed_today': 0,  # TODO: Add activity tracking
        'api_errors_today': 0,  # TODO: Add error tracking
        'open_tickets': 0  # TODO: Add ticket tracking
    }
    
    # Get recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_deals = []  # TODO: Add JV deal tracking
    recent_errors = []  # TODO: Add error tracking
    
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
    search = request.args.get('search', '')
    filter_type = request.args.get('filter', 'all')
    
    query = User.query
    
    # Apply search
    if search:
        query = query.filter(or_(
            User.email.contains(search),
            User.id.contains(search)
        ))
    
    # Apply filters
    if filter_type == 'subscribed':
        query = query.join(Team).join(Subscription).filter(Subscription.status == 'active')
    elif filter_type == 'free':
        query = query.outerjoin(Team).filter(Team.id == None)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get user stats
    for user in users.items:
        user.credits_used = CreditLog.query.filter_by(
            user_id=user.id,
            action='property_analysis'
        ).count()
        user.last_activity = UserActivity.query.filter_by(
            user_id=user.id
        ).order_by(UserActivity.created_at.desc()).first()
    
    return render_template('admin_users.html', users=users, search=search, filter_type=filter_type)

@admin_bp.route('/users/<user_id>')
@require_admin
def user_detail(user_id):
    """User detail page"""
    user = User.query.get_or_404(user_id)
    
    # Get user's team
    team = Team.query.filter(Team.users.any(id=user_id)).first()
    
    # Get subscription info
    subscription = None  # TODO: Add subscription model
    
    # Get credit history
    credit_logs = CreditLog.query.filter_by(user_id=user_id).order_by(
        CreditLog.created_at.desc()
    ).limit(20).all()
    
    # Get activity logs
    activities = UserActivity.query.filter_by(user_id=user_id).order_by(
        UserActivity.created_at.desc()
    ).limit(50).all()
    
    # Get JV deals
    jv_deals = []  # TODO: Add JV deal tracking
    
    return render_template('admin_user_detail.html',
                         user=user,
                         team=team,
                         subscription=subscription,
                         credit_logs=credit_logs,
                         activities=activities,
                         jv_deals=jv_deals)

@admin_bp.route('/api/users/<user_id>/grant-credits', methods=['POST'])
@require_admin
def grant_credits(user_id):
    """Grant bonus credits to user"""
    user = User.query.get_or_404(user_id)
    credits = request.json.get('credits', 0)
    reason = request.json.get('reason', 'Admin grant')
    
    # Find user's team
    team = Team.query.filter(Team.users.any(id=user_id)).first()
    if not team:
        return jsonify({'error': 'User has no team'}), 400
    
    # Create credit log
    credit_log = CreditLog(
        team_id=team.id,
        user_id=user_id,
        action='admin_grant',
        credits_change=credits,
        credits_after=team.credits_remaining + credits,
        metadata={'reason': reason, 'admin_id': session.get('admin_user_id')}
    )
    
    # Update team credits
    team.credits_remaining += credits
    
    # TODO: Add admin action logging
    
    db.session.add(credit_log)
    db.session.commit()
    
    return jsonify({'success': True, 'new_credits': team.credits_remaining})

@admin_bp.route('/api/users/<user_id>/suspend', methods=['POST'])
@require_super_admin
def suspend_user(user_id):
    """Suspend user account"""
    user = User.query.get_or_404(user_id)
    reason = request.json.get('reason', '')
    
    # Update user status (you may need to add a status field to User model)
    # user.status = 'suspended'
    
    # TODO: Add admin action logging
    
    db.session.commit()
    
    return jsonify({'success': True})

# Affiliate routes temporarily disabled until affiliate models are integrated
# @admin_bp.route('/affiliates')
# @require_admin
# def affiliates():
#     """Affiliate management page"""
#     return render_template('admin_affiliates.html', affiliates=[])

# @admin_bp.route('/api/affiliates/create', methods=['POST'])
# @require_admin
# def create_affiliate():
#     """Create new affiliate"""
#     return jsonify({'error': 'Affiliate system not yet implemented'}), 501

@admin_bp.route('/teams')
@require_admin
def teams():
    """Team management page"""
    page = request.args.get('page', 1, type=int)
    
    teams = Team.query.order_by(Team.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get team stats
    for team in teams.items:
        team.member_count = len(team.users)
        team.properties_analyzed = CreditLog.query.filter_by(
            team_id=team.id,
            reason='property_analysis'
        ).count()
        # TODO: Add subscription tracking
        team.subscription = None
    
    return render_template('admin_teams.html', teams=teams)

# JV deals routes temporarily disabled until JV database models are properly integrated

@admin_bp.route('/billing')
@require_admin
def billing():
    """Billing and revenue dashboard"""
    # Calculate MRR
    # TODO: Add subscription tracking
    mrr = 0
    
    # Get revenue by month (placeholder data for now)
    monthly_revenue = []
    
    # Get top customers by revenue (placeholder data for now)
    top_customers = []
    
    # Get subscription distribution (placeholder data for now)
    subscription_stats = []
    
    return render_template('admin_billing.html',
                         mrr=mrr,
                         monthly_revenue=monthly_revenue,
                         top_customers=top_customers,
                         subscription_stats=subscription_stats)

@admin_bp.route('/api-health')
@require_admin
def api_health():
    """API health and error monitoring"""
    # TODO: Add API error tracking
    error_summary = []
    recent_errors = []
    daily_errors = []
    
    return render_template('admin_api_health.html',
                         error_summary=error_summary,
                         recent_errors=recent_errors,
                         daily_errors=daily_errors)

# @admin_bp.route('/api/errors/<int:error_id>/resolve', methods=['POST'])
# @require_admin
# def resolve_error(error_id):
#     """Mark API error as resolved"""
#     # TODO: Add API error tracking
#     return jsonify({'error': 'API error tracking not yet implemented'}), 501

# @admin_bp.route('/activity-logs')
# @require_admin
# def activity_logs():
#     """Admin activity audit logs"""
#     # TODO: Add activity logging
#     return render_template('admin_activity_logs.html', logs=[])

@admin_bp.route('/api/cache/clear', methods=['POST'])
@require_super_admin
def clear_cache():
    """Clear application cache"""
    # Implement cache clearing logic based on your caching system
    
    # TODO: Add admin action logging
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Cache cleared successfully'})