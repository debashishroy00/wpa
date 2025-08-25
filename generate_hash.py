#!/usr/bin/env python3
"""
Generate bcrypt hash for password123
"""
import hashlib

def simple_bcrypt_hash(password: str) -> str:
    """Generate a bcrypt-compatible hash using available libraries"""
    try:
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except ImportError:
        print("bcrypt not available, using hashlib fallback")
        # Simple SHA256 hash as fallback (not recommended for production)
        salt = "wealthpath_salt"
        return hashlib.sha256((password + salt).encode()).hexdigest()

if __name__ == "__main__":
    password = "password123"
    hash_result = simple_bcrypt_hash(password)
    print("=" * 60)
    print("Password Hash Generator")
    print("=" * 60)
    print(f"Password: {password}")
    print(f"Hash: {hash_result}")
    print("=" * 60)
    print("\nTo update in Supabase:")
    print("1. Go to Supabase Dashboard -> Table Editor -> users table")
    print("2. Find row where email = 'debashishroy@gmail.com'")
    print("3. Update password_hash column with the hash above")
    print("4. Save changes")