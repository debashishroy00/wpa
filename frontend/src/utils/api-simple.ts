/**
 * WealthPath AI - SIMPLIFIED API Client
 * No complex refresh logic - just simple auth handling
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { AuthTokens, ApiError } from '../types';

// Smart API URL detection based on environment
const getApiBaseUrl = () => {
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

    // SIMPLIFIED Response interceptor - aggressive auth clearing on 401
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Aggressively clear auth on any 401 error
        if (error.response?.status === 401) {
          console.log('401 error - clearing all auth data immediately');
          
          // Clear all auth data immediately
          localStorage.removeItem('access_token');
          localStorage.removeItem('auth_tokens');
          localStorage.removeItem('wealthpath-auth-store');
          sessionStorage.clear();
          
          // Dispatch event to notify AuthWrapper
          window.dispatchEvent(new CustomEvent('authCleared'));
          
          // Clear from this client too
          this.tokens = undefined;
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
  (window as any).quickLogin = async () => {
    try {
      // First, clear any existing auth data
      console.log('🧹 Clearing existing auth before login...');
      localStorage.removeItem('access_token');
      localStorage.removeItem('auth_tokens');
      localStorage.removeItem('wealthpath-auth-store');
      sessionStorage.clear();
      
      console.log('🔄 Attempting quick login...');
      const baseURL = getApiBaseUrl();
      const response = await fetch(`${baseURL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: 'test@test.com',  // Your test user
          password: 'test123'
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
        console.error('❌ Login failed - no access token in response');
        console.error('Response:', data);
      }
    } catch (error) {
      console.error('❌ Login failed:', error);
    }
  };

  console.log('🛠️ Run window.quickLogin() to login with test credentials');
}