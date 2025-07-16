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

def auto_underwrite_deal_with_mao(deal_data, mao_analysis):
    """
    Enhanced auto-underwrite with MAO analysis and approval logic
    """
    import logging
    
    try:
        # Use provided MAO analysis or calculate fresh
        if mao_analysis:
            asking_price = mao_analysis.get('askingPrice', 0)
            arv = mao_analysis.get('arv', 0)
            rehab_cost = mao_analysis.get('rehabCost', 0)
            wholesale_profit = mao_analysis.get('wholesaleProfit', 0)
            novation_profit = mao_analysis.get('novationProfit', 0)
            recommendations = mao_analysis.get('recommendations', [])
            approval_status = mao_analysis.get('approvalStatus', 'pending')
            approval_reason = mao_analysis.get('approvalReason', '')
        else:
            # Calculate fresh MAO analysis
            asking_price = float(deal_data.get('seller_asking_price', 0))
            arv = float(deal_data.get('arv', 0))
            rehab_cost = float(deal_data.get('rehab_cost', 0))
            
            # Standard wholesale MAO calculation
            wholesale_mao = arv * 0.70 - rehab_cost - 15000  # Assignment fee
            novation_mao = arv * 0.85 - rehab_cost - 25000  # Closing costs
            
            wholesale_profit = wholesale_mao - asking_price
            novation_profit = novation_mao - asking_price
            
            recommendations = []
            if wholesale_profit > 0:
                recommendations.append({
                    'strategy': 'Wholesale',
                    'profit': wholesale_profit,
                    'confidence': 'High' if wholesale_profit > 10000 else 'Medium'
                })
            if novation_profit > 0 and novation_profit > wholesale_profit:
                recommendations.append({
                    'strategy': 'Novation',
                    'profit': novation_profit,
                    'confidence': 'High' if novation_profit > 15000 else 'Medium'
                })
            
            # Approval logic
            max_profit = max(wholesale_profit, novation_profit) if wholesale_profit > 0 or novation_profit > 0 else 0
            if max_profit > 20000:
                approval_status = 'auto_approved'
                approval_reason = 'High profit potential - automatically approved'
            elif max_profit > 10000:
                approval_status = 'likely_approved'
                approval_reason = 'Good profit potential - likely to be approved'
            elif max_profit > 0:
                approval_status = 'needs_review'
                approval_reason = 'Lower profit margins - requires careful review'
            else:
                approval_status = 'needs_review'
                approval_reason = 'No profitable strategies found - requires manual review'
        
        # Determine final recommendation
        if approval_status == 'auto_approved':
            recommendation = 'approved'
        elif approval_status == 'likely_approved':
            recommendation = 'approved'
        else:
            recommendation = 'pending'
        
        # Calculate suggested offer
        if recommendations:
            best_strategy = max(recommendations, key=lambda x: x['profit'])
            suggested_offer = asking_price - (best_strategy['profit'] * 0.1)  # Leave some room for negotiation
        else:
            suggested_offer = asking_price * 0.85  # Conservative offer
        
        reasons = [approval_reason]
        
        # Add strategy recommendations to reasons
        for rec in recommendations:
            reasons.append(f"{rec['strategy']}: ${rec['profit']:,.0f} profit ({rec['confidence']} confidence)")
        
        return {
            'recommendation': recommendation,
            'suggested_offer': suggested_offer,
            'mao': wholesale_mao if 'wholesale_mao' in locals() else 0,
            'profit': max(wholesale_profit, novation_profit) if 'wholesale_profit' in locals() else 0,
            'asking_price_to_arv': asking_price / arv if arv > 0 else 0,
            'rehab_to_arv': rehab_cost / arv if arv > 0 else 0,
            'reasons': reasons,
            'approval_status': approval_status,
            'strategies': recommendations
        }
        
    except Exception as e:
        logging.error(f"Error in auto_underwrite_deal_with_mao: {e}")
        return {
            'recommendation': 'denied',
            'suggested_offer': 0,
            'mao': 0,
            'profit': 0,
            'asking_price_to_arv': 0,
            'rehab_to_arv': 0,
            'reasons': ['Error processing deal data with MAO analysis'],
            'approval_status': 'needs_review',
            'strategies': []
        }