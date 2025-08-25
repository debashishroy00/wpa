#!/usr/bin/env python3
"""
Test backend endpoints for 500 errors
"""
import requests

# Backend URL
BASE_URL = "https://wealthpath-backend.onrender.com"

print("=" * 60)
print("Backend Endpoint Testing")
print("=" * 60)

# 1. Login and get token
print("\n1. Getting authentication token...")
login_data = {
    "username": "debashishroy@gmail.com",
    "password": "password123"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f"✅ Token obtained: {token[:20]}...")
        
        # 2. Test the failing endpoints
        headers = {"Authorization": f"Bearer {token}"}
        
        endpoints_to_test = [
            "/api/v1/projections/comprehensive",
            "/api/v1/intelligence/analyze",
            "/api/v1/chat/message",
            "/api/v1/financial/summary"
        ]
        
        for endpoint in endpoints_to_test:
            print(f"\n2. Testing: {endpoint}")
            try:
                if endpoint == "/api/v1/chat/message":
                    # Chat endpoint needs POST with data
                    test_response = requests.post(
                        f"{BASE_URL}{endpoint}",
                        headers={**headers, "Content-Type": "application/json"},
                        json={
                            "message": "Test message",
                            "conversation_id": "test-123",
                            "user_id": 1
                        }
                    )
                else:
                    # Other endpoints are GET
                    test_response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
                
                print(f"   Status: {test_response.status_code}")
                
                if test_response.status_code == 200:
                    print("   ✅ Success")
                elif test_response.status_code == 500:
                    print(f"   ❌ 500 Error: {test_response.text[:200]}...")
                elif test_response.status_code == 404:
                    print("   ❌ 404 Not Found - endpoint may not exist")
                else:
                    print(f"   ⚠️  Status {test_response.status_code}: {test_response.text[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ Request failed: {e}")
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"❌ Login request failed: {e}")

print("\n" + "=" * 60)