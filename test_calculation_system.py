#!/usr/bin/env python3
"""
Test script for the new ComprehensiveFinancialCalculator system
Tests the user's original problematic queries to verify fixes
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_calculation_query(query: str, description: str):
    """Test a query that should trigger mathematical calculation"""
    
    print(f"\n{'='*60}")
    print(f"CALCULATION TEST: {description}")
    print(f"Query: '{query}'")
    print("="*60)
    
    # Login first
    login_response = requests.post(f"{API_BASE}/api/v1/auth/login", data={
        "username": "debashishroy@gmail.com",
        "password": "Test123!"
    })
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Send the query
    payload = {
        "message": query,
        "provider": "gemini",
        "model_tier": "dev",  
        "insight_level": "balanced"
    }
    
    start_time = time.time()
    response = requests.post(
        f"{API_BASE}/api/v1/chat-simple/message",
        json=payload,
        headers=headers
    )
    end_time = time.time()
    
    print(f"Response time: {end_time - start_time:.2f}s")
    
    if response.status_code != 200:
        print(f"Request failed: {response.status_code}")
        print(f"Error: {response.text}")
        return
    
    result = response.json()
    
    # Check if calculation was performed
    calculation_performed = "calculation_performed" in result
    calculation_type = result.get("calculation_type", "None")
    
    print(f"Calculation performed: {calculation_performed}")
    if calculation_performed:
        print(f"Calculation type: {calculation_type}")
    
    print(f"Confidence: {result.get('confidence', 'Unknown')}")
    print(f"Warnings: {result.get('warnings', [])}")
    
    # Print response (truncated)
    response_text = result.get("response", "No response")
    if len(response_text) > 500:
        response_text = response_text[:500] + "..."
    
    print(f"\nResponse:\n{response_text}")
    
    # Check for mathematical accuracy indicators
    if any(indicator in response_text.lower() for indicator in ["years", "timeline", "goal", "calculate"]):
        print("SUCCESS: Response contains mathematical concepts")
    else:
        print("WARNING: Response may not contain expected mathematical results")
    
    return result

def main():
    """Test the user's original problematic scenarios"""
    
    print("Testing ComprehensiveFinancialCalculator System")
    print("Testing user's original problematic queries...")
    
    # Test 1: Basic retirement timeline (this should work)
    test_calculation_query(
        "Am I on track for my retirement goal?",
        "Basic retirement timeline assessment"
    )
    
    # Test 2: Goal reduction scenario (this was broken before)
    test_calculation_query(
        "what if i reduce my goal to 3000000, how many years it will shave off",
        "Goal reduction impact calculation"
    )
    
    # Test 3: Growth rate specification (this had calculation errors)
    test_calculation_query(
        "consider 7% growth rate",
        "Growth rate specification"
    )
    
    # Test 4: Direct years question (this avoided giving numbers)
    test_calculation_query(
        "how many years exactly can i shave off",
        "Direct years calculation question"
    )
    
    # Test 5: Complex combination (growth + goal change)
    test_calculation_query(
        "If I reduce my retirement goal to $3M with 7% growth rate, how many years will that save me?",
        "Complex goal + growth rate calculation"
    )
    
    print(f"\n{'='*60}")
    print("Testing completed!")
    print("="*60)

if __name__ == "__main__":
    main()