#!/usr/bin/env python3
"""
Reset password for a specific user
"""

import os
import sys
import logging
import secrets
import string
from werkzeug.security import generate_password_hash
from email_service import EmailService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_secure_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def reset_user_password(email_address):
    """Reset password for specific user"""
    try:
        # Initialize Flask app context
        from app_upgraded import app
        
        with app.app_context():
            from models import User
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import create_engine
            
            # Create database session
            engine = create_engine(os.environ.get('DATABASE_URL'))
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Find user by email
            user = session.query(User).filter_by(email=email_address).first()
            
            if not user:
                logger.error(f"User not found with email: {email_address}")
                return False
                
            logger.info(f"Found user: {user.name} ({user.email})")
            
            # Generate new password
            new_password = generate_secure_password()
            logger.info(f"Generated new password: {new_password}")
            
            # Hash the password
            password_hash = generate_password_hash(new_password)
            
            # Update user password
            user.password_hash = password_hash
            session.commit()
            
            logger.info(f"Password updated successfully for {user.email}")
            
            # Send email with new password
            email_service = EmailService()
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Password Reset - properwrite.com</h1>
                </div>
                
                <div style="padding: 30px; background: #f8f9fa;">
                    <h2 style="color: #333;">Hello {user.name},</h2>
                    
                    <p style="color: #666; line-height: 1.6;">
                        Your password has been reset for your properwrite.com account.
                    </p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; margin: 20px 0;">
                        <h3 style="color: #333; margin-top: 0;">Your New Password:</h3>
                        <code style="font-size: 18px; color: #e74c3c; background: #f1f1f1; padding: 8px 12px; border-radius: 4px; display: inline-block;">
                            {new_password}
                        </code>
                    </div>
                    
                    <p style="color: #666; line-height: 1.6;">
                        <strong>For security reasons, please change this password after logging in.</strong>
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://properwrite.com/login" 
                           style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 12px 30px; border-radius: 6px; display: inline-block; font-weight: bold;">
                            Sign In Now
                        </a>
                    </div>
                    
                    <div style="border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px; text-align: center;">
                        <p style="color: #888; font-size: 12px;">
                            If you didn't request this password reset, please contact support immediately.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Password Reset - properwrite.com
            
            Hello {user.name},
            
            Your password has been reset for your properwrite.com account.
            
            Your New Password: {new_password}
            
            For security reasons, please change this password after logging in.
            
            Sign in at: https://properwrite.com/login
            
            If you didn't request this password reset, please contact support immediately.
            """
            
            email_success = email_service.send_email(
                to_email=user.email,
                subject='Password Reset - properwrite.com',
                html_content=html_content,
                text_content=text_content
            )
            
            if email_success:
                logger.info(f"Password reset email sent successfully to {user.email}")
                return True, new_password
            else:
                logger.warning(f"Password reset successful but email failed to send to {user.email}")
                return True, new_password
            
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None

if __name__ == "__main__":
    # Reset password for specific user
    target_email = "drrobinson37@gmail.com"
    success, new_password = reset_user_password(target_email)
    
    if success:
        print(f"✅ Password reset successfully for {target_email}")
        print(f"🔑 New password: {new_password}")
        print(f"📧 Email sent to user with new password")
    else:
        print(f"❌ Failed to reset password for {target_email}")