#!/usr/bin/env python3
"""
Test the new retirement-readiness endpoint
"""

import requests
import json

# Test endpoint - you'll need to adjust the token
BASE_URL = "http://localhost:8000"
TOKEN = "YOUR_TOKEN_HERE"  # Replace with actual token

def test_retirement_endpoint():
    """Test the retirement readiness endpoint"""
    
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/financial/retirement-readiness",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("Retirement Readiness Response:")
            print(json.dumps(data, indent=2))
            
            if data.get('years_to_retirement') is not None:
                print(f"\nYears to Financial Independence: {data['years_to_retirement']}")
                print(f"Retirement Age: {data.get('retirement_age', 'N/A')}")
                print(f"Current Liquid Assets: ${data.get('current_liquid_assets', 0):,.0f}")
                print(f"Target Portfolio: ${data.get('target_portfolio', 0):,.0f}")
                print(f"Message: {data.get('message', '')}")
            else:
                print(f"Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"Request failed with status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error testing endpoint: {e}")

if __name__ == "__main__":
    print("Testing Retirement Readiness Endpoint")
    print("=" * 40)
    print("NOTE: You need to set the TOKEN variable with a valid JWT token")
    print("You can get this from browser DevTools after logging in")
    print()
    
    # Uncomment after setting token
    # test_retirement_endpoint()