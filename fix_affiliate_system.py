#!/usr/bin/env python3
"""
Fix Affiliate Credit System Issues
Creates missing promo codes and synchronizes systems
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from affiliate_models import Base, PromoCode, PromoCodeType

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
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

Session = sessionmaker(bind=engine)

def create_missing_promo_codes():
    """Create missing promo codes from hardcoded system"""
    session = Session()
    
    # Define hardcoded codes that should exist in database
    hardcoded_codes = {
        'AFF001': {'type': PromoCodeType.CREDIT_PACK, 'credit_amount': 100, 'description': 'Affiliate 001 - 100 Credits'},
        'AFF002': {'type': PromoCodeType.CREDIT_PACK, 'credit_amount': 150, 'description': 'Affiliate 002 - 150 Credits'},
        'AFF003': {'type': PromoCodeType.CREDIT_PACK, 'credit_amount': 200, 'description': 'Affiliate 003 - 200 Credits'},
        'WELCOME50': {'type': PromoCodeType.CREDIT_PACK, 'credit_amount': 50, 'description': 'Welcome Pack - 50 Credits'},
        'STARTER100': {'type': PromoCodeType.CREDIT_PACK, 'credit_amount': 100, 'description': 'Starter Pack - 100 Credits'},
        'cg30': {'type': PromoCodeType.CREDIT_PACK, 'credit_amount': 30, 'description': 'Collective Genius - 30 Credits'},
        'F&F25': {'type': PromoCodeType.CREDIT_PACK, 'credit_amount': 25, 'description': 'Fix & Flip - 25 Credits'}
    }
    
    created_count = 0
    
    for code, details in hardcoded_codes.items():
        # Check if code already exists
        existing = session.query(PromoCode).filter_by(code=code).first()
        
        if not existing:
            promo_code = PromoCode(
                code=code,
                type=details['type'],
                credit_amount=details['credit_amount'],
                applies_to_plans=['all'],
                first_month_only=False,
                max_uses=1000,  # High limit
                uses_count=0,
                valid_until=datetime.utcnow() + timedelta(days=365),  # 1 year validity
                campaign_name=details['description'],
                is_active=True
            )
            
            session.add(promo_code)
            created_count += 1
            print(f"✅ Created promo code: {code} ({details['credit_amount']} credits)")
    
    session.commit()
    session.close()
    print(f"✅ Created {created_count} missing promo codes")

def update_existing_codes():
    """Update existing codes to match hardcoded system"""
    session = Session()
    
    # Fix known incorrect codes
    corrections = {
        'subto25': 25,
        'CG40': 40,
        'cg30': 30,
        'F&F25': 25
    }
    
    for code, correct_amount in corrections.items():
        promo_code = session.query(PromoCode).filter_by(code=code).first()
        if promo_code and promo_code.credit_amount != correct_amount:
            old_amount = promo_code.credit_amount
            promo_code.credit_amount = correct_amount
            print(f"✅ Updated {code}: {old_amount} → {correct_amount} credits")
    
    session.commit()
    session.close()

def main():
    """Fix all affiliate system issues"""
    print("🔧 Fixing affiliate credit system issues...")
    
    # Create missing codes
    create_missing_promo_codes()
    
    # Update existing codes
    update_existing_codes()
    
    print("✅ Affiliate system fixes completed!")

if __name__ == "__main__":
    main()