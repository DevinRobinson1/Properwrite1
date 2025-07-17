#!/usr/bin/env python3
"""
Comprehensive Affiliate & Credit Code System Audit
Diagnoses and tests the complete promo code → credit application pipeline
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from billing_service import BillingService
from affiliate_service import AffiliateService
from affiliate_models import (
    Base, Affiliate, PromoCode, PromoCodeType, 
    AffiliateStatus, PromoCodeRedemption
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AffiliateSystemAudit:
    """Comprehensive audit of the affiliate and credit code system"""
    
    def __init__(self):
        self.database_url = os.environ.get("DATABASE_URL")
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "sslmode": "require",
                "connect_timeout": 10,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5
            }
        )
        self.session = sessionmaker(bind=self.engine)()
        self.billing_service = BillingService()
        self.affiliate_service = AffiliateService(self.session)
        self.audit_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
    
    def run_full_audit(self) -> Dict:
        """Run comprehensive audit of affiliate and credit system"""
        logger.info("🔍 Starting comprehensive affiliate & credit system audit...")
        
        # 1. Database Schema Audit
        self._audit_database_schema()
        
        # 2. Credit Code Application Tests
        self._test_credit_code_application()
        
        # 3. Affiliate Attribution Tests  
        self._test_affiliate_attribution()
        
        # 4. API Endpoint Tests
        self._test_api_endpoints()
        
        # 5. Integration Tests
        self._test_system_integration()
        
        # 6. Data Consistency Check
        self._check_data_consistency()
        
        # Generate final report
        self._generate_audit_report()
        
        return self.audit_results
    
    def _audit_database_schema(self):
        """Audit database schema and structure"""
        logger.info("📊 Auditing database schema...")
        
        try:
            # Check required tables exist
            required_tables = [
                'affiliates', 'promo_codes', 'promo_code_redemptions',
                'affiliate_referrals', 'affiliate_payouts', 'users', 'teams'
            ]
            
            existing_tables = self.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).fetchall()
            
            existing_table_names = [t[0] for t in existing_tables]
            
            for table in required_tables:
                if table in existing_table_names:
                    self._pass_test(f"Table {table} exists")
                else:
                    self._fail_test(f"Missing required table: {table}")
            
            # Check promo codes data
            promo_codes = self.session.execute(text("""
                SELECT code, type, credit_amount, discount_percentage 
                FROM promo_codes
            """)).fetchall()
            
            if promo_codes:
                self._pass_test(f"Found {len(promo_codes)} promo codes in database")
                
                # Check for specific hardcoded codes
                hardcoded_codes = {
                    'subto25': 25,
                    'CG40': 40,
                    'AFF001': 100,
                    'AFF002': 150,
                    'WELCOME50': 50
                }
                
                for code_data in promo_codes:
                    code, type_val, credit_amount, discount_percentage = code_data
                    if code in hardcoded_codes:
                        expected_amount = hardcoded_codes[code]
                        if credit_amount != expected_amount:
                            self._fail_test(f"Promo code {code} has incorrect credit amount: {credit_amount} (expected {expected_amount})")
                        else:
                            self._pass_test(f"Promo code {code} has correct credit amount: {credit_amount}")
            else:
                self._fail_test("No promo codes found in database")
                
        except Exception as e:
            self._fail_test(f"Database schema audit failed: {str(e)}")
    
    def _test_credit_code_application(self):
        """Test credit code application functionality"""
        logger.info("💳 Testing credit code application...")
        
        try:
            # Test hardcoded system in billing_service
            test_codes = ['subto25', 'CG40', 'AFF001', 'WELCOME50']
            
            for code in test_codes:
                bonus_credits = self.billing_service._apply_promo_code_bonus(code, 'pro')
                if bonus_credits > 0:
                    self._pass_test(f"Hardcoded promo code {code} returns {bonus_credits} credits")
                else:
                    self._fail_test(f"Hardcoded promo code {code} returns 0 credits")
            
            # Test invalid code
            invalid_bonus = self.billing_service._apply_promo_code_bonus('INVALID123', 'pro')
            if invalid_bonus == 0:
                self._pass_test("Invalid promo code correctly returns 0 credits")
            else:
                self._fail_test(f"Invalid promo code incorrectly returns {invalid_bonus} credits")
                
        except Exception as e:
            self._fail_test(f"Credit code application test failed: {str(e)}")
    
    def _test_affiliate_attribution(self):
        """Test affiliate attribution and referral tracking"""
        logger.info("🔗 Testing affiliate attribution...")
        
        try:
            # Check if affiliate redirect system is working
            from app_upgraded import app
            
            with app.test_client() as client:
                # Test affiliate redirect
                response = client.get('/ref/AFF001')
                if response.status_code == 302:  # Redirect
                    self._pass_test("Affiliate redirect endpoint works")
                else:
                    self._fail_test(f"Affiliate redirect endpoint failed: {response.status_code}")
                    
        except Exception as e:
            self._fail_test(f"Affiliate attribution test failed: {str(e)}")
    
    def _test_api_endpoints(self):
        """Test API endpoints for promo code management"""
        logger.info("🔌 Testing API endpoints...")
        
        try:
            # Test if validate promo code endpoint exists
            from affiliate_api import affiliate_api
            
            if affiliate_api:
                self._pass_test("Affiliate API blueprint exists")
            else:
                self._fail_test("Affiliate API blueprint missing")
                
        except Exception as e:
            self._fail_test(f"API endpoint test failed: {str(e)}")
    
    def _test_system_integration(self):
        """Test integration between billing and affiliate systems"""
        logger.info("🔄 Testing system integration...")
        
        try:
            # Check if promo codes are properly integrated
            promo_codes = self.session.query(PromoCode).all()
            
            if promo_codes:
                for code in promo_codes:
                    # Check if code exists in hardcoded system
                    hardcoded_bonus = self.billing_service._apply_promo_code_bonus(code.code, 'pro')
                    
                    if code.type == PromoCodeType.CREDIT_PACK:
                        if hardcoded_bonus > 0:
                            self._pass_test(f"Promo code {code.code} exists in both systems")
                        else:
                            self._fail_test(f"Promo code {code.code} missing from hardcoded system")
                    
        except Exception as e:
            self._fail_test(f"System integration test failed: {str(e)}")
    
    def _check_data_consistency(self):
        """Check data consistency across systems"""
        logger.info("📋 Checking data consistency...")
        
        try:
            # Check if hardcoded codes match database codes
            hardcoded_codes = {
                'AFF001': 100,
                'AFF002': 150,
                'AFF003': 200,
                'WELCOME50': 50,
                'STARTER100': 100,
                'subto25': 25,
                'CG40': 40
            }
            
            for code, expected_amount in hardcoded_codes.items():
                db_code = self.session.query(PromoCode).filter_by(code=code).first()
                
                if db_code:
                    if db_code.credit_amount == expected_amount:
                        self._pass_test(f"Code {code} has consistent credit amount across systems")
                    else:
                        self._fail_test(f"Code {code} has inconsistent credit amount: DB={db_code.credit_amount}, Hardcoded={expected_amount}")
                else:
                    self.audit_results['warnings'].append(f"Code {code} exists in hardcoded system but not in database")
                    
        except Exception as e:
            self._fail_test(f"Data consistency check failed: {str(e)}")
    
    def _generate_audit_report(self):
        """Generate comprehensive audit report"""
        logger.info("📄 Generating audit report...")
        
        report = {
            'audit_summary': {
                'timestamp': self.audit_results['timestamp'],
                'total_tests': self.audit_results['tests_passed'] + self.audit_results['tests_failed'],
                'tests_passed': self.audit_results['tests_passed'],
                'tests_failed': self.audit_results['tests_failed'],
                'success_rate': f"{(self.audit_results['tests_passed'] / max(1, self.audit_results['tests_passed'] + self.audit_results['tests_failed'])) * 100:.1f}%"
            },
            'critical_issues': self.audit_results['critical_issues'],
            'warnings': self.audit_results['warnings'],
            'recommendations': self.audit_results['recommendations']
        }
        
        # Save to file
        with open('affiliate_credit_audit_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Audit completed: {report['audit_summary']['tests_passed']} passed, {report['audit_summary']['tests_failed']} failed")
        
    def _pass_test(self, message: str):
        """Mark test as passed"""
        self.audit_results['tests_passed'] += 1
        logger.info(f"✅ {message}")
    
    def _fail_test(self, message: str):
        """Mark test as failed"""
        self.audit_results['tests_failed'] += 1
        self.audit_results['critical_issues'].append(message)
        logger.error(f"❌ {message}")
    
    def fix_promo_code_amounts(self):
        """Fix incorrect promo code credit amounts in database"""
        logger.info("🔧 Fixing promo code credit amounts...")
        
        correct_amounts = {
            'subto25': 25,
            'CG40': 40,
            'cg30': 30,
            'REILEGacy': 0,  # This is a percentage discount, not credit
            'F&F25': 25
        }
        
        for code, amount in correct_amounts.items():
            promo_code = self.session.query(PromoCode).filter_by(code=code).first()
            if promo_code and promo_code.type == PromoCodeType.CREDIT_PACK:
                if promo_code.credit_amount != amount:
                    promo_code.credit_amount = amount
                    logger.info(f"Fixed {code}: {promo_code.credit_amount} → {amount}")
        
        self.session.commit()
        logger.info("✅ Promo code amounts fixed")

def main():
    """Run the audit"""
    audit = AffiliateSystemAudit()
    
    # Run full audit
    results = audit.run_full_audit()
    
    # Fix issues found
    audit.fix_promo_code_amounts()
    
    # Print summary
    print("\n" + "="*60)
    print("AFFILIATE & CREDIT CODE SYSTEM AUDIT SUMMARY")
    print("="*60)
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    print(f"Critical Issues: {len(results['critical_issues'])}")
    print(f"Warnings: {len(results['warnings'])}")
    
    if results['critical_issues']:
        print("\nCRITICAL ISSUES:")
        for issue in results['critical_issues']:
            print(f"  ❌ {issue}")
    
    if results['warnings']:
        print("\nWARNINGS:")
        for warning in results['warnings']:
            print(f"  ⚠️  {warning}")
    
    return results

if __name__ == "__main__":
    main()