/**
 * Emergency Auth Reset Utility
 * Use this to clear authentication state and stop infinite loops
 */

// Emergency function to clear all authentication data
export const emergencyAuthReset = () => {
  console.log('🚨 Emergency auth reset initiated...');
  
  try {
    // Clear all possible auth storage
    localStorage.removeItem('auth_tokens');
    localStorage.removeItem('wealthpath-auth-store');
    sessionStorage.clear();
    
    // Clear any other auth-related items
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (key.includes('auth') || key.includes('token') || key.includes('user'))) {
        keysToRemove.push(key);
      }
    }
    
    keysToRemove.forEach(key => localStorage.removeItem(key));
    
    console.log('✅ Emergency auth reset complete');
    console.log('🔄 Please refresh the page');
    
    // Optionally auto-refresh
    setTimeout(() => {
      window.location.href = window.location.origin;
    }, 1000);
    
  } catch (error) {
    console.error('❌ Emergency auth reset failed:', error);
  }
};

// Auto-reset if URL contains clearAuth parameter
if (typeof window !== 'undefined') {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('clearAuth')) {
    console.log('🔍 clearAuth parameter detected, initiating emergency reset...');
    emergencyAuthReset();
  }
}

// Export for console access
if (typeof window !== 'undefined') {
  (window as any).emergencyAuthReset = emergencyAuthReset;
  console.log('🛠️ Emergency auth reset available globally: window.emergencyAuthReset()');
}