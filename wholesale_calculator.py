"""
Wholesale/Cash Offer Calculator with Ackerman Method
Implements Chris Voss's Ackerman Method for descending offer strategy
"""

def calculate_wholesale_offers(arv, repairs, wholesale_arv_percent=0.70, negative_adjustments=0, positive_adjustments=0, min_acceptable_profit=15000):
    """
    Calculate wholesale offers using Ackerman Method
    Based on strict investment logic for cash buyers
    """
    # Core calculations
    all_in_amount = arv * wholesale_arv_percent
    assignment_price = all_in_amount - repairs
    wholesale_mao = assignment_price - min_acceptable_profit
    
    # Ackerman Method Offers (descending strategy)
    offer_1 = wholesale_mao * 0.65  # First lowball offer
    offer_2 = wholesale_mao * 0.85  # Second offer
    offer_3 = wholesale_mao * 0.95  # Final offer (close to MAO)
    
    # Apply adjustments
    adjusted_arv = arv + positive_adjustments - negative_adjustments
    adjusted_mao = wholesale_mao + (positive_adjustments - negative_adjustments) * wholesale_arv_percent
    
    # Profit insights
    mao_as_percent_of_arv = (wholesale_mao / arv) * 100 if arv > 0 else 0
    retail_gap_before_repairs = arv - wholesale_mao
    retail_gap_gross_profit = arv - repairs - wholesale_mao
    
    # Assignment profit calculations
    assignment_profit = assignment_price - wholesale_mao
    assignment_fee = min_acceptable_profit  # Assignment fee = minimum profit
    
    # Return comprehensive data
    return {
        'arv': arv,
        'repairs': repairs,
        'wholesale_arv_percent': wholesale_arv_percent * 100,
        'negative_adjustments': negative_adjustments,
        'positive_adjustments': positive_adjustments,
        'min_acceptable_profit': min_acceptable_profit,
        
        # Core calculations
        'all_in_amount': all_in_amount,
        'assignment_price': assignment_price,
        'wholesale_mao': max(0, wholesale_mao),
        'adjusted_mao': max(0, adjusted_mao),
        
        # Ackerman Method offers
        'ackerman_offers': {
            'offer_1': max(0, offer_1),
            'offer_2': max(0, offer_2), 
            'offer_3': max(0, offer_3)
        },
        
        # Profit analysis
        'mao_as_percent_of_arv': mao_as_percent_of_arv,
        'retail_gap_before_repairs': retail_gap_before_repairs,
        'retail_gap_gross_profit': retail_gap_gross_profit,
        'assignment_profit': assignment_profit,
        'assignment_fee': assignment_fee,
        
        # Strategy notes
        'strategy_notes': {
            'ackerman_method': 'Start with 65% offer, escalate to 85%, final at 95% of MAO',
            'mao_explanation': f'Maximum price ensuring ${min_acceptable_profit:,} minimum profit',
            'assignment_strategy': f'Sell to investor at ${assignment_price:,} for ${assignment_fee:,} profit'
        },
        
        # Validation flags
        'is_profitable': retail_gap_gross_profit >= min_acceptable_profit,
        'recommended_strategy': 'wholesale' if mao_as_percent_of_arv < 75 else 'consider_other_strategies'
    }

def calculate_ackerman_sequence(base_mao, custom_percentages=None):
    """
    Generate Ackerman Method offer sequence
    Default: 65%, 85%, 95% but allows customization
    """
    if custom_percentages is None:
        custom_percentages = [0.65, 0.85, 0.95]
    
    offers = []
    for i, percentage in enumerate(custom_percentages):
        offers.append({
            'offer_number': i + 1,
            'percentage': percentage * 100,
            'amount': base_mao * percentage,
            'strategy_note': get_ackerman_note(i + 1)
        })
    
    return offers

def get_ackerman_note(offer_number):
    """
    Return strategic notes for each Ackerman offer
    """
    notes = {
        1: "Opening lowball - sets anchor, expect rejection",
        2: "Middle ground - shows movement, builds rapport", 
        3: "Final offer - close to MAO, take it or leave it"
    }
    return notes.get(offer_number, "Strategic offer in sequence")

def validate_wholesale_deal(wholesale_data):
    """
    Validate if wholesale deal meets investment criteria
    """
    validations = []
    
    # Check MAO percentage
    if wholesale_data['mao_as_percent_of_arv'] > 80:
        validations.append({
            'type': 'warning',
            'message': 'MAO exceeds 80% of ARV - tight margins for wholesale'
        })
    
    # Check profit margins
    if wholesale_data['retail_gap_gross_profit'] < wholesale_data['min_acceptable_profit']:
        validations.append({
            'type': 'error', 
            'message': f'Insufficient profit margin - need ${wholesale_data["min_acceptable_profit"]:,} minimum'
        })
    
    # Check repair percentage
    repair_percentage = (wholesale_data['repairs'] / wholesale_data['arv']) * 100
    if repair_percentage > 30:
        validations.append({
            'type': 'warning',
            'message': f'High repair cost ({repair_percentage:.1f}% of ARV) - verify estimates'
        })
    
    return validations

def generate_wholesale_summary(wholesale_data):
    """
    Generate executive summary for wholesale deal
    """
    arv = wholesale_data['arv']
    mao = wholesale_data['wholesale_mao']
    profit = wholesale_data['retail_gap_gross_profit']
    
    summary = f"Wholesale deal analysis for ${arv:,} ARV property. "
    summary += f"Maximum allowable offer: ${mao:,} ({wholesale_data['mao_as_percent_of_arv']:.1f}% of ARV). "
    summary += f"Projected gross profit: ${profit:,}. "
    
    if wholesale_data['is_profitable']:
        summary += "Deal meets minimum profit requirements."
    else:
        summary += "Deal does NOT meet minimum profit requirements."
    
    return summary