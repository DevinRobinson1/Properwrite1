"""
Offer Strategy Calculator
Real estate investment offer calculations for multiple acquisition strategies
"""

import logging

def calculate_loan_balance(principal, monthly_payment, annual_rate, months_paid):
    """
    Calculate remaining loan balance after specified months of payments
    """
    if annual_rate == 0:
        return principal - (monthly_payment * months_paid)
    
    monthly_rate = annual_rate / 12
    if monthly_payment == 0:
        return principal
    
    # Use simplified calculation for remaining balance
    total_interest_paid = 0
    current_balance = principal
    
    for month in range(months_paid):
        interest_payment = current_balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        current_balance -= principal_payment
        if current_balance <= 0:
            break
    
    return max(0, current_balance)

def calculate_mao_cash_offer(arv, repair_cost, appraisal_factors=0, wholesale_discount_pct=0.70):
    """
    Calculate Maximum Allowable Offer (MAO) for cash deals
    Based on your reference: ARV $200,000, Repairs $30,000
    Formula: ARV * wholesale_discount_pct - repair_cost - appraisal_factors
    """
    # Calculate "As-Is Value" = ARV - Estimated Repairs - Appraisal Factors
    as_is_value = arv - repair_cost - appraisal_factors
    
    # Recommended discount to sell fast on MLS (default $10,000 or 10% of as-is value)
    mls_discount = min(10000, as_is_value * 0.10)
    
    # MLS List Price
    mls_list_price = as_is_value - mls_discount
    
    # Wholesale offer (70% of ARV by default)
    wholesale_offer = arv * wholesale_discount_pct
    
    # Closing fees and out of pocket costs (based on your reference $18,400)
    closing_costs = 18400  # Fixed amount from reference
    
    # MAO calculation
    mao = wholesale_offer - closing_costs
    
    # Expected profit calculation
    expected_profit = arv - mao - repair_cost - closing_costs
    
    return {
        'offer_amount': max(0, mao),
        'arv': arv,
        'repair_cost': repair_cost,
        'appraisal_factors': appraisal_factors,
        'as_is_value': as_is_value,
        'mls_discount': mls_discount,
        'mls_list_price': mls_list_price,
        'wholesale_offer': wholesale_offer,
        'wholesale_discount_pct': wholesale_discount_pct * 100,
        'closing_costs': closing_costs,
        'expected_profit': max(0, expected_profit),
        'profit_margin': (expected_profit / arv * 100) if arv > 0 else 0,
        'strategy': 'Cash Offer (MAO)',
        'calculation_notes': f"ARV ${arv:,.0f} × {wholesale_discount_pct*100:.0f}% - Closing ${closing_costs:,.0f}",
        'fees_breakdown': {
            'wholesale_discount': arv - wholesale_offer,
            'closing_costs': closing_costs,
            'repair_cost': repair_cost,
            'appraisal_factors': appraisal_factors
        }
    }

def calculate_novation_offer(arv, repair_cost, existing_loan=0, monthly_payment=0, interest_rate=0.055, minimum_profit=25000):
    """
    Calculate Novation/Installment offer
    Based on reference: Take over existing loan, pay equity over time
    """
    # Calculate equity position after repairs
    equity_position = arv - existing_loan - repair_cost
    
    # Installment closing fees (from reference: $18,400)
    closing_costs = 18400
    
    # Minimum acceptable profit (reference shows $15,000-$25,000)
    required_profit = max(minimum_profit, arv * 0.10)  # 10% of ARV or $25k minimum
    
    # Calculate maximum equity we can pay
    max_equity_payment = equity_position - required_profit - closing_costs
    
    # Novation offer = existing loan + equity payment over time
    offer_amount = existing_loan + max(0, max_equity_payment)
    
    # Calculate installment terms for equity portion
    equity_payment = max(0, max_equity_payment)
    installment_term_months = 60  # 5 years typical
    
    if equity_payment > 0:
        monthly_installment = equity_payment / installment_term_months
    else:
        monthly_installment = 0
    
    # Total monthly payment (existing loan + installment)
    total_monthly_payment = monthly_payment + monthly_installment
    
    return {
        'offer_amount': max(existing_loan, offer_amount),
        'existing_loan': existing_loan,
        'existing_monthly_payment': monthly_payment,
        'existing_interest_rate': interest_rate * 100,
        'equity_position': equity_position,
        'equity_payment': equity_payment,
        'monthly_installment': monthly_installment,
        'total_monthly_payment': total_monthly_payment,
        'installment_term_months': installment_term_months,
        'installment_term_years': installment_term_months / 12,
        'repair_cost': repair_cost,
        'closing_costs': closing_costs,
        'required_profit': required_profit,
        'strategy': 'Novation/Installment',
        'calculation_notes': f"Takeover ${existing_loan:,.0f} loan + ${equity_payment:,.0f} equity over {installment_term_months/12:.0f} years",
        'takeover_terms': f"Monthly: ${total_monthly_payment:,.0f} (${monthly_payment:,.0f} loan + ${monthly_installment:,.0f} installment)",
        'fees_breakdown': {
            'existing_loan_takeover': existing_loan,
            'equity_installment': equity_payment,
            'closing_costs': closing_costs,
            'required_profit': required_profit
        }
    }

def calculate_subject_to_offer(arv, existing_loan, monthly_payment, interest_rate=0.045, repair_cost=0, years_remaining=25):
    """
    Calculate Subject-To acquisition terms
    Take over existing mortgage payments, acquire equity position immediately
    """
    # Immediate equity position
    equity_position = arv - existing_loan
    
    # Cash required upfront (repairs + minimal closing costs)
    cash_required = repair_cost + 3000  # Repairs + closing/transfer costs
    
    # Monthly rent estimate (1% rule or market-based)
    monthly_rent_estimate = arv * 0.01  # 1% of ARV rule
    
    # Monthly expenses (PITI + maintenance + vacancy)
    property_taxes = arv * 0.015 / 12  # 1.5% annually
    insurance = arv * 0.005 / 12  # 0.5% annually  
    maintenance_vacancy = monthly_rent_estimate * 0.15  # 15% for maintenance/vacancy
    
    total_monthly_expenses = monthly_payment + property_taxes + insurance + maintenance_vacancy
    
    # Monthly cash flow
    monthly_cash_flow = monthly_rent_estimate - total_monthly_expenses
    annual_cash_flow = monthly_cash_flow * 12
    
    # Calculate remaining principal balance over time
    remaining_balance_5yr = calculate_loan_balance(existing_loan, monthly_payment, interest_rate, 60)
    equity_buildup_5yr = existing_loan - remaining_balance_5yr
    
    # ROI calculations
    cash_on_cash_return = (annual_cash_flow / cash_required * 100) if cash_required > 0 else 0
    total_return_5yr = annual_cash_flow * 5 + equity_buildup_5yr + equity_position
    total_roi_5yr = (total_return_5yr / cash_required * 100) if cash_required > 0 else 0
    
    return {
        'offer_amount': 0,  # No cash to seller, just take over payments
        'cash_required': cash_required,
        'existing_loan': existing_loan,
        'monthly_payment': monthly_payment,
        'interest_rate': interest_rate * 100,
        'years_remaining': years_remaining,
        'immediate_equity': equity_position,
        'monthly_rent_estimate': monthly_rent_estimate,
        'monthly_expenses': total_monthly_expenses,
        'monthly_cash_flow': monthly_cash_flow,
        'annual_cash_flow': annual_cash_flow,
        'cash_on_cash_return': cash_on_cash_return,
        'remaining_balance_5yr': remaining_balance_5yr,
        'equity_buildup_5yr': equity_buildup_5yr,
        'total_return_5yr': total_return_5yr,
        'total_roi_5yr': total_roi_5yr,
        'strategy': 'Subject-To',
        'calculation_notes': f"Take over ${monthly_payment:,.0f}/mo payment, gain ${equity_position:,.0f} equity immediately",
        'takeover_terms': f"$0 to seller + take over ${monthly_payment:,.0f}/mo payments",
        'fees_breakdown': {
            'monthly_payment': monthly_payment,
            'property_taxes': property_taxes,
            'insurance': insurance,
            'maintenance_vacancy': maintenance_vacancy,
            'repair_cost': repair_cost,
            'closing_costs': 3000
        }
    }

def calculate_seller_finance_offer(arv, down_payment_pct=0.10, interest_rate=0.055, term_years=20, repair_cost=0):
    """
    Calculate Seller Finance offer terms
    Full ARV purchase with seller carrying the financing
    """
    # Full ARV offer (common in seller finance deals)
    offer_amount = arv
    down_payment = arv * down_payment_pct
    loan_amount = arv - down_payment
    term_months = term_years * 12
    
    # Calculate monthly payment using amortization formula
    monthly_rate = interest_rate / 12
    if monthly_rate > 0:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
    else:
        monthly_payment = loan_amount / term_months
    
    total_payments = monthly_payment * term_months + down_payment
    total_interest = total_payments - arv
    
    # Rental income estimate (1% rule)
    monthly_rent = arv * 0.01
    
    # Monthly expenses breakdown
    property_taxes = arv * 0.015 / 12  # 1.5% annually
    insurance = arv * 0.005 / 12  # 0.5% annually
    maintenance_vacancy = monthly_rent * 0.15  # 15% for maintenance/vacancy
    total_monthly_expenses = monthly_payment + property_taxes + insurance + maintenance_vacancy
    
    # Cash flow analysis
    monthly_cash_flow = monthly_rent - total_monthly_expenses
    annual_cash_flow = monthly_cash_flow * 12
    
    # ROI calculations
    total_cash_invested = down_payment + repair_cost + 3000  # Down + repairs + closing
    cash_on_cash_return = (annual_cash_flow / total_cash_invested * 100) if total_cash_invested > 0 else 0
    
    # Principal paydown over 5 years
    remaining_balance_5yr = calculate_loan_balance(loan_amount, monthly_payment, interest_rate, 60)
    principal_paydown_5yr = loan_amount - remaining_balance_5yr
    
    # Total return analysis
    total_return_5yr = (annual_cash_flow * 5) + principal_paydown_5yr
    total_roi_5yr = (total_return_5yr / total_cash_invested * 100) if total_cash_invested > 0 else 0
    
    return {
        'offer_amount': offer_amount,
        'down_payment': down_payment,
        'down_payment_pct': down_payment_pct * 100,
        'loan_amount': loan_amount,
        'monthly_payment': monthly_payment,
        'interest_rate': interest_rate * 100,
        'term_months': term_months,
        'term_years': term_years,
        'total_payments': total_payments,
        'total_interest': total_interest,
        'monthly_rent': monthly_rent,
        'monthly_expenses': total_monthly_expenses,
        'monthly_cash_flow': monthly_cash_flow,
        'annual_cash_flow': annual_cash_flow,
        'cash_on_cash_return': cash_on_cash_return,
        'total_cash_invested': total_cash_invested,
        'remaining_balance_5yr': remaining_balance_5yr,
        'principal_paydown_5yr': principal_paydown_5yr,
        'total_return_5yr': total_return_5yr,
        'total_roi_5yr': total_roi_5yr,
        'strategy': 'Seller Finance',
        'calculation_notes': f"${arv:,.0f} @ {interest_rate*100:.1f}% for {term_years} years",
        'financing_terms': f"${down_payment:,.0f} down + ${monthly_payment:,.0f}/mo × {term_years} years",
        'fees_breakdown': {
            'down_payment': down_payment,
            'monthly_payment': monthly_payment,
            'property_taxes': property_taxes,
            'insurance': insurance,
            'maintenance_vacancy': maintenance_vacancy,
            'total_interest': total_interest
        }
    }

def generate_offer_comparison(arv, repair_cost=0, existing_loan=0, monthly_payment=0, interest_rate=0.045, asking_price=0):
    """
    Generate all four offer strategies for comparison using your reference calculations
    """
    offers = {}
    
    # Cash Offer (MAO) - Based on your reference: ARV $200k, Repairs $30k
    offers['cash'] = calculate_mao_cash_offer(arv, repair_cost)
    
    # Novation Offer - Only if existing loan exists
    if existing_loan > 0:
        offers['novation'] = calculate_novation_offer(arv, repair_cost, existing_loan, monthly_payment, interest_rate)
    
    # Subject-To Offer - Only if existing loan and payment exist
    if existing_loan > 0 and monthly_payment > 0:
        offers['subject_to'] = calculate_subject_to_offer(arv, existing_loan, monthly_payment, interest_rate, repair_cost)
    
    # Seller Finance Offer - Always available
    offers['seller_finance'] = calculate_seller_finance_offer(arv, repair_cost=repair_cost)
    
    # Determine best strategy based on ROI and profit
    cash_profit = offers['cash']['expected_profit']
    sf_roi = offers['seller_finance'].get('total_roi_5yr', 0)
    sub2_roi = offers.get('subject_to', {}).get('total_roi_5yr', 0)
    
    best_strategy = 'cash'
    if sf_roi > 50 and sf_roi > cash_profit/1000:  # Convert profit to percentage-like comparison
        best_strategy = 'seller_finance'
    if sub2_roi > sf_roi and sub2_roi > 100:
        best_strategy = 'subject_to'
    
    return {
        'offers': offers,
        'best_strategy': best_strategy,
        'arv': arv,
        'repair_cost': repair_cost,
        'existing_loan': existing_loan,
        'monthly_payment': monthly_payment,
        'interest_rate': interest_rate,
        'summary': {
            'cash_offer': offers['cash']['offer_amount'],
            'seller_finance_offer': offers['seller_finance']['offer_amount'],
            'novation_offer': offers.get('novation', {}).get('offer_amount', 0),
            'subject_to_cash_required': offers.get('subject_to', {}).get('cash_required', 0)
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