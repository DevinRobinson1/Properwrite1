"""
Affiliate Management Service
Handles affiliate operations, promo codes, and commission tracking
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import uuid
import random
import string
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from affiliate_models import (
    Affiliate, AffiliateStatus, PromoCode, PromoCodeType,
    PromoCodeRedemption, AffiliateReferral, AffiliatePayout,
    PayoutStatus, AffiliateActivity
)
import stripe
import openai
import os

logger = logging.getLogger(__name__)

class AffiliateService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.stripe_api_key = os.environ.get('STRIPE_SECRET_KEY')
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        
    # Affiliate Management
    def create_affiliate(self, data: Dict) -> Affiliate:
        """Create a new affiliate partner"""
        affiliate = Affiliate(
            name=data['name'],
            email=data['email'],
            company=data.get('company'),
            website=data.get('website'),
            commission_rate=data.get('commission_rate', 0.30),
            tier=data.get('tier', 'standard'),
            payout_method=data.get('payout_method'),
            payout_details=data.get('payout_details'),
            minimum_payout=data.get('minimum_payout', 100.0),
            notes=data.get('notes'),
            tags=data.get('tags', [])
        )
        
        self.db.add(affiliate)
        self.db.commit()
        
        # Log activity
        self._log_activity(affiliate.id, 'created', details={'source': 'admin'})
        
        return affiliate
    
    def approve_affiliate(self, affiliate_id: str, approved_by: str) -> Affiliate:
        """Approve a pending affiliate"""
        affiliate = self.db.query(Affiliate).filter_by(id=affiliate_id).first()
        if not affiliate:
            raise ValueError("Affiliate not found")
            
        affiliate.status = AffiliateStatus.ACTIVE
        affiliate.approved_at = datetime.utcnow()
        affiliate.approved_by = approved_by
        
        self.db.commit()
        
        # Log activity
        self._log_activity(affiliate.id, 'approved', details={'approved_by': approved_by})
        
        return affiliate
    
    def update_affiliate_stats(self, affiliate_id: str):
        """Update affiliate's denormalized stats"""
        # Count active referrals
        active_count = self.db.query(func.count(AffiliateReferral.id)).filter(
            AffiliateReferral.affiliate_id == affiliate_id,
            AffiliateReferral.user_status == 'active'
        ).scalar()
        
        # Count total referrals
        total_count = self.db.query(func.count(AffiliateReferral.id)).filter(
            AffiliateReferral.affiliate_id == affiliate_id
        ).scalar()
        
        # Calculate revenue
        revenue_data = self.db.query(
            func.sum(AffiliateReferral.total_revenue).label('total_revenue')
        ).filter(
            AffiliateReferral.affiliate_id == affiliate_id
        ).first()
        
        # Update affiliate
        affiliate = self.db.query(Affiliate).filter_by(id=affiliate_id).first()
        if affiliate:
            affiliate.active_referrals = active_count
            affiliate.total_referrals = total_count
            affiliate.total_revenue_generated = revenue_data.total_revenue or 0.0
            affiliate.total_commissions_earned = (revenue_data.total_revenue or 0.0) * affiliate.commission_rate
            
            self.db.commit()
    
    # Promo Code Management
    def create_promo_code(self, data: Dict) -> PromoCode:
        """Create a new promo code"""
        # Generate code if not provided
        if not data.get('code'):
            data['code'] = self._generate_promo_code(data.get('prefix', ''))
        
        promo_code = PromoCode(
            code=data['code'].upper(),
            type=PromoCodeType(data['type']),
            affiliate_id=data.get('affiliate_id'),
            created_by=data.get('created_by'),
            discount_percentage=data.get('discount_percentage'),
            credit_amount=data.get('credit_amount'),
            bonus_seats=data.get('bonus_seats'),
            applies_to_plans=data.get('applies_to_plans', ['all']),
            first_month_only=data.get('first_month_only', True),
            stackable=data.get('stackable', False),
            max_uses=data.get('max_uses'),
            max_uses_per_user=data.get('max_uses_per_user', 1),
            valid_from=data.get('valid_from', datetime.utcnow()),
            valid_until=data.get('valid_until'),
            campaign_name=data.get('campaign_name'),
            tracking_tags=data.get('tracking_tags', [])
        )
        
        self.db.add(promo_code)
        self.db.commit()
        
        return promo_code
    
    def validate_promo_code(self, code: str, user_id: str, plan: str) -> Tuple[bool, str, Optional[PromoCode]]:
        """Validate if a promo code can be used"""
        promo_code = self.db.query(PromoCode).filter_by(
            code=code.upper(),
            is_active=True
        ).first()
        
        if not promo_code:
            return False, "Invalid promo code", None
        
        # Check validity period
        now = datetime.now(timezone.utc)
        if promo_code.valid_until and now > promo_code.valid_until:
            return False, "Promo code has expired", None
        
        if promo_code.valid_from and now < promo_code.valid_from:
            return False, "Promo code is not yet active", None
        
        # Check usage limits
        if promo_code.max_uses and promo_code.uses_count >= promo_code.max_uses:
            return False, "Promo code usage limit reached", None
        
        # Check user usage
        user_redemptions = self.db.query(func.count(PromoCodeRedemption.id)).filter(
            PromoCodeRedemption.promo_code_id == promo_code.id,
            PromoCodeRedemption.user_id == user_id
        ).scalar()
        
        if user_redemptions >= promo_code.max_uses_per_user:
            return False, "You have already used this promo code", None
        
        # Check plan applicability
        if 'all' not in promo_code.applies_to_plans and plan not in promo_code.applies_to_plans:
            return False, f"Promo code not valid for {plan} plan", None
        
        return True, "Valid", promo_code
    
    def redeem_promo_code(self, code: str, user_id: str, team_id: Optional[str], 
                         plan: str, payment_data: Dict) -> PromoCodeRedemption:
        """Redeem a promo code"""
        is_valid, message, promo_code = self.validate_promo_code(code, user_id, plan)
        
        if not is_valid:
            raise ValueError(message)
        
        # Calculate values
        discount_applied = 0.0
        credits_granted = 0
        seats_granted = 0
        
        if promo_code.type == PromoCodeType.PERCENTAGE_DISCOUNT:
            discount_applied = payment_data.get('amount', 0) * (promo_code.discount_percentage / 100)
        elif promo_code.type == PromoCodeType.CREDIT_PACK:
            credits_granted = promo_code.credit_amount
        elif promo_code.type == PromoCodeType.TEAM_BONUS:
            seats_granted = promo_code.bonus_seats
        
        # Create redemption record
        redemption = PromoCodeRedemption(
            promo_code_id=promo_code.id,
            user_id=user_id,
            team_id=team_id,
            stripe_payment_id=payment_data.get('stripe_payment_id'),
            discount_applied=discount_applied,
            credits_granted=credits_granted,
            seats_granted=seats_granted,
            referrer_url=payment_data.get('referrer_url'),
            utm_source=payment_data.get('utm_source'),
            utm_medium=payment_data.get('utm_medium'),
            utm_campaign=payment_data.get('utm_campaign')
        )
        
        self.db.add(redemption)
        
        # Update promo code usage
        promo_code.uses_count += 1
        promo_code.total_redemptions += 1
        promo_code.total_revenue += payment_data.get('amount', 0) - discount_applied
        
        # Create referral if affiliate code
        if promo_code.affiliate_id:
            self._create_referral(promo_code.affiliate_id, user_id, team_id, promo_code.id)
        
        self.db.commit()
        
        return redemption
    
    def _generate_promo_code(self, prefix: str = '') -> str:
        """Generate a unique promo code"""
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        code = f"{prefix}{suffix}".upper()
        
        # Check uniqueness
        while self.db.query(PromoCode).filter_by(code=code).first():
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            code = f"{prefix}{suffix}".upper()
        
        return code
    
    # Referral Tracking
    def _create_referral(self, affiliate_id: str, user_id: str, team_id: Optional[str], 
                        promo_code_id: Optional[str]):
        """Create an affiliate referral record"""
        referral = AffiliateReferral(
            affiliate_id=affiliate_id,
            user_id=user_id,
            team_id=team_id,
            promo_code_id=promo_code_id,
            referral_source='promo_code' if promo_code_id else 'direct_link',
            user_status='trial'
        )
        
        self.db.add(referral)
        
        # Log activity
        self._log_activity(affiliate_id, 'signup', {
            'user_id': user_id,
            'source': 'promo_code' if promo_code_id else 'direct_link'
        })
    
    def track_referral_conversion(self, user_id: str, revenue: float):
        """Track when a referred user converts to paid"""
        referral = self.db.query(AffiliateReferral).filter_by(user_id=user_id).first()
        
        if referral and referral.user_status == 'trial':
            referral.user_status = 'active'
            referral.converted_at = datetime.utcnow()
            referral.total_revenue = revenue
            
            # Update affiliate stats
            self.update_affiliate_stats(referral.affiliate_id)
            
            # Log activity
            self._log_activity(referral.affiliate_id, 'conversion', {
                'user_id': user_id,
                'revenue': revenue
            }, revenue_impact=revenue)
            
            self.db.commit()
    
    def update_referral_revenue(self, user_id: str, additional_revenue: float):
        """Update revenue for a referred user"""
        referral = self.db.query(AffiliateReferral).filter_by(user_id=user_id).first()
        
        if referral:
            referral.total_revenue += additional_revenue
            referral.lifetime_value = referral.total_revenue
            referral.months_active = (datetime.utcnow() - referral.created_at).days // 30
            
            # Update affiliate stats
            self.update_affiliate_stats(referral.affiliate_id)
            
            self.db.commit()
    
    # Payout Management
    def calculate_pending_commissions(self, affiliate_id: str) -> float:
        """Calculate unpaid commissions for an affiliate"""
        affiliate = self.db.query(Affiliate).filter_by(id=affiliate_id).first()
        if not affiliate:
            return 0.0
        
        # Total earned - total paid
        pending = affiliate.total_commissions_earned - affiliate.total_commissions_paid
        
        return max(0, pending)
    
    def create_payout(self, affiliate_id: str, initiated_by: str) -> AffiliatePayout:
        """Create a payout for an affiliate"""
        affiliate = self.db.query(Affiliate).filter_by(id=affiliate_id).first()
        if not affiliate:
            raise ValueError("Affiliate not found")
        
        pending_amount = self.calculate_pending_commissions(affiliate_id)
        
        if pending_amount < affiliate.minimum_payout:
            raise ValueError(f"Minimum payout amount is ${affiliate.minimum_payout}")
        
        # Get commission breakdown
        breakdown = self._get_commission_breakdown(affiliate_id)
        
        payout = AffiliatePayout(
            affiliate_id=affiliate_id,
            amount=pending_amount,
            method=affiliate.payout_method,
            period_start=breakdown['period_start'],
            period_end=breakdown['period_end'],
            initiated_by=initiated_by,
            initiated_at=datetime.utcnow(),
            commission_breakdown=breakdown['details']
        )
        
        self.db.add(payout)
        self.db.commit()
        
        # Process the payout based on method
        self._process_payout(payout, affiliate)
        
        return payout
    
    def _get_commission_breakdown(self, affiliate_id: str) -> Dict:
        """Get detailed commission breakdown"""
        # Get unpaid referral revenue
        last_payout = self.db.query(AffiliatePayout).filter(
            AffiliatePayout.affiliate_id == affiliate_id,
            AffiliatePayout.status == PayoutStatus.PAID
        ).order_by(AffiliatePayout.paid_at.desc()).first()
        
        period_start = last_payout.paid_at if last_payout else datetime(2020, 1, 1)
        period_end = datetime.utcnow()
        
        # Get referral revenue in period
        referrals = self.db.query(AffiliateReferral).filter(
            AffiliateReferral.affiliate_id == affiliate_id,
            AffiliateReferral.converted_at >= period_start,
            AffiliateReferral.converted_at <= period_end
        ).all()
        
        details = []
        for ref in referrals:
            details.append({
                'user_id': str(ref.user_id),
                'revenue': ref.total_revenue,
                'commission': ref.total_revenue * 0.30  # Use affiliate rate
            })
        
        return {
            'period_start': period_start,
            'period_end': period_end,
            'details': details
        }
    
    def _process_payout(self, payout: AffiliatePayout, affiliate: Affiliate):
        """Process the actual payout"""
        try:
            if payout.method == 'stripe_connect':
                # Process via Stripe Connect
                # Implementation depends on Stripe Connect setup
                pass
            elif payout.method == 'paypal':
                # Process via PayPal API
                # Implementation depends on PayPal integration
                pass
            elif payout.method == 'bitcoin':
                # Process via Bitcoin
                # Implementation depends on Bitcoin integration
                pass
            
            # Mark as paid (for now, just mark as processing)
            payout.status = PayoutStatus.PROCESSING
            payout.processed_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            payout.status = PayoutStatus.FAILED
            payout.failed_at = datetime.utcnow()
            payout.failure_reason = str(e)
            self.db.commit()
            raise
    
    # Analytics
    def get_affiliate_metrics(self, affiliate_id: str) -> Dict:
        """Get comprehensive metrics for an affiliate"""
        affiliate = self.db.query(Affiliate).filter_by(id=affiliate_id).first()
        if not affiliate:
            return {}
        
        # Get referral stats
        referral_stats = self.db.query(
            func.count(AffiliateReferral.id).label('total_referrals'),
            func.sum(func.case([(AffiliateReferral.user_status == 'active', 1)], else_=0)).label('active_users'),
            func.sum(AffiliateReferral.total_revenue).label('total_revenue'),
            func.avg(AffiliateReferral.lifetime_value).label('avg_ltv')
        ).filter(
            AffiliateReferral.affiliate_id == affiliate_id
        ).first()
        
        # Get promo code stats
        promo_stats = self.db.query(
            func.count(PromoCode.id).label('total_codes'),
            func.sum(PromoCode.total_redemptions).label('total_redemptions'),
            func.sum(PromoCode.total_revenue).label('promo_revenue')
        ).filter(
            PromoCode.affiliate_id == affiliate_id
        ).first()
        
        # Calculate conversion rate
        conversion_rate = 0
        if referral_stats.total_referrals > 0:
            conversion_rate = (referral_stats.active_users or 0) / referral_stats.total_referrals * 100
        
        return {
            'affiliate': {
                'id': str(affiliate.id),
                'name': affiliate.name,
                'email': affiliate.email,
                'commission_rate': affiliate.commission_rate,
                'tier': affiliate.tier
            },
            'referrals': {
                'total': referral_stats.total_referrals or 0,
                'active': referral_stats.active_users or 0,
                'conversion_rate': round(conversion_rate, 2),
                'total_revenue': referral_stats.total_revenue or 0,
                'avg_ltv': round(referral_stats.avg_ltv or 0, 2)
            },
            'promo_codes': {
                'total': promo_stats.total_codes or 0,
                'redemptions': promo_stats.total_redemptions or 0,
                'revenue': promo_stats.promo_revenue or 0
            },
            'commissions': {
                'earned': affiliate.total_commissions_earned,
                'paid': affiliate.total_commissions_paid,
                'pending': self.calculate_pending_commissions(affiliate_id)
            }
        }
    
    def get_top_affiliates(self, limit: int = 10, period_days: int = 30) -> List[Dict]:
        """Get top performing affiliates"""
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        results = self.db.query(
            Affiliate.id,
            Affiliate.name,
            Affiliate.email,
            func.sum(AffiliateReferral.total_revenue).label('period_revenue'),
            func.count(AffiliateReferral.id).label('period_referrals')
        ).join(
            AffiliateReferral, Affiliate.id == AffiliateReferral.affiliate_id
        ).filter(
            AffiliateReferral.created_at >= cutoff_date,
            Affiliate.status == AffiliateStatus.ACTIVE
        ).group_by(
            Affiliate.id, Affiliate.name, Affiliate.email
        ).order_by(
            func.sum(AffiliateReferral.total_revenue).desc()
        ).limit(limit).all()
        
        return [
            {
                'id': str(r.id),
                'name': r.name,
                'email': r.email,
                'period_revenue': r.period_revenue or 0,
                'period_referrals': r.period_referrals or 0
            }
            for r in results
        ]
    
    # Activity Logging
    def _log_activity(self, affiliate_id: str, activity_type: str, 
                     details: Dict = None, revenue_impact: float = None):
        """Log affiliate activity"""
        activity = AffiliateActivity(
            affiliate_id=affiliate_id,
            activity_type=activity_type,
            details=details or {},
            revenue_impact=revenue_impact
        )
        
        self.db.add(activity)
    
    # GPT-4o Integration
    def generate_affiliate_content(self, affiliate_id: str, content_type: str) -> str:
        """Use GPT-4o to generate affiliate marketing content"""
        affiliate = self.db.query(Affiliate).filter_by(id=affiliate_id).first()
        if not affiliate:
            return ""
        
        metrics = self.get_affiliate_metrics(affiliate_id)
        
        prompts = {
            'email_sequence': f"""
                Create a 3-email sequence for affiliate '{affiliate.name}' to promote ProperWrite.
                Their promo code is their main code.
                Their conversion rate is {metrics['referrals']['conversion_rate']}%.
                
                Email 1: Introduction and value proposition
                Email 2: Case study or success story
                Email 3: Limited time bonus or urgency
                
                Keep each email under 150 words. Use persuasive but authentic language.
            """,
            'social_caption': f"""
                Write 3 social media captions for affiliate '{affiliate.name}' to promote ProperWrite.
                Include their promo code naturally.
                Make them platform-agnostic but engaging.
                Each caption should be 50-100 words.
            """,
            'onboarding_guide': f"""
                Create a quickstart guide for new affiliate '{affiliate.name}'.
                Include:
                - How to access their dashboard
                - Best practices for promotion
                - Commission structure explanation
                - First steps checklist
                
                Keep it actionable and under 300 words.
            """
        }
        
        if content_type not in prompts:
            return ""
        
        try:
            openai.api_key = self.openai_api_key
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a marketing expert helping real estate professionals promote ProperWrite."},
                    {"role": "user", "content": prompts[content_type]}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"GPT-4o content generation failed: {str(e)}")
            return ""