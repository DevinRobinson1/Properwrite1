"""
Construction Service - Handles construction calculations and estimations
Based on Excel workbook logic for Fix & Flip and New Construction projects
"""

import logging
from typing import Dict, List, Optional
from construction_models import construction_db
import json

class ConstructionService:
    def __init__(self):
        self.db = construction_db
    
    def get_catalog_items(self, project_type: str, trade: str = None) -> List[Dict]:
        """
        Get catalog items filtered by project type and optionally by trade
        
        Args:
            project_type: 'fix_flip' or 'new_construction'
            trade: Optional trade filter
            
        Returns:
            List of catalog items
        """
        try:
            return self.db.get_catalog_items(project_type, trade)
        except Exception as e:
            logging.error(f"Error getting catalog items: {e}")
            return []
    
    def calculate_fix_flip_estimate(self, line_items: List[Dict], multipliers: Dict) -> Dict:
        """
        Calculate fix and flip estimate based on line items and multipliers
        
        Args:
            line_items: List of {trade, sub_item, quantity, labor_cost, material_cost}
            multipliers: {overhead_percent, contingency_percent, gc_fee_percent}
        
        Returns:
            Dict with cost breakdown and totals
        """
        try:
            # Calculate hard costs from line items
            hard_costs = 0
            trade_totals = {}
            
            for item in line_items:
                item_total = (item['labor_cost'] + item['material_cost']) * item['quantity']
                hard_costs += item_total
                
                trade = item['trade']
                if trade not in trade_totals:
                    trade_totals[trade] = 0
                trade_totals[trade] += item_total
            
            # Apply multipliers
            overhead_percent = multipliers.get('overhead_percent', 15.0) / 100
            contingency_percent = multipliers.get('contingency_percent', 10.0) / 100
            gc_fee_percent = multipliers.get('gc_fee_percent', 10.0) / 100
            
            overhead_cost = hard_costs * overhead_percent
            contingency_cost = hard_costs * contingency_percent
            gc_fee = hard_costs * gc_fee_percent
            
            total_project_cost = hard_costs + overhead_cost + contingency_cost + gc_fee
            
            return {
                'hard_costs': hard_costs,
                'overhead_cost': overhead_cost,
                'contingency_cost': contingency_cost,
                'gc_fee': gc_fee,
                'total_project_cost': total_project_cost,
                'trade_totals': trade_totals,
                'line_items': line_items,
                'multipliers': multipliers
            }
            
        except Exception as e:
            logging.error(f"Error calculating fix flip estimate: {e}")
            return {}
    
    def calculate_new_construction_estimate(self, line_items: List[Dict], multipliers: Dict, 
                                          land_cost: float = 0, carry_costs: Dict = None) -> Dict:
        """
        Calculate new construction estimate with land and carry costs
        
        Args:
            line_items: Construction line items
            multipliers: Standard multipliers
            land_cost: Land acquisition cost
            carry_costs: {loan_percent, io_months, draw_schedule}
        
        Returns:
            Dict with comprehensive cost breakdown
        """
        try:
            # Calculate base construction costs
            base_estimate = self.calculate_fix_flip_estimate(line_items, multipliers)
            
            # Add land cost
            construction_cost = base_estimate.get('total_project_cost', 0)
            
            # Calculate carrying costs if provided
            total_carry_cost = 0
            if carry_costs:
                loan_percent = carry_costs.get('loan_percent', 80.0) / 100
                io_months = carry_costs.get('io_months', 12)
                interest_rate = carry_costs.get('interest_rate', 8.0) / 100
                
                # Estimate loan amount based on total project cost
                loan_amount = (construction_cost + land_cost) * loan_percent
                monthly_interest = loan_amount * (interest_rate / 12)
                total_carry_cost = monthly_interest * io_months
            
            total_project_cost = construction_cost + land_cost + total_carry_cost
            
            return {
                **base_estimate,
                'land_cost': land_cost,
                'carry_cost': total_carry_cost,
                'total_project_cost': total_project_cost,
                'construction_cost': construction_cost,
                'carry_cost_details': carry_costs or {}
            }
            
        except Exception as e:
            logging.error(f"Error calculating new construction estimate: {e}")
            return {}
    
    def search_catalog_items(self, project_type: str, search_term: str) -> List[Dict]:
        """Search catalog items by trade or sub_item"""
        try:
            all_items = self.db.get_catalog_items(project_type)
            
            if not search_term:
                return all_items
            
            search_term = search_term.lower()
            filtered_items = []
            
            for item in all_items:
                if (search_term in item['trade'].lower() or 
                    search_term in item['sub_item'].lower()):
                    filtered_items.append(item)
            
            return filtered_items
            
        except Exception as e:
            logging.error(f"Error searching catalog items: {e}")
            return []
    
    def get_trade_categories(self, project_type: str) -> List[str]:
        """Get all trade categories for autocomplete"""
        return self.db.get_trades(project_type)
    
    def save_project_estimate(self, user_id: int, project_name: str, project_type: str,
                            estimate_data: Dict, property_address: str = None) -> int:
        """Save project estimate to database"""
        try:
            project_id = self.db.create_project(
                user_id=user_id,
                project_name=project_name,
                project_type=project_type,
                property_address=property_address
            )
            
            if project_id:
                success = self.db.save_project_budget(project_id, estimate_data)
                if success:
                    return project_id
            
            return None
            
        except Exception as e:
            logging.error(f"Error saving project estimate: {e}")
            return None
    
    def generate_excel_export_data(self, project_id: int) -> Dict:
        """Generate data for Excel export"""
        try:
            project = self.db.get_project(project_id)
            if not project:
                return {}
            
            # Format data for Excel export
            export_data = {
                'project_info': {
                    'name': project['project_name'],
                    'type': project['project_type'],
                    'address': project['property_address'],
                    'sqft': project['property_sqft']
                },
                'costs': {
                    'hard_costs': project['hard_costs'],
                    'overhead_percent': project['overhead_percent'],
                    'contingency_percent': project['contingency_percent'],
                    'gc_fee_percent': project['gc_fee_percent'],
                    'land_cost': project['land_cost'],
                    'carry_cost': project['carry_cost'],
                    'total_budget': project['total_budget']
                },
                'line_items': project['project_data'].get('line_items', []),
                'trade_totals': project['project_data'].get('trade_totals', {})
            }
            
            return export_data
            
        except Exception as e:
            logging.error(f"Error generating Excel export data: {e}")
            return {}

# Global service instance
construction_service = ConstructionService()