"""
Password Reset Routes for One-Click Password Reset with Email Verification
Handles forgot password, reset password, and email verification flows
"""

from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, PasswordResetToken
from main import app, db
from password_reset_service import PasswordResetService
import logging
import re

logger = logging.getLogger(__name__)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Handle forgot password requests
    GET: Show forgot password form
    POST: Process forgot password request and send email
    """
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
    # POST request - process forgot password
    try:
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        # Check if user exists
        user = db.session.query(User).filter_by(email=email).first()
        
        if not user:
            # For security, don't reveal if email exists or not
            flash('If an account with this email exists, you will receive a password reset email shortly.', 'info')
            return render_template('auth/forgot_password.html')
        
        if not user.is_active:
            # For security, don't reveal if account is inactive
            flash('If an account with this email exists, you will receive a password reset email shortly.', 'info')
            return render_template('auth/forgot_password.html')
        
        # Generate reset token and send email
        password_reset_service = PasswordResetService(db.session)
        reset_token = password_reset_service.generate_reset_token(user.id)
        
        # Send password reset email
        email_sent = password_reset_service.send_password_reset_email(
            user_email=user.email,
            user_name=user.name,
            reset_token=reset_token
        )
        
        if email_sent:
            flash('Password reset email sent! Check your inbox and click the link to reset your password.', 'success')
            logger.info(f"Password reset email sent to {user.email}")
        else:
            flash('There was an error sending the password reset email. Please try again or contact support.', 'error')
            logger.error(f"Failed to send password reset email to {user.email}")
        
        return render_template('auth/forgot_password.html')
        
    except Exception as e:
        logger.error(f"Error processing forgot password request: {str(e)}")
        flash('An error occurred. Please try again or contact support.', 'error')
        return render_template('auth/forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """
    Handle password reset with token
    GET: Show reset password form (with token validation)
    POST: Process new password and update user
    """
    token = request.args.get('token') or request.form.get('token')
    
    if not token:
        flash('Invalid or missing password reset token.', 'error')
        return redirect(url_for('login'))
    
    # Initialize password reset service
    password_reset_service = PasswordResetService(db.session)
    
    # Validate token
    token_data = password_reset_service.validate_reset_token(token)
    if not token_data:
        flash('Invalid or expired password reset token. Please request a new password reset.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'GET':
        # Show reset password form
        return render_template('auth/reset_password.html', 
                             token=token,
                             email=token_data['email'],
                             user_name=token_data['name'])
    
    # POST request - process password reset
    try:
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('auth/reset_password.html', 
                                 token=token,
                                 email=token_data['email'],
                                 user_name=token_data['name'])
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/reset_password.html', 
                                 token=token,
                                 email=token_data['email'],
                                 user_name=token_data['name'])
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', 
                                 token=token,
                                 email=token_data['email'],
                                 user_name=token_data['name'])
        
        # Re-validate token (in case it expired during form submission)
        token_data = password_reset_service.validate_reset_token(token)
        if not token_data:
            flash('Password reset token has expired. Please request a new password reset.', 'error')
            return redirect(url_for('forgot_password'))
        
        # Update user password
        user = db.session.query(User).filter_by(id=token_data['user_id']).first()
        if not user:
            flash('User account not found.', 'error')
            return redirect(url_for('login'))
        
        # Hash the new password
        password_hash = generate_password_hash(new_password)
        user.password_hash = password_hash
        
        # Mark token as used
        password_reset_service.mark_token_used(token)
        
        # Commit changes
        db.session.commit()
        
        # Log successful password reset
        logger.info(f"Password reset successful for user {user.email}")
        
        # Auto-login user after successful password reset
        login_user(user)
        
        flash('Password reset successful! You are now logged in.', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Error processing password reset: {str(e)}")
        flash('An error occurred while resetting your password. Please try again.', 'error')
        return render_template('auth/reset_password.html', 
                             token=token,
                             email=token_data['email'],
                             user_name=token_data['name'])

@app.route('/api/check-reset-token', methods=['POST'])
def check_reset_token():
    """
    API endpoint to check if a password reset token is valid
    Used by frontend for token validation
    """
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'valid': False, 'message': 'Token is required'}), 400
        
        password_reset_service = PasswordResetService(db.session)
        token_data = password_reset_service.validate_reset_token(token)
        
        if token_data:
            return jsonify({
                'valid': True,
                'user_email': token_data['email'],
                'user_name': token_data['name']
            })
        else:
            return jsonify({'valid': False, 'message': 'Invalid or expired token'})
            
    except Exception as e:
        logger.error(f"Error checking reset token: {str(e)}")
        return jsonify({'valid': False, 'message': 'Server error'}), 500

@app.route('/api/cleanup-expired-tokens', methods=['POST'])
def cleanup_expired_tokens():
    """
    API endpoint to manually trigger cleanup of expired password reset tokens
    Admin only - can be called periodically
    """
    try:
        # Simple admin check - you can enhance this with proper admin authentication
        admin_key = request.headers.get('Admin-Key')
        if admin_key != 'admin123':  # Use your admin key
            return jsonify({'error': 'Unauthorized'}), 401
        
        password_reset_service = PasswordResetService(db.session)
        cleaned_count = password_reset_service.cleanup_expired_tokens()
        
        return jsonify({
            'success': True,
            'cleaned_tokens': cleaned_count,
            'message': f'Cleaned up {cleaned_count} expired tokens'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {str(e)}")
        return jsonify({'error': 'Server error'}), 500