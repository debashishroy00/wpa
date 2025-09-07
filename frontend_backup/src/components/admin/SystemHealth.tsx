/**
 * System Health Dashboard - Real-time System Monitoring
 * Completely isolated component for admin system health monitoring
 */

import React, { useEffect, useState, useRef } from 'react';
import { useAdminStore } from '../../stores/admin/adminStore';

interface HealthService {
  status: 'healthy' | 'error';
  responseTime: number;
  uptime: string;
}

interface SystemHealthData {
  overall: number;
  services: {
    database: HealthService;
    redis: HealthService;
    vectorDB: HealthService;
    llm: HealthService;
    api: HealthService;
  };
}

const SystemHealth: React.FC = () => {
  const { systemHealth, loading, errors, fetchSystemHealth, clearError } = useAdminStore();
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh) {
      // Initial load
      fetchSystemHealth();
      setLastRefresh(new Date());

      // Set up interval
      intervalRef.current = setInterval(() => {
        fetchSystemHealth();
        setLastRefresh(new Date());
      }, refreshInterval * 1000);
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
  }, [autoRefresh, refreshInterval, fetchSystemHealth]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#10b981'; // green
      case 'warning': return '#f59e0b'; // yellow
      case 'error': return '#ef4444';   // red
      default: return '#6b7280';       // gray
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return '❓';
    }
  };

  const formatResponseTime = (ms?: number) => {
    if (!ms && ms !== 0) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const handleManualRefresh = () => {
    fetchSystemHealth();
    setLastRefresh(new Date());
  };

  const testEndpoint = async (endpoint: string) => {
    try {
      // This would call a specific endpoint test
      console.log(`Testing endpoint: ${endpoint}`);
      // TODO: Implement endpoint testing
      alert(`Testing ${endpoint} - Feature coming soon`);
    } catch (error) {
      console.error(`Failed to test ${endpoint}:`, error);
    }
  };

  // Get overall health from API response
  const getOverallHealth = () => {
    if (!systemHealth) return { status: 'unknown', percentage: 0, healthy: 0, total: 0 };
    
    const percentage = systemHealth.overall || 0;
    let status: 'healthy' | 'warning' | 'error' = 'error';
    
    if (percentage >= 80) status = 'healthy';
    else if (percentage >= 50) status = 'warning';
    else status = 'error';

    const services = systemHealth.services || {};
    const healthy = Object.values(services).filter(service => service.status === 'healthy').length;
    const total = Object.keys(services).length;

    return { status, percentage, healthy, total };
  };

  const overall = getOverallHealth();

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">System Health Dashboard</h2>
          <p className="text-sm text-gray-400 mt-1">
            Real-time monitoring of system components and services
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
              <option value={10}>10s</option>
              <option value={30}>30s</option>
              <option value={60}>1m</option>
              <option value={300}>5m</option>
            </select>
          </div>

          {/* Manual refresh */}
          <button
            onClick={handleManualRefresh}
            disabled={loading.health}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            {loading.health ? 'Checking...' : 'Refresh Now'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {errors.health && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <span className="text-red-500">❌</span>
              <span className="text-red-700 text-sm">{errors.health}</span>
            </div>
            <button
              onClick={() => clearError('health')}
              className="text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Overall System Status */}
      <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-white">Overall System Status</h3>
            <p className="text-sm text-gray-400">
              {lastRefresh ? `Last updated: ${lastRefresh.toLocaleTimeString()}` : 'Never updated'}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-center">
              <div className={`text-3xl font-bold`} style={{ color: getStatusColor(overall.status) }}>
                {overall.percentage}%
              </div>
              <div className="text-xs text-gray-400">Healthy</div>
            </div>
            <div className="text-4xl">
              {getStatusIcon(overall.status)}
            </div>
          </div>
        </div>
        
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm text-gray-300">
            <span>Services: {overall.healthy}/{overall.total} healthy</span>
            <span>Status: {overall.status.toUpperCase()}</span>
          </div>
          <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
            <div
              className="h-2 rounded-full transition-all duration-300"
              style={{
                width: `${overall.percentage}%`,
                backgroundColor: getStatusColor(overall.status)
              }}
            />
          </div>
        </div>
      </div>

      {/* Core Services Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Database */}
        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-white">Database</h4>
            <span className="text-2xl">{getStatusIcon(systemHealth?.services?.database?.status || 'unknown')}</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Status:</span>
              <span style={{ color: getStatusColor(systemHealth?.services?.database?.status || 'unknown') }}>
                {systemHealth?.services?.database?.status || 'Unknown'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Response Time:</span>
              <span className="text-gray-300">{formatResponseTime(systemHealth?.services?.database?.responseTime)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Uptime:</span>
              <span className="text-gray-300">{systemHealth?.services?.database?.uptime || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Redis */}
        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-white">Redis Cache</h4>
            <span className="text-2xl">{getStatusIcon(systemHealth?.services?.redis?.status || 'unknown')}</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Status:</span>
              <span style={{ color: getStatusColor(systemHealth?.services?.redis?.status || 'unknown') }}>
                {systemHealth?.services?.redis?.status || 'Unknown'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Response Time:</span>
              <span className="text-gray-300">{formatResponseTime(systemHealth?.services?.redis?.responseTime)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Uptime:</span>
              <span className="text-gray-300">{systemHealth?.services?.redis?.uptime || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Vector Database */}
        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-white">Vector Database</h4>
            <span className="text-2xl">{getStatusIcon(systemHealth?.services?.vectorDB?.status || 'unknown')}</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Status:</span>
              <span style={{ color: getStatusColor(systemHealth?.services?.vectorDB?.status || 'unknown') }}>
                {systemHealth?.services?.vectorDB?.status || 'Unknown'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Response Time:</span>
              <span className="text-gray-300">{formatResponseTime(systemHealth?.services?.vectorDB?.responseTime)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Uptime:</span>
              <span className="text-gray-300">{systemHealth?.services?.vectorDB?.uptime || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* LLM & API Services */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* LLM Services */}
        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-white">LLM Services</h4>
            <span className="text-2xl">{getStatusIcon(systemHealth?.services?.llm?.status || 'unknown')}</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Status:</span>
              <span style={{ color: getStatusColor(systemHealth?.services?.llm?.status || 'unknown') }}>
                {systemHealth?.services?.llm?.status || 'Unknown'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Response Time:</span>
              <span className="text-gray-300">{formatResponseTime(systemHealth?.services?.llm?.responseTime)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Uptime:</span>
              <span className="text-gray-300">{systemHealth?.services?.llm?.uptime || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* API Services */}
        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-white">API Services</h4>
            <span className="text-2xl">{getStatusIcon(systemHealth?.services?.api?.status || 'unknown')}</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Status:</span>
              <span style={{ color: getStatusColor(systemHealth?.services?.api?.status || 'unknown') }}>
                {systemHealth?.services?.api?.status || 'Unknown'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Response Time:</span>
              <span className="text-gray-300">{formatResponseTime(systemHealth?.services?.api?.responseTime)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-300">Uptime:</span>
              <span className="text-gray-300">{systemHealth?.services?.api?.uptime || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* API Endpoints Health Matrix (placeholder) */}
      <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-700">
          <h3 className="text-lg font-medium text-white">API Endpoints Health</h3>
          <p className="text-sm text-gray-400 mt-1">Monitor critical API endpoint response times</p>
        </div>
        <div className="p-6">
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🔧</div>
            <h4 className="text-lg font-medium text-white mb-2">Endpoint Health Matrix</h4>
            <p className="text-gray-400 mb-4">Coming soon - Real-time API endpoint monitoring</p>
            <button
              onClick={() => testEndpoint('/api/v1/health')}
              className="px-4 py-2 bg-gray-600 text-gray-100 rounded-lg hover:bg-gray-500 text-sm"
            >
              Test Endpoint (Preview)
            </button>
          </div>
        </div>
      </div>

      {/* System Resources (placeholder) */}
      <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-700">
          <h3 className="text-lg font-medium text-white">System Resources</h3>
          <p className="text-sm text-gray-400 mt-1">CPU, Memory, and Disk usage monitoring</p>
        </div>
        <div className="p-6">
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📊</div>
            <h4 className="text-lg font-medium text-white mb-2">Resource Monitoring</h4>
            <p className="text-gray-400">Coming soon - System resource usage graphs and alerts</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealth;