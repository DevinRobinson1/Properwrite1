"""
Installment Offer Calculator with Ackerman Method
Implements seller psychology framework: Speed + Price + Convenience (choose 2)
Price + Convenience = Installment/Novation Offers
"""

def calculate_installment_offers(arv, estimated_repairs, negative_adjustments=0, positive_adjustments=0, 
                                discount_to_sell_fast=10000, buyer_over_ask_bonus=0, closing_costs=18400, 
                                min_acceptable_profit=15000, split_with_seller_bonus=0, wholesale_mao=0, 
                                detailed_fees=None):
    """
    Calculate installment offers using real-world underwriting logic
    Based on seller psychology: Price + Convenience framework
    """
    # Handle detailed fees calculation
    if detailed_fees:
        total_closing_costs = calculate_detailed_closing_costs(detailed_fees, arv)
        total_oop_costs = calculate_detailed_oop_costs(detailed_fees)
        total_combined_fees = total_closing_costs + total_oop_costs
    else:
        total_combined_fees = closing_costs
        total_closing_costs = closing_costs
        total_oop_costs = 0
    
    # Core calculation steps
    list_price = arv - estimated_repairs - negative_adjustments + positive_adjustments - discount_to_sell_fast
    final_sales_price = list_price + buyer_over_ask_bonus
    gross_after_closing = final_sales_price - total_combined_fees
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
        'closing_costs': total_combined_fees,
        'detailed_closing_costs': total_closing_costs if detailed_fees else closing_costs,
        'detailed_oop_costs': total_oop_costs,
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
        'gross_profit': gross_after_closing,  # Template expects this field
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

def get_default_installment_fees():
    """
    Return default fee structure for installment deals
    """
    return {
        # Closing Costs (percentage-based on list price or flat fees)
        'flat_fee_listing_service': 500,
        'listing_agent_commission_pct': 2.0,  # % of list price
        'buyer_agent_commission_pct': 2.0,    # % of list price
        'title_escrow_fees_pct': 1.0,         # % of list price
        'loan_concessions': 400,
        'home_warranty': 650,
        'hoa_resale_certificate': 500,
        'hoa_transfer_fee': 350,
        'survey_fee': 650,
        'attorney_fees': 0,
        'private_lending_fees': 0,
        'closing_other_1': 0,
        'closing_other_2': 0,
        'closing_other_3': 0,
        
        # Out-of-Pocket Costs (flat fees)
        'professional_staging': 2500,
        'make_ready_cleaning': 750,
        'photography': 350,
        'matterport': 250,
        'inspection_fee': 1000,
        'max_repairs_pre_close': 3000,
        'earnest_money': 0,
        'due_diligence': 0,
        'oop_other_1': 0,
        'oop_other_2': 0,
        'oop_other_3': 0
    }

def calculate_detailed_closing_costs(fees, list_price):
    """
    Calculate total closing costs from detailed fee structure
    """
    closing_costs = 0
    
    # Flat fees
    closing_costs += fees.get('flat_fee_listing_service', 500)
    closing_costs += fees.get('loan_concessions', 400)
    closing_costs += fees.get('home_warranty', 650)
    closing_costs += fees.get('hoa_resale_certificate', 500)
    closing_costs += fees.get('hoa_transfer_fee', 350)
    closing_costs += fees.get('survey_fee', 650)
    closing_costs += fees.get('attorney_fees', 0)
    closing_costs += fees.get('private_lending_fees', 0)
    closing_costs += fees.get('closing_other_1', 0)
    closing_costs += fees.get('closing_other_2', 0)
    closing_costs += fees.get('closing_other_3', 0)
    
    # Percentage-based fees
    listing_commission = list_price * (fees.get('listing_agent_commission_pct', 2.0) / 100)
    buyer_commission = list_price * (fees.get('buyer_agent_commission_pct', 2.0) / 100)
    title_fees = list_price * (fees.get('title_escrow_fees_pct', 1.0) / 100)
    
    closing_costs += listing_commission + buyer_commission + title_fees
    
    return closing_costs

def calculate_detailed_oop_costs(fees):
    """
    Calculate total out-of-pocket costs from detailed fee structure
    """
    oop_costs = 0
    
    # Out-of-pocket flat fees
    oop_costs += fees.get('professional_staging', 2500)
    oop_costs += fees.get('make_ready_cleaning', 750)
    oop_costs += fees.get('photography', 350)
    oop_costs += fees.get('matterport', 250)
    oop_costs += fees.get('inspection_fee', 1000)
    oop_costs += fees.get('max_repairs_pre_close', 3000)
    oop_costs += fees.get('earnest_money', 0)
    oop_costs += fees.get('due_diligence', 0)
    oop_costs += fees.get('oop_other_1', 0)
    oop_costs += fees.get('oop_other_2', 0)
    oop_costs += fees.get('oop_other_3', 0)
    
    return oop_costs

def validate_installment_fees(fees, list_price):
    """
    Validate fee structure and provide warnings
    """
    validations = []
    
    total_commission = fees.get('listing_agent_commission_pct', 0) + fees.get('buyer_agent_commission_pct', 0)
    if total_commission > 7:
        validations.append({
            'type': 'warning',
            'message': f'High total commission ({total_commission}%) - consider negotiating lower rates'
        })
    
    staging_cost = fees.get('professional_staging', 0)
    if staging_cost > list_price * 0.02:
        validations.append({
            'type': 'warning', 
            'message': f'Staging cost (${staging_cost:,}) exceeds 2% of list price'
        })
    
    repairs_pre_close = fees.get('max_repairs_pre_close', 0)
    if repairs_pre_close > 5000:
        validations.append({
            'type': 'warning',
            'message': f'Pre-closing repairs (${repairs_pre_close:,}) are high - consider wholesale instead'
        })
    
    return validations

def get_fee_tooltips():
    """
    Return tooltips for each fee item
    """
    return {
        'flat_fee_listing_service': 'Flat fee MLS listing service. Range: $300-$800',
        'listing_agent_commission_pct': 'Commission to listing agent. Typical: 2-3%',
        'buyer_agent_commission_pct': 'Commission to buyer\'s agent. Typical: 2-3%',
        'title_escrow_fees_pct': 'Title insurance and escrow fees. Typical: 0.5-1.5%',
        'loan_concessions': 'Buyer closing cost concessions. Range: $0-$2,000',
        'home_warranty': 'Home warranty for buyer. Range: $400-$800',
        'hoa_resale_certificate': 'HOA resale package and certificates. Range: $300-$700',
        'hoa_transfer_fee': 'HOA ownership transfer fee. Range: $200-$500',
        'survey_fee': 'Property survey if required. Range: $400-$1,000',
        'professional_staging': 'Full home staging service. Range: $1,500-$4,000',
        'make_ready_cleaning': 'Deep cleaning before listing. Range: $500-$1,200',
        'photography': 'Professional listing photos. Range: $200-$500',
        'matterport': '3D virtual tour service. Range: $150-$400',
        'inspection_fee': 'Pre-listing inspection. Range: $400-$1,500',
        'max_repairs_pre_close': 'Maximum repair concessions. Limit: 10% of repair budget'
    }