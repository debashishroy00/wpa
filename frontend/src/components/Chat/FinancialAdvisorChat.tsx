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
// Replaced legacy suggested list with Question Sets panel
import ContextPanel from './ContextPanel';
import LLMProviderSettings from './LLMProviderSettings';
import LLMSettingsService, { ChatSettings } from '../../services/LLMSettingsService';
import { useUnifiedAuthStore } from '../../stores/unified-auth-store';
import { getApiBaseUrl } from '../../utils/getApiBaseUrl';
import { adaptNewChatResponse, shouldUseNewEndpoint } from '../../utils/chatAdapter';

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
    confidence?: string;
    assumptions?: string[];
    warnings?: string[];
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

        // Get or create persistent session ID
        const getOrCreateSessionId = () => {
            const storageKey = `wpa_session_${userId}`;
            let sessionId = localStorage.getItem(storageKey);
            
            if (!sessionId) {
                // Generate persistent session ID that doesn't change
                sessionId = `chat_${userId}_persistent`;
                localStorage.setItem(storageKey, sessionId);
                console.log('✨ Created new persistent session ID:', sessionId);
            } else {
                console.log('♻️ Using existing persistent session ID:', sessionId);
            }
            
            return sessionId;
        };

        const sessionId = getOrCreateSessionId();
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
        
        // Start with empty messages - no welcome message
        setMessages([]);
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
            // Check if we should use the new endpoint
            const useNewChat = shouldUseNewEndpoint();
            
            // Send message to backend - select endpoint based on feature flags
            const baseUrl = getApiBaseUrl();
            const endpoint = useNewChat 
                ? '/api/v1/chat-simple/message'
                : (useIntelligentChat ? '/api/v1/chat/intelligent' : '/api/v1/chat/message');
            const fullUrl = `${baseUrl}${endpoint}`;
            console.log('🔗 Chat API Base URL:', baseUrl);
            console.log('🌐 Full Chat URL:', fullUrl);
            console.log('🆕 Using new chat endpoint:', useNewChat);
            console.log('🧠 Using intelligent chat:', useIntelligentChat);
            
            const requestBody = useNewChat ? {
                message: content,
                session_id: currentSession?.sessionId,
                provider: llmSettings.provider,
                model_tier: llmSettings.modelTier,
                insight_level: llmSettings.insightLevel || 'balanced'
            } : (useIntelligentChat ? {
                message: content,
                session_id: currentSession.sessionId,
                provider: llmSettings.provider,
                model_tier: llmSettings.modelTier,
                insight_level: llmSettings.insightLevel || 'balanced'
            } : {
                user_id: userId,
                message: content,
                session_id: currentSession.sessionId,
                provider: llmSettings.provider,
                model_tier: llmSettings.modelTier,
                include_context: true,
                insight_level: llmSettings.insightLevel || 'balanced'
            });
            
            const response = await fetch(fullUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify(requestBody)
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
            
            // Adapt response format if using new endpoint
            const responseData = useNewChat ? adaptNewChatResponse(data) : data;

            // Store intelligence metrics if available
            if (useIntelligentChat && responseData.intelligence_metrics) {
                setIntelligenceMetrics(responseData.intelligence_metrics);
                console.log('🧠 Intelligence metrics:', responseData.intelligence_metrics);
            }

            // If Precision Gate fired, render a friendly clarifier message
            let contentToRender = responseData.message.content;
            if (useNewChat && responseData.is_clarify && responseData.clarify) {
                const card = responseData.clarify;
                const opts = (card.options || []).map((o: any, idx: number) => `${idx + 1}. ${o.label}`).join('\n');
                const fallbacks = (card.fallbacks || []).map((o: any) => `• ${o.label}`).join('\n');
                const assumptions = (card.assumptions_if_skipped || []).map((a: string) => `• ${a}`).join('\n');
                const example = (card.options && card.options.length > 0) ? card.options[0].label : 'an option above';
                contentToRender = `🧭 ${card.message}\n\nOptions:\n${opts}${fallbacks ? `\n\nAlso:\n${fallbacks}` : ''}${assumptions ? `\n\nIf you say "Use defaults", I'll assume:\n${assumptions}` : ''}\n\nReply with one option (e.g., "${example}") or choose "Use defaults".`;
            }

            // Create assistant message
            const assistantMessage: Message = {
                id: `msg_${Date.now()}_assistant`,
                userId,
                role: 'assistant',
                content: contentToRender,
                timestamp: new Date(),
                context: (useNewChat && responseData.is_clarify) ? undefined : responseData.context_used,
                tokenCount: responseData.tokens_used?.total || 0,
                cost: responseData.cost_breakdown?.total || 0,
                model: llmSettings.selectedModel,
                provider: llmSettings.provider,
                modelTier: llmSettings.modelTier,
                sessionId: responseData.session_id || currentSession.sessionId,
                confidence: responseData.confidence,
                assumptions: responseData.assumptions,
                warnings: responseData.warnings
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
        <div className="w-full text-white">
            <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-6 py-2">
                {/* Compact Header */}
                <div className="flex items-center justify-between mb-4">
                    <div className="text-xs sm:text-sm text-gray-500 flex flex-wrap items-center gap-2 sm:gap-4">
                        {/* Simplified LLM Info */}
                        <div className="flex items-center gap-2">
                            <span>{LLMSettingsService.getProviderIcon(llmSettings.provider)}</span>
                            <span>AI: {llmSettings.provider.toUpperCase()}</span>
                        </div>
                        
                        {/* Cost Display (kept for transparency) */}
                        <div className="flex items-center gap-2">
                            <DollarSign className="w-4 h-4" />
                            <span>Cost: ${llmSettings.estimatedCostPerMessage.toFixed(3)}/msg</span>
                        </div>
                        
                        {/* Intelligence Metrics Display */}
                        {useIntelligentChat && intelligenceMetrics && (
                            <div className="flex items-center gap-2 text-purple-400">
                                <span>🧠</span>
                                <span>AI Memory: {intelligenceMetrics.insights_extracted} insights captured</span>
                            </div>
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
                    
                    {/* Reorganized Button Layout - Mobile-first responsive */}
                    <div className="space-y-3">
                        {/* Top row - Core functions - Stack on mobile, row on larger screens */}
                        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                            {/* Enhanced Sync Finances Button */}
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
                                📊 {syncStatus === 'syncing' ? 'Syncing...' : 'Sync Finances'}
                            </Button>
                            
                            <Button
                                onClick={() => setShowProviderSettings(!showProviderSettings)}
                                variant="outline"
                                size="sm"
                                leftIcon={<Zap className="w-4 h-4" />}
                                className={`text-xs ${showProviderSettings ? 'ring-2 ring-orange-400' : ''}`}
                            >
                                ⚙️ LLM Settings
                            </Button>
                            
                            <Button
                                onClick={() => setShowContextPanel(!showContextPanel)}
                                variant="outline"
                                size="sm"
                                leftIcon={<BarChart3 className="w-4 h-4" />}
                            >
                                📋 Context & Usage
                            </Button>
                        </div>

                        {/* Bottom row - Memory and actions */}
                        <div className="flex justify-between items-center">
                            {/* AI Memory Button - Enhanced with insight count */}
                            <Button
                                onClick={() => setUseIntelligentChat(!useIntelligentChat)}
                                variant={useIntelligentChat ? "primary" : "outline"}
                                size="sm"
                                leftIcon={<span>🧠</span>}
                                className={`
                                    ${useIntelligentChat 
                                        ? 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white border-none' 
                                        : 'border-purple-500 text-purple-400 hover:bg-purple-500/10'
                                    }
                                `}
                            >
                                AI Memory: {useIntelligentChat 
                                    ? `On${intelligenceMetrics?.insights_extracted ? ` (${intelligenceMetrics.insights_extracted} insights)` : ''}`
                                    : 'Off'
                                }
                            </Button>
                            
                            <Button
                                onClick={clearChat}
                                variant="outline"
                                size="sm"
                                className="text-red-400 border-red-500/50 hover:bg-red-900/20"
                            >
                                🗑️ Clear Chat
                            </Button>
                        </div>
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

                {/* Legacy LLM Provider Settings (for advanced users) */}
                {showProviderSettings && (
                    <div className="mb-6">
                        <Card className="bg-gray-800/50 border-gray-700">
                            <Card.Header className="border-b border-gray-700 pb-3">
                                <h3 className="text-lg font-medium text-white">Advanced Technical Settings</h3>
                                <p className="text-sm text-gray-400">For developers and advanced users only</p>
                            </Card.Header>
                            <Card.Body className="p-4">
                                <LLMProviderSettings />
                            </Card.Body>
                        </Card>
                    </div>
                )}

                {/* Context Panel */}
                {showContextPanel && currentSession && (
                    <div className="mb-6">
                        <ContextPanel session={currentSession} />
                    </div>
                )}

                
                {/* Main Chat Layout - Mobile-first responsive */}
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 lg:gap-6">
                    
                    {/* Chat Interface - Main Area - Full width on mobile, 3/4 on desktop */}
                    <div className="lg:col-span-3 order-1">
                        <ChatInterface
                            messages={messages}
                            loading={loading}
                            onSendMessage={sendMessage}
                        />
                    </div>
                    
                    {/* Suggested Questions - Sidebar - Show above chat on mobile, side on desktop */}
                    <div className="lg:col-span-1 order-0 lg:order-1">
                        <SuggestedQuestions
                            onQuestionClick={sendMessage}
                            disabled={loading}
                        />
                    </div>
                </div>

                {/* Session Stats */}
                {currentSession && (
                    <Card className="mt-6 bg-gray-800/50 border-gray-700">
                        <Card.Body className="p-4">
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-xs sm:text-sm text-gray-400 gap-3">
                                <div className="flex flex-wrap items-center gap-2 sm:gap-4">
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
                                <div className="text-xs opacity-60 truncate">
                                    ID: {currentSession.sessionId.substring(0, 8)}...
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
