/**
 * Smart API URL detection based on environment
 * Works automatically for both local development and production
 */
export const getApiBaseUrl = (): string => {
  // Check if we have an environment variable set
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // Check if we're in development (localhost)
  if (window.location.hostname === 'localhost' || 
      window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000';  // Use local backend
  }
  
  // Default to production backend for any other domain
  return 'https://wealthpath-backend.onrender.com';
};

// Export a ready-to-use constant
export const API_BASE_URL = getApiBaseUrl();

// Log which backend we're using (helpful for debugging)
console.log('🔗 API Base URL:', API_BASE_URL);