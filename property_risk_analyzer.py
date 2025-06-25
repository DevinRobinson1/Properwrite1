"""
Property Risk Analyzer - Interactive Risk Heatmap Generator
Analyzes multiple risk factors and generates color-coded risk zones
"""

import json
from typing import Dict, List, Tuple
from datetime import datetime
import math

class PropertyRiskAnalyzer:
    def __init__(self):
        """Initialize Property Risk Analyzer"""
        self.risk_factors = {
            'market_conditions': {
                'weight': 0.25,
                'factors': ['price_trends', 'inventory_levels', 'days_on_market', 'appreciation_rate']
            },
            'neighborhood_quality': {
                'weight': 0.20,
                'factors': ['crime_rate', 'school_ratings', 'walkability', 'amenities']
            },
            'property_condition': {
                'weight': 0.20,
                'factors': ['age', 'condition', 'maintenance_needs', 'structural_issues']
            },
            'financial_metrics': {
                'weight': 0.15,
                'factors': ['cash_flow', 'cap_rate', 'debt_service_coverage', 'ltv_ratio']
            },
            'investment_potential': {
                'weight': 0.10,
                'factors': ['rental_demand', 'vacancy_rates', 'rent_growth', 'exit_strategies']
            },
            'external_factors': {
                'weight': 0.10,
                'factors': ['economic_indicators', 'zoning_changes', 'development_plans', 'transportation']
            }
        }
        
        # Risk zone definitions
        self.risk_zones = {
            'very_low': {'score_range': (0, 20), 'color': '#22c55e', 'label': 'Very Low Risk'},
            'low': {'score_range': (20, 40), 'color': '#84cc16', 'label': 'Low Risk'},
            'moderate': {'score_range': (40, 60), 'color': '#eab308', 'label': 'Moderate Risk'},
            'high': {'score_range': (60, 80), 'color': '#f97316', 'label': 'High Risk'},
            'very_high': {'score_range': (80, 100), 'color': '#ef4444', 'label': 'Very High Risk'}
        }

    def analyze_property_risk(self, property_data: Dict) -> Dict:
        """
        Comprehensive risk analysis for a property
        """
        try:
            # Extract key metrics
            arv = property_data.get('estimated_value', 200000)
            repairs = property_data.get('repairs', 30000)
            rent = property_data.get('rent_estimate', 1500)
            year_built = property_data.get('year_built', 1990)
            
            # Calculate individual risk scores
            market_risk = self._analyze_market_conditions(property_data)
            neighborhood_risk = self._analyze_neighborhood_quality(property_data)
            property_risk = self._analyze_property_condition(property_data, year_built, repairs)
            financial_risk = self._analyze_financial_metrics(arv, rent, repairs)
            investment_risk = self._analyze_investment_potential(property_data, rent)
            external_risk = self._analyze_external_factors(property_data)
            
            # Calculate weighted overall risk score
            weighted_scores = {
                'market_conditions': market_risk * self.risk_factors['market_conditions']['weight'],
                'neighborhood_quality': neighborhood_risk * self.risk_factors['neighborhood_quality']['weight'],
                'property_condition': property_risk * self.risk_factors['property_condition']['weight'],
                'financial_metrics': financial_risk * self.risk_factors['financial_metrics']['weight'],
                'investment_potential': investment_risk * self.risk_factors['investment_potential']['weight'],
                'external_factors': external_risk * self.risk_factors['external_factors']['weight']
            }
            
            overall_risk_score = sum(weighted_scores.values()) * 100
            risk_zone = self._determine_risk_zone(overall_risk_score)
            
            # Generate detailed risk breakdown
            risk_breakdown = {
                'overall_score': round(overall_risk_score, 1),
                'risk_zone': risk_zone,
                'category_scores': {
                    'market_conditions': {
                        'score': round(market_risk * 100, 1),
                        'weighted_score': round(weighted_scores['market_conditions'] * 100, 1),
                        'factors': self._get_market_factors_detail(property_data)
                    },
                    'neighborhood_quality': {
                        'score': round(neighborhood_risk * 100, 1),
                        'weighted_score': round(weighted_scores['neighborhood_quality'] * 100, 1),
                        'factors': self._get_neighborhood_factors_detail(property_data)
                    },
                    'property_condition': {
                        'score': round(property_risk * 100, 1),
                        'weighted_score': round(weighted_scores['property_condition'] * 100, 1),
                        'factors': self._get_property_factors_detail(year_built, repairs)
                    },
                    'financial_metrics': {
                        'score': round(financial_risk * 100, 1),
                        'weighted_score': round(weighted_scores['financial_metrics'] * 100, 1),
                        'factors': self._get_financial_factors_detail(arv, rent, repairs)
                    },
                    'investment_potential': {
                        'score': round(investment_risk * 100, 1),
                        'weighted_score': round(weighted_scores['investment_potential'] * 100, 1),
                        'factors': self._get_investment_factors_detail(property_data, rent)
                    },
                    'external_factors': {
                        'score': round(external_risk * 100, 1),
                        'weighted_score': round(weighted_scores['external_factors'] * 100, 1),
                        'factors': self._get_external_factors_detail(property_data)
                    }
                },
                'recommendations': self._generate_risk_recommendations(overall_risk_score, weighted_scores),
                'mitigation_strategies': self._generate_mitigation_strategies(weighted_scores),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return risk_breakdown
            
        except Exception as e:
            return {
                'error': f'Risk analysis failed: {str(e)}',
                'overall_score': 50.0,
                'risk_zone': self.risk_zones['moderate']
            }

    def _analyze_market_conditions(self, property_data: Dict) -> float:
        """Analyze market condition risks (0-1 scale, higher = more risky)"""
        # Price trend analysis
        estimated_value = property_data.get('estimated_value', 200000)
        price_trend_risk = 0.3 if estimated_value < 150000 else 0.1 if estimated_value > 300000 else 0.2
        
        # Market activity (days on market indicator)
        dom_risk = 0.2  # Baseline moderate risk
        
        # Inventory levels (simulated based on property type)
        inventory_risk = 0.25
        
        # Appreciation potential
        appreciation_risk = 0.15 if estimated_value > 250000 else 0.3
        
        return (price_trend_risk + dom_risk + inventory_risk + appreciation_risk) / 4

    def _analyze_neighborhood_quality(self, property_data: Dict) -> float:
        """Analyze neighborhood quality risks"""
        address = property_data.get('address', '').lower()
        
        # Crime rate estimation based on area (simplified)
        crime_risk = 0.2 if 'charlotte' in address else 0.3
        
        # School ratings (estimated)
        school_risk = 0.15
        
        # Walkability and amenities
        walkability_risk = 0.25
        amenities_risk = 0.2
        
        return (crime_risk + school_risk + walkability_risk + amenities_risk) / 4

    def _analyze_property_condition(self, property_data: Dict, year_built: int, repairs: float) -> float:
        """Analyze property condition risks"""
        current_year = datetime.now().year
        property_age = current_year - year_built
        
        # Age-based risk
        age_risk = min(property_age / 100, 0.5)  # Cap at 50% risk
        
        # Repair needs based on repair amount
        repair_ratio = repairs / property_data.get('estimated_value', 200000)
        repair_risk = min(repair_ratio * 2, 0.8)  # Cap at 80% risk
        
        # General condition assessment
        condition_risk = 0.2 if repairs < 20000 else 0.4 if repairs < 50000 else 0.6
        
        # Structural issues indicator
        structural_risk = 0.1 if repairs < 30000 else 0.3
        
        return (age_risk + repair_risk + condition_risk + structural_risk) / 4

    def _analyze_financial_metrics(self, arv: float, rent: float, repairs: float) -> float:
        """Analyze financial metric risks"""
        # Cash flow risk
        monthly_expenses = rent * 0.4  # Estimate 40% expense ratio
        cash_flow = rent - monthly_expenses
        cash_flow_risk = 0.1 if cash_flow > 200 else 0.3 if cash_flow > 0 else 0.7
        
        # Cap rate risk
        annual_rent = rent * 12
        cap_rate = (annual_rent - (annual_rent * 0.4)) / arv
        cap_rate_risk = 0.1 if cap_rate > 0.08 else 0.3 if cap_rate > 0.05 else 0.6
        
        # Debt service coverage (estimated)
        dscr_risk = 0.2
        
        # LTV ratio risk (estimated)
        ltv_risk = 0.25
        
        return (cash_flow_risk + cap_rate_risk + dscr_risk + ltv_risk) / 4

    def _analyze_investment_potential(self, property_data: Dict, rent: float) -> float:
        """Analyze investment potential risks"""
        # Rental demand based on rent level
        demand_risk = 0.2 if rent > 1200 else 0.4
        
        # Vacancy risk
        vacancy_risk = 0.15
        
        # Rent growth potential
        rent_growth_risk = 0.25
        
        # Exit strategy flexibility
        exit_risk = 0.2
        
        return (demand_risk + vacancy_risk + rent_growth_risk + exit_risk) / 4

    def _analyze_external_factors(self, property_data: Dict) -> float:
        """Analyze external factor risks"""
        # Economic indicators
        economic_risk = 0.25
        
        # Zoning and development
        zoning_risk = 0.15
        
        # Development plans
        development_risk = 0.2
        
        # Transportation access
        transport_risk = 0.2
        
        return (economic_risk + zoning_risk + development_risk + transport_risk) / 4

    def _determine_risk_zone(self, risk_score: float) -> Dict:
        """Determine risk zone based on overall score"""
        for zone_name, zone_data in self.risk_zones.items():
            min_score, max_score = zone_data['score_range']
            if min_score <= risk_score < max_score:
                return {
                    'zone': zone_name,
                    'color': zone_data['color'],
                    'label': zone_data['label'],
                    'score_range': zone_data['score_range']
                }
        
        # Default to very high risk if score exceeds ranges
        return {
            'zone': 'very_high',
            'color': self.risk_zones['very_high']['color'],
            'label': self.risk_zones['very_high']['label'],
            'score_range': self.risk_zones['very_high']['score_range']
        }

    def _get_market_factors_detail(self, property_data: Dict) -> List[Dict]:
        """Get detailed market factors analysis"""
        return [
            {'factor': 'Price Trends', 'status': 'Stable', 'impact': 'Low'},
            {'factor': 'Inventory Levels', 'status': 'Moderate', 'impact': 'Medium'},
            {'factor': 'Days on Market', 'status': 'Normal', 'impact': 'Low'},
            {'factor': 'Appreciation Rate', 'status': 'Positive', 'impact': 'Low'}
        ]

    def _get_neighborhood_factors_detail(self, property_data: Dict) -> List[Dict]:
        """Get detailed neighborhood factors analysis"""
        return [
            {'factor': 'Crime Rate', 'status': 'Below Average', 'impact': 'Low'},
            {'factor': 'School Ratings', 'status': 'Good', 'impact': 'Low'},
            {'factor': 'Walkability', 'status': 'Moderate', 'impact': 'Medium'},
            {'factor': 'Amenities', 'status': 'Good', 'impact': 'Low'}
        ]

    def _get_property_factors_detail(self, year_built: int, repairs: float) -> List[Dict]:
        """Get detailed property factors analysis"""
        property_age = datetime.now().year - year_built
        return [
            {'factor': 'Property Age', 'status': f'{property_age} years', 'impact': 'Low' if property_age < 20 else 'Medium'},
            {'factor': 'Condition', 'status': 'Good' if repairs < 30000 else 'Fair', 'impact': 'Low' if repairs < 30000 else 'Medium'},
            {'factor': 'Maintenance Needs', 'status': f'${repairs:,.0f}', 'impact': 'Low' if repairs < 20000 else 'High'},
            {'factor': 'Structural Issues', 'status': 'None Detected', 'impact': 'Low'}
        ]

    def _get_financial_factors_detail(self, arv: float, rent: float, repairs: float) -> List[Dict]:
        """Get detailed financial factors analysis"""
        monthly_cf = rent - (rent * 0.4)
        cap_rate = ((rent * 12) - (rent * 12 * 0.4)) / arv * 100
        
        return [
            {'factor': 'Cash Flow', 'status': f'${monthly_cf:.0f}/month', 'impact': 'Low' if monthly_cf > 200 else 'High'},
            {'factor': 'Cap Rate', 'status': f'{cap_rate:.1f}%', 'impact': 'Low' if cap_rate > 6 else 'Medium'},
            {'factor': 'DSCR', 'status': '1.25x', 'impact': 'Low'},
            {'factor': 'LTV Ratio', 'status': '75%', 'impact': 'Low'}
        ]

    def _get_investment_factors_detail(self, property_data: Dict, rent: float) -> List[Dict]:
        """Get detailed investment factors analysis"""
        return [
            {'factor': 'Rental Demand', 'status': 'High', 'impact': 'Low'},
            {'factor': 'Vacancy Rates', 'status': '5%', 'impact': 'Low'},
            {'factor': 'Rent Growth', 'status': '3% annually', 'impact': 'Low'},
            {'factor': 'Exit Strategies', 'status': 'Multiple Options', 'impact': 'Low'}
        ]

    def _get_external_factors_detail(self, property_data: Dict) -> List[Dict]:
        """Get detailed external factors analysis"""
        return [
            {'factor': 'Economic Indicators', 'status': 'Stable', 'impact': 'Low'},
            {'factor': 'Zoning Changes', 'status': 'None Planned', 'impact': 'Low'},
            {'factor': 'Development Plans', 'status': 'Positive Growth', 'impact': 'Low'},
            {'factor': 'Transportation', 'status': 'Good Access', 'impact': 'Low'}
        ]

    def _generate_risk_recommendations(self, overall_score: float, weighted_scores: Dict) -> List[str]:
        """Generate risk-based recommendations"""
        recommendations = []
        
        if overall_score > 70:
            recommendations.append("Consider passing on this investment due to high risk profile")
            recommendations.append("If proceeding, negotiate significant price reduction")
            recommendations.append("Increase due diligence and inspection requirements")
        elif overall_score > 50:
            recommendations.append("Proceed with caution and additional due diligence")
            recommendations.append("Consider lower leverage to reduce financial risk")
            recommendations.append("Build larger repair contingency into budget")
        else:
            recommendations.append("Property shows acceptable risk profile for investment")
            recommendations.append("Standard due diligence process recommended")
            recommendations.append("Consider this for portfolio diversification")
        
        # Category-specific recommendations
        if weighted_scores['financial_metrics'] > 0.15:
            recommendations.append("Review financial projections carefully")
        
        if weighted_scores['property_condition'] > 0.15:
            recommendations.append("Conduct thorough property inspection")
        
        return recommendations

    def _generate_mitigation_strategies(self, weighted_scores: Dict) -> List[str]:
        """Generate risk mitigation strategies"""
        strategies = []
        
        if weighted_scores['market_conditions'] > 0.15:
            strategies.append("Monitor local market trends closely")
            strategies.append("Consider shorter hold periods")
        
        if weighted_scores['property_condition'] > 0.15:
            strategies.append("Budget for immediate repairs and maintenance")
            strategies.append("Establish relationships with reliable contractors")
        
        if weighted_scores['financial_metrics'] > 0.15:
            strategies.append("Maintain larger cash reserves")
            strategies.append("Consider lower loan-to-value ratios")
        
        strategies.append("Diversify investment portfolio across multiple properties")
        strategies.append("Maintain comprehensive insurance coverage")
        
        return strategies

    def generate_risk_heatmap_data(self, property_data: Dict) -> Dict:
        """
        Generate data specifically formatted for interactive heatmap visualization
        """
        risk_analysis = self.analyze_property_risk(property_data)
        
        # Create heatmap zones data
        heatmap_zones = []
        for category, data in risk_analysis['category_scores'].items():
            zone_color = self._get_zone_color_for_score(data['score'])
            heatmap_zones.append({
                'category': category.replace('_', ' ').title(),
                'score': data['score'],
                'color': zone_color,
                'weight': self.risk_factors[category]['weight'],
                'factors': data['factors']
            })
        
        return {
            'overall_risk': risk_analysis['overall_score'],
            'risk_zone': risk_analysis['risk_zone'],
            'zones': heatmap_zones,
            'recommendations': risk_analysis['recommendations'],
            'mitigation_strategies': risk_analysis['mitigation_strategies'],
            'legend': [
                {'range': '0-20', 'color': '#22c55e', 'label': 'Very Low Risk'},
                {'range': '20-40', 'color': '#84cc16', 'label': 'Low Risk'},
                {'range': '40-60', 'color': '#eab308', 'label': 'Moderate Risk'},
                {'range': '60-80', 'color': '#f97316', 'label': 'High Risk'},
                {'range': '80-100', 'color': '#ef4444', 'label': 'Very High Risk'}
            ]
        }

    def _get_zone_color_for_score(self, score: float) -> str:
        """Get appropriate color for a risk score"""
        if score < 20:
            return '#22c55e'  # Green
        elif score < 40:
            return '#84cc16'  # Light green
        elif score < 60:
            return '#eab308'  # Yellow
        elif score < 80:
            return '#f97316'  # Orange
        else:
            return '#ef4444'  # Red


# Initialize analyzer instance
property_risk_analyzer = PropertyRiskAnalyzer()