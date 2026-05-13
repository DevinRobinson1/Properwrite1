"""
Email Service for properwrite.com
Handles sending emails from support@fundflowos.com
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
import requests

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Auto-detect SMTP server based on email domain
        smtp_username = os.environ.get('SMTP_USERNAME', '')
        # Google Workspace uses Gmail SMTP for custom domains
        if '@gmail.com' in smtp_username.lower() or smtp_username:
            default_smtp_server = 'smtp.gmail.com'
            default_smtp_port = '587'
        elif '@outlook.com' in smtp_username.lower() or '@hotmail.com' in smtp_username.lower():
            default_smtp_server = 'smtp-mail.outlook.com'
            default_smtp_port = '587'
        elif '@yahoo.com' in smtp_username.lower():
            default_smtp_server = 'smtp.mail.yahoo.com'
            default_smtp_port = '587'
        else:
            default_smtp_server = 'smtp.gmail.com'
            default_smtp_port = '587'
        
        self.smtp_server = os.environ.get('SMTP_SERVER', default_smtp_server)
        self.smtp_port = int(os.environ.get('SMTP_PORT', default_smtp_port))
        self.smtp_username = smtp_username
        # Handle Google App Password format (remove spaces if present)
        raw_password = os.environ.get('SMTP_PASSWORD', '')
        self.smtp_password = raw_password.replace(' ', '') if raw_password else ''
        self.from_email = os.environ.get('FROM_EMAIL', smtp_username)
        self.from_name = os.environ.get('FROM_NAME', 'Properwrite Team')
        
        # Alternative: SendGrid API
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        
        # Alternative: Mailgun API
        self.mailgun_api_key = os.environ.get('MAILGUN_API_KEY')
        self.mailgun_domain = os.environ.get('MAILGUN_DOMAIN')
        
    def send_email_smtp(self, to_email: str, subject: str, html_content: str, 
                       text_content: str = None, attachments: List = None) -> bool:
        """
        Send email using SMTP (works with Gmail, Outlook, etc.)
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text version
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {str(e)}")
            return False
    
    def send_email_sendgrid(self, to_email: str, subject: str, html_content: str, 
                           text_content: str = None) -> bool:
        """
        Send email using SendGrid API
        """
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            # Use a verified sender domain for SendGrid
            from_email_address = os.environ.get('FROM_EMAIL', 'support@fundflowos.com')
            from_name = os.environ.get('FROM_NAME', 'Properwrite Team')
            
            mail = Mail(
                from_email=from_email_address,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            if text_content:
                mail.plain_text_content = text_content
            
            response = sg.send(mail)
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully via SendGrid to {to_email}")
                return True
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {str(e)}")
            return False
    
    def send_email_mailgun(self, to_email: str, subject: str, html_content: str, 
                          text_content: str = None) -> bool:
        """
        Send email using Mailgun API
        """
        try:
            response = requests.post(
                f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages",
                auth=("api", self.mailgun_api_key),
                data={
                    "from": f"{self.from_name} <{self.from_email}>",
                    "to": to_email,
                    "subject": subject,
                    "text": text_content or html_content,
                    "html": html_content
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully via Mailgun to {to_email}")
                return True
            else:
                logger.error(f"Mailgun API error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email via Mailgun: {str(e)}")
            return False
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                  text_content: str = None, attachments: List = None) -> bool:
        """
        Send email using the best available method
        Priority: Gmail SMTP > SendGrid > Mailgun
        """
        # Try Gmail SMTP first (support@fundflowos.com)
        if self.smtp_username and self.smtp_password:
            if self.send_email_smtp(to_email, subject, html_content, text_content, attachments):
                return True
        
        # Try SendGrid second
        if self.sendgrid_api_key:
            if self.send_email_sendgrid(to_email, subject, html_content, text_content):
                return True
        
        # Try Mailgun third
        if self.mailgun_api_key and self.mailgun_domain:
            if self.send_email_mailgun(to_email, subject, html_content, text_content):
                return True
        
        logger.error("No email service configured")
        return False
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new users"""
        subject = "Welcome to Properwrite - Real Estate Investment Analysis"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center;">
                <h1 style="color: white; margin: 0;">Welcome to Properwrite!</h1>
                <p style="color: white; font-size: 18px; margin-top: 10px;">Professional Real Estate Investment Analysis</p>
            </div>
            
            <div style="padding: 40px;">
                <h2 style="color: #333;">Hello {user_name},</h2>
                
                <p style="color: #666; line-height: 1.6;">
                    Thank you for joining Properwrite! You now have access to our comprehensive real estate investment analysis platform.
                </p>
                
                <h3 style="color: #333;">What you can do:</h3>
                <ul style="color: #666; line-height: 1.8;">
                    <li>🏠 Analyze properties with external data integration</li>
                    <li>💰 Calculate multiple acquisition strategies</li>
                    <li>📊 Generate professional investment reports</li>
                    <li>🤝 Submit JV partnership opportunities</li>
                    <li>🎯 Access AI-powered market insights</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://properwrite.com/dashboard" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Access Your Dashboard
                    </a>
                </div>
                
                <p style="color: #666; line-height: 1.6;">
                    If you have any questions, feel free to reach out to our support team.
                </p>
                
                <p style="color: #666;">
                    Best regards,<br>
                    The Properwrite Team
                </p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #e9ecef;">
                <p style="color: #6c757d; font-size: 14px; margin: 0;">
                    © 2025 Properwrite. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Properwrite!
        
        Hello {user_name},
        
        Thank you for joining Properwrite! You now have access to our comprehensive real estate investment analysis platform.
        
        What you can do:
        • Analyze properties with external data integration
        • Calculate multiple acquisition strategies
        • Generate professional investment reports
        • Submit JV partnership opportunities
        • Access AI-powered market insights
        
        Access your dashboard: https://properwrite.com/dashboard
        
        If you have any questions, feel free to reach out to our support team.
        
        Best regards,
        The Properwrite Team
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_password_reset_email(self, user_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        subject = "Reset Your Properwrite Password"
        reset_url = f"https://properwrite.com/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #667eea; padding: 40px; text-align: center;">
                <h1 style="color: white; margin: 0;">Password Reset</h1>
            </div>
            
            <div style="padding: 40px;">
                <h2 style="color: #333;">Reset Your Password</h2>
                
                <p style="color: #666; line-height: 1.6;">
                    You requested to reset your password for your Properwrite account.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Reset Password
                    </a>
                </div>
                
                <p style="color: #666; line-height: 1.6;">
                    If you didn't request this reset, please ignore this email. This link will expire in 24 hours.
                </p>
                
                <p style="color: #666;">
                    Best regards,<br>
                    The Properwrite Team
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_credit_purchase_confirmation(self, user_email: str, credits_purchased: int, amount_paid: float) -> bool:
        """Send credit purchase confirmation email"""
        subject = "Credit Purchase Confirmation - Properwrite"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #28a745; padding: 40px; text-align: center;">
                <h1 style="color: white; margin: 0;">Purchase Confirmed!</h1>
            </div>
            
            <div style="padding: 40px;">
                <h2 style="color: #333;">Thank you for your purchase</h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">Purchase Details:</h3>
                    <p style="color: #666; margin: 5px 0;"><strong>Credits Purchased:</strong> {credits_purchased}</p>
                    <p style="color: #666; margin: 5px 0;"><strong>Amount Paid:</strong> ${amount_paid:.2f}</p>
                    <p style="color: #666; margin: 5px 0;"><strong>Purchase Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                
                <p style="color: #666; line-height: 1.6;">
                    Your credits have been added to your account and are ready to use for property analysis.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://properwrite.com/dashboard" 
                       style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        View Dashboard
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)

# Global email service instance
email_service = EmailService()