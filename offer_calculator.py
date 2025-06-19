"""
Offer Strategy Calculator
Real estate investment offer calculations for multiple acquisition strategies
"""

import logging

def calculate_mao_cash_offer(arv, repair_cost, profit_margin=0.20):
    """
    Calculate Maximum Allowable Offer (MAO) for cash deals
    Standard formula: ARV * (1 - profit_margin) - repair_cost - closing_costs
    """
    closing_costs = arv * 0.03  # 3% of ARV for closing costs
    holding_costs = repair_cost * 0.15  # 15% of repair cost for holding
    
    mao = arv * (1 - profit_margin) - repair_cost - closing_costs - holding_costs
    
    return {
        'offer_amount': max(0, mao),
        'arv': arv,
        'repair_cost': repair_cost,
        'closing_costs': closing_costs,
        'holding_costs': holding_costs,
        'profit_margin': profit_margin * 100,
        'expected_profit': arv - mao - repair_cost - closing_costs - holding_costs,
        'strategy': 'Cash Offer',
        'fees_breakdown': {
            'closing_costs': closing_costs,
            'holding_costs': holding_costs,
            'repair_cost': repair_cost
        }
    }

def calculate_novation_offer(arv, repair_cost, existing_loan=0, profit_margin=0.15):
    """
    Calculate Novation/Installment offer
    Take over existing loan and pay difference over time
    """
    equity_position = arv - existing_loan - repair_cost
    closing_costs = arv * 0.02  # Lower closing costs for novation
    
    # Novation typically offers 85-90% of equity position
    offer_amount = existing_loan + (equity_position * (1 - profit_margin))
    
    return {
        'offer_amount': max(existing_loan, offer_amount),
        'existing_loan': existing_loan,
        'equity_position': equity_position,
        'repair_cost': repair_cost,
        'closing_costs': closing_costs,
        'profit_margin': profit_margin * 100,
        'strategy': 'Novation Offer',
        'takeover_terms': f"Take over ${existing_loan:,.0f} loan + ${offer_amount - existing_loan:,.0f} equity",
        'fees_breakdown': {
            'existing_loan_takeover': existing_loan,
            'equity_payment': offer_amount - existing_loan,
            'closing_costs': closing_costs
        }
    }

def calculate_subject_to_offer(arv, existing_loan, monthly_payment, repair_cost=0):
    """
    Calculate Subject-To acquisition terms
    Take over existing mortgage payments, acquire equity position
    """
    equity_position = arv - existing_loan
    monthly_rent_estimate = arv * 0.008  # 0.8% of ARV monthly rent rule
    
    # Calculate monthly cash flow
    monthly_expenses = monthly_payment * 1.3  # Include taxes, insurance, maintenance
    monthly_cash_flow = monthly_rent_estimate - monthly_expenses
    
    # Subject-To typically requires minimal cash down
    cash_required = repair_cost + 2000  # Repair cost + buffer
    
    return {
        'offer_amount': existing_loan,
        'cash_required': cash_required,
        'existing_loan': existing_loan,
        'monthly_payment': monthly_payment,
        'equity_position': equity_position,
        'monthly_rent_estimate': monthly_rent_estimate,
        'monthly_cash_flow': monthly_cash_flow,
        'annual_cash_flow': monthly_cash_flow * 12,
        'strategy': 'Subject-To',
        'takeover_terms': f"Takeover ${existing_loan:,.0f} loan + ${equity_position:,.0f} equity",
        'cash_on_cash_return': (monthly_cash_flow * 12 / cash_required * 100) if cash_required > 0 else 0,
        'fees_breakdown': {
            'loan_takeover': existing_loan,
            'repair_cost': repair_cost,
            'closing_buffer': 2000
        }
    }

def calculate_seller_finance_offer(arv, down_payment_pct=0.10, interest_rate=0.055, term_months=240):
    """
    Calculate Seller Finance offer terms
    Standard seller financing with monthly payments
    """
    down_payment = arv * down_payment_pct
    loan_amount = arv - down_payment
    
    # Calculate monthly payment using amortization formula
    monthly_rate = interest_rate / 12
    if monthly_rate > 0:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
    else:
        monthly_payment = loan_amount / term_months
    
    total_payments = monthly_payment * term_months
    total_interest = total_payments - loan_amount
    
    # Estimate rental income and cash flow
    monthly_rent = arv * 0.008
    monthly_expenses = arv * 0.004  # 0.4% of value for expenses
    monthly_cash_flow = monthly_rent - monthly_payment - monthly_expenses
    
    return {
        'offer_amount': arv,
        'down_payment': down_payment,
        'loan_amount': loan_amount,
        'monthly_payment': monthly_payment,
        'interest_rate': interest_rate * 100,
        'term_months': term_months,
        'term_years': term_months / 12,
        'total_payments': total_payments,
        'total_interest': total_interest,
        'monthly_rent': monthly_rent,
        'monthly_cash_flow': monthly_cash_flow,
        'annual_cash_flow': monthly_cash_flow * 12,
        'strategy': 'Seller Finance',
        'financing_terms': f"${arv:,.0f} w/ ${down_payment:,.0f} down @ {interest_rate*100:.1f}% for {term_months} months",
        'fees_breakdown': {
            'down_payment': down_payment,
            'monthly_payment': monthly_payment,
            'total_interest': total_interest
        }
    }

def generate_offer_comparison(arv, repair_cost=0, existing_loan=0, monthly_payment=0, asking_price=0):
    """
    Generate all four offer strategies for comparison
    """
    offers = {}
    
    # Cash Offer (MAO)
    offers['cash'] = calculate_mao_cash_offer(arv, repair_cost)
    
    # Novation Offer
    if existing_loan > 0:
        offers['novation'] = calculate_novation_offer(arv, repair_cost, existing_loan)
    
    # Subject-To Offer
    if existing_loan > 0 and monthly_payment > 0:
        offers['subject_to'] = calculate_subject_to_offer(arv, existing_loan, monthly_payment, repair_cost)
    
    # Seller Finance Offer
    offers['seller_finance'] = calculate_seller_finance_offer(arv)
    
    # Determine best strategy
    cash_profit = offers['cash']['expected_profit']
    sf_cash_flow = offers['seller_finance']['annual_cash_flow']
    
    best_strategy = 'cash' if cash_profit > sf_cash_flow else 'seller_finance'
    
    return {
        'offers': offers,
        'best_strategy': best_strategy,
        'arv': arv,
        'repair_cost': repair_cost,
        'existing_loan': existing_loan,
        'summary': {
            'cash_offer': offers['cash']['offer_amount'],
            'seller_finance_offer': offers['seller_finance']['offer_amount'],
            'novation_offer': offers.get('novation', {}).get('offer_amount', 0),
            'subject_to_takeover': offers.get('subject_to', {}).get('offer_amount', 0)
        }
    }

def get_strategy_recommendation(offers):
    """
    Provide strategy recommendations based on calculations
    """
    recommendations = []
    
    cash_offer = offers.get('cash', {})
    sf_offer = offers.get('seller_finance', {})
    sub2_offer = offers.get('subject_to', {})
    
    if cash_offer.get('expected_profit', 0) > 30000:
        recommendations.append({
            'strategy': 'Cash Offer',
            'status': 'Most Profitable',
            'icon': '✅',
            'reason': f"High profit margin: ${cash_offer.get('expected_profit', 0):,.0f}"
        })
    
    if sf_offer.get('monthly_cash_flow', 0) > 500:
        recommendations.append({
            'strategy': 'Seller Finance',
            'status': 'Strong Cash Flow',
            'icon': '💰',
            'reason': f"Monthly cash flow: ${sf_offer.get('monthly_cash_flow', 0):,.0f}"
        })
    
    if sub2_offer.get('cash_on_cash_return', 0) > 20:
        recommendations.append({
            'strategy': 'Subject-To',
            'status': 'High ROI',
            'icon': '🚀',
            'reason': f"Cash-on-cash return: {sub2_offer.get('cash_on_cash_return', 0):.1f}%"
        })
    
    return recommendations