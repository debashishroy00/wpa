#!/bin/bash

# Test production authentication
echo "Testing authentication against production backend..."
echo "Backend: https://wealthpath-backend.onrender.com"
echo ""

# Test health endpoint first
echo "1. Testing health endpoint..."
curl -s https://wealthpath-backend.onrender.com/health | jq '.' || echo "Health check failed"
echo ""

# Test login with the user credentials
echo "2. Testing login with debashishroy@gmail.com..."
response=$(curl -s -X POST https://wealthpath-backend.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=debashishroy@gmail.com&password=password123")

if echo "$response" | grep -q "access_token"; then
  echo "✅ Login successful!"
  echo "$response" | jq '.access_token' | cut -c1-50
  echo "..."
  
  # Extract token for further testing
  token=$(echo "$response" | jq -r '.access_token')
  
  echo ""
  echo "3. Testing authenticated endpoint..."
  curl -s -H "Authorization: Bearer $token" \
    https://wealthpath-backend.onrender.com/api/v1/financial/summary | jq '.' | head -20
else
  echo "❌ Login failed!"
  echo "$response" | jq '.'
fi