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