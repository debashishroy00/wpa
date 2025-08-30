#!/usr/bin/env python3
"""
Debug script to check all expense entries in the database
"""
import os
import sys
sys.path.append('backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://wealthpath_user:wealthpath_dev_password@localhost:5432/wealthpath_db"

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Query all expense entries for user 1 (debashishroy@gmail.com)
    query = text("""
        SELECT id, description, category, subcategory, amount, frequency, created_at 
        FROM financial_entries 
        WHERE user_id = 1 
        AND category = 'expenses'
        ORDER BY created_at DESC;
    """)
    
    result = session.execute(query)
    entries = result.fetchall()
    
    print(f"Found {len(entries)} expense entries:")
    print("=" * 80)
    
    for i, entry in enumerate(entries, 1):
        print(f"{i:2d}. ID: {entry.id}")
        print(f"    Description: {entry.description}")
        print(f"    Category: {entry.category}")  
        print(f"    Subcategory: {entry.subcategory}")
        print(f"    Amount: ${entry.amount}")
        print(f"    Frequency: {entry.frequency}")
        print(f"    Created: {entry.created_at}")
        print()
        
    session.close()
    
except Exception as e:
    print(f"Error: {e}")
    print("Make sure PostgreSQL is running and accessible")