/**
 * WealthPath AI - API Client
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
    console.log('🔗 API connected to:', baseURL);
    
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

    // Response interceptor with improved refresh token logic
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Only handle 401 errors that haven't been retried yet
        if (error.response?.status === 401 && !originalRequest._retry) {
          
          // If we don't have a refresh token, just clear tokens and reject
          if (!this.tokens?.refresh_token) {
            console.warn('🚫 401 error but no refresh token available, clearing auth');
            this.clearTokens();
            return Promise.reject(new Error('Authentication required'));
          }

          // If we're already refreshing, queue this request
          if (this.isRefreshing) {
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            }).then(() => {
              if (this.tokens?.access_token) {
                originalRequest.headers.Authorization = `Bearer ${this.tokens.access_token}`;
                return this.client(originalRequest);
              }
              return Promise.reject(new Error('Authentication failed'));
            }).catch(err => {
              return Promise.reject(err);
            });
          }

          // Mark request as retried and start refresh process
          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            console.log('🔄 Attempting token refresh...');
            const refreshResponse = await this.refreshTokenDirectly();
            this.setTokens(refreshResponse.data);
            
            // Process the failed queue
            this.processQueue(null);
            
            // Retry the original request
            originalRequest.headers.Authorization = `Bearer ${refreshResponse.data.access_token}`;
            return this.client(originalRequest);
            
          } catch (refreshError) {
            console.error('❌ Token refresh failed:', refreshError);
            
            // Process queue with error
            this.processQueue(refreshError);
            
            // Clear tokens and redirect
            this.clearTokens();
            
            return Promise.reject(new Error('Authentication expired. Please log in again.'));
          } finally {
            this.isRefreshing = false;
          }
        }

        // Transform error response
        const apiError: ApiError = {
          detail: error.response?.data?.detail || 'An unexpected error occurred',
          status_code: error.response?.status || 500,
          timestamp: new Date().toISOString(),
        };

        return Promise.reject(apiError);
      }
    );
  }

  private processQueue(error: any) {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error);
      } else {
        resolve();
      }
    });
    
    this.failedQueue = [];
  }

  private async refreshToken(): Promise<AxiosResponse<AuthTokens>> {
    return this.client.post('/api/v1/auth/refresh', {
      token: this.tokens?.refresh_token,
    });
  }

  // Direct refresh token method that bypasses interceptors to prevent loops
  private async refreshTokenDirectly(): Promise<AxiosResponse<AuthTokens>> {
    const baseURL = getApiBaseUrl();
    
    const response = await fetch(`${baseURL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token: this.tokens?.refresh_token,
      }),
    });

    if (!response.ok) {
      throw new Error(`Refresh token failed: ${response.status}`);
    }

    const data = await response.json();
    return { data } as AxiosResponse<AuthTokens>;
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
export const apiClient = new ApiClient();

// Initialize tokens from storage on app start
apiClient.loadTokensFromStorage();