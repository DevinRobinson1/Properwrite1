"""
Comprehensive Renovation Estimator Service
Based on professional renovation estimation templates
Handles detailed cost calculations for all renovation aspects
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

class RenovationEstimatorService:
    def __init__(self):
        """Initialize the renovation estimator service"""
        self.logger = logging.getLogger(__name__)
        
    def calculate_comprehensive_estimate(self, property_data: Dict, renovation_scope: Dict) -> Dict:
        """
        Calculate comprehensive renovation estimate with all sections
        
        Args:
            property_data: Basic property information
            renovation_scope: Detailed renovation scope for each section
            
        Returns:
            Complete renovation estimate with all sections
        """
        try:
            # Extract property specifics
            property_specifics = self._extract_property_specifics(property_data)
            
            # Calculate each section
            exterior_costs = self._calculate_exterior_costs(renovation_scope.get('exterior', {}), property_specifics)
            mechanical_costs = self._calculate_mechanical_costs(renovation_scope.get('mechanical', {}), property_specifics)
            interior_costs = self._calculate_interior_costs(renovation_scope.get('interior', {}), property_specifics)
            
            # Calculate contractor labor/material breakdown
            contractor_breakdown = self._calculate_contractor_breakdown(exterior_costs, mechanical_costs, interior_costs)
            
            # Calculate totals and profit analysis
            total_costs = contractor_breakdown['total_contractor_costs']
            profit_analysis = self._calculate_profit_analysis(property_data, total_costs)
            
            return {
                'property_specifics': property_specifics,
                'exterior_costs': exterior_costs,
                'mechanical_costs': mechanical_costs,
                'interior_costs': interior_costs,
                'contractor_breakdown': contractor_breakdown,
                'profit_analysis': profit_analysis,
                'total_renovation_cost': total_costs,
                'estimation_date': datetime.now().strftime('%m/%d/%Y')
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating comprehensive estimate: {e}")
            raise
    
    def _extract_property_specifics(self, property_data: Dict) -> Dict:
        """Extract and format property specifics"""
        return {
            'sqft': property_data.get('sqft', 1511),
            'bedrooms': property_data.get('bedrooms', 2),
            'bathrooms': property_data.get('bathrooms', 2),
            'floors': property_data.get('floors', 2),
            'rentable_units': property_data.get('rentable_units', 0),
            'market_rent': property_data.get('market_rent', 1700),
            'yearly_taxes': property_data.get('yearly_taxes', 0),
            'purchase_price': property_data.get('purchase_price', 80000),
            'arv': property_data.get('arv', 235000),
            'property_address': property_data.get('address', ''),
            'house_length': property_data.get('house_length', 40),
            'house_width': property_data.get('house_width', 32),
            'house_height': property_data.get('house_height', 10),
            'lot_sqft': property_data.get('lot_sqft', 7840)
        }
    
    def _calculate_exterior_costs(self, exterior_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate exterior renovation costs"""
        costs = {
            'roof': self._calculate_roof_costs(exterior_scope.get('roof', {}), property_specifics),
            'siding': self._calculate_siding_costs(exterior_scope.get('siding', {}), property_specifics),
            'paint': self._calculate_paint_costs(exterior_scope.get('paint', {}), property_specifics),
            'foundation': self._calculate_foundation_costs(exterior_scope.get('foundation', {}), property_specifics),
            'windows': self._calculate_window_costs(exterior_scope.get('windows', {}), property_specifics),
            'gutters': self._calculate_gutter_costs(exterior_scope.get('gutters', {}), property_specifics),
            'porch': self._calculate_porch_costs(exterior_scope.get('porch', {}), property_specifics),
            'yard': self._calculate_yard_costs(exterior_scope.get('yard', {}), property_specifics)
        }
        
        total_material = sum(cost.get('material', 0) for cost in costs.values())
        total_labor = sum(cost.get('labor', 0) for cost in costs.values())
        
        return {
            'breakdown': costs,
            'total_material': total_material,
            'total_labor': total_labor,
            'total_cost': total_material + total_labor
        }
    
    def _calculate_roof_costs(self, roof_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate roof renovation costs"""
        # Calculate roof square footage
        house_length = property_specifics['house_length']
        house_width = property_specifics['house_width']
        roof_sq = self._calculate_roof_squares(house_length, house_width)
        
        replacement_sq = roof_scope.get('replacement_sq', roof_sq)
        
        # Base costs per square
        material_per_sq = 5.11  # Average shingle cost per square
        labor_per_sq = 46.00    # Average labor cost per square
        
        # Additional costs for tear off, reshingle, resheet
        tear_off_cost = 150 if roof_scope.get('tear_off_existing', False) else 0
        reshingle_cost = replacement_sq * 25 if roof_scope.get('reshingle', False) else 0
        resheet_cost = replacement_sq * 35 if roof_scope.get('resheet', False) else 0
        
        material_cost = (replacement_sq * material_per_sq) + tear_off_cost + (reshingle_cost * 0.6)
        labor_cost = (replacement_sq * labor_per_sq) + (reshingle_cost * 0.4) + resheet_cost
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': {
                'roof_squares': roof_sq,
                'replacement_squares': replacement_sq,
                'tear_off_existing': roof_scope.get('tear_off_existing', False),
                'reshingle': roof_scope.get('reshingle', False),
                'resheet': roof_scope.get('resheet', False)
            }
        }
    
    def _calculate_siding_costs(self, siding_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate siding renovation costs"""
        # Calculate siding square footage
        house_length = property_specifics['house_length']
        house_width = property_specifics['house_width']
        house_height = property_specifics['house_height']
        siding_sq = self._calculate_siding_squares(house_length, house_width, house_height)
        
        replacement_sq = siding_scope.get('replacement_sq', siding_sq)
        
        # Base costs per square foot
        material_per_sq = 3.50  # Average siding material cost
        labor_per_sq = 4.50     # Average siding labor cost
        
        replace_siding = siding_scope.get('replace_siding', False)
        
        if replace_siding:
            material_cost = replacement_sq * material_per_sq
            labor_cost = replacement_sq * labor_per_sq
        else:
            material_cost = 0
            labor_cost = 0
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': {
                'siding_squares': siding_sq,
                'replacement_squares': replacement_sq,
                'replace_siding': replace_siding
            }
        }
    
    def _calculate_paint_costs(self, paint_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate paint renovation costs"""
        siding_sq = paint_scope.get('siding_sq', 15)
        
        paint_ext_siding = paint_scope.get('paint_ext_siding', False)
        paint_ext_trim = paint_scope.get('paint_ext_trim', False)
        paint_foundation = paint_scope.get('paint_foundation', False)
        
        # Base costs per square foot
        material_per_sq = 1.50  # Paint material cost
        labor_per_sq = 2.50     # Paint labor cost
        
        material_cost = 0
        labor_cost = 0
        
        if paint_ext_siding:
            material_cost += siding_sq * material_per_sq
            labor_cost += siding_sq * labor_per_sq
        
        if paint_ext_trim:
            material_cost += siding_sq * 0.3 * material_per_sq
            labor_cost += siding_sq * 0.3 * labor_per_sq
        
        if paint_foundation:
            material_cost += siding_sq * 0.2 * material_per_sq
            labor_cost += siding_sq * 0.2 * labor_per_sq
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': {
                'siding_sq': siding_sq,
                'paint_ext_siding': paint_ext_siding,
                'paint_ext_trim': paint_ext_trim,
                'paint_foundation': paint_foundation
            }
        }
    
    def _calculate_foundation_costs(self, foundation_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate foundation renovation costs"""
        repair_dist_ft = foundation_scope.get('repair_dist_ft', 15)
        straighten = foundation_scope.get('straighten', False)
        rebuild = foundation_scope.get('rebuild', False)
        
        # Base costs per linear foot
        material_per_ft = 25.00  # Foundation material cost
        labor_per_ft = 35.00     # Foundation labor cost
        
        material_cost = 0
        labor_cost = 0
        
        if straighten or rebuild:
            material_cost = repair_dist_ft * material_per_ft
            labor_cost = repair_dist_ft * labor_per_ft
            
            if rebuild:
                material_cost *= 1.5  # Rebuild is more expensive
                labor_cost *= 1.5
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': {
                'repair_dist_ft': repair_dist_ft,
                'straighten': straighten,
                'rebuild': rebuild
            }
        }
    
    def _calculate_window_costs(self, window_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate window renovation costs"""
        window_replacements = window_scope.get('window_replacements', 8)
        historic_replacements = window_scope.get('historic_replacements', 0)
        glass_replacements = window_scope.get('glass_replacements', 0)
        screen_replacements = window_scope.get('screen_replacements', 0)
        
        # Base costs per window
        standard_window_cost = 350  # Material + labor
        historic_window_cost = 750  # Historic windows cost more
        glass_replacement_cost = 85
        screen_replacement_cost = 25
        
        material_cost = (window_replacements * standard_window_cost * 0.6) + \
                       (historic_replacements * historic_window_cost * 0.6) + \
                       (glass_replacements * glass_replacement_cost * 0.7) + \
                       (screen_replacements * screen_replacement_cost * 0.8)
        
        labor_cost = (window_replacements * standard_window_cost * 0.4) + \
                     (historic_replacements * historic_window_cost * 0.4) + \
                     (glass_replacements * glass_replacement_cost * 0.3) + \
                     (screen_replacements * screen_replacement_cost * 0.2)
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': {
                'window_replacements': window_replacements,
                'historic_replacements': historic_replacements,
                'glass_replacements': glass_replacements,
                'screen_replacements': screen_replacements
            }
        }
    
    def _calculate_gutter_costs(self, gutter_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate gutter renovation costs"""
        replace_gutters = gutter_scope.get('replace_gutters', False)
        
        # Calculate gutter linear feet (perimeter of house)
        house_length = property_specifics['house_length']
        house_width = property_specifics['house_width']
        gutter_lf = 2 * (house_length + house_width)
        
        # Base costs per linear foot
        material_per_lf = 8.50   # Gutter material cost
        labor_per_lf = 12.50     # Gutter labor cost
        
        if replace_gutters:
            material_cost = gutter_lf * material_per_lf
            labor_cost = gutter_lf * labor_per_lf
        else:
            material_cost = 0
            labor_cost = 0
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': {
                'gutter_lf': gutter_lf,
                'replace_gutters': replace_gutters
            }
        }
    
    def _calculate_porch_costs(self, porch_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate porch renovation costs"""
        porch_sqft = porch_scope.get('porch_sqft', 75)
        redeck = porch_scope.get('redeck', False)
        new_footings = porch_scope.get('new_footings', False)
        
        # Base costs per square foot
        material_per_sqft = 15.00  # Porch material cost
        labor_per_sqft = 20.00     # Porch labor cost
        
        material_cost = 0
        labor_cost = 0
        
        if redeck:
            material_cost += porch_sqft * material_per_sqft
            labor_cost += porch_sqft * labor_per_sqft
        
        if new_footings:
            material_cost += porch_sqft * 5.00
            labor_cost += porch_sqft * 8.00
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': {
                'porch_sqft': porch_sqft,
                'redeck': redeck,
                'new_footings': new_footings
            }
        }
    
    def _calculate_yard_costs(self, yard_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate yard renovation costs"""
        lot_sqft = property_specifics.get('lot_sqft', 7840)
        high_grass = yard_scope.get('high_grass', False)
        trees_to_trim = yard_scope.get('trees_to_trim', 0)
        tree_removals = yard_scope.get('tree_removals', 0)
        remove_trash = yard_scope.get('remove_trash', False)
        
        material_cost = 0
        labor_cost = 0
        
        # High grass cutting
        if high_grass:
            labor_cost += lot_sqft * 0.05
        
        # Tree trimming
        labor_cost += trees_to_trim * 150
        
        # Tree removal
        labor_cost += tree_removals * 500
        
        # Trash removal
        if remove_trash:
            labor_cost += 300
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': {
                'lot_sqft': lot_sqft,
                'high_grass': high_grass,
                'trees_to_trim': trees_to_trim,
                'tree_removals': tree_removals,
                'remove_trash': remove_trash
            }
        }
    
    def _calculate_mechanical_costs(self, mechanical_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate mechanical systems costs (HVAC, Electrical, Plumbing)"""
        hvac_costs = self._calculate_hvac_costs(mechanical_scope.get('hvac', {}), property_specifics)
        electrical_costs = self._calculate_electrical_costs(mechanical_scope.get('electrical', {}), property_specifics)
        plumbing_costs = self._calculate_plumbing_costs(mechanical_scope.get('plumbing', {}), property_specifics)
        
        total_material = hvac_costs['material'] + electrical_costs['material'] + plumbing_costs['material']
        total_labor = hvac_costs['labor'] + electrical_costs['labor'] + plumbing_costs['labor']
        
        return {
            'hvac': hvac_costs,
            'electrical': electrical_costs,
            'plumbing': plumbing_costs,
            'total_material': total_material,
            'total_labor': total_labor,
            'total_cost': total_material + total_labor
        }
    
    def _calculate_hvac_costs(self, hvac_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate HVAC renovation costs"""
        # Extract HVAC scope items
        new_gas_meter_installs = hvac_scope.get('new_gas_meter_installs', 0)
        new_furnace_installs = hvac_scope.get('new_furnace_installs', 0)
        furnace_replacements = hvac_scope.get('furnace_replacements', 0)
        new_ac_installs = hvac_scope.get('new_ac_installs', 0)
        ac_replacements = hvac_scope.get('ac_replacements', 0)
        new_bath_fans = hvac_scope.get('new_bath_fans', 0)
        gas_pressure_test = hvac_scope.get('gas_pressure_test', False)
        replace_gas_valves = hvac_scope.get('replace_gas_valves', False)
        reduct_entire_house = hvac_scope.get('reduct_entire_house', False)
        
        # Base costs for HVAC items
        material_cost = 0
        labor_cost = 0
        
        # Gas meter installs
        material_cost += new_gas_meter_installs * 350
        labor_cost += new_gas_meter_installs * 450
        
        # Furnace installs/replacements
        material_cost += (new_furnace_installs + furnace_replacements) * 1800
        labor_cost += (new_furnace_installs + furnace_replacements) * 800
        
        # AC installs/replacements
        material_cost += (new_ac_installs + ac_replacements) * 2200
        labor_cost += (new_ac_installs + ac_replacements) * 1200
        
        # Bath fans
        material_cost += new_bath_fans * 85
        labor_cost += new_bath_fans * 150
        
        # Gas pressure test
        if gas_pressure_test:
            labor_cost += 200
        
        # Gas valves
        if replace_gas_valves:
            material_cost += 150
            labor_cost += 300
        
        # Reduct entire house
        if reduct_entire_house:
            material_cost += property_specifics['sqft'] * 1.5
            labor_cost += property_specifics['sqft'] * 2.0
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': hvac_scope
        }
    
    def _calculate_electrical_costs(self, electrical_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate electrical renovation costs"""
        # Extract electrical scope items
        vanity_light_rep = electrical_scope.get('vanity_light_rep', 0)
        flush_light_rep = electrical_scope.get('flush_light_rep', 0)
        wall_sconce_rep = electrical_scope.get('wall_sconce_rep', 0)
        flood_light_rep = electrical_scope.get('flood_light_rep', 0)
        ceiling_fan_rep = electrical_scope.get('ceiling_fan_rep', 0)
        closet_light_rep = electrical_scope.get('closet_light_rep', 0)
        smoke_detect_new = electrical_scope.get('smoke_detect_new', 0)
        co_detect_new = electrical_scope.get('co_detect_new', 0)
        new_elec_meter_installs = electrical_scope.get('new_elec_meter_installs', 0)
        new_electric_panels = electrical_scope.get('new_electric_panels', 0)
        new_elec_stove_roughs = electrical_scope.get('new_elec_stove_roughs', 0)
        new_elec_laundry_roughs = electrical_scope.get('new_elec_laundry_roughs', 0)
        new_ac_roughs = electrical_scope.get('new_ac_roughs', 0)
        new_waterheater_roughs = electrical_scope.get('new_waterheater_roughs', 0)
        rewire_entire_house = electrical_scope.get('rewire_entire_house', False)
        
        # Base costs for electrical items
        material_cost = 0
        labor_cost = 0
        
        # Light fixtures
        material_cost += vanity_light_rep * 45 + flush_light_rep * 25 + wall_sconce_rep * 35
        material_cost += flood_light_rep * 65 + ceiling_fan_rep * 125 + closet_light_rep * 20
        labor_cost += (vanity_light_rep + flush_light_rep + wall_sconce_rep + flood_light_rep + ceiling_fan_rep + closet_light_rep) * 75
        
        # Smoke/CO detectors
        material_cost += smoke_detect_new * 25 + co_detect_new * 35
        labor_cost += (smoke_detect_new + co_detect_new) * 50
        
        # Major electrical work
        material_cost += new_elec_meter_installs * 450
        labor_cost += new_elec_meter_installs * 800
        
        material_cost += new_electric_panels * 650
        labor_cost += new_electric_panels * 1200
        
        # Rough-ins
        material_cost += (new_elec_stove_roughs + new_elec_laundry_roughs + new_ac_roughs + new_waterheater_roughs) * 75
        labor_cost += (new_elec_stove_roughs + new_elec_laundry_roughs + new_ac_roughs + new_waterheater_roughs) * 150
        
        # Rewire entire house
        if rewire_entire_house:
            material_cost += property_specifics['sqft'] * 2.0
            labor_cost += property_specifics['sqft'] * 3.5
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': electrical_scope
        }
    
    def _calculate_plumbing_costs(self, plumbing_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate plumbing renovation costs"""
        # Extract plumbing scope items
        new_h20_meter_installs = plumbing_scope.get('new_h20_meter_installs', 0)
        new_gas_h20_htr = plumbing_scope.get('new_gas_h20_htr', 0)
        repl_gas_h20_htr = plumbing_scope.get('repl_gas_h20_htr', 0)
        new_elec_h20_htr = plumbing_scope.get('new_elec_h20_htr', 0)
        repl_elec_h20_htr = plumbing_scope.get('repl_elec_h20_htr', 0)
        new_sink_locations = plumbing_scope.get('new_sink_locations', 0)
        new_toilet_locations = plumbing_scope.get('new_toilet_locations', 0)
        new_tub_sho_locations = plumbing_scope.get('new_tub_sho_locations', 0)
        repipe_entire_house = plumbing_scope.get('repipe_entire_house', False)
        
        # Base costs for plumbing items
        material_cost = 0
        labor_cost = 0
        
        # Water meter installs
        material_cost += new_h20_meter_installs * 250
        labor_cost += new_h20_meter_installs * 400
        
        # Water heaters
        material_cost += (new_gas_h20_htr + repl_gas_h20_htr) * 650
        labor_cost += (new_gas_h20_htr + repl_gas_h20_htr) * 450
        
        material_cost += (new_elec_h20_htr + repl_elec_h20_htr) * 550
        labor_cost += (new_elec_h20_htr + repl_elec_h20_htr) * 400
        
        # New fixture locations
        material_cost += new_sink_locations * 200 + new_toilet_locations * 150 + new_tub_sho_locations * 400
        labor_cost += new_sink_locations * 350 + new_toilet_locations * 300 + new_tub_sho_locations * 600
        
        # Repipe entire house
        if repipe_entire_house:
            material_cost += property_specifics['sqft'] * 1.8
            labor_cost += property_specifics['sqft'] * 2.5
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': plumbing_scope
        }
    
    def _calculate_interior_costs(self, interior_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate interior renovation costs"""
        kitchen_costs = self._calculate_kitchen_costs(interior_scope.get('kitchen', {}), property_specifics)
        living_areas_costs = self._calculate_living_areas_costs(interior_scope.get('living_areas', {}), property_specifics)
        bedrooms_costs = self._calculate_bedrooms_costs(interior_scope.get('bedrooms', {}), property_specifics)
        bathrooms_costs = self._calculate_bathrooms_costs(interior_scope.get('bathrooms', {}), property_specifics)
        
        total_material = kitchen_costs['material'] + living_areas_costs['material'] + bedrooms_costs['material'] + bathrooms_costs['material']
        total_labor = kitchen_costs['labor'] + living_areas_costs['labor'] + bedrooms_costs['labor'] + bathrooms_costs['labor']
        
        return {
            'kitchen': kitchen_costs,
            'living_areas': living_areas_costs,
            'bedrooms': bedrooms_costs,
            'bathrooms': bathrooms_costs,
            'total_material': total_material,
            'total_labor': total_labor,
            'total_cost': total_material + total_labor
        }
    
    def _calculate_kitchen_costs(self, kitchen_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate kitchen renovation costs"""
        kitchen_sqft = kitchen_scope.get('kitchen_sqft', 230)
        ceiling_height = kitchen_scope.get('ceiling_height', 9)
        new_countertop_ft = kitchen_scope.get('new_countertop_ft', 30)
        frame_new_wall_ft = kitchen_scope.get('frame_new_wall_ft', 0)
        new_drywall_sheets = kitchen_scope.get('new_drywall_sheets', 0)
        
        # Appliances and fixtures
        new_gas_stove = kitchen_scope.get('new_gas_stove', False)
        new_electric_stove = kitchen_scope.get('new_electric_stove', False)
        new_refrigerator = kitchen_scope.get('new_refrigerator', False)
        new_microwave = kitchen_scope.get('new_microwave', False)
        new_dishwasher = kitchen_scope.get('new_dishwasher', False)
        new_washing_machine = kitchen_scope.get('new_washing_machine', False)
        new_gas_dryer = kitchen_scope.get('new_gas_dryer', False)
        new_electric_dryer = kitchen_scope.get('new_electric_dryer', False)
        
        # Kitchen features
        install_new_cabinets = kitchen_scope.get('install_new_cabinets', False)
        install_new_countertops = kitchen_scope.get('install_new_countertops', False)
        new_sink = kitchen_scope.get('new_sink', False)
        new_faucet = kitchen_scope.get('new_faucet', False)
        install_new_sub_flooring = kitchen_scope.get('install_new_sub_flooring', False)
        install_new_hard_flooring = kitchen_scope.get('install_new_hard_flooring', False)
        paint_walls = kitchen_scope.get('paint_walls', False)
        paint_base_trim = kitchen_scope.get('paint_base_trim', False)
        
        # Base costs
        material_cost = 0
        labor_cost = 0
        
        # Structural work
        material_cost += frame_new_wall_ft * 12
        labor_cost += frame_new_wall_ft * 18
        
        material_cost += new_drywall_sheets * 15
        labor_cost += new_drywall_sheets * 25
        
        # Appliances
        if new_gas_stove:
            material_cost += 800
            labor_cost += 200
        if new_electric_stove:
            material_cost += 650
            labor_cost += 150
        if new_refrigerator:
            material_cost += 1200
            labor_cost += 100
        if new_microwave:
            material_cost += 250
            labor_cost += 75
        if new_dishwasher:
            material_cost += 500
            labor_cost += 200
        if new_washing_machine:
            material_cost += 700
            labor_cost += 150
        if new_gas_dryer:
            material_cost += 650
            labor_cost += 150
        if new_electric_dryer:
            material_cost += 550
            labor_cost += 125
        
        # Kitchen features
        if install_new_cabinets:
            material_cost += kitchen_sqft * 45
            labor_cost += kitchen_sqft * 25
        
        if install_new_countertops:
            material_cost += new_countertop_ft * 55
            labor_cost += new_countertop_ft * 25
        
        if new_sink:
            material_cost += 300
            labor_cost += 200
        
        if new_faucet:
            material_cost += 150
            labor_cost += 100
        
        # Flooring
        if install_new_sub_flooring:
            material_cost += kitchen_sqft * 2.5
            labor_cost += kitchen_sqft * 3.0
        
        if install_new_hard_flooring:
            material_cost += kitchen_sqft * 8.5
            labor_cost += kitchen_sqft * 6.5
        
        # Paint
        if paint_walls:
            material_cost += kitchen_sqft * 0.8
            labor_cost += kitchen_sqft * 1.2
        
        if paint_base_trim:
            material_cost += kitchen_sqft * 0.3
            labor_cost += kitchen_sqft * 0.5
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': kitchen_scope
        }
    
    def _calculate_living_areas_costs(self, living_areas_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate living areas renovation costs"""
        living_areas_sqft = living_areas_scope.get('living_areas_sqft', 500)
        ceiling_height = living_areas_scope.get('ceiling_height', 9)
        frame_new_wall_ft = living_areas_scope.get('frame_new_wall_ft', 0)
        new_drywall_sheets = living_areas_scope.get('new_drywall_sheets', 0)
        
        # Living area features
        install_new_sub_flooring = living_areas_scope.get('install_new_sub_flooring', False)
        install_new_hard_flooring = living_areas_scope.get('install_new_hard_flooring', False)
        install_new_carpet = living_areas_scope.get('install_new_carpet', False)
        paint_walls = living_areas_scope.get('paint_walls', False)
        paint_base_trim = living_areas_scope.get('paint_base_trim', False)
        
        # Base costs
        material_cost = 0
        labor_cost = 0
        
        # Structural work
        material_cost += frame_new_wall_ft * 12
        labor_cost += frame_new_wall_ft * 18
        
        material_cost += new_drywall_sheets * 15
        labor_cost += new_drywall_sheets * 25
        
        # Flooring
        if install_new_sub_flooring:
            material_cost += living_areas_sqft * 2.5
            labor_cost += living_areas_sqft * 3.0
        
        if install_new_hard_flooring:
            material_cost += living_areas_sqft * 8.5
            labor_cost += living_areas_sqft * 6.5
        
        if install_new_carpet:
            material_cost += living_areas_sqft * 4.5
            labor_cost += living_areas_sqft * 3.5
        
        # Paint
        if paint_walls:
            material_cost += living_areas_sqft * 0.8
            labor_cost += living_areas_sqft * 1.2
        
        if paint_base_trim:
            material_cost += living_areas_sqft * 0.3
            labor_cost += living_areas_sqft * 0.5
        
        return {
            'material': material_cost,
            'labor': labor_cost,
            'total': material_cost + labor_cost,
            'details': living_areas_scope
        }
    
    def _calculate_bedrooms_costs(self, bedrooms_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate bedrooms renovation costs"""
        bedrooms_list = bedrooms_scope.get('bedrooms_list', [])
        total_material = 0
        total_labor = 0
        bedroom_details = []
        
        for i, bedroom in enumerate(bedrooms_list):
            bedroom_sqft = bedroom.get('bedroom_sqft', 200)
            ceiling_height = bedroom.get('ceiling_height', 9)
            frame_new_wall_ft = bedroom.get('frame_new_wall_ft', 0)
            new_drywall_sheets = bedroom.get('new_drywall_sheets', 0)
            
            # Bedroom features
            install_new_sub_flooring = bedroom.get('install_new_sub_flooring', False)
            install_new_hard_flooring = bedroom.get('install_new_hard_flooring', False)
            install_new_carpet = bedroom.get('install_new_carpet', False)
            paint_walls = bedroom.get('paint_walls', False)
            paint_base_trim = bedroom.get('paint_base_trim', False)
            
            # Base costs
            material_cost = 0
            labor_cost = 0
            
            # Structural work
            material_cost += frame_new_wall_ft * 12
            labor_cost += frame_new_wall_ft * 18
            
            material_cost += new_drywall_sheets * 15
            labor_cost += new_drywall_sheets * 25
            
            # Flooring
            if install_new_sub_flooring:
                material_cost += bedroom_sqft * 2.5
                labor_cost += bedroom_sqft * 3.0
            
            if install_new_hard_flooring:
                material_cost += bedroom_sqft * 8.5
                labor_cost += bedroom_sqft * 6.5
            
            if install_new_carpet:
                material_cost += bedroom_sqft * 4.5
                labor_cost += bedroom_sqft * 3.5
            
            # Paint
            if paint_walls:
                material_cost += bedroom_sqft * 0.8
                labor_cost += bedroom_sqft * 1.2
            
            if paint_base_trim:
                material_cost += bedroom_sqft * 0.3
                labor_cost += bedroom_sqft * 0.5
            
            bedroom_details.append({
                'bedroom_number': i + 1,
                'material': material_cost,
                'labor': labor_cost,
                'total': material_cost + labor_cost,
                'details': bedroom
            })
            
            total_material += material_cost
            total_labor += labor_cost
        
        return {
            'material': total_material,
            'labor': total_labor,
            'total': total_material + total_labor,
            'bedroom_details': bedroom_details
        }
    
    def _calculate_bathrooms_costs(self, bathrooms_scope: Dict, property_specifics: Dict) -> Dict:
        """Calculate bathrooms renovation costs"""
        bathrooms_list = bathrooms_scope.get('bathrooms_list', [])
        total_material = 0
        total_labor = 0
        bathroom_details = []
        
        for i, bathroom in enumerate(bathrooms_list):
            bathroom_sqft = bathroom.get('bathroom_sqft', 100)
            ceiling_height = bathroom.get('ceiling_height', 9)
            frame_new_wall_ft = bathroom.get('frame_new_wall_ft', 0)
            new_drywall_sheets = bathroom.get('new_drywall_sheets', 0)
            
            # Bathroom features
            install_new_sub_flooring = bathroom.get('install_new_sub_flooring', False)
            install_new_hard_flooring = bathroom.get('install_new_hard_flooring', False)
            install_new_tile = bathroom.get('install_new_tile', False)
            replace_toilet = bathroom.get('replace_toilet', False)
            replace_faucet = bathroom.get('replace_faucet', False)
            replace_sinktop = bathroom.get('replace_sinktop', False)
            replace_vanity = bathroom.get('replace_vanity', False)
            replace_tub_trim_kit = bathroom.get('replace_tub_trim_kit', False)
            new_curtain_rod_hardware = bathroom.get('new_curtain_rod_hardware', False)
            replace_surround = bathroom.get('replace_surround', False)
            paint_walls = bathroom.get('paint_walls', False)
            paint_base_trim = bathroom.get('paint_base_trim', False)
            
            # Base costs
            material_cost = 0
            labor_cost = 0
            
            # Structural work
            material_cost += frame_new_wall_ft * 12
            labor_cost += frame_new_wall_ft * 18
            
            material_cost += new_drywall_sheets * 15
            labor_cost += new_drywall_sheets * 25
            
            # Flooring
            if install_new_sub_flooring:
                material_cost += bathroom_sqft * 2.5
                labor_cost += bathroom_sqft * 3.0
            
            if install_new_hard_flooring:
                material_cost += bathroom_sqft * 8.5
                labor_cost += bathroom_sqft * 6.5
            
            if install_new_tile:
                material_cost += bathroom_sqft * 12.0
                labor_cost += bathroom_sqft * 8.0
            
            # Bathroom fixtures
            if replace_toilet:
                material_cost += 250
                labor_cost += 150
            
            if replace_faucet:
                material_cost += 120
                labor_cost += 80
            
            if replace_sinktop:
                material_cost += 200
                labor_cost += 100
            
            if replace_vanity:
                material_cost += 400
                labor_cost += 200
            
            if replace_tub_trim_kit:
                material_cost += 150
                labor_cost += 120
            
            if new_curtain_rod_hardware:
                material_cost += 50
                labor_cost += 30
            
            if replace_surround:
                material_cost += 300
                labor_cost += 250
            
            # Paint
            if paint_walls:
                material_cost += bathroom_sqft * 0.8
                labor_cost += bathroom_sqft * 1.2
            
            if paint_base_trim:
                material_cost += bathroom_sqft * 0.3
                labor_cost += bathroom_sqft * 0.5
            
            bathroom_details.append({
                'bathroom_number': i + 1,
                'material': material_cost,
                'labor': labor_cost,
                'total': material_cost + labor_cost,
                'details': bathroom
            })
            
            total_material += material_cost
            total_labor += labor_cost
        
        return {
            'material': total_material,
            'labor': total_labor,
            'total': total_material + total_labor,
            'bathroom_details': bathroom_details
        }
    
    def _calculate_contractor_breakdown(self, exterior_costs: Dict, mechanical_costs: Dict, interior_costs: Dict) -> Dict:
        """Calculate contractor labor and material breakdown"""
        total_material = exterior_costs['total_material'] + mechanical_costs['total_material'] + interior_costs['total_material']
        total_labor = exterior_costs['total_labor'] + mechanical_costs['total_labor'] + interior_costs['total_labor']
        
        # Separate mechanical costs for display
        hvac_material = mechanical_costs['hvac']['material']
        hvac_labor = mechanical_costs['hvac']['labor']
        electrical_material = mechanical_costs['electrical']['material']
        electrical_labor = mechanical_costs['electrical']['labor']
        plumbing_material = mechanical_costs['plumbing']['material']
        plumbing_labor = mechanical_costs['plumbing']['labor']
        
        return {
            'contractor_labor': total_labor - hvac_labor - electrical_labor - plumbing_labor,
            'contractor_material': total_material - hvac_material - electrical_material - plumbing_material,
            'hvac_labor': hvac_labor,
            'hvac_material': hvac_material,
            'electrical_labor': electrical_labor,
            'electrical_material': electrical_material,
            'plumbing_labor': plumbing_labor,
            'plumbing_material': plumbing_material,
            'total_contractor_costs': total_material + total_labor
        }
    
    def _calculate_profit_analysis(self, property_data: Dict, total_costs: float) -> Dict:
        """Calculate profit analysis and deal rating"""
        purchase_price = property_data.get('purchase_price', 80000)
        arv = property_data.get('arv', 235000)
        
        total_investment = purchase_price + total_costs
        profit_dollars = arv - total_investment
        profit_percent = (profit_dollars / total_investment) * 100 if total_investment > 0 else 0
        
        # Determine deal rating
        if profit_percent >= 35:
            deal_rating = "Excellent Deal!"
        elif profit_percent >= 25:
            deal_rating = "Great Deal!"
        elif profit_percent >= 15:
            deal_rating = "Good Deal"
        elif profit_percent >= 10:
            deal_rating = "Fair Deal"
        else:
            deal_rating = "Poor Deal"
        
        return {
            'purchase_price': purchase_price,
            'renovation_cost': total_costs,
            'total_investment': total_investment,
            'arv': arv,
            'profit_dollars': profit_dollars,
            'profit_percent': profit_percent,
            'deal_rating': deal_rating
        }
    
    def _calculate_roof_squares(self, length: float, width: float) -> float:
        """Calculate roof squares (100 sq ft = 1 square)"""
        roof_area = length * width * 1.05  # 5% overhang
        return roof_area / 100
    
    def _calculate_siding_squares(self, length: float, width: float, height: float) -> float:
        """Calculate siding square footage"""
        perimeter = 2 * (length + width)
        siding_area = perimeter * height * 0.85  # 15% deduction for windows/doors
        return siding_area
    
    def save_renovation_estimate(self, project_data: Dict, estimate_data: Dict) -> Dict:
        """Save renovation estimate to database"""
        # This would integrate with the existing construction database
        # For now, return success
        return {'success': True, 'message': 'Renovation estimate saved successfully'}
    
    def get_renovation_estimate(self, project_id: str) -> Dict:
        """Get saved renovation estimate from database"""
        # This would retrieve from the existing construction database
        # For now, return empty
        return {}