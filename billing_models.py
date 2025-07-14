"""
Billing and Subscription Models for Team Management
Implements PostgreSQL schema for subscription tiers, teams, and credit tracking
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, UUID, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    stripe_customer_id = Column(Text, unique=True)
    tier = Column(Text, nullable=False, default='starter')  # starter, pro, team5, growth10
    seats_max = Column(Integer, default=1)
    credit_balance = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    users = relationship("User", back_populates="team")
    credit_logs = relationship("CreditLog", back_populates="team")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'))
    role = Column(Text, nullable=False, default='analyst')  # owner, manager, analyst
    password_hash = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="users")

class CreditLog(Base):
    __tablename__ = 'credit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'), nullable=False)
    delta = Column(Integer, nullable=False)  # +100 on purchase, -1 on analysis
    reason = Column(Text, nullable=False)    # "pack-500", "analysis", "monthly-credit"
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="credit_logs")

class TeamInvite(Base):
    __tablename__ = 'team_invites'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'), nullable=False)
    email = Column(Text, nullable=False)
    role = Column(Text, nullable=False, default='analyst')
    token = Column(Text, nullable=False, unique=True)
    status = Column(Text, nullable=False, default='pending')  # pending, accepted, cancelled, expired
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Tier configuration
TIER_CONFIG = {
    'starter': {
        'seats_max': 1,
        'monthly_credits': 5,  # Free tier - 5 credits total on registration
        'price_monthly': 0,
        'stripe_lookup_key': 'starter_free'
    },
    'individual': {
        'seats_max': 1,
        'monthly_credits': 100,
        'price_monthly': 27,
        'stripe_lookup_key': 'individual_m'
    },
    'pro': {
        'seats_max': 1,
        'monthly_credits': 300,
        'price_monthly': 79,
        'stripe_lookup_key': 'pro_m'
    },
    'team5': {
        'seats_max': 5,
        'monthly_credits': 1000,
        'price_monthly': 199,
        'stripe_lookup_key': 'team5_m'
    },
    'growth10': {
        'seats_max': 10,
        'monthly_credits': -1,  # Unlimited
        'price_monthly': 399,
        'stripe_lookup_key': 'growth10_m'
    }
}

CREDIT_PACKS = {
    'pack-100': {
        'credits': 100,
        'price': 15,
        'stripe_lookup_key': 'credit_pack_100'
    },
    'pack-500': {
        'credits': 500,
        'price': 60,
        'stripe_lookup_key': 'credit_pack_500'
    },
    'pack-1000': {
        'credits': 1000,
        'price': 99,
        'stripe_lookup_key': 'credit_pack_1000'
    }
}