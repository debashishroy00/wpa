/**
 * Admin Dashboard - Main Layout Component (Completely Isolated)
 * This component provides the main admin dashboard without affecting existing routing
 */

import React, { useState, useEffect } from 'react';
import { useAdminStore } from '../../stores/admin/adminStore';
import UserManagement from '../../components/admin/UserManagement';
import SystemHealth from '../../components/admin/SystemHealth';
import AuthenticationMonitor from '../../components/admin/AuthenticationMonitor';
import DebugTools from '../../components/admin/DebugTools';
import DataIntegrityPanel from '../../components/admin/DataIntegrityPanel';
import ShadowModeMonitor from '../../components/admin/ShadowModeMonitor';

type AdminSection = 'users' | 'health' | 'auth' | 'debug' | 'data-integrity' | 'shadow-mode';

interface AdminDashboardProps {
  user?: {
    id: number;
    email: string;
    first_name?: string;
    last_name?: string;
    is_active: boolean;
  };
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ user }) => {
  const [activeSection, setActiveSection] = useState<AdminSection>('users');
  const { isAdminAvailable, checkAdminAvailability } = useAdminStore();

  useEffect(() => {
    // Check if admin features are available
    checkAdminAvailability();
  }, [checkAdminAvailability]);

  const navigationItems = [
    { id: 'users' as AdminSection, label: 'User Management', icon: '👥', description: 'Manage users and sessions' },
    { id: 'health' as AdminSection, label: 'System Health', icon: '🏥', description: 'Monitor system status' },
    { id: 'auth' as AdminSection, label: 'Auth Monitor', icon: '🔐', description: 'Authentication tracking' },
    { id: 'debug' as AdminSection, label: 'Debug Tools', icon: '🔧', description: 'System debugging' },
    { id: 'data-integrity' as AdminSection, label: 'Data Integrity', icon: '🛡️', description: 'Data validation' },
    { id: 'shadow-mode' as AdminSection, label: 'Shadow Mode Testing', icon: '🧪', description: 'LLM response testing' },
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'users':
        return <UserManagement />;
      case 'health':
        return <SystemHealth />;
      case 'auth':
        return <AuthenticationMonitor />;
      case 'debug':
        return <DebugTools />;
      case 'data-integrity':
        return <DataIntegrityPanel />;
      case 'shadow-mode':
        return <ShadowModeMonitor />;
      default:
        return <UserManagement />;
    }
  };

  if (!isAdminAvailable) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#1a1a1a' }}>
        <div className="max-w-md w-full rounded-lg shadow-lg p-8 text-center" style={{ backgroundColor: '#2a2a2a', border: '1px solid #404040' }}>
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold mb-4" style={{ color: '#ffffff' }}>Admin Features Unavailable</h2>
          <p className="mb-6" style={{ color: '#a0a0a0' }}>
            Admin backend services are not currently available. Please check that the admin API endpoints are deployed and accessible.
          </p>
          <button
            onClick={checkAdminAvailability}
            className="px-4 py-2 rounded-lg hover:opacity-80 transition-opacity"
            style={{ backgroundColor: '#3b82f6', color: '#ffffff' }}
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#1a1a1a' }}>
      {/* Header */}
      <div style={{ backgroundColor: '#1a1a2e', borderBottom: '1px solid #404040' }} className="shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-xl font-semibold" style={{ color: '#ffffff' }}>Admin Dashboard</h1>
              <p className="text-sm" style={{ color: '#9ca3af' }}>WealthPath AI System Administration</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm" style={{ color: '#9ca3af' }}>
                Logged in as: <span className="font-medium" style={{ color: '#ffffff' }}>{user?.email || 'Unknown'}</span>
              </div>
              <div className="w-2 h-2 bg-green-400 rounded-full" title="Admin features active"></div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="lg:grid lg:grid-cols-12 lg:gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-3">
            <nav className="space-y-1">
              {navigationItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => !item.disabled && setActiveSection(item.id)}
                  disabled={item.disabled}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeSection === item.id
                      ? 'border-l-4 border-blue-500'
                      : item.disabled
                      ? 'cursor-not-allowed'
                      : ''
                  }`}
                  style={{
                    backgroundColor: activeSection === item.id ? '#1e3a8a20' : 'transparent',
                    color: activeSection === item.id ? '#60a5fa' : item.disabled ? '#666666' : '#ffffff',
                  }}
                  onMouseEnter={(e) => {
                    if (!item.disabled && activeSection !== item.id) {
                      e.currentTarget.style.backgroundColor = '#333333';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!item.disabled && activeSection !== item.id) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">{item.icon}</span>
                    <div>
                      <div className="font-medium">{item.label}</div>
                      <div className="text-xs" style={{ color: '#888888' }}>{item.description}</div>
                    </div>
                  </div>
                  {item.disabled && (
                    <div className="text-xs mt-1" style={{ color: '#666666' }}>Coming Soon</div>
                  )}
                </button>
              ))}
            </nav>

            {/* System Status Indicator */}
            <div className="mt-8 p-4 rounded-lg shadow" style={{ backgroundColor: '#2a2a2a', border: '1px solid #404040' }}>
              <h3 className="text-sm font-medium mb-2" style={{ color: '#ffffff' }}>System Status</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs" style={{ color: '#a0a0a0' }}>Admin API</span>
                  <span className="w-2 h-2 bg-green-400 rounded-full" title="Healthy"></span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs" style={{ color: '#a0a0a0' }}>Database</span>
                  <span className="w-2 h-2 bg-yellow-400 rounded-full" title="Unknown"></span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs" style={{ color: '#a0a0a0' }}>Cache</span>
                  <span className="w-2 h-2 bg-yellow-400 rounded-full" title="Unknown"></span>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="mt-8 lg:mt-0 lg:col-span-9">
            <div className="rounded-lg shadow" style={{ backgroundColor: '#2a2a2a', border: '1px solid #404040' }}>
              <div className="p-6">
                {renderContent()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;