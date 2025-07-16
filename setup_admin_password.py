#!/usr/bin/env python3
"""
Setup admin password directly in the environment for immediate use
"""

import os
from werkzeug.security import generate_password_hash

def setup_admin_password():
    """Set up admin password hash in environment variable"""
    password = '2UfdI!2t&MvND7W9'
    password_hash = generate_password_hash(password)
    
    # Set in current environment
    os.environ['ADMIN_PASSWORD_HASH'] = password_hash
    
    print(f"Admin password hash set up successfully!")
    print(f"Password: {password}")
    print(f"Hash: {password_hash}")
    
    # Verify it works
    from werkzeug.security import check_password_hash
    test_result = check_password_hash(password_hash, password)
    print(f"Verification test: {'PASSED' if test_result else 'FAILED'}")
    
    return password_hash

if __name__ == "__main__":
    setup_admin_password()