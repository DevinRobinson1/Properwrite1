# Zapier Integration Setup Guide

## Overview
Your JV submission system is already configured to send webhooks to Zapier when new deals are submitted. This allows you to create automated workflows triggered by JV submissions.

## Available Webhook Triggers

### 1. New JV Submission (`NEW_JV_SUBMISSION`)
**Triggered when:** Someone submits a new JV deal through your submission form
**Environment Variable:** `ZAPIER_HOOK_NEW_JV_SUBMISSION`

**Data Payload:**
```json
{
  "deal_id": "uuid-string",
  "property_address": "123 Main St",
  "property_city": "Charlotte",
  "property_state": "NC",
  "asking_price": 300000,
  "suggested_offer": 250000,
  "arv": 400000,
  "repairs": 50000,
  "partner_name": "John Doe",
  "partner_email": "john@example.com",
  "partner_phone": "(555) 123-4567",
  "partner_company": "ABC Investments",
  "partner_markets": ["NC", "SC"],
  "submission_date": "2025-07-16T19:30:00Z",
  "auto_evaluation": "auto-approved",
  "evaluation_reasons": ["Good profit margin", "Low risk area"],
  "_metadata": {
    "trigger": "NEW_JV_SUBMISSION",
    "timestamp": "2025-07-16T19:30:00Z",
    "environment": "production"
  }
}
```

### 2. JV Deal Approved (`JV_DEAL_APPROVED`)
**Triggered when:** Admin approves a JV deal in the admin panel
**Environment Variable:** `ZAPIER_HOOK_JV_DEAL_APPROVED`

### 3. JV Deal Denied (`JV_DEAL_DENIED`)
**Triggered when:** Admin denies a JV deal in the admin panel
**Environment Variable:** `ZAPIER_HOOK_JV_DEAL_DENIED`

### 4. JV Deal Status Changed (`JV_DEAL_STATUS_CHANGED`)
**Triggered when:** Admin changes the status of a JV deal
**Environment Variable:** `ZAPIER_HOOK_JV_DEAL_STATUS_CHANGED`

## Setup Instructions

### Step 1: Create Your Zapier Webhook
1. Log into your Zapier account
2. Click "Create Zap"
3. Choose "Webhooks by Zapier" as the trigger
4. Select "Catch Hook" as the trigger event
5. Copy the webhook URL provided by Zapier

### Step 2: Configure Environment Variables
Add the following to your `.env` file:

```bash
# Zapier Webhook URLs
ZAPIER_HOOK_NEW_JV_SUBMISSION=https://hooks.zapier.com/hooks/catch/YOUR_WEBHOOK_ID/
ZAPIER_HOOK_JV_DEAL_APPROVED=https://hooks.zapier.com/hooks/catch/YOUR_WEBHOOK_ID/
ZAPIER_HOOK_JV_DEAL_DENIED=https://hooks.zapier.com/hooks/catch/YOUR_WEBHOOK_ID/
ZAPIER_HOOK_JV_DEAL_STATUS_CHANGED=https://hooks.zapier.com/hooks/catch/YOUR_WEBHOOK_ID/

# Optional: Zapier shared secret for inbound webhooks
ZAPIER_SHARED_SECRET=your-secure-secret-here
```

### Step 3: Test the Integration
1. Go to `/jv-submit` on your site
2. Submit a test JV deal
3. Check your Zapier webhook dashboard to confirm data was received
4. Complete your Zapier workflow with desired actions

## Common Automation Ideas

### Email Notifications
- Send immediate email alerts when new deals are submitted
- Notify different team members based on deal evaluation results
- Send follow-up emails to partners

### CRM Integration
- Add new partners to your CRM system
- Create new deal records in your CRM
- Update existing contact information

### Slack/Teams Notifications
- Post new deal alerts to specific channels
- Send different notifications for approved vs denied deals
- Create threaded discussions for deal reviews

### Google Sheets/Airtable
- Log all deal submissions to a spreadsheet
- Track partner performance metrics
- Create deal pipeline dashboards

### SMS Notifications
- Send text alerts for high-value deals
- Notify key team members of urgent submissions
- Send confirmations to partners

## Advanced Features

### Conditional Workflows
Use the `auto_evaluation` field to create different workflows:
- **auto-approved**: Immediate approval notifications
- **auto-denied**: Send to review queue
- **pending**: Trigger manual review process

### Partner Segmentation
Use `partner_markets` array to:
- Route deals to regional team members
- Apply different approval criteria by market
- Track market-specific performance

### Deal Value Triggers
Use `asking_price`, `suggested_offer`, and `arv` fields to:
- Escalate high-value deals to senior team
- Apply different approval thresholds
- Calculate potential profit margins

## Security Notes
- All webhooks include metadata with timestamps and environment info
- Use HTTPS webhook URLs only
- Consider implementing the shared secret for additional security
- Monitor webhook delivery failures in application logs

## Troubleshooting

### Webhook Not Firing
1. Check environment variables are set correctly
2. Verify webhook URL is valid and accessible
3. Check application logs for webhook errors
4. Test with a simple webhook testing tool

### Missing Data
- All fields are optional and may be null
- Check the `_metadata` section for debugging info
- Verify the trigger type matches your expectation

### Rate Limiting
- Webhooks have a 10-second timeout
- Failed webhooks won't retry automatically
- Monitor logs for delivery failures

## Need Help?
Check the application logs for webhook delivery status:
- Successful deliveries: `Successfully fired Zapier webhook: NEW_JV_SUBMISSION`
- Failed deliveries: `Zapier webhook failed: NEW_JV_SUBMISSION, status: 400`
- Errors: `Error firing Zapier webhook NEW_JV_SUBMISSION: [error message]`