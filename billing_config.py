"""
Billing Configuration
Updated subscription plans with new credit allocations
"""

SUBSCRIPTION_PLANS = {
    'individual': {
        'name': 'Individual',
        'price': 2700,  # $27/month
        'credits_per_month': 100,
        'seats': 1,
        'description': '100 credits per month, 1 user'
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
    '25-credits': {
        'name': '25 Credits',
        'credits': 25,
        'price': 1500,  # $15
        'description': '25 additional analysis credits'
    },
    '50-credits': {
        'name': '50 Credits',
        'credits': 50,
        'price': 2500,  # $25
        'description': '50 additional analysis credits'
    },
    '100-credits': {
        'name': '100 Credits',
        'credits': 100,
        'price': 4500,  # $45
        'description': '100 additional analysis credits'
    },
    '250-credits': {
        'name': '250 Credits',
        'credits': 250,
        'price': 9900,  # $99
        'description': '250 additional analysis credits'
    },
    '500-credits': {
        'name': '500 Credits',
        'credits': 500,
        'price': 17500,  # $175
        'description': '500 additional analysis credits'
    },
    '1000-credits': {
        'name': '1000 Credits',
        'credits': 1000,
        'price': 29900,  # $299
        'description': '1000 additional analysis credits'
    }
}

# Comping Credits - Admin feature
COMPING_CREDITS_ENABLED = True
COMPING_CREDITS_FEATURE_STATUS = "Coming Soon"

# Stripe Price IDs - Live Production Prices
STRIPE_PRICES = {
    'individual_m': 'price_1Rk7HzPWMstJbjAaYgpfG3W2',  # $27/month, 100 credits ✅ LIVE
    'pro_m': 'price_1Rk7I0PWMstJbjAaHeEmxNKC',  # $79/month, 300 credits ✅ LIVE
    'team5_m': 'price_1Rk7I0PWMstJbjAaNkWF5566',  # $199/month, 1000 credits, 5 seats ✅ LIVE
    'growth10_m': 'price_1Rk7I1PWMstJbjAanDo5w6B4',  # $399/month, unlimited credits, 10 seats ✅ LIVE
    
    # Credit packs (one-time purchases) - Live Production Prices
    'credits_25': 'price_1Rk7I1PWMstJbjAa9oTuYUa8',   # $15 ✅ LIVE
    'credits_50': 'price_1Rk7I2PWMstJbjAajspO9IbC',   # $25 ✅ LIVE
    'credits_100': 'price_1Rk7I2PWMstJbjAaWdAl8pjB',  # $45 ✅ LIVE
    'credits_250': 'price_1Rk7I3PWMstJbjAa0hkfRdSu',  # $99 ✅ LIVE
    'credits_500': 'price_1Rk7I3PWMstJbjAamanEHqdc',  # $175 ✅ LIVE
    'credits_1000': 'price_1Rk7I4PWMstJbjAaY8UiKHvJ', # $299 ✅ LIVE
}

# Bitcoin Pricing Matrix (25% discount from USD prices)
BITCOIN_PRICES = {
    'individual_btc': 20.25,    # $27 - 25% = $20.25
    'pro_btc': 59.25,          # $79 - 25% = $59.25
    'team5_btc': 149.25,       # $199 - 25% = $149.25
    'growth10_btc': 299.25,    # $399 - 25% = $299.25
    
    # Bitcoin Credit Packs (25% discount)
    'credits_25_btc': 11.25,   # $15 - 25% = $11.25
    'credits_50_btc': 18.75,   # $25 - 25% = $18.75
    'credits_100_btc': 33.75,  # $45 - 25% = $33.75
    'credits_250_btc': 74.25,  # $99 - 25% = $74.25
    'credits_500_btc': 131.25, # $175 - 25% = $131.25
    'credits_1000_btc': 224.25 # $299 - 25% = $224.25
}

# Tier configuration for subscription enforcement
SUBSCRIPTION_TIERS = {
    'individual': {
        'max_seats': 1,
        'monthly_credits': 100,
        'price': 27
    },
    'pro': {
        'max_seats': 1, 
        'monthly_credits': 300,
        'price': 79
    },
    'team5': {
        'max_seats': 5,
        'monthly_credits': 1000, 
        'price': 199
    },
    'growth10': {
        'max_seats': 10,
        'monthly_credits': -1,  # Unlimited
        'price': 399
    }
}