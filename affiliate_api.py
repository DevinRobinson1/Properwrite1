"""
Affiliate Management API Endpoints
Handles affiliate, promo code, and commission operations
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import logging
from billing_service import BillingService
from affiliate_service import AffiliateService
from affiliate_models import AffiliateStatus, PromoCodeType
import openai
import os
import functools

logger = logging.getLogger(__name__)

affiliate_api = Blueprint('affiliate_api', __name__)

# Import CSRF for exemption
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()

def get_db_session():
    """Get database session from billing service"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os
    
    DATABASE_URL = os.environ.get("DATABASE_URL")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    )
    Session = sessionmaker(bind=engine)
    return Session()

def require_admin(f):
    """Admin authentication decorator - uses same auth as main admin API"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated as admin
        admin_token = request.headers.get('X-Admin-Token')
        if admin_token == 'admin123':  # Keep for backward compatibility
            return f(*args, **kwargs)
        
        # Try session-based authentication (matches admin_routes_minimal.py)
        from flask import session
        if not session.get('is_admin'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# Affiliate Management Endpoints
@affiliate_api.route('/api/admin/affiliates', methods=['GET'])
@csrf.exempt
@require_admin
def get_affiliates():
    """Get all affiliates with filtering and pagination"""
    db = get_db_session()
    try:
        service = AffiliateService(db)
        
        # Get query parameters
        status = request.args.get('status')
        tier = request.args.get('tier')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        from affiliate_models import Affiliate
        query = db.query(Affiliate)
        
        if status:
            query = query.filter_by(status=AffiliateStatus(status))
        if tier:
            query = query.filter_by(tier=tier)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        affiliates = query.offset((page - 1) * per_page).limit(per_page).all()
        
        results = []
        for affiliate in affiliates:
            # Simplified metrics for now - just basic fields
            results.append({
                'id': str(affiliate.id),
                'name': affiliate.name,
                'email': affiliate.email,
                'company': affiliate.company,
                'status': affiliate.status.value,
                'tier': affiliate.tier,
                'commission_rate': affiliate.commission_rate,
                'created_at': affiliate.created_at.isoformat() if affiliate.created_at else None,
                'metrics': {
                    'referrals': {
                        'total': affiliate.total_referrals or 0,
                        'active': affiliate.active_referrals or 0,
                        'total_revenue': affiliate.total_revenue_generated or 0.0
                    }
                }
            })
        
        return jsonify({
            'affiliates': results,
            'total': total,
            'page': page,
            'per_page': per_page
        })
        
    finally:
        db.close()

@affiliate_api.route('/api/admin/affiliates', methods=['POST'])
@require_admin
def create_affiliate():
    """Create a new affiliate"""
    db = get_db_session()
    try:
        service = AffiliateService(db)
        data = request.json
        
        affiliate = service.create_affiliate(data)
        
        return jsonify({
            'id': str(affiliate.id),
            'name': affiliate.name,
            'email': affiliate.email,
            'status': affiliate.status.value
        })
        
    finally:
        db.close()

@affiliate_api.route('/api/admin/affiliates/<affiliate_id>/approve', methods=['POST'])
@require_admin
def approve_affiliate(affiliate_id):
    """Approve a pending affiliate"""
    db = get_db_session()
    try:
        service = AffiliateService(db)
        
        # Get admin user ID from session
        from flask import session
        admin_id = session.get('admin_user_id', 'admin_user_id')
        
        affiliate = service.approve_affiliate(affiliate_id, admin_id)
        
        return jsonify({
            'id': str(affiliate.id),
            'status': affiliate.status.value,
            'approved_at': affiliate.approved_at.isoformat()
        })
        
    finally:
        db.close()

@affiliate_api.route('/api/admin/affiliates/<affiliate_id>/metrics', methods=['GET'])
@require_admin
def get_affiliate_metrics(affiliate_id):
    """Get detailed metrics for an affiliate"""
    db = get_db_session()
    try:
        service = AffiliateService(db)
        metrics = service.get_affiliate_metrics(affiliate_id)
        
        return jsonify(metrics)
        
    finally:
        db.close()

# Promo Code Management Endpoints
@affiliate_api.route('/api/admin/promo-codes', methods=['GET'])
@csrf.exempt
@require_admin
def get_promo_codes():
    """Get all promo codes with filtering"""
    db = get_db_session()
    try:
        from affiliate_models import PromoCode
        
        # Get query parameters
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        affiliate_id = request.args.get('affiliate_id')
        code_type = request.args.get('type')
        
        query = db.query(PromoCode)
        
        if active_only:
            query = query.filter_by(is_active=True)
        if affiliate_id:
            query = query.filter_by(affiliate_id=affiliate_id)
        if code_type:
            query = query.filter_by(type=PromoCodeType(code_type))
        
        promo_codes = query.order_by(PromoCode.created_at.desc()).all()
        
        results = []
        for code in promo_codes:
            results.append({
                'id': str(code.id),
                'code': code.code,
                'type': code.type.value,
                'affiliate_id': str(code.affiliate_id) if code.affiliate_id else None,
                'discount_percentage': code.discount_percentage,
                'credit_amount': code.credit_amount,
                'bonus_seats': code.bonus_seats,
                'uses_count': code.uses_count,
                'max_uses': code.max_uses,
                'valid_until': code.valid_until.isoformat() if code.valid_until else None,
                'is_active': code.is_active,
                'total_revenue': code.total_revenue,
                'conversion_rate': code.conversion_rate
            })
        
        return jsonify({'promo_codes': results})
        
    finally:
        db.close()

@affiliate_api.route('/api/admin/promo-codes', methods=['POST'])
@csrf.exempt
@require_admin
def create_promo_code():
    """Create a new promo code"""
    db = get_db_session()
    try:
        service = AffiliateService(db)
        data = request.json
        
        # Get admin user ID from session
        from flask import session
        data['created_by'] = session.get('admin_user_id', 'admin_user_id')
        
        promo_code = service.create_promo_code(data)
        
        return jsonify({
            'id': str(promo_code.id),
            'code': promo_code.code,
            'type': promo_code.type.value,
            'created': True
        })
        
    finally:
        db.close()

@affiliate_api.route('/api/admin/promo-codes/<code_id>', methods=['PUT'])
@csrf.exempt
@require_admin
def update_promo_code(code_id):
    """Update an existing promo code"""
    db = get_db_session()
    try:
        from affiliate_models import PromoCode, PromoCodeType
        
        promo_code = db.query(PromoCode).filter_by(id=code_id).first()
        if not promo_code:
            return jsonify({'error': 'Promo code not found'}), 404
        
        data = request.json
        
        # Update fields if provided
        if 'code' in data:
            promo_code.code = data['code']
        if 'type' in data:
            promo_code.type = PromoCodeType(data['type'])
        if 'discount_percentage' in data:
            promo_code.discount_percentage = data['discount_percentage']
        if 'credit_amount' in data:
            promo_code.credit_amount = data['credit_amount']
        if 'bonus_seats' in data:
            promo_code.bonus_seats = data['bonus_seats']
        if 'max_uses' in data:
            promo_code.max_uses = data['max_uses']
        if 'valid_until' in data:
            from datetime import datetime
            promo_code.valid_until = datetime.fromisoformat(data['valid_until']) if data['valid_until'] else None
        if 'is_active' in data:
            promo_code.is_active = data['is_active']
        if 'first_month_only' in data:
            promo_code.first_month_only = data['first_month_only']
        if 'description' in data:
            promo_code.description = data['description']
        
        db.commit()
        
        return jsonify({
            'id': str(promo_code.id),
            'code': promo_code.code,
            'type': promo_code.type.value,
            'discount_percentage': promo_code.discount_percentage,
            'credit_amount': promo_code.credit_amount,
            'bonus_seats': promo_code.bonus_seats,
            'max_uses': promo_code.max_uses,
            'valid_until': promo_code.valid_until.isoformat() if promo_code.valid_until else None,
            'is_active': promo_code.is_active,
            'first_month_only': promo_code.first_month_only,
            'description': promo_code.description,
            'updated': True
        })
        
    finally:
        db.close()

@affiliate_api.route('/api/admin/promo-codes/<code_id>/deactivate', methods=['POST'])
@csrf.exempt
@require_admin
def deactivate_promo_code(code_id):
    """Deactivate a promo code"""
    db = get_db_session()
    try:
        from affiliate_models import PromoCode
        
        promo_code = db.query(PromoCode).filter_by(id=code_id).first()
        if not promo_code:
            return jsonify({'error': 'Promo code not found'}), 404
        
        promo_code.is_active = False
        db.commit()
        
        return jsonify({'deactivated': True})
        
    finally:
        db.close()

# Payout Management Endpoints
@affiliate_api.route('/api/admin/payouts/pending', methods=['GET'])
@csrf.exempt
@require_admin
def get_pending_payouts():
    """Get affiliates with pending payouts"""
    db = get_db_session()
    try:
        service = AffiliateService(db)
        from affiliate_models import Affiliate, AffiliateStatus
        
        affiliates = db.query(Affiliate).filter_by(
            status=AffiliateStatus.ACTIVE
        ).all()
        
        pending_payouts = []
        for affiliate in affiliates:
            pending_amount = service.calculate_pending_commissions(str(affiliate.id))
            if pending_amount >= affiliate.minimum_payout:
                pending_payouts.append({
                    'affiliate_id': str(affiliate.id),
                    'affiliate_name': affiliate.name,
                    'affiliate_email': affiliate.email,
                    'pending_amount': pending_amount,
                    'minimum_payout': affiliate.minimum_payout,
                    'payout_method': affiliate.payout_method
                })
        
        return jsonify({'pending_payouts': pending_payouts})
        
    finally:
        db.close()

@affiliate_api.route('/api/admin/payouts', methods=['POST'])
@require_admin
def create_payout():
    """Create a payout for an affiliate"""
    db = get_db_session()
    try:
        service = AffiliateService(db)
        data = request.json
        
        # Get admin user ID from session
        from flask import session
        initiated_by = session.get('admin_user_id', 'admin_user_id')
        
        payout = service.create_payout(data['affiliate_id'], initiated_by)
        
        return jsonify({
            'id': str(payout.id),
            'affiliate_id': str(payout.affiliate_id),
            'amount': payout.amount,
            'status': payout.status.value,
            'created_at': payout.created_at.isoformat()
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

# Public Promo Code Endpoints
@affiliate_api.route('/api/apply-promo-code', methods=['POST'])
@csrf.exempt
def apply_promo_code():
    """Apply a promo code and add credits to user account"""
    try:
        data = request.json
        if not data or 'code' not in data:
            return jsonify({'error': 'Promo code required'}), 400
        
        code = data.get('code', '').strip().upper()
        if not code:
            return jsonify({'error': 'Promo code required'}), 400
        
        # Get user info from session
        from flask import session
        user_id = session.get('user_id')
        user_email = session.get('user_email')
        
        if not user_id:
            return jsonify({'error': 'User must be logged in'}), 401
        
        # Get user and team info
        from billing_models import User, Team
        db = get_db_session()
        
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        team = db.query(Team).filter_by(id=user.team_id).first()
        if not team:
            return jsonify({'error': 'Team not found'}), 404
        
        # Validate promo code using affiliate service
        affiliate_service = AffiliateService(db)
        is_valid, message, promo_code = affiliate_service.validate_promo_code(
            code, user_id, team.tier or 'free'
        )
        
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Apply the promo code
        credits_added = 0
        
        if promo_code.type == PromoCodeType.CREDIT_PACK:
            credits_added = promo_code.credit_amount or 0
            
            # Add credits to team
            team.credit_balance += credits_added
            
            # Log the credit addition
            from billing_models import CreditLog
            credit_log = CreditLog(
                team_id=team.id,
                delta=credits_added,
                reason=f'promo-{code}'
            )
            db.add(credit_log)
            
            # Create redemption record
            redemption = affiliate_service.redeem_promo_code(
                code, user_id, team.id, {
                    'amount': 0,  # No payment amount for direct credit application
                    'stripe_payment_id': None
                }
            )
            
            db.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully applied promo code {code}',
                'credits_added': credits_added,
                'new_balance': team.credit_balance,
                'promo_type': 'credit_pack'
            })
            
        else:
            # For other types (percentage discount, team bonus), they apply at checkout
            # Just mark as used for tracking
            redemption = affiliate_service.redeem_promo_code(
                code, user_id, team.id, {
                    'amount': 0,
                    'stripe_payment_id': None
                }
            )
            
            db.commit()
            
            return jsonify({
                'success': True,
                'message': f'Promo code {code} will be applied at checkout',
                'credits_added': 0,
                'new_balance': team.credit_balance,
                'promo_type': promo_code.type.value
            })
            
    except Exception as e:
        logging.error(f"Error applying promo code: {str(e)}")
        return jsonify({'error': 'Failed to apply promo code'}), 500
    finally:
        if 'db' in locals():
            db.close()

@affiliate_api.route('/api/validate-promo-code', methods=['POST'])
@csrf.exempt
def validate_promo_code_endpoint():
    """Validate a promo code without applying it"""
    try:
        data = request.json
        if not data or 'code' not in data:
            return jsonify({'error': 'Promo code required'}), 400
        
        code = data.get('code', '').strip().upper()
        if not code:
            return jsonify({'error': 'Promo code required'}), 400
        
        # Get user info from session
        from flask import session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User must be logged in'}), 401
        
        # Get user and team info
        from billing_models import User, Team
        db = get_db_session()
        
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        team = db.query(Team).filter_by(id=user.team_id).first()
        if not team:
            return jsonify({'error': 'Team not found'}), 404
        
        # Validate promo code using affiliate service
        affiliate_service = AffiliateService(db)
        is_valid, message, promo_code = affiliate_service.validate_promo_code(
            code, user_id, team.tier or 'free'
        )
        
        if not is_valid:
            return jsonify({'valid': False, 'message': message}), 200
        
        return jsonify({
            'valid': True,
            'message': 'Valid promo code',
            'code': promo_code.code,
            'type': promo_code.type.value,
            'credit_amount': promo_code.credit_amount,
            'discount_percentage': promo_code.discount_percentage,
            'description': promo_code.campaign_name or f'{promo_code.code} promo code'
        })
        
    except Exception as e:
        logging.error(f"Error validating promo code: {str(e)}")
        return jsonify({'error': 'Failed to validate promo code'}), 500
    finally:
        if 'db' in locals():
            db.close()

# Analytics Endpoints
@affiliate_api.route('/api/admin/affiliates/top-performers', methods=['GET'])
@require_admin
def get_top_affiliates():
    """Get top performing affiliates"""
    db = get_db_session()
    try:
        service = AffiliateService(db)
        
        period_days = int(request.args.get('period_days', 30))
        limit = int(request.args.get('limit', 10))
        
        top_affiliates = service.get_top_affiliates(limit, period_days)
        
        return jsonify({'top_affiliates': top_affiliates})
        
    finally:
        db.close()

@affiliate_api.route('/api/admin/promo-codes/analytics', methods=['GET'])
@require_admin
def get_promo_analytics():
    """Get promo code analytics"""
    db = get_db_session()
    try:
        from affiliate_models import PromoCode, PromoCodeRedemption
        from sqlalchemy import func
        
        # Get date range
        days = int(request.args.get('days', 30))
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Most used codes
        most_used = db.query(
            PromoCode.code,
            PromoCode.type,
            func.count(PromoCodeRedemption.id).label('redemptions')
        ).join(
            PromoCodeRedemption, PromoCode.id == PromoCodeRedemption.promo_code_id
        ).filter(
            PromoCodeRedemption.redeemed_at >= cutoff_date
        ).group_by(
            PromoCode.code, PromoCode.type
        ).order_by(
            func.count(PromoCodeRedemption.id).desc()
        ).limit(10).all()
        
        # Best converting codes
        best_converting = db.query(PromoCode).filter(
            PromoCode.conversion_rate > 0
        ).order_by(
            PromoCode.conversion_rate.desc()
        ).limit(10).all()
        
        results = {
            'most_used': [
                {
                    'code': code.code,
                    'type': code.type.value,
                    'redemptions': code.redemptions
                }
                for code in most_used
            ],
            'best_converting': [
                {
                    'code': code.code,
                    'type': code.type.value,
                    'conversion_rate': code.conversion_rate,
                    'total_revenue': code.total_revenue
                }
                for code in best_converting
            ]
        }
        
        return jsonify(results)
        
    finally:
        db.close()

# GPT-4o Integration Endpoints
@affiliate_api.route('/api/admin/affiliates/<affiliate_id>/generate-content', methods=['POST'])
@require_admin
def generate_affiliate_content(affiliate_id):
    """Generate marketing content for an affiliate using GPT-4o"""
    db = get_db_session()
    try:
        service = AffiliateService(db)
        data = request.json
        
        content_type = data.get('content_type', 'email_sequence')
        content = service.generate_affiliate_content(affiliate_id, content_type)
        
        return jsonify({
            'content': content,
            'content_type': content_type
        })
        
    finally:
        db.close()

@affiliate_api.route('/api/admin/ai/generate-promo-code', methods=['POST'])
@require_admin
def ai_generate_promo_code():
    """Use GPT-4o to generate a promo code based on requirements"""
    data = request.json
    requirements = data.get('requirements', '')
    
    try:
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        
        prompt = f"""
        Based on these requirements: "{requirements}"
        
        Generate a promo code configuration:
        1. Code name (6-10 characters, memorable)
        2. Type: percentage_discount, credit_pack, or team_bonus
        3. Value (percentage, credits, or seats)
        4. Validity period
        5. Target audience
        6. Campaign name
        
        Return as JSON format.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a marketing expert for a SaaS platform."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Parse response and create the promo code
        # In production, properly parse the GPT response
        
        return jsonify({
            'suggestion': response.choices[0].message.content,
            'ready_to_create': True
        })
        
    except Exception as e:
        logger.error(f"GPT-4o promo code generation failed: {str(e)}")
        return jsonify({'error': 'Failed to generate promo code'}), 500

# Validate promo code (public endpoint)
@affiliate_api.route('/api/validate-promo-code', methods=['POST'])
def validate_promo_code():
    """Validate a promo code for a user"""
    db = get_db_session()
    try:
        service = AffiliateService(db)
        data = request.json
        
        code = data.get('code', '')
        user_id = session.get('user_id', '')
        plan = data.get('plan', 'individual')
        
        is_valid, message, promo_code = service.validate_promo_code(code, user_id, plan)
        
        response = {
            'valid': is_valid,
            'message': message
        }
        
        if is_valid and promo_code:
            # Add discount info
            if promo_code.type == PromoCodeType.PERCENTAGE_DISCOUNT:
                response['discount_percentage'] = promo_code.discount_percentage
                response['first_month_only'] = promo_code.first_month_only
            elif promo_code.type == PromoCodeType.CREDIT_PACK:
                response['bonus_credits'] = promo_code.credit_amount
            elif promo_code.type == PromoCodeType.TEAM_BONUS:
                response['bonus_seats'] = promo_code.bonus_seats
        
        return jsonify(response)
        
    finally:
        db.close()