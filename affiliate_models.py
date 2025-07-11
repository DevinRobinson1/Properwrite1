"""
Affiliate System Models
Database models for affiliate program and referral tracking
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from models import Base


class Affiliate(Base):
    """Affiliate tracking and management"""
    __tablename__ = 'affiliates'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False, unique=True)
    referral_code = Column(String(50), unique=True, nullable=False)
    tier = Column(String(20), default='basic')  # 'basic', 'premium', 'top'
    commission_rate = Column(Float, default=0.20)  # 20% default
    total_referrals = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    total_earnings = Column(Float, default=0.0)
    pending_payout = Column(Float, default=0.0)
    status = Column(String(20), default='active')  # 'active', 'suspended', 'inactive'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', backref='affiliate')
    referrals = relationship('AffiliateReferral', back_populates='affiliate')
    payouts = relationship('AffiliatePayout', back_populates='affiliate')


class AffiliateReferral(Base):
    """Track individual referrals"""
    __tablename__ = 'affiliate_referrals'
    
    id = Column(Integer, primary_key=True)
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=False)
    referred_user_id = Column(String, ForeignKey('users.id'), nullable=False)
    referral_code = Column(String(50), nullable=False)
    conversion_date = Column(DateTime)
    revenue_generated = Column(Float, default=0.0)
    commission_earned = Column(Float, default=0.0)
    status = Column(String(20), default='pending')  # 'pending', 'converted', 'expired'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    affiliate = relationship('Affiliate', back_populates='referrals')
    referred_user = relationship('User', foreign_keys=[referred_user_id], backref='referral_source')


class AffiliatePayout(Base):
    """Track affiliate payouts"""
    __tablename__ = 'affiliate_payouts'
    
    id = Column(Integer, primary_key=True)
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String(50))  # 'paypal', 'bank_transfer', 'stripe'
    transaction_id = Column(String(100))
    status = Column(String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    affiliate = relationship('Affiliate', back_populates='payouts')


class AffiliateClick(Base):
    """Track affiliate link clicks"""
    __tablename__ = 'affiliate_clicks'
    
    id = Column(Integer, primary_key=True)
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=False)
    referral_code = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    referrer_url = Column(String(500))
    landing_page = Column(String(500))
    converted = Column(Boolean, default=False)
    conversion_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    affiliate = relationship('Affiliate', backref='clicks')


class AffiliateCommission(Base):
    """Track commission calculations"""
    __tablename__ = 'affiliate_commissions'
    
    id = Column(Integer, primary_key=True)
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=False)
    referral_id = Column(Integer, ForeignKey('affiliate_referrals.id'), nullable=False)
    transaction_type = Column(String(50))  # 'subscription', 'credit_purchase', 'upgrade'
    transaction_amount = Column(Float, nullable=False)
    commission_rate = Column(Float, nullable=False)
    commission_amount = Column(Float, nullable=False)
    paid_out = Column(Boolean, default=False)
    payout_id = Column(Integer, ForeignKey('affiliate_payouts.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    affiliate = relationship('Affiliate', backref='commissions')
    referral = relationship('AffiliateReferral', backref='commissions')
    payout = relationship('AffiliatePayout', backref='commissions')