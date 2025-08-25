#!/usr/bin/env python
"""
Reset password for a user in the database
"""
import os
import sys
sys.path.append('/mnt/c/projects/wpa/backend')

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User

def reset_password(email: str, new_password: str):
    """Reset password for a user"""
    db = SessionLocal()
    try:
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User not found: {email}")
            return False
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        db.commit()
        
        print(f"✅ Password reset successfully for: {email}")
        print(f"   User ID: {user.id}")
        print(f"   Is Active: {user.is_active}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Reset password for the test user
    reset_password("debashishroy@gmail.com", "password123")