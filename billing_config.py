"""
Billing Configuration
Simple configuration for subscription plans and credit packs
"""

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