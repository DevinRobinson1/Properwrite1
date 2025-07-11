# Email Service Setup Guide

## Overview
This guide helps you set up email sending from support@fundflowos.com for your Properwrite application.

## Option 1: Gmail SMTP (Recommended for Development)

### 1. Create a Gmail account or use existing
- Email: support@fundflowos.com (you'll need to create this Gmail account)
- Or use an existing Gmail account

### 2. Enable App Passwords (Required for Gmail)
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication if not already enabled
3. Go to "App passwords" section
4. Generate a new app password for "Mail"
5. Save this 16-character password

### 3. Set Environment Variables
Add these to your `.env` file:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=support@fundflowos.com
SMTP_PASSWORD=your_16_character_app_password
FROM_EMAIL=support@fundflowos.com
FROM_NAME=Properwrite Support
```

## Option 2: SendGrid (Recommended for Production)

### 1. Create SendGrid Account
- Go to [SendGrid.com](https://sendgrid.com/)
- Sign up for free account (100 emails/day free)
- Verify your account

### 2. Add Custom Domain
1. Go to Settings → Sender Authentication
2. Add your domain: fundflowos.com
3. Follow DNS setup instructions
4. Verify domain ownership

### 3. Create API Key
1. Go to Settings → API Keys
2. Create a new API key with "Full Access"
3. Save the API key securely

### 4. Set Environment Variables
Add these to your `.env` file:
```
SENDGRID_API_KEY=your_sendgrid_api_key
FROM_EMAIL=support@fundflowos.com
FROM_NAME=Properwrite Support
```

## Option 3: Mailgun (Alternative)

### 1. Create Mailgun Account
- Go to [Mailgun.com](https://www.mailgun.com/)
- Sign up for free account (5,000 emails/month free)

### 2. Add Custom Domain
1. Go to Domains → Add New Domain
2. Add: fundflowos.com
3. Follow DNS setup instructions
4. Verify domain

### 3. Get API Key
1. Go to Settings → API Keys
2. Copy your Private API key

### 4. Set Environment Variables
Add these to your `.env` file:
```
MAILGUN_API_KEY=your_mailgun_api_key
MAILGUN_DOMAIN=fundflowos.com
FROM_EMAIL=support@fundflowos.com
FROM_NAME=Properwrite Support
```

## DNS Setup for Custom Domain

### For SendGrid or Mailgun:
You'll need to add these DNS records to your fundflowos.com domain:

**SPF Record (TXT)**
```
v=spf1 include:sendgrid.net ~all
```
or for Mailgun:
```
v=spf1 include:mailgun.org ~all
```

**DKIM Record (TXT)**
- Follow the specific instructions from SendGrid/Mailgun dashboard
- Usually involves adding a TXT record with a specific key

**DMARC Record (TXT)**
```
v=DMARC1; p=none; rua=mailto:support@fundflowos.com
```

## Testing the Email Service

After setup, test by running:
```python
from email_service import email_service

# Test sending
success = email_service.send_email(
    to_email="your_test_email@gmail.com",
    subject="Test Email",
    html_content="<h1>Test successful!</h1>"
)

print(f"Email sent: {success}")
```

## Security Best Practices

1. **Never commit email credentials to code**
2. **Use environment variables for all sensitive data**
3. **Rotate API keys regularly**
4. **Monitor email sending quotas**
5. **Set up proper SPF/DKIM/DMARC records**

## Troubleshooting

### Common Issues:
- **SMTP Auth Failed**: Check app password is correct
- **Domain not verified**: Complete domain verification process
- **Rate limits**: Check your sending quotas
- **Spam folder**: Ensure proper DNS records are set

### Email Deliverability Tips:
- Use authenticated domain (support@fundflowos.com)
- Set up SPF, DKIM, and DMARC records
- Monitor bounce rates
- Include unsubscribe links in marketing emails
- Warm up your sending reputation gradually

## Integration with Properwrite

The email service is already integrated with these features:
- Welcome emails for new users
- Password reset emails
- Credit purchase confirmations
- Support notifications

To use in your application:
```python
from email_service import email_service

# Send welcome email
email_service.send_welcome_email(user_email, user_name)

# Send custom email
email_service.send_email(to_email, subject, html_content)
```