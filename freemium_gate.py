"""
Freemium Access Gate Middleware
Implements feature gating with free trial functionality
"""

import logging
from functools import wraps
from flask import request, jsonify, session, make_response
from auth_middleware import auth_service
from billing_service import BillingService

# Initialize billing service
billing_service = BillingService()

# Features that are always public (no gating)
PUBLIC_FEATURES = {
    'wholesalePrice',
    'propertyData',  # Basic property info display
    'landingPage'    # Main page viewing
}

def gate_feature(feature_name):
    """
    Decorator to gate features based on authentication and free use
    
    Args:
        feature_name (str): Name of the feature to gate
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if feature is public
            if feature_name in PUBLIC_FEATURES:
                return f(*args, **kwargs)
            
            # Check if user is authenticated
            auth_data = auth_service.get_current_user()
            if auth_data['success']:
                # User is authenticated, allow access
                return f(*args, **kwargs)
            
            # User is not authenticated, check free use
            free_use_cookie = request.cookies.get('free_use')
            
            # If user hasn't used their free action yet
            if not free_use_cookie:
                # Allow this action and set the cookie
                response = make_response(f(*args, **kwargs))
                
                # Set free use cookie (expires in 1 year)
                response.set_cookie(
                    'free_use', 
                    'true', 
                    max_age=365*24*3600,  # 1 year
                    httponly=False,       # Allow JavaScript access
                    samesite='Lax'
                )
                
                # Add header to indicate this was a free use
                response.headers['X-Free-Use'] = 'true'
                
                return response
            
            # User has already used their free action
            return jsonify({
                'error': 'auth_required',
                'message': 'Create an account to unlock this feature. Get 5 free credits + full access.',
                'feature': feature_name
            }), 403
            
        return decorated_function
    return decorator

def check_free_use_status():
    """
    Check if user has used their free action
    
    Returns:
        Dict with free use status
    """
    auth_data = auth_service.get_current_user()
    if auth_data['success']:
        return {
            'authenticated': True,
            'free_use_available': False,
            'free_use_used': False
        }
    
    free_use_cookie = request.cookies.get('free_use')
    return {
        'authenticated': False,
        'free_use_available': not bool(free_use_cookie),
        'free_use_used': bool(free_use_cookie)
    }

def seed_free_credits(user_id: str) -> bool:
    """
    Seed new user with 5 free credits
    
    Args:
        user_id (str): User ID
        
    Returns:
        bool: Success status
    """
    try:
        with billing_service.db_session() as db:
            from billing_models import Team, User
            
            # Get user and team
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
                
            team = db.query(Team).filter(Team.id == user.team_id).first()
            if not team:
                return False
            
            # Add 5 free credits to team
            team.credit_balance += 5
            
            # Log the credit addition
            billing_service.log_credit_transaction(
                team_id=str(team.id),
                amount=5,
                transaction_type='free_signup',
                description='Free signup bonus credits'
            )
            
            db.commit()
            logging.info(f"Seeded 5 free credits for user {user_id}")
            return True
            
    except Exception as e:
        logging.error(f"Error seeding free credits: {e}")
        return False

def get_feature_access_info(feature_name: str) -> dict:
    """
    Get information about feature access for frontend
    
    Args:
        feature_name (str): Feature name
        
    Returns:
        dict: Access information
    """
    # Check if feature is public
    if feature_name in PUBLIC_FEATURES:
        return {
            'accessible': True,
            'reason': 'public_feature',
            'action_required': None
        }
    
    # Check authentication
    auth_data = auth_service.get_current_user()
    if auth_data['success']:
        return {
            'accessible': True,
            'reason': 'authenticated',
            'action_required': None
        }
    
    # Check free use status
    free_use_status = check_free_use_status()
    
    if free_use_status['free_use_available']:
        return {
            'accessible': True,
            'reason': 'free_use_available',
            'action_required': None
        }
    
    return {
        'accessible': False,
        'reason': 'auth_required',
        'action_required': 'signup',
        'message': 'Create an account to unlock this feature. Get 5 free credits + full access.'
    }