/**
 * Admin Store - Completely Isolated State Management
 * This store manages admin-specific state without affecting existing stores
 */

import { create } from 'zustand';
import { adminApi } from '../../services/admin/adminApi';

interface AdminUser {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
  status: string;
  financial_entries_count?: number;
  net_worth?: number;
  goals_count?: number;
}

interface AdminSession {
  id: number;
  user: string;
  login_time: string;
  expires_at: string;
  status: string;
  ip_address: string;
}

interface SystemHealth {
  overall: number;
  services: {
    database: { status: 'healthy' | 'error'; responseTime: number; uptime: string };
    redis: { status: 'healthy' | 'error'; responseTime: number; uptime: string };
    vectorDB: { status: 'healthy' | 'error'; responseTime: number; uptime: string };
    llm: { status: 'healthy' | 'error'; responseTime: number; uptime: string };
    api: { status: 'healthy' | 'error'; responseTime: number; uptime: string };
  };
}

interface AdminState {
  // Data
  users: AdminUser[];
  sessions: AdminSession[];
  systemHealth: SystemHealth | null;
  logs: any[];
  
  // Loading states
  loading: {
    users: boolean;
    sessions: boolean;
    health: boolean;
    logs: boolean;
  };
  
  // Error states (isolated from main app)
  errors: {
    users: string | null;
    sessions: string | null;
    health: string | null;
    logs: string | null;
  };
  
  // Admin feature availability
  isAdminAvailable: boolean;
  
  // Actions
  fetchUsers: () => Promise<void>;
  fetchSessions: () => Promise<void>;
  fetchSystemHealth: () => Promise<void>;
  fetchLogs: (limit?: number) => Promise<void>;
  forceLogoutUser: (userId: number) => Promise<boolean>;
  clearUserCache: (userId: number) => Promise<boolean>;
  clearUserTokens: (userId: number) => Promise<boolean>;
  clearAllCaches: () => Promise<boolean>;
  checkAdminAvailability: () => Promise<void>;
  clearError: (errorType: keyof AdminState['errors']) => void;
  resetStore: () => void;
}

const initialState = {
  users: [],
  sessions: [],
  systemHealth: null,
  logs: [],
  loading: {
    users: false,
    sessions: false,
    health: false,
    logs: false,
  },
  errors: {
    users: null,
    sessions: null,
    health: null,
    logs: null,
  },
  isAdminAvailable: false,
};

export const useAdminStore = create<AdminState>((set, get) => ({
  ...initialState,

  fetchUsers: async () => {
    try {
      set((state) => ({ 
        loading: { ...state.loading, users: true },
        errors: { ...state.errors, users: null }
      }));
      
      const users = await adminApi.getAllUsers();
      
      set((state) => ({ 
        users,
        loading: { ...state.loading, users: false }
      }));
    } catch (error: any) {
      set((state) => ({ 
        loading: { ...state.loading, users: false },
        errors: { ...state.errors, users: error.message || 'Failed to fetch users' }
      }));
    }
  },

  fetchSessions: async () => {
    try {
      set((state) => ({ 
        loading: { ...state.loading, sessions: true },
        errors: { ...state.errors, sessions: null }
      }));
      
      const sessions = await adminApi.getActiveSessions();
      
      set((state) => ({ 
        sessions,
        loading: { ...state.loading, sessions: false }
      }));
    } catch (error: any) {
      set((state) => ({ 
        loading: { ...state.loading, sessions: false },
        errors: { ...state.errors, sessions: error.message || 'Failed to fetch sessions' }
      }));
    }
  },

  fetchSystemHealth: async () => {
    try {
      set((state) => ({ 
        loading: { ...state.loading, health: true },
        errors: { ...state.errors, health: null }
      }));
      
      const systemHealth = await adminApi.getSystemHealth();
      
      set((state) => ({ 
        systemHealth,
        loading: { ...state.loading, health: false }
      }));
    } catch (error: any) {
      set((state) => ({ 
        loading: { ...state.loading, health: false },
        errors: { ...state.errors, health: error.message || 'Failed to fetch health status' }
      }));
    }
  },

  fetchLogs: async (limit = 100) => {
    try {
      set((state) => ({ 
        loading: { ...state.loading, logs: true },
        errors: { ...state.errors, logs: null }
      }));
      
      const logs = await adminApi.getSystemLogs(limit);
      
      set((state) => ({ 
        logs,
        loading: { ...state.loading, logs: false }
      }));
    } catch (error: any) {
      set((state) => ({ 
        loading: { ...state.loading, logs: false },
        errors: { ...state.errors, logs: error.message || 'Failed to fetch logs' }
      }));
    }
  },

  forceLogoutUser: async (userId: number) => {
    try {
      const success = await adminApi.forceLogoutUser(userId);
      if (success) {
        // Refresh sessions after successful logout
        get().fetchSessions();
      }
      return success;
    } catch (error) {
      console.error('Admin: Force logout failed:', error);
      return false;
    }
  },

  clearUserCache: async (userId: number) => {
    try {
      return await adminApi.clearUserCache(userId);
    } catch (error) {
      console.error('Admin: Clear cache failed:', error);
      return false;
    }
  },

  clearUserTokens: async (userId: number) => {
    try {
      const success = await adminApi.clearUserTokens(userId);
      if (success) {
        // Refresh sessions after clearing tokens
        get().fetchSessions();
      }
      return success;
    } catch (error) {
      console.error('Admin: Clear tokens failed:', error);
      return false;
    }
  },

  clearAllCaches: async () => {
    try {
      return await adminApi.clearAllCaches();
    } catch (error) {
      console.error('Admin: Clear all caches failed:', error);
      return false;
    }
  },

  checkAdminAvailability: async () => {
    try {
      const isAvailable = await adminApi.testAdminAvailability();
      set({ isAdminAvailable: isAvailable });
    } catch (error) {
      set({ isAdminAvailable: false });
    }
  },

  clearError: (errorType) => {
    set((state) => ({
      errors: { ...state.errors, [errorType]: null }
    }));
  },

  resetStore: () => {
    set(initialState);
  },
}));