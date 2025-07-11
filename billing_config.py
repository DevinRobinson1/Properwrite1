"""
Billing Configuration
Updated subscription plans with new credit allocations
"""

SUBSCRIPTION_PLANS = {
    'starter': {
        'name': 'Starter',
        'price': 3900,  # $39/month
        'credits_per_month': 300,
        'seats': 1,
        'description': '300 credits per month, 1 user'
    },
    'pro': {
        'name': 'Pro',
        'price': 7900,  # $79/month
        'credits_per_month': 300,
        'seats': 1,
        'description': '300 credits per month, 1 user'
    },
    'team5': {
        'name': 'Team5',
        'price': 19900,  # $199/month
        'credits_per_month': 1000,
        'seats': 5,
        'description': '1,000 credits per month, 5 users'
    },
    'growth10': {
        'name': 'Growth10',
        'price': 39900,  # $399/month
        'credits_per_month': -1,  # Unlimited
        'seats': 10,
        'description': 'Unlimited credits, 10 users'
    }
}

CREDIT_PACKS = {
    '10-credits': {
        'name': '10 Credits',
        'credits': 10,
        'price': 1999,  # $19.99
        'description': '10 additional analysis credits'
    },
    '25-credits': {
        'name': '25 Credits',
        'credits': 25,
        'price': 4499,  # $44.99
        'description': '25 additional analysis credits'
    },
    '50-credits': {
        'name': '50 Credits',
        'credits': 50,
        'price': 7999,  # $79.99
        'description': '50 additional analysis credits'
    },
    '100-credits': {
        'name': '100 Credits',
        'credits': 100,
        'price': 14999,  # $149.99
        'description': '100 additional analysis credits'
    }
}

# Comping Credits - Admin feature
COMPING_CREDITS_ENABLED = True
COMPING_CREDITS_FEATURE_STATUS = "Coming Soon"

# Stripe Price IDs - These would be configured in Stripe Dashboard
STRIPE_PRICES = {
    'starter_m': 'price_starter_monthly',
    'pro_m': 'price_pro_monthly', 
    'team5_m': 'price_team5_monthly',
    'growth10_m': 'price_growth10_monthly',
    'credit_pack_100': 'price_credit_pack_100',
    'credit_pack_500': 'price_credit_pack_500',
    'credit_pack_1000': 'price_credit_pack_1000'
}

# Tier configuration for subscription enforcement
SUBSCRIPTION_TIERS = {
    'starter': {
        'max_seats': 1,
        'monthly_credits': 50,
        'price': 39
    },
    'pro': {
        'max_seats': 1, 
        'monthly_credits': 150,
        'price': 79
    },
    'team5': {
        'max_seats': 5,
        'monthly_credits': 450, 
        'price': 199
    },
    'growth10': {
        'max_seats': 10,
        'monthly_credits': 1000,
        'price': 399
    }
}

# Credit pack configuration
CREDIT_PACKS = {
    'pack-100': {'credits': 100, 'price': 15},
    'pack-500': {'credits': 500, 'price': 60}, 
    'pack-1000': {'credits': 1000, 'price': 99}
}