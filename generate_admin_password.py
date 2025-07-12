#!/usr/bin/env python3
"""
Generate secure password hash for admin authentication
Usage: python generate_admin_password.py
"""

from werkzeug.security import generate_password_hash
import getpass
import os

def main():
    print("=== Fund Flow OS Admin Password Generator ===")
    print("\nThis script generates a secure password hash for admin authentication.")
    print("You'll need to set the ADMIN_PASSWORD_HASH environment variable with the generated hash.\n")
    
    # Get password from user
    while True:
        password = getpass.getpass("Enter admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        
        if password != confirm:
            print("Passwords don't match. Please try again.\n")
            continue
            
        if len(password) < 12:
            print("Password must be at least 12 characters long. Please try again.\n")
            continue
            
        break
    
    # Generate hash
    password_hash = generate_password_hash(password)
    
    print("\n" + "="*60)
    print("Password hash generated successfully!")
    print("="*60)
    print("\nAdd this to your environment variables:")
    print(f"\nADMIN_PASSWORD_HASH={password_hash}")
    print("\nFor Replit:")
    print("1. Go to the Secrets tab in your Replit project")
    print("2. Add a new secret with key: ADMIN_PASSWORD_HASH")
    print(f"3. Paste this value: {password_hash}")
    print("\nFor local development:")
    print(f"export ADMIN_PASSWORD_HASH='{password_hash}'")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()