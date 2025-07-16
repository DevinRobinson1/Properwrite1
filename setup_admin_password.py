#!/usr/bin/env python3
"""
Admin Password Setup Script
Generates secure admin password hash for employee access to JV admin panel
"""

import os
import secrets
import string
from werkzeug.security import generate_password_hash

def generate_secure_password(length=16):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def setup_admin_password():
    """Set up admin password and hash for employee access"""
    print("=== Admin Password Setup ===")
    print("This script will generate a secure admin password for employee access to the JV admin panel.")
    print()
    
    # Generate secure password
    admin_password = generate_secure_password()
    
    # Generate password hash
    password_hash = generate_password_hash(admin_password)
    
    print(f"Generated Admin Password: {admin_password}")
    print(f"Password Hash: {password_hash}")
    print()
    
    # Show instructions
    print("=== Setup Instructions ===")
    print("1. Copy the password hash above")
    print("2. In your Replit project, go to Secrets tab")
    print("3. Add a new secret with:")
    print("   Key: ADMIN_PASSWORD_HASH")
    print(f"   Value: {password_hash}")
    print()
    print("4. Share the admin password with your employees:")
    print(f"   Password: {admin_password}")
    print()
    print("=== Employee Access Instructions ===")
    print("Your employees can now access the JV admin panel by:")
    print("1. Going to: https://your-domain.com/admin/login")
    print(f"2. Entering the password: {admin_password}")
    print("3. They will be redirected to the main admin dashboard")
    print("4. Click 'JV Deals' tab to access the enhanced JV admin panel")
    print()
    print("Note: The enhanced JV admin panel includes:")
    print("- Sortable data grid with deal filtering")
    print("- User portfolio management")
    print("- Advanced search and export features")
    print("- Real-time metrics and analytics")

if __name__ == "__main__":
    setup_admin_password()