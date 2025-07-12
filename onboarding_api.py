"""
API Routes for Interactive User Onboarding Toolkit System
Handles all onboarding-related API endpoints
"""

from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from onboarding_service import OnboardingService
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import os
import logging

onboarding_bp = Blueprint('onboarding', __name__)
onboarding_service = OnboardingService()

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

@onboarding_bp.route('/api/onboarding/status', methods=['GET'])
@login_required
def get_onboarding_status():
    """Get current user's onboarding status"""
    try:
        user_id = current_user.id
        with Session(engine) as db:
            status = onboarding_service.get_user_onboarding_status(user_id, db)
        
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logging.error(f"Error getting onboarding status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get onboarding status'
        }), 500

@onboarding_bp.route('/api/onboarding/start-step', methods=['POST'])
@login_required
def start_onboarding_step():
    """Start a specific onboarding step"""
    try:
        data = request.get_json()
        step_key = data.get('step_key')
        
        if not step_key:
            return jsonify({
                'success': False,
                'error': 'Step key is required'
            }), 400
        
        user_id = current_user.id
        with Session(engine) as db:
            result = onboarding_service.start_onboarding_step(user_id, step_key, db)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logging.error(f"Error starting onboarding step: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to start onboarding step'
        }), 500

@onboarding_bp.route('/api/onboarding/complete-step', methods=['POST'])
@login_required
def complete_onboarding_step():
    """Complete a specific onboarding step"""
    try:
        data = request.get_json()
        step_key = data.get('step_key')
        interaction_data = data.get('interaction_data', {})
        
        if not step_key:
            return jsonify({
                'success': False,
                'error': 'Step key is required'
            }), 400
        
        user_id = current_user.id
        with Session(engine) as db:
            result = onboarding_service.complete_onboarding_step(
                user_id, step_key, db, interaction_data
            )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logging.error(f"Error completing onboarding step: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to complete onboarding step'
        }), 500

@onboarding_bp.route('/api/onboarding/skip-step', methods=['POST'])
@login_required
def skip_onboarding_step():
    """Skip a specific onboarding step"""
    try:
        data = request.get_json()
        step_key = data.get('step_key')
        
        if not step_key:
            return jsonify({
                'success': False,
                'error': 'Step key is required'
            }), 400
        
        user_id = current_user.id
        with Session(engine) as db:
            result = onboarding_service.skip_onboarding_step(user_id, step_key, db)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logging.error(f"Error skipping onboarding step: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to skip onboarding step'
        }), 500

@onboarding_bp.route('/api/onboarding/tutorial-content/<step_key>', methods=['GET'])
@login_required
def get_tutorial_content(step_key):
    """Get tutorial content for a specific step"""
    try:
        content = onboarding_service.get_onboarding_tutorial_content(step_key)
        
        if content:
            return jsonify({
                'success': True,
                'content': content
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Tutorial content not found'
            }), 404
            
    except Exception as e:
        logging.error(f"Error getting tutorial content: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get tutorial content'
        }), 500

@onboarding_bp.route('/api/onboarding/record-interaction', methods=['POST'])
@login_required
def record_user_interaction():
    """Record user interaction with onboarding step"""
    try:
        data = request.get_json()
        step_key = data.get('step_key')
        interaction_type = data.get('interaction_type')
        interaction_data = data.get('interaction_data', {})
        
        if not step_key or not interaction_type:
            return jsonify({
                'success': False,
                'error': 'Step key and interaction type are required'
            }), 400
        
        user_id = current_user.id
        with Session(engine) as db:
            success = onboarding_service.record_user_interaction(
                user_id, step_key, interaction_type, interaction_data, db
            )
        
        return jsonify({
            'success': success
        })
            
    except Exception as e:
        logging.error(f"Error recording interaction: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to record interaction'
        }), 500

@onboarding_bp.route('/api/onboarding/recommendations', methods=['GET'])
@login_required
def get_personalized_recommendations():
    """Get personalized recommendations for the user"""
    try:
        user_id = current_user.id
        with Session(engine) as db:
            recommendations = onboarding_service.get_personalized_recommendations(user_id, db)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
            
    except Exception as e:
        logging.error(f"Error getting recommendations: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get recommendations'
        }), 500

@onboarding_bp.route('/api/onboarding/reset', methods=['POST'])
@login_required
def reset_onboarding():
    """Reset onboarding progress for the current user"""
    try:
        user_id = current_user.id
        with Session(engine) as db:
            success = onboarding_service.reset_onboarding(user_id, db)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Onboarding progress reset successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to reset onboarding progress'
            }), 500
            
    except Exception as e:
        logging.error(f"Error resetting onboarding: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to reset onboarding'
        }), 500

@onboarding_bp.route('/api/onboarding/guest-tips', methods=['GET'])
def get_guest_onboarding_tips():
    """Get onboarding tips for guest users"""
    try:
        # Simple tips for guest users who aren't logged in
        guest_tips = [
            {
                'id': 'property_input',
                'title': 'Start with a Property Address',
                'description': 'Enter any property address to see real market data analysis',
                'target': '#property-address',
                'action': 'focus_input'
            },
            {
                'id': 'free_analysis',
                'title': 'Free Analysis Available',
                'description': 'You get one free property analysis. Register for 4 more credits!',
                'target': '.credit-display',
                'action': 'highlight'
            },
            {
                'id': 'strategy_overview',
                'title': 'Multiple Investment Strategies',
                'description': 'Explore different ways to structure your real estate deals',
                'target': '.acquisition-tabs',
                'action': 'highlight'
            }
        ]
        
        return jsonify({
            'success': True,
            'tips': guest_tips
        })
            
    except Exception as e:
        logging.error(f"Error getting guest tips: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get guest tips'
        }), 500

@onboarding_bp.route('/api/onboarding/trigger-event', methods=['POST'])
@login_required
def trigger_onboarding_event():
    """Trigger an onboarding event (e.g., property_analyzed, strategy_selected)"""
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        event_data = data.get('event_data', {})
        
        if not event_type:
            return jsonify({
                'success': False,
                'error': 'Event type is required'
            }), 400
        
        user_id = current_user.id
        
        # Get current onboarding status
        with Session(engine) as db:
            status = onboarding_service.get_user_onboarding_status(user_id, db)
        
        # Find steps triggered by this event
        triggered_steps = []
        for step in onboarding_service.default_steps:
            if step.get('trigger_event') == event_type:
                # Check if step is eligible to be triggered
                if not status['is_onboarding_complete']:
                    triggered_steps.append(step)
        
        return jsonify({
            'success': True,
            'event_processed': event_type,
            'triggered_steps': triggered_steps,
            'onboarding_status': status
        })
            
    except Exception as e:
        logging.error(f"Error triggering onboarding event: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to trigger onboarding event'
        }), 500