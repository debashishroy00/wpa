/**
 * WealthPath AI - Step 7: Debug View
 * Direct visibility into vector database contents and LLM payloads
 */

import React, { useState, useEffect } from 'react';
import { 
  Database, 
  MessageSquare, 
  RefreshCw, 
  Eye, 
  Search,
  AlertTriangle,
  CheckCircle,
  Info
} from 'lucide-react';

import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { useUnifiedAuthStore } from '../../stores/unified-auth-store';

interface VectorDocument {
  id: string;
  content: string;
  metadata: any;
}

interface VectorContents {
  status: string;
  user_id: number;
  total_documents: number;
  last_updated: string;
  documents: VectorDocument[];
  debug_info: any;
}

interface LLMPayload {
  status: string;
  user_id: number;
  query: string;
  timestamp: string;
  provider: string;
  system_prompt: string;
  user_message: string;
  context_used: string;
  analysis: {
    has_goals: boolean;
    has_dti: boolean;
    has_interest_rates: boolean;
    dti_value?: string;
    system_prompt_size: number;
    user_message_size: number;
    total_size: number;
  };
}

const DebugView: React.FC = () => {
  const [vectorData, setVectorData] = useState<VectorContents | null>(null);
  const [llmPayload, setLlmPayload] = useState<LLMPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const user = useUnifiedAuthStore((state) => state.user);
  const userId = user?.id || 0;

  const fetchVectorContents = async () => {
    try {
      const authTokens = localStorage.getItem('auth_tokens');
      const token = authTokens ? JSON.parse(authTokens).access_token : null;
      
      if (!token) {
        throw new Error('No authentication token found. Please log in.');
      }
      
      if (!userId || userId === 0) {
        throw new Error('User not authenticated. Please log in.');
      }
      
      console.log('🔍 Fetching vector contents for user:', userId);
      
      const response = await fetch(`/api/v1/debug/vector-contents/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setVectorData(data);
      } else {
        throw new Error(`Failed to fetch vector contents: ${response.status}`);
      }
    } catch (err) {
      setError(`Vector DB Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const fetchLLMPayload = async () => {
    try {
      const authTokens = localStorage.getItem('auth_tokens');
      const token = authTokens ? JSON.parse(authTokens).access_token : null;
      
      if (!token) {
        throw new Error('No authentication token found. Please log in.');
      }
      
      if (!userId || userId === 0) {
        throw new Error('User not authenticated. Please log in.');
      }
      
      console.log('🔍 Fetching LLM payload for user:', userId);
      
      const response = await fetch(`/api/v1/debug/last-llm-payload/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setLlmPayload(data);
      } else {
        throw new Error(`Failed to fetch LLM payload: ${response.status}`);
      }
    } catch (err) {
      setError(`LLM Payload Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const triggerVectorSync = async () => {
    setSyncLoading(true);
    setError(null);
    
    try {
      const authTokens = localStorage.getItem('auth_tokens');
      const token = authTokens ? JSON.parse(authTokens).access_token : null;
      
      if (!token) {
        throw new Error('No authentication token found. Please log in.');
      }
      
      if (!userId || userId === 0) {
        throw new Error('User not authenticated. Please log in.');
      }
      
      console.log('🔄 Triggering vector sync for user:', userId);
      
      const response = await fetch(`/api/v1/debug/trigger-vector-sync/${userId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        setSyncResult(result);
        console.log('✅ Vector sync completed:', result);
        
        // Refresh vector contents after successful sync
        await fetchVectorContents();
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(`Sync failed: ${errorData.detail || response.status}`);
      }
    } catch (err) {
      setError(`Vector Sync Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSyncLoading(false);
    }
  };

  const refreshAll = async () => {
    setLoading(true);
    setError(null);
    
    await Promise.all([
      fetchVectorContents(),
      fetchLLMPayload()
    ]);
    
    setLoading(false);
  };

  useEffect(() => {
    // Only fetch data when we have a valid user ID
    if (userId && userId !== 0) {
      refreshAll();
    }
  }, [userId]);

  const filteredDocuments = vectorData?.documents?.filter(doc => 
    searchTerm === '' || 
    doc.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.id.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
              <Eye className="w-8 h-8 mr-3 text-blue-400" />
              Debug View - Raw Data Visibility
            </h1>
            <p className="text-gray-400">
              Direct view into vector database contents and LLM payloads - no more guessing!
              {user && <span className="ml-2 text-green-400">(User ID: {userId})</span>}
            </p>
          </div>
          
          <div className="flex gap-2">
            <Button
              onClick={triggerVectorSync}
              disabled={syncLoading || !userId || userId === 0}
              leftIcon={syncLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
              className="bg-green-600 hover:bg-green-700"
            >
              {syncLoading ? 'Syncing...' : 'Sync Vector DB'}
            </Button>
            
            <Button
              onClick={refreshAll}
              disabled={loading || !userId || userId === 0}
              leftIcon={loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {loading ? 'Refreshing...' : 'Refresh All'}
            </Button>
          </div>
        </div>

        {error && (
          <Card className="mb-6 bg-red-900/30 border-red-500">
            <div className="flex items-center gap-2 text-red-400">
              <AlertTriangle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </Card>
        )}

        {(!userId || userId === 0) && (
          <Card className="mb-6 bg-yellow-900/30 border-yellow-500">
            <div className="flex items-center gap-2 text-yellow-400">
              <AlertTriangle className="w-5 h-5" />
              <span>User not authenticated. Please log in to view debug data.</span>
            </div>
          </Card>
        )}

        {syncResult && (
          <Card className="mb-6 bg-green-900/30 border-green-500">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle className="w-5 h-5" />
                <span className="font-medium">Vector Sync Completed Successfully</span>
              </div>
              <Button
                onClick={() => setSyncResult(null)}
                className="text-gray-400 hover:text-white text-sm"
                variant="ghost"
              >
                ✕
              </Button>
            </div>
            <div className="text-sm text-gray-300">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-400">Documents Before:</span>
                  <span className="ml-2 font-mono">{syncResult.pre_sync_stats?.user_docs || 0}</span>
                </div>
                <div>
                  <span className="text-gray-400">Documents After:</span>
                  <span className="ml-2 font-mono">{syncResult.post_sync_stats?.user_docs || 0}</span>
                </div>
                <div>
                  <span className="text-gray-400">Documents Added:</span>
                  <span className="ml-2 font-mono text-green-400">+{syncResult.documents_added || 0}</span>
                </div>
                <div>
                  <span className="text-gray-400">Sync Time:</span>
                  <span className="ml-2 font-mono text-xs">{formatTimestamp(syncResult.timestamp)}</span>
                </div>
              </div>
            </div>
          </Card>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Vector Database Contents Panel */}
          <Card className="bg-gray-800 border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center">
                <Database className="w-6 h-6 mr-2 text-green-400" />
                Vector Database Contents
              </h2>
              {vectorData && (
                <Badge variant="outline" className="text-green-400 border-green-400">
                  {vectorData.total_documents} docs
                </Badge>
              )}
            </div>

            {vectorData ? (
              <div className="space-y-4">
                {/* Summary */}
                <div className="bg-gray-700 p-3 rounded">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Total Documents:</span>
                      <span className="ml-2 font-mono">{vectorData.total_documents}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Last Updated:</span>
                      <span className="ml-2 font-mono text-xs">{formatTimestamp(vectorData.last_updated)}</span>
                    </div>
                    {vectorData.debug_info && (
                      <>
                        <div>
                          <span className="text-gray-400">Storage File:</span>
                          <span className={`ml-2 font-mono text-xs ${vectorData.debug_info.storage_file_exists ? 'text-green-400' : 'text-red-400'}`}>
                            {vectorData.debug_info.storage_file_exists ? '✓ Exists' : '✗ Missing'}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-400">Store Total:</span>
                          <span className="ml-2 font-mono">{vectorData.debug_info.total_docs_in_store || 0}</span>
                        </div>
                      </>
                    )}
                  </div>
                  {vectorData.debug_info?.storage_path && (
                    <div className="mt-2 text-xs text-gray-400">
                      <span>Path: </span>
                      <code className="bg-gray-800 px-1 rounded">{vectorData.debug_info.storage_path}</code>
                    </div>
                  )}
                </div>

                {/* Search */}
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search documents..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Documents */}
                <div className="max-h-96 overflow-y-auto space-y-2">
                  {filteredDocuments.map((doc, index) => (
                    <details key={doc.id} className="bg-gray-700 rounded">
                      <summary className="p-3 cursor-pointer hover:bg-gray-600 rounded flex items-center justify-between">
                        <span className="font-mono text-sm text-blue-400">{doc.id}</span>
                        <span className="text-xs text-gray-400">
                          {doc.content.substring(0, 50)}...
                        </span>
                      </summary>
                      <div className="px-3 pb-3">
                        <div className="mb-2">
                          <span className="text-xs text-gray-400">Content:</span>
                          <pre className="text-xs bg-gray-800 p-2 rounded mt-1 whitespace-pre-wrap break-words">
                            {doc.content}
                          </pre>
                        </div>
                        <div>
                          <span className="text-xs text-gray-400">Metadata:</span>
                          <pre className="text-xs bg-gray-800 p-2 rounded mt-1">
                            {JSON.stringify(doc.metadata, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </details>
                  ))}
                </div>

                {searchTerm && filteredDocuments.length === 0 && (
                  <div className="text-center text-gray-400 py-4">
                    No documents match "{searchTerm}"
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-400 py-8">
                <Database className="w-12 h-12 mx-auto mb-2 opacity-50" />
                {loading ? 'Loading vector contents...' : 'No vector data loaded'}
              </div>
            )}
          </Card>

          {/* LLM Payload Panel */}
          <Card className="bg-gray-800 border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center">
                <MessageSquare className="w-6 h-6 mr-2 text-purple-400" />
                Last LLM Payload
              </h2>
              {llmPayload?.analysis && (
                <div className="flex gap-2">
                  {llmPayload.analysis.has_goals ? (
                    <Badge variant="outline" className="text-green-400 border-green-400">Goals ✓</Badge>
                  ) : (
                    <Badge variant="outline" className="text-red-400 border-red-400">No Goals</Badge>
                  )}
                  {llmPayload.analysis.has_dti ? (
                    <Badge variant="outline" className="text-green-400 border-green-400">DTI ✓</Badge>
                  ) : (
                    <Badge variant="outline" className="text-red-400 border-red-400">No DTI</Badge>
                  )}
                </div>
              )}
            </div>

            {llmPayload ? (
              llmPayload.status === 'no_data' ? (
                <div className="text-center text-gray-400 py-8">
                  <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No LLM payload stored yet</p>
                  <p className="text-sm">Send a chat message in Step 6 first</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Summary */}
                  <div className="bg-gray-700 p-3 rounded">
                    <div className="grid grid-cols-1 gap-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Query:</span>
                        <span className="font-mono text-blue-400">{llmPayload.query}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Provider:</span>
                        <span className="font-mono">{llmPayload.provider}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Timestamp:</span>
                        <span className="font-mono text-xs">{formatTimestamp(llmPayload.timestamp)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Total Size:</span>
                        <span className="font-mono">{llmPayload.analysis.total_size} chars</span>
                      </div>
                    </div>
                  </div>

                  {/* Analysis */}
                  {llmPayload.analysis && (
                    <div className="bg-gray-700 p-3 rounded">
                      <h3 className="text-sm font-bold mb-2 text-yellow-400">Content Analysis</h3>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="flex items-center gap-2">
                          {llmPayload.analysis.has_goals ? 
                            <CheckCircle className="w-4 h-4 text-green-400" /> : 
                            <AlertTriangle className="w-4 h-4 text-red-400" />
                          }
                          <span>Retirement Goals</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {llmPayload.analysis.has_dti ? 
                            <CheckCircle className="w-4 h-4 text-green-400" /> : 
                            <AlertTriangle className="w-4 h-4 text-red-400" />
                          }
                          <span>DTI Ratio {llmPayload.analysis.dti_value && `(${llmPayload.analysis.dti_value})`}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {llmPayload.analysis.has_interest_rates ? 
                            <CheckCircle className="w-4 h-4 text-green-400" /> : 
                            <AlertTriangle className="w-4 h-4 text-red-400" />
                          }
                          <span>Interest Rates</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Payload Details */}
                  <div className="space-y-3">
                    <details className="bg-gray-700 rounded">
                      <summary className="p-3 cursor-pointer hover:bg-gray-600 rounded flex items-center justify-between">
                        <span className="font-medium">System Prompt</span>
                        <span className="text-xs text-gray-400">{llmPayload.analysis.system_prompt_size} chars</span>
                      </summary>
                      <div className="px-3 pb-3">
                        <pre className="text-xs bg-gray-800 p-2 rounded whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                          {llmPayload.system_prompt}
                        </pre>
                      </div>
                    </details>

                    <details className="bg-gray-700 rounded">
                      <summary className="p-3 cursor-pointer hover:bg-gray-600 rounded flex items-center justify-between">
                        <span className="font-medium">User Message</span>
                        <span className="text-xs text-gray-400">{llmPayload.analysis.user_message_size} chars</span>
                      </summary>
                      <div className="px-3 pb-3">
                        <pre className="text-xs bg-gray-800 p-2 rounded whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                          {llmPayload.user_message}
                        </pre>
                      </div>
                    </details>
                  </div>
                </div>
              )
            ) : (
              <div className="text-center text-gray-400 py-8">
                <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
                {loading ? 'Loading LLM payload...' : 'No LLM payload loaded'}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DebugView;