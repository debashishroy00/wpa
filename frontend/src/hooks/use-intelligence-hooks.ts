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
          analysis_id: 'mock-analysis',
          timestamp: new Date().toISOString(),
          overall_score: 73,
          success_probability: 0.73,
          goals: [
            {
              goal_id: 'retirement-goal',
              name: 'Retirement Planning',
              category: 'retirement',
              target_amount: 3500000,
              current_amount: 450000,
              target_date: '2035-12-31',
              feasibility_score: 85,
              monthly_required: 8500,
              risk_aligned: true
            },
            {
              goal_id: 'vacation-home',
              name: 'Vacation Home',
              category: 'real_estate',
              target_amount: 350000,
              current_amount: 25000,
              target_date: '2027-12-31',
              feasibility_score: 72,
              monthly_required: 6000,
              risk_aligned: false
            }
          ],
          gaps: {
            monthly_shortfall: -14839,
            total_capital_needed: 4050000,
            current_trajectory: 2800000,
            gap_amount: 1250000
          },
          conflicts: [
            {
              id: 'mock-conflict',
              type: 'cash_flow',
              severity: 'critical',
              description: 'Monthly requirement exceeds available funds',
              affected_goals: ['retirement', 'vacation_home'],
              resolution_options: [],
              shortfall_amount: 14839
            }
          ],
          scenarios: [
            {
              id: 'balanced',
              name: 'Balanced Optimization',
              description: 'Optimize for balanced risk and return with moderate lifestyle adjustments',
              is_recommended: true,
              success_rate: 84,
              monthly_requirement_change: -2000,
              timeline_impact: 6,
              required_changes: [
                { type: 'timeline_adjustment', description: 'Delay non-critical goals by 12-18 months', amount: 800 },
                { type: 'investment_optimization', description: 'Increase equity allocation based on risk tolerance', amount: 600 },
                { type: 'income_optimization', description: 'Negotiate 8-12% salary increase', amount: 1200 },
                { type: 'expense_optimization', description: 'Optimize recurring expenses (mortgage refinance, etc.)', amount: 400 }
              ],
              projected_outcomes: {
                total_savings: 4200000,
                goal_completion_rate: 92,
                risk_score: 6
              },
              monte_carlo_completed: false
            },
            {
              id: 'conservative',
              name: 'Conservative Approach',
              description: 'Lower risk approach prioritizing stability and guaranteed returns',
              is_recommended: false,
              success_rate: 68,
              monthly_requirement_change: -1000,
              timeline_impact: 12,
              required_changes: [
                { type: 'goal_reduction', description: 'Reduce target amounts by 15-20%', amount: 500 },
                { type: 'timeline_extension', description: 'Extend timelines by 2-3 years', amount: 300 },
                { type: 'safe_investments', description: 'Focus on guaranteed returns and bonds', amount: 200 }
              ],
              projected_outcomes: {
                total_savings: 3800000,
                goal_completion_rate: 78,
                risk_score: 3
              },
              monte_carlo_completed: false
            },
            {
              id: 'aggressive',
              name: 'Aggressive Growth',
              description: 'High-growth strategy maximizing returns through increased risk and lifestyle changes',
              is_recommended: false,
              success_rate: 85,
              monthly_requirement_change: -3000,
              timeline_impact: -6,
              required_changes: [
                { type: 'income_boost', description: 'Pursue significant income increase (15-25%)', amount: 2500 },
                { type: 'high_growth_investments', description: 'Maximize equity allocation (90%+)', amount: 1000 },
                { type: 'lifestyle_optimization', description: 'Reduce discretionary spending by 20%', amount: 800 },
                { type: 'side_income', description: 'Develop additional income streams', amount: 1200 }
              ],
              projected_outcomes: {
                total_savings: 4800000,
                goal_completion_rate: 95,
                risk_score: 9
              },
              monte_carlo_completed: false
            }
          ],
          recommendations: {
            immediate: [
              {
                id: 'budget-review',
                type: 'immediate',
                category: 'budgeting',
                title: 'Review Monthly Budget',
                description: 'Analyze current expenses and identify optimization opportunities',
                impact_description: 'Could reduce monthly expenses by $500-1000',
                projected_impact: {
                  success_rate_improvement: 15,
                  cost_reduction: 750
                },
                difficulty: 'easy',
                estimated_time: '2-3 hours',
                action_steps: ['Download expense tracking app', 'Categorize last 3 months expenses', 'Identify top 3 reduction areas'],
                priority: 'high',
                status: 'new',
                goals_affected: ['retirement', 'vacation_home']
              }
            ],
            short_term: [
              {
                id: 'debt-payoff',
                type: 'short_term',
                category: 'debt_management',
                title: 'Accelerate Debt Payoff',
                description: 'Focus on high-interest debt elimination',
                impact_description: 'Free up $800/month after debt elimination',
                projected_impact: {
                  success_rate_improvement: 25,
                  cost_reduction: 800
                },
                difficulty: 'moderate',
                estimated_time: '6-12 months',
                action_steps: ['List all debts by interest rate', 'Apply debt avalanche method', 'Consider debt consolidation'],
                priority: 'high',
                status: 'new',
                goals_affected: ['retirement']
              }
            ],
            long_term: [
              {
                id: 'investment-optimization',
                type: 'long_term',
                category: 'investment',
                title: 'Optimize Investment Portfolio',
                description: 'Rebalance portfolio for better risk-adjusted returns',
                impact_description: 'Potential for 1-2% higher annual returns',
                projected_impact: {
                  success_rate_improvement: 35,
                  additional_savings: 50000
                },
                difficulty: 'moderate',
                estimated_time: '3-6 months',
                action_steps: ['Review current asset allocation', 'Research low-cost index funds', 'Implement systematic rebalancing'],
                priority: 'medium',
                status: 'new',
                goals_affected: ['retirement', 'vacation_home']
              }
            ]
          }
        };
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
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
      // Invalidate and refetch intelligence queries
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