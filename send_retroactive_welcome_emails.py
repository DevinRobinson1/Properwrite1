#!/usr/bin/env python3
"""
Send retroactive welcome emails to all existing users
"""

import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from email_service import EmailService
from billing_models import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_retroactive_welcome_emails():
    """Send welcome emails to all existing users"""
    
    # Database connection
    DATABASE_URL = os.environ.get("DATABASE_URL")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    )
    
    # Initialize email service
    email_service = EmailService()
    
    try:
        with Session(engine) as session:
            # Get all active users
            users = session.query(User).filter(User.is_active == True).all()
            
            logger.info(f"Found {len(users)} active users")
            
            sent_count = 0
            failed_count = 0
            
            for user in users:
                try:
                    # Send welcome email
                    user_name = user.name or user.email.split('@')[0]
                    success = email_service.send_welcome_email(user.email, user_name)
                    
                    if success:
                        sent_count += 1
                        logger.info(f"✓ Welcome email sent to {user.email}")
                    else:
                        failed_count += 1
                        logger.error(f"✗ Failed to send welcome email to {user.email}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"✗ Error sending welcome email to {user.email}: {str(e)}")
            
            logger.info(f"Email sending completed: {sent_count} sent, {failed_count} failed")
            
            # Also send emails to any JV deal submitters
            try:
                # Get JV deal submitters from partners table
                jv_result = session.execute(text("""
                    SELECT DISTINCT email, name 
                    FROM partners 
                    WHERE email IS NOT NULL AND email != ''
                """))
                
                jv_partners = jv_result.fetchall()
                logger.info(f"Found {len(jv_partners)} JV partners")
                
                for partner in jv_partners:
                    try:
                        partner_email = partner[0]
                        partner_name = partner[1] or partner_email.split('@')[0]
                        
                        # Send welcome email to JV partner
                        success = email_service.send_welcome_email(partner_email, partner_name)
                        
                        if success:
                            sent_count += 1
                            logger.info(f"✓ Welcome email sent to JV partner {partner_email}")
                        else:
                            failed_count += 1
                            logger.error(f"✗ Failed to send welcome email to JV partner {partner_email}")
                            
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"✗ Error sending welcome email to JV partner {partner_email}: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Error processing JV partners: {str(e)}")
            
            return {
                'total_sent': sent_count,
                'total_failed': failed_count,
                'success': True
            }
            
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {
            'total_sent': 0,
            'total_failed': 0,
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    result = send_retroactive_welcome_emails()
    print(f"Results: {result}")