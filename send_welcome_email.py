#!/usr/bin/env python3
"""
Send welcome email to a specific user
"""

import sys
import os
import logging
from email_service import EmailService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_welcome_to_user(email_address):
    """Send welcome email to specific user"""
    try:
        # Initialize Flask app context
        from app_upgraded import app
        from billing_service import BillingService
        
        with app.app_context():
            # Initialize services
            email_service = EmailService()
            billing_service = BillingService()
            
            # Find user by email using billing service
            from models import User
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import create_engine
            
            # Create database session
            engine = create_engine(os.environ.get('DATABASE_URL'))
            Session = sessionmaker(bind=engine)
            session = Session()
            
            user = session.query(User).filter_by(email=email_address).first()
            
            if not user:
                logger.error(f"User not found with email: {email_address}")
                return False
                
            logger.info(f"Found user: {user.name} ({user.email})")
            
            # Send welcome email
            success = email_service.send_welcome_email(user.email, user.name)
            
            if success:
                logger.info(f"Welcome email sent successfully to {user.email}")
                return True
            else:
                logger.error(f"Failed to send welcome email to {user.email}")
                return False
            
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Send welcome email to specific user
    target_email = "Drrobinson37@gmail.com"
    result = send_welcome_to_user(target_email)
    
    if result:
        print(f"✅ Welcome email sent successfully to {target_email}")
    else:
        print(f"❌ Failed to send welcome email to {target_email}")