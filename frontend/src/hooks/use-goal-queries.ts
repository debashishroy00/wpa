/**
 * WealthPath AI - Goal Management React Query Hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { goalsApi } from '../utils/goal-api';
import type { 
  Goal, 
  GoalCreate, 
  GoalUpdate, 
  GoalProgressCreate,
  UserPreferencesUpdate
} from '../types/goals';

// Query keys
export const goalQueryKeys = {
  all: ['goals'] as const,
  lists: () => [...goalQueryKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...goalQueryKeys.lists(), { filters }] as const,
  details: () => [...goalQueryKeys.all, 'detail'] as const,
  detail: (id: string) => [...goalQueryKeys.details(), id] as const,
  progress: (id: string) => [...goalQueryKeys.detail(id), 'progress'] as const,
  history: (id: string) => [...goalQueryKeys.detail(id), 'history'] as const,
  summary: () => [...goalQueryKeys.all, 'summary'] as const,
  conflicts: () => [...goalQueryKeys.all, 'conflicts'] as const,
  preferences: () => ['preferences'] as const,
  categories: () => ['categories'] as const,
  templates: () => ['templates'] as const,
};

// Goals queries
export const useGoalsQuery = (filters?: {
  status?: string;
  category?: string;
  limit?: number;
  offset?: number;
}) => {
  return useQuery({
    queryKey: goalQueryKeys.list(filters || {}),
    queryFn: async () => {
      try {
        console.log('🔍 Fetching goals with filters:', filters);
        const result = await goalsApi.getGoals(filters);
        console.log('✅ Goals API response:', result);
        console.log('📊 Goals count:', result?.length || 0);
        console.log('📋 First goal (if any):', result?.[0]);
        return result || [];
      } catch (error) {
        console.error('❌ Error fetching goals:', error);
        console.error('🔐 Auth tokens:', localStorage.getItem('auth_tokens'));
        return [];
      }
    },
  });
};

export const useGoalQuery = (goalId: string) => {
  return useQuery({
    queryKey: goalQueryKeys.detail(goalId),
    queryFn: () => goalsApi.getGoal(goalId),
    enabled: !!goalId,
  });
};

export const useGoalProgressQuery = (goalId: string, limit?: number) => {
  return useQuery({
    queryKey: goalQueryKeys.progress(goalId),
    queryFn: () => goalsApi.getGoalProgress(goalId, limit),
    enabled: !!goalId,
  });
};

export const useGoalHistoryQuery = (goalId: string) => {
  return useQuery({
    queryKey: goalQueryKeys.history(goalId),
    queryFn: () => goalsApi.getGoalHistory(goalId),
    enabled: !!goalId,
  });
};

export const useGoalSummaryQuery = () => {
  return useQuery({
    queryKey: goalQueryKeys.summary(),
    queryFn: async () => {
      try {
        const result = await goalsApi.getGoalSummary();
        return result || {
          active_goals: 0,
          achieved_goals: 0,
          total_target: 0,
          nearest_deadline: null,
          average_progress: 0
        };
      } catch (error) {
        console.error('Error fetching goal summary:', error);
        return {
          active_goals: 0,
          achieved_goals: 0,
          total_target: 0,
          nearest_deadline: null,
          average_progress: 0
        };
      }
    },
  });
};

export const useGoalConflictsQuery = () => {
  return useQuery({
    queryKey: goalQueryKeys.conflicts(),
    queryFn: async () => {
      try {
        const result = await goalsApi.getGoalConflicts();
        return result || [];
      } catch (error) {
        console.error('Error fetching goal conflicts:', error);
        return [];
      }
    },
  });
};

// User preferences queries
export const useUserPreferencesQuery = () => {
  return useQuery({
    queryKey: goalQueryKeys.preferences(),
    queryFn: goalsApi.getPreferences,
  });
};

// Categories and templates
export const useCategoriesQuery = () => {
  return useQuery({
    queryKey: goalQueryKeys.categories(),
    queryFn: async () => {
      try {
        const result = await goalsApi.getCategories();
        return result || {};
      } catch (error) {
        console.error('Error fetching categories:', error);
        return {};
      }
    },
  });
};

export const useTemplatesQuery = () => {
  return useQuery({
    queryKey: goalQueryKeys.templates(),
    queryFn: async () => {
      try {
        const result = await goalsApi.getTemplates();
        return result || [];
      } catch (error) {
        console.error('Error fetching templates:', error);
        return [];
      }
    },
  });
};

// Mutations
export const useCreateGoalMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (goalData: GoalCreate) => goalsApi.createGoal(goalData),
    onSuccess: () => {
      // Invalidate and refetch goals list and summary
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.summary() });
    },
  });
};

export const useUpdateGoalMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ goalId, update }: { goalId: string; update: GoalUpdate }) => 
      goalsApi.updateGoal(goalId, update),
    onSuccess: (data) => {
      // Update the specific goal in cache
      queryClient.setQueryData(goalQueryKeys.detail(data.goal_id), data);
      // Invalidate lists and summary
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.summary() });
    },
  });
};

export const useDeleteGoalMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (goalId: string) => goalsApi.deleteGoal(goalId),
    onSuccess: (_, goalId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: goalQueryKeys.detail(goalId) });
      // Invalidate lists and summary
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.summary() });
    },
  });
};

export const useRecordProgressMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ goalId, progress }: { goalId: string; progress: GoalProgressCreate }) =>
      goalsApi.recordProgress(goalId, progress),
    onSuccess: (_, { goalId }) => {
      // Invalidate progress, goal detail, and summary
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.progress(goalId) });
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.detail(goalId) });
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.summary() });
    },
  });
};

export const useBatchUpdateGoalsMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ goalIds, updates, reason }: { 
      goalIds: string[]; 
      updates: GoalUpdate; 
      reason: string;
    }) => goalsApi.batchUpdateGoals(goalIds, updates, reason),
    onSuccess: () => {
      // Invalidate all goal-related queries
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.all });
    },
  });
};

export const useUpdatePreferencesMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (update: UserPreferencesUpdate) => goalsApi.updatePreferences(update),
    onSuccess: (data) => {
      // Update preferences in cache
      queryClient.setQueryData(goalQueryKeys.preferences(), data);
    },
  });
};