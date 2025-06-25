"""
AI Exit Strategy Assistant
Uses OpenAI to analyze dispositions data and recommend optimal exit strategies
"""

import os
import json
from typing import Dict, List
from openai import OpenAI

class AIExitStrategyAssistant:
    def __init__(self):
        """Initialize AI Exit Strategy Assistant with OpenAI client"""
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def suggest_best_exit_strategy(self, dispositions_data: Dict) -> Dict:
        """
        Analyze all exit strategies and recommend the best approach with reasoning
        """
        try:
            # Calculate all exit strategy metrics
            exit_metrics = self._calculate_exit_metrics(dispositions_data)
            
            # Create prompt for GPT-4o analysis
            prompt = self._create_exit_analysis_prompt(dispositions_data, exit_metrics)
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert real estate investment advisor specializing in exit strategies. "
                        + "Analyze the provided property data and exit strategy options to recommend the optimal approach. "
                        + "Consider profit margins, timeline, risk factors, and market conditions. "
                        + "Provide clear reasoning and rank all strategies. "
                        + "Respond with structured JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "recommendation": self._format_recommendation(result),
                "exit_metrics": exit_metrics,
                "raw_analysis": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze exit strategies: {str(e)}"
            }
    
    def _calculate_exit_metrics(self, data: Dict) -> Dict:
        """Calculate key metrics for all exit strategies"""
        arv = data.get('arv', 200000)
        repairs = data.get('repairs', 30000)
        acquisition_cost = data.get('acquisition_cost', 120000)
        rent = data.get('rent', 1500)
        piti = data.get('piti', 980)
        
        # Cash Sale (70% ARV - Repairs)
        cash_price = (arv * 0.70) - repairs
        cash_profit = cash_price - acquisition_cost
        cash_roi = (cash_profit / acquisition_cost) * 100 if acquisition_cost > 0 else 0
        
        # MLS Sale (90% of As-Is value)
        as_is_value = arv - repairs
        mls_discount = max(as_is_value * 0.10, 20000)
        mls_price = as_is_value - mls_discount
        mls_profit = mls_price - acquisition_cost
        mls_roi = (mls_profit / acquisition_cost) * 100 if acquisition_cost > 0 else 0
        
        # Seller Finance Wrap
        wrap_price = as_is_value * 1.1  # 10% premium
        down_payment = 20000
        buyer_rate = 0.08
        term_years = 15
        loan_amount = wrap_price - down_payment
        
        monthly_rate = buyer_rate / 12
        num_payments = term_years * 12
        buyer_monthly = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        
        wrap_cash_flow = buyer_monthly - piti
        wrap_initial_profit = down_payment - acquisition_cost
        
        # Lease Option (8% ARV)
        lease_option_c2c = arv * 0.08
        lease_cash_flow = rent - piti
        lease_initial_profit = lease_option_c2c - acquisition_cost
        
        return {
            "cash_sale": {
                "price": cash_price,
                "profit": cash_profit,
                "roi": cash_roi,
                "timeline_days": 37,  # Average 30-45 days
                "risk_level": "Low"
            },
            "mls_sale": {
                "price": mls_price,
                "profit": mls_profit,
                "roi": mls_roi,
                "timeline_days": 75,  # Average 60-90 days
                "risk_level": "Medium"
            },
            "seller_finance_wrap": {
                "price": wrap_price,
                "initial_profit": wrap_initial_profit,
                "monthly_cash_flow": wrap_cash_flow,
                "timeline_years": term_years,
                "risk_level": "Medium-High"
            },
            "lease_option": {
                "cash_to_close": lease_option_c2c,
                "initial_profit": lease_initial_profit,
                "monthly_cash_flow": lease_cash_flow,
                "timeline_years": 2,  # Average 1-3 years
                "risk_level": "High"
            }
        }
    
    def _create_exit_analysis_prompt(self, data: Dict, metrics: Dict) -> str:
        """Create structured prompt for exit strategy analysis"""
        return f"""
        Analyze this real estate investment property and recommend the optimal exit strategy:

        PROPERTY DATA:
        - ARV: ${data.get('arv', 200000):,}
        - Repairs Needed: ${data.get('repairs', 30000):,}
        - Acquisition Cost: ${data.get('acquisition_cost', 120000):,}
        - Monthly Rent: ${data.get('rent', 1500):,}
        - Monthly PITI: ${data.get('piti', 980):,}
        - Location: {data.get('city', 'Charlotte')}, {data.get('state', 'NC')}

        EXIT STRATEGY METRICS:

        1. CASH SALE TO INVESTOR:
        - Sale Price: ${metrics['cash_sale']['price']:,.0f}
        - Profit: ${metrics['cash_sale']['profit']:,.0f}
        - ROI: {metrics['cash_sale']['roi']:.1f}%
        - Timeline: {metrics['cash_sale']['timeline_days']} days
        - Risk: {metrics['cash_sale']['risk_level']}

        2. MLS SALE:
        - Sale Price: ${metrics['mls_sale']['price']:,.0f}
        - Profit: ${metrics['mls_sale']['profit']:,.0f}
        - ROI: {metrics['mls_sale']['roi']:.1f}%
        - Timeline: {metrics['mls_sale']['timeline_days']} days
        - Risk: {metrics['mls_sale']['risk_level']}

        3. SELLER FINANCE WRAP:
        - Sale Price: ${metrics['seller_finance_wrap']['price']:,.0f}
        - Initial Profit: ${metrics['seller_finance_wrap']['initial_profit']:,.0f}
        - Monthly Cash Flow: ${metrics['seller_finance_wrap']['monthly_cash_flow']:,.0f}
        - Timeline: {metrics['seller_finance_wrap']['timeline_years']} years
        - Risk: {metrics['seller_finance_wrap']['risk_level']}

        4. LEASE OPTION:
        - Cash-to-Close: ${metrics['lease_option']['cash_to_close']:,.0f}
        - Initial Profit: ${metrics['lease_option']['initial_profit']:,.0f}
        - Monthly Cash Flow: ${metrics['lease_option']['monthly_cash_flow']:,.0f}
        - Timeline: {metrics['lease_option']['timeline_years']} years
        - Risk: {metrics['lease_option']['risk_level']}

        Please provide your analysis in JSON format with:
        {{
            "recommended_strategy": "strategy_name",
            "reasoning": "detailed explanation of why this is the best option",
            "strategy_ranking": [
                {{"strategy": "name", "rank": 1, "pros": ["list"], "cons": ["list"]}},
                // ... other strategies
            ],
            "market_considerations": "relevant market factors",
            "risk_assessment": "overall risk analysis"
        }}
        """
    
    def _format_recommendation(self, analysis: Dict) -> str:
        """Format the AI recommendation into HTML for display"""
        recommended = analysis.get('recommended_strategy', 'Unknown')
        reasoning = analysis.get('reasoning', 'No reasoning provided')
        rankings = analysis.get('strategy_ranking', [])
        market_factors = analysis.get('market_considerations', '')
        risk_assessment = analysis.get('risk_assessment', '')
        
        html = f"""
        <div class="space-y-6">
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 class="text-lg font-bold text-green-800 mb-2">🎯 Recommended Strategy: {recommended}</h4>
                <p class="text-green-700">{reasoning}</p>
            </div>
            
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 class="text-lg font-bold text-blue-800 mb-3">📊 Strategy Rankings</h4>
                <div class="space-y-3">
        """
        
        for strategy in rankings:
            rank = strategy.get('rank', 0)
            name = strategy.get('strategy', 'Unknown')
            pros = strategy.get('pros', [])
            cons = strategy.get('cons', [])
            
            html += f"""
                <div class="bg-white rounded border p-3">
                    <div class="flex items-center mb-2">
                        <span class="bg-blue-500 text-white text-sm px-2 py-1 rounded mr-2">#{rank}</span>
                        <span class="font-semibold">{name}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <div class="text-green-600 font-medium mb-1">Pros:</div>
                            <ul class="text-green-700 space-y-1">
                                {"".join([f"<li>• {pro}</li>" for pro in pros])}
                            </ul>
                        </div>
                        <div>
                            <div class="text-red-600 font-medium mb-1">Cons:</div>
                            <ul class="text-red-700 space-y-1">
                                {"".join([f"<li>• {con}</li>" for con in cons])}
                            </ul>
                        </div>
                    </div>
                </div>
            """
        
        html += f"""
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 class="text-lg font-bold text-yellow-800 mb-2">🏪 Market Considerations</h4>
                    <p class="text-yellow-700 text-sm">{market_factors}</p>
                </div>
                
                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 class="text-lg font-bold text-red-800 mb-2">⚠️ Risk Assessment</h4>
                    <p class="text-red-700 text-sm">{risk_assessment}</p>
                </div>
            </div>
        </div>
        """
        
        return html