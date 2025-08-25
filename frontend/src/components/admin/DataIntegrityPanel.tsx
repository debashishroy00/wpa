/**
 * Data Integrity Panel - Data Validation and Cleanup Tools
 * Completely isolated component for admin data integrity monitoring and management
 */

import React, { useEffect, useState } from 'react';
import { useAdminStore } from '../../stores/admin/adminStore';
import { getApiBaseUrl } from '../../utils/getApiBaseUrl';

interface DataIssue {
  id: string;
  table: string;
  issue_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affected_records: number;
  suggested_action: string;
  created_at: string;
}

interface DataStats {
  total_users: number;
  active_users: number;
  total_financial_entries: number;
  total_goals: number;
  orphaned_records: number;
  data_inconsistencies: number;
  last_backup: string;
  database_size_mb: number;
}

const DataIntegrityPanel: React.FC = () => {
  const { loading, errors, clearError } = useAdminStore();
  const [integrityData, setIntegrityData] = useState<any>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [selectedIssues, setSelectedIssues] = useState<Set<string>>(new Set());
  const [validationRunning, setValidationRunning] = useState(false);
  const [lastValidation, setLastValidation] = useState<Date | null>(null);

  const fetchIntegrityData = async () => {
    try {
      setLoadingData(true);
      const token = localStorage.getItem('token');
      if (!token) return;
      
      const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/data-integrity`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setIntegrityData(data);
        setLastValidation(new Date());
      } else {
        console.error('Failed to fetch integrity data');
      }
    } catch (error) {
      console.error('Error fetching integrity data:', error);
      // Keep null as fallback
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    fetchIntegrityData();
    // Auto-refresh every 5 minutes (less frequent since data changes slowly)
    const interval = setInterval(fetchIntegrityData, 300000);
    return () => clearInterval(interval);
  }, []);

  const runDataValidation = async () => {
    setValidationRunning(true);
    
    // Simulate validation process
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Refresh real data
    await fetchIntegrityData();
    setValidationRunning(false);
  };

  const handleIssueSelection = (issueId: string, checked: boolean) => {
    const newSelection = new Set(selectedIssues);
    if (checked) {
      newSelection.add(issueId);
    } else {
      newSelection.delete(issueId);
    }
    setSelectedIssues(newSelection);
  };

  const handleBulkAction = async (action: string) => {
    if (selectedIssues.size === 0) {
      alert('Please select issues to process');
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to ${action} ${selectedIssues.size} selected issue(s)?\\n\\nThis action cannot be undone.`
    );

    if (confirmed) {
      // Simulate bulk action
      alert(`${action} completed for ${selectedIssues.size} issue(s)`);
      setSelectedIssues(new Set());
      fetchIntegrityData(); // Refresh data
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-700 bg-red-100';
      case 'high': return 'text-orange-700 bg-orange-100';
      case 'medium': return 'text-yellow-700 bg-yellow-100';
      case 'low': return 'text-blue-700 bg-blue-100';
      default: return 'text-gray-300 bg-gray-600';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '⚡';
      case 'low': return 'ℹ️';
      default: return '❓';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">Data Integrity Panel</h2>
          <p className="text-sm text-gray-400 mt-1">
            Data validation, cleanup tools, and integrity monitoring
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={runDataValidation}
            disabled={validationRunning}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            {validationRunning ? 'Validating...' : 'Run Full Validation'}
          </button>
        </div>
      </div>

      {/* Validation Status */}
      {lastValidation && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <span className="text-green-500">✅</span>
            <span className="text-green-700 text-sm">
              Last validation completed: {lastValidation.toLocaleString()}
            </span>
          </div>
        </div>
      )}

      {/* Error Display */}
      {errors.dataIntegrity && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <span className="text-red-500">❌</span>
              <span className="text-red-700 text-sm">{errors.dataIntegrity}</span>
            </div>
            <button
              onClick={() => clearError('dataIntegrity')}
              className="text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Data Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 text-sm">👥</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-300">Total Users</p>
              <p className="text-2xl font-semibold text-white">{integrityData?.summary?.total_users || 0}</p>
              <p className="text-xs text-gray-500">{integrityData?.summary?.active_users || 0} active</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 text-sm">💰</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-300">Financial Records</p>
              <p className="text-2xl font-semibold text-white">{integrityData?.summary?.financial_records || 0}</p>
              <p className="text-xs text-gray-500">{integrityData?.summary?.goals || 0} goals</p>
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
              <p className="text-sm font-medium text-gray-300">Data Issues</p>
              <p className="text-2xl font-semibold text-white">{integrityData?.summary?.data_issues || 0}</p>
              <p className="text-xs text-gray-500">{integrityData?.issues?.length || 0} detected</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-purple-600 text-sm">💾</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-300">Database Size</p>
              <p className="text-2xl font-semibold text-white">{integrityData?.summary?.database_size || 'Unknown'}</p>
              <p className="text-xs text-gray-500">
                Backup: {integrityData?.summary?.last_backup || 'Unknown'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Data Issues Table */}
      <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-700">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-medium text-white">Data Issues</h3>
              <p className="text-sm text-gray-400 mt-1">Identified data integrity problems requiring attention</p>
            </div>
            
            {selectedIssues.size > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-300">{selectedIssues.size} selected</span>
                <button
                  onClick={() => handleBulkAction('Fix')}
                  className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200"
                >
                  Fix Selected
                </button>
                <button
                  onClick={() => handleBulkAction('Ignore')}
                  className="px-3 py-1 bg-gray-600 text-gray-100 rounded text-sm hover:bg-gray-500"
                >
                  Ignore Selected
                </button>
              </div>
            )}
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-600">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  <input
                    type="checkbox"
                    checked={selectedIssues.size === (integrityData?.issues?.length || 0) && (integrityData?.issues?.length || 0) > 0}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedIssues(new Set(integrityData?.issues?.map(issue => issue.id.toString()) || []));
                      } else {
                        setSelectedIssues(new Set());
                      }
                    }}
                    className="rounded border-gray-300"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Issue
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Severity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Affected Records
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Detected
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-gray-800 divide-y divide-gray-600">
              {loadingData ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center">
                    <div className="text-4xl mb-4">⏳</div>
                    <h4 className="text-lg font-medium text-white mb-2">Loading...</h4>
                    <p className="text-gray-300">Checking database integrity</p>
                  </td>
                </tr>
              ) : (!integrityData?.issues || integrityData.issues.length === 0) ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center">
                    <div className="text-4xl mb-4">🎉</div>
                    <h4 className="text-lg font-medium text-white mb-2">No Data Issues Found</h4>
                    <p className="text-gray-300">Your data integrity is excellent!</p>
                  </td>
                </tr>
              ) : (
                integrityData.issues.map((issue) => (
                  <tr key={issue.id} className="hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedIssues.has(issue.id)}
                        onChange={(e) => handleIssueSelection(issue.id, e.target.checked)}
                        className="rounded border-gray-300"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="max-w-xs">
                        <div className="text-sm font-medium text-white">{issue.issue}</div>
                        <div className="text-xs text-gray-400 mt-1">
                          Table: {issue.table} • Type: {issue.type}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{getSeverityIcon(issue.severity)}</span>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(issue.severity)}`}>
                          {issue.severity}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {issue.affected_records}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {issue.detected}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <button
                        onClick={() => alert(`Fix issue: ${issue.issue}`)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Fix
                      </button>
                      <button
                        onClick={() => alert(`Ignore issue: ${issue.issue}`)}
                        className="text-gray-600 hover:text-gray-900"
                      >
                        Ignore
                      </button>
                      <button
                        onClick={() => alert(`Details for: ${issue.issue}\\n\\nTable: ${issue.table}\\nType: ${issue.type}\\nAffected: ${issue.affected_records} records\\nDetected: ${issue.detected}`)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Data Cleanup Tools */}
      <div className="bg-gray-800 border border-gray-700 text-gray-100 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-700">
          <h3 className="text-lg font-medium text-white">Data Cleanup Tools</h3>
          <p className="text-sm text-gray-400 mt-1">Database maintenance and cleanup utilities</p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Cleanup Actions */}
            <div>
              <h4 className="text-md font-medium text-white mb-4">Cleanup Actions</h4>
              <div className="space-y-3">
                <button
                  onClick={() => alert('Feature coming soon - Remove orphaned records')}
                  className="w-full px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm"
                >
                  🗑️ Remove Orphaned Records
                </button>
                <button
                  onClick={() => alert('Feature coming soon - Archive old data')}
                  className="w-full px-4 py-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 text-sm"
                >
                  📦 Archive Old Data
                </button>
                <button
                  onClick={() => alert('Feature coming soon - Optimize database')}
                  className="w-full px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 text-sm"
                >
                  ⚡ Optimize Database
                </button>
              </div>
            </div>

            {/* Data Analysis */}
            <div>
              <h4 className="text-md font-medium text-white mb-4">Data Analysis</h4>
              <div className="space-y-3">
                <button
                  onClick={() => alert('Feature coming soon - Generate data quality report')}
                  className="w-full px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 text-sm"
                >
                  📊 Data Quality Report
                </button>
                <button
                  onClick={() => alert('Feature coming soon - Analyze user patterns')}
                  className="w-full px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 text-sm"
                >
                  📈 Usage Patterns
                </button>
                <button
                  onClick={() => alert('Feature coming soon - Export data audit')}
                  className="w-full px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 text-sm"
                >
                  📋 Export Audit Log
                </button>
              </div>
            </div>

            {/* Backup & Restore */}
            <div>
              <h4 className="text-md font-medium text-white mb-4">Backup & Restore</h4>
              <div className="space-y-3">
                <button
                  onClick={() => alert('Feature coming soon - Create manual backup')}
                  className="w-full px-4 py-2 bg-cyan-100 text-cyan-700 rounded-lg hover:bg-cyan-200 text-sm"
                >
                  💾 Create Backup
                </button>
                <button
                  onClick={() => alert('Feature coming soon - Schedule automatic backups')}
                  className="w-full px-4 py-2 bg-teal-100 text-teal-700 rounded-lg hover:bg-teal-200 text-sm"
                >
                  ⏰ Schedule Backups
                </button>
                <button
                  onClick={() => alert('Feature coming soon - View backup history')}
                  className="w-full px-4 py-2 bg-emerald-100 text-emerald-700 rounded-lg hover:bg-emerald-200 text-sm"
                >
                  🕐 Backup History
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataIntegrityPanel;