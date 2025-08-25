/**
 * WealthPath AI - SIMPLIFIED API Client
 * No complex refresh logic - just simple auth handling
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { AuthTokens, ApiError } from '../types';

// Smart API URL detection based on environment - UPDATED v2
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  const envVar = import.meta.env.VITE_API_BASE_URL;
  const mode = import.meta.env.MODE;
  const prod = import.meta.env.PROD;
  
  // FORCE PRODUCTION URL FOR ANY NON-LOCALHOST
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    console.log('🔗 PRODUCTION MODE - Using render backend:', hostname);
    return 'https://wealthpath-backend.onrender.com';
  }
  
  // Log environment detection for debugging
  console.log('🔍 Environment detection v2:', {
    hostname,
    envVar,
    mode,
    prod,
    url: envVar || 'fallback'
  });
  
  // Check if we have an environment variable set (for localhost only now)
  if (envVar && (hostname === 'localhost' || hostname === '127.0.0.1')) {
    console.log('Using ENV variable for localhost:', envVar);
    return envVar;
  }
  
  // Localhost fallback
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    console.log('Detected localhost - using local backend');
    return 'http://localhost:8000';
  }
  
  // This should never be reached, but just in case
  console.log('⚠️ Fallback to production backend');
  return 'https://wealthpath-backend.onrender.com';
};

class ApiClient {
  private client: AxiosInstance;
  private tokens?: AuthTokens;

  constructor() {
    const baseURL = getApiBaseUrl();
    console.log('🔗 API connected to (SIMPLIFIED):', baseURL);
    
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupSimpleInterceptors();
  }

  private setupSimpleInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        // Simple token check - use stored token if available
        const token = localStorage.getItem('access_token') || this.tokens?.access_token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // SIMPLIFIED Response interceptor - no refresh logic
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Just pass through the error - don't try to refresh
        if (error.response?.status === 401) {
          console.log('401 error - auth required (no auto-refresh)');
          // Don't clear tokens, don't refresh, just let it fail gracefully
        }
        
        return Promise.reject(error);
      }
    );
  }

  setTokens(tokens: AuthTokens) {
    this.tokens = tokens;
    // Store in localStorage for persistence
    localStorage.setItem('auth_tokens', JSON.stringify(tokens));
    localStorage.setItem('access_token', tokens.access_token);
  }

  clearTokens() {
    this.tokens = undefined;
    localStorage.removeItem('auth_tokens');
    localStorage.removeItem('access_token');
  }

  loadTokensFromStorage() {
    const stored = localStorage.getItem('auth_tokens');
    if (stored) {
      try {
        this.tokens = JSON.parse(stored);
      } catch (error) {
        console.error('Failed to parse stored tokens:', error);
        this.clearTokens();
      }
    }
  }

  // Generic API methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    return this.get('/health');
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Initialize tokens from storage on app start
apiClient.loadTokensFromStorage();

// Add quickLogin function to window for easy testing
if (typeof window !== 'undefined') {
  (window as any).quickLogin = async (username, password) => {
    if (!username || !password) {
      console.log('Usage: window.quickLogin("your-email@domain.com", "your-password")');
      console.log('Example: window.quickLogin("your-email@example.com", "your-password")');
      return;
    }
    
    try {
      console.log('🔄 Attempting login with provided credentials...');
      const baseURL = getApiBaseUrl();
      const response = await fetch(`${baseURL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          username,
          password
        })
      });
      
      const data = await response.json();
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
          apiClient.setTokens(data);
        }
        console.log('✅ Logged in! Refreshing...');
        window.location.reload();
      } else {
        console.error('❌ Login failed:', data);
      }
    } catch (error) {
      console.error('❌ Login failed:', error);
    }
  };

  (window as any).clearAndLogin = async (username, password) => {
    if (!username || !password) {
      console.log('Usage: window.clearAndLogin("your-email@domain.com", "your-password")');
      console.log('Example: window.clearAndLogin("your-email@example.com", "your-password")');
      return;
    }
    
    console.log('🧹 Clearing old tokens...');
    localStorage.clear();
    sessionStorage.clear();
    
    console.log('🔐 Logging in with provided credentials...');
    try {
      const baseURL = getApiBaseUrl();
      const response = await fetch(`${baseURL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          username,
          password
        })
      });
      
      const data = await response.json();
      if (response.ok && data.access_token) {
        localStorage.setItem('access_token', data.access_token);
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
          apiClient.setTokens(data);
        }
        console.log('✅ Fresh login successful! Refreshing...');
        window.location.reload();
      } else {
        console.error('❌ Login failed:', data);
      }
    } catch (error) {
      console.error('❌ Login error:', error);
    }
  };

  console.log('🛠️ Usage: window.quickLogin("email", "password")');
  console.log('💡 Usage: window.clearAndLogin("email", "password") - clears old tokens first');
  
  // Auto-clear tokens if URL has clear parameter
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('clear') || urlParams.get('reset') || urlParams.get('clearAuth')) {
    console.log('🧹 Auto-clearing all tokens...');
    localStorage.clear();
    sessionStorage.clear();
    // Remove parameter and reload
    window.history.replaceState({}, document.title, window.location.pathname);
    setTimeout(() => window.location.reload(), 100);
  }
}