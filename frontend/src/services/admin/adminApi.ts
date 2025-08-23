/**
 * Admin API Service - Completely Isolated
 * This service handles all admin-specific API calls without affecting existing services
 */

import { apiClient } from '../../utils/api';

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
  database: { status: 'healthy' | 'error'; response_time_ms?: number };
  redis: { status: 'healthy' | 'error'; response_time_ms?: number };
  vector_db: { status: 'healthy' | 'error'; response_time_ms?: number };
  llm_services: {
    openai: { status: 'healthy' | 'error'; response_time_ms?: number };
    gemini: { status: 'healthy' | 'error'; response_time_ms?: number };
    claude: { status: 'healthy' | 'error'; response_time_ms?: number };
  };
}

class AdminApiService {
  /**
   * Get all users with admin data (safe wrapper)
   */
  async getAllUsers(): Promise<AdminUser[]> {
    try {
      return await apiClient.get<AdminUser[]>('/api/v1/admin/users');
    } catch (error) {
      console.error('Admin: Failed to fetch users:', error);
      return [];
    }
  }

  /**
   * Get user details by ID (safe wrapper)
   */
  async getUserById(userId: number): Promise<AdminUser | null> {
    try {
      return await apiClient.get<AdminUser>(`/api/v1/admin/users/${userId}`);
    } catch (error) {
      console.error(`Admin: Failed to fetch user ${userId}:`, error);
      return null;
    }
  }

  /**
   * Get active sessions (safe wrapper)
   */
  async getActiveSessions(): Promise<AdminSession[]> {
    try {
      const response = await apiClient.get<any>('/api/v1/admin/sessions');
      // Extract sessions array from the response object
      return response.sessions || [];
    } catch (error) {
      console.error('Admin: Failed to fetch sessions:', error);
      return [];
    }
  }

  /**
   * Get system health status (safe wrapper)
   */
  async getSystemHealth(): Promise<SystemHealth | null> {
    try {
      return await apiClient.get<SystemHealth>('/api/v1/admin/health');
    } catch (error) {
      console.error('Admin: Failed to fetch health status:', error);
      return null;
    }
  }

  /**
   * Force logout user (safe wrapper)
   */
  async forceLogoutUser(userId: number): Promise<boolean> {
    try {
      await apiClient.post(`/api/v1/admin/force-logout/${userId}`);
      return true;
    } catch (error) {
      console.error(`Admin: Failed to logout user ${userId}:`, error);
      return false;
    }
  }

  /**
   * Clear user cache (safe wrapper)
   */
  async clearUserCache(userId: number): Promise<boolean> {
    try {
      await apiClient.delete(`/api/v1/admin/user-cache/${userId}`);
      return true;
    } catch (error) {
      console.error(`Admin: Failed to clear cache for user ${userId}:`, error);
      return false;
    }
  }

  /**
   * Clear user tokens (safe wrapper)
   */
  async clearUserTokens(userId: number): Promise<boolean> {
    try {
      await apiClient.delete(`/api/v1/admin/user-tokens/${userId}`);
      return true;
    } catch (error) {
      console.error(`Admin: Failed to clear tokens for user ${userId}:`, error);
      return false;
    }
  }

  /**
   * Clear all system caches (safe wrapper)
   */
  async clearAllCaches(): Promise<boolean> {
    try {
      await apiClient.post('/api/v1/admin/clear-cache');
      return true;
    } catch (error) {
      console.error('Admin: Failed to clear all caches:', error);
      return false;
    }
  }

  /**
   * Get recent system logs (safe wrapper)
   */
  async getSystemLogs(limit: number = 100): Promise<any[]> {
    try {
      return await apiClient.get<any[]>(`/api/v1/admin/logs?limit=${limit}`);
    } catch (error) {
      console.error('Admin: Failed to fetch logs:', error);
      return [];
    }
  }

  /**
   * Test if admin endpoints are available
   */
  async testAdminAvailability(): Promise<boolean> {
    try {
      await apiClient.get('/api/v1/admin/health');
      return true;
    } catch (error) {
      return false;
    }
  }
}

// Export singleton instance
export const adminApi = new AdminApiService();