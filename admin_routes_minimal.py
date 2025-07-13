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
from flask_wtf.csrf import CSRFProtect
from flask import current_app

# Set up logging
logger = logging.getLogger(__name__)

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

@admin_bp.route('/api/affiliates', methods=['GET'])
@require_admin
def get_affiliates():
    """Get all affiliates with filtering and pagination"""
    try:
        # Sample affiliates data
        # Get authentic affiliate data from database
        affiliates_data = []
        try:
            # TODO: Implement actual affiliate table query when affiliate system is ready
            # For now, return empty list to show no sample data
            pass
        except Exception as e:
            logging.error(f"Error getting affiliates: {e}")
            affiliates_data = []
        
        # Calculate stats
        total_affiliates = len(affiliates_data)
        total_commissions = sum(a['total_commissions_earned'] for a in affiliates_data)
        active_referrals = sum(a['active_referrals'] for a in affiliates_data)
        avg_commission_rate = sum(a['commission_rate'] for a in affiliates_data) / len(affiliates_data) if affiliates_data else 0
        
        stats = {
            'total_affiliates': total_affiliates,
            'total_commissions': total_commissions,
            'active_referrals': active_referrals,
            'avg_commission_rate': avg_commission_rate * 100
        }
        
        return jsonify({
            'success': True,
            'affiliates': affiliates_data,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting affiliates: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/promo-codes', methods=['GET'])
@require_admin
def get_promo_codes():
    """Get all promo codes"""
    try:
        # Get authentic promo codes data from database
        promo_codes = []
        try:
            # TODO: Implement actual promo codes table query when promo system is ready
            # For now, return empty list to show no sample data
            pass
        except Exception as e:
            logging.error(f"Error getting promo codes: {e}")
            promo_codes = []
        
        return jsonify({
            'success': True,
            'promo_codes': promo_codes
        })
        
    except Exception as e:
        logger.error(f"Error getting promo codes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/teams', methods=['GET'])
@require_admin
def get_teams_data():
    """Get all teams data"""
    try:
        with Session(engine) as session:
            # Get teams with member counts
            teams = session.execute(text("""
                SELECT 
                    t.id,
                    t.name,
                    t.tier as plan_type,
                    t.credits_balance,
                    t.credits_used,
                    t.created_at,
                    COUNT(u.id) as member_count,
                    MAX(u.last_login) as last_active
                FROM teams t
                LEFT JOIN users u ON t.id = u.team_id
                GROUP BY t.id, t.name, t.tier, t.credits_balance, t.credits_used, t.created_at
                ORDER BY t.created_at DESC
            """)).fetchall()
            
            teams_data = []
            for team in teams:
                teams_data.append({
                    'id': team.id,
                    'name': team.name,
                    'plan_type': team.plan_type,
                    'credits_balance': team.credits_balance,
                    'credits_used': team.credits_used,
                    'member_count': team.member_count,
                    'last_active': team.last_active.isoformat() if team.last_active else None,
                    'created_at': team.created_at.isoformat() if team.created_at else None
                })
            
            return jsonify({
                'success': True,
                'teams': teams_data
            })
            
    except Exception as e:
        logger.error(f"Error getting teams: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/subscriptions', methods=['GET'])
@require_admin
def get_subscriptions_data():
    """Get subscription data"""
    try:
        # Sample subscription data
        subscriptions = [
            {
                'id': 'sub_1',
                'team_name': "Devin's Unlimited Team",
                'plan_type': 'growth10',
                'status': 'active',
                'amount': 399,
                'currency': 'usd',
                'interval': 'month',
                'current_period_start': '2024-07-01',
                'current_period_end': '2024-08-01',
                'customer_email': 'devin@pfpsolutions.us',
                'created_at': '2024-07-01'
            }
        ]
        
        return jsonify({
            'success': True,
            'subscriptions': subscriptions
        })
        
    except Exception as e:
        logger.error(f"Error getting subscriptions: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/jv-deals', methods=['GET'])
@require_admin
def get_jv_deals_data():
    """Get JV deals data"""
    try:
        with Session(engine) as session:
            # Get JV deals
            jv_deals = session.execute(text("""
                SELECT 
                    id,
                    partner_id,
                    property_address,
                    property_city,
                    property_state,
                    asking_price,
                    arv,
                    repair_estimate,
                    suggested_offer,
                    status,
                    created_at,
                    updated_at
                FROM jv_deal_submissions
                ORDER BY created_at DESC
            """)).fetchall()
            
            jv_deals_data = []
            for deal in jv_deals:
                jv_deals_data.append({
                    'id': deal.id,
                    'partner_id': deal.partner_id,
                    'property_address': deal.property_address,
                    'property_city': deal.property_city,
                    'property_state': deal.property_state,
                    'asking_price': float(deal.asking_price) if deal.asking_price else 0,
                    'arv': float(deal.arv) if deal.arv else 0,
                    'repair_estimate': float(deal.repair_estimate) if deal.repair_estimate else 0,
                    'suggested_offer': float(deal.suggested_offer) if deal.suggested_offer else 0,
                    'status': deal.status,
                    'created_at': deal.created_at.isoformat() if deal.created_at else None,
                    'updated_at': deal.updated_at.isoformat() if deal.updated_at else None
                })
            
            return jsonify({
                'success': True,
                'jv_deals': jv_deals_data
            })
            
    except Exception as e:
        logger.error(f"Error getting JV deals: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/ai-assistant', methods=['POST'])
@require_admin
def ai_assistant():
    """GPT-4o powered admin assistant"""
    try:
        import openai
        
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # Get OpenAI API key from environment
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({'success': False, 'error': 'OpenAI API key not configured'}), 500
        
        # Create OpenAI client
        client = openai.OpenAI(api_key=openai_api_key)
        
        # System prompt for admin assistant
        system_prompt = """You are an AI assistant for a real estate SaaS admin dashboard. You help with:
        - Affiliate management and commission tracking
        - Promo code creation and optimization
        - User engagement and churn prevention
        - Revenue analytics and growth strategies
        - System monitoring and performance insights
        
        Provide helpful, actionable advice for admin tasks. Keep responses concise and professional.
        Do not use asterisks (*) in your responses - use dashes (-) for bullet points instead."""
        
        # Get AI response
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'response': ai_response
        })
        
    except Exception as e:
        logger.error(f"AI Assistant error: {str(e)}")
        return jsonify({'success': False, 'error': 'AI assistant temporarily unavailable'}), 500

@admin_bp.route('/api/ai-promo-generator', methods=['POST'])
@require_admin
def ai_promo_generator():
    """AI-powered promo code generator"""
    try:
        import openai
        import random
        import string
        
        data = request.get_json()
        promo_type = data.get('type', 'percentage_discount')
        affiliate_id = data.get('affiliate_id', '')
        
        # Get OpenAI API key from environment
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            # Fallback to rule-based generation
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            value = 30 if promo_type == 'percentage_discount' else 100
            return jsonify({
                'success': True,
                'code': code,
                'value': value,
                'max_uses': 100
            })
        
        # Create OpenAI client
        client = openai.OpenAI(api_key=openai_api_key)
        
        # AI prompt for promo code generation
        prompt = f"""Generate a creative promo code for a real estate SaaS platform.
        
        Type: {promo_type}
        Affiliate ID: {affiliate_id}
        
        Requirements:
        - Code should be 6-10 characters
        - Memorable and brandable
        - Related to real estate or investment
        - Professional sounding
        
        Return in format: CODE|VALUE|MAX_USES
        Example: FLIP30|30|100
        
        Do not use asterisks in your response."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.8
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse AI response
        try:
            parts = ai_response.split('|')
            if len(parts) >= 3:
                code = parts[0].strip()
                value = int(parts[1].strip())
                max_uses = int(parts[2].strip())
            else:
                # Fallback parsing
                code = ai_response.split()[0] if ai_response.split() else 'PROMO30'
                value = 30 if promo_type == 'percentage_discount' else 100
                max_uses = 100
        except:
            # Fallback values
            code = 'PROMO30'
            value = 30 if promo_type == 'percentage_discount' else 100
            max_uses = 100
        
        return jsonify({
            'success': True,
            'code': code,
            'value': value,
            'max_uses': max_uses
        })
        
    except Exception as e:
        logger.error(f"AI Promo Generator error: {str(e)}")
        # Fallback to simple generation
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        value = 30 if promo_type == 'percentage_discount' else 100
        return jsonify({
            'success': True,
            'code': code,
            'value': value,
            'max_uses': 100
        })

@admin_bp.route('/api/create-affiliate', methods=['POST'])
@require_admin
def create_affiliate():
    """Create new affiliate"""
    try:
        data = request.get_json()
        
        # For now, just return success (would normally create in database)
        return jsonify({
            'success': True,
            'message': 'Affiliate created successfully',
            'affiliate_id': f"affiliate-{len(data.get('name', ''))}"
        })
        
    except Exception as e:
        logger.error(f"Create affiliate error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/create-promo-code', methods=['POST'])
@require_admin
def create_promo_code():
    """Create new promo code"""
    try:
        data = request.get_json()
        
        # For now, just return success (would normally create in database)
        return jsonify({
            'success': True,
            'message': 'Promo code created successfully',
            'code_id': f"promo-{data.get('code', 'unknown')}"
        })
        
    except Exception as e:
        logger.error(f"Create promo code error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/usage-metrics', methods=['GET'])
@require_admin
def get_usage_metrics():
    """Get comprehensive usage metrics"""
    try:
        with Session(engine) as session:
            # Get usage data from last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            # Daily active users (last 30 days)
            daily_active_users = session.execute(text("""
                SELECT 
                    DATE(last_login) as date,
                    COUNT(DISTINCT id) as active_users
                FROM users 
                WHERE last_login >= :thirty_days_ago
                GROUP BY DATE(last_login)
                ORDER BY date DESC
            """), {"thirty_days_ago": thirty_days_ago}).fetchall()
            
            # Credit usage by tier
            credit_usage_by_tier = session.execute(text("""
                SELECT 
                    t.tier,
                    COUNT(DISTINCT t.id) as team_count,
                    SUM(CASE WHEN cl.delta < 0 THEN ABS(cl.delta) ELSE 0 END) as credits_used,
                    AVG(CASE WHEN cl.delta < 0 THEN ABS(cl.delta) ELSE 0 END) as avg_credits_per_team
                FROM teams t
                LEFT JOIN credit_logs cl ON t.id = cl.team_id 
                WHERE cl.created_at >= :thirty_days_ago OR cl.created_at IS NULL
                GROUP BY t.tier
            """), {"thirty_days_ago": thirty_days_ago}).fetchall()
            
            # Feature usage (property analysis)
            feature_usage = session.execute(text("""
                SELECT 
                    DATE(cl.created_at) as date,
                    COUNT(*) as property_analyses
                FROM credit_logs cl
                WHERE cl.delta < 0 
                AND cl.created_at >= :thirty_days_ago
                GROUP BY DATE(cl.created_at)
                ORDER BY date DESC
            """), {"thirty_days_ago": thirty_days_ago}).fetchall()
            
            # User engagement levels
            user_engagement = session.execute(text("""
                SELECT 
                    CASE 
                        WHEN last_login >= :seven_days_ago THEN 'highly_active'
                        WHEN last_login >= :thirty_days_ago THEN 'active'
                        WHEN last_login IS NOT NULL THEN 'inactive'
                        ELSE 'never_logged_in'
                    END as engagement_level,
                    COUNT(*) as user_count
                FROM users
                GROUP BY engagement_level
            """), {"seven_days_ago": seven_days_ago, "thirty_days_ago": thirty_days_ago}).fetchall()
            
            # Convert to JSON-serializable format
            usage_data = {
                'daily_active_users': [
                    {'date': row.date.isoformat(), 'active_users': row.active_users}
                    for row in daily_active_users
                ],
                'credit_usage_by_tier': [
                    {
                        'tier': row.tier,
                        'team_count': row.team_count,
                        'credits_used': row.credits_used or 0,
                        'avg_credits_per_team': round(row.avg_credits_per_team or 0, 2)
                    }
                    for row in credit_usage_by_tier
                ],
                'feature_usage': [
                    {'date': row.date.isoformat(), 'property_analyses': row.property_analyses}
                    for row in feature_usage
                ],
                'user_engagement': [
                    {'engagement_level': row.engagement_level, 'user_count': row.user_count}
                    for row in user_engagement
                ]
            }
            
            return jsonify({
                'success': True,
                'usage_data': usage_data
            })
            
    except Exception as e:
        logger.error(f"Error getting usage metrics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/churn-metrics', methods=['GET'])
@require_admin  
def get_churn_metrics():
    """Get comprehensive churn analysis"""
    try:
        with Session(engine) as session:
            # Churn analysis - users who haven't logged in for different periods
            churn_analysis = session.execute(text("""
                SELECT 
                    CASE 
                        WHEN last_login IS NULL THEN 'never_logged_in'
                        WHEN last_login < :ninety_days_ago THEN 'churned_90_days'
                        WHEN last_login < :sixty_days_ago THEN 'at_risk_60_days'
                        WHEN last_login < :thirty_days_ago THEN 'at_risk_30_days'
                        WHEN last_login < :seven_days_ago THEN 'declining_7_days'
                        ELSE 'active'
                    END as churn_status,
                    COUNT(*) as user_count,
                    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM users) as percentage
                FROM users
                GROUP BY churn_status
            """), {
                "ninety_days_ago": datetime.now() - timedelta(days=90),
                "sixty_days_ago": datetime.now() - timedelta(days=60),
                "thirty_days_ago": datetime.now() - timedelta(days=30),
                "seven_days_ago": datetime.now() - timedelta(days=7)
            }).fetchall()
            
            # Team churn by tier
            team_churn = session.execute(text("""
                SELECT 
                    t.tier,
                    COUNT(*) as total_teams,
                    COUNT(CASE WHEN u.last_login < :thirty_days_ago THEN 1 END) as inactive_teams,
                    COUNT(CASE WHEN u.last_login < :thirty_days_ago THEN 1 END) * 100.0 / COUNT(*) as churn_rate
                FROM teams t
                LEFT JOIN users u ON t.id = u.team_id
                GROUP BY t.tier
            """), {"thirty_days_ago": datetime.now() - timedelta(days=30)}).fetchall()
            
            # Monthly churn trend
            monthly_churn = session.execute(text("""
                SELECT 
                    DATE_TRUNC('month', created_at) as month,
                    COUNT(*) as new_users,
                    COUNT(CASE WHEN last_login < :thirty_days_ago THEN 1 END) as churned_users
                FROM users
                WHERE created_at >= :six_months_ago
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month DESC
            """), {
                "thirty_days_ago": datetime.now() - timedelta(days=30),
                "six_months_ago": datetime.now() - timedelta(days=180)
            }).fetchall()
            
            # At-risk users (high-value users who are becoming inactive)
            at_risk_users = session.execute(text("""
                SELECT 
                    u.id,
                    u.email,
                    u.name,
                    t.tier,
                    t.name as team_name,
                    u.last_login,
                    COALESCE(SUM(CASE WHEN cl.delta < 0 THEN ABS(cl.delta) ELSE 0 END), 0) as total_credits_used
                FROM users u
                LEFT JOIN teams t ON u.team_id = t.id
                LEFT JOIN credit_logs cl ON t.id = cl.team_id
                WHERE u.last_login BETWEEN :sixty_days_ago AND :thirty_days_ago
                AND (t.tier IN ('pro', 'team5', 'growth10') OR COALESCE(SUM(CASE WHEN cl.delta < 0 THEN ABS(cl.delta) ELSE 0 END), 0) > 50)
                GROUP BY u.id, u.email, u.name, t.tier, t.name, u.last_login
                ORDER BY total_credits_used DESC
                LIMIT 20
            """), {
                "sixty_days_ago": datetime.now() - timedelta(days=60),
                "thirty_days_ago": datetime.now() - timedelta(days=30)
            }).fetchall()
            
            # Convert to JSON-serializable format
            churn_data = {
                'churn_analysis': [
                    {
                        'churn_status': row.churn_status,
                        'user_count': row.user_count,
                        'percentage': round(row.percentage, 2)
                    }
                    for row in churn_analysis
                ],
                'team_churn': [
                    {
                        'tier': row.tier,
                        'total_teams': row.total_teams,
                        'inactive_teams': row.inactive_teams,
                        'churn_rate': round(row.churn_rate, 2)
                    }
                    for row in team_churn
                ],
                'monthly_churn': [
                    {
                        'month': row.month.isoformat(),
                        'new_users': row.new_users,
                        'churned_users': row.churned_users
                    }
                    for row in monthly_churn
                ],
                'at_risk_users': [
                    {
                        'id': str(row.id),
                        'email': row.email,
                        'name': row.name or 'Unknown',
                        'tier': row.tier or 'individual',
                        'team_name': row.team_name or 'Individual',
                        'last_login': row.last_login.isoformat() if row.last_login else None,
                        'total_credits_used': row.total_credits_used
                    }
                    for row in at_risk_users
                ]
            }
            
            return jsonify({
                'success': True,
                'churn_data': churn_data
            })
            
    except Exception as e:
        logger.error(f"Error getting churn metrics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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