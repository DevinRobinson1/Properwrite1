"""
Database migration to add onboarding tables
"""

from billing_models import Base
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class OnboardingStep(Base):
    """Individual onboarding steps and tutorials"""
    __tablename__ = 'onboarding_steps'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    step_key = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    sequence_order = Column(Integer, default=0)
    
    # Tutorial content
    tutorial_content = Column(JSON)
    target_selector = Column(String(200))
    trigger_event = Column(String(50))
    
    # Completion tracking
    completion_required = Column(Boolean, default=False)
    completion_action = Column(String(100))
    
    # Timing and conditions
    delay_seconds = Column(Integer, default=0)
    prerequisites = Column(JSON)
    conditions = Column(JSON)
    
    # Content and styling
    position = Column(String(20), default='bottom')
    theme = Column(String(20), default='default')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class UserOnboardingProgress(Base):
    """Track user progress through onboarding steps"""
    __tablename__ = 'user_onboarding_progress'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    step_key = Column(String(100), nullable=False)
    
    # Progress tracking
    status = Column(String(20), default='not_started')
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Interaction data
    interactions = Column(JSON)
    time_spent = Column(Integer, default=0)
    
    # Feedback and personalization
    user_feedback = Column(JSON)
    personalization_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def create_onboarding_tables():
    """Create onboarding tables"""
    try:
        from sqlalchemy import create_engine
        import os
        
        # Database connection
        DATABASE_URL = os.environ.get("DATABASE_URL")
        engine = create_engine(DATABASE_URL)
        
        # Create tables
        OnboardingStep.__table__.create(engine, checkfirst=True)
        UserOnboardingProgress.__table__.create(engine, checkfirst=True)
        
        print("✓ Onboarding tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating onboarding tables: {e}")
        return False

if __name__ == "__main__":
    # Import the app to initialize database
    from app_upgraded import app
    
    with app.app_context():
        create_onboarding_tables()