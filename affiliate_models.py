"""
Affiliate Management Database Models
Comprehensive models for tracking affiliates, promo codes, and revenue attribution
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text, Enum, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class AffiliateStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

class PromoCodeType(enum.Enum):
    PERCENTAGE_DISCOUNT = "percentage_discount"
    CREDIT_PACK = "credit_pack"
    TEAM_BONUS = "team_bonus"

class PayoutStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"

class Affiliate(Base):
    """Track affiliate partners and their performance"""
    __tablename__ = 'affiliates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(36), nullable=True)  # Optional link to user account
    
    # Basic Info
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    company = Column(String(255))
    website = Column(String(500))
    
    # Commission Settings
    commission_rate = Column(Float, default=0.30)  # 30% default
    tier = Column(String(50), default='standard')  # standard, elite, premium
    
    # Status
    status = Column(Enum(AffiliateStatus), default=AffiliateStatus.PENDING)
    approved_at = Column(DateTime(timezone=True))
    approved_by = Column(String(36), nullable=True)  # Reference to users.id but no FK constraint
    
    # Payout Settings
    payout_method = Column(String(50))  # paypal, bitcoin, stripe_connect
    payout_details = Column(JSON)  # encrypted payment details
    minimum_payout = Column(Float, default=100.0)
    
    # Stats (denormalized for performance)
    total_referrals = Column(Integer, default=0)
    active_referrals = Column(Integer, default=0)
    total_revenue_generated = Column(Float, default=0.0)
    total_commissions_earned = Column(Float, default=0.0)
    total_commissions_paid = Column(Float, default=0.0)
    
    # Metadata
    notes = Column(Text)
    tags = Column(JSON)  # ['youtube', 'real_estate_pro', 'educator']
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_affiliates_status', 'status'),
        Index('idx_affiliates_created_at', 'created_at'),
    )

class PromoCode(Base):
    """Promotional codes for discounts, credits, and bonuses"""
    __tablename__ = 'promo_codes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    type = Column(Enum(PromoCodeType), nullable=False)
    
    # Ownership
    affiliate_id = Column(String(36), nullable=True)  # Reference to affiliates.id
    created_by = Column(String(36), nullable=True)  # Reference to users.id
    
    # Value Settings
    discount_percentage = Column(Float)  # For PERCENTAGE_DISCOUNT
    credit_amount = Column(Integer)  # For CREDIT_PACK
    bonus_seats = Column(Integer)  # For TEAM_BONUS
    
    # Application Rules
    applies_to_plans = Column(JSON)  # ['individual', 'pro', 'team5', 'growth10']
    first_month_only = Column(Boolean, default=True)
    stackable = Column(Boolean, default=False)
    
    # Limits
    max_uses = Column(Integer)  # null = unlimited
    uses_count = Column(Integer, default=0)
    max_uses_per_user = Column(Integer, default=1)
    
    # Validity
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Tracking
    campaign_name = Column(String(255))
    tracking_tags = Column(JSON)  # ['instagram', 'july_promo', 'influencer']
    
    # Stats
    total_redemptions = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_promo_codes_code', 'code'),
        Index('idx_promo_codes_affiliate_id', 'affiliate_id'),
        Index('idx_promo_codes_valid_until', 'valid_until'),
        Index('idx_promo_codes_is_active', 'is_active'),
    )

class PromoCodeRedemption(Base):
    """Track promo code usage"""
    __tablename__ = 'promo_code_redemptions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    promo_code_id = Column(String(36), nullable=False)  # Reference to promo_codes.id
    user_id = Column(String(36), nullable=False)  # Reference to users.id
    team_id = Column(String(36), nullable=True)  # Reference to teams.id
    
    # Redemption Details
    stripe_payment_id = Column(String(255))
    discount_applied = Column(Float)
    credits_granted = Column(Integer)
    seats_granted = Column(Integer)
    
    # Attribution
    referrer_url = Column(Text)
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    
    redeemed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_redemptions_promo_code_id', 'promo_code_id'),
        Index('idx_redemptions_user_id', 'user_id'),
        Index('idx_redemptions_redeemed_at', 'redeemed_at'),
        UniqueConstraint('promo_code_id', 'user_id', name='unique_user_promo_redemption'),
    )

class AffiliateReferral(Base):
    """Track users referred by affiliates"""
    __tablename__ = 'affiliate_referrals'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    affiliate_id = Column(String(36), nullable=False)  # Reference to affiliates.id
    user_id = Column(String(36), nullable=False)  # Reference to users.id
    team_id = Column(String(36), nullable=True)  # Reference to teams.id
    
    # Attribution
    promo_code_id = Column(String(36), nullable=True)  # Reference to promo_codes.id
    referral_source = Column(String(100))  # direct_link, promo_code, email
    landing_page = Column(Text)
    
    # User Status
    user_status = Column(String(50))  # trial, active, churned
    converted_at = Column(DateTime(timezone=True))
    churned_at = Column(DateTime(timezone=True))
    
    # Revenue Tracking
    total_revenue = Column(Float, default=0.0)
    lifetime_value = Column(Float, default=0.0)
    months_active = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_referrals_affiliate_id', 'affiliate_id'),
        Index('idx_referrals_user_id', 'user_id'),
        Index('idx_referrals_created_at', 'created_at'),
        UniqueConstraint('user_id', name='unique_user_referral'),
    )

class AffiliatePayout(Base):
    """Track commission payouts to affiliates"""
    __tablename__ = 'affiliate_payouts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    affiliate_id = Column(String(36), nullable=False)  # Reference to affiliates.id
    
    # Payout Details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    method = Column(String(50))  # paypal, bitcoin, stripe_connect
    
    # Transaction Info
    transaction_id = Column(String(255))
    transaction_details = Column(JSON)
    
    # Period Coverage
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    
    # Status
    status = Column(Enum(PayoutStatus), default=PayoutStatus.PENDING)
    initiated_by = Column(String(36), nullable=True)  # Reference to users.id
    
    # Timing
    initiated_at = Column(DateTime(timezone=True))
    processed_at = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    failure_reason = Column(Text)
    
    # Breakdown
    commission_breakdown = Column(JSON)  # detailed commission calculations
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_payouts_affiliate_id', 'affiliate_id'),
        Index('idx_payouts_status', 'status'),
        Index('idx_payouts_created_at', 'created_at'),
    )

class AffiliateActivity(Base):
    """Track detailed affiliate activity for analytics"""
    __tablename__ = 'affiliate_activity'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    affiliate_id = Column(String(36), nullable=False)  # Reference to affiliates.id
    
    # Activity Type
    activity_type = Column(String(50))  # click, signup, conversion, churn
    
    # Related Entities
    user_id = Column(String(36), nullable=True)  # Reference to users.id
    promo_code_id = Column(String(36), nullable=True)  # Reference to promo_codes.id
    
    # Activity Details
    details = Column(JSON)
    revenue_impact = Column(Float)
    
    # Tracking
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_activity_affiliate_id', 'affiliate_id'),
        Index('idx_activity_type', 'activity_type'),
        Index('idx_activity_occurred_at', 'occurred_at'),
    )