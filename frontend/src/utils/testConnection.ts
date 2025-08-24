/**
 * Test utility to verify backend connection
 * Use this to check if the frontend can connect to the backend API
 */

import { getApiBaseUrl } from './getApiBaseUrl';

export const testBackendConnection = async (): Promise<boolean> => {
  const baseURL = getApiBaseUrl();
  
  try {
    console.log('🔍 Testing backend connection to:', baseURL);
    
    const response = await fetch(`${baseURL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      console.error('❌ Backend connection failed with status:', response.status);
      return false;
    }
    
    const data = await response.json();
    console.log('✅ Backend connected successfully:', data);
    console.log('📍 Backend URL:', baseURL);
    console.log('📊 Response:', {
      status: data.status,
      service: data.service,
      version: data.version
    });
    
    return true;
  } catch (error) {
    console.error('❌ Backend connection error:', error);
    console.error('📍 Attempted URL:', `${baseURL}/health`);
    console.error('💡 Make sure the backend is running and accessible');
    return false;
  }
};

// Auto-run test on module import (optional - comment out if not needed)
if (typeof window !== 'undefined') {
  // Run test after a short delay to ensure the app is loaded
  setTimeout(() => {
    testBackendConnection().then(connected => {
      if (connected) {
        console.log('🎉 Backend connectivity test passed!');
      } else {
        console.warn('⚠️ Backend connectivity test failed - check your configuration');
      }
    });
  }, 1000);
}