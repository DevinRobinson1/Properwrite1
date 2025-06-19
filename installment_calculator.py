"""
Installment Offer Calculator with Ackerman Method
Implements seller psychology framework: Speed + Price + Convenience (choose 2)
Price + Convenience = Installment/Novation Offers
"""

def calculate_installment_offers(arv, estimated_repairs, negative_adjustments=0, positive_adjustments=0, 
                                discount_to_sell_fast=10000, buyer_over_ask_bonus=0, closing_costs=18400, 
                                min_acceptable_profit=15000, split_with_seller_bonus=0, wholesale_mao=0):
    """
    Calculate installment offers using real-world underwriting logic
    Based on seller psychology: Price + Convenience framework
    """
    # Core calculation steps
    list_price = arv - estimated_repairs - negative_adjustments + positive_adjustments - discount_to_sell_fast
    final_sales_price = list_price + buyer_over_ask_bonus
    gross_after_closing = final_sales_price - closing_costs
    installment_mao = gross_after_closing - min_acceptable_profit + split_with_seller_bonus
    
    # Ackerman Method Offers (descending strategy)
    offer_3 = installment_mao * 0.95  # Final offer (close to MAO)
    offer_2 = installment_mao * 0.85  # Second offer
    offer_1 = installment_mao * 0.65  # Opening lowball
    
    # Bonus metrics and comparisons
    mao_as_percent_of_arv = (installment_mao / arv) * 100 if arv > 0 else 0
    installment_vs_wholesale_gap = installment_mao - wholesale_mao if wholesale_mao > 0 else 0
    
    # Profit analysis
    net_profit = gross_after_closing - installment_mao
    profit_margin = (net_profit / final_sales_price) * 100 if final_sales_price > 0 else 0
    
    # As-is value calculation
    as_is_value = arv - estimated_repairs
    
    return {
        'arv': arv,
        'estimated_repairs': estimated_repairs,
        'negative_adjustments': negative_adjustments,
        'positive_adjustments': positive_adjustments,
        'discount_to_sell_fast': discount_to_sell_fast,
        'buyer_over_ask_bonus': buyer_over_ask_bonus,
        'closing_costs': closing_costs,
        'min_acceptable_profit': min_acceptable_profit,
        'split_with_seller_bonus': split_with_seller_bonus,
        
        # Calculated values
        'as_is_value': as_is_value,
        'list_price': list_price,
        'final_sales_price': final_sales_price,
        'gross_after_closing': gross_after_closing,
        'installment_mao': max(0, installment_mao),
        
        # Ackerman offers
        'ackerman_offers': {
            'offer_1': max(0, offer_1),
            'offer_2': max(0, offer_2),
            'offer_3': max(0, offer_3)
        },
        
        # Metrics and insights
        'mao_as_percent_of_arv': mao_as_percent_of_arv,
        'installment_vs_wholesale_gap': installment_vs_wholesale_gap,
        'net_profit': net_profit,
        'profit_margin': profit_margin,
        
        # Strategy framework
        'seller_psychology': {
            'framework': 'Price + Convenience = Installment Offer',
            'value_proposition': 'Higher price with easy closing process',
            'trade_off': 'Slower timeline for maximum seller value'
        },
        
        # Validation
        'is_profitable': net_profit >= min_acceptable_profit,
        'recommended': mao_as_percent_of_arv >= 65 and mao_as_percent_of_arv <= 85
    }

def get_installment_ackerman_strategy(offer_number):
    """
    Return strategic notes for installment Ackerman offers
    """
    strategies = {
        1: "Opening anchor - establishes negotiation floor",
        2: "Middle position - shows flexibility and movement",
        3: "Final offer - maximum price for installment deal"
    }
    return strategies.get(offer_number, "Strategic installment offer")

def calculate_installment_vs_alternatives(installment_data, wholesale_mao=0, subject_to_equity=0):
    """
    Compare installment offer against other strategies
    """
    comparisons = {}
    
    # vs Wholesale
    if wholesale_mao > 0:
        wholesale_advantage = installment_data['installment_mao'] - wholesale_mao
        comparisons['vs_wholesale'] = {
            'advantage': wholesale_advantage,
            'percentage_increase': (wholesale_advantage / wholesale_mao * 100) if wholesale_mao > 0 else 0,
            'recommendation': 'Installment preferred' if wholesale_advantage > 20000 else 'Consider wholesale for speed'
        }
    
    # vs Subject-To
    if subject_to_equity > 0:
        equity_vs_installment = subject_to_equity - installment_data['installment_mao']
        comparisons['vs_subject_to'] = {
            'equity_difference': equity_vs_installment,
            'recommendation': 'Subject-to preferred' if equity_vs_installment > 10000 else 'Installment offers better seller appeal'
        }
    
    return comparisons

def validate_installment_deal(installment_data):
    """
    Validate installment deal against investment criteria
    """
    validations = []
    
    # Check MAO percentage
    mao_percent = installment_data['mao_as_percent_of_arv']
    if mao_percent > 85:
        validations.append({
            'type': 'warning',
            'message': f'High MAO ({mao_percent:.1f}% of ARV) - verify profit margins carefully'
        })
    elif mao_percent < 50:
        validations.append({
            'type': 'warning',
            'message': f'Low MAO ({mao_percent:.1f}% of ARV) - seller may reject offer'
        })
    
    # Check profit adequacy
    if installment_data['net_profit'] < installment_data['min_acceptable_profit']:
        validations.append({
            'type': 'error',
            'message': f'Insufficient profit: ${installment_data["net_profit"]:,.0f} < ${installment_data["min_acceptable_profit"]:,.0f} minimum'
        })
    
    # Check repair percentage
    repair_percent = (installment_data['estimated_repairs'] / installment_data['arv']) * 100
    if repair_percent > 25:
        validations.append({
            'type': 'warning',
            'message': f'High repair cost ({repair_percent:.1f}% of ARV) - consider wholesale instead'
        })
    
    # Check list price viability
    list_vs_arv = (installment_data['list_price'] / installment_data['arv']) * 100
    if list_vs_arv < 80:
        validations.append({
            'type': 'warning',
            'message': f'Low list price ({list_vs_arv:.1f}% of ARV) - may indicate market challenges'
        })
    
    return validations

def generate_installment_summary(installment_data):
    """
    Generate executive summary for installment deal
    """
    arv = installment_data['arv']
    mao = installment_data['installment_mao']
    final_price = installment_data['final_sales_price']
    profit = installment_data['net_profit']
    
    summary = f"Installment deal for ${arv:,} ARV property. "
    summary += f"Maximum offer: ${mao:,} ({installment_data['mao_as_percent_of_arv']:.1f}% of ARV). "
    summary += f"Target sale price: ${final_price:,} with ${profit:,} net profit. "
    
    if installment_data['is_profitable']:
        summary += "Deal structure meets minimum profit requirements for installment strategy."
    else:
        summary += "Deal requires adjustment to meet minimum profit thresholds."
    
    return summary

def get_seller_psychology_framework():
    """
    Return the complete seller psychology framework for UI tooltips
    """
    return {
        'core_principle': 'Sellers can choose any 2 of 3 benefits: Speed, Convenience, Price',
        'strategies': {
            'speed_convenience': {
                'name': 'Wholesale Offer',
                'description': 'Quick cash sale with minimal seller hassle',
                'trade_off': 'Lower price for immediate liquidity'
            },
            'speed_price': {
                'name': 'Subject-To or Seller Finance',
                'description': 'Fast closing at higher price point',
                'trade_off': 'Seller carries financing or deed transfer'
            },
            'price_convenience': {
                'name': 'Installment/Novation',
                'description': 'Maximum price with easy process',
                'trade_off': 'Extended timeline for highest value'
            }
        },
        'installment_benefits': [
            'Highest price of all strategies',
            'Professional marketing and sale',
            'Minimal seller involvement required',
            'Profit sharing on above-ask performance'
        ]
    }