/**
 * WealthPath AI - React Query Client Configuration
 */
import { QueryClient } from '@tanstack/react-query';
import { ApiError } from '../types';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Global query defaults
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        // Don't retry on authentication errors
        if ((error as ApiError)?.status_code === 401) {
          return false;
        }
        // Don't retry on client errors (4xx)
        if ((error as ApiError)?.status_code >= 400 && (error as ApiError)?.status_code < 500) {
          return false;
        }
        // Retry up to 3 times for server errors
        return failureCount < 3;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      // Global mutation defaults
      retry: (failureCount, error) => {
        // Don't retry mutations on client errors
        if ((error as ApiError)?.status_code >= 400 && (error as ApiError)?.status_code < 500) {
          return false;
        }
        // Retry once for server errors
        return failureCount < 1;
      },
    },
  },
});