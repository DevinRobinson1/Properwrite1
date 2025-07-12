"""
Interactive User Onboarding Toolkit System
Provides comprehensive guided tours, tutorials, and user engagement features
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import session, current_app
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class OnboardingStep(Base):
    """Individual onboarding steps and tutorials"""
    __tablename__ = 'onboarding_steps'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    step_key = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)  # welcome, property_analysis, calculations, advanced
    sequence_order = Column(Integer, default=0)
    
    # Tutorial content
    tutorial_content = Column(JSON)  # {type: 'tooltip|modal|highlight', content: {...}}
    target_selector = Column(String(200))  # CSS selector for element to highlight
    trigger_event = Column(String(50))  # page_load, click, form_submit, etc.
    
    # Completion tracking
    completion_required = Column(Boolean, default=False)
    completion_action = Column(String(100))  # specific action needed to complete
    
    # Timing and conditions
    delay_seconds = Column(Integer, default=0)
    prerequisites = Column(JSON)  # List of step_keys that must be completed first
    conditions = Column(JSON)  # Conditions for showing this step
    
    # Content and styling
    position = Column(String(20), default='bottom')  # top, bottom, left, right
    theme = Column(String(20), default='default')  # default, success, warning, info
    
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
    status = Column(String(20), default='not_started')  # not_started, in_progress, completed, skipped
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Interaction data
    interactions = Column(JSON)  # Track user interactions with this step
    time_spent = Column(Integer, default=0)  # Seconds spent on this step
    
    # Feedback and personalization
    user_feedback = Column(JSON)  # User ratings, comments, suggestions
    personalization_data = Column(JSON)  # Custom data for this user's experience
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OnboardingService:
    """Main service for managing interactive user onboarding"""
    
    def __init__(self):
        self.default_steps = self._get_default_onboarding_steps()
    
    def _get_default_onboarding_steps(self) -> List[Dict]:
        """Define default onboarding steps for the platform"""
        return [
            {
                "step_key": "welcome_tour",
                "title": "Welcome to Properwrite!",
                "description": "Let's take a quick tour of your real estate investment analysis platform",
                "category": "welcome",
                "sequence_order": 1,
                "tutorial_content": {
                    "type": "modal",
                    "content": {
                        "title": "Welcome to Properwrite!",
                        "body": "You're now part of the most advanced real estate investment analysis platform. Let's show you around so you can start analyzing deals like a pro.",
                        "features": [
                            "🏠 Advanced property analysis with real market data",
                            "💰 Multiple acquisition strategies (Wholesale, Installment, Subject-To, Seller Finance)",
                            "📊 Professional exit strategy analysis",
                            "🤖 AI-powered insights and recommendations",
                            "🎯 Deal submission and partnership opportunities"
                        ],
                        "cta_text": "Start Tour",
                        "skip_option": True
                    }
                },
                "trigger_event": "page_load",
                "delay_seconds": 2,
                "theme": "success"
            },
            {
                "step_key": "property_input_guide",
                "title": "Enter Your First Property",
                "description": "Start by entering a property address to analyze",
                "category": "property_analysis",
                "sequence_order": 2,
                "tutorial_content": {
                    "type": "tooltip",
                    "content": {
                        "title": "Start Here: Enter Property Address",
                        "body": "Type any property address to begin your analysis. We'll pull real market data from Zillow, Redfin, and other sources to give you accurate valuations.",
                        "tip": "Try: '123 Main St, Charlotte, NC' or use our autocomplete for best results"
                    }
                },
                "target_selector": "#property-address",
                "trigger_event": "focus",
                "position": "bottom",
                "prerequisites": ["welcome_tour"]
            },
            {
                "step_key": "property_data_explanation",
                "title": "Understanding Property Data",
                "description": "Learn what each property field means",
                "category": "property_analysis",
                "sequence_order": 3,
                "tutorial_content": {
                    "type": "highlight",
                    "content": {
                        "title": "Property Data Fields",
                        "body": "These fields show real market data we pulled for this property. You can edit any field to customize your analysis.",
                        "fields": {
                            "ARV": "After Repair Value - What the property will be worth after improvements",
                            "Repairs": "Estimated renovation costs",
                            "Rent": "Monthly rental income potential",
                            "Acquisitions Price": "Your maximum purchase price target"
                        }
                    }
                },
                "target_selector": ".property-header",
                "trigger_event": "data_loaded",
                "position": "bottom"
            },
            {
                "step_key": "strategy_tabs_intro",
                "title": "Explore Investment Strategies",
                "description": "Discover different ways to structure your deals",
                "category": "calculations",
                "sequence_order": 4,
                "tutorial_content": {
                    "type": "tooltip",
                    "content": {
                        "title": "Choose Your Strategy",
                        "body": "Each tab shows a different investment approach. Click through to see which strategy works best for your situation.",
                        "strategies": {
                            "Wholesale": "Quick assignment deals with minimal capital",
                            "Installment": "Seller financing with gradual payments",
                            "Subject-To": "Take over existing mortgage payments",
                            "Seller Finance": "Owner financing arrangements"
                        }
                    }
                },
                "target_selector": ".acquisition-tabs",
                "trigger_event": "property_analyzed",
                "position": "top"
            },
            {
                "step_key": "ai_assistant_intro",
                "title": "Meet Your AI Assistant",
                "description": "Get intelligent insights and recommendations",
                "category": "advanced",
                "sequence_order": 5,
                "tutorial_content": {
                    "type": "tooltip",
                    "content": {
                        "title": "AI-Powered Analysis",
                        "body": "Our AI assistant can help with objections, deal analysis, and listing creation. Try asking about seller motivations or market conditions.",
                        "examples": [
                            "Handle seller objections about price",
                            "Analyze deal profitability",
                            "Generate marketing copy for investors"
                        ]
                    }
                },
                "target_selector": ".ai-control-center",
                "trigger_event": "strategy_selected",
                "position": "left"
            },
            {
                "step_key": "dispositions_overview",
                "title": "Plan Your Exit Strategy",
                "description": "Learn how to sell or refinance your deals",
                "category": "advanced",
                "sequence_order": 6,
                "tutorial_content": {
                    "type": "modal",
                    "content": {
                        "title": "Dispositions: Your Exit Strategy",
                        "body": "Once you acquire a property, you need an exit plan. The Dispositions section shows you different ways to sell or refinance.",
                        "exit_options": [
                            "Cash Sale to Investors",
                            "MLS Listing",
                            "Subject-To Wrapping",
                            "Seller Finance Arrangements",
                            "Lease-Option Deals"
                        ],
                        "tip": "Each exit strategy has different profit potential and timelines"
                    }
                },
                "target_selector": ".dispositions-section",
                "trigger_event": "acquisitions_completed",
                "position": "center"
            },
            {
                "step_key": "dashboard_features",
                "title": "Explore Your Dashboard",
                "description": "Manage your account, team, and credits",
                "category": "advanced",
                "sequence_order": 7,
                "tutorial_content": {
                    "type": "tooltip",
                    "content": {
                        "title": "Your Command Center",
                        "body": "Access your dashboard to manage credits, invite team members, and track your analysis history.",
                        "features": [
                            "Credit management and usage tracking",
                            "Team collaboration tools",
                            "Analysis history and saved reports",
                            "Account settings and preferences"
                        ]
                    }
                },
                "target_selector": ".dashboard-button",
                "trigger_event": "manual",
                "position": "bottom"
            },
            {
                "step_key": "completion_celebration",
                "title": "You're Ready to Analyze Deals!",
                "description": "Congratulations on completing the onboarding tour",
                "category": "welcome",
                "sequence_order": 8,
                "tutorial_content": {
                    "type": "modal",
                    "content": {
                        "title": "🎉 Onboarding Complete!",
                        "body": "You're now ready to analyze real estate deals like a professional investor. Here's what you can do next:",
                        "next_steps": [
                            "Analyze your first property deal",
                            "Explore different investment strategies",
                            "Use AI assistance for market insights",
                            "Join our community resources",
                            "Consider upgrading for unlimited analysis"
                        ],
                        "cta_text": "Start Analyzing",
                        "celebration": True
                    }
                },
                "trigger_event": "tour_completed",
                "theme": "success"
            }
        ]
    
    def get_user_onboarding_status(self, user_id: str, db_session) -> Dict:
        """Get current onboarding status for a user"""
        try:
            # Get all progress records for this user
            progress_records = db_session.query(UserOnboardingProgress).filter_by(
                user_id=user_id
            ).all()
            
            # Calculate completion stats
            total_steps = len(self.default_steps)
            completed_steps = len([p for p in progress_records if p.status == 'completed'])
            
            # Get current step
            current_step = self._get_next_step(user_id, db_session)
            
            # Calculate progress percentage
            progress_percentage = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
            
            return {
                'is_onboarding_complete': progress_percentage >= 100,
                'progress_percentage': round(progress_percentage, 1),
                'total_steps': total_steps,
                'completed_steps': completed_steps,
                'current_step': current_step,
                'steps_remaining': total_steps - completed_steps
            }
        except Exception as e:
            current_app.logger.error(f"Error getting onboarding status: {e}")
            return {
                'is_onboarding_complete': False,
                'progress_percentage': 0,
                'total_steps': len(self.default_steps),
                'completed_steps': 0,
                'current_step': None,
                'steps_remaining': len(self.default_steps)
            }
    
    def _get_next_step(self, user_id: str, db_session) -> Optional[Dict]:
        """Get the next step user should see"""
        try:
            # Get completed steps
            completed_steps = db_session.query(UserOnboardingProgress).filter_by(
                user_id=user_id,
                status='completed'
            ).all()
            
            completed_keys = [p.step_key for p in completed_steps]
            
            # Find next step in sequence
            for step in sorted(self.default_steps, key=lambda x: x['sequence_order']):
                if step['step_key'] not in completed_keys:
                    # Check prerequisites
                    prerequisites = step.get('prerequisites', [])
                    if all(prereq in completed_keys for prereq in prerequisites):
                        return step
            
            return None
        except Exception as e:
            current_app.logger.error(f"Error getting next step: {e}")
            return None
    
    def start_onboarding_step(self, user_id: str, step_key: str, db_session) -> Dict:
        """Start a specific onboarding step"""
        try:
            # Get or create progress record
            progress = db_session.query(UserOnboardingProgress).filter_by(
                user_id=user_id,
                step_key=step_key
            ).first()
            
            if not progress:
                progress = UserOnboardingProgress(
                    user_id=user_id,
                    step_key=step_key
                )
                db_session.add(progress)
            
            # Update status
            progress.status = 'in_progress'
            progress.started_at = datetime.utcnow()
            progress.interactions = progress.interactions or {}
            
            db_session.commit()
            
            # Get step details
            step_details = next((s for s in self.default_steps if s['step_key'] == step_key), None)
            
            return {
                'success': True,
                'step': step_details,
                'progress': {
                    'status': progress.status,
                    'started_at': progress.started_at.isoformat() if progress.started_at else None
                }
            }
        except Exception as e:
            current_app.logger.error(f"Error starting onboarding step: {e}")
            return {'success': False, 'error': str(e)}
    
    def complete_onboarding_step(self, user_id: str, step_key: str, db_session, 
                                interaction_data: Dict = None) -> Dict:
        """Complete a specific onboarding step"""
        try:
            # Get progress record
            progress = db_session.query(UserOnboardingProgress).filter_by(
                user_id=user_id,
                step_key=step_key
            ).first()
            
            if not progress:
                # Create new progress record
                progress = UserOnboardingProgress(
                    user_id=user_id,
                    step_key=step_key,
                    started_at=datetime.utcnow()
                )
                db_session.add(progress)
            
            # Update completion
            progress.status = 'completed'
            progress.completed_at = datetime.utcnow()
            
            # Add interaction data
            if interaction_data:
                progress.interactions = progress.interactions or {}
                progress.interactions.update(interaction_data)
            
            # Calculate time spent
            if progress.started_at:
                time_spent = (datetime.utcnow() - progress.started_at).total_seconds()
                progress.time_spent = int(time_spent)
            
            db_session.commit()
            
            # Get updated status
            status = self.get_user_onboarding_status(user_id, db_session)
            
            return {
                'success': True,
                'step_completed': step_key,
                'onboarding_status': status,
                'next_step': self._get_next_step(user_id, db_session)
            }
        except Exception as e:
            current_app.logger.error(f"Error completing onboarding step: {e}")
            return {'success': False, 'error': str(e)}
    
    def skip_onboarding_step(self, user_id: str, step_key: str, db_session) -> Dict:
        """Skip a specific onboarding step"""
        try:
            # Get or create progress record
            progress = db_session.query(UserOnboardingProgress).filter_by(
                user_id=user_id,
                step_key=step_key
            ).first()
            
            if not progress:
                progress = UserOnboardingProgress(
                    user_id=user_id,
                    step_key=step_key
                )
                db_session.add(progress)
            
            # Update status
            progress.status = 'skipped'
            progress.completed_at = datetime.utcnow()
            
            db_session.commit()
            
            return {
                'success': True,
                'step_skipped': step_key,
                'next_step': self._get_next_step(user_id, db_session)
            }
        except Exception as e:
            current_app.logger.error(f"Error skipping onboarding step: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_onboarding_tutorial_content(self, step_key: str) -> Optional[Dict]:
        """Get tutorial content for a specific step"""
        step = next((s for s in self.default_steps if s['step_key'] == step_key), None)
        return step.get('tutorial_content') if step else None
    
    def record_user_interaction(self, user_id: str, step_key: str, interaction_type: str, 
                               interaction_data: Dict, db_session) -> bool:
        """Record user interaction with onboarding step"""
        try:
            progress = db_session.query(UserOnboardingProgress).filter_by(
                user_id=user_id,
                step_key=step_key
            ).first()
            
            if not progress:
                return False
            
            # Add interaction
            progress.interactions = progress.interactions or {}
            progress.interactions[interaction_type] = {
                'timestamp': datetime.utcnow().isoformat(),
                'data': interaction_data
            }
            
            db_session.commit()
            return True
        except Exception as e:
            current_app.logger.error(f"Error recording interaction: {e}")
            return False
    
    def get_personalized_recommendations(self, user_id: str, db_session) -> List[Dict]:
        """Get personalized recommendations based on user progress"""
        try:
            # Get user's completed steps and interactions
            progress_records = db_session.query(UserOnboardingProgress).filter_by(
                user_id=user_id
            ).all()
            
            recommendations = []
            
            # Analyze user behavior patterns
            has_analyzed_property = any(p.step_key == 'property_data_explanation' and p.status == 'completed' 
                                     for p in progress_records)
            has_used_ai = any(p.step_key == 'ai_assistant_intro' and p.status == 'completed' 
                            for p in progress_records)
            
            # Generate recommendations
            if not has_analyzed_property:
                recommendations.append({
                    'type': 'tutorial',
                    'title': 'Analyze Your First Property',
                    'description': 'Start with a property analysis to see how our platform works',
                    'action': 'start_property_analysis',
                    'priority': 'high'
                })
            
            if not has_used_ai:
                recommendations.append({
                    'type': 'feature',
                    'title': 'Try Our AI Assistant',
                    'description': 'Get intelligent insights and handle objections with AI',
                    'action': 'open_ai_assistant',
                    'priority': 'medium'
                })
            
            return recommendations
        except Exception as e:
            current_app.logger.error(f"Error getting recommendations: {e}")
            return []
    
    def reset_onboarding(self, user_id: str, db_session) -> bool:
        """Reset onboarding progress for a user"""
        try:
            # Delete all progress records
            db_session.query(UserOnboardingProgress).filter_by(
                user_id=user_id
            ).delete()
            
            db_session.commit()
            return True
        except Exception as e:
            current_app.logger.error(f"Error resetting onboarding: {e}")
            return False