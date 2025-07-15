"""
Professional Renovation Estimator Backend Service
Based on the "Copy of Full Renovation Estimator" PDF template
"""

import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class RenovationEstimatorService:
    """
    Professional renovation cost calculator service based on industry-standard templates
    """
    
    def __init__(self):
        """Initialize the renovation estimator service with professional cost databases"""
        self.cost_database = {
            'exterior': {
                'roof': {
                    'tearoff_per_sq': 150,
                    'reshingle_per_sq': 350,
                    'resheet_per_sq': 120,
                    'base_cost': 500
                },
                'siding': {
                    'replace_per_sqft': 8.50,
                    'base_cost': 300
                },
                'paint': {
                    'ext_siding_per_sqft': 3.20,
                    'ext_trim_per_sqft': 4.50,
                    'foundation_per_sqft': 2.80,
                    'base_cost': 200
                },
                'foundation': {
                    'straighten_per_ft': 85,
                    'rebuild_per_ft': 125,
                    'base_cost': 400
                },
                'windows': {
                    'standard_replacement': 650,
                    'historic_replacement': 1250,
                    'glass_replacement': 180,
                    'base_cost': 100
                }
            },
            'mechanical': {
                'hvac': {
                    'gas_meter_install': 850,
                    'furnace_install': 3500,
                    'ac_install': 4200,
                    'bath_fan_install': 225,
                    'reduct_per_sqft': 4.50,
                    'base_cost': 300
                },
                'electrical': {
                    'panel_replacement': 1800,
                    'vanity_light': 185,
                    'ceiling_fan': 275,
                    'smoke_detector': 95,
                    'rewire_per_sqft': 3.80,
                    'base_cost': 250
                },
                'plumbing': {
                    'water_heater': 1250,
                    'sink_location': 850,
                    'toilet_location': 650,
                    'tub_location': 1400,
                    'repipe_per_sqft': 4.20,
                    'base_cost': 200
                }
            },
            'interior': {
                'kitchen': {
                    'renovation_per_sqft': 125,
                    'countertop_per_lf': 85,
                    'cabinets_multiplier': 1.25,
                    'appliances_multiplier': 1.15,
                    'flooring_multiplier': 1.10,
                    'paint_multiplier': 1.05,
                    'base_cost': 1000
                },
                'bathrooms': {
                    'renovation_per_sqft': 140,
                    'fixtures_multiplier': 1.20,
                    'tile_multiplier': 1.30,
                    'vanity_multiplier': 1.15,
                    'base_cost': 800
                },
                'living_areas': {
                    'renovation_per_sqft': 45,
                    'flooring_multiplier': 1.25,
                    'paint_multiplier': 1.08,
                    'base_cost': 300
                },
                'bedrooms': {
                    'renovation_per_sqft': 38,
                    'flooring_multiplier': 1.20,
                    'paint_multiplier': 1.05,
                    'base_cost': 200
                }
            }
        }
    
    def calculate_renovation_estimate(self, property_data: Dict[str, Any], renovation_scope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive renovation estimate based on property data and renovation scope
        
        Args:
            property_data: Property specifics (sqft, bedrooms, bathrooms, etc.)
            renovation_scope: Detailed renovation requirements by category
            
        Returns:
            Dict containing detailed cost breakdown and profit analysis
        """
        try:
            # Extract property specifics
            sqft = property_data.get('sqft', 0)
            bedrooms = property_data.get('bedrooms', 0)
            bathrooms = property_data.get('bathrooms', 0)
            purchase_price = property_data.get('purchase_price', 0)
            arv = property_data.get('arv', 0)
            
            # Calculate costs by category
            exterior_costs = self._calculate_exterior_costs(renovation_scope.get('exterior', {}), sqft)
            mechanical_costs = self._calculate_mechanical_costs(renovation_scope.get('mechanical', {}), sqft)
            interior_costs = self._calculate_interior_costs(renovation_scope.get('interior', {}), sqft)
            
            # Calculate total costs
            total_costs = exterior_costs['total'] + mechanical_costs['total'] + interior_costs['total']
            
            # Calculate profit analysis
            profit_analysis = self._calculate_profit_analysis(
                purchase_price, total_costs, arv
            )
            
            return {
                'exterior_costs': exterior_costs,
                'mechanical_costs': mechanical_costs,
                'interior_costs': interior_costs,
                'total_costs': total_costs,
                'profit_analysis': profit_analysis,
                'property_data': property_data
            }
            
        except Exception as e:
            logger.error(f"Error calculating renovation estimate: {str(e)}")
            raise Exception(f"Failed to calculate renovation estimate: {str(e)}")
    
    def _calculate_exterior_costs(self, exterior_scope: Dict[str, Any], sqft: float) -> Dict[str, Any]:
        """Calculate exterior renovation costs"""
        costs = self.cost_database['exterior']
        total = 0
        breakdown = {}
        
        # Roof costs
        roof = exterior_scope.get('roof', {})
        roof_cost = costs['roof']['base_cost']
        if roof.get('tearoff'):
            roof_cost += roof.get('squares', 0) * costs['roof']['tearoff_per_sq']
        if roof.get('reshingle'):
            roof_cost += roof.get('squares', 0) * costs['roof']['reshingle_per_sq']
        if roof.get('resheet'):
            roof_cost += roof.get('squares', 0) * costs['roof']['resheet_per_sq']
        
        breakdown['roof'] = roof_cost
        total += roof_cost
        
        # Siding costs
        siding = exterior_scope.get('siding', {})
        siding_cost = costs['siding']['base_cost']
        if siding.get('replace'):
            siding_cost += siding.get('squares', 0) * costs['siding']['replace_per_sqft']
        
        breakdown['siding'] = siding_cost
        total += siding_cost
        
        # Paint costs
        paint = exterior_scope.get('paint', {})
        paint_cost = costs['paint']['base_cost']
        if paint.get('ext_siding'):
            paint_cost += paint.get('siding_sq', 0) * costs['paint']['ext_siding_per_sqft']
        if paint.get('ext_trim'):
            paint_cost += sqft * 0.15 * costs['paint']['ext_trim_per_sqft']
        if paint.get('foundation'):
            paint_cost += sqft * 0.20 * costs['paint']['foundation_per_sqft']
        
        breakdown['paint'] = paint_cost
        total += paint_cost
        
        # Foundation costs
        foundation = exterior_scope.get('foundation', {})
        foundation_cost = costs['foundation']['base_cost']
        if foundation.get('straighten'):
            foundation_cost += foundation.get('repair_ft', 0) * costs['foundation']['straighten_per_ft']
        if foundation.get('rebuild'):
            foundation_cost += foundation.get('repair_ft', 0) * costs['foundation']['rebuild_per_ft']
        
        breakdown['foundation'] = foundation_cost
        total += foundation_cost
        
        # Windows costs
        windows = exterior_scope.get('windows', {})
        windows_cost = costs['windows']['base_cost']
        windows_cost += windows.get('replacements', 0) * costs['windows']['standard_replacement']
        windows_cost += windows.get('historic', 0) * costs['windows']['historic_replacement']
        windows_cost += windows.get('glass', 0) * costs['windows']['glass_replacement']
        
        breakdown['windows'] = windows_cost
        total += windows_cost
        
        return {
            'total': total,
            'breakdown': breakdown
        }
    
    def _calculate_mechanical_costs(self, mechanical_scope: Dict[str, Any], sqft: float) -> Dict[str, Any]:
        """Calculate mechanical renovation costs"""
        costs = self.cost_database['mechanical']
        total = 0
        breakdown = {}
        
        # HVAC costs
        hvac = mechanical_scope.get('hvac', {})
        hvac_cost = costs['hvac']['base_cost']
        hvac_cost += hvac.get('gas_meter', 0) * costs['hvac']['gas_meter_install']
        hvac_cost += hvac.get('furnace', 0) * costs['hvac']['furnace_install']
        hvac_cost += hvac.get('ac', 0) * costs['hvac']['ac_install']
        hvac_cost += hvac.get('bath_fans', 0) * costs['hvac']['bath_fan_install']
        if hvac.get('reduct'):
            hvac_cost += sqft * costs['hvac']['reduct_per_sqft']
        
        breakdown['hvac'] = hvac_cost
        total += hvac_cost
        
        # Electrical costs
        electrical = mechanical_scope.get('electrical', {})
        electrical_cost = costs['electrical']['base_cost']
        electrical_cost += electrical.get('panels', 0) * costs['electrical']['panel_replacement']
        electrical_cost += electrical.get('vanity_lights', 0) * costs['electrical']['vanity_light']
        electrical_cost += electrical.get('ceiling_fans', 0) * costs['electrical']['ceiling_fan']
        electrical_cost += electrical.get('smoke_detectors', 0) * costs['electrical']['smoke_detector']
        if electrical.get('rewire'):
            electrical_cost += sqft * costs['electrical']['rewire_per_sqft']
        
        breakdown['electrical'] = electrical_cost
        total += electrical_cost
        
        # Plumbing costs
        plumbing = mechanical_scope.get('plumbing', {})
        plumbing_cost = costs['plumbing']['base_cost']
        plumbing_cost += plumbing.get('water_heater', 0) * costs['plumbing']['water_heater']
        plumbing_cost += plumbing.get('sink_locations', 0) * costs['plumbing']['sink_location']
        plumbing_cost += plumbing.get('toilet_locations', 0) * costs['plumbing']['toilet_location']
        plumbing_cost += plumbing.get('tub_locations', 0) * costs['plumbing']['tub_location']
        if plumbing.get('repipe'):
            plumbing_cost += sqft * costs['plumbing']['repipe_per_sqft']
        
        breakdown['plumbing'] = plumbing_cost
        total += plumbing_cost
        
        return {
            'total': total,
            'breakdown': breakdown
        }
    
    def _calculate_interior_costs(self, interior_scope: Dict[str, Any], sqft: float) -> Dict[str, Any]:
        """Calculate interior renovation costs"""
        costs = self.cost_database['interior']
        total = 0
        breakdown = {}
        
        # Kitchen costs
        kitchen = interior_scope.get('kitchen', {})
        kitchen_sqft = kitchen.get('sqft', 0)
        kitchen_cost = costs['kitchen']['base_cost']
        kitchen_cost += kitchen_sqft * costs['kitchen']['renovation_per_sqft']
        kitchen_cost += kitchen.get('countertop', 0) * costs['kitchen']['countertop_per_lf']
        
        # Apply multipliers for upgrades
        if kitchen.get('cabinets'):
            kitchen_cost *= costs['kitchen']['cabinets_multiplier']
        if kitchen.get('appliances'):
            kitchen_cost *= costs['kitchen']['appliances_multiplier']
        if kitchen.get('flooring'):
            kitchen_cost *= costs['kitchen']['flooring_multiplier']
        if kitchen.get('paint'):
            kitchen_cost *= costs['kitchen']['paint_multiplier']
        
        breakdown['kitchen'] = kitchen_cost
        total += kitchen_cost
        
        # Bathrooms costs
        bathrooms = interior_scope.get('bathrooms', {})
        bathroom_count = bathrooms.get('count', 0)
        bathroom_sqft = bathrooms.get('sqft', 0)
        bathrooms_cost = costs['bathrooms']['base_cost'] * bathroom_count
        bathrooms_cost += bathroom_sqft * bathroom_count * costs['bathrooms']['renovation_per_sqft']
        
        # Apply multipliers for upgrades
        if bathrooms.get('fixtures'):
            bathrooms_cost *= costs['bathrooms']['fixtures_multiplier']
        if bathrooms.get('tile'):
            bathrooms_cost *= costs['bathrooms']['tile_multiplier']
        if bathrooms.get('vanity'):
            bathrooms_cost *= costs['bathrooms']['vanity_multiplier']
        
        breakdown['bathrooms'] = bathrooms_cost
        total += bathrooms_cost
        
        # Living areas costs
        living_areas = interior_scope.get('living_areas', {})
        living_sqft = living_areas.get('sqft', 0)
        living_cost = costs['living_areas']['base_cost']
        living_cost += living_sqft * costs['living_areas']['renovation_per_sqft']
        
        # Apply multipliers for upgrades
        if living_areas.get('flooring'):
            living_cost *= costs['living_areas']['flooring_multiplier']
        if living_areas.get('paint'):
            living_cost *= costs['living_areas']['paint_multiplier']
        
        breakdown['living_areas'] = living_cost
        total += living_cost
        
        # Bedrooms costs
        bedrooms = interior_scope.get('bedrooms', {})
        bedroom_count = bedrooms.get('count', 0)
        bedroom_sqft = bedrooms.get('sqft', 0)
        bedrooms_cost = costs['bedrooms']['base_cost'] * bedroom_count
        bedrooms_cost += bedroom_sqft * bedroom_count * costs['bedrooms']['renovation_per_sqft']
        
        # Apply multipliers for upgrades
        if bedrooms.get('flooring'):
            bedrooms_cost *= costs['bedrooms']['flooring_multiplier']
        if bedrooms.get('paint'):
            bedrooms_cost *= costs['bedrooms']['paint_multiplier']
        
        breakdown['bedrooms'] = bedrooms_cost
        total += bedrooms_cost
        
        return {
            'total': total,
            'breakdown': breakdown
        }
    
    def _calculate_profit_analysis(self, purchase_price: float, renovation_costs: float, arv: float) -> Dict[str, Any]:
        """Calculate profit analysis and deal rating"""
        total_investment = purchase_price + renovation_costs
        profit_dollars = arv - total_investment
        
        # Calculate deal rating
        if profit_dollars >= 50000:
            deal_rating = "Excellent"
        elif profit_dollars >= 30000:
            deal_rating = "Good"
        elif profit_dollars >= 15000:
            deal_rating = "Fair"
        elif profit_dollars >= 0:
            deal_rating = "Marginal"
        else:
            deal_rating = "Poor"
        
        return {
            'total_investment': total_investment,
            'profit_dollars': profit_dollars,
            'deal_rating': deal_rating,
            'profit_margin': (profit_dollars / arv * 100) if arv > 0 else 0
        }
    
    def save_renovation_project(self, project_data: Dict[str, Any], estimate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save renovation project to database"""
        try:
            # In a real application, this would save to database
            # For now, we'll just return success
            return {
                'success': True,
                'project_id': 'temp_project_id',
                'message': 'Project saved successfully'
            }
        except Exception as e:
            logger.error(f"Error saving renovation project: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }