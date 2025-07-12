"""
Zapier API Endpoints
Inbound actions from Zapier with authentication
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import uuid
from zapier_webhook_service import require_zapier_auth, zapier_service
from billing_models import User, Team, CreditLog
from jv_database import JVDatabase
from admin_database_models import CreditLedger

zapier_api_bp = Blueprint('zapier_api', __name__, url_prefix='/admin/zap')
logger = logging.getLogger(__name__)

# Get database session
def get_db_session():
    """Get database session from billing service"""
    from billing_service import engine
    return Session(engine)

@zapier_api_bp.route('/credits/grant', methods=['POST'])
@require_zapier_auth
def grant_bonus_credits():
    """
    Grant bonus credits to a user
    Expected payload: {user_id, credits, reason}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON payload'}), 422
            
        user_id = data.get('user_id')
        credits = data.get('credits')
        reason = data.get('reason', 'Zapier bonus credits')
        
        # Validate inputs
        if not user_id or not credits:
            return jsonify({'error': 'Missing required fields: user_id, credits'}), 422
            
        try:
            credits = int(credits)
            if credits <= 0:
                return jsonify({'error': 'Credits must be positive'}), 422
        except ValueError:
            return jsonify({'error': 'Credits must be a number'}), 422
            
        with get_db_session() as db:
            # Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': f'User not found: {user_id}'}), 404
                
            # Get current balance
            current_balance = user.credits_balance or 0
            new_balance = current_balance + credits
            
            # Update user credits
            user.credits_balance = new_balance
            
            # Log the credit transaction
            credit_log = CreditLedger(
                id=uuid.uuid4(),
                user_id=user.id,
                team_id=user.team_id,
                transaction_type='credit',
                amount=credits,
                balance_after=new_balance,
                source='zapier_grant',
                source_id=f'zap_{datetime.utcnow().timestamp()}',
                description=reason
            )
            db.add(credit_log)
            db.commit()
            
            logger.info(f"Granted {credits} credits to user {user_id} via Zapier")
            
            return jsonify({
                'success': True,
                'user_id': str(user_id),
                'credits_granted': credits,
                'new_balance': new_balance,
                'transaction_id': str(credit_log.id)
            }), 200
            
    except Exception as e:
        logger.error(f"Error granting credits via Zapier: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@zapier_api_bp.route('/jv/approve', methods=['POST'])
@require_zapier_auth
def approve_jv_deal():
    """
    Approve a JV deal
    Expected payload: {deal_id, notes}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON payload'}), 422
            
        deal_id = data.get('deal_id')
        notes = data.get('notes', '')
        
        if not deal_id:
            return jsonify({'error': 'Missing required field: deal_id'}), 422
            
        # Use JV database to update deal
        jv_db = JVDatabase()
        
        # Get deal details first
        with get_db_session() as db:
            from jv_database import JVDeal
            deal = db.query(JVDeal).filter(JVDeal.id == deal_id).first()
            if not deal:
                return jsonify({'error': f'Deal not found: {deal_id}'}), 404
                
            # Update deal status
            deal.status = 'approved'
            deal.admin_status = 'Approved'
            deal.admin_notes = notes
            deal.updated_at = datetime.utcnow()
            db.commit()
            
            # Prepare deal data for webhook
            deal_data = {
                'id': deal.id,
                'address': deal.property_address,
                'partner_name': deal.partner.full_name if deal.partner else 'Unknown',
                'partner_email': deal.partner.email if deal.partner else 'Unknown',
                'approved_by': 'zapier_automation'
            }
            
            # Fire approved webhook
            from zapier_webhook_service import trigger_jv_approved
            trigger_jv_approved(deal_data)
            
            logger.info(f"Approved JV deal {deal_id} via Zapier")
            
            return jsonify({
                'success': True,
                'deal_id': str(deal_id),
                'status': 'approved',
                'approved_at': datetime.utcnow().isoformat()
            }), 200
            
    except Exception as e:
        logger.error(f"Error approving JV deal via Zapier: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@zapier_api_bp.route('/notify', methods=['POST'])
@require_zapier_auth
def send_user_notification():
    """
    Send notification to a user
    Expected payload: {user_id, message, type}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON payload'}), 422
            
        user_id = data.get('user_id')
        message = data.get('message')
        notification_type = data.get('type', 'info')
        
        if not user_id or not message:
            return jsonify({'error': 'Missing required fields: user_id, message'}), 422
            
        with get_db_session() as db:
            # Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': f'User not found: {user_id}'}), 404
            
            # For now, log the notification
            # In a real implementation, you'd insert into a notifications table
            # and/or send an email
            logger.info(f"Notification for user {user_id}: {message}")
            
            # If email service is configured, send email
            try:
                from email_service import email_service
                if notification_type == 'important':
                    email_service.send_email(
                        to_email=user.email,
                        subject="Important Notification from properwrite.com",
                        html_content=f"""
                        <div style="font-family: Arial, sans-serif; padding: 20px;">
                            <h2>Important Notification</h2>
                            <p>{message}</p>
                            <p>Best regards,<br>The properwrite.com Team</p>
                        </div>
                        """
                    )
            except Exception as email_error:
                logger.warning(f"Could not send email notification: {str(email_error)}")
            
            return jsonify({
                'success': True,
                'user_id': str(user_id),
                'message_sent': message,
                'type': notification_type,
                'sent_at': datetime.utcnow().isoformat()
            }), 200
            
    except Exception as e:
        logger.error(f"Error sending notification via Zapier: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@zapier_api_bp.route('/test', methods=['GET'])
@require_zapier_auth
def test_zapier_connection():
    """Test endpoint to verify Zapier authentication"""
    return jsonify({
        'success': True,
        'message': 'Zapier authentication successful',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# Additional useful endpoints for Zapier

@zapier_api_bp.route('/credits/deduct', methods=['POST'])
@require_zapier_auth
def deduct_credits():
    """
    Deduct credits from a user
    Expected payload: {user_id, credits, reason}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON payload'}), 422
            
        user_id = data.get('user_id')
        credits = data.get('credits')
        reason = data.get('reason', 'Zapier credit deduction')
        
        # Validate inputs
        if not user_id or not credits:
            return jsonify({'error': 'Missing required fields: user_id, credits'}), 422
            
        try:
            credits = int(credits)
            if credits <= 0:
                return jsonify({'error': 'Credits must be positive'}), 422
        except ValueError:
            return jsonify({'error': 'Credits must be a number'}), 422
            
        with get_db_session() as db:
            # Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': f'User not found: {user_id}'}), 404
                
            # Get current balance
            current_balance = user.credits_balance or 0
            
            # Check if user has enough credits
            if current_balance < credits:
                return jsonify({'error': 'Insufficient credits'}), 400
                
            new_balance = current_balance - credits
            
            # Update user credits
            user.credits_balance = new_balance
            
            # Log the credit transaction
            credit_log = CreditLedger(
                id=uuid.uuid4(),
                user_id=user.id,
                team_id=user.team_id,
                transaction_type='debit',
                amount=-credits,
                balance_after=new_balance,
                source='zapier_deduct',
                source_id=f'zap_{datetime.utcnow().timestamp()}',
                description=reason
            )
            db.add(credit_log)
            db.commit()
            
            # Check if credits are low
            if new_balance <= 10:
                from zapier_webhook_service import trigger_credits_low
                trigger_credits_low({'id': user.id, 'email': user.email}, new_balance)
            
            logger.info(f"Deducted {credits} credits from user {user_id} via Zapier")
            
            return jsonify({
                'success': True,
                'user_id': str(user_id),
                'credits_deducted': credits,
                'new_balance': new_balance,
                'transaction_id': str(credit_log.id)
            }), 200
            
    except Exception as e:
        logger.error(f"Error deducting credits via Zapier: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@zapier_api_bp.route('/user/update-plan', methods=['POST'])
@require_zapier_auth
def update_user_plan():
    """
    Update user's subscription plan
    Expected payload: {user_id, plan}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON payload'}), 422
            
        user_id = data.get('user_id')
        plan = data.get('plan')
        
        if not user_id or not plan:
            return jsonify({'error': 'Missing required fields: user_id, plan'}), 422
            
        valid_plans = ['free', 'pro', 'team5', 'growth10']
        if plan.lower() not in valid_plans:
            return jsonify({'error': f'Invalid plan. Must be one of: {valid_plans}'}), 422
            
        with get_db_session() as db:
            # Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': f'User not found: {user_id}'}), 404
                
            # Update user plan
            old_plan = user.subscription_tier
            user.subscription_tier = plan.lower()
            db.commit()
            
            logger.info(f"Updated user {user_id} plan from {old_plan} to {plan} via Zapier")
            
            return jsonify({
                'success': True,
                'user_id': str(user_id),
                'old_plan': old_plan,
                'new_plan': plan,
                'updated_at': datetime.utcnow().isoformat()
            }), 200
            
    except Exception as e:
        logger.error(f"Error updating user plan via Zapier: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500