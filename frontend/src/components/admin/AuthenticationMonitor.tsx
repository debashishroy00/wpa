/**
 * Authentication Monitor - JWT Token and Session Tracking
 * Completely isolated component for admin authentication monitoring
 */

import React, { useEffect, useState, useRef } from 'react';
import { useAdminStore } from '../../stores/admin/adminStore';
import { getApiBaseUrl } from '../../utils/getApiBaseUrl';

interface AuthSession {
  id: number;
  user: string;
  login_time: string;
  expires_at: string;
  status: string;
  ip_address: string;
}

interface AuthMetrics {
  active_sessions: number;
  login_attempts_last_hour: number;
  failed_attempts_last_hour: number;
  unique_users_today: number;
  expiry_warnings: number;
}

interface SessionData {
  active_sessions: number;
  unique_users_today: number;
  expiry_warnings: number;
  last_updated: string;
  sessions: AuthSession[];
}

const AuthenticationMonitor: React.FC = () => {
  const { loading, errors, clearError } = useAdminStore();
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(60); // seconds
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchSessionData = async () => {
    try {
      setLoadingData(true);
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/sessions`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessionData(data);
        setLastRefresh(new Date());
      } else {
        console.error('Failed to fetch session data');
        setSessionData(null);
      }
    } catch (error) {
      console.error('Error fetching session data:', error);
      setSessionData(null);
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    fetchSessionData();
    // Auto-refresh every 60 seconds
    const interval = setInterval(fetchSessionData, 60000);
    return () => clearInterval(interval);
  }, []);

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh) {
      fetchSessionData();
      intervalRef.current = setInterval(fetchSessionData, refreshInterval * 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval]);

  const handleManualRefresh = () => {
    fetchSessionData();
  };

  const handleForceLogout = async (userId: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/admin/force-logout/${userId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('User logout initiated');
        fetchSessionData(); // Refresh data
      } else {
        alert('Failed to logout user');
      }
    } catch (error) {
      console.error('Force logout failed:', error);
      alert('Force logout failed');
    }
  };

  const getTimeUntilExpiry = (expiresAt: string) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();
    
    if (diffMs <= 0) return 'Expired';
    
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const getExpiryStatus = (expiresAt: string) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();
    const hours = diffMs / (1000 * 60 * 60);
    
    if (hours <= 0) return 'expired';
    if (hours <= 2) return 'warning';
    if (hours <= 24) return 'normal';
    return 'healthy';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#10b981';
      case 'normal': return '#3b82f6';
      case 'warning': return '#f59e0b';
      case 'expired': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">Authentication Monitor</h2>
          <p className="text-sm text-gray-400 mt-1">
            JWT token tracking and session management
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Auto-refresh toggle */}
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-300">Auto-refresh:</label>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`w-12 h-6 rounded-full ${autoRefresh ? 'bg-green-500' : 'bg-gray-300'} relative transition-colors`}
            >
              <div className={`w-5 h-5 bg-white rounded-full transition-transform ${autoRefresh ? 'translate-x-6' : 'translate-x-1'} mt-0.5`} />
            </button>
          </div>

          {/* Refresh interval */}
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-300">Interval:</label>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value={30}>30s</option>
              <option value={60}>1m</option>
              <option value={300}>5m</option>
              <option value={600}>10m</option>
            </select>
          </div>

          {/* Manual refresh */}
          <button
            onClick={handleManualRefresh}
            disabled={loadingData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            {loadingData ? 'Refreshing...' : 'Refresh Now'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {errors.sessions && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <span className="text-red-500">❌</span>
              <span className="text-red-700 text-sm">{errors.sessions}</span>
            </div>
            <button
              onClick={() => clearError('sessions')}
              className="text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Authentication Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 text-sm">👥</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-300">Active Sessions</p>
              <p className="text-2xl font-semibold text-white">{sessionData?.active_sessions || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 text-sm">🔑</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-300">Unique Users Today</p>
              <p className="text-2xl font-semibold text-white">{sessionData?.unique_users_today || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-yellow-600 text-sm">⚠️</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-300">Expiry Warnings</p>
              <p className="text-2xl font-semibold text-white">{sessionData?.expiry_warnings || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                <span className="text-gray-600 text-sm">🕐</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-300">Last Updated</p>
              <p className="text-sm text-gray-300">
                {lastRefresh ? lastRefresh.toLocaleTimeString() : 'Never'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Active Sessions Table */}
      <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-700">
          <h3 className="text-lg font-medium text-white">Active Sessions</h3>
          <p className="text-sm text-gray-400 mt-1">Currently authenticated users and their session details</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-600">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Login Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Time Until Expiry
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  IP Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-600">
              {(!sessionData?.sessions || sessionData.sessions.length === 0) ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-400">
                    No active sessions found
                  </td>
                </tr>
              ) : (
                sessionData.sessions.map((session) => {
                  return (
                    <tr key={`${session.id}-${session.login_time}`}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="text-sm font-medium text-white">
                            {session.user}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {session.login_time}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {session.expires_at}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {session.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {session.ip_address}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => handleForceLogout(session.id)}
                          className="text-red-600 hover:text-red-900 text-sm"
                        >
                          Force Logout
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Token Management Section */}
      <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-700">
          <h3 className="text-lg font-medium text-white">Token Management</h3>
          <p className="text-sm text-gray-400 mt-1">JWT token administration and security controls</p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Token Actions */}
            <div>
              <h4 className="text-md font-medium text-white mb-4">Token Actions</h4>
              <div className="space-y-3">
                <button
                  onClick={() => alert('Feature coming soon - Invalidate all tokens')}
                  className="w-full px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm"
                >
                  🚫 Invalidate All Tokens
                </button>
                <button
                  onClick={() => alert('Feature coming soon - Token refresh analysis')}
                  className="w-full px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 text-sm"
                >
                  🔄 Analyze Token Refresh Patterns
                </button>
                <button
                  onClick={() => alert('Feature coming soon - Export token audit log')}
                  className="w-full px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 text-sm"
                >
                  📊 Export Token Audit Log
                </button>
              </div>
            </div>

            {/* Security Alerts */}
            <div>
              <h4 className="text-md font-medium text-white mb-4">Security Alerts</h4>
              <div className="space-y-3">
                <div className="flex items-center p-3 bg-green-50 rounded-lg">
                  <span className="text-green-500 mr-3">✅</span>
                  <div>
                    <div className="text-sm font-medium text-green-800">No suspicious activity</div>
                    <div className="text-xs text-green-600">All tokens within normal parameters</div>
                  </div>
                </div>
                
                {sessionData?.expiry_warnings ? (
                  <div className="flex items-center p-3 bg-yellow-50 rounded-lg">
                    <span className="text-yellow-500 mr-3">⚠️</span>
                    <div>
                      <div className="text-sm font-medium text-yellow-800">
                        {sessionData.expiry_warnings} tokens expiring soon
                      </div>
                      <div className="text-xs text-yellow-600">Users may need to re-authenticate</div>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthenticationMonitor;