"""
JV Auto-Underwrite Logic
Handles automatic deal evaluation for joint venture submissions
"""

def auto_underwrite_deal(deal_data):
    """
    Auto-underwrite logic for JV deals
    Returns: { status: "auto-approved" | "auto-denied", mao: float, reasons: list }
    """
    arv = float(deal_data.get('arv', 0))
    purchase_price = float(deal_data.get('purchase_price', 0)) if deal_data.get('purchase_price') else None
    seller_asking_price = float(deal_data.get('seller_asking_price', 0))
    deal_type = deal_data.get('deal_type', '')
    rehab_cost = float(deal_data.get('rehab_cost', 0)) if deal_data.get('rehab_needed') == 'yes' else 0
    
    reasons = []
    mao = 0
    
    if deal_type == 'wholesale':
        # Wholesale: mao = arv*0.70 - rehabCost
        mao = arv * 0.70 - rehab_cost
        
        if purchase_price is None:
            return {
                'status': 'auto-denied',
                'mao': mao,
                'reasons': ['Purchase price is required for wholesale deals']
            }
        
        if purchase_price <= mao:
            return {
                'status': 'auto-approved',
                'mao': mao,
                'reasons': [f'Purchase price ${purchase_price:,.0f} is within MAO of ${mao:,.0f}']
            }
        else:
            excess = purchase_price - mao
            reasons.append(f'Purchase price exceeds MAO by ${excess:,.0f}')
            return {
                'status': 'auto-denied',
                'mao': mao,
                'reasons': reasons
            }
    
    elif deal_type == 'creative_finance':
        # Creative Finance: Check minimum cash flow
        min_cash_flow = 200  # $200/month minimum
        est_rent = (arv * 0.01) / 12  # 1% rule monthly rent
        
        # For creative finance, we estimate PITI based on purchase price or asking price
        estimated_purchase = purchase_price if purchase_price else seller_asking_price
        # Estimate PITI as roughly 0.8% of property value monthly (conservative)
        monthly_piti = estimated_purchase * 0.008
        
        projected_cash_flow = est_rent - monthly_piti
        
        if projected_cash_flow >= min_cash_flow:
            return {
                'status': 'auto-approved',
                'mao': 0,  # MAO not applicable for creative finance
                'reasons': [f'Projected cash flow ${projected_cash_flow:,.0f}/month meets minimum ${min_cash_flow}/month']
            }
        else:
            shortfall = min_cash_flow - projected_cash_flow
            reasons.append(f'Projected cash flow ${projected_cash_flow:,.0f}/month falls short by ${shortfall:,.0f}/month')
            return {
                'status': 'auto-denied',
                'mao': 0,
                'reasons': reasons
            }
    
    elif deal_type == 'mls_help':
        # MLS Help: Approve if arv - rehabCost >= 90% of askingPrice
        adjusted_arv = arv - rehab_cost
        threshold = seller_asking_price * 0.90
        
        if adjusted_arv >= threshold:
            return {
                'status': 'auto-approved',
                'mao': 0,  # MAO not applicable for MLS help
                'reasons': [f'Adjusted ARV ${adjusted_arv:,.0f} exceeds 90% of asking price ${threshold:,.0f}']
            }
        else:
            shortfall = threshold - adjusted_arv
            reasons.append(f'Adjusted ARV falls short of 90% asking price threshold by ${shortfall:,.0f}')
            return {
                'status': 'auto-denied',
                'mao': 0,
                'reasons': reasons
            }
    
    else:
        return {
            'status': 'auto-denied',
            'mao': 0,
            'reasons': ['Invalid deal type specified']
        }