"""
Bitcoin Payment Service with Coinbase Commerce Integration
Handles Bitcoin payments with 25% discount pricing
"""

import os
import json
import hashlib
import hmac
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from billing_config import SUBSCRIPTION_TIERS, BITCOIN_PRICES

class BitcoinPaymentService:
    def __init__(self):
        self.api_key = os.environ.get('COINBASE_COMMERCE_API_KEY')
        self.webhook_secret = os.environ.get('COINBASE_WEBHOOK_SECRET')
        self.base_url = 'https://api.commerce.coinbase.com'
        self.headers = {
            'Content-Type': 'application/json',
            'X-CC-Api-Key': self.api_key
        }

    def create_subscription_charge(self, plan_key: str, user_email: str, team_id: str = None) -> Dict[str, Any]:
        """
        Create Coinbase Commerce charge for subscription plan
        """
        if plan_key not in BITCOIN_PRICES:
            raise ValueError(f"Invalid plan key: {plan_key}")
        
        # Get plan details
        plan_info = SUBSCRIPTION_TIERS.get(plan_key, {})
        btc_price = BITCOIN_PRICES[f"{plan_key}_btc"]
        
        # Create charge payload
        charge_data = {
            "name": f"PropertyWrite {plan_info.get('name', plan_key.title())} Plan",
            "description": f"{plan_info.get('credits', 'Unlimited')} credits/month - 25% Bitcoin discount",
            "pricing_type": "fixed_price",
            "local_price": {
                "amount": str(btc_price),
                "currency": "USD"
            },
            "metadata": {
                "plan_key": plan_key,
                "user_email": user_email,
                "team_id": team_id or "",
                "payment_method": "bitcoin",
                "type": "subscription",
                "discount_percent": 25,
                "original_price": self._get_original_price(plan_key)
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/charges",
                headers=self.headers,
                json=charge_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create Bitcoin charge: {str(e)}")

    def create_credit_pack_charge(self, credits: int, user_email: str, team_id: str = None) -> Dict[str, Any]:
        """
        Create Coinbase Commerce charge for credit pack
        """
        pack_key = f"credits_{credits}"
        
        if f"{pack_key}_btc" not in BITCOIN_PRICES:
            raise ValueError(f"Invalid credit pack: {credits}")
        
        btc_price = BITCOIN_PRICES[f"{pack_key}_btc"]
        
        # Create charge payload
        charge_data = {
            "name": f"PropertyWrite {credits} Credits Pack",
            "description": f"One-time purchase of {credits} property analysis credits - 25% Bitcoin discount",
            "pricing_type": "fixed_price",
            "local_price": {
                "amount": str(btc_price),
                "currency": "USD"
            },
            "metadata": {
                "credits": credits,
                "user_email": user_email,
                "team_id": team_id or "",
                "payment_method": "bitcoin",
                "type": "credit_pack",
                "discount_percent": 25,
                "original_price": self._get_original_credit_price(credits)
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/charges",
                headers=self.headers,
                json=charge_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create Bitcoin charge: {str(e)}")

    def _get_original_price(self, plan_key: str) -> float:
        """Get original USD price for plan"""
        price_map = {
            'individual': 27.00,
            'pro': 79.00,
            'team5': 199.00,
            'growth10': 399.00
        }
        return price_map.get(plan_key, 0.00)

    def _get_original_credit_price(self, credits: int) -> float:
        """Get original USD price for credit pack"""
        price_map = {
            25: 15.00,
            50: 25.00,
            100: 45.00,
            250: 99.00,
            500: 175.00,
            1000: 299.00
        }
        return price_map.get(credits, 0.00)

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify Coinbase Commerce webhook signature
        """
        if not self.webhook_secret:
            return False
        
        computed_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)

    def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Coinbase Commerce webhook event
        """
        event_type = event_data.get('type')
        charge_data = event_data.get('data', {})
        
        if event_type == 'charge:confirmed':
            return self._handle_charge_confirmed(charge_data)
        elif event_type == 'charge:failed':
            return self._handle_charge_failed(charge_data)
        elif event_type == 'charge:delayed':
            return self._handle_charge_delayed(charge_data)
        
        return {"status": "ignored", "event_type": event_type}

    def _handle_charge_confirmed(self, charge_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle confirmed Bitcoin payment
        """
        metadata = charge_data.get('metadata', {})
        charge_id = charge_data.get('id')
        
        # Extract payment details
        payment_type = metadata.get('type')
        user_email = metadata.get('user_email')
        team_id = metadata.get('team_id')
        
        result = {
            "status": "success",
            "charge_id": charge_id,
            "payment_method": "bitcoin",
            "user_email": user_email,
            "team_id": team_id
        }
        
        if payment_type == 'subscription':
            # Handle subscription payment
            plan_key = metadata.get('plan_key')
            result.update({
                "type": "subscription",
                "plan_key": plan_key,
                "plan_name": SUBSCRIPTION_TIERS.get(plan_key, {}).get('name', plan_key),
                "credits": SUBSCRIPTION_TIERS.get(plan_key, {}).get('credits', 0),
                "seats": SUBSCRIPTION_TIERS.get(plan_key, {}).get('seats', 1)
            })
        elif payment_type == 'credit_pack':
            # Handle credit pack payment
            credits = int(metadata.get('credits', 0))
            result.update({
                "type": "credit_pack",
                "credits": credits
            })
        
        return result

    def _handle_charge_failed(self, charge_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle failed Bitcoin payment
        """
        return {
            "status": "failed",
            "charge_id": charge_data.get('id'),
            "reason": "Bitcoin payment failed"
        }

    def _handle_charge_delayed(self, charge_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle delayed Bitcoin payment
        """
        return {
            "status": "delayed",
            "charge_id": charge_data.get('id'),
            "reason": "Bitcoin payment delayed - waiting for confirmations"
        }

    def get_charge_status(self, charge_id: str) -> Dict[str, Any]:
        """
        Get status of a Bitcoin charge
        """
        try:
            response = requests.get(
                f"{self.base_url}/charges/{charge_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get charge status: {str(e)}")

# Initialize service
bitcoin_service = BitcoinPaymentService()