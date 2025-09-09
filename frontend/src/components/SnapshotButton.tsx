import React, { useState } from 'react';
import { Camera, AlertTriangle, CheckCircle } from 'lucide-react';
import { snapshotApi } from '../services/snapshotApi';
import { LastSnapshotInfo } from '../types/snapshot';

interface SnapshotButtonProps {
  onSnapshotCreated?: () => void;
  className?: string;
}

const SnapshotButton: React.FC<SnapshotButtonProps> = ({ onSnapshotCreated, className = '' }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [snapshotName, setSnapshotName] = useState('');
  const [lastSnapshotInfo, setLastSnapshotInfo] = useState<LastSnapshotInfo | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning'; text: string } | null>(null);

  const checkLastSnapshot = async () => {
    try {
      const info = await snapshotApi.getLastSnapshotInfo();
      setLastSnapshotInfo(info);
      
      if (!info.can_create_new) {
        setMessage({
          type: 'warning',
          text: `Last snapshot was ${info.days_since_last} days ago. Wait at least 30 days between snapshots.`
        });
        return false;
      }
      return true;
    } catch (error) {
      console.error('Failed to check last snapshot:', error);
      return true; // Allow if we can't check
    }
  };

  const handleSnapshotClick = async () => {
    setMessage(null);
    const canCreate = await checkLastSnapshot();
    
    if (canCreate) {
      setShowModal(true);
    }
  };

  const createSnapshot = async () => {
    setIsLoading(true);
    try {
      await snapshotApi.createSnapshot({ name: snapshotName.trim() || undefined });
      setMessage({ type: 'success', text: 'Financial snapshot created successfully!' });
      setShowModal(false);
      setSnapshotName('');
      onSnapshotCreated?.();
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to create snapshot' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={handleSnapshotClick}
        className={`flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors ${className}`}
        disabled={isLoading}
      >
        <Camera className="w-4 h-4" />
        Take Snapshot
      </button>

      {message && (
        <div className={`mt-2 p-3 rounded-lg flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-100 text-green-800' :
          message.type === 'error' ? 'bg-red-100 text-red-800' :
          'bg-yellow-100 text-yellow-800'
        }`}>
          {message.type === 'success' && <CheckCircle className="w-4 h-4" />}
          {message.type === 'warning' && <AlertTriangle className="w-4 h-4" />}
          <span className="text-sm">{message.text}</span>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold mb-4">Create Financial Snapshot</h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Snapshot Name (Optional)</label>
              <input
                type="text"
                value={snapshotName}
                onChange={(e) => setSnapshotName(e.target.value)}
                placeholder="e.g., Q1 2024, Year End 2023"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={createSnapshot}
                disabled={isLoading}
                className="flex-1 bg-green-600 text-white py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {isLoading ? 'Creating...' : 'Create Snapshot'}
              </button>
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SnapshotButton;