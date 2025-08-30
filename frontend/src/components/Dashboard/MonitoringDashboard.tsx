/**
 * Production Monitoring Dashboard
 * Real-time system health and performance monitoring
 */
import React, { useState, useEffect } from 'react';
import { useUnifiedAuthStore } from '../../stores/unified-auth-store';
import { getApiBaseUrl } from '../../utils/api-simple';
import '../../styles/monitoring-dashboard.css';

interface SystemHealth {
  status: string;
  timestamp: string;
  system: {
    cpu_usage: number;
    memory: {
      total: number;
      available: number;
      percent: number;
      used: number;
    };
    disk: {
      total: number;
      used: number;
      free: number;
      percent: number;
    };
  };
  services: {
    database: string;
    cache: string;
    vector_store: string;
  };
}

interface ChatMetrics {
  timestamp: string;
  sessions: {
    total: number;
    active_24h: number;
    avg_messages_per_session: number;
  };
  messages: {
    total: number;
    last_24h: number;
  };
  users: {
    active_24h: number;
  };
  intents: Record<string, number>;
  vector_store: {
    total_documents: number;
    storage_size_mb: number;
  };
}

interface Alert {
  level: 'info' | 'warning' | 'critical';
  message: string;
  timestamp: string;
  category: string;
}

interface Activity {
  type: string;
  timestamp: string;
  description: string;
  session_id?: string;
  user_id?: string;
}

const MonitoringDashboard: React.FC = () => {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [chatMetrics, setChatMetrics] = useState<ChatMetrics | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [liveActivity, setLiveActivity] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  const user = useUnifiedAuthStore((state) => state.user);
  const authToken = useUnifiedAuthStore((state) => state.getAccessToken());

  useEffect(() => {
    if (user && authToken) {
      fetchAllData();
      
      if (autoRefresh) {
        const interval = setInterval(fetchAllData, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
      }
    }
  }, [user, authToken, autoRefresh]);

  const fetchWithAuth = async (endpoint: string) => {
    const baseUrl = getApiBaseUrl();
    const response = await fetch(`${baseUrl}/api/v1/monitoring${endpoint}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch ${endpoint}: ${response.statusText}`);
    }
    
    return response.json();
  };

  const fetchAllData = async () => {
    try {
      setError(null);
      
      const [healthData, metricsData, alertsData, activityData] = await Promise.all([
        fetchWithAuth('/system-health'),
        fetchWithAuth('/chat-metrics'),
        fetchWithAuth('/alerts'),
        fetchWithAuth('/live-activity')
      ]);
      
      setSystemHealth(healthData);
      setChatMetrics(metricsData);
      setAlerts(alertsData.alerts);
      setLiveActivity(activityData.activities);
      
    } catch (err) {
      console.error('Failed to fetch monitoring data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load monitoring data');
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInMin = Math.floor(diffInMs / (1000 * 60));
    
    if (diffInMin < 1) return 'Just now';
    if (diffInMin < 60) return `${diffInMin}m ago`;
    const diffInHr = Math.floor(diffInMin / 60);
    if (diffInHr < 24) return `${diffInHr}h ago`;
    const diffInDays = Math.floor(diffInHr / 24);
    return `${diffInDays}d ago`;
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy': return 'green';
      case 'warning': return 'orange';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'critical': return '🚨';
      case 'warning': return '⚠️';
      default: return 'ℹ️';
    }
  };

  if (loading) {
    return (
      <div className="monitoring-dashboard loading">
        <div className="loading-spinner"></div>
        <p>Loading monitoring data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="monitoring-dashboard error">
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
          <button onClick={fetchAllData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="monitoring-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <h1>Production Monitoring</h1>
        <div className="header-controls">
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh (30s)
          </label>
          <button onClick={fetchAllData} className="refresh-button">
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* System Health */}
      <div className="monitoring-section">
        <h2>System Health</h2>
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>CPU Usage</h3>
            <div className="metric-value">
              {systemHealth?.system.cpu_usage.toFixed(1)}%
            </div>
            <div className={`metric-bar ${systemHealth?.system.cpu_usage > 80 ? 'high' : 'normal'}`}>
              <div 
                className="metric-fill" 
                style={{ width: `${systemHealth?.system.cpu_usage}%` }}
              ></div>
            </div>
          </div>
          
          <div className="metric-card">
            <h3>Memory</h3>
            <div className="metric-value">
              {systemHealth?.system.memory.percent.toFixed(1)}%
            </div>
            <div className="metric-details">
              {formatBytes(systemHealth?.system.memory.used || 0)} / {formatBytes(systemHealth?.system.memory.total || 0)}
            </div>
            <div className={`metric-bar ${systemHealth?.system.memory.percent > 80 ? 'high' : 'normal'}`}>
              <div 
                className="metric-fill" 
                style={{ width: `${systemHealth?.system.memory.percent}%` }}
              ></div>
            </div>
          </div>
          
          <div className="metric-card">
            <h3>Disk Usage</h3>
            <div className="metric-value">
              {systemHealth?.system.disk.percent.toFixed(1)}%
            </div>
            <div className="metric-details">
              {formatBytes(systemHealth?.system.disk.used || 0)} / {formatBytes(systemHealth?.system.disk.total || 0)}
            </div>
            <div className={`metric-bar ${systemHealth?.system.disk.percent > 80 ? 'high' : 'normal'}`}>
              <div 
                className="metric-fill" 
                style={{ width: `${systemHealth?.system.disk.percent}%` }}
              ></div>
            </div>
          </div>
        </div>
        
        {/* Service Status */}
        <div className="services-status">
          <h3>Service Status</h3>
          <div className="service-indicators">
            {systemHealth?.services && Object.entries(systemHealth.services).map(([service, status]) => (
              <div key={service} className="service-indicator">
                <span 
                  className={`status-dot ${getStatusColor(status)}`}
                  title={status}
                ></span>
                <span className="service-name">{service.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Metrics */}
      <div className="monitoring-section">
        <h2>Chat System Metrics</h2>
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Total Sessions</h3>
            <div className="metric-value">{chatMetrics?.sessions.total}</div>
            <div className="metric-details">
              {chatMetrics?.sessions.active_24h} active in last 24h
            </div>
          </div>
          
          <div className="metric-card">
            <h3>Total Messages</h3>
            <div className="metric-value">{chatMetrics?.messages.total}</div>
            <div className="metric-details">
              {chatMetrics?.messages.last_24h} in last 24h
            </div>
          </div>
          
          <div className="metric-card">
            <h3>Active Users</h3>
            <div className="metric-value">{chatMetrics?.users.active_24h}</div>
            <div className="metric-details">Last 24 hours</div>
          </div>
          
          <div className="metric-card">
            <h3>Avg Messages/Session</h3>
            <div className="metric-value">{chatMetrics?.sessions.avg_messages_per_session}</div>
            <div className="metric-details">Conversation depth</div>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="monitoring-section alerts-section">
          <h2>System Alerts ({alerts.length})</h2>
          <div className="alerts-list">
            {alerts.map((alert, index) => (
              <div key={index} className={`alert-item ${alert.level}`}>
                <span className="alert-icon">{getAlertIcon(alert.level)}</span>
                <div className="alert-content">
                  <div className="alert-message">{alert.message}</div>
                  <div className="alert-meta">
                    {alert.category} • {formatTimeAgo(alert.timestamp)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Live Activity */}
      <div className="monitoring-section">
        <h2>Live Activity</h2>
        <div className="activity-feed">
          {liveActivity.length === 0 ? (
            <div className="no-activity">No recent activity</div>
          ) : (
            liveActivity.slice(0, 10).map((activity, index) => (
              <div key={index} className="activity-item">
                <div className="activity-time">{formatTimeAgo(activity.timestamp)}</div>
                <div className="activity-description">{activity.description}</div>
                {activity.session_id && (
                  <div className="activity-meta">Session: {activity.session_id.slice(-8)}</div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="dashboard-footer">
        <div className="last-updated">
          Last updated: {systemHealth ? formatTimeAgo(systemHealth.timestamp) : 'Unknown'}
        </div>
      </div>
    </div>
  );
};

export default MonitoringDashboard;