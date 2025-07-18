#!/usr/bin/env python3
"""
Create Stripe products and prices for properwrite.com subscription tiers
Run this script to set up all necessary Stripe products and pricing
"""

import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set your Stripe secret key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def create_products_and_prices():
    """Create all Stripe products and prices for properwrite.com"""
    
    print("Creating Stripe products and prices for properwrite.com...")
    
    # 1. Individual Plan - 100 credits/month
    try:
        individual_product = stripe.Product.create(
            name="Individual Plan",
            description="100 property analyses per month for individual investors",
            metadata={
                "credits_per_month": "100",
                "max_users": "1",
                "tier": "individual"
            }
        )
        print(f"✓ Created Individual Plan product: {individual_product.id}")
        
        # Individual Plan Price - $27/month
        individual_price = stripe.Price.create(
            product=individual_product.id,
            unit_amount=2700,  # $27.00 in cents
            currency="usd",
            recurring={"interval": "month"},
            metadata={
                "credits_per_month": "100",
                "max_users": "1"
            }
        )
        print(f"✓ Created Individual Plan price: {individual_price.id} - $27/month")
        
    except Exception as e:
        print(f"✗ Error creating Individual Plan: {e}")
    
    # 2. Pro Plan - 300 credits/month
    try:
        pro_product = stripe.Product.create(
            name="Pro Plan",
            description="300 property analyses per month for individual investors",
            metadata={
                "credits_per_month": "300",
                "max_users": "1",
                "tier": "pro"
            }
        )
        print(f"✓ Created Pro Plan product: {pro_product.id}")
        
        # Pro Plan Price - $79/month
        pro_price = stripe.Price.create(
            product=pro_product.id,
            unit_amount=7900,  # $79.00 in cents
            currency="usd",
            recurring={"interval": "month"},
            metadata={
                "credits_per_month": "300",
                "max_users": "1"
            }
        )
        print(f"✓ Created Pro Plan price: {pro_price.id} - $79/month")
        
    except Exception as e:
        print(f"✗ Error creating Pro Plan: {e}")
    
    # 2. Team5 Plan - 1,000 credits/month, 5 users
    try:
        team5_product = stripe.Product.create(
            name="Team5 Plan",
            description="1,000 property analyses per month for teams up to 5 users",
            metadata={
                "credits_per_month": "1000",
                "max_users": "5",
                "tier": "team5"
            }
        )
        print(f"✓ Created Team5 Plan product: {team5_product.id}")
        
        # Team5 Plan Price - $199/month
        team5_price = stripe.Price.create(
            product=team5_product.id,
            unit_amount=19900,  # $199.00 in cents
            currency="usd",
            recurring={"interval": "month"},
            metadata={
                "credits_per_month": "1000",
                "max_users": "5"
            }
        )
        print(f"✓ Created Team5 Plan price: {team5_price.id} - $199/month")
        
    except Exception as e:
        print(f"✗ Error creating Team5 Plan: {e}")
    
    # 3. Growth10 Plan - Unlimited credits, 10 users
    try:
        growth10_product = stripe.Product.create(
            name="Growth10 Plan",
            description="Unlimited property analyses for growing teams up to 10 users",
            metadata={
                "credits_per_month": "unlimited",
                "max_users": "10",
                "tier": "growth10"
            }
        )
        print(f"✓ Created Growth10 Plan product: {growth10_product.id}")
        
        # Growth10 Plan Price - $399/month
        growth10_price = stripe.Price.create(
            product=growth10_product.id,
            unit_amount=39900,  # $399.00 in cents
            currency="usd",
            recurring={"interval": "month"},
            metadata={
                "credits_per_month": "unlimited",
                "max_users": "10"
            }
        )
        print(f"✓ Created Growth10 Plan price: {growth10_price.id} - $399/month")
        
    except Exception as e:
        print(f"✗ Error creating Growth10 Plan: {e}")
    
    # 4. Credit Packs (One-time purchases)
    credit_packs = [
        {"name": "25 Credits", "credits": 25, "price": 1500, "lookup_key": "25-credits"},    # $15.00
        {"name": "50 Credits", "credits": 50, "price": 2500, "lookup_key": "50-credits"},    # $25.00
        {"name": "100 Credits", "credits": 100, "price": 4500, "lookup_key": "100-credits"},  # $45.00
        {"name": "250 Credits", "credits": 250, "price": 9900, "lookup_key": "250-credits"},  # $99.00
        {"name": "500 Credits", "credits": 500, "price": 17500, "lookup_key": "500-credits"}, # $175.00
        {"name": "1000 Credits", "credits": 1000, "price": 29900, "lookup_key": "1000-credits"} # $299.00
    ]
    
    for pack in credit_packs:
        try:
            credit_product = stripe.Product.create(
                name=pack["name"],
                description=f"One-time purchase of {pack['credits']} property analyses",
                metadata={
                    "credits": str(pack["credits"]),
                    "type": "credit_pack"
                }
            )
            print(f"✓ Created {pack['name']} product: {credit_product.id}")
            
            credit_price = stripe.Price.create(
                product=credit_product.id,
                unit_amount=pack["price"],
                currency="usd",
                lookup_key=pack["lookup_key"],
                metadata={
                    "credits": str(pack["credits"]),
                    "type": "credit_pack"
                }
            )
            print(f"✓ Created {pack['name']} price: {credit_price.id} - ${pack['price']/100:.2f} (lookup_key: {pack['lookup_key']})")
            
        except Exception as e:
            print(f"✗ Error creating {pack['name']}: {e}")
    
    print("\n" + "="*60)
    print("Stripe products and prices created successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Update your billing_config.py with the new price IDs")
    print("2. Test the checkout flow in your application")
    print("3. Set up webhook endpoints for subscription management")
    print("\nTo get price IDs for your config:")
    print("stripe prices list --limit 20")

def list_existing_products():
    """List existing Stripe products for reference"""
    print("\nExisting Stripe products:")
    try:
        products = stripe.Product.list(limit=20)
        for product in products:
            print(f"- {product.name} ({product.id})")
    except Exception as e:
        print(f"Error listing products: {e}")

if __name__ == "__main__":
    if not stripe.api_key:
        print("Error: STRIPE_SECRET_KEY environment variable not set")
        print("Please set your Stripe secret key in your environment variables")
        exit(1)
    
    print("properwrite.com - Stripe Product Setup")
    print("="*50)
    
    # List existing products first
    list_existing_products()
    
    print("\nCreating new products...")
    create_products_and_prices()