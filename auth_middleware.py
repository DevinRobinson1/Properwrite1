"""
Authentication and Authorization Middleware
Handles user authentication, team access control, and seat limits
"""

import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, g
from sqlalchemy.orm import Session
from sqlalchemy import and_, create_engine
from billing_models import User, Team
from billing_service import BillingService
import logging

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

class AuthService:
    def __init__(self):
        self.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
        self.billing_service = BillingService()
    
    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """
        Generate JWT token for user authentication
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> dict:
        """
        Verify JWT token and return user data
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return {'success': True, 'user_id': payload['user_id']}
        except jwt.ExpiredSignatureError:
            return {'success': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'success': False, 'error': 'Invalid token'}
    
    def get_current_user(self) -> dict:
        """
        Get current user from session or token
        """
        try:
            with Session(engine) as db:
                # Try session first
                user_id = session.get('user_id')
                
                # Try Authorization header
                if not user_id:
                    auth_header = request.headers.get('Authorization')
                    if auth_header and auth_header.startswith('Bearer '):
                        token = auth_header.split(' ')[1]
                        token_data = self.verify_token(token)
                        if token_data['success']:
                            user_id = token_data['user_id']
                
                if not user_id:
                    return {'success': False, 'error': 'Not authenticated'}
                
                # Get user with team data
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.is_active:
                    return {'success': False, 'error': 'User not found or inactive'}
                
                team = db.query(Team).filter(Team.id == user.team_id).first()
                if not team:
                    return {'success': False, 'error': 'Team not found'}
                
                return {
                    'success': True,
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'name': user.name,
                        'role': user.role,
                        'team_id': str(user.team_id)
                    },
                    'team': {
                        'id': str(team.id),
                        'name': team.name,
                        'tier': team.tier,
                        'seats_max': team.seats_max,
                        'credit_balance': team.credit_balance
                    }
                }
                
        except Exception as e:
            logging.error(f"Error getting current user: {e}")
            return {'success': False, 'error': 'Authentication error'}

auth_service = AuthService()

def require_auth(f):
    """
    Decorator to require authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_data = auth_service.get_current_user()
        if not auth_data['success']:
            return jsonify({'error': auth_data['error']}), 401
        
        # Store user data in Flask g for use in route
        g.current_user = auth_data['user']
        g.current_team = auth_data['team']
        
        return f(*args, **kwargs)
    return decorated_function

def require_seat(f):
    """
    Decorator to enforce seat limits
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check authentication
        auth_data = auth_service.get_current_user()
        if not auth_data['success']:
            return jsonify({'error': auth_data['error']}), 401
        
        try:
            with Session(engine) as db:
                # Count active users in team
                active_users = db.query(User).filter(
                    and_(User.team_id == auth_data['team']['id'], User.is_active == True)
                ).count()
                
                if active_users > auth_data['team']['seats_max']:
                    return jsonify({
                        'error': 'Team has exceeded seat limit',
                        'seats_used': active_users,
                        'seats_max': auth_data['team']['seats_max']
                    }), 402
                
                # Store user data in Flask g for use in route
                g.current_user = auth_data['user']
                g.current_team = auth_data['team']
                
                return f(*args, **kwargs)
                
        except Exception as e:
            logging.error(f"Error checking seat limit: {e}")
            return jsonify({'error': 'Authorization error'}), 500
    
    return decorated_function

def require_role(required_role):
    """
    Decorator to require specific role (owner, manager, analyst)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_data = auth_service.get_current_user()
            if not auth_data['success']:
                return jsonify({'error': auth_data['error']}), 401
            
            user_role = auth_data['user']['role']
            
            # Role hierarchy: owner > manager > analyst
            role_levels = {'owner': 3, 'manager': 2, 'analyst': 1}
            
            if role_levels.get(user_role, 0) < role_levels.get(required_role, 0):
                return jsonify({
                    'error': f'Insufficient permissions. Required: {required_role}',
                    'user_role': user_role
                }), 403
            
            # Store user data in Flask g for use in route
            g.current_user = auth_data['user']
            g.current_team = auth_data['team']
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_credits(f):
    """
    Decorator to check and consume credits for analysis
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_data = auth_service.get_current_user()
        if not auth_data['success']:
            return jsonify({'error': auth_data['error']}), 401
        
        # Check and consume credit
        billing_service = BillingService()
        credit_result = billing_service.consume_credit(
            auth_data['team']['id'], 
            'analysis'
        )
        
        if not credit_result['success']:
            if credit_result.get('code') == 402:
                return jsonify({
                    'error': 'Insufficient credits',
                    'credit_balance': 0,
                    'upgrade_url': '/settings/billing'
                }), 402
            else:
                return jsonify({'error': credit_result['error']}), 500
        
        # Store user data and remaining credits in Flask g
        g.current_user = auth_data['user']
        g.current_team = auth_data['team']
        g.remaining_credits = credit_result['remaining_credits']
        
        return f(*args, **kwargs)
    return decorated_function