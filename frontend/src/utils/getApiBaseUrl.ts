/**
 * Smart API URL detection based on environment - UPDATED v2
 * Works automatically for both local development and production
 */
export const getApiBaseUrl = (): string => {
  const hostname = window.location.hostname;
  
  // FORCE PRODUCTION URL FOR ANY NON-LOCALHOST
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    console.log('🔗 PRODUCTION MODE (Utility) - Using render backend:', hostname);
    return 'https://wealthpath-backend.onrender.com';
  }
  
  // Localhost fallback
  console.log('🔍 Localhost detected (Utility) - using local backend');
  return 'http://localhost:8000';
};

// Export a ready-to-use constant
export const API_BASE_URL = getApiBaseUrl();

// Log which backend we're using (helpful for debugging)
console.log('🔗 API Base URL:', API_BASE_URL);