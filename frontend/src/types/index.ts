/**
 * WealthPath AI - Export all types
 */

export * from './auth';
export * from './financial';
export * from './goals';

// Common API types
export interface ApiError {
  detail: string;
  status_code: number;
  timestamp: string;
}

// Navigation and UI types
export interface StepProgress {
  currentStep: number;
  totalSteps: number;
  completedSteps: boolean[];
}

export interface NavigationState {
  currentPage: string;
  previousPage?: string;
  stepProgress?: StepProgress;
}

// Application configuration
export interface AppConfig {
  apiBaseUrl: string;
  environment: 'development' | 'staging' | 'production';
  features: {
    enableAnalytics: boolean;
    enableMetrics: boolean;
    enableDebug: boolean;
  };
}

// Loading and error states
export interface LoadingState {
  [key: string]: boolean;
}

export interface ErrorState {
  [key: string]: string | null;
}