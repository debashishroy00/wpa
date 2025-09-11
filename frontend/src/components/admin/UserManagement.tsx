/**
 * Admin User Management Component - Completely Isolated
 * This component provides user management functionality without affecting existing UI
 */

import React, { useEffect, useState } from 'react';
import { useAdminStore } from '../../stores/admin/adminStore';

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

const UserManagement: React.FC = () => {
  const {
    users,
    sessions,
    loading,
    errors,
    fetchUsers,
    fetchSessions,
    forceLogoutUser,
    clearUserCache,
    clearUserTokens,
    clearError
  } = useAdminStore();

  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [confirmAction, setConfirmAction] = useState<{
    type: string;
    userId: number;
    userEmail: string;
  } | null>(null);

  useEffect(() => {
    // Safely load data on mount
    try {
      fetchUsers();
      fetchSessions();
    } catch (error) {
      console.error('Admin: Failed to load initial data:', error);
    }
  }, [fetchUsers, fetchSessions]);

  const handleAction = async (action: string, userId: number, userEmail: string) => {
    if (action === 'view') {
      const user = users.find(u => u.id === userId);
      setSelectedUser(user || null);
      return;
    }

    // For destructive actions, show confirmation
    if (['force_logout', 'clear_cache', 'clear_tokens'].includes(action)) {
      setConfirmAction({ type: action, userId, userEmail });
      return;
    }

    // Handle impersonate (open new tab)
    if (action === 'impersonate') {
      try {
        const newTab = window.open(window.location.origin, '_blank');
        if (newTab) {
          // This would require backend support to generate impersonation tokens
          console.log(`Admin: Impersonating user ${userEmail} (feature pending backend support)`);
        }
      } catch (error) {
        console.error('Admin: Impersonate failed:', error);
      }
    }
  };

  const executeConfirmedAction = async () => {
    if (!confirmAction) return;

    try {
      let success = false;
      
      switch (confirmAction.type) {
        case 'force_logout':
          success = await forceLogoutUser(confirmAction.userId);
          break;
        case 'clear_cache':
          success = await clearUserCache(confirmAction.userId);
          break;
        case 'clear_tokens':
          success = await clearUserTokens(confirmAction.userId);
          break;
      }

      if (success) {
        console.log(`Admin: Successfully executed ${confirmAction.type} for ${confirmAction.userEmail}`);
        // Refresh data
        fetchUsers();
        fetchSessions();
      } else {
        console.error(`Admin: Failed to execute ${confirmAction.type} for ${confirmAction.userEmail}`);
      }
    } catch (error) {
      console.error('Admin: Action execution failed:', error);
    } finally {
      setConfirmAction(null);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return 'N/A';
    }
  };

  const getActiveSessionsForUser = (userId: number) => {
    // Find user by ID to get email
    const user = users.find(u => u.id === userId);
    if (!user) return [];
    
    // Filter sessions by user email since the new session structure uses email
    return sessions.filter(session => session.user === user.email);
  };

  // Safe error display
  const ErrorMessage = ({ error, onClear }: { error: string; onClear: () => void }) => (
    <div className="mb-4 p-3 bg-red-900/20 border border-red-800 rounded-lg">
      <div className="flex justify-between items-center">
        <span className="text-red-400 text-sm">{error}</span>
        <button
          onClick={onClear}
          className="text-red-400 hover:text-red-300 text-sm"
        >
          ×
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-semibold text-white">User Management</h2>
          <p className="text-sm text-gray-400 mt-1">Manage users and sessions</p>
        </div>
        <button
          onClick={() => {
            fetchUsers();
            fetchSessions();
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          disabled={loading.users || loading.sessions}
        >
          {loading.users || loading.sessions ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Error Messages */}
      {errors.users && (
        <ErrorMessage 
          error={errors.users} 
          onClear={() => clearError('users')} 
        />
      )}
      {errors.sessions && (
        <ErrorMessage 
          error={errors.sessions} 
          onClear={() => clearError('sessions')} 
        />
      )}

      {/* Users Table */}
      <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-700">
          <h3 className="text-lg font-medium text-white">
            Registered Users ({users.length})
          </h3>
        </div>

        {loading.users ? (
          <div className="p-6 text-center">
            <div className="text-gray-500">Loading users...</div>
          </div>
        ) : users.length === 0 ? (
          <div className="p-6 text-center">
            <div className="text-gray-400">No users found</div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-600">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Activity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Data Summary
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Active Sessions
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-600">
                {users.map((user) => {
                  const userSessions = getActiveSessionsForUser(user.id);
                  return (
                    <tr key={user.id} className="hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-white">
                            {user.first_name || user.last_name 
                              ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                              : 'N/A'
                            }
                          </div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                          <div className="text-xs text-gray-400">ID: {user.id}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            user.is_active 
                              ? 'bg-green-900/50 text-green-400 border border-green-800' 
                              : 'bg-red-900/50 text-red-400 border border-red-800'
                          }`}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                          <span className="text-xs text-gray-400 mt-1">{user.status}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                        <div>
                          <div>Registered: {formatDate(user.created_at)}</div>
                          <div>Last Login: {user.last_login_at ? formatDate(user.last_login_at) : 'Never'}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                        <div>
                          <div>Entries: {user.financial_entries_count || 0}</div>
                          <div>Net Worth: ${user.net_worth?.toLocaleString() || 'N/A'}</div>
                          <div>Goals: {user.goals_count || 0}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            userSessions.length > 0 
                              ? 'bg-green-900/50 text-green-400 border border-green-800' 
                              : 'bg-gray-700 text-gray-300 border border-gray-600'
                          }`}>
                            {userSessions.length} active
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex space-x-2 justify-end">
                          <button
                            onClick={() => handleAction('view', user.id, user.email)}
                            className="text-blue-400 hover:text-blue-300 text-xs transition-colors"
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleAction('clear_cache', user.id, user.email)}
                            className="text-yellow-400 hover:text-yellow-300 text-xs transition-colors"
                          >
                            Clear Cache
                          </button>
                          <button
                            onClick={() => handleAction('clear_tokens', user.id, user.email)}
                            className="text-orange-400 hover:text-orange-300 text-xs transition-colors"
                          >
                            Clear Tokens
                          </button>
                          {userSessions.length > 0 && (
                            <button
                              onClick={() => handleAction('force_logout', user.id, user.email)}
                              className="text-red-400 hover:text-red-300 text-xs transition-colors"
                            >
                              Force Logout
                            </button>
                          )}
                          <button
                            onClick={() => handleAction('impersonate', user.id, user.email)}
                            className="text-purple-400 hover:text-purple-300 text-xs transition-colors"
                          >
                            Impersonate
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* User Details Modal */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-75 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border border-gray-700 w-11/12 max-w-2xl shadow-lg rounded-lg bg-gray-800">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-white">User Details</h3>
              <button
                onClick={() => setSelectedUser(null)}
                className="text-gray-400 hover:text-gray-200 text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400">Email</label>
                  <div className="text-sm text-gray-200">{selectedUser.email}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400">ID</label>
                  <div className="text-sm text-gray-200">{selectedUser.id}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400">Name</label>
                  <div className="text-sm text-gray-200">
                    {selectedUser.first_name || selectedUser.last_name 
                      ? `${selectedUser.first_name || ''} ${selectedUser.last_name || ''}`.trim()
                      : 'N/A'
                    }
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400">Status</label>
                  <div className="text-sm text-gray-200">{selectedUser.status}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400">Created</label>
                  <div className="text-sm text-gray-200">{formatDate(selectedUser.created_at)}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400">Last Login</label>
                  <div className="text-sm text-gray-200">
                    {selectedUser.last_login_at ? formatDate(selectedUser.last_login_at) : 'Never'}
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-700 pt-4">
                <h4 className="text-sm font-medium text-gray-300 mb-2">Data Summary</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-gray-700/50 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-blue-400">
                      {selectedUser.financial_entries_count || 0}
                    </div>
                    <div className="text-xs text-gray-400">Financial Entries</div>
                  </div>
                  <div className="bg-gray-700/50 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-green-400">
                      ${selectedUser.net_worth?.toLocaleString() || 'N/A'}
                    </div>
                    <div className="text-xs text-gray-400">Net Worth</div>
                  </div>
                  <div className="bg-gray-700/50 p-3 rounded-lg">
                    <div className="text-2xl font-bold text-purple-400">
                      {selectedUser.goals_count || 0}
                    </div>
                    <div className="text-xs text-gray-400">Goals</div>
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-700 pt-4">
                <h4 className="text-sm font-medium text-gray-300 mb-2">Active Sessions</h4>
                {getActiveSessionsForUser(selectedUser.id).length === 0 ? (
                  <div className="text-sm text-gray-400">No active sessions</div>
                ) : (
                  <div className="space-y-2">
                    {getActiveSessionsForUser(selectedUser.id).map((session, index) => (
                      <div key={index} className="p-2 bg-gray-700 rounded text-xs text-gray-300">
                        <div>Login: {formatDate(session.login_time)}</div>
                        <div>Expires: {formatDate(session.expires_at)}</div>
                        {session.ip_address && <div>IP: {session.ip_address}</div>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmAction && (
        <div className="fixed inset-0 bg-black bg-opacity-75 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border border-gray-700 w-96 shadow-lg rounded-lg bg-gray-800">
            <div className="mb-4">
              <h3 className="text-lg font-medium text-white">Confirm Action</h3>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-300">
                Are you sure you want to <strong className="text-white">{confirmAction.type.replace('_', ' ')}</strong> for user{' '}
                <strong className="text-white">{confirmAction.userEmail}</strong>?
              </p>
            </div>

            <div className="flex space-x-4 justify-end">
              <button
                onClick={() => setConfirmAction(null)}
                className="px-4 py-2 text-sm text-gray-300 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={executeConfirmedAction}
                className="px-4 py-2 text-sm text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;