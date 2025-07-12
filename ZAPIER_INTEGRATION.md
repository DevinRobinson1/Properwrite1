# Zapier Integration Documentation

## Overview
The properwrite.com platform includes comprehensive Zapier integration for automated workflow triggers and actions.

## Environment Variables

```bash
# Required for Zapier webhook functionality
ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID/
ZAPIER_SHARED_SECRET=your-secure-shared-secret

# Optional: Specific webhook URLs for different triggers
ZAPIER_WEBHOOK_NEW_USER=https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID/
ZAPIER_WEBHOOK_LOW_CREDITS=https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID/
ZAPIER_WEBHOOK_JV_SUBMISSION=https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID/
ZAPIER_WEBHOOK_PAYMENT=https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID/
ZAPIER_WEBHOOK_JV_APPROVED=https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID/
ZAPIER_WEBHOOK_ERROR_THRESHOLD=https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID/
```

## Outbound Triggers (App → Zapier)

### 1. New User Signup
Fires when a new user registers on the platform.

**Payload:**
```json
{
  "trigger": "new_user_signup",
  "data": {
    "id": "user-uuid",
    "email": "user@example.com",
    "plan": "pro",
    "team_id": "team-uuid",
    "created_at": "2025-07-12T12:00:00Z"
  }
}
```

### 2. Credits Low
Fires when a team's credit balance drops below 20 credits.

**Payload:**
```json
{
  "trigger": "credits_low",
  "data": {
    "user_id": "user-uuid",
    "email": "owner@example.com",
    "credits_remaining": 15
  }
}
```

### 3. JV Deal Submission
Fires when a partner submits a new JV deal.

**Payload:**
```json
{
  "trigger": "jv_submission",
  "data": {
    "id": "deal-uuid",
    "address": "123 Main St, Charlotte, NC",
    "user_id": "partner-uuid",
    "partner_name": "John Doe",
    "partner_email": "partner@example.com",
    "status": "pending",
    "created_at": "2025-07-12T12:00:00Z"
  }
}
```

### 4. Payment Received
Fires when a payment is successfully processed.

**Payload:**
```json
{
  "trigger": "payment_received",
  "data": {
    "customer_id": "cus_xxx",
    "user_id": "user-uuid",
    "amount": 7900,
    "currency": "usd",
    "plan_name": "Pro Plan",
    "invoice_id": "inv_xxx",
    "subscription_id": "sub_xxx"
  }
}
```

### 5. JV Deal Approved
Fires when an admin approves a JV deal.

**Payload:**
```json
{
  "trigger": "jv_approved",
  "data": {
    "id": "deal-uuid",
    "address": "123 Main St, Charlotte, NC",
    "user_id": "partner-uuid",
    "partner_name": "John Doe",
    "partner_email": "partner@example.com",
    "approved_at": "2025-07-12T12:00:00Z"
  }
}
```

### 6. Error Threshold
Fires when error count exceeds configured threshold.

**Payload:**
```json
{
  "trigger": "error_threshold",
  "data": {
    "error_count": 25,
    "error_type": "api_failure"
  }
}
```

## Inbound Actions (Zapier → App)

All inbound actions require authentication via `X-Zapier-Secret` header.

### 1. Grant Bonus Credits
**Endpoint:** `POST /api/zapier/grant-credits`

**Headers:**
```
X-Zapier-Secret: your-secure-shared-secret
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "user-uuid",
  "credits": 50,
  "reason": "Referral bonus"
}
```

### 2. Approve JV Deal
**Endpoint:** `POST /api/zapier/approve-jv`

**Request Body:**
```json
{
  "deal_id": "deal-uuid",
  "notes": "Approved via automation"
}
```

### 3. Send User Notification
**Endpoint:** `POST /api/zapier/send-notification`

**Request Body:**
```json
{
  "user_id": "user-uuid",
  "message": "Your referral bonus has been credited!",
  "type": "success"
}
```

### 4. Deduct Credits
**Endpoint:** `POST /api/zapier/deduct-credits`

**Request Body:**
```json
{
  "user_id": "user-uuid",
  "credits": 10,
  "reason": "Manual adjustment"
}
```

### 5. Update User Plan
**Endpoint:** `POST /api/zapier/update-plan`

**Request Body:**
```json
{
  "user_id": "user-uuid",
  "plan": "growth10"
}
```

## Testing

Use the included test script to verify integration:

```bash
python test_zapier_integration.py
```

## Security

- All inbound actions require the `X-Zapier-Secret` header
- The shared secret should be long and randomly generated
- Use HTTPS for all webhook URLs
- Webhook URLs should be kept confidential

## Example Zapier Workflows

1. **Welcome Email Automation**
   - Trigger: New User Signup
   - Action: Send welcome email via SendGrid/Mailgun

2. **Low Credits Alert**
   - Trigger: Credits Low
   - Action: Send SMS via Twilio or Email notification

3. **JV Deal Processing**
   - Trigger: JV Deal Submission
   - Action: Create task in Asana/Trello, notify team on Slack

4. **Subscription Renewal Celebration**
   - Trigger: Payment Received
   - Action: Grant bonus credits, send thank you email

5. **JV Deal Approval Notification**
   - Trigger: JV Deal Approved
   - Action: Send congratulations email to partner

6. **Error Monitoring**
   - Trigger: Error Threshold
   - Action: Create urgent ticket in support system, page on-call engineer