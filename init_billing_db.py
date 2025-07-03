"""
Initialize billing database tables
Creates all necessary tables for subscription and team management
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from billing_models import Base, TIER_CONFIG, CREDIT_PACKS

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def init_billing_database():
    """Initialize all billing-related database tables"""
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        
        print("✓ Created billing database tables:")
        print("  - teams")
        print("  - users") 
        print("  - credit_logs")
        print("  - team_invites")
        print()
        print("✓ Tier configuration loaded:")
        for tier, config in TIER_CONFIG.items():
            print(f"  - {tier}: {config['seats_max']} seats, {config['monthly_credits']} credits, ${config['price_monthly']}/mo")
        print()
        print("✓ Credit packs configured:")
        for pack, config in CREDIT_PACKS.items():
            print(f"  - {pack}: {config['credits']} credits, ${config['price']}")
        print()
        print("🚀 Billing system ready!")
        
    except Exception as e:
        print(f"❌ Error initializing billing database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    init_billing_database()