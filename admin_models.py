"""
Admin Dashboard Models
Extends existing models with admin-specific tracking
"""

from datetime import datetime
from sqlalchemy import func, Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from models import Base

class UserActivity(Base):
    """Track user activity and analytics"""
    __tablename__ = 'user_activity'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    action = Column(String(100), nullable=False)  # 'property_analysis', 'ai_tool_use', etc
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', backref='activities')

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
    status = Column(String(20), default='active')  # 'active', 'suspended'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', backref='affiliate')

class AffiliateReferral(Base):
    """Track individual referrals"""
    __tablename__ = 'affiliate_referrals'
    
    id = Column(Integer, primary_key=True)
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=False)
    referred_user_id = Column(String, ForeignKey('users.id'), nullable=False)
    conversion_date = Column(DateTime)
    revenue_generated = Column(Float, default=0.0)
    commission_earned = Column(Float, default=0.0)
    status = Column(String(20), default='pending')  # 'pending', 'converted', 'expired'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    affiliate = relationship('Affiliate', backref='referrals')
    referred_user = relationship('User', backref='referred_by')

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
    
    affiliate = relationship('Affiliate', backref='payouts')

class AdminAction(Base):
    """Audit log for admin actions"""
    __tablename__ = 'admin_actions'
    
    id = Column(Integer, primary_key=True)
    admin_user_id = Column(String, ForeignKey('users.id'), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50))  # 'user', 'team', 'deal', 'credit'
    target_id = Column(String(50))
    details = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    admin_user = relationship('User', backref='admin_actions')

class SupportTicket(Base):
    """Support tickets and issues"""
    __tablename__ = 'support_tickets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50))  # 'billing', 'technical', 'account', 'feature_request'
    priority = Column(String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    status = Column(String(20), default='open')  # 'open', 'in_progress', 'resolved', 'closed'
    assigned_to = Column(String, ForeignKey('users.id'))
    resolution = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    user = relationship('User', foreign_keys=[user_id], backref='tickets')
    assigned_admin = relationship('User', foreign_keys=[assigned_to], backref='assigned_tickets')

class APIError(Base):
    """Track API errors and failures"""
    __tablename__ = 'api_errors'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    endpoint = Column(String(100))
    error_type = Column(String(50))  # 'zillow_fail', 'redfin_fail', 'address_validation_fail'
    error_message = Column(Text)
    request_data = Column(JSON)
    stack_trace = Column(Text)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', backref='api_errors')