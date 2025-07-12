from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(UserMixin, Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Optional for simple email auth
    name = Column(String(255), nullable=True)
    credits = Column(Integer, default=4)  # 4 remaining credits after registration
    subscription_tier = Column(String(50), default='free')  # free, starter, pro, team5, growth10
    subscription_status = Column(String(50), default='active')  # active, trial, cancelled
    unlimited_credits = Column(Boolean, default=False)  # True for growth10 plan
    total_credits_used = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    def get_id(self):
        return str(self.id)
    
    def use_credit(self):
        """Use one credit and return True if successful"""
        # Growth10 plan has unlimited credits
        if self.unlimited_credits or self.subscription_tier == 'growth10':
            self.total_credits_used += 1
            return True
        
        if self.credits > 0:
            self.credits -= 1
            self.total_credits_used += 1
            return True
        return False
    
    def add_credits(self, amount):
        """Add credits to user account"""
        self.credits += amount

class CreditPurchase(Base):
    __tablename__ = 'credit_purchases'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    credits_purchased = Column(Integer, nullable=False)
    amount_paid = Column(Integer, nullable=False)  # in cents
    purchase_type = Column(String(50), default='credit_pack')  # credit_pack, subscription, comping
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CompingCredit(Base):
    __tablename__ = 'comping_credits'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    credits_granted = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    granted_by = Column(String(255), nullable=True)  # Admin who granted
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GuestUsage(Base):
    __tablename__ = 'guest_usage'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address = Column(String(45), nullable=False)
    session_id = Column(String(255), nullable=False)
    usage_count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())