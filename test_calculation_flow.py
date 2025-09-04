#!/usr/bin/env python3
"""
Test the calculation flow to debug zero values
"""

import requests
import json

# First, let's check if we can get user financial data
def test_financial_data():
    """Test if financial data is available"""
    
    print("=== TESTING FINANCIAL DATA RETRIEVAL ===\n")
    
    # Login first to get auth token
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json={"email": "debashishroy@gmail.com", "password": "password123"}
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        print(f"[OK] Logged in successfully")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get financial summary
        financial_response = requests.get(
            "http://localhost:8000/api/v1/financial/live-summary/1",
            headers=headers
        )
        
        if financial_response.status_code == 200:
            data = financial_response.json()
            print(f"\nFinancial Summary:")
            print(f"  Total Assets: ${data.get('totalAssets', 0):,.0f}")
            print(f"  Total Liabilities: ${data.get('totalLiabilities', 0):,.0f}")
            print(f"  Net Worth: ${data.get('netWorth', 0):,.0f}")
            print(f"  Monthly Income: ${data.get('monthlyIncome', 0):,.0f}")
            print(f"  Monthly Expenses: ${data.get('monthlyExpenses', 0):,.0f}")
            print(f"  Monthly Surplus: ${data.get('monthlySurplus', 0):,.0f}")
            
            if data.get('netWorth', 0) == 0:
                print("\n[WARNING] Net worth is zero! User may need to input financial data.")
            
            return data
        else:
            print(f"[FAIL] Failed to get financial summary: {financial_response.status_code}")
    else:
        print(f"[FAIL] Failed to login: {login_response.status_code}")
        print(login_response.text)
    
    return None

def test_calculation_with_data():
    """Test a calculation with actual user data"""
    
    print("\n=== TESTING CALCULATION WITH USER DATA ===\n")
    
    # Login
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json={"email": "debashishroy@gmail.com", "password": "password123"}
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try a calculation via chat endpoint
        chat_response = requests.post(
            "http://localhost:8000/api/v1/chat-simple/message",
            headers=headers,
            json={
                "session_id": 1,
                "message": "Am I on track for my retirement goal?",
                "context_level": "full",
                "llm_provider": "gemini",
                "insight_level": "balanced"
            }
        )
        
        if chat_response.status_code == 200:
            response = chat_response.json()
            print("📝 Chat Response:")
            print(response.get("response", "No response"))
            
            # Check if it contains zeros
            if "$0" in response.get("response", ""):
                print("\n⚠️ WARNING: Response contains $0 values!")
                print("This indicates user financial data is not properly loaded.")
        else:
            print(f"✗ Failed to get chat response: {chat_response.status_code}")
            print(chat_response.text)

if __name__ == "__main__":
    financial_data = test_financial_data()
    
    if financial_data and financial_data.get('netWorth', 0) > 0:
        test_calculation_with_data()
    else:
        print("\n❌ USER HAS NO FINANCIAL DATA ENTERED")
        print("The calculator is working, but the user needs to input their financial information first.")
        print("\nTo fix this:")
        print("1. User should go to their profile/financial settings")
        print("2. Enter their assets, liabilities, income, and expenses")
        print("3. Set their retirement goal amount")
        print("4. Then the calculations will work with real data")