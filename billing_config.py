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

# Stripe Price IDs - These are configured in Stripe Dashboard
STRIPE_PRICES = {
    'pro_m': 'price_1RjhMpPWMstJbjAav2Tyy5aR',  # $79/month, 300 credits
    'team5_m': 'price_1RjhMqPWMstJbjAasyrGqEoB',  # $199/month, 1000 credits, 5 seats
    'growth10_m': 'price_1RjhMqPWMstJbjAaB7bd7VbK',  # $399/month, unlimited credits, 10 seats
    
    # Credit packs (one-time purchases)
    'credits_25': 'price_1RjhMrPWMstJbjAaBHIImsW3',   # $15
    'credits_50': 'price_1RjhMrPWMstJbjAaKrBVHVTS',   # $25
    'credits_100': 'price_1RjhMsPWMstJbjAaw7tHWOqX',  # $45
    'credits_250': 'price_1RjhMsPWMstJbjAaBMSOvN81',  # $99
    'credits_500': 'price_1RjhMtPWMstJbjAak8gUKHJ0',  # $175
    'credits_1000': 'price_1RjhMtPWMstJbjAaiNNiZ50k', # $299
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