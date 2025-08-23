/**
 * WealthPath AI - Authentication Types
 */

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  status: 'active' | 'inactive' | 'suspended' | 'deleted';
  created_at: string;
  updated_at?: string;
  last_login_at?: string;
  email_verified_at?: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
}

export interface UserProfile {
  id: number;
  user_id: number;
  date_of_birth?: string;
  location?: string;
  timezone: string;
  risk_tolerance: number; // 1-10 scale
  investment_experience: 'beginner' | 'intermediate' | 'advanced';
  annual_income?: number;
  employment_status?: string;
  currency: string;
  language: string;
  data_sharing_consent: boolean;
  marketing_consent: boolean;
  analytics_consent: boolean;
  email_notifications: boolean;
  push_notifications: boolean;
  sms_notifications: boolean;
  created_at: string;
  updated_at?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
}

export interface AuthState {
  user?: User;
  profile?: UserProfile;
  tokens?: AuthTokens;
  isAuthenticated: boolean;
  isLoading: boolean;
  error?: string;
}

export interface LoginResponse {
  user: User;
  profile?: UserProfile;
  tokens: AuthTokens;
}

export interface RegisterResponse {
  user: User;
  tokens: AuthTokens;
  message: string;
}