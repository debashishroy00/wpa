#!/usr/bin/env python3
"""
Test Supabase connection
"""
import psycopg2
import socket

# Connection details
supabase_conn = "postgresql://postgres:WealthPath2025@db.pxattzoxobqwkrwwtzae.supabase.co:5432/postgres"

def test_connection():
    print("Testing Supabase connection...")
    
    try:
        # Test DNS resolution first
        host = "db.pxattzoxobqwkrwwtzae.supabase.co"
        print(f"Resolving {host}...")
        ip = socket.gethostbyname(host)
        print(f"Resolved to: {ip}")
        
        # Try connection
        print("Attempting database connection...")
        conn = psycopg2.connect(supabase_conn)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"Connected successfully!")
        print(f"PostgreSQL version: {version[:50]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()