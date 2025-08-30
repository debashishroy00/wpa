#!/usr/bin/env python3
"""
Test script to check categorized entries API response
"""
import requests
import json

# Test the API endpoint directly
url = "http://localhost:8000/api/v1/financial/entries/categorized"

# Try to get a token first - we'll use admin access
auth_url = "http://localhost:8000/api/v1/auth/login"
auth_data = {
    "username": "debashishroy@gmail.com", 
    "password": "admin123"
}

try:
    # Login to get token
    auth_response = requests.post(auth_url, data=auth_data)
    if auth_response.status_code == 200:
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get categorized entries
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            expenses = data.get('categories', {}).get('expenses', {})
            
            print("Expense Categories and Entry Counts:")
            print("=" * 50)
            
            total_entries = 0
            for category, entries in expenses.items():
                count = len(entries)
                total_entries += count
                print(f"{category}: {count} entries")
                
                # Show details for each entry
                for entry in entries:
                    print(f"  - {entry['description']} (${entry['amount']})")
                print()
            
            print(f"Total expense entries in API response: {total_entries}")
            
            # Also check counts
            counts = data.get('counts', {})
            print(f"Total expense count from API: {counts.get('expenses', 'N/A')}")
            
        else:
            print(f"API Error: {response.status_code}")
            print(response.text)
    else:
        print(f"Auth Error: {auth_response.status_code}")
        print(auth_response.text)
        
except Exception as e:
    print(f"Error: {e}")