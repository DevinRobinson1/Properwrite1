#!/usr/bin/env python3
"""
Initialize Affiliate Management Database Tables
Creates all necessary tables for the affiliate management system
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from affiliate_models import Base, AffiliateStatus, PromoCodeType, PayoutStatus
from datetime import datetime, timedelta

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

def create_affiliate_tables():
    """Create all affiliate management tables"""
    print("Creating affiliate management tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        print("✓ All affiliate tables created successfully")
        
        # Create session for test data
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Add sample data for testing
        create_sample_data(session)
        
        session.close()
        print("✓ Sample data added successfully")
        
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        sys.exit(1)

def create_sample_data(session):
    """Create sample affiliate data for testing"""
    from affiliate_models import Affiliate, PromoCode, AffiliateReferral, PromoCodeRedemption
    
    # Check if sample data already exists
    existing_affiliate = session.query(Affiliate).first()
    if existing_affiliate:
        print("Sample data already exists, skipping...")
        return
    
    print("Creating sample affiliate data...")
    
    # Create sample affiliates
    sample_affiliates = [
        {
            'name': 'John Martinez',
            'email': 'john@realestatecoach.com',
            'company': 'Real Estate Coach LLC',
            'website': 'https://realestatecoach.com',
            'commission_rate': 0.30,
            'tier': 'elite',
            'status': AffiliateStatus.ACTIVE,
            'approved_at': datetime.utcnow(),
            'payout_method': 'paypal',
            'payout_details': {'paypal_email': 'john@realestatecoach.com'},
            'tags': ['youtube', 'coaching', 'educator'],
            'notes': 'Top-performing affiliate with strong YouTube presence'
        },
        {
            'name': 'Sarah Johnson',
            'email': 'sarah@flippernetwork.com',
            'company': 'Flipper Network',
            'website': 'https://flippernetwork.com',
            'commission_rate': 0.25,
            'tier': 'standard',
            'status': AffiliateStatus.ACTIVE,
            'approved_at': datetime.utcnow(),
            'payout_method': 'stripe_connect',
            'payout_details': {'stripe_account_id': 'acct_test123'},
            'tags': ['instagram', 'flipping', 'content_creator'],
            'notes': 'Strong Instagram following, focuses on house flipping'
        },
        {
            'name': 'Mike Thompson',
            'email': 'mike@wholesaleacademy.com',
            'company': 'Wholesale Academy',
            'website': 'https://wholesaleacademy.com',
            'commission_rate': 0.35,
            'tier': 'premium',
            'status': AffiliateStatus.PENDING,
            'payout_method': 'bitcoin',
            'payout_details': {'bitcoin_address': 'bc1qtest123'},
            'tags': ['education', 'wholesale', 'masterclass'],
            'notes': 'Pending approval - runs wholesale education programs'
        }
    ]
    
    affiliates = []
    for affiliate_data in sample_affiliates:
        affiliate = Affiliate(**affiliate_data)
        session.add(affiliate)
        affiliates.append(affiliate)
    
    session.flush()  # Get IDs
    
    # Create sample promo codes
    sample_promo_codes = [
        {
            'code': 'FLIP30',
            'type': PromoCodeType.PERCENTAGE_DISCOUNT,
            'affiliate_id': affiliates[0].id,
            'discount_percentage': 30.0,
            'applies_to_plans': ['individual', 'pro'],
            'first_month_only': True,
            'max_uses': 100,
            'uses_count': 23,
            'valid_until': datetime.utcnow() + timedelta(days=30),
            'campaign_name': 'YouTube Launch Campaign',
            'tracking_tags': ['youtube', 'launch', 'discount'],
            'total_redemptions': 23,
            'total_revenue': 1840.0,
            'conversion_rate': 12.5
        },
        {
            'code': 'BONUS100',
            'type': PromoCodeType.CREDIT_PACK,
            'affiliate_id': affiliates[1].id,
            'credit_amount': 100,
            'applies_to_plans': ['all'],
            'first_month_only': False,
            'max_uses': 50,
            'uses_count': 31,
            'valid_until': datetime.utcnow() + timedelta(days=60),
            'campaign_name': 'Instagram Bonus Credits',
            'tracking_tags': ['instagram', 'bonus', 'credits'],
            'total_redemptions': 31,
            'total_revenue': 2480.0,
            'conversion_rate': 18.2
        },
        {
            'code': 'TEAM5FREE',
            'type': PromoCodeType.TEAM_BONUS,
            'affiliate_id': affiliates[0].id,
            'bonus_seats': 5,
            'applies_to_plans': ['team5', 'growth10'],
            'first_month_only': False,
            'max_uses': 20,
            'uses_count': 7,
            'valid_until': datetime.utcnow() + timedelta(days=90),
            'campaign_name': 'Team Expansion Offer',
            'tracking_tags': ['team', 'expansion', 'bonus'],
            'total_redemptions': 7,
            'total_revenue': 1393.0,
            'conversion_rate': 35.0
        }
    ]
    
    promo_codes = []
    for promo_data in sample_promo_codes:
        promo_code = PromoCode(**promo_data)
        session.add(promo_code)
        promo_codes.append(promo_code)
    
    session.flush()
    
    # Update affiliate stats with sample data
    affiliates[0].total_referrals = 45
    affiliates[0].active_referrals = 38
    affiliates[0].total_revenue_generated = 8640.0
    affiliates[0].total_commissions_earned = 2592.0
    affiliates[0].total_commissions_paid = 1200.0
    
    affiliates[1].total_referrals = 32
    affiliates[1].active_referrals = 28
    affiliates[1].total_revenue_generated = 6240.0
    affiliates[1].total_commissions_earned = 1560.0
    affiliates[1].total_commissions_paid = 800.0
    
    session.commit()
    print("✓ Sample affiliates created")
    print("✓ Sample promo codes created")
    print("✓ Sample metrics populated")

if __name__ == "__main__":
    print("Initializing Affiliate Management Database...")
    create_affiliate_tables()
    print("✓ Database initialization complete!")