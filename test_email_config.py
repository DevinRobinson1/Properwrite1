#!/usr/bin/env python3
"""
Test Email Configuration
Tests various SMTP configurations for support@fundflowos.com
"""

import os
import smtplib
from email.mime.text import MIMEText
import logging

logging.basicConfig(level=logging.INFO)

def test_smtp_config(smtp_server, smtp_port, username, password, to_email):
    """Test a specific SMTP configuration"""
    try:
        print(f"\n=== Testing SMTP Configuration ===")
        print(f"Server: {smtp_server}")
        print(f"Port: {smtp_port}")
        print(f"Username: {username}")
        print(f"Password: {'*' * len(password) if password else 'None'}")
        
        # Create test message
        msg = MIMEText("This is a test email from your team invitation system.")
        msg['Subject'] = 'SMTP Configuration Test'
        msg['From'] = username
        msg['To'] = to_email
        
        # Try to connect and send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Enable debug output
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ SUCCESS: Email sent successfully via {smtp_server}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def main():
    username = os.environ.get('SMTP_USERNAME', '')
    password = os.environ.get('SMTP_PASSWORD', '')
    to_email = 'devin@pureflairhomes.com'
    
    print(f"Testing email configurations for: {username}")
    print(f"Sending test email to: {to_email}")
    
    if not username or not password:
        print("❌ ERROR: SMTP_USERNAME or SMTP_PASSWORD not set")
        return
    
    # Test configurations
    configurations = [
        # Google Workspace (for custom domains using Gmail)
        ('smtp.gmail.com', 587, username, password),
        
        # Try the domain's direct SMTP server
        ('smtp.fundflowos.com', 587, username, password),
        ('mail.fundflowos.com', 587, username, password),
        
        # Common hosting providers
        ('smtp.hostgator.com', 587, username, password),
        ('smtp.godaddy.com', 587, username, password),
        ('smtp.bluehost.com', 587, username, password),
        
        # Alternative ports
        ('smtp.gmail.com', 465, username, password),
        ('smtp.gmail.com', 25, username, password),
    ]
    
    success_count = 0
    for smtp_server, smtp_port, user, pwd in configurations:
        if test_smtp_config(smtp_server, smtp_port, user, pwd, to_email):
            success_count += 1
            print(f"\n🎉 WORKING CONFIGURATION FOUND:")
            print(f"   SMTP_SERVER={smtp_server}")
            print(f"   SMTP_PORT={smtp_port}")
            print(f"   SMTP_USERNAME={user}")
            break
    
    if success_count == 0:
        print(f"\n❌ No working SMTP configuration found.")
        print(f"This usually means:")
        print(f"1. The email account needs an app-specific password")
        print(f"2. The domain uses a different email provider")
        print(f"3. The email account has two-factor authentication enabled")
        print(f"\nPlease check with your email provider for the correct SMTP settings.")

if __name__ == "__main__":
    main()