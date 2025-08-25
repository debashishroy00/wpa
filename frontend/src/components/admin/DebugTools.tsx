/**
 * Debug Tools - System Debugging and Diagnostic Utilities
 * Completely isolated component for admin debugging and system diagnostics
 */

import React, { useEffect, useState, useRef } from 'react';
import { useAdminStore } from '../../stores/admin/adminStore';
import { getApiBaseUrl } from '../../utils/getApiBaseUrl';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  module: string;
}

interface DebugMetrics {
  api_requests_last_hour: number;
  error_rate_percentage: number;
  average_response_time: number;
  active_connections: number;
  memory_usage_mb: number;
  cpu_usage_percentage: number;
}

const DebugTools: React.FC = () => {
  const { loading, errors, clearError } = useAdminStore();
  const [debugData, setDebugData] = useState<any>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [autoRefreshLogs, setAutoRefreshLogs] = useState(true);
  const [logLimit, setLogLimit] = useState(100);
  const [logLevel, setLogLevel] = useState('INFO');
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchDebugData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/debug/performance`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDebugData(data);
      } else {
        console.error('Failed to fetch debug data');
      }
    } catch (error) {
      console.error('Error fetching debug data:', error);
    }
  };

  const fetchLogs = async (level = logLevel) => {
    try {
      setLoadingData(true);
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const response = await fetch(`/api/v1/admin/debug/logs?level=${level}&limit=${logLimit}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs);
        setLastRefresh(new Date());
      } else {
        console.error('Failed to fetch logs');
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    fetchDebugData();
    fetchLogs();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchDebugData();
      fetchLogs();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefreshLogs) {
      fetchLogs();
      fetchDebugData();
      
      intervalRef.current = setInterval(() => {
        fetchLogs();
        fetchDebugData();
      }, 30000); // 30 seconds
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
  }, [autoRefreshLogs, logLimit, logLevel]);

  const handleManualRefresh = () => {
    fetchLogs();
    fetchDebugData();
  };

  const clearAllCaches = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/clear-cache`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('All system caches cleared successfully');
      } else {
        alert('Failed to clear caches');
      }
    } catch (error) {
      console.error('Clear caches failed:', error);
      alert('Clear caches failed');
    }
  };

  const testEndpoint = async (endpoint: string) => {
    try {
      const token = localStorage.getItem('token');
      const startTime = performance.now();
      
      const response = await fetch(endpoint, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const endTime = performance.now();
      const responseTime = Math.round(endTime - startTime);
      
      if (response.ok) {
        alert(`✅ Endpoint Test Successful\\nURL: ${endpoint}\\nResponse Time: ${responseTime}ms\\nStatus: ${response.status}`);
      } else {
        alert(`❌ Endpoint Test Failed\\nURL: ${endpoint}\\nResponse Time: ${responseTime}ms\\nStatus: ${response.status}`);
      }
    } catch (error) {
      alert(`❌ Endpoint Test Error\\nURL: ${endpoint}\\nError: ${error}`);
    }
  };

  const exportLogs = () => {
    const logsText = logs.map(log => 
      `[${log.timestamp}] ${log.level.toUpperCase()} ${log.module}: ${log.message}`
    ).join('\\n');
    
    const blob = new Blob([logsText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `system-logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getLogLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error': return 'text-red-600 bg-red-50';
      case 'warning': case 'warn': return 'text-yellow-600 bg-yellow-50';
      case 'info': return 'text-blue-600 bg-blue-50';
      case 'debug': return 'text-gray-300 bg-gray-600';
      default: return 'text-gray-300 bg-gray-600';
    }
  };

  // Logs are now filtered on the backend

  const getMetricColor = (value: number, type: string) => {
    switch (type) {
      case 'error_rate':
        if (value > 2) return 'text-red-600';
        if (value > 1) return 'text-yellow-600';
        return 'text-green-600';
      case 'response_time':
        if (value > 200) return 'text-red-600';
        if (value > 100) return 'text-yellow-600';
        return 'text-green-600';
      case 'cpu':
        if (value > 80) return 'text-red-600';
        if (value > 60) return 'text-yellow-600';
        return 'text-green-600';
      default:
        return 'text-gray-900';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">Debug Tools</h2>
          <p className="text-sm text-gray-400 mt-1">
            System logs, diagnostics, and debugging utilities
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Auto-refresh toggle */}
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-300">Auto-refresh:</label>
            <button
              onClick={() => setAutoRefreshLogs(!autoRefreshLogs)}
              className={`w-12 h-6 rounded-full ${autoRefreshLogs ? 'bg-green-500' : 'bg-gray-300'} relative transition-colors`}
            >
              <div className={`w-5 h-5 bg-white rounded-full transition-transform ${autoRefreshLogs ? 'translate-x-6' : 'translate-x-1'} mt-0.5`} />
            </button>
          </div>

          {/* Manual refresh */}
          <button
            onClick={handleManualRefresh}
            disabled={loading.logs}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            {loading.logs ? 'Refreshing...' : 'Refresh Now'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {errors.logs && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <span className="text-red-500">❌</span>
              <span className="text-red-700 text-sm">{errors.logs}</span>
            </div>
            <button
              onClick={() => clearError('logs')}
              className="text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Debug Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-white">API Performance</h4>
            <span className="text-2xl">📊</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Error Rate:</span>
              <span className="font-medium text-red-400">
                {debugData?.api_performance?.error_rate || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Avg Response:</span>
              <span className="font-medium text-green-400">
                {debugData?.api_performance?.avg_response_time || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Last Updated:</span>
              <span className="font-medium text-gray-300">
                {debugData?.last_updated ? new Date(debugData.last_updated).toLocaleTimeString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-white">System Resources</h4>
            <span className="text-2xl">💻</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>CPU Usage:</span>
              <span className="font-medium text-yellow-400">
                {debugData?.system_resources?.cpu_usage || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Memory Usage:</span>
              <span className="font-medium text-blue-400">
                {debugData?.system_resources?.memory_usage || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Status:</span>
              <span className="font-medium text-green-400">
                {debugData ? 'Online' : 'Loading...'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-white">System Actions</h4>
            <span className="text-2xl">🔧</span>
          </div>
          <div className="space-y-2">
            <button
              onClick={clearAllCaches}
              className="w-full px-3 py-2 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200"
            >
              Clear All Caches
            </button>
            <button
              onClick={() => testEndpoint('/api/v1/auth/me')}
              className="w-full px-3 py-2 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200"
            >
              Test Auth Endpoint
            </button>
            <button
              onClick={() => testEndpoint('/api/v1/admin/health')}
              className="w-full px-3 py-2 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200"
            >
              Test Health Endpoint
            </button>
          </div>
        </div>
      </div>

      {/* System Logs */}
      <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-700">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-medium text-white">System Logs</h3>
              <p className="text-sm text-gray-400 mt-1">
                Recent system logs and events
                {lastRefresh && (
                  <span className="ml-2">
                    (Last updated: {lastRefresh.toLocaleTimeString()})
                  </span>
                )}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {/* Log Level Filter */}
              <div className="flex items-center space-x-2">
                <label className="text-sm text-gray-300">Level:</label>
                <select
                  value={logLevel}
                  onChange={(e) => {
                    setLogLevel(e.target.value);
                    fetchLogs(e.target.value);
                  }}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value="ALL">All</option>
                  <option value="ERROR">Error</option>
                  <option value="WARNING">Warning</option>
                  <option value="INFO">Info</option>
                  <option value="DEBUG">Debug</option>
                </select>
              </div>

              {/* Log Limit */}
              <div className="flex items-center space-x-2">
                <label className="text-sm text-gray-300">Limit:</label>
                <select
                  value={logLimit}
                  onChange={(e) => setLogLimit(Number(e.target.value))}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={200}>200</option>
                  <option value={500}>500</option>
                </select>
              </div>

              {/* Export Logs */}
              <button
                onClick={exportLogs}
                className="px-3 py-2 bg-gray-600 text-gray-100 rounded text-sm hover:bg-gray-500"
              >
                Export Logs
              </button>
            </div>
          </div>
        </div>
        
        <div className="max-h-96 overflow-y-auto">
          {loadingData ? (
            <div className="p-6 text-center text-gray-400">
              <div className="text-4xl mb-4">⏳</div>
              <p>Loading logs...</p>
            </div>
          ) : logs.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              <div className="text-4xl mb-4">📋</div>
              <p>No logs available</p>
              <p className="text-sm mt-2">System logs will appear here when available</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {logs.map((log, index) => (
                <div key={index} className="p-4 hover:bg-gray-700">
                  <div className="flex items-start space-x-3">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getLogLevelColor(log.level)}`}>
                      {log.level.toUpperCase()}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm text-white break-words">{log.message}</p>
                        <div className="flex items-center space-x-2 text-xs text-gray-400 ml-4 flex-shrink-0">
                          <span>{log.module}</span>
                          <span>•</span>
                          <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Endpoint Testing */}
      <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-700">
          <h3 className="text-lg font-medium text-white">Endpoint Testing</h3>
          <p className="text-sm text-gray-400 mt-1">Test API endpoints and monitor response times</p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { name: 'Health Check', endpoint: '/api/v1/admin/health' },
              { name: 'User Profile', endpoint: '/api/v1/auth/me' },
              { name: 'User List', endpoint: '/api/v1/admin/users' },
              { name: 'System Sessions', endpoint: '/api/v1/admin/sessions' },
              { name: 'Financial Data', endpoint: '/api/v1/financial/' },
              { name: 'Goals Data', endpoint: '/api/v1/goals-v2/' }
            ].map((test) => (
              <button
                key={test.endpoint}
                onClick={() => testEndpoint(test.endpoint)}
                className="p-4 border border-gray-600 rounded-lg hover:bg-gray-700 text-left"
              >
                <div className="font-medium text-gray-900">{test.name}</div>
                <div className="text-sm text-gray-600 mt-1">{test.endpoint}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DebugTools;