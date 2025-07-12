#!/usr/bin/env python3
"""
Generate a test admin password hash for demonstration
"""

from werkzeug.security import generate_password_hash

# Generate a test hash for demonstration purposes
# In production, use generate_admin_password.py to create a secure password
test_password = "SecureAdminPassword123!"
password_hash = generate_password_hash(test_password)

print(f"Test admin password hash generated:")
print(f"ADMIN_PASSWORD_HASH={password_hash}")
print(f"\nThis is for testing only. Use generate_admin_password.py to create a secure production password.")