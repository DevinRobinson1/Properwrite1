from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, CreditPurchase, CompingCredit
from main import app, db
from auth_service import get_user_status, check_usage_limit, consume_credit
from billing_config import SUBSCRIPTION_PLANS, CREDIT_PACKS, COMPING_CREDITS_ENABLED
import stripe
import os
import uuid

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@app.route('/auth/login', methods=['GET', 'POST'])
def auth_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email:
            flash('Email is required', 'error')
            return render_template('auth/login.html')
        
        user = db.session.query(User).filter_by(email=email).first()
        
        if user:
            # If user has password, check it
            if user.password_hash and password:
                if check_password_hash(user.password_hash, password):
                    login_user(user)
                    flash(f'Welcome back! You have {user.credits} credits.', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Invalid password', 'error')
            # If user has no password (email-only login)
            elif not user.password_hash:
                login_user(user)
                flash(f'Welcome back! You have {user.credits} credits.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Password required for this account', 'error')
        else:
            flash('No account found with this email. Please register first.', 'error')
    
    return render_template('auth/login.html')

@app.route('/auth/register', methods=['GET', 'POST'])
def auth_register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        credit_code = request.form.get('credit_code', '').strip().upper()
        
        if not email:
            flash('Email is required', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        existing_user = db.session.query(User).filter_by(email=email).first()
        if existing_user:
            flash('Account already exists with this email. Please login.', 'error')
            return redirect(url_for('login_page'))
        
        # Start with default credits
        starting_credits = 4
        credit_message = 'Registration successful! You now have 4 credits to use.'
        
        # Check credit code if provided
        if credit_code:
            try:
                from billing_service import BillingService
                billing_service = BillingService()
                
                # Try to redeem the credit code
                result = billing_service.redeem_credit_code(credit_code, email)
                
                if result.get('success'):
                    starting_credits += result.get('credits_added', 0)
                    credit_message = f'Registration successful! Credit code "{credit_code}" redeemed for {result.get("credits_added", 0)} bonus credits. You now have {starting_credits} credits to use.'
                else:
                    # Show error but continue with registration
                    flash(f'Credit code "{credit_code}" is {result.get("error", "invalid")}. Continuing with 4 default credits.', 'warning')
            except Exception as e:
                import logging
                logging.error(f"Error redeeming credit code during registration: {e}")
                flash(f'Could not validate credit code. Continuing with 4 default credits.', 'warning')
        
        # Create new user
        user = User(
            email=email,
            name=name,
            credits=starting_credits
        )
        
        # Add password if provided
        if password:
            user.password_hash = generate_password_hash(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log the user in
        login_user(user)
        flash(credit_message, 'success')
        return redirect(url_for('index'))
    
    return render_template('auth/register.html')

@app.route('/auth/logout', methods=['GET', 'POST'])
@login_required
def auth_logout():
    logout_user()
    
    if request.method == 'POST':
        # Handle AJAX logout request
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
    else:
        # Handle regular logout request
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

@app.route('/api/user-status')
def api_user_status():
    """Get current user status for frontend"""
    return jsonify(get_user_status(db))

@app.route('/api/check-usage')
def api_check_usage():
    """Check if user can use the analyzer"""
    can_use, message, redirect_url = check_usage_limit(db)
    return jsonify({
        'can_use': can_use,
        'message': message,
        'redirect_url': redirect_url
    })

@app.route('/purchase-credits')
@login_required
def purchase_credits():
    """Credit purchase page"""
    return render_template('auth/purchase_credits.html', 
                         user=current_user,
                         subscription_plans=SUBSCRIPTION_PLANS,
                         credit_packs=CREDIT_PACKS,
                         comping_enabled=COMPING_CREDITS_ENABLED)

@app.route('/api/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription or credit purchase"""
    try:
        data = request.get_json()
        package_type = data.get('package')
        purchase_type = data.get('type', 'credit_pack')  # 'credit_pack' or 'subscription'
        
        # Get domain
        domain = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
        if not domain.startswith('http'):
            domain = f'https://{domain}'
        
        if purchase_type == 'subscription':
            # Handle subscription purchase
            subscription_info = SUBSCRIPTION_PLANS.get(package_type)
            if not subscription_info:
                return jsonify({'error': 'Invalid subscription plan'}), 400
            
            # Create Stripe checkout session for subscription
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': subscription_info['price'],
                        'product_data': {
                            'name': f"properwrite.com {subscription_info['name']}",
                            'description': subscription_info['description']
                        },
                        'recurring': {
                            'interval': 'month'
                        }
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=domain + '/purchase-success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain + '/purchase-credits',
                metadata={
                    'user_id': str(current_user.id),
                    'package_type': package_type,
                    'purchase_type': 'subscription',
                    'credits_per_month': str(subscription_info['credits_per_month'])
                }
            )
        else:
            # Handle credit pack purchase
            package_info = CREDIT_PACKS.get(package_type)
            if not package_info:
                return jsonify({'error': 'Invalid credit package'}), 400
            
            # Create checkout session for one-time payment
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': package_info['name'],
                            'description': f"{package_info['credits']} property analysis credits"
                        },
                        'unit_amount': package_info['price'],
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=domain + '/purchase-success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain + '/purchase-credits',
                metadata={
                    'user_id': str(current_user.id),
                    'package_type': package_type,
                    'purchase_type': 'credit_pack',
                    'credits': str(package_info['credits'])
                }
            )
        
        return jsonify({'checkout_url': checkout_session.url})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/purchase-success')
@login_required
def purchase_success():
    """Handle successful purchase"""
    session_id = request.args.get('session_id')
    
    if session_id:
        try:
            # Retrieve the session
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                purchase_type = session.metadata.get('purchase_type', 'credit_pack')
                
                if purchase_type == 'subscription':
                    # Handle subscription activation
                    plan_type = session.metadata.get('package_type')
                    credits_per_month = session.metadata.get('credits_per_month', '300')
                    
                    # Update user subscription
                    current_user.subscription_tier = plan_type
                    if plan_type == 'growth10':
                        current_user.unlimited_credits = True
                    else:
                        current_user.credits += int(credits_per_month)
                    
                    # Record the purchase
                    purchase = CreditPurchase(
                        user_id=current_user.id,
                        stripe_payment_intent_id=session.payment_intent,
                        credits_purchased=int(credits_per_month) if credits_per_month != '-1' else 0,
                        amount_paid=session.amount_total,
                        purchase_type='subscription'
                    )
                    db.session.add(purchase)
                    db.session.commit()
                    
                    flash(f'Success! {plan_type.title()} subscription activated.', 'success')
                else:
                    # Handle credit pack purchase
                    credits_to_add = int(session.metadata.get('credits', 0))
                    current_user.add_credits(credits_to_add)
                    
                    # Record the purchase
                    purchase = CreditPurchase(
                        user_id=current_user.id,
                        stripe_payment_intent_id=session.payment_intent,
                        credits_purchased=credits_to_add,
                        amount_paid=session.amount_total,
                        purchase_type='credit_pack'
                    )
                    db.session.add(purchase)
                    db.session.commit()
                    
                    flash(f'Success! {credits_to_add} credits added to your account.', 'success')
            else:
                flash('Payment not completed. Please try again.', 'error')
                
        except Exception as e:
            flash('Error processing payment. Please contact support.', 'error')
    
    return redirect(url_for('index'))

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Fulfill the purchase
        user_id = session.metadata.get('user_id')
        credits = int(session.metadata.get('credits', 0))
        
        user = db.session.get(User, user_id)
        if user:
            user.add_credits(credits)
            
            purchase = CreditPurchase(
                user_id=user.id,
                stripe_payment_intent_id=session.payment_intent,
                credits_purchased=credits,
                amount_paid=session.amount_total
            )
            db.session.add(purchase)
            db.session.commit()
    
    return 'OK', 200