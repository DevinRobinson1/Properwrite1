"""
Admin Dashboard Database Models
Comprehensive models for tracking billing events, app errors, and admin metrics
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Float, JSON, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class BillingEvent(Base):
    """Track all Stripe webhook events and billing transactions"""
    __tablename__ = 'billing_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stripe_event_id = Column(String(255), unique=True, nullable=False)  # Stripe's event ID for deduplication
    event_type = Column(String(100), nullable=False)  # customer.subscription.created, invoice.payment_succeeded, etc
    customer_id = Column(String(255))  # Stripe customer ID
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Financial data
    amount = Column(Integer)  # Amount in cents
    currency = Column(String(3), default='usd')
    status = Column(String(50))  # succeeded, failed, pending, etc
    description = Column(Text)
    
    # Subscription data
    subscription_id = Column(String(255))
    plan_id = Column(String(255))
    plan_name = Column(String(100))
    interval = Column(String(20))  # month, year
    
    # Metadata
    raw_data = Column(JSON)  # Full Stripe event object
    processed = Column(Boolean, default=False)
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_billing_events_stripe_event_id', 'stripe_event_id'),
        Index('idx_billing_events_team_id', 'team_id'),
        Index('idx_billing_events_created_at', 'created_at'),
        Index('idx_billing_events_event_type', 'event_type'),
    )

class AppError(Base):
    """Track application errors for debugging and support"""
    __tablename__ = 'app_errors'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'))
    
    error_type = Column(String(100), nullable=False)  # api_error, validation_error, etc
    error_code = Column(String(50))
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text)
    
    # Context
    endpoint = Column(String(255))
    method = Column(String(10))
    request_data = Column(JSON)
    response_data = Column(JSON)
    
    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_app_errors_user_id', 'user_id'),
        Index('idx_app_errors_created_at', 'created_at'),
        Index('idx_app_errors_error_type', 'error_type'),
        Index('idx_app_errors_resolved', 'resolved'),
    )

class AdminMetric(Base):
    """Pre-calculated metrics for dashboard performance"""
    __tablename__ = 'admin_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_date = Column(DateTime(timezone=True), nullable=False)
    metric_type = Column(String(50), nullable=False)  # daily_mrr, daily_active_users, etc
    
    # Metrics
    value = Column(Float, nullable=False)
    previous_value = Column(Float)
    change_percent = Column(Float)
    
    # Breakdown
    breakdown = Column(JSON)  # Additional data like plan distribution
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_admin_metrics_date_type', 'metric_date', 'metric_type'),
    )

class CreditLedger(Base):
    """Extended credit tracking with more detail than CreditLog"""
    __tablename__ = 'credit_ledger'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # purchase, consumption, grant, refund
    amount = Column(Integer, nullable=False)  # Positive for credits added, negative for consumed
    balance_after = Column(Integer, nullable=False)
    
    # Source
    source = Column(String(50))  # stripe_purchase, admin_grant, monthly_refresh, etc
    source_id = Column(String(255))  # Stripe payment ID, admin action ID, etc
    
    # Context
    description = Column(Text)
    meta_data = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_credit_ledger_team_id', 'team_id'),
        Index('idx_credit_ledger_created_at', 'created_at'),
        Index('idx_credit_ledger_transaction_type', 'transaction_type'),
    )

class JVDealSubmission(Base):
    """Track JV deal submissions"""
    __tablename__ = 'jv_deal_submissions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id = Column(String, ForeignKey('partners.id'), nullable=False)
    
    # Deal details
    property_address = Column(Text, nullable=False)
    property_city = Column(String(100))
    property_state = Column(String(2))
    property_zip = Column(String(10))
    
    # Financial data
    asking_price = Column(Float)
    arv = Column(Float)
    repair_estimate = Column(Float)
    suggested_offer = Column(Float)
    
    # Status tracking
    status = Column(String(20), default='pending')  # pending, approved, denied, withdrawn
    auto_evaluation = Column(String(20))  # approved, denied
    evaluation_reasons = Column(JSON)
    admin_notes = Column(Text)
    
    # Metadata
    submission_data = Column(JSON)  # Full form submission
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Indexes
    __table_args__ = (
        Index('idx_jv_deals_partner_id', 'partner_id'),
        Index('idx_jv_deals_status', 'status'),
        Index('idx_jv_deals_created_at', 'created_at'),
    )