#!/usr/bin/env python3
"""
Test backend authentication directly
"""
import requests
import json

# Backend URL
BASE_URL = "https://wealthpath-backend.onrender.com"

print("Testing WealthPath Backend Authentication")
print("=" * 50)

# 1. Test health endpoint
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   Error: {e}")

# 2. Test login with correct credentials
print("\n2. Testing login with debashishroy@gmail.com...")
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
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("   ✅ Login successful!")
        print(f"   Access token: {data.get('access_token', '')[:50]}...")
        
        # 3. Test authenticated endpoint
        if 'access_token' in data:
            print("\n3. Testing authenticated endpoint...")
            headers = {"Authorization": f"Bearer {data['access_token']}"}
            response = requests.get(f"{BASE_URL}/api/v1/financial/summary", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Authenticated request successful!")
    else:
        print(f"   ❌ Login failed: {response.json()}")
        
except Exception as e:
    print(f"   Error: {e}")

# 4. Try with different password variations
print("\n4. Testing password variations...")
passwords = ["Password123", "Password123!", "password", "admin123"]
for pwd in passwords:
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": "debashishroy@gmail.com", "password": pwd},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            print(f"   ✅ SUCCESS with password: {pwd}")
            break
        else:
            print(f"   ❌ Failed with: {pwd}")
    except:
        pass