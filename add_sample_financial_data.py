#!/usr/bin/env python3
"""
Add sample financial data to the database for user testing
"""

import requests
import json

def add_financial_data():
    """Add sample financial data for the test user"""
    
    print("=== ADDING SAMPLE FINANCIAL DATA ===\n")
    
    # Login first
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        data={"username": "debashishroy@gmail.com", "password": "password123"}
    )
    
    if login_response.status_code != 200:
        print(f"[FAIL] Failed to login: {login_response.status_code}")
        return False
    
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Logged in successfully")
    
    # Add financial entries
    financial_entries = [
        {
            "category": "retirement_accounts",
            "subcategory": "401k",
            "amount": 310216,
            "description": "401k retirement account"
        },
        {
            "category": "investment_accounts", 
            "subcategory": "brokerage",
            "amount": 560784,
            "description": "Investment brokerage account"
        },
        {
            "category": "real_estate",
            "subcategory": "primary_residence",
            "amount": 1450000,
            "description": "Primary home value"
        },
        {
            "category": "cash_accounts",
            "subcategory": "savings",
            "amount": 108945,
            "description": "Savings account"
        },
        {
            "category": "alternative_investments",
            "subcategory": "cryptocurrency",
            "amount": 114600,
            "description": "Bitcoin holdings"
        },
        {
            "category": "liabilities",
            "subcategory": "mortgage",
            "amount": -280000,
            "description": "Home mortgage balance"
        },
        {
            "category": "income",
            "subcategory": "salary",
            "amount": 15347,
            "description": "Monthly salary income",
            "is_monthly": True
        },
        {
            "category": "expenses",
            "subcategory": "living_expenses",
            "amount": 7484,
            "description": "Monthly living expenses",
            "is_monthly": True
        }
    ]
    
    success_count = 0
    for entry in financial_entries:
        response = requests.post(
            "http://localhost:8000/api/v1/financial/entries",
            headers=headers,
            json=entry
        )
        
        if response.status_code in [200, 201]:
            success_count += 1
            print(f"[OK] Added {entry['subcategory']}: ${entry['amount']:,.0f}")
        else:
            print(f"[WARN] Failed to add {entry['subcategory']}: {response.status_code}")
    
    print(f"\nAdded {success_count}/{len(financial_entries)} entries")
    
    # Set retirement goal
    goal_response = requests.post(
        "http://localhost:8000/api/v1/goals",
        headers=headers,
        json={
            "goal_type": "retirement",
            "name": "Retirement Goal",
            "target_amount": 3500000,
            "target_date": "2035-01-01",
            "priority": "high",
            "category": "retirement"
        }
    )
    
    if goal_response.status_code in [200, 201]:
        print(f"[OK] Set retirement goal: $3,500,000")
    else:
        print(f"[WARN] Failed to set retirement goal: {goal_response.status_code}")
    
    # Verify the data
    print("\n=== VERIFYING FINANCIAL DATA ===\n")
    
    summary_response = requests.get(
        "http://localhost:8000/api/v1/financial/live-summary/1",
        headers=headers
    )
    
    if summary_response.status_code == 200:
        data = summary_response.json()
        print(f"Total Assets: ${data.get('totalAssets', 0):,.0f}")
        print(f"Total Liabilities: ${data.get('totalLiabilities', 0):,.0f}")
        print(f"Net Worth: ${data.get('netWorth', 0):,.0f}")
        print(f"Monthly Income: ${data.get('monthlyIncome', 0):,.0f}")
        print(f"Monthly Expenses: ${data.get('monthlyExpenses', 0):,.0f}")
        print(f"Monthly Surplus: ${data.get('monthlySurplus', 0):,.0f}")
        
        if data.get('netWorth', 0) > 0:
            print("\n[SUCCESS] Financial data added successfully!")
            return True
    
    return False

if __name__ == "__main__":
    if add_financial_data():
        print("\n" + "="*50)
        print("NEXT STEPS:")
        print("1. Refresh the web app")
        print("2. Try the retirement calculator again")
        print("3. You should now see real values instead of $0")
    else:
        print("\n[ERROR] Failed to add financial data")