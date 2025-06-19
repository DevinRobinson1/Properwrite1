"""
Subject-To Offer Calculator for Creative Financing
Calculates monthly payment structure, entry fees, 5-year payoff outcomes, 
lease option exit profits, and equity structure
"""

import math

def calculate_subject_to_offer(arv, principal_balance, purchase_price, cash_to_seller=4000, 
                              annual_interest_rate=7.2, loan_term_months=360, annual_insurance=1200,
                              annual_taxes=750, monthly_pi=1800, monthly_escrow=300,
                              acquisition_costs=2000, closing_costs=2500, rehab=0, wholesale_fee=20000,
                              equity_amount_financed=0, equity_interest_rate=0.0, equity_payment=0,
                              equity_term_months=72, rent_income=1900, lease_option_income=2000,
                              lease_option_sale_price=299000, lease_option_fee_upfront=10000,
                              hoa_monthly=0, capital_cost_monthly=100, bedrooms=3, bathrooms=2, square_feet=1200):
    """
    Calculate comprehensive Subject-To offer analysis with creative financing options
    """
    
    # Basic calculations
    monthly_piti = monthly_pi + monthly_escrow
    entry_fees_total = acquisition_costs + closing_costs + rehab + wholesale_fee
    
    # Monthly cash flow calculations
    monthly_equity_payment = equity_payment if equity_amount_financed > 0 else 0
    cash_flow_rental = rent_income - monthly_piti - monthly_equity_payment - hoa_monthly - capital_cost_monthly
    cash_flow_lease_option = lease_option_income - monthly_piti - monthly_equity_payment - hoa_monthly - capital_cost_monthly
    
    # Loan balance calculations over 5 years
    monthly_rate = (annual_interest_rate / 100) / 12
    remaining_months = loan_term_months
    
    # Calculate loan balance after 5 years (60 months)
    balance_after_5_years = calculate_remaining_balance(
        principal_balance, monthly_rate, remaining_months, 60
    )
    
    # Principal paydown over 5 years
    principal_paydown_5_years = principal_balance - balance_after_5_years
    
    # 5-year performance calculations
    total_cash_flow_rental = cash_flow_rental * 60
    total_cash_flow_lease_option = cash_flow_lease_option * 60
    
    # Lease option exit calculations
    lease_option_profit = (lease_option_sale_price - purchase_price - entry_fees_total + 
                          principal_paydown_5_years + lease_option_fee_upfront)
    
    total_profit_lease_option = lease_option_profit + total_cash_flow_lease_option
    
    # Long-term hold calculations (assuming property appreciation)
    appreciation_5_years = arv * 0.03 * 5  # 3% annual appreciation
    hold_exit_value = arv + appreciation_5_years
    hold_profit = hold_exit_value - purchase_price - entry_fees_total + principal_paydown_5_years
    total_profit_hold = hold_profit + total_cash_flow_rental
    
    # Equity calculations if applicable
    total_equity_paid = monthly_equity_payment * min(60, equity_term_months) if equity_amount_financed > 0 else 0
    remaining_equity_balance = max(0, equity_amount_financed - total_equity_paid) if equity_amount_financed > 0 else 0
    
    # ROI calculations
    total_investment = cash_to_seller + entry_fees_total
    roi_lease_option = (total_profit_lease_option / total_investment * 100) if total_investment > 0 else 0
    roi_hold = (total_profit_hold / total_investment * 100) if total_investment > 0 else 0
    
    return {
        # Input values
        'arv': arv,
        'principal_balance': principal_balance,
        'purchase_price': purchase_price,
        'cash_to_seller': cash_to_seller,
        'annual_interest_rate': annual_interest_rate,
        'loan_term_months': loan_term_months,
        'annual_insurance': annual_insurance,
        'annual_taxes': annual_taxes,
        'monthly_pi': monthly_pi,
        'monthly_escrow': monthly_escrow,
        'monthly_piti': monthly_piti,
        
        # Entry fees
        'acquisition_costs': acquisition_costs,
        'closing_costs': closing_costs,
        'rehab': rehab,
        'wholesale_fee': wholesale_fee,
        'entry_fees_total': entry_fees_total,
        
        # Equity terms
        'equity_amount_financed': equity_amount_financed,
        'equity_interest_rate': equity_interest_rate,
        'equity_payment': equity_payment,
        'equity_term_months': equity_term_months,
        'monthly_equity_payment': monthly_equity_payment,
        
        # Income and cash flow
        'rent_income': rent_income,
        'lease_option_income': lease_option_income,
        'cash_flow_rental': cash_flow_rental,
        'cash_flow_lease_option': cash_flow_lease_option,
        
        # 5-year projections
        'balance_after_5_years': balance_after_5_years,
        'principal_paydown_5_years': principal_paydown_5_years,
        'total_cash_flow_rental': total_cash_flow_rental,
        'total_cash_flow_lease_option': total_cash_flow_lease_option,
        
        # Exit strategies
        'lease_option_sale_price': lease_option_sale_price,
        'lease_option_fee_upfront': lease_option_fee_upfront,
        'lease_option_profit': lease_option_profit,
        'total_profit_lease_option': total_profit_lease_option,
        
        'appreciation_5_years': appreciation_5_years,
        'hold_exit_value': hold_exit_value,
        'hold_profit': hold_profit,
        'total_profit_hold': total_profit_hold,
        
        # Equity tracking
        'total_equity_paid': total_equity_paid,
        'remaining_equity_balance': remaining_equity_balance,
        
        # Investment metrics
        'total_investment': total_investment,
        'roi_lease_option': roi_lease_option,
        'roi_hold': roi_hold,
        
        # Immediate equity position
        'immediate_equity': arv - principal_balance,
        
        # Strategy comparison
        'preferred_strategy': 'lease_option' if total_profit_lease_option > total_profit_hold else 'long_term_hold',
        'strategy_advantage': abs(total_profit_lease_option - total_profit_hold)
    }

def calculate_remaining_balance(principal, monthly_rate, total_months, months_paid):
    """
    Calculate remaining loan balance after specified months of payments
    """
    if monthly_rate == 0:
        return principal - (principal / total_months * months_paid)
    
    # Standard amortization formula
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**total_months) / ((1 + monthly_rate)**total_months - 1)
    
    # Calculate remaining balance
    remaining_balance = principal * ((1 + monthly_rate)**(total_months - months_paid) - 1) / ((1 + monthly_rate)**total_months - 1)
    
    return max(0, remaining_balance)

def calculate_monthly_payment(principal, annual_rate, term_months):
    """
    Calculate monthly payment for given loan terms
    """
    if annual_rate == 0:
        return principal / term_months
    
    monthly_rate = (annual_rate / 100) / 12
    return principal * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)

def validate_subject_to_deal(subject_to_data):
    """
    Validate Subject-To deal and provide warnings/recommendations
    """
    validations = []
    
    # Check loan-to-value ratio
    ltv = (subject_to_data['principal_balance'] / subject_to_data['arv']) * 100
    if ltv > 90:
        validations.append({
            'type': 'warning',
            'message': f'High LTV ({ltv:.1f}%) - limited equity cushion for market fluctuations'
        })
    elif ltv < 70:
        validations.append({
            'type': 'info',
            'message': f'Good LTV ({ltv:.1f}%) - solid equity position for appreciation'
        })
    
    # Check cash flow
    if subject_to_data['cash_flow_rental'] < -200:
        validations.append({
            'type': 'error',
            'message': f'Negative cash flow (${subject_to_data["cash_flow_rental"]:,.0f}/month) exceeds acceptable threshold'
        })
    elif subject_to_data['cash_flow_rental'] < 0:
        validations.append({
            'type': 'warning',
            'message': f'Negative cash flow (${subject_to_data["cash_flow_rental"]:,.0f}/month) - ensure adequate reserves'
        })
    
    # Check interest rate vs market
    if subject_to_data['annual_interest_rate'] > 8.0:
        validations.append({
            'type': 'warning',
            'message': f'High interest rate ({subject_to_data["annual_interest_rate"]:.1f}%) - consider refinance strategy'
        })
    
    # Check total investment vs returns
    if subject_to_data['roi_lease_option'] < 15:
        validations.append({
            'type': 'warning',
            'message': f'Low ROI ({subject_to_data["roi_lease_option"]:.1f}%) - consider alternative strategies'
        })
    
    # Check equity payment burden
    if subject_to_data['monthly_equity_payment'] > subject_to_data['rent_income'] * 0.3:
        validations.append({
            'type': 'warning',
            'message': 'Equity payment exceeds 30% of rent income - high payment burden'
        })
    
    return validations

def generate_subject_to_summary(subject_to_data):
    """
    Generate executive summary for Subject-To deal
    """
    strategy = "Lease Option" if subject_to_data['preferred_strategy'] == 'lease_option' else "Long-Term Hold"
    profit = subject_to_data['total_profit_lease_option'] if subject_to_data['preferred_strategy'] == 'lease_option' else subject_to_data['total_profit_hold']
    
    summary = f"Subject-To acquisition of ${subject_to_data['purchase_price']:,} property with ${subject_to_data['principal_balance']:,} existing loan. "
    summary += f"Recommended strategy: {strategy} with projected 5-year profit of ${profit:,}. "
    
    if subject_to_data['cash_flow_rental'] >= 0:
        summary += f"Positive cash flow of ${subject_to_data['cash_flow_rental']:,}/month supports holding strategy."
    else:
        summary += f"Negative cash flow of ${abs(subject_to_data['cash_flow_rental']):,}/month offset by appreciation and principal paydown."
    
    return summary

def get_subject_to_strategies():
    """
    Return available Subject-To exit strategies with descriptions
    """
    return {
        'lease_option': {
            'name': 'Lease Option Exit',
            'description': 'Tenant-buyer pays option fee and higher rent, exercises option to purchase',
            'timeline': '2-5 years',
            'benefits': ['Higher monthly income', 'Upfront option fee', 'Faster exit', 'Less maintenance responsibility'],
            'considerations': ['Tenant may not exercise option', 'Legal complexity', 'Market timing risk']
        },
        'long_term_hold': {
            'name': 'Long-Term Hold & Appreciation',
            'description': 'Hold property for appreciation and principal paydown, exit via sale or refinance',
            'timeline': '5+ years',
            'benefits': ['Maximum appreciation capture', 'Principal reduction', 'Tax benefits', 'Control over timing'],
            'considerations': ['Property management required', 'Market risk', 'Negative cash flow periods']
        },
        'refinance_exit': {
            'name': '6-12 Month Refinance',
            'description': 'Improve property and credit, refinance to remove original loan',
            'timeline': '6-12 months',
            'benefits': ['Quick exit strategy', 'Remove due-on-sale risk', 'Establish conventional financing'],
            'considerations': ['Credit requirements', 'Income documentation', 'Appraisal risk', 'Closing costs']
        }
    }

def calculate_refinance_scenario(subject_to_data, new_loan_amount, new_interest_rate, new_term_months, cash_out=0):
    """
    Calculate refinance exit scenario for Subject-To deal
    """
    new_monthly_payment = calculate_monthly_payment(new_loan_amount, new_interest_rate, new_term_months)
    
    # Calculate cash required/received at refinance
    existing_balance = subject_to_data['principal_balance']  # Assuming immediate refinance
    cash_flow_change = subject_to_data['monthly_piti'] - new_monthly_payment
    
    refinance_costs = new_loan_amount * 0.03  # Assume 3% refinance costs
    net_cash_at_close = new_loan_amount - existing_balance - refinance_costs + cash_out
    
    return {
        'new_loan_amount': new_loan_amount,
        'new_interest_rate': new_interest_rate,
        'new_monthly_payment': new_monthly_payment,
        'cash_flow_improvement': cash_flow_change,
        'refinance_costs': refinance_costs,
        'net_cash_at_close': net_cash_at_close,
        'break_even_months': abs(refinance_costs / cash_flow_change) if cash_flow_change != 0 else float('inf')
    }