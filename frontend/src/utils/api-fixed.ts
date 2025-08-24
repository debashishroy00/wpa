/**
 * WealthPath AI - API Client (FIXED VERSION)
 * This is a copy of api.ts with the refresh token fix applied
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

class ApiClientFixed {
  private client: AxiosInstance;
  private tokens?: AuthTokens;

  constructor() {
    const baseURL = getApiBaseUrl();
    console.log('🔗 API connected to (Fixed Version):', baseURL);
    
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.tokens?.access_token) {
          config.headers.Authorization = `Bearer ${this.tokens.access_token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          if (this.tokens?.refresh_token) {
            try {
              console.log('🔄 Refresh token request - FIXED VERSION (2025-08-22-v2)', { 
                tokenLength: this.tokens?.refresh_token?.length 
              });
              const refreshResponse = await this.refreshToken();
              this.setTokens(refreshResponse.data);
              
              // Retry the original request with new token
              originalRequest.headers.Authorization = `Bearer ${refreshResponse.data.access_token}`;
              return this.client(originalRequest);
            } catch (refreshError) {
              // Refresh failed, clear tokens and redirect to login
              this.clearTokens();
              // Could emit event for app to handle redirect
              return Promise.reject(refreshError);
            }
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private async refreshToken(): Promise<AxiosResponse<AuthTokens>> {
    // FIXED: Use 'token' field instead of 'refresh_token'
    return this.client.post('/api/v1/auth/refresh', {
      token: this.tokens?.refresh_token,  // ✅ CORRECT field name
    });
  }

  setTokens(tokens: AuthTokens) {
    this.tokens = tokens;
    // Store in localStorage for persistence
    localStorage.setItem('auth_tokens', JSON.stringify(tokens));
  }

  clearTokens() {
    this.tokens = undefined;
    localStorage.removeItem('auth_tokens');
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
export const apiClientFixed = new ApiClientFixed();

// Initialize tokens from storage on app start
apiClientFixed.loadTokensFromStorage();

export default apiClientFixed;