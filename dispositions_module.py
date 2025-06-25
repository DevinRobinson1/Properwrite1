"""
Dispositions Module - Handles property exit strategies and investor listing generation
Determines optimal exit strategies and creates compelling investor listings
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from rentcast_service import rentcast_service

logger = logging.getLogger(__name__)

class DispositionsModule:
    def __init__(self):
        """Initialize Dispositions Module"""
        self.exit_strategies = ['cash_sale', 'mls_listing', 'seller_finance_wrap', 'lease_option']
    
    def analyze_exit_strategies(self, property_data: Dict, acquisition_strategy: str = None) -> Dict:
        """
        Analyze all possible exit strategies for maximum profit
        """
        try:
            arv = property_data.get('estimated_value', 0)
            repairs = property_data.get('repairs', 0)
            monthly_rent = property_data.get('rent_estimate', 0)
            acquisition_cost = property_data.get('acquisition_cost', arv * 0.7)
            
            logger.info(f"Analyzing exit strategies for ARV: ${arv:,}, Acquisition: ${acquisition_cost:,}")
            
            exit_analysis = {}
            
            # 1. Cash Sale to Investors (Wholesale Exit)
            cash_sale_price = self._calculate_investor_cash_price(arv, repairs)
            exit_analysis['cash_sale'] = {
                'strategy': 'Cash Sale to Investors',
                'sale_price': cash_sale_price,
                'profit': cash_sale_price - acquisition_cost - repairs,
                'timeline': '30-60 days',
                'effort_level': 'Low',
                'risk_level': 'Low'
            }
            
            # 2. MLS Listing (Post-Renovation)
            mls_price = self._calculate_mls_listing_price(arv, repairs)
            exit_analysis['mls_listing'] = {
                'strategy': 'MLS Listing (Renovated)',
                'sale_price': mls_price,
                'profit': mls_price - acquisition_cost - repairs - (mls_price * 0.06),  # 6% selling costs
                'timeline': '90-120 days',
                'effort_level': 'High',
                'risk_level': 'Medium'
            }
            
            # 3. Seller Finance Wrap
            wrap_price = self._calculate_seller_finance_wrap_price(arv)
            exit_analysis['seller_finance_wrap'] = {
                'strategy': 'Seller Finance Wrap',
                'sale_price': wrap_price,
                'down_payment': wrap_price * 0.15,
                'monthly_payment': (wrap_price * 0.85 * 0.065) / 12,  # 6.5% interest
                'total_profit': wrap_price - acquisition_cost - repairs,
                'timeline': '60-90 days',
                'effort_level': 'Medium',
                'risk_level': 'Medium'
            }
            
            # 4. Lease Option Resale
            lease_option_price = self._calculate_lease_option_price(arv, monthly_rent)
            exit_analysis['lease_option'] = {
                'strategy': 'Lease Option Resale',
                'option_price': lease_option_price,
                'monthly_rent': monthly_rent * 1.1,  # 10% markup
                'option_fee': lease_option_price * 0.05,
                'timeline': '30-45 days',
                'effort_level': 'Medium',
                'risk_level': 'Medium'
            }
            
            # Determine optimal exit strategy
            optimal_exit = self._determine_optimal_exit(exit_analysis, acquisition_strategy)
            
            return {
                'status': 'success',
                'exit_strategies': exit_analysis,
                'optimal_exit': optimal_exit,
                'market_conditions': self._assess_market_conditions(property_data)
            }
            
        except Exception as e:
            logger.error(f"Exit strategy analysis error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'exit_strategies': {}
            }
    
    def generate_investor_listing_data(self, property_data: Dict, exit_strategy: str = 'cash_sale') -> Dict:
        """
        Generate comprehensive data package for AI listing generator
        """
        try:
            # Core property details
            address = property_data.get('address', 'Property Address')
            bedrooms = property_data.get('bedrooms', 3)
            bathrooms = property_data.get('bathrooms', 2.0)
            square_feet = property_data.get('square_feet', 1200)
            year_built = property_data.get('year_built', 1990)
            
            # Financial details
            arv = property_data.get('estimated_value', 0)
            repairs = property_data.get('repairs', 0)
            monthly_rent = property_data.get('rent_estimate', 0)
            
            # Exit strategy pricing
            exit_analysis = self.analyze_exit_strategies(property_data)
            exit_data = exit_analysis.get('exit_strategies', {}).get(exit_strategy, {})
            
            # Get comparable sales data
            comparable_sales = self._format_comparable_sales(property_data.get('comparable_sales', []))
            active_listings = self._get_active_listings(property_data)
            
            # Neighborhood and location data
            location_data = self._extract_location_data(property_data)
            
            listing_data = {
                'property_details': {
                    'address': address,
                    'bedrooms': bedrooms,
                    'bathrooms': bathrooms,
                    'square_feet': square_feet,
                    'year_built': year_built,
                    'lot_size': property_data.get('lot_size_sqft', 'N/A'),
                    'property_type': property_data.get('property_type', 'Single Family Home')
                },
                'financial_overview': {
                    'buy_now_price': exit_data.get('sale_price', arv * 0.7),
                    'estimated_rehab': repairs,
                    'arv': arv,
                    'projected_profit': exit_data.get('profit', 0),
                    'rent_estimate': monthly_rent,
                    'cap_rate': (monthly_rent * 12) / exit_data.get('sale_price', 1) if exit_data.get('sale_price') else 0
                },
                'comparable_sales': comparable_sales,
                'active_listings': active_listings,
                'location_data': location_data,
                'exit_strategy': exit_strategy,
                'market_analysis': {
                    'avg_days_on_market': self._calculate_avg_dom(comparable_sales),
                    'price_trend': self._analyze_price_trend(comparable_sales),
                    'inventory_level': len(active_listings)
                }
            }
            
            return {
                'status': 'success',
                'listing_data': listing_data
            }
            
        except Exception as e:
            logger.error(f"Listing data generation error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'listing_data': {}
            }
    
    def _calculate_investor_cash_price(self, arv: float, repairs: float) -> float:
        """Calculate cash price for investor buyers (70% ARV rule)"""
        return (arv * 0.70) - repairs
    
    def _calculate_mls_listing_price(self, arv: float, repairs: float) -> float:
        """Calculate MLS listing price post-renovation"""
        return arv * 0.95  # 5% below ARV for quick sale
    
    def _calculate_seller_finance_wrap_price(self, arv: float) -> float:
        """Calculate seller finance wrap price"""
        return arv * 1.05  # 5% premium for financing
    
    def _calculate_lease_option_price(self, arv: float, monthly_rent: float) -> float:
        """Calculate lease option price"""
        return arv * 1.1  # 10% premium for option
    
    def _determine_optimal_exit(self, exit_analysis: Dict, acquisition_strategy: str) -> Dict:
        """Determine optimal exit strategy based on profit and risk"""
        strategies = exit_analysis
        
        # Score each strategy
        scores = {}
        for strategy, data in strategies.items():
            profit = data.get('profit', data.get('total_profit', 0))
            risk_score = {'Low': 3, 'Medium': 2, 'High': 1}.get(data.get('risk_level', 'Medium'), 2)
            effort_score = {'Low': 3, 'Medium': 2, 'High': 1}.get(data.get('effort_level', 'Medium'), 2)
            
            # Calculate composite score
            scores[strategy] = (profit * 0.6) + (risk_score * 1000) + (effort_score * 500)
        
        optimal = max(scores.items(), key=lambda x: x[1])
        return {
            'strategy': optimal[0],
            'details': strategies[optimal[0]],
            'score': optimal[1],
            'reasoning': f"Optimal based on profit potential and risk assessment"
        }
    
    def _assess_market_conditions(self, property_data: Dict) -> Dict:
        """Assess current market conditions"""
        return {
            'market_temperature': 'Balanced',
            'investor_demand': 'High',
            'absorption_rate': 'Moderate',
            'recommended_pricing': '70% ARV for quick sale'
        }
    
    def _format_comparable_sales(self, raw_comps: List[Dict]) -> List[Dict]:
        """Format comparable sales for listing display"""
        formatted_comps = []
        
        for comp in raw_comps[:3]:  # Top 3 comps
            formatted_comp = {
                'address': comp.get('address', 'Comparable Property'),
                'beds_baths': f"{comp.get('bedrooms', 3)}/{comp.get('bathrooms', 2)}",
                'sale_price': comp.get('sale_price', 0),
                'sale_date': comp.get('sale_date', 'Recent'),
                'square_feet': comp.get('square_feet', 0),
                'price_per_sqft': comp.get('price_per_sqft', 0),
                'distance': comp.get('distance_miles', 0)
            }
            formatted_comps.append(formatted_comp)
        
        return formatted_comps
    
    def _get_active_listings(self, property_data: Dict) -> List[Dict]:
        """Get active MLS listings for comparison"""
        # In a real implementation, this would query MLS data
        # For now, generate representative active listings
        bedrooms = property_data.get('bedrooms', 3)
        bathrooms = property_data.get('bathrooms', 2)
        arv = property_data.get('estimated_value', 200000)
        
        active_listings = [
            {
                'address': 'Sample Active Listing 1',
                'beds_baths': f"{bedrooms}/{bathrooms}",
                'list_price': int(arv * 1.05),
                'days_on_market': 14,
                'status': 'Active'
            },
            {
                'address': 'Sample Active Listing 2', 
                'beds_baths': f"{bedrooms}/{bathrooms}",
                'list_price': int(arv * 1.08),
                'days_on_market': 27,
                'status': 'Active'
            }
        ]
        
        return active_listings
    
    def _extract_location_data(self, property_data: Dict) -> Dict:
        """Extract location and neighborhood data"""
        address = property_data.get('address', '')
        
        # Extract city and state from address
        address_parts = address.split(', ')
        city = address_parts[1] if len(address_parts) > 1 else 'City'
        state = address_parts[2].split(' ')[0] if len(address_parts) > 2 else 'State'
        
        return {
            'city': city,
            'state': state,
            'neighborhood': f"{city} Area",
            'nearby_amenities': [
                'Schools within 2 miles',
                'Shopping centers nearby',
                'Major commuter routes',
                'Parks and recreation'
            ],
            'growth_indicators': [
                'Established neighborhood',
                'Strong rental demand',
                'Investment opportunity zone'
            ]
        }
    
    def _calculate_avg_dom(self, comparable_sales: List[Dict]) -> int:
        """Calculate average days on market"""
        return 30  # Default estimate
    
    def _analyze_price_trend(self, comparable_sales: List[Dict]) -> str:
        """Analyze price trends from comps"""
        return "Stable with slight appreciation"

# Create global instance
dispositions_module = DispositionsModule()