/**
 * Auth Wrapper - Only render children if user has a VALID token
 * Prevents automatic API calls when not authenticated or tokens are invalid
 */
import React, { useState, useEffect } from 'react';

interface AuthWrapperProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

const AuthWrapper: React.FC<AuthWrapperProps> = ({ children, fallback }) => {
  const [isValid, setIsValid] = useState<boolean | null>(null); // null = checking, false = invalid, true = valid
  
  useEffect(() => {
    const checkTokenValidity = async () => {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        console.log('🚫 AuthWrapper: No token found');
        setIsValid(false);
        return;
      }
      
      // Simple token expiration check (if it's a JWT)
      try {
        console.log('🔍 AuthWrapper: Checking token expiration...');
        const payload = JSON.parse(atob(token.split('.')[1]));
        const currentTime = Math.floor(Date.now() / 1000);
        
        if (payload.exp && payload.exp < currentTime) {
          console.log('❌ AuthWrapper: Token is expired, clearing localStorage');
          // Clear all auth-related data
          localStorage.removeItem('access_token');
          localStorage.removeItem('auth_tokens');
          localStorage.removeItem('wealthpath-auth-store');
          setIsValid(false);
        } else {
          console.log('✅ AuthWrapper: Token appears valid (not expired)');
          setIsValid(true);
        }
      } catch (error) {
        // If token isn't JWT or can't be decoded, assume it's invalid
        console.log('❌ AuthWrapper: Token is not valid JWT format, clearing localStorage');
        localStorage.removeItem('access_token');
        localStorage.removeItem('auth_tokens');
        localStorage.removeItem('wealthpath-auth-store');
        setIsValid(false);
      }
    };
    
    checkTokenValidity();
  }, []);
  
  // Still checking token validity
  if (isValid === null) {
    return (
      <div className="bg-gray-800 rounded-lg shadow-md p-6 border border-gray-700 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-300">Validating authentication...</p>
      </div>
    );
  }
  
  // Token is invalid or doesn't exist
  if (!isValid) {
    return (
      <div className="bg-gray-800 rounded-lg shadow-md p-6 border border-gray-700 text-center">
        <div className="text-gray-400 mb-4">
          <span className="text-6xl">🔒</span>
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">Authentication Required</h3>
        <p className="text-gray-300 mb-4">
          Please log in to access this section.
        </p>
        <button 
          onClick={() => (window as any).quickLogin?.()}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
        >
          Quick Login (Test)
        </button>
        <p className="text-sm text-gray-400 mt-2">
          Or run <code className="bg-gray-700 px-2 py-1 rounded">window.quickLogin()</code> in console
        </p>
        {fallback}
      </div>
    );
  }

  return <>{children}</>;
};

export default AuthWrapper;