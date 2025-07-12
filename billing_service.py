"""
Billing Service for Subscription Management
Handles Stripe integration, webhooks, and credit management
"""

import stripe
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_
from billing_models import Team, User, CreditLog, TeamInvite, TIER_CONFIG, CREDIT_PACKS
import secrets
import jwt
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
        
    def create_checkout_session(self, lookup_key: str, quantity: int = 1, customer_email: str = None, 
                               team_id: str = None, success_url: str = None, cancel_url: str = None) -> Dict:
        """
        Create Stripe checkout session for subscription or one-time purchase
        """
        try:
            # Retrieve price by lookup key
            prices = stripe.Price.list(lookup_key=lookup_key, limit=1)
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
                    'quantity': str(quantity)
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
                            team.seats_max = TIER_CONFIG[tier]['seats_max'] * quantity
                            team.stripe_customer_id = customer.id
                    else:
                        # New team creation
                        team = Team(
                            name=f"{customer.email}'s Team",
                            stripe_customer_id=customer.id,
                            tier=tier,
                            seats_max=TIER_CONFIG[tier]['seats_max'] * quantity,
                            credit_balance=TIER_CONFIG[tier]['monthly_credits']
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
                            delta=TIER_CONFIG[tier]['monthly_credits'],
                            reason=f'initial-{tier}'
                        )
                        db.add(credit_log)
                
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
                
                if team and team.tier in TIER_CONFIG:
                    # Add monthly credits
                    monthly_credits = TIER_CONFIG[team.tier]['monthly_credits']
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
                
                # Create new user
                user = User(
                    id=str(uuid.uuid4()),
                    email=user_data['email'],
                    name=user_data.get('name', user_data['email'].split('@')[0]),
                    credits=5,  # Starting credits
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                
                # Hash password if provided
                if 'password' in user_data:
                    from werkzeug.security import generate_password_hash
                    user.password_hash = generate_password_hash(user_data['password'])
                
                db.add(user)
                db.commit()
                db.refresh(user)
                
                # Fire webhook for new user
                self._fire_webhook('new_user_signup', {
                    'user_id': str(user.id),
                    'email': user.email,
                    'name': user.name
                })
                
                return {
                    'success': True,
                    'user_id': str(user.id),
                    'email': user.email
                }
                
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            return {'success': False, 'error': str(e)}
    
    def accept_team_invite(self, token: str, user_id: str) -> Dict:
        """
        Accept a team invitation and add user to the team
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
                    return {'success': False, 'error': 'Team is at maximum capacity'}
                
                # Get the user
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return {'success': False, 'error': 'User not found'}
                
                # Add user to team
                user.team_id = team.id
                user.team_role = invite.role
                
                # Delete the invite
                db.delete(invite)
                db.commit()
                
                return {
                    'success': True,
                    'team_name': team.name,
                    'role': invite.role
                }
                
        except Exception as e:
            logging.error(f"Error accepting team invite: {e}")
            return {'success': False, 'error': str(e)}
    
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