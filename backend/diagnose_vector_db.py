#!/usr/bin/env python3
"""
URGENT: Vector Database Diagnostic Script
Diagnoses document count loss from 48 to 7 documents
"""

import chromadb
from chromadb.config import Settings
import sqlite3
import os

def diagnose_vector_database():
    """Examine both vector databases to understand document loss"""
    
    print("🔍 VECTOR DATABASE DIAGNOSTIC")
    print("=" * 50)
    
    # Check main vector_db
    print("\n1. MAIN VECTOR DATABASE (/vector_db)")
    try:
        client = chromadb.PersistentClient(path="/mnt/c/projects/wpa/backend/vector_db")
        collections = client.list_collections()
        
        print(f"Collections found: {len(collections)}")
        for collection in collections:
            print(f"  - Collection: {collection.name}")
            count = collection.count()
            print(f"    Documents: {count}")
            
            if count > 0:
                # Sample first few documents
                sample = collection.get(limit=5)
                print(f"    Sample IDs: {sample.get('ids', [])[0:3] if sample.get('ids') else 'None'}")
                if sample.get('metadatas'):
                    print(f"    Sample metadata keys: {list(sample['metadatas'][0].keys()) if sample['metadatas'] else 'None'}")
    except Exception as e:
        print(f"    ❌ Error accessing main vector_db: {e}")
    
    # Check secure vector_db  
    print("\n2. SECURE VECTOR DATABASE (/vector_db_secure)")
    try:
        client_secure = chromadb.PersistentClient(path="/mnt/c/projects/wpa/backend/vector_db_secure")
        collections_secure = client_secure.list_collections()
        
        print(f"Collections found: {len(collections_secure)}")
        for collection in collections_secure:
            print(f"  - Collection: {collection.name}")
            count = collection.count()
            print(f"    Documents: {count}")
            
            if count > 0:
                # Sample first few documents
                sample = collection.get(limit=5)
                print(f"    Sample IDs: {sample.get('ids', [])[0:3] if sample.get('ids') else 'None'}")
                if sample.get('metadatas'):
                    print(f"    Sample metadata keys: {list(sample['metadatas'][0].keys()) if sample['metadatas'] else 'None'}")
    except Exception as e:
        print(f"    ❌ Error accessing secure vector_db: {e}")
    
    # Check SQLite databases for traces
    print("\n3. SQLITE DATABASE ANALYSIS")
    
    # Main DB
    main_db_path = "/mnt/c/projects/wpa/backend/vector_db/chroma.sqlite3"
    if os.path.exists(main_db_path):
        print(f"\nMain DB file size: {os.path.getsize(main_db_path)} bytes")
        try:
            conn = sqlite3.connect(main_db_path)
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables: {[t[0] for t in tables]}")
            
            # Check collections table
            cursor.execute("SELECT id, name FROM collections")
            collections_data = cursor.fetchall()
            print(f"Collections in DB: {collections_data}")
            
            conn.close()
        except Exception as e:
            print(f"    ❌ Error reading main SQLite: {e}")
    
    # Secure DB
    secure_db_path = "/mnt/c/projects/wpa/backend/vector_db_secure/chroma.sqlite3"
    if os.path.exists(secure_db_path):
        print(f"\nSecure DB file size: {os.path.getsize(secure_db_path)} bytes")
        try:
            conn = sqlite3.connect(secure_db_path)
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables: {[t[0] for t in tables]}")
            
            # Check collections table
            cursor.execute("SELECT id, name FROM collections")
            collections_data = cursor.fetchall()
            print(f"Collections in DB: {collections_data}")
            
            conn.close()
        except Exception as e:
            print(f"    ❌ Error reading secure SQLite: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 DIAGNOSIS COMPLETE")
    print("\nNext steps:")
    print("1. Compare current counts vs expected 48 documents")
    print("2. Check for backup/source data if documents are missing")
    print("3. Investigate which service caused the deletion")

if __name__ == "__main__":
    diagnose_vector_database()