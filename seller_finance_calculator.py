"""
Seller Finance Offer Calculator
Calculates monthly payments, total interest, and 5-10 year cash flow projections
with amortization or interest-only logic, balloon terms, and exit strategies
"""

import math

def calculate_seller_finance_offer(arv, seller_finance_purchase_price, down_payment=15000,
                                  interest_rate=6.5, amortization_term_months=360, 
                                  balloon_term_months=0, monthly_taxes=150, monthly_insurance=100,
                                  monthly_hoa=0, monthly_rent=2000, annual_maintenance_reserve=1200,
                                  closing_costs=5000, rehab_budget=30000, capital_cost=10000,
                                  is_interest_only=False):
    """
    Calculate comprehensive Seller Finance offer analysis with payment structures and exit strategies
    """
    
    # Basic loan calculations
    loan_amount = seller_finance_purchase_price - down_payment
    monthly_rate = (interest_rate / 100) / 12
    
    # Calculate monthly payment based on structure
    if is_interest_only:
        monthly_pi = loan_amount * monthly_rate
        total_interest_paid = monthly_pi * (balloon_term_months if balloon_term_months > 0 else amortization_term_months)
    else:
        # Amortized payment calculation
        if monthly_rate == 0:
            monthly_pi = loan_amount / amortization_term_months
        else:
            monthly_pi = (loan_amount * monthly_rate * (1 + monthly_rate)**amortization_term_months) / ((1 + monthly_rate)**amortization_term_months - 1)
        
        # Calculate total interest over full term
        total_payments = monthly_pi * amortization_term_months
        total_interest_paid = total_payments - loan_amount
    
    # Monthly expenses
    monthly_maintenance = annual_maintenance_reserve / 12
    monthly_expenses = monthly_taxes + monthly_insurance + monthly_hoa + monthly_maintenance
    monthly_total_outflow = monthly_pi + monthly_expenses
    
    # Cash flow analysis
    monthly_cash_flow = monthly_rent - monthly_total_outflow
    annual_cash_flow = monthly_cash_flow * 12
    
    # Total investment calculation
    total_investment = down_payment + closing_costs + rehab_budget + capital_cost
    
    # Balloon/Exit strategy calculations
    has_balloon = balloon_term_months > 0
    
    if has_balloon:
        # Calculate remaining balance at balloon
        if is_interest_only:
            remaining_balance_at_balloon = loan_amount  # No principal reduction with IO
        else:
            remaining_balance_at_balloon = calculate_remaining_balance(
                loan_amount, monthly_rate, amortization_term_months, balloon_term_months
            )
        
        # Exit strategy calculations
        projected_arv_at_balloon = arv * (1.03 ** (balloon_term_months / 12))  # 3% annual appreciation
        gross_proceeds = projected_arv_at_balloon
        net_proceeds = gross_proceeds - remaining_balance_at_balloon - (closing_costs * 0.5)  # Assume 50% of original closing costs
        
        # Cash flow accumulation to balloon
        total_cash_flow_to_balloon = monthly_cash_flow * balloon_term_months
        
        # Total return calculation
        total_return = net_proceeds + total_cash_flow_to_balloon - total_investment
    else:
        remaining_balance_at_balloon = 0
        projected_arv_at_balloon = arv
        net_proceeds = 0
        total_cash_flow_to_balloon = 0
        total_return = 0
    
    # 5-year and 10-year projections
    cash_flow_5_years = monthly_cash_flow * 60
    cash_flow_10_years = monthly_cash_flow * 120
    
    # Calculate loan balance after 5 and 10 years for non-balloon scenarios
    if not is_interest_only and not has_balloon:
        balance_after_5_years = calculate_remaining_balance(loan_amount, monthly_rate, amortization_term_months, 60)
        balance_after_10_years = calculate_remaining_balance(loan_amount, monthly_rate, amortization_term_months, 120)
        
        # Principal paydown
        principal_paydown_5_years = loan_amount - balance_after_5_years
        principal_paydown_10_years = loan_amount - balance_after_10_years
    else:
        balance_after_5_years = loan_amount if is_interest_only else remaining_balance_at_balloon
        balance_after_10_years = loan_amount if is_interest_only else 0
        principal_paydown_5_years = 0 if is_interest_only else loan_amount - balance_after_5_years
        principal_paydown_10_years = 0 if is_interest_only else loan_amount
    
    # ROI calculations
    if total_investment > 0:
        cash_on_cash_return = (annual_cash_flow / total_investment) * 100
        if has_balloon and balloon_term_months > 0:
            annualized_return = ((total_return / total_investment + 1) ** (12 / balloon_term_months) - 1) * 100
        else:
            annualized_return = cash_on_cash_return
    else:
        cash_on_cash_return = 0
        annualized_return = 0
    
    # Payment structure summary
    payment_structure = {
        'type': 'Interest Only' if is_interest_only else 'Amortized',
        'monthly_pi': monthly_pi,
        'balloon_months': balloon_term_months if has_balloon else 0,
        'amortization_months': amortization_term_months
    }
    
    return {
        # Input values
        'arv': arv,
        'seller_finance_purchase_price': seller_finance_purchase_price,
        'purchase_price': seller_finance_purchase_price,  # Template expects this field
        'down_payment': down_payment,
        'interest_rate': interest_rate,
        'amortization_term_months': amortization_term_months,
        'balloon_term_months': balloon_term_months,
        'is_interest_only': is_interest_only,
        
        # Operating data
        'monthly_taxes': monthly_taxes,
        'monthly_insurance': monthly_insurance,
        'monthly_hoa': monthly_hoa,
        'monthly_rent': monthly_rent,
        'annual_maintenance_reserve': annual_maintenance_reserve,
        'closing_costs': closing_costs,
        'rehab_budget': rehab_budget,
        'capital_cost': capital_cost,
        
        # Calculated values
        'loan_amount': loan_amount,
        'monthly_pi': monthly_pi,
        'monthly_maintenance': monthly_maintenance,
        'monthly_expenses': monthly_expenses,
        'monthly_total_outflow': monthly_total_outflow,
        'monthly_cash_flow': monthly_cash_flow,
        'annual_cash_flow': annual_cash_flow,
        'total_investment': total_investment,
        'total_interest_paid': total_interest_paid,
        
        # Balloon/Exit strategy
        'has_balloon': has_balloon,
        'remaining_balance_at_balloon': remaining_balance_at_balloon,
        'projected_arv_at_balloon': projected_arv_at_balloon,
        'net_proceeds': net_proceeds,
        'total_cash_flow_to_balloon': total_cash_flow_to_balloon,
        'total_return': total_return,
        
        # Long-term projections
        'cash_flow_5_years': cash_flow_5_years,
        'cash_flow_10_years': cash_flow_10_years,
        'balance_after_5_years': balance_after_5_years,
        'balance_after_10_years': balance_after_10_years,
        'principal_paydown_5_years': principal_paydown_5_years,
        'principal_paydown_10_years': principal_paydown_10_years,
        
        # ROI metrics
        'cash_on_cash_return': cash_on_cash_return,
        'annualized_return': annualized_return,
        
        # Payment structure
        'payment_structure': payment_structure,
        
        # Validation
        'is_cash_flow_positive': monthly_cash_flow >= 0,
        'debt_service_coverage_ratio': monthly_rent / monthly_pi if monthly_pi > 0 else 0
    }

def calculate_remaining_balance(principal, monthly_rate, total_months, months_paid):
    """
    Calculate remaining loan balance after specified months of payments
    """
    if monthly_rate == 0:
        return principal - (principal / total_months * months_paid)
    
    # Calculate remaining balance using amortization formula
    remaining_payments = total_months - months_paid
    if remaining_payments <= 0:
        return 0
    
    monthly_payment = (principal * monthly_rate * (1 + monthly_rate)**total_months) / ((1 + monthly_rate)**total_months - 1)
    remaining_balance = monthly_payment * ((1 + monthly_rate)**remaining_payments - 1) / monthly_rate
    
    return max(0, remaining_balance)

def generate_amortization_schedule(loan_amount, interest_rate, term_months, num_periods=12):
    """
    Generate amortization schedule for first num_periods
    """
    monthly_rate = (interest_rate / 100) / 12
    if monthly_rate == 0:
        monthly_payment = loan_amount / term_months
    else:
        monthly_payment = (loan_amount * monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
    
    schedule = []
    remaining_balance = loan_amount
    
    for month in range(1, min(num_periods + 1, term_months + 1)):
        interest_payment = remaining_balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        remaining_balance -= principal_payment
        
        schedule.append({
            'month': month,
            'payment': monthly_payment,
            'principal': principal_payment,
            'interest': interest_payment,
            'balance': max(0, remaining_balance)
        })
        
        if remaining_balance <= 0:
            break
    
    return schedule

def validate_seller_finance_deal(seller_finance_data):
    """
    Validate Seller Finance deal and provide warnings/recommendations
    """
    validations = []
    
    # Check loan-to-value ratio
    ltv = (seller_finance_data['loan_amount'] / seller_finance_data['arv']) * 100
    if ltv > 80:
        validations.append({
            'type': 'warning',
            'message': f'High LTV ({ltv:.1f}%) - seller taking significant risk'
        })
    elif ltv < 50:
        validations.append({
            'type': 'info',
            'message': f'Conservative LTV ({ltv:.1f}%) - good security for seller'
        })
    
    # Check debt service coverage ratio
    dscr = seller_finance_data['debt_service_coverage_ratio']
    if dscr < 1.2:
        validations.append({
            'type': 'error',
            'message': f'Low debt service coverage ({dscr:.2f}) - rental income barely covers payment'
        })
    elif dscr < 1.5:
        validations.append({
            'type': 'warning',
            'message': f'Marginal debt service coverage ({dscr:.2f}) - consider higher down payment'
        })
    
    # Check cash flow
    if seller_finance_data['monthly_cash_flow'] < 0:
        validations.append({
            'type': 'error',
            'message': f'Negative cash flow (${seller_finance_data["monthly_cash_flow"]:,.0f}/month) - deal not sustainable'
        })
    elif seller_finance_data['monthly_cash_flow'] < 200:
        validations.append({
            'type': 'warning',
            'message': f'Low cash flow (${seller_finance_data["monthly_cash_flow"]:,.0f}/month) - minimal buffer for expenses'
        })
    
    # Check interest rate reasonableness
    if seller_finance_data['interest_rate'] > 10:
        validations.append({
            'type': 'warning',
            'message': f'High interest rate ({seller_finance_data["interest_rate"]:.1f}%) - may limit buyer pool'
        })
    elif seller_finance_data['interest_rate'] < 4:
        validations.append({
            'type': 'info',
            'message': f'Below-market rate ({seller_finance_data["interest_rate"]:.1f}%) - attractive to buyer'
        })
    
    # Check balloon term viability
    if seller_finance_data['has_balloon'] and seller_finance_data['balloon_term_months'] < 36:
        validations.append({
            'type': 'warning',
            'message': f'Short balloon term ({seller_finance_data["balloon_term_months"]} months) - refinance risk'
        })
    
    return validations

def generate_seller_finance_term_sheet(seller_finance_data):
    """
    Generate plain language term sheet for Seller Finance deal
    """
    payment_type = "Interest-Only" if seller_finance_data['is_interest_only'] else "Amortized"
    balloon_text = f" with balloon payment due in {seller_finance_data['balloon_term_months']} months" if seller_finance_data['has_balloon'] else ""
    
    term_sheet = f"""
SELLER FINANCE TERM SHEET

Property: ${seller_finance_data['arv']:,} ARV
Purchase Price: ${seller_finance_data['seller_finance_purchase_price']:,}
Down Payment: ${seller_finance_data['down_payment']:,} ({(seller_finance_data['down_payment']/seller_finance_data['seller_finance_purchase_price']*100):.1f}%)
Loan Amount: ${seller_finance_data['loan_amount']:,}

FINANCING TERMS:
Interest Rate: {seller_finance_data['interest_rate']:.2f}% per annum
Payment Type: {payment_type}
Amortization: {seller_finance_data['amortization_term_months']} months ({seller_finance_data['amortization_term_months']//12} years)
{f"Balloon Due: {seller_finance_data['balloon_term_months']} months ({seller_finance_data['balloon_term_months']//12} years)" if seller_finance_data['has_balloon'] else ""}

MONTHLY PAYMENT BREAKDOWN:
Principal & Interest: ${seller_finance_data['monthly_pi']:,.0f}
Taxes: ${seller_finance_data['monthly_taxes']:,.0f}
Insurance: ${seller_finance_data['monthly_insurance']:,.0f}
HOA: ${seller_finance_data['monthly_hoa']:,.0f}
Maintenance Reserve: ${seller_finance_data['monthly_maintenance']:,.0f}
Total Monthly Outflow: ${seller_finance_data['monthly_total_outflow']:,.0f}

CASH FLOW ANALYSIS:
Monthly Rental Income: ${seller_finance_data['monthly_rent']:,.0f}
Monthly Cash Flow: ${seller_finance_data['monthly_cash_flow']:,.0f}
Annual Cash Flow: ${seller_finance_data['annual_cash_flow']:,.0f}
Cash-on-Cash Return: {seller_finance_data['cash_on_cash_return']:.1f}%

{"BALLOON PAYMENT ANALYSIS:" if seller_finance_data['has_balloon'] else ""}
{f"Balloon Balance: ${seller_finance_data['remaining_balance_at_balloon']:,.0f}" if seller_finance_data['has_balloon'] else ""}
{f"Projected Property Value: ${seller_finance_data['projected_arv_at_balloon']:,.0f}" if seller_finance_data['has_balloon'] else ""}
{f"Net Proceeds at Sale: ${seller_finance_data['net_proceeds']:,.0f}" if seller_finance_data['has_balloon'] else ""}
"""
    
    return term_sheet.strip()

def get_seller_finance_strategies():
    """
    Return different Seller Finance structures and their use cases
    """
    return {
        'amortized_long_term': {
            'name': 'Traditional Amortized',
            'description': '30-year amortization with steady principal reduction',
            'best_for': 'Stable long-term income, seller wants predictable payments',
            'pros': ['Steady principal paydown', 'Lower monthly payments', 'Traditional structure'],
            'cons': ['Lower early cash flow', 'Longer seller commitment', 'Interest rate risk']
        },
        'interest_only_balloon': {
            'name': 'Interest-Only with Balloon',
            'description': 'Interest-only payments with principal due at balloon',
            'best_for': 'Short-term hold, renovation projects, buyer expects appreciation',
            'pros': ['Lower monthly payments', 'Maximum cash flow', 'Flexible exit timing'],
            'cons': ['No principal reduction', 'Balloon risk', 'Higher total interest']
        },
        'short_term_balloon': {
            'name': 'Amortized with Short Balloon',
            'description': '30-year amortization with 3-7 year balloon',
            'best_for': 'Seller wants shorter commitment, buyer plans to refinance',
            'pros': ['Moderate payments', 'Some principal reduction', 'Shorter seller risk'],
            'cons': ['Refinance pressure', 'Rate risk at balloon', 'Complex structure']
        },
        'owner_carry_hybrid': {
            'name': 'Hybrid Owner Carry',
            'description': 'Combination of bank financing and seller carry-back',
            'best_for': 'Large transactions, seller wants partial liquidity',
            'pros': ['Seller gets some cash upfront', 'Reduced seller risk', 'Higher LTV possible'],
            'cons': ['Complex structure', 'Multiple lenders', 'Coordination required']
        }
    }