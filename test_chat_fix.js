// Chat URL Fix Verification Script
// Run this in browser console on https://wpa-dusky.vercel.app

console.log("🔍 Testing Chat URL Fix");
console.log("=" * 50);

// 1. Check if getApiBaseUrl is available and working
if (typeof getApiBaseUrl === 'function') {
  console.log("✅ getApiBaseUrl function available");
  console.log("🔗 API Base URL:", getApiBaseUrl());
} else {
  console.log("❌ getApiBaseUrl function not found");
}

// 2. Check environment detection
console.log("🌍 Current hostname:", window.location.hostname);
console.log("🔍 Environment variables:", {
  VITE_API_BASE_URL: typeof import !== 'undefined' && import.meta?.env?.VITE_API_BASE_URL || 'Not available'
});

// 3. Test direct backend connection
console.log("\n🧪 Testing direct backend connection...");
const token = JSON.parse(localStorage.getItem('auth_tokens') || '{}').access_token;
if (token) {
  console.log("✅ Token found:", token.substring(0, 20) + "...");
  
  // Test with correct backend URL
  fetch('https://wealthpath-backend.onrender.com/api/v1/chat/message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      message: "Test message from console",
      session_id: "console-test-" + Date.now(),
      user_id: 1
    })
  })
  .then(r => {
    console.log("📡 Response status:", r.status);
    return r.json();
  })
  .then(data => {
    console.log("📨 Response data:", data);
    if (data.error) {
      console.log("❌ Backend error:", data.error);
    } else {
      console.log("✅ Backend responded successfully");
    }
  })
  .catch(err => {
    console.log("❌ Request failed:", err);
  });
} else {
  console.log("❌ No token found. Please login first.");
}

// 4. Check if chat component is using the right URL
console.log("\n🔍 Checking chat component implementation...");
const chatElements = document.querySelectorAll('[data-testid*="chat"], [class*="chat"], [id*="chat"]');
console.log(`📱 Found ${chatElements.length} chat-related elements`);

// 5. Network monitoring
console.log("\n🌐 Monitor network requests for relative URLs:");
console.log("Open Network tab and send a chat message.");
console.log("Look for POST requests to /api/v1/chat/message (BAD) vs full URLs (GOOD)");

console.log("\n" + "=" * 50);
console.log("🎯 Quick Fix: If seeing relative URLs, try:");
console.log("1. Hard refresh (Ctrl+F5)");
console.log("2. Clear cache and hard reload");
console.log("3. Check if latest build is deployed on Vercel");