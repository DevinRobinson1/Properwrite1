"""
AI Strategy Assistant for Real Estate Investment Analysis
Uses OpenAI to provide creative financing insights and deal recommendations
"""

import os
import logging
from typing import Dict, Optional
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
logger = logging.getLogger(__name__)

class AIStrategyAssistant:
    def __init__(self):
        """Initialize AI Strategy Assistant with OpenAI client"""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def generate_strategy_insight(self, arv: int, repairs: int, rent: int, equity: int, 
                                location: str, exit_goals: str, comparable_sales: list = None) -> Dict:
        """
        Generate AI-powered strategy insights for real estate deals
        """
        if not self.client:
            return {
                'status': 'error',
                'error': 'OpenAI API key not configured',
                'insight': 'AI insights require OpenAI API configuration'
            }
        
        try:
            # Prepare market context from comparable sales
            market_context = self._analyze_comparables(comparable_sales) if comparable_sales else "No comparable sales data available"
            
            # Create comprehensive prompt for AI analysis
            prompt = f"""
You are an expert real estate investment advisor analyzing a creative financing opportunity.

DEAL ANALYSIS:
- Property ARV (After Repair Value): ${arv:,}
- Estimated Repairs: ${repairs:,}
- Monthly Rent Potential: ${rent:,}
- Seller Equity Position: ${equity:,}
- Location: {location}
- Seller's Primary Goal: {exit_goals}

MARKET CONTEXT:
{market_context}

ANALYSIS REQUIRED:
1. Recommend the optimal creative financing strategy (Wholesale, Subject-To, Novation/Installment, or Seller Finance)
2. Provide a realistic offer range with rationale
3. Explain the strategic advantages for both investor and seller
4. Draft a seller-friendly summary that positions the offer attractively

FORMAT RESPONSE AS:
## Recommended Strategy: [Strategy Name]

## Offer Range Analysis
- Suggested Offer: $[amount]
- Rationale: [explanation]

## Strategic Advantages
For Investor:
- [advantage 1]
- [advantage 2]

For Seller:
- [advantage 1] 
- [advantage 2]

## Seller Presentation Summary
[2-3 sentences explaining the offer in seller-friendly language]

## Execution Notes
[Key considerations for implementing this strategy]

IMPORTANT: Do not use asterisks (*) anywhere in your response. Use regular text formatting only.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            
            insight_content = response.choices[0].message.content
            
            return {
                'status': 'success',
                'insight': insight_content,
                'prompt_used': prompt[:200] + "...",  # Store first 200 chars for debugging
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'insight': f'Unable to generate AI insights: {str(e)}'
            }
    
    def analyze_deal_feasibility(self, wholesale_data: Dict, installment_data: Dict, 
                                subject_to_data: Dict, seller_finance_data: Dict) -> Dict:
        """
        Compare all four strategies and recommend the best approach
        """
        if not self.client:
            return {
                'status': 'error',
                'error': 'OpenAI API key not configured',
                'analysis': 'AI analysis requires OpenAI API configuration'
            }
        
        try:
            # Extract key metrics from each strategy
            strategies_summary = f"""
WHOLESALE ANALYSIS:
- MAO (Maximum Allowable Offer): ${wholesale_data.get('recommended_mao', 0):,}
- Profit Potential: ${wholesale_data.get('profit_potential', 0):,}
- Risk Level: {wholesale_data.get('risk_level', 'Unknown')}

INSTALLMENT/NOVATION:
- Purchase Price: ${installment_data.get('purchase_price', 0):,}
- Monthly Cash Flow: ${installment_data.get('monthly_cash_flow', 0):,}
- Total Profit: ${installment_data.get('total_profit', 0):,}

SUBJECT-TO:
- Cash to Seller: ${subject_to_data.get('cash_to_seller', 0):,}
- Monthly Cash Flow: ${subject_to_data.get('monthly_cash_flow', 0):,}
- Equity Capture: ${subject_to_data.get('equity_capture', 0):,}

SELLER FINANCE:
- Down Payment: ${seller_finance_data.get('down_payment', 0):,}
- Monthly Payment: ${seller_finance_data.get('monthly_payment', 0):,}
- Total Interest: ${seller_finance_data.get('total_interest', 0):,}
"""

            prompt = f"""
As a real estate investment strategist, analyze these four acquisition strategies and provide clear guidance:

{strategies_summary}

PROVIDE:
1. Rank strategies from best to worst for this deal
2. Identify the primary advantages of your top recommendation
3. Highlight any red flags or risks to consider
4. Suggest next steps for implementation

Keep response concise and actionable.
IMPORTANT: Do not use asterisks (*) anywhere in your response. Use regular text formatting only.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=600
            )
            
            analysis_content = response.choices[0].message.content
            
            return {
                'status': 'success',
                'analysis': analysis_content,
                'strategies_compared': 4,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            logger.error(f"OpenAI feasibility analysis error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'analysis': f'Unable to generate feasibility analysis: {str(e)}'
            }
    
    def _analyze_comparables(self, comparable_sales: list) -> str:
        """
        Analyze comparable sales data for market context
        """
        if not comparable_sales:
            return "No comparable sales data available for market analysis."
        
        # Extract key market metrics
        prices = [comp.get('sale_price', 0) for comp in comparable_sales if comp.get('sale_price', 0) > 0]
        sqft_values = [comp.get('square_feet', 0) for comp in comparable_sales if comp.get('square_feet', 0) > 0]
        
        if not prices:
            return "Comparable sales data incomplete - no valid sale prices found."
        
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        price_per_sqft = []
        if sqft_values and len(prices) == len(sqft_values):
            price_per_sqft = [prices[i] / sqft_values[i] for i in range(len(prices)) if sqft_values[i] > 0]
        
        market_summary = f"""
COMPARABLE SALES ANALYSIS ({len(comparable_sales)} properties):
- Price Range: ${min_price:,} - ${max_price:,}
- Average Sale Price: ${avg_price:,.0f}
"""
        
        if price_per_sqft:
            avg_psf = sum(price_per_sqft) / len(price_per_sqft)
            market_summary += f"- Average Price per Sq Ft: ${avg_psf:.0f}"
        
        return market_summary
    
    def get_seller_psychology_guidance(self, exit_goals: str) -> Dict:
        """
        Provide seller psychology insights based on their stated goals
        """
        psychology_map = {
            'highest_price': {
                'strategy': 'Seller Finance',
                'approach': 'Emphasize full ARV purchase price and steady monthly income',
                'talking_points': ['Full market value', 'Secure monthly payments', 'Tax advantages']
            },
            'speed': {
                'strategy': 'Wholesale',
                'approach': 'Highlight quick closing and no contingencies',
                'talking_points': ['Cash offer', '7-14 day closing', 'No financing contingencies']
            },
            'no_repairs': {
                'strategy': 'Subject-To or Installment',
                'approach': 'Stress as-is purchase with no repair responsibilities',
                'talking_points': ['As-is condition', 'No repair obligations', 'Immediate relief']
            },
            'monthly_income': {
                'strategy': 'Seller Finance',
                'approach': 'Focus on steady passive income stream',
                'talking_points': ['Guaranteed monthly income', 'Better than bank rates', 'Passive investment']
            }
        }
        
        # Default guidance if specific goal not mapped
        guidance = psychology_map.get(exit_goals.lower().replace(' ', '_'), {
            'strategy': 'Flexible',
            'approach': 'Assess seller priorities during conversation',
            'talking_points': ['Multiple options available', 'Customized solution', 'Win-win approach']
        })
        
        return {
            'recommended_strategy': guidance['strategy'],
            'communication_approach': guidance['approach'],
            'key_talking_points': guidance['talking_points'],
            'seller_goal': exit_goals
        }

# Create global instance
ai_strategy_assistant = AIStrategyAssistant()