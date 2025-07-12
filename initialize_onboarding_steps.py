"""
Initialize default onboarding steps for new users
Creates a comprehensive onboarding experience for real estate investment platform
"""

import os
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker
import uuid
from datetime import datetime

# Database setup
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

class OnboardingStep(Base):
    """Individual onboarding steps and tutorials"""
    __tablename__ = 'onboarding_steps'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    step_key = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    sequence_order = Column(Integer, default=0)
    
    # Tutorial content and configuration
    tutorial_content = Column(JSON)
    target_selector = Column(String(200))
    trigger_event = Column(String(50))
    
    # Completion tracking
    completion_required = Column(Boolean, default=False)
    completion_action = Column(String(100))
    
    # Display configuration
    delay_seconds = Column(Integer, default=0)
    prerequisites = Column(JSON)
    conditions = Column(JSON)
    
    # UI styling
    position = Column(String(20), default='bottom')
    theme = Column(String(20), default='default')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

def initialize_onboarding_steps():
    """Initialize default onboarding steps"""
    session = SessionLocal()
    
    try:
        # Clear existing steps
        session.query(OnboardingStep).delete()
        
        # Define comprehensive onboarding steps
        steps = [
            {
                'step_key': 'welcome_intro',
                'title': 'Welcome to Properwrite!',
                'description': 'Let\'s get you started with a quick tour of our real estate investment platform.',
                'category': 'introduction',
                'sequence_order': 1,
                'tutorial_content': {
                    'type': 'modal',
                    'content': {
                        'title': '🎉 Welcome to Properwrite!',
                        'body': '''
                        <div class="text-center">
                            <div class="mb-4">
                                <img src="/static/properwrite-logo.png" alt="Properwrite" class="w-16 h-16 mx-auto mb-4">
                            </div>
                            <h3 class="text-xl font-bold mb-3">Ready to analyze your first property?</h3>
                            <p class="text-gray-600 mb-4">We'll walk you through the essential features to help you make informed real estate investment decisions.</p>
                            <div class="bg-blue-50 rounded-lg p-4 mb-4">
                                <h4 class="font-semibold text-blue-900 mb-2">What you'll learn:</h4>
                                <ul class="text-sm text-blue-800 space-y-1">
                                    <li>✓ How to enter property information</li>
                                    <li>✓ Understanding the four investment strategies</li>
                                    <li>✓ Reading property valuations and estimates</li>
                                    <li>✓ Using AI-powered insights</li>
                                    <li>✓ Managing your account and credits</li>
                                </ul>
                            </div>
                            <p class="text-sm text-gray-500">This tour takes about 3 minutes and can be skipped at any time.</p>
                        </div>
                        ''',
                        'actions': [
                            {'text': 'Start Tour', 'action': 'continue', 'style': 'primary'},
                            {'text': 'Skip for Now', 'action': 'skip', 'style': 'secondary'}
                        ]
                    }
                },
                'trigger_event': 'page_load',
                'delay_seconds': 3,
                'conditions': {'user_new': True}
            },
            {
                'step_key': 'property_address_input',
                'title': 'Enter Property Address',
                'description': 'Start by entering the property address you want to analyze.',
                'category': 'property_input',
                'sequence_order': 2,
                'tutorial_content': {
                    'type': 'tooltip',
                    'content': {
                        'title': 'Property Address',
                        'body': '''
                        <p class="mb-3">Enter the complete address of the property you want to analyze.</p>
                        <div class="bg-green-50 rounded-lg p-3 mb-3">
                            <h4 class="font-semibold text-green-900 mb-1">💡 Pro Tip:</h4>
                            <p class="text-sm text-green-800">Use our Google Places autocomplete to ensure accurate address formatting and automatic city/state/ZIP population.</p>
                        </div>
                        <p class="text-sm text-gray-600">Try entering: <code class="bg-gray-100 px-2 py-1 rounded">14303 Evening Flight Lane, Charlotte, NC</code></p>
                        '''
                    }
                },
                'target_selector': '#address',
                'trigger_event': 'focus',
                'completion_action': 'input_filled',
                'position': 'bottom'
            },
            {
                'step_key': 'property_details_header',
                'title': 'Property Information',
                'description': 'Review and adjust the key property details that drive your investment calculations.',
                'category': 'property_input',
                'sequence_order': 3,
                'tutorial_content': {
                    'type': 'highlight',
                    'content': {
                        'title': 'Property Information Header',
                        'body': '''
                        <p class="mb-3">These fields control all your investment calculations:</p>
                        <ul class="text-sm space-y-2 mb-3">
                            <li><strong>ARV:</strong> After Repair Value - what the property will be worth after renovations</li>
                            <li><strong>Repairs:</strong> Estimated renovation costs</li>
                            <li><strong>Rent:</strong> Monthly rental income potential</li>
                            <li><strong>Acquisitions Price:</strong> Your maximum purchase price</li>
                        </ul>
                        <div class="bg-blue-50 rounded-lg p-3">
                            <p class="text-sm text-blue-800">💡 These values are automatically populated from property data APIs, but you can edit them based on your local market knowledge.</p>
                        </div>
                        '''
                    }
                },
                'target_selector': '.property-header',
                'trigger_event': 'manual',
                'position': 'bottom'
            },
            {
                'step_key': 'investment_strategies_tabs',
                'title': 'Investment Strategies',
                'description': 'Explore the four main investment strategies available for analysis.',
                'category': 'strategies',
                'sequence_order': 4,
                'tutorial_content': {
                    'type': 'tooltip',
                    'content': {
                        'title': 'Four Investment Strategies',
                        'body': '''
                        <p class="mb-3">Choose from four proven real estate investment strategies:</p>
                        <div class="space-y-2 mb-3">
                            <div class="flex items-center space-x-2">
                                <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                                <span class="text-sm"><strong>Wholesale:</strong> Quick cash deals with assignment fees</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <div class="w-3 h-3 bg-orange-500 rounded-full"></div>
                                <span class="text-sm"><strong>Installment:</strong> Novation deals with seller financing</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <div class="w-3 h-3 bg-purple-500 rounded-full"></div>
                                <span class="text-sm"><strong>Subject-To:</strong> Take over existing mortgage payments</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <div class="w-3 h-3 bg-blue-500 rounded-full"></div>
                                <span class="text-sm"><strong>Seller Finance:</strong> Owner financing arrangements</span>
                            </div>
                        </div>
                        <p class="text-sm text-gray-600">Click on each tab to explore detailed calculations and analysis.</p>
                        '''
                    }
                },
                'target_selector': '.strategy-tabs',
                'trigger_event': 'manual',
                'position': 'top'
            },
            {
                'step_key': 'ai_control_center',
                'title': 'AI-Powered Insights',
                'description': 'Use our AI assistant for objection handling, deal analysis, and listing generation.',
                'category': 'ai_features',
                'sequence_order': 5,
                'tutorial_content': {
                    'type': 'tooltip',
                    'content': {
                        'title': 'AI Control Center',
                        'body': '''
                        <p class="mb-3">Access powerful AI tools for smarter investing:</p>
                        <div class="space-y-2 mb-3">
                            <div class="flex items-center space-x-2">
                                <i class="fas fa-brain text-blue-500"></i>
                                <span class="text-sm"><strong>Objection Handler:</strong> Get expert responses to seller objections</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <i class="fas fa-chart-line text-green-500"></i>
                                <span class="text-sm"><strong>Deal Analysis:</strong> AI-powered investment recommendations</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <i class="fas fa-file-alt text-purple-500"></i>
                                <span class="text-sm"><strong>Listing Generator:</strong> Create professional property listings</span>
                            </div>
                        </div>
                        <p class="text-sm text-gray-600">All AI features are powered by GPT-4 and trained on real estate best practices.</p>
                        '''
                    }
                },
                'target_selector': '.ai-control-center',
                'trigger_event': 'manual',
                'position': 'bottom'
            },
            {
                'step_key': 'dispositions_section',
                'title': 'Exit Strategies',
                'description': 'Plan your exit strategy with buyer targeting and profit optimization.',
                'category': 'dispositions',
                'sequence_order': 6,
                'tutorial_content': {
                    'type': 'tooltip',
                    'content': {
                        'title': 'Dispositions & Exit Strategies',
                        'body': '''
                        <p class="mb-3">Once you acquire a property, plan your exit strategy:</p>
                        <div class="space-y-2 mb-3">
                            <div class="flex items-center space-x-2">
                                <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                                <span class="text-sm"><strong>Cash Sale:</strong> Target different buyer personas</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <div class="w-3 h-3 bg-blue-500 rounded-full"></div>
                                <span class="text-sm"><strong>MLS Listing:</strong> Calculate net proceeds after commissions</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <div class="w-3 h-3 bg-orange-500 rounded-full"></div>
                                <span class="text-sm"><strong>Sub-To Wrap:</strong> Wrap existing financing</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <div class="w-3 h-3 bg-purple-500 rounded-full"></div>
                                <span class="text-sm"><strong>Seller Finance:</strong> Create financing packages</span>
                            </div>
                        </div>
                        <p class="text-sm text-gray-600">Each strategy includes buyer targeting, profit calculations, and timeline estimates.</p>
                        '''
                    }
                },
                'target_selector': '.dispositions-section',
                'trigger_event': 'manual',
                'position': 'top'
            },
            {
                'step_key': 'user_dashboard_access',
                'title': 'Your Dashboard',
                'description': 'Access your account dashboard for credits, team management, and settings.',
                'category': 'account',
                'sequence_order': 7,
                'tutorial_content': {
                    'type': 'tooltip',
                    'content': {
                        'title': 'Account Dashboard',
                        'body': '''
                        <p class="mb-3">Your dashboard provides complete account management:</p>
                        <div class="space-y-2 mb-3">
                            <div class="flex items-center space-x-2">
                                <i class="fas fa-credit-card text-green-500"></i>
                                <span class="text-sm">Credit balance and usage history</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <i class="fas fa-users text-blue-500"></i>
                                <span class="text-sm">Team management and invitations</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <i class="fas fa-cog text-purple-500"></i>
                                <span class="text-sm">Account settings and preferences</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <i class="fas fa-chart-bar text-orange-500"></i>
                                <span class="text-sm">Analytics and usage reports</span>
                            </div>
                        </div>
                        <p class="text-sm text-gray-600">Click the Dashboard button to access all account features.</p>
                        '''
                    }
                },
                'target_selector': 'a[href="/dashboard"]',
                'trigger_event': 'manual',
                'position': 'bottom'
            },
            {
                'step_key': 'onboarding_complete',
                'title': 'You\'re All Set!',
                'description': 'Complete your onboarding and start analyzing properties.',
                'category': 'completion',
                'sequence_order': 8,
                'tutorial_content': {
                    'type': 'modal',
                    'content': {
                        'title': '🎉 Onboarding Complete!',
                        'body': '''
                        <div class="text-center">
                            <div class="mb-4">
                                <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <i class="fas fa-check text-green-600 text-2xl"></i>
                                </div>
                            </div>
                            <h3 class="text-xl font-bold mb-3">You're ready to start investing!</h3>
                            <p class="text-gray-600 mb-4">You now know how to use all the key features of Properwrite. Here's what to do next:</p>
                            <div class="bg-blue-50 rounded-lg p-4 mb-4">
                                <h4 class="font-semibold text-blue-900 mb-2">Next Steps:</h4>
                                <ul class="text-sm text-blue-800 space-y-1">
                                    <li>✓ Analyze your first property</li>
                                    <li>✓ Compare multiple investment strategies</li>
                                    <li>✓ Use AI insights for better decisions</li>
                                    <li>✓ Invite team members to collaborate</li>
                                    <li>✓ Set up your disposition strategies</li>
                                </ul>
                            </div>
                            <div class="bg-green-50 rounded-lg p-4 mb-4">
                                <p class="text-sm text-green-800">💡 <strong>Pro Tip:</strong> You can restart this tour anytime by clicking the "Help" button in the navigation.</p>
                            </div>
                        </div>
                        ''',
                        'actions': [
                            {'text': 'Start Analyzing', 'action': 'complete', 'style': 'primary'},
                            {'text': 'Visit Dashboard', 'action': 'dashboard', 'style': 'secondary'}
                        ]
                    }
                },
                'trigger_event': 'manual',
                'completion_required': True,
                'completion_action': 'mark_complete'
            }
        ]
        
        # Create onboarding steps
        for step_data in steps:
            step = OnboardingStep(**step_data)
            session.add(step)
        
        session.commit()
        print(f"✓ Created {len(steps)} onboarding steps successfully")
        
        # Display created steps
        created_steps = session.query(OnboardingStep).order_by(OnboardingStep.sequence_order).all()
        print("\nCreated onboarding steps:")
        for step in created_steps:
            print(f"  {step.sequence_order}. {step.title} ({step.step_key})")
        
    except Exception as e:
        session.rollback()
        print(f"Error creating onboarding steps: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    initialize_onboarding_steps()