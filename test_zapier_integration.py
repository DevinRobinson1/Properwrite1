"""
Test Zapier webhook integration
"""
import os
import requests
import json
from datetime import datetime

# Test settings
ZAPIER_SHARED_SECRET = os.environ.get('ZAPIER_SHARED_SECRET', 'test-secret-key')
BASE_URL = 'http://localhost:5000'

def test_zapier_auth():
    """Test Zapier authentication endpoint"""
    print("Testing Zapier authentication...")
    
    # Test with correct secret
    response = requests.get(
        f'{BASE_URL}/api/zapier/test',
        headers={'X-Zapier-Secret': ZAPIER_SHARED_SECRET}
    )
    print(f"With correct secret: {response.status_code} - {response.json()}")
    
    # Test with incorrect secret
    response = requests.get(
        f'{BASE_URL}/api/zapier/test',
        headers={'X-Zapier-Secret': 'wrong-secret'}
    )
    print(f"With wrong secret: {response.status_code} - {response.json()}")
    
def test_inbound_actions():
    """Test Zapier inbound actions"""
    print("\nTesting inbound actions...")
    
    headers = {'X-Zapier-Secret': ZAPIER_SHARED_SECRET}
    
    # Test grant credits
    print("\n1. Testing grant credits:")
    response = requests.post(
        f'{BASE_URL}/api/zapier/grant-credits',
        headers=headers,
        json={
            'user_id': 'test-user-id',
            'credits': 50,
            'reason': 'Testing Zapier integration'
        }
    )
    print(f"Grant credits: {response.status_code} - {response.json()}")
    
    # Test send notification
    print("\n2. Testing send notification:")
    response = requests.post(
        f'{BASE_URL}/api/zapier/send-notification',
        headers=headers,
        json={
            'user_id': 'test-user-id',
            'message': 'Test notification from Zapier',
            'type': 'success'
        }
    )
    print(f"Send notification: {response.status_code} - {response.json()}")

def test_webhook_triggers():
    """Test webhook triggers (simulated)"""
    print("\nWebhook triggers would be fired on these events:")
    print("1. New user signup - fires when user registers")
    print("2. Low credits alert - fires when credits < 20")
    print("3. JV deal submission - fires when partner submits deal")
    print("4. Payment received - fires on successful payment")
    print("5. JV deal approved - fires when admin approves deal")
    print("6. Error threshold - fires when error count exceeds limit")
    
    # Note: Actual webhook firing would require configured webhook URLs
    # which are set via ZAPIER_WEBHOOK_URL environment variable

if __name__ == '__main__':
    print("=== Zapier Integration Test ===")
    print(f"Using secret: {ZAPIER_SHARED_SECRET}")
    print(f"Testing against: {BASE_URL}")
    print("================================\n")
    
    test_zapier_auth()
    test_inbound_actions()
    test_webhook_triggers()
    
    print("\n=== Test Complete ===")
    print("To enable actual webhook firing, set ZAPIER_WEBHOOK_URL environment variable")
    print("Example: ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID/")