from flask import session, request, jsonify
from flask_login import current_user
from models import User, GuestUsage
import logging
import uuid
from datetime import datetime

def check_usage_limit(db):
    """
    Check if user can use the analyzer
    Returns: (can_use: bool, message: str, redirect_url: str|None)
    """
    
    # If user is logged in, check their credits
    if current_user.is_authenticated:
        if current_user.credits > 0:
            return True, f"You have {current_user.credits} credits remaining", None
        else:
            return False, "You've used all your credits. Purchase more to continue.", "/purchase-credits"
    
    # For guests, check session and IP-based usage
    ip_address = request.remote_addr
    session_id = session.get('session_id')
    
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    # Check guest usage
    guest_usage = db.session.query(GuestUsage).filter_by(
        ip_address=ip_address, 
        session_id=session_id
    ).first()
    
    if guest_usage:
        if guest_usage.usage_count >= 1:
            return False, "Free trial expired. Register with your email to get 4 more credits.", "/register"
        else:
            return True, "This is your free trial use", None
    else:
        return True, "This is your free trial use", None

def consume_credit(db):
    """
    Consume one credit/usage
    Returns: (success: bool, message: str)
    """
    
    if current_user.is_authenticated:
        if current_user.use_credit():
            db.session.commit()
            return True, f"Analysis complete. {current_user.credits} credits remaining."
        else:
            return False, "No credits remaining. Please purchase more credits."
    
    # For guests
    ip_address = request.remote_addr
    session_id = session.get('session_id')
    
    guest_usage = db.session.query(GuestUsage).filter_by(
        ip_address=ip_address, 
        session_id=session_id
    ).first()
    
    if guest_usage:
        guest_usage.usage_count += 1
        guest_usage.updated_at = datetime.utcnow()
    else:
        guest_usage = GuestUsage(
            ip_address=ip_address,
            session_id=session_id,
            usage_count=1
        )
        db.session.add(guest_usage)
    
    db.session.commit()
    return True, "Free trial used. Register to get 4 more credits."

def get_user_status(db):
    """Get current user status for frontend"""
    if current_user.is_authenticated:
        return {
            'logged_in': True,
            'email': current_user.email,
            'credits': current_user.credits,
            'total_used': current_user.total_credits_used
        }
    
    # Check guest usage
    ip_address = request.remote_addr
    session_id = session.get('session_id')
    
    guest_usage = db.session.query(GuestUsage).filter_by(
        ip_address=ip_address, 
        session_id=session_id
    ).first()
    
    used_count = guest_usage.usage_count if guest_usage else 0
    remaining = max(0, 1 - used_count)
    
    return {
        'logged_in': False,
        'guest_uses_remaining': remaining,
        'guest_uses_total': used_count
    }