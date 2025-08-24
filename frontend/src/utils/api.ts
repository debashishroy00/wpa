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

    // Response interceptor for error handling and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          if (this.tokens?.refresh_token) {
            try {
              const refreshResponse = await this.refreshToken();
              this.setTokens(refreshResponse.data);
              
              // Retry the original request with new token
              originalRequest.headers.Authorization = `Bearer ${refreshResponse.data.access_token}`;
              return this.client(originalRequest);
            } catch (refreshError) {
              // Refresh failed, clear tokens but don't redirect
              console.error('Token refresh failed:', refreshError);
              this.clearTokens();
              // Let the error bubble up so the form can handle it gracefully
              return Promise.reject(new Error('Authentication expired. Please refresh the page and try again.'));
            }
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

  private async refreshToken(): Promise<AxiosResponse<AuthTokens>> {
    return this.client.post('/api/v1/auth/refresh', {
      token: this.tokens?.refresh_token,
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
export const apiClient = new ApiClient();

// Initialize tokens from storage on app start
apiClient.loadTokensFromStorage();