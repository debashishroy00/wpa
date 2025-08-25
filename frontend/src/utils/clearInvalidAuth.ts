/**
 * Emergency Auth Clearing Utility
 * Clears all authentication data to stop 401 loops
 */

export const clearAllAuthData = () => {
  console.log('🧹 Clearing all authentication data...');
  
  // Clear all possible auth storage locations
  const keysToRemove = [
    'access_token',
    'refresh_token', 
    'auth_tokens',
    'wealthpath-auth-store',
    'user',
    'profile'
  ];
  
  keysToRemove.forEach(key => {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  });
  
  // Clear any other auth-related items
  for (let i = localStorage.length - 1; i >= 0; i--) {
    const key = localStorage.key(i);
    if (key && (key.includes('auth') || key.includes('token') || key.includes('user'))) {
      localStorage.removeItem(key);
    }
  }
  
  console.log('✅ All authentication data cleared');
  
  // Dispatch custom event to notify AuthWrapper components
  window.dispatchEvent(new CustomEvent('authCleared'));
};

// Auto-clear if page has clearAuth parameter
if (typeof window !== 'undefined') {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('clearAuth') || urlParams.get('reset')) {
    clearAllAuthData();
    // Remove the parameter and reload
    window.history.replaceState({}, document.title, window.location.pathname);
    setTimeout(() => window.location.reload(), 100);
  }
}

// Make it globally available
if (typeof window !== 'undefined') {
  (window as any).clearAllAuthData = clearAllAuthData;
  console.log('🛠️ Global function available: window.clearAllAuthData()');
}