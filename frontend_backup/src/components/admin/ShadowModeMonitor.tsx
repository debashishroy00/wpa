/**
 * Shadow Mode Testing Monitor Component
 * Provides interface for testing and monitoring shadow mode functionality
 */

import React, { useState, useEffect } from 'react';
import { getApiBaseUrl } from '../../utils/getApiBaseUrl';

interface ShadowTestResult {
  id: string;
  timestamp: string;
  query: string;
  normalResponse: string;
  shadowResponse: string;
  match: boolean;
  responseTime: number;
}

const ShadowModeMonitor: React.FC = () => {
  const [shadowModeEnabled, setShadowModeEnabled] = useState(false);
  const [testResults, setTestResults] = useState<ShadowTestResult[]>([]);
  const [vectorDbStatus, setVectorDbStatus] = useState<{
    documents: number;
    status: string;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Check vector database status
  const checkVectorDbStatus = async () => {
    try {
      const token = localStorage.getItem('access_token');
      console.log('🔍 Checking vector DB status with token:', token ? 'Present' : 'Missing');
      
      if (token) {
        // Try authenticated endpoint if token exists
        const response = await fetch(`${getApiBaseUrl()}/api/v1/vector/status/1`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        console.log('📊 Vector DB status response:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('📊 Vector DB data:', data);
          setVectorDbStatus({
            documents: data.total_documents || 0,
            status: data.total_documents >= 40 ? 'Ready (Authenticated)' : 'Insufficient Data'
          });
          return;
        }
      }
      
      // Fallback to debug endpoint (no authentication required)
      console.log('🔄 Trying debug endpoint...');
      const debugResponse = await fetch(`${getApiBaseUrl()}/api/v1/vector/debug-status`);
      
      if (debugResponse.ok) {
        const data = await debugResponse.json();
        console.log('📊 Debug endpoint data:', data);
        setVectorDbStatus({
          documents: data.total_documents || 0,
          status: data.total_documents >= 40 ? 'Ready (Debug Mode)' : 'Insufficient Data'
        });
      } else {
        setVectorDbStatus({
          documents: 0,
          status: 'Connection Error'
        });
      }
    } catch (error) {
      console.error('Failed to check vector DB status:', error);
      setVectorDbStatus({
        documents: 0,
        status: 'Connection Error'
      });
    }
  };

  // Run shadow mode test
  const runShadowTest = async () => {
    setIsLoading(true);
    const testQuery = "What's my current financial health?";
    
    try {
      // Simulate shadow mode test
      const startTime = Date.now();
      
      // In a real implementation, this would call both normal and shadow endpoints
      const mockResult: ShadowTestResult = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        query: testQuery,
        normalResponse: "Your financial health is excellent with a net worth of $2.5M...",
        shadowResponse: "Your financial health is excellent with a net worth of $2.5M...",
        match: true,
        responseTime: Date.now() - startTime
      };
      
      setTestResults(prev => [mockResult, ...prev.slice(0, 4)]); // Keep last 5 results
    } catch (error) {
      console.error('Shadow test failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkVectorDbStatus();
    const interval = setInterval(checkVectorDbStatus, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold" style={{ color: '#ffffff' }}>Shadow Mode Testing</h2>
        <p className="text-sm" style={{ color: '#a0a0a0' }}>
          Monitor and test shadow mode functionality for LLM responses
        </p>
      </div>

      {/* Vector Database Status */}
      <div className="p-4 rounded-lg" style={{ backgroundColor: '#1a1a1a', border: '1px solid #404040' }}>
        <h3 className="text-lg font-medium mb-3" style={{ color: '#ffffff' }}>Vector Database Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-3 rounded-lg" style={{ backgroundColor: '#2a2a2a' }}>
            <div className="text-2xl font-bold" style={{ color: '#10b981' }}>
              {vectorDbStatus?.documents || 0}
            </div>
            <div className="text-sm" style={{ color: '#a0a0a0' }}>Documents</div>
          </div>
          <div className="text-center p-3 rounded-lg" style={{ backgroundColor: '#2a2a2a' }}>
            <div className={`text-2xl ${vectorDbStatus?.status === 'Ready' ? 'text-green-400' : 'text-yellow-400'}`}>
              {vectorDbStatus?.status === 'Ready' ? '✅' : '⚠️'}
            </div>
            <div className="text-sm" style={{ color: '#a0a0a0' }}>Status</div>
          </div>
          <div className="text-center p-3 rounded-lg" style={{ backgroundColor: '#2a2a2a' }}>
            <div className="text-2xl" style={{ color: '#60a5fa' }}>
              {shadowModeEnabled ? '🟢' : '🔴'}
            </div>
            <div className="text-sm" style={{ color: '#a0a0a0' }}>Shadow Mode</div>
          </div>
        </div>
      </div>

      {/* Shadow Mode Controls */}
      <div className="p-4 rounded-lg" style={{ backgroundColor: '#1a1a1a', border: '1px solid #404040' }}>
        <h3 className="text-lg font-medium mb-3" style={{ color: '#ffffff' }}>Controls</h3>
        <div className="flex items-center justify-between mb-4">
          <div>
            <label className="text-sm font-medium" style={{ color: '#ffffff' }}>
              Enable Shadow Mode Testing
            </label>
            <p className="text-xs" style={{ color: '#a0a0a0' }}>
              Run parallel LLM queries for comparison testing
            </p>
          </div>
          <button
            onClick={() => setShadowModeEnabled(!shadowModeEnabled)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              shadowModeEnabled ? 'bg-blue-600' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                shadowModeEnabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={runShadowTest}
            disabled={!shadowModeEnabled || isLoading}
            className="px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ 
              backgroundColor: shadowModeEnabled ? '#3b82f6' : '#666666',
              color: '#ffffff'
            }}
          >
            {isLoading ? '🔄 Running Test...' : '▶️ Run Shadow Test'}
          </button>
          
          <button
            onClick={checkVectorDbStatus}
            className="px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: '#059669', color: '#ffffff' }}
          >
            🔄 Refresh Status
          </button>
          
          <button
            onClick={() => {
              console.log('🐛 DEBUG: Token in localStorage:', localStorage.getItem('access_token') ? 'EXISTS' : 'MISSING');
              console.log('🐛 DEBUG: Full token:', localStorage.getItem('access_token'));
              checkVectorDbStatus();
            }}
            className="px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: '#dc2626', color: '#ffffff' }}
          >
            🐛 Debug
          </button>
          
          <button
            onClick={async () => {
              try {
                console.log('🧪 Testing backend directly...');
                const response = await fetch(`${getApiBaseUrl()}/api/v1/vector/debug-status`);
                console.log('🧪 Debug endpoint response:', response.status);
                if (response.ok) {
                  const data = await response.json();
                  console.log('🧪 Debug data:', data);
                  setVectorDbStatus({
                    documents: data.total_documents || 0,
                    status: data.total_documents >= 40 ? 'Ready' : 'Insufficient Data'
                  });
                } else {
                  console.log('🧪 Debug endpoint failed:', await response.text());
                }
              } catch (error) {
                console.error('🧪 Debug test failed:', error);
              }
            }}
            className="px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: '#f59e0b', color: '#ffffff' }}
          >
            🧪 Test Backend
          </button>
        </div>
      </div>

      {/* Test Results */}
      <div className="p-4 rounded-lg" style={{ backgroundColor: '#1a1a1a', border: '1px solid #404040' }}>
        <h3 className="text-lg font-medium mb-3" style={{ color: '#ffffff' }}>Recent Test Results</h3>
        
        {testResults.length === 0 ? (
          <div className="text-center py-8" style={{ color: '#a0a0a0' }}>
            <div className="text-4xl mb-2">🧪</div>
            <p>No test results yet. Run a shadow test to begin monitoring.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {testResults.map((result) => (
              <div
                key={result.id}
                className="p-3 rounded-lg"
                style={{ backgroundColor: '#2a2a2a', border: '1px solid #404040' }}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={result.match ? 'text-green-400' : 'text-red-400'}>
                      {result.match ? '✅' : '❌'}
                    </span>
                    <span className="text-sm font-medium" style={{ color: '#ffffff' }}>
                      {result.match ? 'Responses Match' : 'Responses Differ'}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-xs" style={{ color: '#a0a0a0' }}>
                      {result.responseTime}ms
                    </span>
                    <span className="text-xs" style={{ color: '#a0a0a0' }}>
                      {new Date(result.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
                
                <div className="text-sm mb-2" style={{ color: '#a0a0a0' }}>
                  <strong>Query:</strong> {result.query}
                </div>
                
                {!result.match && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
                    <div>
                      <div className="text-xs font-medium mb-1" style={{ color: '#ffffff' }}>Normal Response:</div>
                      <div className="text-xs p-2 rounded" style={{ backgroundColor: '#1a1a1a', color: '#a0a0a0' }}>
                        {result.normalResponse.substring(0, 100)}...
                      </div>
                    </div>
                    <div>
                      <div className="text-xs font-medium mb-1" style={{ color: '#ffffff' }}>Shadow Response:</div>
                      <div className="text-xs p-2 rounded" style={{ backgroundColor: '#1a1a1a', color: '#a0a0a0' }}>
                        {result.shadowResponse.substring(0, 100)}...
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ShadowModeMonitor;