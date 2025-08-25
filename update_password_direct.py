#!/usr/bin/env python3
"""
Direct password update using Supabase connection
Run this script locally where Python dependencies are available
"""
import bcrypt
import psycopg2
import os
from datetime import datetime

# Supabase connection details (replace with your actual credentials)
# You need to get these from your Supabase dashboard
DATABASE_URL = os.environ.get('DATABASE_URL', '')

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def update_user_password(email: str, new_password: str):
    """Update user password directly in database"""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set")
        print("Please set it to your Supabase PostgreSQL connection string")
        print("Example: export DATABASE_URL='postgresql://user:pass@host:port/database'")
        return
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # First, check if user exists
        cursor.execute("SELECT id, email, is_active FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User not found: {email}")
            return
        
        user_id, user_email, is_active = user
        print(f"Found user: {user_email} (ID: {user_id}, Active: {is_active})")
        
        # Hash the new password
        hashed_password = hash_password(new_password)
        
        # Update the password
        cursor.execute(
            "UPDATE users SET password_hash = %s, updated_at = %s WHERE id = %s",
            (hashed_password, datetime.utcnow(), user_id)
        )
        
        conn.commit()
        print(f"✅ Password updated successfully for {email}")
        print(f"   New password: {new_password}")
        print(f"   Hash: {hashed_password[:20]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("WealthPath AI - Password Reset Tool")
    print("=" * 60)
    
    # Check if we have database URL
    if not DATABASE_URL:
        print("\n⚠️  Please set DATABASE_URL environment variable first!")
        print("You can find this in your Supabase project settings.")
        print("\nExample:")
        print('export DATABASE_URL="postgresql://postgres.xxxxx:password@aws-0-us-west-1.pooler.supabase.com:6543/postgres"')
    else:
        # Reset password for the main user
        update_user_password("debashishroy@gmail.com", "password123")