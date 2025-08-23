/**
 * WealthPath AI - Projection API Hooks
 * React Query hooks for managing projection data and assumptions
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../utils/api';
import { ProjectionResponse } from '../types/financial';

export interface ProjectionAssumptions {
  salary_growth_rate: number;
  rental_income_growth?: number;
  business_income_growth?: number;
  real_estate_appreciation: number;
  stock_market_return: number;
  retirement_account_return: number;
  cash_equivalent_return?: number;
  inflation_rate: number;
  lifestyle_inflation?: number;
  healthcare_inflation?: number;
  stock_volatility?: number;
  real_estate_volatility?: number;
  income_volatility?: number;
  effective_tax_rate?: number;
  capital_gains_rate?: number;
}

export interface ProjectionRequest {
  years?: number;
  include_monte_carlo?: boolean;
  monte_carlo_iterations?: number;
  scenario_type?: string;
}

// Get comprehensive projection
export const useProjectionQuery = (params: ProjectionRequest = {}) => {
  return useQuery({
    queryKey: ['projection', 'comprehensive', params],
    queryFn: async () => {
      const queryParams = new URLSearchParams({
        years: String(params.years || 20),
        include_monte_carlo: String(params.include_monte_carlo !== false),
        monte_carlo_iterations: String(params.monte_carlo_iterations || 1000),
        force_recalculate: 'false'
      });

      const response = await apiClient.get<ProjectionResponse>(`/api/v1/projections/comprehensive?${queryParams}`);
      return response;
    },
    staleTime: 1000 * 60 * 10, // 10 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes
    enabled: true,
    retry: 2,
    retryDelay: 1000
  });
};

// Get current projection assumptions
export const useProjectionAssumptionsQuery = () => {
  return useQuery({
    queryKey: ['projection', 'assumptions'],
    queryFn: async () => {
      const response = await apiClient.get<ProjectionAssumptions>('/api/v1/projections/assumptions');
      return response;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15 // 15 minutes
  });
};

// Update projection assumptions
export const useUpdateAssumptionsMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (assumptions: Partial<ProjectionAssumptions>) => {
      const response = await apiClient.post<ProjectionAssumptions>('/api/v1/projections/assumptions', assumptions);
      return response;
    },
    onSuccess: () => {
      // Invalidate and refetch projection data
      queryClient.invalidateQueries({ queryKey: ['projection'] });
    },
    onError: (error) => {
      console.error('Failed to update projection assumptions:', error);
    }
  });
};

// Get projection breakdown (detailed calculation explanation)
export const useProjectionBreakdownQuery = (years: number = 20) => {
  return useQuery({
    queryKey: ['projection', 'breakdown', years],
    queryFn: async () => {
      const response = await apiClient.get<any>(`/api/v1/projections/breakdown/${years}`);
      return response;
    },
    enabled: years > 0,
    staleTime: 1000 * 60 * 15, // 15 minutes
    gcTime: 1000 * 60 * 30 // 30 minutes
  });
};

// Calculate scenario analysis
export const useScenarioMutation = () => {
  return useMutation({
    mutationFn: async ({ scenario_type, years, adjustments }: { 
      scenario_type: string; 
      years: number[]; 
      adjustments?: Record<string, any> 
    }) => {
      const response = await apiClient.post<ProjectionResponse>('/api/v1/projections/scenario', {
        scenario_type,
        years,
        adjustments: adjustments || {}
      });
      return response;
    },
    onError: (error) => {
      console.error('Failed to calculate scenario:', error);
    }
  });
};

// Get sensitivity analysis
export const useSensitivityAnalysisQuery = (years: number = 20) => {
  return useQuery({
    queryKey: ['projection', 'sensitivity', years],
    queryFn: async () => {
      const response = await apiClient.get<any>(`/api/v1/projections/sensitivity-analysis?years=${years}`);
      return response;
    },
    enabled: years > 0,
    staleTime: 1000 * 60 * 30, // 30 minutes - expensive calculation
    gcTime: 1000 * 60 * 60 // 1 hour
  });
};

// Get projection history
export const useProjectionHistoryQuery = (limit: number = 10) => {
  return useQuery({
    queryKey: ['projection', 'history', limit],
    queryFn: async () => {
      const response = await apiClient.get<any>(`/api/v1/projections/history?limit=${limit}`);
      return response;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15 // 15 minutes
  });
};

// Clear projection cache
export const useClearCacheMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.delete<{ message: string }>('/api/v1/projections/cache');
      return response;
    },
    onSuccess: () => {
      // Clear local React Query cache as well
      queryClient.invalidateQueries({ queryKey: ['projection'] });
    }
  });
};