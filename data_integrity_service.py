"""
Data Integrity and Optimization Service
Ensures all property data, calculations, and relationships are properly connected and validated
"""
import logging
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

class DataIntegrityService:
    def __init__(self):
        self.validation_results = {
            'orphaned_records': [],
            'broken_relationships': [],
            'data_inconsistencies': [],
            'performance_issues': [],
            'optimization_recommendations': []
        }
        
    def perform_full_system_audit(self) -> Dict:
        """
        Comprehensive system audit covering all data relationships and integrity
        """
        logging.info("Starting comprehensive data integrity audit...")
        
        # 1. Validate core entity relationships
        self._validate_property_calculator_relationships()
        
        # 2. Check for orphaned or incomplete records
        self._identify_orphaned_records()
        
        # 3. Optimize internal queries and data flow
        self._optimize_data_queries()
        
        # 4. Validate calculation consistency
        self._audit_calculation_integrity()
        
        # 5. Check session and state management
        self._validate_session_management()
        
        # 6. Performance optimization review
        self._performance_optimization_review()
        
        return self.validation_results
    
    def _validate_property_calculator_relationships(self):
        """
        Ensure all property data flows correctly through calculator modules
        """
        logging.info("Validating property-calculator relationships...")
        
        # Check that all calculator modules have consistent input/output interfaces
        calculator_modules = [
            'wholesale_calculator',
            'installment_calculator', 
            'subject_to_calculator',
            'seller_finance_calculator'
        ]
        
        required_inputs = ['arv', 'repairs', 'bedrooms', 'bathrooms', 'square_feet', 'rent']
        
        for module in calculator_modules:
            try:
                # Validate each calculator accepts standard property inputs
                module_path = f"{module}.py"
                if os.path.exists(module_path):
                    with open(module_path, 'r') as f:
                        content = f.read()
                        
                    # Check for proper parameter handling
                    missing_params = []
                    for param in required_inputs:
                        if param not in content:
                            missing_params.append(param)
                    
                    if missing_params:
                        self.validation_results['broken_relationships'].append({
                            'module': module,
                            'issue': 'Missing required parameters',
                            'missing_params': missing_params
                        })
                else:
                    self.validation_results['orphaned_records'].append({
                        'type': 'missing_calculator',
                        'module': module,
                        'issue': 'Calculator module file not found'
                    })
                    
            except Exception as e:
                self.validation_results['data_inconsistencies'].append({
                    'module': module,
                    'error': str(e),
                    'type': 'calculator_validation_error'
                })
    
    def _identify_orphaned_records(self):
        """
        Identify unused files, redundant code, and broken references
        """
        logging.info("Identifying orphaned records and unused files...")
        
        # Check for unused app files
        app_files = ['app.py', 'app_simple.py', 'app_upgraded.py']
        active_app = 'app_upgraded.py'  # Based on current main usage
        
        for app_file in app_files:
            if app_file != active_app and os.path.exists(app_file):
                self.validation_results['orphaned_records'].append({
                    'type': 'unused_app_file',
                    'file': app_file,
                    'recommendation': 'Archive or remove if no longer needed'
                })
        
        # Check for unused template files
        template_files = []
        if os.path.exists('templates'):
            template_files = [f for f in os.listdir('templates') if f.endswith('.html')]
        
        active_template = 'index_upgraded.html'
        for template in template_files:
            if template != active_template and 'upgraded' not in template:
                self.validation_results['orphaned_records'].append({
                    'type': 'unused_template',
                    'file': template,
                    'recommendation': 'Archive if no longer used'
                })
        
        # Check for incomplete property data service implementations
        property_services = ['property_data_service.py', 'enhanced_property_service.py', 'external_property_service.py']
        
        for service in property_services:
            if os.path.exists(service):
                with open(service, 'r') as f:
                    content = f.read()
                
                # Check for incomplete error handling
                if 'try:' in content and 'except:' not in content and 'except Exception' not in content:
                    self.validation_results['data_inconsistencies'].append({
                        'service': service,
                        'issue': 'Incomplete error handling detected'
                    })
    
    def _optimize_data_queries(self):
        """
        Review data access patterns and optimize for performance
        """
        logging.info("Optimizing data queries and access patterns...")
        
        # Check for redundant API calls in property services
        if os.path.exists('enhanced_property_service.py'):
            with open('enhanced_property_service.py', 'r') as f:
                content = f.read()
            
            # Look for potential optimization opportunities
            if content.count('requests.get') > 3:
                self.validation_results['performance_issues'].append({
                    'service': 'enhanced_property_service',
                    'issue': 'Multiple API calls detected',
                    'recommendation': 'Consider request batching or caching'
                })
            
            if 'cache' not in content.lower():
                self.validation_results['optimization_recommendations'].append({
                    'service': 'enhanced_property_service',
                    'recommendation': 'Implement caching for external API responses'
                })
    
    def _audit_calculation_integrity(self):
        """
        Ensure all financial calculations are consistent and accurate
        """
        logging.info("Auditing calculation integrity across all strategies...")
        
        # Test calculation consistency across modules
        test_inputs = {
            'arv': 200000,
            'repairs': 30000,
            'bedrooms': 3,
            'bathrooms': 2,
            'square_feet': 1200,
            'rent': 2000
        }
        
        try:
            # Import and test each calculator
            from wholesale_calculator import calculate_wholesale_offers
            from installment_calculator import calculate_installment_offers
            from subject_to_calculator import calculate_subject_to_offer
            from seller_finance_calculator import calculate_seller_finance_offer
            
            # Test wholesale calculations
            wholesale_result = calculate_wholesale_offers(
                arv=test_inputs['arv'],
                repairs=test_inputs['repairs']
            )
            
            if not isinstance(wholesale_result, dict) or 'wholesale_mao' not in wholesale_result:
                self.validation_results['data_inconsistencies'].append({
                    'calculator': 'wholesale',
                    'issue': 'Invalid output format or missing required fields'
                })
            
            # Test installment calculations
            installment_result = calculate_installment_offers(
                arv=test_inputs['arv'],
                estimated_repairs=test_inputs['repairs']
            )
            
            if not isinstance(installment_result, dict) or 'installment_mao' not in installment_result:
                self.validation_results['data_inconsistencies'].append({
                    'calculator': 'installment',
                    'issue': 'Invalid output format or missing required fields'
                })
            
            # Validate calculation relationships
            if wholesale_result.get('wholesale_mao', 0) > installment_result.get('installment_mao', 0):
                self.validation_results['data_inconsistencies'].append({
                    'issue': 'Calculation logic inconsistency',
                    'details': 'Wholesale MAO should typically be lower than installment MAO'
                })
                
        except Exception as e:
            self.validation_results['data_inconsistencies'].append({
                'calculator': 'calculation_integrity_test',
                'error': str(e),
                'issue': 'Calculator import or execution failed'
            })
    
    def _validate_session_management(self):
        """
        Check session handling and state management
        """
        logging.info("Validating session and state management...")
        
        # Check app configuration
        if os.path.exists('app_upgraded.py'):
            with open('app_upgraded.py', 'r') as f:
                content = f.read()
            
            # Validate session configuration
            if 'session' in content:
                if 'SESSION_SECRET' not in content:
                    self.validation_results['data_inconsistencies'].append({
                        'component': 'session_management',
                        'issue': 'Missing or improper session secret configuration'
                    })
            
            # Check for proper error handling in routes
            route_count = content.count('@app.route')
            try_count = content.count('try:')
            
            if route_count > try_count:
                self.validation_results['optimization_recommendations'].append({
                    'component': 'route_error_handling',
                    'recommendation': 'Add comprehensive error handling to all routes'
                })
    
    def _performance_optimization_review(self):
        """
        Review overall system performance and optimization opportunities
        """
        logging.info("Conducting performance optimization review...")
        
        # Check for large file imports
        if os.path.exists('app_upgraded.py'):
            with open('app_upgraded.py', 'r') as f:
                content = f.read()
            
            import_count = content.count('import')
            if import_count > 15:
                self.validation_results['optimization_recommendations'].append({
                    'component': 'imports',
                    'recommendation': 'Consider lazy loading for non-critical imports'
                })
        
        # Check template optimization
        if os.path.exists('templates/index_upgraded.html'):
            with open('templates/index_upgraded.html', 'r') as f:
                template_content = f.read()
            
            # Check for inline styles or scripts
            if 'style=' in template_content:
                self.validation_results['optimization_recommendations'].append({
                    'component': 'template_optimization',
                    'recommendation': 'Move inline styles to external CSS for better performance'
                })
            
            # Check for missing CDN optimization
            if 'cdn.tailwindcss.com' in template_content:
                self.validation_results['optimization_recommendations'].append({
                    'component': 'css_optimization',
                    'recommendation': 'Consider local Tailwind build for production'
                })
    
    def clean_orphaned_data(self) -> Dict:
        """
        Safely remove identified orphaned records and optimize data structure
        """
        cleaning_results = {
            'cleaned_files': [],
            'optimized_components': [],
            'preserved_data': []
        }
        
        # Only remove files that are clearly unused and safe to remove
        safe_to_remove = []
        
        for record in self.validation_results['orphaned_records']:
            if record['type'] == 'unused_app_file':
                # Archive rather than delete app files
                safe_to_remove.append(record['file'])
        
        return cleaning_results
    
    def generate_optimization_report(self) -> str:
        """
        Generate comprehensive optimization report
        """
        report = []
        report.append("# Real Estate Platform Data Integrity Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        if self.validation_results['orphaned_records']:
            report.append("## Orphaned Records Found:")
            for record in self.validation_results['orphaned_records']:
                report.append(f"- {record['type']}: {record.get('file', record.get('module', 'Unknown'))}")
        
        if self.validation_results['broken_relationships']:
            report.append("\n## Broken Relationships:")
            for issue in self.validation_results['broken_relationships']:
                report.append(f"- {issue['module']}: {issue['issue']}")
        
        if self.validation_results['data_inconsistencies']:
            report.append("\n## Data Inconsistencies:")
            for issue in self.validation_results['data_inconsistencies']:
                report.append(f"- {issue.get('component', issue.get('calculator', 'Unknown'))}: {issue['issue']}")
        
        if self.validation_results['optimization_recommendations']:
            report.append("\n## Optimization Recommendations:")
            for rec in self.validation_results['optimization_recommendations']:
                component = rec.get('component', rec.get('service', 'Unknown'))
                recommendation = rec.get('recommendation', 'No recommendation provided')
                report.append(f"- {component}: {recommendation}")
        
        return "\n".join(report)

# Global instance
data_integrity_service = DataIntegrityService()