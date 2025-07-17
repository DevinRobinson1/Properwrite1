"""
Billing Service for Subscription Management
Handles Stripe integration, webhooks, and credit management
"""

import stripe
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, and_
from billing_models import Team, User, CreditLog, TeamInvite
from billing_config import SUBSCRIPTION_PLANS, CREDIT_PACKS
import secrets
import jwt
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_service import EmailService

# Configure Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Database connection with enhanced SSL settings
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

class BillingService:
    def __init__(self):
        self.stripe = stripe
        self.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
        self.email_service = EmailService()
        
    def db_session(self):
        """Create a database session"""
        return sessionmaker(bind=engine)()
        
    def _fire_webhook(self, event_type: str, data: dict):
        """Fire webhook for events (placeholder for webhook service)"""
        try:
            # Import here to avoid circular imports
            from zapier_webhook_service import fire_webhook
            fire_webhook(event_type, data)
        except ImportError:
            logging.info(f"Webhook service not available for event: {event_type}")
        except Exception as e:
            logging.warning(f"Webhook firing failed for {event_type}: {e}")
        
    def create_checkout_session(self, lookup_key: str, quantity: int = 1, customer_email: str = None, 
                               team_id: str = None, success_url: str = None, cancel_url: str = None, 
                               promo_code: str = None) -> Dict:
        """
        Create Stripe checkout session for subscription or one-time purchase
        """
        try:
            # Retrieve price by lookup key
            prices = stripe.Price.list(lookup_keys=[lookup_key], limit=1)
            if not prices.data:
                raise ValueError(f"No price found for lookup key: {lookup_key}")
            
            price = prices.data[0]
            
            # Determine if this is a subscription or one-time purchase
            is_subscription = price.recurring is not None
            
            # Build line items
            line_items = [{
                'price': price.id,
                'quantity': quantity,
            }]
            
            # Build session parameters
            session_params = {
                'payment_method_types': ['card'],
                'line_items': line_items,
                'mode': 'subscription' if is_subscription else 'payment',
                'success_url': success_url or 'https://your-domain.com/success',
                'cancel_url': cancel_url or 'https://your-domain.com/cancel',
                'metadata': {
                    'lookup_key': lookup_key,
                    'team_id': team_id or '',
                    'quantity': str(quantity),
                    'promo_code': promo_code or ''
                }
            }
            
            # Add customer email if provided
            if customer_email:
                session_params['customer_email'] = customer_email
            
            # Create the session
            session = stripe.checkout.Session.create(**session_params)
            
            return {
                'success': True,
                'session_id': session.id,
                'url': session.url
            }
            
        except Exception as e:
            logging.error(f"Error creating checkout session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_webhook(self, payload: str, signature: str) -> Dict:
        """
        Handle Stripe webhook events
        """
        try:
            endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
            event = stripe.Webhook.construct_event(payload, signature, endpoint_secret)
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                return self._handle_checkout_completed(event['data']['object'])
            elif event['type'] == 'invoice.paid':
                return self._handle_invoice_paid(event['data']['object'])
            elif event['type'] == 'payment_intent.succeeded':
                return self._handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_cancelled(event['data']['object'])
            
            return {'success': True, 'message': 'Event handled'}
            
        except Exception as e:
            logging.error(f"Webhook error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_checkout_completed(self, session) -> Dict:
        """Handle successful checkout completion"""
        try:
            with Session(engine) as db:
                lookup_key = session.get('metadata', {}).get('lookup_key')
                team_id = session.get('metadata', {}).get('team_id')
                quantity = int(session.get('metadata', {}).get('quantity', 1))
                promo_code = session.get('metadata', {}).get('promo_code')
                
                # Get customer
                customer = stripe.Customer.retrieve(session['customer'])
                
                if lookup_key in ['starter_m', 'pro_m', 'team5_m', 'growth10_m']:
                    # Subscription signup
                    tier = lookup_key.replace('_m', '')
                    
                    if team_id:
                        # Existing team upgrade
                        team = db.query(Team).filter(Team.id == team_id).first()
                        if team:
                            team.tier = tier
                            team.seats_max = SUBSCRIPTION_PLANS[tier]['seats'] * quantity
                            team.stripe_customer_id = customer.id
                    else:
                        # New team creation
                        team = Team(
                            name=f"{customer.email}'s Team",
                            stripe_customer_id=customer.id,
                            tier=tier,
                            seats_max=SUBSCRIPTION_PLANS[tier]['seats'] * quantity,
                            credit_balance=SUBSCRIPTION_PLANS[tier]['credits_per_month']
                        )
                        db.add(team)
                        db.flush()
                        
                        # Create owner user
                        owner = User(
                            email=customer.email,
                            name=customer.name or customer.email,
                            team_id=team.id,
                            role='owner'
                        )
                        db.add(owner)
                        db.flush()  # Ensure owner.id is available
                        
                        # Trigger Zapier webhook for new user
                        from zapier_webhook_service import trigger_new_user_signup
                        trigger_new_user_signup({
                            'id': owner.id,
                            'email': owner.email,
                            'plan': tier,
                            'team_id': team.id,
                            'created_at': owner.created_at
                        })
                        
                        # Log initial credits
                        credit_log = CreditLog(
                            team_id=team.id,
                            delta=SUBSCRIPTION_PLANS[tier]['credits_per_month'],
                            reason=f'initial-{tier}'
                        )
                        db.add(credit_log)
                        
                        # Apply promo code bonus if present
                        if promo_code:
                            bonus_credits = self._apply_promo_code_bonus(promo_code, tier)
                            if bonus_credits > 0:
                                team.credit_balance += bonus_credits
                                bonus_log = CreditLog(
                                    team_id=team.id,
                                    delta=bonus_credits,
                                    reason=f'promo-{promo_code}'
                                )
                                db.add(bonus_log)
                
                db.commit()
                
            return {'success': True, 'message': 'Checkout completed successfully'}
            
        except Exception as e:
            logging.error(f"Error handling checkout completion: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_invoice_paid(self, invoice) -> Dict:
        """Handle monthly subscription renewal"""
        try:
            with Session(engine) as db:
                # Find team by Stripe customer ID
                team = db.query(Team).filter(
                    Team.stripe_customer_id == invoice['customer']
                ).first()
                
                if team and team.tier in SUBSCRIPTION_PLANS:
                    # Add monthly credits
                    monthly_credits = SUBSCRIPTION_PLANS[team.tier]['credits_per_month']
                    team.credit_balance += monthly_credits
                    
                    # Log the credit addition
                    credit_log = CreditLog(
                        team_id=team.id,
                        delta=monthly_credits,
                        reason=f'monthly-{team.tier}'
                    )
                    db.add(credit_log)
                    db.commit()
                    
                    # Trigger Zapier webhook for payment received
                    from zapier_webhook_service import trigger_payment_received
                    trigger_payment_received({
                        'customer_id': invoice['customer'],
                        'user_id': None,  # Would need to look up user from team
                        'amount': invoice['amount_paid'],
                        'currency': invoice['currency'],
                        'plan_name': f'{team.tier} Plan',
                        'invoice_id': invoice['id'],
                        'subscription_id': invoice['subscription']
                    })
                
            return {'success': True, 'message': 'Monthly credits added'}
            
        except Exception as e:
            logging.error(f"Error handling invoice payment: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_payment_succeeded(self, payment_intent) -> Dict:
        """Handle one-time credit pack purchase"""
        try:
            with Session(engine) as db:
                # Get the associated checkout session
                sessions = stripe.checkout.Session.list(
                    payment_intent=payment_intent['id'],
                    limit=1
                )
                
                if sessions.data:
                    session = sessions.data[0]
                    lookup_key = session.get('metadata', {}).get('lookup_key')
                    team_id = session.get('metadata', {}).get('team_id')
                    
                    if lookup_key in CREDIT_PACKS and team_id:
                        pack = CREDIT_PACKS[lookup_key]
                        
                        # Find team
                        team = db.query(Team).filter(Team.id == team_id).first()
                        if team:
                            # Add credits
                            team.credit_balance += pack['credits']
                            
                            # Log the purchase
                            credit_log = CreditLog(
                                team_id=team.id,
                                delta=pack['credits'],
                                reason=lookup_key
                            )
                            db.add(credit_log)
                            db.commit()
                
            return {'success': True, 'message': 'Credit pack processed'}
            
        except Exception as e:
            logging.error(f"Error handling payment success: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_cancelled(self, subscription) -> Dict:
        """Handle subscription cancellation"""
        try:
            with Session(engine) as db:
                # Find team by Stripe customer ID
                team = db.query(Team).filter(
                    Team.stripe_customer_id == subscription['customer']
                ).first()
                
                if team:
                    # Downgrade to basic tier or deactivate
                    team.tier = 'cancelled'
                    team.seats_max = 0
                    
                    # Deactivate all users except owner
                    users = db.query(User).filter(
                        and_(User.team_id == team.id, User.role != 'owner')
                    ).all()
                    
                    for user in users:
                        user.is_active = False
                    
                    db.commit()
                
            return {'success': True, 'message': 'Subscription cancelled'}
            
        except Exception as e:
            logging.error(f"Error handling subscription cancellation: {e}")
            return {'success': False, 'error': str(e)}
    
    def consume_credit(self, team_id: str, reason: str = 'analysis') -> Dict:
        """
        Consume one credit for analysis
        """
        try:
            with Session(engine) as db:
                team = db.query(Team).filter(Team.id == team_id).first()
                
                if not team:
                    return {'success': False, 'error': 'Team not found'}
                
                if team.credit_balance <= 0:
                    return {'success': False, 'error': 'Insufficient credits', 'code': 402}
                
                # Deduct credit
                team.credit_balance -= 1
                
                # Log the consumption
                credit_log = CreditLog(
                    team_id=team.id,
                    delta=-1,
                    reason=reason
                )
                db.add(credit_log)
                db.commit()
                
                # Trigger low credits webhook if below threshold
                if team.credit_balance < 20:  # Low credit threshold
                    from zapier_webhook_service import trigger_credits_low
                    # Find a user from this team to report
                    owner = db.query(User).filter(
                        User.team_id == team.id,
                        User.role == 'owner'
                    ).first()
                    
                    if owner:
                        trigger_credits_low({
                            'user_id': owner.id,
                            'email': owner.email,
                            'credits_remaining': team.credit_balance
                        }, balance=team.credit_balance)
                
                return {
                    'success': True,
                    'remaining_credits': team.credit_balance
                }
                
        except Exception as e:
            logging.error(f"Error consuming credit: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_team_stats(self, team_id: str) -> Dict:
        """
        Get team statistics and billing information
        """
        try:
            with Session(engine) as db:
                team = db.query(Team).filter(Team.id == team_id).first()
                
                if not team:
                    return {'success': False, 'error': 'Team not found'}
                
                # Count active users
                active_users = db.query(User).filter(
                    and_(User.team_id == team_id, User.is_active == True)
                ).count()
                
                # Get recent credit activity
                recent_logs = db.query(CreditLog).filter(
                    CreditLog.team_id == team_id
                ).order_by(CreditLog.created_at.desc()).limit(10).all()
                
                # Get team members
                team_members = db.query(User).filter(
                    User.team_id == team_id
                ).all()
                
                return {
                    'success': True,
                    'team': {
                        'id': str(team.id),
                        'name': team.name,
                        'tier': team.tier,
                        'seats_used': active_users,
                        'seats_max': team.seats_max,
                        'credit_balance': team.credit_balance,
                        'created_at': team.created_at.isoformat()
                    },
                    'members': [
                        {
                            'id': member.id,
                            'name': member.name,
                            'email': member.email,
                            'role': member.role,
                            'is_active': member.is_active,
                            'created_at': member.created_at.isoformat() if member.created_at else None,
                            'last_active': member.created_at.isoformat() if member.created_at else None
                        } for member in team_members
                    ],
                    'stats': {
                        'total_members': len(team_members),
                        'active_members': active_users,
                        'seats_available': team.seats_max - active_users
                    },
                    'recent_activity': [
                        {
                            'delta': log.delta,
                            'reason': log.reason,
                            'created_at': log.created_at.isoformat()
                        } for log in recent_logs
                    ]
                }
                
        except Exception as e:
            logging.error(f"Error getting team stats: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_team_invite(self, team_id: str, email: str, role: str = 'analyst') -> Dict:
        """
        Create a team invitation
        """
        try:
            with Session(engine) as db:
                # Check if team exists and has available seats
                team = db.query(Team).filter(Team.id == team_id).first()
                if not team:
                    return {'success': False, 'error': 'Team not found'}
                
                active_users = db.query(User).filter(
                    and_(User.team_id == team_id, User.is_active == True)
                ).count()
                
                if active_users >= team.seats_max:
                    return {'success': False, 'error': 'Team is at maximum capacity'}
                
                # Generate invite token
                token = secrets.token_urlsafe(32)
                expires_at = datetime.utcnow() + timedelta(days=7)
                
                # Create invite
                invite = TeamInvite(
                    team_id=team.id,
                    email=email,
                    role=role,
                    token=token,
                    expires_at=expires_at
                )
                db.add(invite)
                db.commit()
                
                # Send invitation email
                email_sent = self._send_invitation_email(email, team.name, token)
                
                # Create invitation link
                base_url = os.environ.get('BASE_URL', 'https://properwrite.com')
                invitation_link = f"{base_url}/accept-invitation?token={token}"
                
                return {
                    'success': True,
                    'invite_token': token,
                    'expires_at': expires_at.isoformat(),
                    'email_sent': email_sent,
                    'invitation_link': invitation_link
                }
                
        except Exception as e:
            logging.error(f"Error creating team invite: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_team_invite_info(self, token: str) -> Dict:
        """
        Get information about a team invite
        """
        try:
            with self.db_session() as db:
                invite = db.query(TeamInvite).filter(TeamInvite.token == token).first()
                
                if not invite:
                    return {'success': False, 'error': 'Invalid invitation'}
                
                if invite.expires_at < datetime.utcnow():
                    return {'success': False, 'error': 'Invitation has expired'}
                
                team = db.query(Team).filter(Team.id == invite.team_id).first()
                
                return {
                    'success': True,
                    'team_info': {
                        'name': team.name,
                        'email': invite.email,
                        'role': invite.role
                    }
                }
        except Exception as e:
            logging.error(f"Error getting team invite info: {e}")
            return {'success': False, 'error': str(e)}
    
    def authenticate_user(self, email: str, password: str) -> Dict:
        """
        Authenticate a user with email and password
        """
        try:
            with self.db_session() as db:
                user = db.query(User).filter(User.email == email).first()
                
                if not user:
                    return {'success': False, 'error': 'Invalid credentials'}
                
                # Check password
                from werkzeug.security import check_password_hash
                if not user.password_hash or not check_password_hash(user.password_hash, password):
                    return {'success': False, 'error': 'Invalid credentials'}
                
                if not user.is_active:
                    return {'success': False, 'error': 'Account is inactive'}
                
                return {
                    'success': True,
                    'user_id': str(user.id),
                    'email': user.email,
                    'name': user.name
                }
                
        except Exception as e:
            logging.error(f"Error authenticating user: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_user(self, user_data: Dict) -> Dict:
        """
        Create a new user account
        """
        try:
            with self.db_session() as db:
                # Check if user already exists
                existing_user = db.query(User).filter(User.email == user_data['email']).first()
                if existing_user:
                    return {'success': False, 'error': 'User with this email already exists'}
                
                # Check if user is joining via team invite
                invite_token = user_data.get('invite_token')
                team = None
                user_role = 'owner'
                
                if invite_token:
                    # Find the invite and validate it
                    invite = db.query(TeamInvite).filter(TeamInvite.token == invite_token).first()
                    
                    if invite and invite.expires_at >= datetime.utcnow():
                        # Get the team from the invite
                        team = db.query(Team).filter(Team.id == invite.team_id).first()
                        
                        if team:
                            # Check team capacity
                            active_users = db.query(User).filter(
                                and_(User.team_id == team.id, User.is_active == True)
                            ).count()
                            
                            if active_users >= team.seats_max:
                                return {'success': False, 'error': 'Team is out of seats; ask your admin to upgrade.'}
                            
                            user_role = invite.role
                            
                            # Mark invite as accepted
                            invite.status = 'accepted'
                            invite.accepted_at = datetime.utcnow()
                            invite.used = True
                
                # If no valid invite, create a new team for the user
                if not team:
                    team = Team(
                        id=uuid.uuid4(),
                        name=f"{user_data.get('name', user_data['email'].split('@')[0])}'s Team",
                        tier='starter',
                        credit_balance=5,  # Starting credits
                        seats_max=1
                    )
                    db.add(team)
                    
                    # Log the initial free credits
                    free_credits_log = CreditLog(
                        team_id=team.id,
                        delta=5,
                        reason='signup-bonus'
                    )
                    db.add(free_credits_log)
                
                # Create new user
                user = User(
                    id=uuid.uuid4(),
                    email=user_data['email'],
                    name=user_data.get('name', user_data['email'].split('@')[0]),
                    team=team,
                    role=user_role,
                    is_active=True
                )
                
                # Hash password if provided
                if 'password' in user_data and user_data['password']:
                    from werkzeug.security import generate_password_hash
                    user.password_hash = generate_password_hash(user_data['password'])
                
                # Add user to database
                db.add(user)
                db.commit()
                db.refresh(user)
                db.refresh(team)
                
                # Fire webhook for new user (if webhook service is available)
                try:
                    self._fire_webhook('new_user_signup', {
                        'user_id': str(user.id),
                        'email': user.email,
                        'name': user.name,
                        'team_id': str(team.id),
                        'joined_via_invite': bool(invite_token)
                    })
                except Exception as e:
                    logging.warning(f"Webhook firing failed: {e}")
                
                return {
                    'success': True,
                    'user_id': str(user.id),
                    'email': user.email,
                    'team_id': str(team.id),
                    'team_name': team.name,
                    'role': user_role
                }
                
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            return {'success': False, 'error': str(e)}
    
    def seed_free_credits(self, user_id: str) -> bool:
        """
        Seed new user with 5 free credits
        """
        try:
            with self.db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                
                if not user:
                    return False
                
                # Find user's team
                team = db.query(Team).filter(Team.id == user.team_id).first()
                
                if not team:
                    return False
                
                # Check if user already has signup bonus
                existing_bonus = db.query(CreditLog).filter(
                    and_(CreditLog.team_id == team.id, CreditLog.reason == 'signup-bonus')
                ).first()
                
                if existing_bonus:
                    return True  # Already has bonus
                
                # Add 5 free credits
                team.credit_balance += 5
                
                # Log the credit addition
                credit_log = CreditLog(
                    team_id=team.id,
                    delta=5,
                    reason='signup-bonus'
                )
                db.add(credit_log)
                db.commit()
                
                return True
                
        except Exception as e:
            logging.error(f"Error seeding free credits: {e}")
            return False
    
    def accept_team_invite(self, token: str, user_id: str) -> Dict:
        """
        Accept a team invitation and add user to the team
        This method is now primarily for existing users accepting invites
        """
        try:
            with self.db_session() as db:
                # Find the invite
                invite = db.query(TeamInvite).filter(TeamInvite.token == token).first()
                
                if not invite:
                    return {'success': False, 'error': 'Invalid invitation'}
                
                if invite.expires_at < datetime.utcnow():
                    return {'success': False, 'error': 'Invitation has expired'}
                
                # Get the team
                team = db.query(Team).filter(Team.id == invite.team_id).first()
                if not team:
                    return {'success': False, 'error': 'Team not found'}
                
                # Check team capacity
                active_users = db.query(User).filter(
                    and_(User.team_id == team.id, User.is_active == True)
                ).count()
                
                if active_users >= team.seats_max:
                    return {'success': False, 'error': 'Team is out of seats; ask your admin to upgrade.'}
                
                # Get the user
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {'success': False, 'error': 'User not found'}
                
                # Check if user has their own single-user team that should be cleaned up
                old_team = user.team
                should_cleanup_old_team = False
                
                if old_team and old_team.id != team.id:
                    # Check if it's a single-user team that can be safely removed
                    team_users = db.query(User).filter(User.team_id == old_team.id).count()
                    if team_users == 1 and old_team.seats_max == 1:
                        should_cleanup_old_team = True
                
                # Add user to new team
                user.team_id = team.id
                user.role = invite.role
                
                # Mark the invite as accepted
                invite.status = 'accepted'
                invite.accepted_at = datetime.utcnow()
                invite.used = True
                
                # Clean up the old single-user team if appropriate
                if should_cleanup_old_team:
                    db.delete(old_team)
                
                db.commit()
                
                return {
                    'success': True,
                    'team_name': team.name,
                    'role': invite.role
                }
                
        except Exception as e:
            logging.error(f"Error accepting team invite: {e}")
            return {'success': False, 'error': str(e)}
    
    def _apply_promo_code_bonus(self, promo_code: str, tier: str) -> int:
        """Apply promo code bonus credits"""
        # Define promo code bonuses
        PROMO_BONUSES = {
            'AFF001': 100,
            'AFF002': 150,
            'AFF003': 200,
            'WELCOME50': 50,
            'STARTER100': 100,
            'subto25': 25,
            'CG40': 40
        }
        
        return PROMO_BONUSES.get(promo_code, 0)
    
    def remove_team_member(self, team_id: str, member_id: str) -> Dict:
        """
        Remove a team member
        """
        try:
            with Session(engine) as db:
                # Check if team exists
                team = db.query(Team).filter(Team.id == team_id).first()
                if not team:
                    return {'success': False, 'error': 'Team not found'}
                
                # Check if member exists and is part of the team
                member = db.query(User).filter(
                    and_(User.id == member_id, User.team_id == team_id)
                ).first()
                
                if not member:
                    return {'success': False, 'error': 'Member not found in team'}
                
                # Don't allow removing the team owner
                if member.role == 'owner':
                    return {'success': False, 'error': 'Cannot remove team owner'}
                
                # Deactivate the user instead of deleting
                member.is_active = False
                member.team_id = None
                member.role = 'analyst'
                db.commit()
                
                return {'success': True, 'message': 'Team member removed successfully'}
                
        except Exception as e:
            logging.error(f"Error removing team member: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_member_role(self, team_id: str, member_id: str, new_role: str) -> Dict:
        """
        Update team member role
        """
        try:
            with Session(engine) as db:
                # Check if team exists
                team = db.query(Team).filter(Team.id == team_id).first()
                if not team:
                    return {'success': False, 'error': 'Team not found'}
                
                # Check if member exists and is part of the team
                member = db.query(User).filter(
                    and_(User.id == member_id, User.team_id == team_id)
                ).first()
                
                if not member:
                    return {'success': False, 'error': 'Member not found in team'}
                
                # Update the role
                member.role = new_role
                db.commit()
                
                return {'success': True, 'message': 'Member role updated successfully'}
                
        except Exception as e:
            logging.error(f"Error updating member role: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_invitation_email(self, email: str, team_name: str, token: str):
        """
        Send team invitation email
        """
        try:
            # Create invitation link
            base_url = os.environ.get('BASE_URL', 'https://properwrite.com')
            invitation_link = f"{base_url}/accept-invitation?token={token}"
            
            # Create email content
            subject = f"You've been invited to join {team_name} on Properwrite"
            
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .header h1 {{ color: white; margin: 0; font-size: 24px; }}
                    .content {{ background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🏠 Properwrite Team Invitation</h1>
                    </div>
                    <div class="content">
                        <h2>You've been invited to join {team_name}!</h2>
                        <p>Hello,</p>
                        <p>You've been invited to join the <strong>{team_name}</strong> team on Properwrite, the premier real estate investment analysis platform.</p>
                        <p>Click the button below to accept your invitation and start analyzing properties:</p>
                        <a href="{invitation_link}" class="button">Accept Invitation</a>
                        <p>If the button doesn't work, copy and paste this link into your browser:</p>
                        <p><a href="{invitation_link}">{invitation_link}</a></p>
                        <p>This invitation will expire in 7 days.</p>
                        <p>Best regards,<br>The Properwrite Team</p>
                    </div>
                    <div class="footer">
                        <p>This email was sent from Properwrite. If you didn't expect this invitation, you can safely ignore this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            You've been invited to join {team_name} on Properwrite!
            
            You've been invited to join the {team_name} team on Properwrite, the premier real estate investment analysis platform.
            
            Click this link to accept your invitation: {invitation_link}
            
            This invitation will expire in 7 days.
            
            Best regards,
            The Properwrite Team
            """
            
            # Try to send email
            email_sent = self.email_service.send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if email_sent:
                logging.info(f"Team invitation email sent successfully to {email} for team {team_name}")
            else:
                logging.warning(f"Failed to send invitation email to {email} - email service may not be configured")
                
            # Always log the invitation for tracking
            logging.info(f"Team invitation sent to {email} for team {team_name} with token {token}")
            
            return email_sent
            
        except Exception as e:
            logging.error(f"Error sending invitation email: {e}")
            # Still log the invitation for tracking even if email fails
            logging.info(f"Team invitation sent to {email} for team {team_name} with token {token}")
            return False
    
    def check_low_credits(self, threshold: int = 20) -> List[Dict]:
        """
        Check for teams with low credit balances
        """
        try:
            with Session(engine) as db:
                low_credit_teams = db.query(Team).filter(
                    Team.credit_balance < threshold
                ).all()
                
                return [
                    {
                        'team_id': str(team.id),
                        'team_name': team.name,
                        'credit_balance': team.credit_balance,
                        'owner_email': db.query(User).filter(
                            and_(User.team_id == team.id, User.role == 'owner')
                        ).first().email
                    } for team in low_credit_teams
                ]
                
        except Exception as e:
            logging.error(f"Error checking low credits: {e}")
            return []
    
    def get_credit_codes(self) -> List[Dict]:
        """
        Get all active credit codes (placeholder - implement with actual storage)
        """
        # This is a placeholder method - in a real implementation, 
        # you would store credit codes in a database table
        # For now, we'll use a simple in-memory store or file-based approach
        
        try:
            # Simple file-based storage for credit codes
            import json
            credit_codes_file = 'credit_codes.json'
            
            if os.path.exists(credit_codes_file):
                with open(credit_codes_file, 'r') as f:
                    credit_codes = json.load(f)
                    return credit_codes
            else:
                return []
        except Exception as e:
            logging.error(f"Error getting credit codes: {e}")
            return []
    
    def save_credit_codes(self, credit_codes: List[Dict]) -> bool:
        """
        Save credit codes to storage
        """
        try:
            import json
            credit_codes_file = 'credit_codes.json'
            
            with open(credit_codes_file, 'w') as f:
                json.dump(credit_codes, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving credit codes: {e}")
            return False
    
    def update_credit_code_usage(self, code: str, new_usage_count: int) -> bool:
        """
        Update credit code usage count
        """
        try:
            credit_codes = self.get_credit_codes()
            
            # Find and update the credit code
            for cc in credit_codes:
                if cc.get('code') == code:
                    cc['current_uses'] = new_usage_count
                    cc['last_used'] = datetime.utcnow().isoformat()
                    
                    # If usage has reached max, deactivate the code
                    if new_usage_count >= cc.get('max_uses', 1):
                        cc['status'] = 'exhausted'
                    
                    # Save updated credit codes
                    return self.save_credit_codes(credit_codes)
            
            return False  # Code not found
        except Exception as e:
            logging.error(f"Error updating credit code usage: {e}")
            return False
    
    def redeem_credit_code(self, code: str, user_email: str) -> Dict:
        """
        Redeem a credit code for a user
        """
        try:
            credit_codes = self.get_credit_codes()
            
            # Find the credit code
            target_code = None
            for cc in credit_codes:
                if cc.get('code') == code:
                    target_code = cc
                    break
            
            if not target_code:
                return {'success': False, 'error': 'invalid'}
            
            # Check if code is active
            if target_code.get('status') != 'active':
                return {'success': False, 'error': 'expired or disabled'}
            
            # Check if code has expired
            if target_code.get('expires_at'):
                from datetime import datetime
                expiry_date = datetime.fromisoformat(target_code['expires_at'])
                if datetime.utcnow() > expiry_date:
                    target_code['status'] = 'expired'
                    self.save_credit_codes(credit_codes)
                    return {'success': False, 'error': 'expired'}
            
            # Check if code has reached max uses
            current_uses = target_code.get('current_uses', 0)
            max_uses = target_code.get('max_uses', 1)
            
            if current_uses >= max_uses:
                target_code['status'] = 'exhausted'
                self.save_credit_codes(credit_codes)
                return {'success': False, 'error': 'exhausted'}
            
            # Redeem the code
            credits_to_add = target_code.get('credit_amount', 0)
            
            # Update usage count
            target_code['current_uses'] = current_uses + 1
            target_code['last_used'] = datetime.utcnow().isoformat()
            
            # Add redemption record
            if 'redemptions' not in target_code:
                target_code['redemptions'] = []
            
            target_code['redemptions'].append({
                'email': user_email,
                'redeemed_at': datetime.utcnow().isoformat(),
                'credits_added': credits_to_add
            })
            
            # Mark as exhausted if reached max uses
            if target_code['current_uses'] >= max_uses:
                target_code['status'] = 'exhausted'
            
            # Save updated credit codes
            self.save_credit_codes(credit_codes)
            
            return {
                'success': True,
                'credits_added': credits_to_add,
                'description': target_code.get('description', 'Credit code redeemed')
            }
            
        except Exception as e:
            logging.error(f"Error redeeming credit code: {e}")
            return {'success': False, 'error': 'system error'}
    
    def add_credits(self, user_email: str, credits: int, payment_method: str = 'bitcoin') -> Dict:
        """
        Add credits to a user's team account
        """
        try:
            with self.db_session() as db:
                # Find the user
                user = db.query(User).filter(User.email == user_email).first()
                if not user:
                    return {'success': False, 'error': 'User not found'}
                
                # Get the team
                team = db.query(Team).filter(Team.id == user.team_id).first()
                if not team:
                    return {'success': False, 'error': 'Team not found'}
                
                # Add credits to team balance
                team.credit_balance = (team.credit_balance or 0) + credits
                
                # Create credit log entry
                credit_log = CreditLog(
                    team_id=user.team_id,
                    user_id=user.id,
                    delta=credits,
                    reason=f'Credit pack purchase via {payment_method}'
                )
                
                db.add(credit_log)
                db.commit()
                
                return {
                    'success': True,
                    'credits_added': credits,
                    'new_balance': team.credit_balance
                }
                
        except Exception as e:
            logging.error(f"Error adding credits: {e}")
            return {'success': False, 'error': str(e)}
    
    def activate_subscription(self, user_email: str, plan_key: str, payment_method: str = 'bitcoin') -> Dict:
        """
        Activate a subscription for a user's team
        """
        try:
            with self.db_session() as db:
                # Find the user
                user = db.query(User).filter(User.email == user_email).first()
                if not user:
                    return {'success': False, 'error': 'User not found'}
                
                # Get the team
                team = db.query(Team).filter(Team.id == user.team_id).first()
                if not team:
                    return {'success': False, 'error': 'Team not found'}
                
                # Get plan configuration
                plan_config = SUBSCRIPTION_PLANS.get(plan_key)
                if not plan_config:
                    return {'success': False, 'error': 'Invalid plan key'}
                
                # Update team subscription
                team.tier = plan_key
                team.seats_max = plan_config['seats']
                team.credit_balance = plan_config.get('credits', 0)  # Set to plan credits or 0 for unlimited
                team.stripe_customer_id = f"bitcoin_{user_email}"  # Mark as Bitcoin customer
                
                # Create credit log entry for subscription activation
                credit_log = CreditLog(
                    team_id=user.team_id,
                    user_id=user.id,
                    delta=plan_config.get('credits', 0),
                    reason=f'Subscription activated via {payment_method}'
                )
                
                db.add(credit_log)
                db.commit()
                
                return {
                    'success': True,
                    'plan_key': plan_key,
                    'tier': plan_key,
                    'credits': plan_config.get('credits', 0),
                    'seats': plan_config['seats']
                }
                
        except Exception as e:
            logging.error(f"Error activating subscription: {e}")
            return {'success': False, 'error': str(e)}
    
    def change_plan(self, team_id: str, new_plan_key: str, user_id: str) -> Dict:
        """
        Change team's subscription plan
        """
        try:
            with self.db_session() as db:
                # Get the team
                team = db.query(Team).filter(Team.id == team_id).first()
                if not team:
                    return {'success': False, 'error': 'Team not found'}
                
                # Get plan configuration
                plan_config = SUBSCRIPTION_PLANS.get(new_plan_key)
                if not plan_config:
                    return {'success': False, 'error': 'Invalid plan'}
                
                # Debug logging
                logging.info(f"Changing plan for team {team_id} from {team.tier} to {new_plan_key}")
                logging.info(f"Plan config: {plan_config}")
                
                old_plan = team.tier
                
                # Update team plan
                team.tier = new_plan_key
                team.seats_max = plan_config['seats']  # Use direct access since we validated the config exists
                
                # Handle credit allocation for plan changes
                monthly_credits = plan_config['credits_per_month']
                if monthly_credits > 0:
                    # For plans with monthly credits, set balance to plan credits
                    team.credit_balance = monthly_credits
                elif monthly_credits == -1:
                    # For unlimited plans, set a high number
                    team.credit_balance = 999999
                
                # Create log entry for plan change
                credit_log = CreditLog(
                    team_id=team_id,
                    user_id=user_id,
                    delta=monthly_credits if monthly_credits > 0 else 0,
                    reason=f'Plan changed from {old_plan} to {new_plan_key}'
                )
                
                db.add(credit_log)
                db.commit()
                
                return {
                    'success': True,
                    'old_plan': old_plan,
                    'new_plan': new_plan_key,
                    'credits': monthly_credits,
                    'seats': plan_config['seats']
                }
                
        except Exception as e:
            logging.error(f"Error changing plan: {e}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}
    
    def get_billing_history(self, team_id: str, limit: int = 50) -> List[Dict]:
        """
        Get billing history for a team
        """
        try:
            with self.db_session() as db:
                # Get credit logs for billing history
                logs = db.query(CreditLog).filter(
                    CreditLog.team_id == team_id
                ).order_by(CreditLog.created_at.desc()).limit(limit).all()
                
                return [
                    {
                        'id': str(log.id),
                        'date': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'Credit Purchase' if log.delta > 0 else 'Credit Usage',
                        'description': log.reason,
                        'amount': log.delta,
                        'balance_after': team.credit_balance if log == logs[0] else None
                    } for log in logs
                ]
                
        except Exception as e:
            logging.error(f"Error getting billing history: {e}")
            return []