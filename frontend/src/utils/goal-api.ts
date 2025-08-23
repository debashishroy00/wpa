/**
 * WealthPath AI - Goal Management API
 */
import { apiClient as api } from './api';
import type { 
  Goal, 
  GoalCreate, 
  GoalUpdate, 
  GoalProgress, 
  GoalProgressCreate,
  UserPreferences,
  UserPreferencesUpdate,
  GoalConflict,
  GoalSummary,
  GoalHistory,
  GoalCategory,
  GoalTemplate
} from '../types/goals';

const GOALS_API_BASE = '/api/v1';

// Goals CRUD
export const goalsApi = {
  // Goals
  createGoal: async (goalData: GoalCreate): Promise<Goal> => {
    const response = await api.post(`${GOALS_API_BASE}/goals`, goalData);
    return response;
  },

  getGoals: async (params?: {
    status?: string;
    category?: string;
    limit?: number;
    offset?: number;
  }): Promise<Goal[]> => {
    const response = await api.get(`${GOALS_API_BASE}/goals`, { params });
    return response; // api.get already returns response.data
  },

  getGoal: async (goalId: string): Promise<Goal> => {
    const response = await api.get(`${GOALS_API_BASE}/goals/${goalId}`);
    return response;
  },

  updateGoal: async (goalId: string, update: GoalUpdate): Promise<Goal> => {
    const response = await api.put(`${GOALS_API_BASE}/goals/${goalId}`, update);
    return response;
  },

  deleteGoal: async (goalId: string): Promise<void> => {
    await api.delete(`${GOALS_API_BASE}/goals/${goalId}`);
  },

  // Progress tracking
  recordProgress: async (goalId: string, progress: GoalProgressCreate): Promise<GoalProgress> => {
    const response = await api.post(`${GOALS_API_BASE}/goals/${goalId}/progress`, progress);
    return response;
  },

  getGoalProgress: async (goalId: string, limit?: number): Promise<GoalProgress[]> => {
    const response = await api.get(`${GOALS_API_BASE}/goals/${goalId}/progress`, {
      params: { limit }
    });
    return response;
  },

  // History and audit
  getGoalHistory: async (goalId: string): Promise<GoalHistory[]> => {
    const response = await api.get(`${GOALS_API_BASE}/goals/${goalId}/history`);
    return response;
  },

  // Analysis
  getGoalConflicts: async (): Promise<GoalConflict[]> => {
    const response = await api.get(`${GOALS_API_BASE}/goals/analysis/conflicts`);
    return response;
  },

  getGoalSummary: async (): Promise<GoalSummary> => {
    const response = await api.get(`${GOALS_API_BASE}/goals/summary`);
    return response;
  },

  // Batch operations
  batchUpdateGoals: async (goalIds: string[], updates: GoalUpdate, reason: string): Promise<Goal[]> => {
    const response = await api.put(`${GOALS_API_BASE}/goals/batch`, {
      goal_ids: goalIds,
      updates,
      batch_reason: reason
    });
    return response;
  },

  // User preferences
  createPreferences: async (preferences: Partial<UserPreferences>): Promise<UserPreferences> => {
    const response = await api.post(`${GOALS_API_BASE}/preferences`, preferences);
    return response;
  },

  getPreferences: async (): Promise<UserPreferences> => {
    const response = await api.get(`${GOALS_API_BASE}/preferences`);
    return response;
  },

  updatePreferences: async (update: UserPreferencesUpdate): Promise<UserPreferences> => {
    const response = await api.put(`${GOALS_API_BASE}/preferences`, update);
    return response;
  },

  // Categories and templates
  getCategories: async (): Promise<Record<string, GoalCategory>> => {
    const response = await api.get(`${GOALS_API_BASE}/categories`);
    return response;
  },

  getTemplates: async (): Promise<GoalTemplate[]> => {
    const response = await api.get(`${GOALS_API_BASE}/templates`);
    return response;
  }
};