"""
Zapier Webhook Service
Handles outbound triggers and inbound actions for Zapier integration
"""
import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

class ZapierWebhookService:
    """Service for handling Zapier webhook integrations"""
    
    def __init__(self):
        self.webhook_urls = {
            'NEW_USER_SIGNED_UP': os.environ.get('ZAPIER_HOOK_NEW_USER_SIGNED_UP'),
            'CREDITS_BELOW_THRESHOLD': os.environ.get('ZAPIER_HOOK_CREDITS_BELOW_THRESHOLD'),
            'NEW_JV_SUBMISSION': os.environ.get('ZAPIER_HOOK_NEW_JV_SUBMISSION'),
            'PAYMENT_RECEIVED': os.environ.get('ZAPIER_HOOK_PAYMENT_RECEIVED'),
            'JV_DEAL_APPROVED': os.environ.get('ZAPIER_HOOK_JV_DEAL_APPROVED'),
            'SUBSCRIPTION_CANCELLED': os.environ.get('ZAPIER_HOOK_SUBSCRIPTION_CANCELLED'),
            'TEAM_MEMBER_ADDED': os.environ.get('ZAPIER_HOOK_TEAM_MEMBER_ADDED'),
            'ERROR_THRESHOLD_REACHED': os.environ.get('ZAPIER_HOOK_ERROR_THRESHOLD_REACHED')
        }
        self.shared_secret = os.environ.get('ZAPIER_SHARED_SECRET', 'dev-zapier-secret')
        

    
    def fire_webhook(self, trigger_name: str, payload: Dict[str, Any]) -> bool:
        """Fire a Zapier webhook synchronously"""
        url = self.webhook_urls.get(trigger_name)
        if not url:
            logger.warning(f"No webhook URL configured for trigger: {trigger_name}")
            return False
            
        try:
            # Add metadata to payload
            enriched_payload = {
                **payload,
                '_metadata': {
                    'trigger': trigger_name,
                    'timestamp': datetime.utcnow().isoformat(),
                    'environment': os.environ.get('REPLIT_ENV', 'development')
                }
            }
            
            response = requests.post(
                url,
                json=enriched_payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully fired Zapier webhook: {trigger_name}")
                return True
            else:
                logger.error(f"Zapier webhook failed: {trigger_name}, status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error firing Zapier webhook {trigger_name}: {str(e)}")
            return False
    
    def validate_zapier_secret(self, provided_secret: str) -> bool:
        """Validate the Zapier shared secret"""
        return provided_secret == self.shared_secret

def require_zapier_auth(f):
    """Decorator to require Zapier authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        provided_secret = request.headers.get('X-ZAP-SECRET')
        
        if not provided_secret:
            return jsonify({'error': 'Missing authentication header'}), 401
            
        zapier_service = ZapierWebhookService()
        if not zapier_service.validate_zapier_secret(provided_secret):
            return jsonify({'error': 'Invalid authentication'}), 401
            
        return f(*args, **kwargs)
    return decorated_function

# Global instance
zapier_service = ZapierWebhookService()

# Helper functions for common triggers
def trigger_new_user_signup(user_data: Dict[str, Any]):
    """Trigger when a new user signs up"""
    payload = {
        'user_id': str(user_data.get('id')),
        'email': user_data.get('email'),
        'plan': user_data.get('plan', 'free'),
        'team_id': str(user_data.get('team_id')) if user_data.get('team_id') else None,
        'created_at': user_data.get('created_at', datetime.utcnow()).isoformat()
    }
    zapier_service.fire_webhook('NEW_USER_SIGNED_UP', payload)

def trigger_credits_low(user_data: Dict[str, Any], balance: int):
    """Trigger when user credits are below threshold"""
    payload = {
        'user_id': str(user_data.get('id')),
        'email': user_data.get('email'),
        'balance': balance,
        'plan': user_data.get('plan', 'free'),
        'threshold': 10  # Configurable threshold
    }
    zapier_service.fire_webhook('CREDITS_BELOW_THRESHOLD', payload)

def trigger_jv_submission(deal_data: Dict[str, Any]):
    """Trigger when a new JV deal is submitted"""
    payload = {
        'deal_id': str(deal_data.get('id')),
        'address': deal_data.get('address'),
        'user_id': str(deal_data.get('user_id')),
        'partner_name': deal_data.get('partner_name'),
        'partner_email': deal_data.get('partner_email'),
        'status': deal_data.get('status', 'pending'),
        'submitted_at': deal_data.get('created_at', datetime.utcnow()).isoformat()
    }
    zapier_service.fire_webhook('NEW_JV_SUBMISSION', payload)

def trigger_payment_received(payment_data: Dict[str, Any]):
    """Trigger when a payment is received"""
    payload = {
        'customer_id': payment_data.get('customer_id'),
        'user_id': str(payment_data.get('user_id')) if payment_data.get('user_id') else None,
        'amount': payment_data.get('amount'),
        'currency': payment_data.get('currency', 'usd'),
        'plan': payment_data.get('plan_name'),
        'invoice_id': payment_data.get('invoice_id'),
        'subscription_id': payment_data.get('subscription_id'),
        'payment_date': datetime.utcnow().isoformat()
    }
    zapier_service.fire_webhook('PAYMENT_RECEIVED', payload)

def trigger_jv_approved(deal_data: Dict[str, Any]):
    """Trigger when a JV deal is approved"""
    payload = {
        'deal_id': str(deal_data.get('id')),
        'address': deal_data.get('address'),
        'partner_name': deal_data.get('partner_name'),
        'partner_email': deal_data.get('partner_email'),
        'approved_by': deal_data.get('approved_by', 'admin'),
        'approved_at': datetime.utcnow().isoformat()
    }
    zapier_service.fire_webhook('JV_DEAL_APPROVED', payload)

def trigger_error_threshold(error_count: int, error_type: str):
    """Trigger when error count exceeds threshold"""
    payload = {
        'error_count': error_count,
        'error_type': error_type,
        'threshold': 10,  # Configurable
        'time_window': '1_hour',
        'alert_time': datetime.utcnow().isoformat()
    }
    zapier_service.fire_webhook('ERROR_THRESHOLD_REACHED', payload)