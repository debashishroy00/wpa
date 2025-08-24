/**
 * Simple Authentication Helper
 * No validation, just check if token exists
 */

// Simple token check - don't validate with backend
export const checkAuth = (): boolean => {
  const token = localStorage.getItem('access_token');
  if (token) {
    console.log('✅ Token found - assuming valid');
    return true;
  } else {
    console.log('❌ No token found');
    return false;
  }
};

// Simple login status
export const isLoggedIn = (): boolean => {
  return checkAuth();
};

// Get token without validation
export const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

// Set token simply
export const setToken = (token: string): void => {
  localStorage.setItem('access_token', token);
  console.log('✅ Token stored');
};

// Clear token
export const clearToken = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('auth_tokens');
  localStorage.removeItem('refresh_token');
  console.log('🗑️ Tokens cleared');
};

// Simple user info from token (if it's a JWT)
export const getUserFromToken = (): any => {
  const token = getToken();
  if (!token) return null;
  
  try {
    // Try to decode JWT payload
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      id: payload.sub,
      email: payload.email || 'user@example.com',
      name: payload.name || 'User'
    };
  } catch (error) {
    console.log('Token is not JWT format, that\'s ok');
    return { id: 1, email: 'user@example.com', name: 'User' };
  }
};

console.log('🔧 Simple auth utils loaded');
console.log('📋 Available functions: checkAuth(), isLoggedIn(), getToken(), setToken(), clearToken()');