/**
 * Centralized Error Handling Utilities
 * Provides consistent error handling across the application
 */

export interface AppError {
  type: 'network' | 'authentication' | 'authorization' | 'server' | 'validation' | 'unknown';
  message: string;
  originalError?: Error;
  statusCode?: number;
  timestamp: number;
}

export class ErrorHandler {
  /**
   * Parse and categorize an error
   */
  static parseError(error: any): AppError {
    const timestamp = Date.now();
    
    // Network/Connection errors
    if (error instanceof TypeError || error.name === 'TypeError') {
      return {
        type: 'network',
        message: 'Connection error. Please check your internet connection and try again.',
        originalError: error,
        timestamp
      };
    }
    
    // HTTP Response errors
    if (error.status || (error.message && /\b\d{3}\b/.test(error.message))) {
      const statusCode = error.status || parseInt(error.message.match(/\b(\d{3})\b/)?.[1] || '0');
      
      switch (statusCode) {
        case 401:
          return {
            type: 'authentication',
            message: 'Session expired. Please refresh the page and log in again.',
            originalError: error,
            statusCode,
            timestamp
          };
          
        case 403:
          return {
            type: 'authorization',
            message: 'Access denied. You don\'t have permission for this action.',
            originalError: error,
            statusCode,
            timestamp
          };
          
        case 429:
          return {
            type: 'server',
            message: 'Too many requests. Please wait a moment before trying again.',
            originalError: error,
            statusCode,
            timestamp
          };
          
        case 500:
        case 502:
        case 503:
        case 504:
          return {
            type: 'server',
            message: 'Server error. Our team has been notified. Please try again in a moment.',
            originalError: error,
            statusCode,
            timestamp
          };
          
        default:
          return {
            type: 'server',
            message: `Request failed (${statusCode}). Please try again.`,
            originalError: error,
            statusCode,
            timestamp
          };
      }
    }
    
    // Validation errors
    if (error.message && (
      error.message.includes('validation') ||
      error.message.includes('invalid') ||
      error.message.includes('required')
    )) {
      return {
        type: 'validation',
        message: error.message || 'Please check your input and try again.',
        originalError: error,
        timestamp
      };
    }
    
    // Generic server errors
    if (error.message && error.message.includes('Failed to fetch')) {
      return {
        type: 'network',
        message: 'Unable to connect to the server. Please check your connection.',
        originalError: error,
        timestamp
      };
    }
    
    // Unknown errors
    return {
      type: 'unknown',
      message: error.message || 'An unexpected error occurred. Please try again.',
      originalError: error,
      timestamp
    };
  }
  
  /**
   * Get user-friendly error message
   */
  static getUserMessage(error: AppError): string {
    return error.message;
  }
  
  /**
   * Get recovery suggestions based on error type
   */
  static getRecoverySuggestions(error: AppError): string[] {
    switch (error.type) {
      case 'network':
        return [
          'Check your internet connection',
          'Try refreshing the page',
          'Wait a moment and try again'
        ];
        
      case 'authentication':
        return [
          'Refresh the page',
          'Log out and log back in',
          'Clear your browser cache'
        ];
        
      case 'authorization':
        return [
          'Contact support if you believe this is an error',
          'Try logging out and back in',
          'Check if you have the required permissions'
        ];
        
      case 'server':
        return [
          'Wait a moment and try again',
          'The issue is temporary and should resolve shortly',
          'Contact support if the problem persists'
        ];
        
      case 'validation':
        return [
          'Check your input for any missing or invalid information',
          'Make sure all required fields are filled',
          'Try typing your message again'
        ];
        
      default:
        return [
          'Try refreshing the page',
          'Wait a moment and try again',
          'Contact support if the problem continues'
        ];
    }
  }
  
  /**
   * Determine if error should trigger auto-retry
   */
  static shouldAutoRetry(error: AppError): boolean {
    return error.type === 'network' && error.statusCode !== 401 && error.statusCode !== 403;
  }
  
  /**
   * Get retry delay in milliseconds
   */
  static getRetryDelay(error: AppError, attemptNumber: number = 1): number {
    const baseDelay = 1000;
    const maxDelay = 30000;
    
    switch (error.type) {
      case 'network':
        // Exponential backoff: 1s, 2s, 4s, 8s, etc.
        return Math.min(baseDelay * Math.pow(2, attemptNumber - 1), maxDelay);
        
      case 'server':
        // Longer delay for server errors
        return Math.min(baseDelay * 2 * attemptNumber, maxDelay);
        
      default:
        return baseDelay;
    }
  }
  
  /**
   * Log error for monitoring/debugging
   */
  static logError(error: AppError, context?: string): void {
    const logData = {
      type: error.type,
      message: error.message,
      statusCode: error.statusCode,
      timestamp: new Date(error.timestamp).toISOString(),
      context,
      originalError: error.originalError?.stack || error.originalError?.message
    };
    
    console.error('[WealthPath AI Error]', logData);
    
    // In production, you would send this to your monitoring service
    // Example: sendToMonitoring(logData);
  }
}

/**
 * React hook for error handling
 */
export const useErrorHandler = () => {
  const handleError = (error: any, context?: string): AppError => {
    const appError = ErrorHandler.parseError(error);
    ErrorHandler.logError(appError, context);
    return appError;
  };
  
  return { handleError };
};

export default ErrorHandler;