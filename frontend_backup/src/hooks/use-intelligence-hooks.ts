/**
 * WealthPath AI - Intelligence Analysis Hooks
 * React hooks for intelligence analysis API integration
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../utils/api-simple';

// Types
interface IntelligenceAnalysis {
  analysis_id: string;
  timestamp: string;
  overall_score: number;
  success_probability: number;
  goals: any[];
  gaps: {
    monthly_shortfall: number;
    total_capital_needed: number;
    current_trajectory: number;
    gap_amount: number;
  };
  conflicts: any[];
  scenarios: any[];
  recommendations: {
    immediate: any[];
    short_term: any[];
    long_term: any[];
  };
}

interface IntelligenceAnalyzeRequest {
  include_simulations?: boolean;
  scenario_count?: number;
  optimization_level?: 'conservative' | 'balanced' | 'aggressive';
}

interface ConflictResolutionRequest {
  conflict_id: string;
  selected_resolution: string;
  parameters?: Record<string, any>;
}

interface MonteCarloRequest {
  scenario_id: string;
  iterations?: number;
  variables?: Record<string, any>;
}

// Query Keys
const intelligenceKeys = {
  all: ['intelligence'] as const,
  analysis: () => [...intelligenceKeys.all, 'analysis'] as const,
  scenarios: () => [...intelligenceKeys.all, 'scenarios'] as const,
  timeline: () => [...intelligenceKeys.all, 'timeline'] as const,
  simulation: (scenarioId: string) => [...intelligenceKeys.all, 'simulation', scenarioId] as const,
};

// Hook: Get Intelligence Analysis
export const useIntelligenceAnalysis = () => {
  return useQuery({
    queryKey: intelligenceKeys.analysis(),
    queryFn: async (): Promise<IntelligenceAnalysis> => {
      try {
        const data = await apiClient.post<IntelligenceAnalysis>('/api/v1/intelligence/analyze', {
          include_simulations: true,
          scenario_count: 3,
          optimization_level: 'balanced'
        });
        return data; // apiClient.post already returns response.data
      } catch (error) {
        console.error('Intelligence analysis failed:', error);
        // Re-throw error instead of returning mock data
        throw error;
      }
    },
    staleTime: 30 * 1000, // 30 seconds - allow fresher data
    gcTime: 15 * 60 * 1000, // 15 minutes cache (replaces cacheTime)
    retry: 1,
    refetchOnWindowFocus: false, // Prevent excessive refetching
  });
};

// Hook: Run Analysis Mutation
export const useRunAnalysisMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: IntelligenceAnalyzeRequest): Promise<IntelligenceAnalysis> => {
      const data = await apiClient.post<IntelligenceAnalysis>('/api/v1/intelligence/analyze', {
        include_simulations: true,
        scenario_count: 3,
        optimization_level: 'balanced',
        ...request
      });
      return data; // apiClient.post already returns response.data
    },
    onSuccess: () => {
      // Clear cache completely and refetch
      queryClient.removeQueries({ queryKey: intelligenceKeys.all });
      queryClient.invalidateQueries({ queryKey: intelligenceKeys.all });
    },
  });
};

// Hook: Resolve Conflict Mutation
export const useResolveConflictMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: ConflictResolutionRequest) => {
      const data = await apiClient.post('/api/v1/intelligence/resolve-conflict', request);
      return data;
    },
    onSuccess: () => {
      // Invalidate analysis to show updated results
      queryClient.invalidateQueries({ queryKey: intelligenceKeys.analysis() });
    },
  });
};

// Hook: Compare Scenarios
export const useScenarioComparison = () => {
  return useQuery({
    queryKey: intelligenceKeys.scenarios(),
    queryFn: async () => {
      const data = await apiClient.get('/api/v1/intelligence/compare-scenarios');
      return data;
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Hook: Get Goal Timeline
export const useGoalTimeline = () => {
  return useQuery({
    queryKey: intelligenceKeys.timeline(),
    queryFn: async () => {
      const data = await apiClient.get('/api/v1/intelligence/goal-timeline');
      return data;
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Hook: Run Monte Carlo Simulation
export const useMonteCarloSimulation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: MonteCarloRequest) => {
      const data = await apiClient.post('/api/v1/intelligence/simulate', {
        iterations: 1000,
        variables: {},
        ...request
      });
      return data;
    },
    onSuccess: (data, variables) => {
      // Cache simulation result
      queryClient.setQueryData(
        intelligenceKeys.simulation(variables.scenario_id),
        data
      );
    },
  });
};

// Hook: Get Cached Simulation Result
export const useSimulationResult = (scenarioId: string | null) => {
  return useQuery({
    queryKey: intelligenceKeys.simulation(scenarioId || ''),
    queryFn: async () => {
      // This would typically fetch from cache or API
      // For now, return null if no scenarioId
      return null;
    },
    enabled: !!scenarioId,
    staleTime: Infinity, // Simulation results don't change
  });
};

// Hook: Track Recommendation Action
export const useRecommendationActionMutation = () => {
  return useMutation({
    mutationFn: async (action: {
      recommendation_id: string;
      action: 'viewed' | 'accepted' | 'rejected' | 'completed';
      notes?: string;
    }) => {
      // This would be implemented when we have the tracking endpoint
      console.log('Tracking recommendation action:', action);
      return action;
    },
  });
};