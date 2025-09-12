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

// Helper to get current user ID from auth token
const getCurrentUserId = (): string | null => {
  try {
    const tokens = localStorage.getItem('auth_tokens');
    if (!tokens) return null;
    
    const tokenData = JSON.parse(tokens);
    const accessToken = tokenData.access_token;
    if (!accessToken) return null;
    
    // Decode JWT to get user ID
    const payload = JSON.parse(atob(accessToken.split('.')[1]));
    return payload.sub || payload.user_id || null;
  } catch (error) {
    console.warn('Failed to extract user ID from token:', error);
    return null;
  }
};

// Query keys with user context
export const goalQueryKeys = {
  all: (userId?: string) => ['goals', userId || getCurrentUserId()] as const,
  lists: (userId?: string) => [...goalQueryKeys.all(userId), 'list'] as const,
  list: (filters: Record<string, any>, userId?: string) => [...goalQueryKeys.lists(userId), { filters }] as const,
  details: (userId?: string) => [...goalQueryKeys.all(userId), 'detail'] as const,
  detail: (id: string, userId?: string) => [...goalQueryKeys.details(userId), id] as const,
  progress: (id: string, userId?: string) => [...goalQueryKeys.detail(id, userId), 'progress'] as const,
  history: (id: string, userId?: string) => [...goalQueryKeys.detail(id, userId), 'history'] as const,
  summary: (userId?: string) => [...goalQueryKeys.all(userId), 'summary'] as const,
  conflicts: (userId?: string) => [...goalQueryKeys.all(userId), 'conflicts'] as const,
  preferences: (userId?: string) => ['preferences', userId || getCurrentUserId()] as const,
  categories: () => ['categories'] as const, // Global data
  templates: () => ['templates'] as const, // Global data
};

// Goals queries
export const useGoalsQuery = (filters?: {
  status?: string;
  category?: string;
  limit?: number;
  offset?: number;
}) => {
  const userId = getCurrentUserId();
  
  return useQuery({
    queryKey: goalQueryKeys.list(filters || {}, userId),
    queryFn: async () => {
      try {
        console.log('🔍 Fetching goals with filters:', filters, 'for user:', userId);
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
    enabled: !!userId, // Only fetch if we have a user ID
  });
};

export const useGoalQuery = (goalId: string) => {
  const userId = getCurrentUserId();
  
  return useQuery({
    queryKey: goalQueryKeys.detail(goalId, userId),
    queryFn: () => goalsApi.getGoal(goalId),
    enabled: !!goalId && !!userId,
  });
};

export const useGoalProgressQuery = (goalId: string, limit?: number) => {
  const userId = getCurrentUserId();
  
  return useQuery({
    queryKey: goalQueryKeys.progress(goalId, userId),
    queryFn: () => goalsApi.getGoalProgress(goalId, limit),
    enabled: !!goalId && !!userId,
  });
};

export const useGoalHistoryQuery = (goalId: string) => {
  const userId = getCurrentUserId();
  
  return useQuery({
    queryKey: goalQueryKeys.history(goalId, userId),
    queryFn: () => goalsApi.getGoalHistory(goalId),
    enabled: !!goalId && !!userId,
  });
};

export const useGoalSummaryQuery = () => {
  const userId = getCurrentUserId();
  
  return useQuery({
    queryKey: goalQueryKeys.summary(userId),
    queryFn: async () => {
      try {
        console.log('🔍 Fetching goal summary for user:', userId);
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
    enabled: !!userId,
  });
};

export const useGoalConflictsQuery = () => {
  const userId = getCurrentUserId();
  
  return useQuery({
    queryKey: goalQueryKeys.conflicts(userId),
    queryFn: async () => {
      try {
        const result = await goalsApi.getGoalConflicts();
        return result || [];
      } catch (error) {
        console.error('Error fetching goal conflicts:', error);
        return [];
      }
    },
    enabled: !!userId,
  });
};

// User preferences queries
export const useUserPreferencesQuery = () => {
  const userId = getCurrentUserId();
  
  return useQuery({
    queryKey: goalQueryKeys.preferences(userId),
    queryFn: goalsApi.getPreferences,
    enabled: !!userId,
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
  const userId = getCurrentUserId();
  
  return useMutation({
    mutationFn: (goalData: GoalCreate) => goalsApi.createGoal(goalData),
    onSuccess: () => {
      // Invalidate and refetch goals list and summary for current user
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.lists(userId) });
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.summary(userId) });
    },
  });
};

export const useUpdateGoalMutation = () => {
  const queryClient = useQueryClient();
  const userId = getCurrentUserId();
  
  return useMutation({
    mutationFn: ({ goalId, update }: { goalId: string; update: GoalUpdate }) => 
      goalsApi.updateGoal(goalId, update),
    onSuccess: (data) => {
      // Update the specific goal in cache
      queryClient.setQueryData(goalQueryKeys.detail(data.goal_id, userId), data);
      // Invalidate lists and summary for current user
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.lists(userId) });
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.summary(userId) });
    },
  });
};

export const useDeleteGoalMutation = () => {
  const queryClient = useQueryClient();
  const userId = getCurrentUserId();
  
  return useMutation({
    mutationFn: (goalId: string) => goalsApi.deleteGoal(goalId),
    onSuccess: (_, goalId) => {
      // Remove from cache for current user
      queryClient.removeQueries({ queryKey: goalQueryKeys.detail(goalId, userId) });
      // Invalidate lists and summary for current user
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.lists(userId) });
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.summary(userId) });
    },
  });
};

export const useRecordProgressMutation = () => {
  const queryClient = useQueryClient();
  const userId = getCurrentUserId();
  
  return useMutation({
    mutationFn: ({ goalId, progress }: { goalId: string; progress: GoalProgressCreate }) =>
      goalsApi.recordProgress(goalId, progress),
    onSuccess: (_, { goalId }) => {
      // Invalidate progress, goal detail, and summary for current user
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.progress(goalId, userId) });
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.detail(goalId, userId) });
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.summary(userId) });
    },
  });
};

export const useBatchUpdateGoalsMutation = () => {
  const queryClient = useQueryClient();
  const userId = getCurrentUserId();
  
  return useMutation({
    mutationFn: ({ goalIds, updates, reason }: { 
      goalIds: string[]; 
      updates: GoalUpdate; 
      reason: string;
    }) => goalsApi.batchUpdateGoals(goalIds, updates, reason),
    onSuccess: () => {
      // Invalidate all goal-related queries for current user
      queryClient.invalidateQueries({ queryKey: goalQueryKeys.all(userId) });
    },
  });
};

export const useUpdatePreferencesMutation = () => {
  const queryClient = useQueryClient();
  const userId = getCurrentUserId();
  
  return useMutation({
    mutationFn: (update: UserPreferencesUpdate) => goalsApi.updatePreferences(update),
    onSuccess: (data) => {
      // Update preferences in cache for current user
      queryClient.setQueryData(goalQueryKeys.preferences(userId), data);
    },
  });
};