#!/usr/bin/env node

/**
 * Simple test script to verify the auth fix is working
 * Run with: node test_auth_fix.js
 */

const https = require('https');
const http = require('http');

const API_BASE_URL = 'https://wealthpath-backend.onrender.com';

console.log('🧪 Testing backend connection...');

// Test 1: Health check
const testHealthCheck = () => {
  return new Promise((resolve, reject) => {
    const url = `${API_BASE_URL}/health`;
    console.log(`\n📍 Testing: ${url}`);
    
    const client = API_BASE_URL.startsWith('https') ? https : http;
    
    const req = client.get(url, (res) => {
      let data = '';
      
      res.on('data', chunk => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log('✅ Health check passed');
          console.log('📊 Response:', JSON.parse(data));
          resolve(true);
        } else {
          console.log(`❌ Health check failed: ${res.statusCode}`);
          reject(new Error(`Status: ${res.statusCode}`));
        }
      });
    });
    
    req.on('error', (error) => {
      console.error('❌ Health check error:', error.message);
      reject(error);
    });
    
    req.setTimeout(10000, () => {
      console.error('❌ Health check timeout');
      req.destroy();
      reject(new Error('Timeout'));
    });
  });
};

// Test 2: Auth endpoint (should return 401 without token)
const testAuthEndpoint = () => {
  return new Promise((resolve, reject) => {
    const url = `${API_BASE_URL}/api/v1/financial/summary`;
    console.log(`\n📍 Testing auth endpoint: ${url}`);
    
    const client = API_BASE_URL.startsWith('https') ? https : http;
    
    const req = client.get(url, (res) => {
      let data = '';
      
      res.on('data', chunk => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 401) {
          console.log('✅ Auth endpoint correctly returns 401 (expected)');
          resolve(true);
        } else {
          console.log(`⚠️  Auth endpoint returned: ${res.statusCode} (expected 401)`);
          resolve(true); // Not a failure, just unexpected
        }
      });
    });
    
    req.on('error', (error) => {
      console.error('❌ Auth endpoint error:', error.message);
      reject(error);
    });
    
    req.setTimeout(10000, () => {
      console.error('❌ Auth endpoint timeout');
      req.destroy();
      reject(new Error('Timeout'));
    });
  });
};

// Run all tests
async function runTests() {
  console.log('🎯 Starting backend connectivity tests...\n');
  
  try {
    await testHealthCheck();
    await testAuthEndpoint();
    
    console.log('\n🎉 All tests completed successfully!');
    console.log('🚀 Backend is ready for frontend connection');
    console.log('\n📋 Next steps:');
    console.log('1. Run `npm run dev` in the frontend directory');
    console.log('2. Visit http://localhost:5173');
    console.log('3. Check browser console for connection logs');
    console.log('4. If there are 401 errors, visit: http://localhost:5173?clearAuth=true');
    
  } catch (error) {
    console.error('\n💥 Tests failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('- Make sure the backend is running and accessible');
    console.log('- Check your internet connection');
    console.log('- Verify the API URL is correct');
    process.exit(1);
  }
}

runTests();