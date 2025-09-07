/**
 * Simple Auth Wrapper - Only render children if user has a token
 * Prevents automatic API calls when not authenticated
 */
import React from 'react';

interface AuthWrapperProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

const AuthWrapper: React.FC<AuthWrapperProps> = ({ children, fallback }) => {
  // Simple token check - don't validate, just check if exists
  const hasToken = !!localStorage.getItem('access_token');
  
  if (!hasToken) {
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