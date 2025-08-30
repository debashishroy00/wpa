/**
 * WealthPath AI - Step 6: Financial Advisor Chat
 * Intelligent chat interface with LLM provider selection and vector database context
 */

import React, { useState, useEffect } from 'react';
import { 
  MessageSquare, 
  Settings, 
  BarChart3, 
  DollarSign, 
  Zap,
  Clock,
  AlertTriangle,
  RefreshCw,
  CheckCircle,
  Database
} from 'lucide-react';

import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import ChatInterface from './ChatInterface';
import SuggestedQuestions from './SuggestedQuestions';
import ContextPanel from './ContextPanel';
import LLMProviderSettings from './LLMProviderSettings';
import LLMSettingsService, { ChatSettings } from '../../services/LLMSettingsService';
import { useUnifiedAuthStore } from '../../stores/unified-auth-store';
import { getApiBaseUrl } from '../../utils/getApiBaseUrl';

interface Message {
    id: string;
    userId: number;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    context?: string;
    tokenCount: number;
    cost: number;
    model: string;
    provider: 'openai' | 'gemini' | 'claude';
    modelTier: 'dev' | 'prod';
    sessionId: string;
}

interface ChatSession {
    sessionId: string;
    userId: number;
    startTime: Date;
    messages: Message[];
    totalTokens: number;
    totalCost: number;
    status: 'active' | 'ended';
}

const FinancialAdvisorChat: React.FC = () => {
    console.log('💬 FinancialAdvisorChat component MOUNTED');
    
    let user;
    try {
        console.log('📍 About to call useAuthUser hook in Chat...');
        user = useUnifiedAuthStore((state) => state.user);
        console.log('👤 Chat user from auth store:', user);
        console.log('🔑 Chat auth token exists:', !!localStorage.getItem('auth_tokens'));
    } catch (error) {
        console.error('💥 Error calling useAuthUser in Chat:', error);
        user = null;
    }
    
    const [messages, setMessages] = useState<Message[]>([]);
    const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showProviderSettings, setShowProviderSettings] = useState(false);
    const [showContextPanel, setShowContextPanel] = useState(false);
    const [llmSettings, setLlmSettings] = useState<ChatSettings>(LLMSettingsService.getSettings());
    const [syncStatus, setSyncStatus] = useState<'synced' | 'pending' | 'syncing' | 'error'>('synced');
    const [syncInfo, setSyncInfo] = useState<{unsynced: number; total: number; dti_ratio?: number; last_sync?: string} | null>(null);
    const [syncMetrics, setSyncMetrics] = useState<any>(null);
    const [useIntelligentChat, setUseIntelligentChat] = useState(true);
    const [intelligenceMetrics, setIntelligenceMetrics] = useState<any>(null);

    // Get user ID from auth context
    const userId = user?.id;
    console.log('🆔 Chat userId extracted:', userId);

    useEffect(() => {
        // Subscribe to LLM settings changes
        const unsubscribe = LLMSettingsService.onSettingsChange((settings) => {
            setLlmSettings(settings);
        });

        // Only initialize when we have a valid user
        if (userId) {
            // Initialize chat session
            initializeChatSession();
            
            // Check sync status on load
            checkSyncStatus();
        }

        return unsubscribe;
    }, [userId]);

    const getAuthHeaders = () => {
        const authTokens = localStorage.getItem('auth_tokens');
        if (!authTokens) {
            throw new Error('Authentication token not found');
        }
        
        try {
            const tokens = JSON.parse(authTokens);
            const token = tokens.access_token;
            
            return {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            };
        } catch (error) {
            throw new Error('Invalid auth tokens format');
        }
    };

    const getBaseURL = () => {
        // Smart API URL detection
        if (import.meta.env.VITE_API_BASE_URL) {
            return import.meta.env.VITE_API_BASE_URL;
        }
        
        // Check if we're in development (localhost)
        if (window.location.hostname === 'localhost' || 
            window.location.hostname === '127.0.0.1') {
            return getApiBaseUrl();  // Use environment-aware backend
        }
        
        // Default to production backend
        return 'https://wealthpath-backend.onrender.com';
    };

    const checkSyncStatus = async () => {
        try {
            const response = await fetch(`${getBaseURL()}/api/v1/financial/sync/status`, {
                headers: getAuthHeaders()
            });
            if (response.ok) {
                const data = await response.json();
                setSyncStatus(data.needs_sync ? 'pending' : 'synced');
                setSyncInfo({
                    unsynced: data.unsynced_count,
                    total: data.total_entries
                });
            }
        } catch (error) {
            console.error('Failed to check sync status:', error);
        }
    };

    const handleManualSync = async () => {
        setSyncStatus('syncing');
        try {
            console.log('🔄 Starting complete vector database sync...');
            const response = await fetch(`${getBaseURL()}/api/v1/financial/sync/complete`, {
                method: 'POST',
                headers: getAuthHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                setSyncStatus('synced');
                setSyncMetrics(data.metrics);
                setSyncInfo({
                    unsynced: 0,
                    total: data.documents_indexed,
                    dti_ratio: data.metrics.dti_ratio,
                    last_sync: data.timestamp
                });
                
                console.log('✅ Complete sync successful:', {
                    documents_removed: data.documents_removed,
                    documents_indexed: data.documents_indexed,
                    dti_ratio: data.metrics.dti_ratio,
                    validation: data.validation
                });
                
                // Show success message with validation
                if (data.validation && data.validation.dti_found_in_vector) {
                    console.log(`✅ DTI validation: Vector DB now contains ${data.validation.vector_dti_value}% (expected: ${data.validation.expected_dti}%)`);
                }
                
                // Refresh chat context after successful sync
                // The next message will use the updated vector data
                
            } else {
                const errorData = await response.json();
                setSyncStatus('error');
                console.error('❌ Complete sync failed:', errorData);
                throw new Error(errorData.detail || 'Complete sync failed');
            }
        } catch (error) {
            console.error('❌ Complete sync error:', error);
            setSyncStatus('error');
            setSyncInfo(null);
        }
    };

    const initializeChatSession = () => {
        if (!userId) {
            console.warn('Cannot initialize chat session: user not authenticated');
            return;
        }

        const sessionId = `chat_${userId}_${Date.now()}`;
        const session: ChatSession = {
            sessionId,
            userId,
            startTime: new Date(),
            messages: [],
            totalTokens: 0,
            totalCost: 0,
            status: 'active'
        };
        
        setCurrentSession(session);
        
        // Load persisted messages
        loadPersistedMessages(sessionId);
        
        // Add welcome message
        const welcomeMessage: Message = {
            id: `msg_${Date.now()}`,
            userId,
            role: 'assistant',
            content: `Hello! I'm your AI Financial Advisor. I have access to your complete financial profile including your $2.56M net worth, investment preferences, goals, and real-time data. How can I help you today?`,
            timestamp: new Date(),
            tokenCount: 45,
            cost: 0,
            model: llmSettings.selectedModel,
            provider: llmSettings.provider,
            modelTier: llmSettings.modelTier,
            sessionId
        };
        
        setMessages([welcomeMessage]);
    };

    const loadPersistedMessages = (sessionId: string) => {
        try {
            const stored = localStorage.getItem(`chat_session_${sessionId}`);
            if (stored) {
                const session = JSON.parse(stored);
                setMessages(session.messages || []);
                setCurrentSession(session);
            }
        } catch (error) {
            console.error('Failed to load persisted messages:', error);
        }
    };

    const persistSession = (session: ChatSession) => {
        try {
            localStorage.setItem(`chat_session_${session.sessionId}`, JSON.stringify(session));
        } catch (error) {
            console.error('Failed to persist session:', error);
        }
    };

    const sendMessage = async (content: string) => {
        console.log('📨 Send message triggered');
        console.log('💬 Message content:', content);
        console.log('🔍 Debug state check:');
        console.log('  - currentSession exists:', !!currentSession);
        console.log('  - loading:', loading);
        console.log('  - userId:', userId);
        console.log('  - user object:', user);
        console.log('  - auth tokens:', localStorage.getItem('auth_tokens'));
        
        if (!currentSession || loading || !userId) {
            console.error('❌ Send message blocked!');
            console.log('🔍 Blocking reason:');
            console.log('  - No current session:', !currentSession);
            console.log('  - Currently loading:', loading);
            console.log('  - No user ID:', !userId);
            
            if (!userId) {
                console.error('💥 CRITICAL: User not authenticated in chat!');
                setError('User not authenticated - Debug: Check console for details');
            }
            return;
        }

        console.log('✅ Proceeding with message send...');
        setLoading(true);
        setError(null);

        // Create user message
        const userMessage: Message = {
            id: `msg_${Date.now()}_user`,
            userId,
            role: 'user',
            content,
            timestamp: new Date(),
            tokenCount: Math.ceil(content.length / 4), // Rough token estimation
            cost: 0,
            model: llmSettings.selectedModel,
            provider: llmSettings.provider,
            modelTier: llmSettings.modelTier,
            sessionId: currentSession.sessionId
        };

        const updatedMessages = [...messages, userMessage];
        setMessages(updatedMessages);

        try {
            // Send message to backend
            const baseUrl = getApiBaseUrl();
            const fullUrl = `${baseUrl}/api/v1/chat/message`;
            console.log('🔗 Chat API Base URL:', baseUrl);
            console.log('🌐 Full Chat URL:', fullUrl);
            
            const response = await fetch(fullUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify({
                    user_id: userId,
                    message: content,
                    session_id: currentSession.sessionId,
                    provider: llmSettings.provider,
                    model_tier: llmSettings.modelTier,
                    include_context: true,
                    insight_level: llmSettings.insightLevel || 'balanced'
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Chat API Error Details:', {
                    status: response.status,
                    statusText: response.statusText,
                    body: errorText,
                    request: {
                        user_id: userId,
                        message: content,
                        session_id: currentSession.sessionId,
                        provider: llmSettings.provider,
                        model_tier: llmSettings.modelTier
                    }
                });
                throw new Error(`Chat API error: ${response.status} - ${errorText}`);
            }

            const data = await response.json();

            // Create assistant message
            const assistantMessage: Message = {
                id: `msg_${Date.now()}_assistant`,
                userId,
                role: 'assistant',
                content: data.message.content,
                timestamp: new Date(),
                context: data.context_used,
                tokenCount: data.tokens_used?.total || 0,
                cost: data.cost_breakdown?.total || 0,
                model: llmSettings.selectedModel,
                provider: llmSettings.provider,
                modelTier: llmSettings.modelTier,
                sessionId: currentSession.sessionId
            };

            const finalMessages = [...updatedMessages, assistantMessage];
            setMessages(finalMessages);

            // Update session
            const updatedSession: ChatSession = {
                ...currentSession,
                messages: finalMessages,
                totalTokens: currentSession.totalTokens + userMessage.tokenCount + assistantMessage.tokenCount,
                totalCost: currentSession.totalCost + assistantMessage.cost
            };
            
            setCurrentSession(updatedSession);
            persistSession(updatedSession);

        } catch (error) {
            console.error('Failed to send message:', error);
            setError(error instanceof Error ? error.message : 'Failed to send message');
        } finally {
            setLoading(false);
        }
    };

    const getAuthToken = (): string => {
        const authTokens = localStorage.getItem('auth_tokens');
        if (!authTokens) {
            console.error('No auth tokens found in localStorage');
            throw new Error('No auth token');
        }
        
        try {
            const tokens = JSON.parse(authTokens);
            if (!tokens.access_token) {
                console.error('Access token missing from stored auth tokens:', tokens);
                throw new Error('Access token missing');
            }
            return tokens.access_token;
        } catch (parseError) {
            console.error('Failed to parse auth tokens:', parseError);
            throw new Error('Invalid auth token format');
        }
    };

    const handleSuggestedQuestion = (question: string) => {
        sendMessage(question);
    };

    const clearChat = () => {
        setMessages([]);
        if (currentSession) {
            localStorage.removeItem(`chat_session_${currentSession.sessionId}`);
        }
        initializeChatSession();
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            <div className="max-w-7xl mx-auto px-4 py-6">
                
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
                            <MessageSquare className="w-8 h-8 mr-3 text-blue-400" />
                            AI Financial Advisor
                        </h1>
                        <p className="text-gray-400 mb-2">
                            Personalized financial guidance powered by your real data
                        </p>
                        <div className="text-sm text-gray-500 flex items-center gap-4">
                            <div className="flex items-center gap-2">
                                <span>{LLMSettingsService.getProviderIcon(llmSettings.provider)}</span>
                                <span>Provider: {llmSettings.provider.toUpperCase()}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Zap className="w-4 h-4" />
                                <span>Model: {llmSettings.selectedModel}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <DollarSign className="w-4 h-4" />
                                <span>Cost: ${llmSettings.estimatedCostPerMessage.toFixed(3)}/msg</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <BarChart3 className="w-4 h-4" />
                                <span>Response: {llmSettings.insightLevel === 'focused' ? 'Focused' : 
                                              llmSettings.insightLevel === 'balanced' ? 'Balanced' : 'Comprehensive'}</span>
                            </div>
                            {LLMSettingsService.isCheapestOption(llmSettings.provider, llmSettings.modelTier) && (
                                <Badge variant="success" size="sm" className="bg-green-600 text-white">
                                    CHEAPEST!
                                </Badge>
                            )}
                            
                            {/* Enhanced Sync Status Indicator */}
                            <div className="flex items-center gap-2">
                                <Database className="w-4 h-4" />
                                {syncStatus === 'synced' && syncInfo && (
                                    <div className="flex items-center gap-1 text-green-400">
                                        <CheckCircle className="w-4 h-4" />
                                        <span>Synced • {syncInfo.total} docs</span>
                                        {syncInfo.dti_ratio && (
                                            <span className="text-xs">• DTI: {syncInfo.dti_ratio.toFixed(1)}%</span>
                                        )}
                                    </div>
                                )}
                                {syncStatus === 'pending' && syncInfo && (
                                    <div className="flex items-center gap-1 text-yellow-400">
                                        <RefreshCw className="w-4 h-4" />
                                        <span>{syncInfo.unsynced} updates pending</span>
                                    </div>
                                )}
                                {syncStatus === 'syncing' && (
                                    <div className="flex items-center gap-1 text-blue-400">
                                        <RefreshCw className="w-4 h-4 animate-spin" />
                                        <span>Syncing AI data...</span>
                                    </div>
                                )}
                                {syncStatus === 'error' && (
                                    <div className="flex items-center gap-1 text-red-400">
                                        <AlertTriangle className="w-4 h-4" />
                                        <span>Sync failed - click to retry</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                    
                    <div className="flex space-x-3">
                        {/* Enhanced Sync Finances Button - Always Visible */}
                        <Button
                            onClick={handleManualSync}
                            variant="outline"
                            size="sm"
                            disabled={syncStatus === 'syncing'}
                            leftIcon={
                                syncStatus === 'syncing' ? 
                                    <RefreshCw className="w-4 h-4 animate-spin" /> : 
                                    <Database className="w-4 h-4" />
                            }
                            className={`
                                ${syncStatus === 'error' ? 'border-red-500 text-red-400 hover:bg-red-500/10' : ''}
                                ${syncStatus === 'pending' ? 'border-yellow-500 text-yellow-400 hover:bg-yellow-500/10' : ''}
                                ${syncStatus === 'synced' ? 'border-green-500 text-green-400 hover:bg-green-500/10' : ''}
                                ${syncStatus === 'syncing' ? 'border-blue-500 text-blue-400 cursor-not-allowed' : ''}
                            `}
                        >
                            {syncStatus === 'syncing' ? 'Syncing...' : 'Sync Finances'}
                        </Button>
                        
                        <Button
                            onClick={() => setShowProviderSettings(!showProviderSettings)}
                            variant="outline"
                            size="sm"
                            leftIcon={<Settings className="w-4 h-4" />}
                        >
                            LLM Settings
                        </Button>
                        
                        <Button
                            onClick={() => setShowContextPanel(!showContextPanel)}
                            variant="outline"
                            size="sm"
                            leftIcon={<BarChart3 className="w-4 h-4" />}
                        >
                            Context & Usage
                        </Button>
                        
                        <Button
                            onClick={clearChat}
                            variant="outline"
                            size="sm"
                            className="text-red-400 border-red-500/50 hover:bg-red-900/20"
                        >
                            Clear Chat
                        </Button>
                    </div>
                </div>

                {/* Error Display */}
                {error && (
                    <Card className="bg-red-900/20 border-red-500/50 mb-6">
                        <Card.Body className="p-4">
                            <div className="flex items-center space-x-2">
                                <AlertTriangle className="w-5 h-5 text-red-400" />
                                <span className="text-red-400 font-medium">Error</span>
                            </div>
                            <p className="text-red-300 mt-2">{error}</p>
                        </Card.Body>
                    </Card>
                )}

                {/* LLM Provider Settings */}
                {showProviderSettings && (
                    <div className="mb-6">
                        <LLMProviderSettings />
                    </div>
                )}

                {/* Context Panel */}
                {showContextPanel && currentSession && (
                    <div className="mb-6">
                        <ContextPanel session={currentSession} />
                    </div>
                )}

                {/* Main Chat Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    
                    {/* Chat Interface - Main Area */}
                    <div className="lg:col-span-3">
                        <ChatInterface
                            messages={messages}
                            loading={loading}
                            onSendMessage={sendMessage}
                        />
                    </div>
                    
                    {/* Suggested Questions - Sidebar */}
                    <div className="lg:col-span-1">
                        <SuggestedQuestions
                            onQuestionClick={handleSuggestedQuestion}
                            disabled={loading}
                        />
                    </div>
                </div>

                {/* Session Stats */}
                {currentSession && (
                    <Card className="mt-6 bg-gray-800/50 border-gray-700">
                        <Card.Body className="p-4">
                            <div className="flex items-center justify-between text-sm text-gray-400">
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center gap-2">
                                        <Clock className="w-4 h-4" />
                                        <span>Session: {new Date(currentSession.startTime).toLocaleTimeString()}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <MessageSquare className="w-4 h-4" />
                                        <span>{messages.length} messages</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <BarChart3 className="w-4 h-4" />
                                        <span>{currentSession.totalTokens} tokens</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <DollarSign className="w-4 h-4" />
                                        <span>${currentSession.totalCost.toFixed(4)} total cost</span>
                                    </div>
                                </div>
                                <div className="text-xs opacity-60">
                                    Session ID: {currentSession.sessionId}
                                </div>
                            </div>
                        </Card.Body>
                    </Card>
                )}

                {/* Compliance Disclaimer */}
                <Card className="mt-4 bg-yellow-900/20 border-yellow-500/30">
                    <Card.Body className="p-4">
                        <div className="flex items-start space-x-3">
                            <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
                            <div className="text-sm text-yellow-300">
                                <p className="font-medium mb-1">Important Disclaimer</p>
                                <p className="opacity-90">
                                    This AI advisor provides general financial information based on your data. 
                                    This is not personalized investment advice. Please consult with a qualified 
                                    financial professional before making investment decisions. Past performance 
                                    does not guarantee future results.
                                </p>
                            </div>
                        </div>
                    </Card.Body>
                </Card>

            </div>
        </div>
    );
};

export default FinancialAdvisorChat;