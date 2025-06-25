"""
Acquisitions Module - Handles all seller offer strategies and deal structuring
Responsible for determining optimal acquisition strategies and generating offers
"""

import logging
from typing import Dict, List, Optional
from wholesale_calculator import calculate_wholesale_offers
from installment_calculator import calculate_installment_offers
from subject_to_calculator import calculate_subject_to_offer
from seller_finance_calculator import calculate_seller_finance_offer
from ai_strategy_assistant import ai_strategy_assistant

logger = logging.getLogger(__name__)

class AcquisitionsModule:
    def __init__(self):
        """Initialize Acquisitions Module"""
        self.strategies = ['wholesale', 'installment', 'subject_to', 'seller_finance']
    
    def analyze_all_acquisition_strategies(self, property_data: Dict) -> Dict:
        """
        Comprehensive analysis of all four acquisition strategies
        """
        try:
            # Extract property parameters
            arv = property_data.get('estimated_value', 200000)
            repairs = property_data.get('repairs', 30000)
            bedrooms = property_data.get('bedrooms', 3)
            bathrooms = property_data.get('bathrooms', 2.0)
            square_feet = property_data.get('square_feet', 1200)
            monthly_rent = property_data.get('rent_estimate', 2000)
            
            logger.info(f"Analyzing acquisitions for ARV: ${arv:,}, Repairs: ${repairs:,}")
            
            # Calculate all strategies
            strategies_analysis = {}
            
            # 1. Wholesale Strategy
            wholesale_result = calculate_wholesale_offers(
                arv=arv,
                repairs=repairs,
                wholesale_arv_percent=0.70,
                min_acceptable_profit=15000,
                bedrooms=int(bedrooms),
                bathrooms=int(bathrooms),
                square_feet=int(square_feet),
                rent=int(monthly_rent)
            )
            strategies_analysis['wholesale'] = wholesale_result
            
            # 2. Installment/Novation Strategy
            installment_result = calculate_installment_offers(
                arv=arv,
                estimated_repairs=repairs,
                discount_to_sell_fast=10000,
                buyer_over_ask_bonus=5000,
                min_acceptable_profit=25000,
                bedrooms=int(bedrooms),
                bathrooms=int(bathrooms),
                square_feet=int(square_feet),
                rent=int(monthly_rent)
            )
            strategies_analysis['installment'] = installment_result
            
            # 3. Subject-To Strategy
            estimated_loan_balance = arv * 0.75
            subject_to_result = calculate_subject_to_offer(
                arv=arv,
                principal_balance=int(estimated_loan_balance),
                purchase_price=4000,
                cash_to_seller=4000,
                monthly_pi=int(estimated_loan_balance * 0.006),
                rent_income=int(monthly_rent),
                rehab=int(repairs),
                bedrooms=int(bedrooms),
                bathrooms=int(bathrooms),
                square_feet=int(square_feet)
            )
            strategies_analysis['subject_to'] = subject_to_result
            
            # 4. Seller Finance Strategy
            seller_finance_result = calculate_seller_finance_offer(
                arv=arv,
                seller_finance_purchase_price=arv * 0.95,
                down_payment=15000,
                interest_rate=6.5,
                monthly_rent=int(monthly_rent),
                rehab_budget=int(repairs),
                bedrooms=int(bedrooms),
                bathrooms=int(bathrooms),
                square_feet=int(square_feet)
            )
            strategies_analysis['seller_finance'] = seller_finance_result
            
            # Generate AI recommendation
            ai_recommendation = self._get_ai_strategy_recommendation(
                strategies_analysis, property_data
            )
            
            return {
                'status': 'success',
                'strategies': strategies_analysis,
                'ai_recommendation': ai_recommendation,
                'property_summary': {
                    'arv': arv,
                    'repairs': repairs,
                    'estimated_equity': arv - estimated_loan_balance,
                    'monthly_rent': monthly_rent,
                    'location': property_data.get('address', 'Unknown Location')
                }
            }
            
        except Exception as e:
            logger.error(f"Acquisitions analysis error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'strategies': {},
                'ai_recommendation': None
            }
    
    def get_optimal_acquisition_strategy(self, property_data: Dict, seller_goals: str = 'speed') -> Dict:
        """
        Determine the optimal acquisition strategy based on property data and seller psychology
        """
        try:
            analysis = self.analyze_all_acquisition_strategies(property_data)
            
            if analysis['status'] == 'error':
                return analysis
            
            strategies = analysis['strategies']
            
            # Strategy scoring based on seller goals
            strategy_scores = self._score_strategies_by_seller_goals(strategies, seller_goals)
            
            # Get top recommendation
            optimal_strategy = max(strategy_scores.items(), key=lambda x: x[1])
            
            return {
                'status': 'success',
                'optimal_strategy': optimal_strategy[0],
                'strategy_details': strategies[optimal_strategy[0]],
                'confidence_score': optimal_strategy[1],
                'seller_goals': seller_goals,
                'all_scores': strategy_scores,
                'reasoning': self._get_strategy_reasoning(optimal_strategy[0], seller_goals)
            }
            
        except Exception as e:
            logger.error(f"Optimal strategy analysis error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'optimal_strategy': None
            }
    
    def generate_offer_package(self, strategy_name: str, property_data: Dict, seller_profile: Dict = None) -> Dict:
        """
        Generate complete offer package for selected strategy
        """
        try:
            analysis = self.analyze_all_acquisition_strategies(property_data)
            
            if analysis['status'] == 'error':
                return analysis
            
            strategy_data = analysis['strategies'].get(strategy_name)
            if not strategy_data:
                return {
                    'status': 'error',
                    'error': f'Strategy {strategy_name} not found'
                }
            
            # Generate seller-facing offer summary
            offer_summary = self._create_seller_offer_summary(strategy_name, strategy_data, property_data)
            
            # Generate negotiation talking points
            talking_points = self._generate_talking_points(strategy_name, seller_profile or {})
            
            # Calculate alternative offers for negotiation
            alternative_offers = self._generate_alternative_offers(strategy_name, strategy_data)
            
            return {
                'status': 'success',
                'strategy': strategy_name,
                'primary_offer': strategy_data,
                'offer_summary': offer_summary,
                'talking_points': talking_points,
                'alternative_offers': alternative_offers,
                'next_steps': self._get_strategy_next_steps(strategy_name)
            }
            
        except Exception as e:
            logger.error(f"Offer package generation error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_ai_strategy_recommendation(self, strategies: Dict, property_data: Dict) -> Optional[Dict]:
        """Get AI-powered strategy recommendation"""
        try:
            location = property_data.get('address', 'Unknown Location')
            arv = property_data.get('estimated_value', 0)
            repairs = property_data.get('repairs', 0)
            rent = property_data.get('rent_estimate', 0)
            equity = arv * 0.25  # Estimate equity
            
            ai_insight = ai_strategy_assistant.analyze_deal_feasibility(
                wholesale_data=strategies.get('wholesale', {}),
                installment_data=strategies.get('installment', {}),
                subject_to_data=strategies.get('subject_to', {}),
                seller_finance_data=strategies.get('seller_finance', {})
            )
            
            return ai_insight
            
        except Exception as e:
            logger.error(f"AI recommendation error: {e}")
            return None
    
    def _score_strategies_by_seller_goals(self, strategies: Dict, seller_goals: str) -> Dict:
        """Score strategies based on seller psychology and goals"""
        scores = {}
        
        goal_weights = {
            'speed': {'wholesale': 0.9, 'subject_to': 0.7, 'installment': 0.5, 'seller_finance': 0.3},
            'highest_price': {'seller_finance': 0.9, 'installment': 0.7, 'subject_to': 0.5, 'wholesale': 0.3},
            'no_repairs': {'subject_to': 0.9, 'installment': 0.8, 'wholesale': 0.6, 'seller_finance': 0.4},
            'monthly_income': {'seller_finance': 0.9, 'installment': 0.6, 'subject_to': 0.4, 'wholesale': 0.2}
        }
        
        weights = goal_weights.get(seller_goals, goal_weights['speed'])
        
        for strategy, weight in weights.items():
            if strategy in strategies:
                # Base score from seller goal alignment
                base_score = weight * 100
                
                # Adjust based on strategy viability
                strategy_data = strategies[strategy]
                if strategy == 'wholesale' and strategy_data.get('recommended_mao', 0) > 0:
                    base_score += 10
                elif strategy == 'seller_finance' and strategy_data.get('monthly_payment', 0) > 0:
                    base_score += 15
                
                scores[strategy] = min(base_score, 100)
        
        return scores
    
    def _get_strategy_reasoning(self, strategy: str, seller_goals: str) -> str:
        """Get reasoning for strategy recommendation"""
        reasoning_map = {
            'wholesale': f"Best for {seller_goals} - provides quick cash closing with minimal complications",
            'installment': f"Optimal for {seller_goals} - balances price and convenience with flexible terms",
            'subject_to': f"Ideal for {seller_goals} - immediate relief from payments with equity preservation",
            'seller_finance': f"Perfect for {seller_goals} - maximizes price while creating passive income stream"
        }
        
        return reasoning_map.get(strategy, "Strategic recommendation based on deal analysis")
    
    def _create_seller_offer_summary(self, strategy: str, strategy_data: Dict, property_data: Dict) -> str:
        """Create seller-friendly offer summary"""
        summaries = {
            'wholesale': f"Cash offer of ${strategy_data.get('recommended_mao', 0):,} with 7-14 day closing. No repairs, no contingencies, no financing delays.",
            'installment': f"Purchase price of ${strategy_data.get('purchase_price', 0):,} with ${strategy_data.get('down_payment', 0):,} down and monthly payments. As-is condition.",
            'subject_to': f"Take over your existing mortgage payments plus ${strategy_data.get('cash_to_seller', 0):,} cash to you at closing. Immediate payment relief.",
            'seller_finance': f"Full purchase price of ${strategy_data.get('purchase_price', 0):,} with ${strategy_data.get('down_payment', 0):,} down. You carry financing at competitive rates."
        }
        
        return summaries.get(strategy, "Custom acquisition terms available")
    
    def _generate_talking_points(self, strategy: str, seller_profile: Dict) -> List[str]:
        """Generate negotiation talking points"""
        base_points = {
            'wholesale': [
                "Guaranteed cash closing - no financing contingencies",
                "Close in 7-14 days vs 30-45 for traditional sales",
                "No repair obligations or additional costs",
                "No real estate commission fees"
            ],
            'installment': [
                "Higher purchase price than wholesale",
                "Monthly income stream for steady cash flow",
                "As-is purchase - no repair requirements",
                "Flexible terms to meet your needs"
            ],
            'subject_to': [
                "Immediate relief from monthly mortgage payments",
                "Preserve your credit rating",
                "Cash in your pocket at closing",
                "No liability for future payments"
            ],
            'seller_finance': [
                "Full market value purchase price",
                "Better returns than bank CDs or savings",
                "Monthly passive income for retirement",
                "Tax advantages with installment sale"
            ]
        }
        
        return base_points.get(strategy, ["Flexible terms available", "Win-win solution"])
    
    def _generate_alternative_offers(self, strategy: str, strategy_data: Dict) -> List[Dict]:
        """Generate alternative offers for negotiation"""
        alternatives = []
        
        if strategy == 'wholesale':
            base_mao = strategy_data.get('recommended_mao', 0)
            alternatives = [
                {'offer': base_mao * 0.95, 'terms': 'Quick 7-day closing'},
                {'offer': base_mao * 1.05, 'terms': '14-day closing with inspection'},
                {'offer': base_mao * 1.1, 'terms': '21-day closing, all cash'}
            ]
        elif strategy == 'seller_finance':
            base_price = strategy_data.get('purchase_price', 0)
            base_down = strategy_data.get('down_payment', 0)
            alternatives = [
                {'down_payment': base_down * 1.2, 'rate': '6.0%', 'terms': 'Higher down, lower rate'},
                {'down_payment': base_down * 0.8, 'rate': '7.0%', 'terms': 'Lower down, market rate'},
                {'down_payment': base_down, 'rate': '6.5%', 'terms': 'Balloon payment option'}
            ]
        
        return alternatives
    
    def _get_strategy_next_steps(self, strategy: str) -> List[str]:
        """Get next steps for strategy implementation"""
        next_steps = {
            'wholesale': [
                "Schedule property walkthrough",
                "Verify repair estimates with contractor",
                "Prepare cash proof of funds",
                "Draft purchase agreement"
            ],
            'installment': [
                "Analyze existing mortgage details",
                "Structure payment terms",
                "Prepare installment agreement",
                "Schedule title company meeting"
            ],
            'subject_to': [
                "Review existing mortgage documents",
                "Verify payment history and balance",
                "Prepare authorization to make payments",
                "Draft deed and closing documents"
            ],
            'seller_finance': [
                "Structure financing terms",
                "Prepare promissory note",
                "Schedule appraisal if required",
                "Coordinate with title company"
            ]
        }
        
        return next_steps.get(strategy, ["Prepare documentation", "Schedule closing"])

# Create global instance
acquisitions_module = AcquisitionsModule()