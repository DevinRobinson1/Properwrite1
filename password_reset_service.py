"""
Password Reset Service for One-Click Password Reset with Email Verification
Handles password reset token generation, validation, and email sending
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from models import User, PasswordResetToken
from email_service import EmailService
import logging

logger = logging.getLogger(__name__)

class PasswordResetService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.email_service = EmailService()
        
    def generate_reset_token(self, user_id: str) -> str:
        """
        Generate a secure password reset token
        Returns: secure token string
        """
        # Generate cryptographically secure token
        token = secrets.token_urlsafe(32)
        
        # Create hash of token for database storage (security best practice)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Set expiration time (15 minutes from now)
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        # Delete any existing tokens for this user
        self.db_session.query(PasswordResetToken).filter_by(user_id=user_id).delete()
        
        # Create new token record
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False
        )
        
        self.db_session.add(reset_token)
        self.db_session.commit()
        
        return token
    
    def validate_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate password reset token
        Returns: user data if valid, None if invalid
        """
        if not token:
            return None
        
        # Create hash of provided token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Find token in database
        reset_token = self.db_session.query(PasswordResetToken).filter_by(
            token_hash=token_hash,
            used=False
        ).first()
        
        if not reset_token:
            logger.warning(f"Invalid or used password reset token attempted")
            return None
        
        # Check if token has expired
        if datetime.utcnow() > reset_token.expires_at:
            logger.warning(f"Expired password reset token attempted")
            # Clean up expired token
            self.db_session.delete(reset_token)
            self.db_session.commit()
            return None
        
        # Get user data
        user = self.db_session.query(User).filter_by(id=reset_token.user_id).first()
        if not user:
            logger.error(f"User not found for valid password reset token")
            return None
        
        return {
            'user_id': user.id,
            'email': user.email,
            'name': user.name,
            'token_id': reset_token.id
        }
    
    def mark_token_used(self, token: str) -> bool:
        """
        Mark password reset token as used
        Returns: True if successful, False otherwise
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        reset_token = self.db_session.query(PasswordResetToken).filter_by(
            token_hash=token_hash,
            used=False
        ).first()
        
        if reset_token:
            reset_token.used = True
            reset_token.used_at = datetime.utcnow()
            self.db_session.commit()
            return True
        
        return False
    
    def send_password_reset_email(self, user_email: str, user_name: str, reset_token: str) -> bool:
        """
        Send password reset email with one-click reset link
        Returns: True if email sent successfully, False otherwise
        """
        try:
            # Create reset link
            base_url = os.environ.get('BASE_URL', 'https://properwrite.com')
            reset_link = f"{base_url}/reset-password?token={reset_token}"
            
            # Email subject
            subject = "Reset Your Properwrite Password - One-Click Reset"
            
            # HTML email content
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        line-height: 1.6; 
                        color: #333; 
                        margin: 0; 
                        padding: 0;
                    }}
                    .container {{ 
                        max-width: 600px; 
                        margin: 0 auto; 
                        padding: 20px; 
                    }}
                    .header {{ 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 40px 30px; 
                        text-align: center; 
                        border-radius: 10px 10px 0 0; 
                    }}
                    .header h1 {{ 
                        color: white; 
                        margin: 0; 
                        font-size: 28px; 
                        font-weight: bold;
                    }}
                    .header p {{ 
                        color: #f0f0f0; 
                        margin: 10px 0 0 0; 
                        font-size: 16px;
                    }}
                    .content {{ 
                        background: white; 
                        padding: 40px 30px; 
                        border-radius: 0 0 10px 10px; 
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
                    }}
                    .reset-button {{ 
                        display: inline-block; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; 
                        padding: 15px 40px; 
                        text-decoration: none; 
                        border-radius: 8px; 
                        margin: 25px 0; 
                        font-size: 18px; 
                        font-weight: bold; 
                        text-align: center; 
                        transition: all 0.3s ease;
                    }}
                    .reset-button:hover {{ 
                        transform: translateY(-2px); 
                        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
                    }}
                    .security-info {{ 
                        background: #f8f9fa; 
                        padding: 20px; 
                        border-radius: 8px; 
                        margin: 25px 0; 
                        border-left: 4px solid #667eea;
                    }}
                    .security-info h3 {{ 
                        color: #333; 
                        margin-top: 0; 
                        font-size: 16px;
                    }}
                    .security-info ul {{ 
                        margin: 10px 0; 
                        padding-left: 20px; 
                    }}
                    .security-info li {{ 
                        margin: 5px 0; 
                        color: #666;
                    }}
                    .footer {{ 
                        text-align: center; 
                        margin-top: 30px; 
                        padding-top: 20px; 
                        border-top: 1px solid #eee; 
                        color: #666; 
                        font-size: 14px; 
                    }}
                    .link-fallback {{ 
                        word-break: break-all; 
                        color: #667eea; 
                        text-decoration: none; 
                        font-size: 14px; 
                        margin-top: 15px; 
                        display: block;
                    }}
                    .expires-note {{ 
                        color: #dc3545; 
                        font-weight: bold; 
                        margin-top: 20px; 
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔐 Password Reset</h1>
                        <p>One-click password reset for your Properwrite account</p>
                    </div>
                    
                    <div class="content">
                        <p>Hello {user_name or 'there'},</p>
                        
                        <p>We received a request to reset your password for your Properwrite account. Click the button below to create a new password:</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_link}" class="reset-button">Reset My Password</a>
                        </div>
                        
                        <div class="security-info">
                            <h3>🛡️ Security Information:</h3>
                            <ul>
                                <li>This link will expire in <strong>15 minutes</strong> for your security</li>
                                <li>The link can only be used once</li>
                                <li>If you didn't request this reset, you can safely ignore this email</li>
                                <li>Your account remains secure until you click the link above</li>
                            </ul>
                        </div>
                        
                        <p>If the button doesn't work, copy and paste this link into your browser:</p>
                        <a href="{reset_link}" class="link-fallback">{reset_link}</a>
                        
                        <p class="expires-note">⚠️ This link expires in 15 minutes and can only be used once.</p>
                        
                        <p>If you have any questions or need assistance, please contact our support team.</p>
                        
                        <p>Best regards,<br>
                        The Properwrite Team</p>
                    </div>
                    
                    <div class="footer">
                        <p>This email was sent from Properwrite (properwrite.com)</p>
                        <p>If you didn't request this password reset, please ignore this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            Password Reset Request - Properwrite
            
            Hello {user_name or 'there'},
            
            We received a request to reset your password for your Properwrite account.
            
            Click this link to reset your password:
            {reset_link}
            
            IMPORTANT SECURITY INFORMATION:
            - This link will expire in 15 minutes for your security
            - The link can only be used once
            - If you didn't request this reset, you can safely ignore this email
            - Your account remains secure until you click the link above
            
            If you have any questions or need assistance, please contact our support team.
            
            Best regards,
            The Properwrite Team
            
            ---
            This email was sent from Properwrite (properwrite.com)
            If you didn't request this password reset, please ignore this email.
            """
            
            # Send email using the email service
            success = self.email_service.send_email(
                to_email=user_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"Password reset email sent successfully to {user_email}")
                return True
            else:
                logger.error(f"Failed to send password reset email to {user_email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            return False
    
    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired password reset tokens
        Returns: number of tokens cleaned up
        """
        try:
            expired_tokens = self.db_session.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at < datetime.utcnow()
            ).all()
            
            count = len(expired_tokens)
            
            for token in expired_tokens:
                self.db_session.delete(token)
            
            self.db_session.commit()
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired password reset tokens")
                
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
            return 0