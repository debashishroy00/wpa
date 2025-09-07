/**
 * WealthPath AI - Context Panel Component
 * Displays token usage, cost tracking, and context information
 */

import React, { useState } from 'react';
import { 
    BarChart3, 
    DollarSign, 
    Clock, 
    Database, 
    ChevronDown, 
    ChevronUp,
    Zap,
    MessageSquare
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

interface ChatSession {
    sessionId: string;
    userId: number;
    startTime: Date;
    messages: Array<{
        id: string;
        role: 'user' | 'assistant' | 'system';
        tokenCount: number;
        cost: number;
        provider: string;
        model: string;
        timestamp: Date;
        context?: string;
    }>;
    totalTokens: number;
    totalCost: number;
    status: 'active' | 'ended';
}

interface ContextPanelProps {
    session: ChatSession;
}

const ContextPanel: React.FC<ContextPanelProps> = ({ session }) => {
    const [showContextDetails, setShowContextDetails] = useState(false);
    const [showMessageBreakdown, setShowMessageBreakdown] = useState(false);

    const calculateProviderBreakdown = () => {
        const breakdown: Record<string, { messages: number; cost: number; tokens: number }> = {};
        
        session.messages.forEach(message => {
            if (message.role === 'assistant') {
                if (!breakdown[message.provider]) {
                    breakdown[message.provider] = { messages: 0, cost: 0, tokens: 0 };
                }
                breakdown[message.provider].messages++;
                breakdown[message.provider].cost += message.cost;
                breakdown[message.provider].tokens += message.tokenCount;
            }
        });
        
        return breakdown;
    };

    const getContextSummary = () => {
        const messagesWithContext = session.messages.filter(m => m.context);
        const totalContextLength = messagesWithContext.reduce(
            (sum, m) => sum + (m.context?.length || 0), 
            0
        );
        
        return {
            messagesWithContext: messagesWithContext.length,
            averageContextLength: messagesWithContext.length > 0 
                ? Math.round(totalContextLength / messagesWithContext.length) 
                : 0,
            totalContextLength
        };
    };

    const providerBreakdown = calculateProviderBreakdown();
    const contextSummary = getContextSummary();
    const assistantMessages = session.messages.filter(m => m.role === 'assistant');
    const averageCostPerMessage = assistantMessages.length > 0 
        ? session.totalCost / assistantMessages.length 
        : 0;
    const sessionDuration = new Date().getTime() - session.startTime.getTime();
    const sessionMinutes = Math.round(sessionDuration / (1000 * 60));

    const getProviderIcon = (provider: string) => {
        const icons = { openai: '⚡', gemini: '💰', claude: '🎯' };
        return icons[provider as keyof typeof icons] || '🤖';
    };

    return (
        <Card className="bg-gray-800/50 border-gray-700">
            <Card.Header>
                <Card.Title className="text-white flex items-center justify-between">
                    <div className="flex items-center">
                        <BarChart3 className="w-5 h-5 mr-2 text-green-400" />
                        Context & Usage Analytics
                    </div>
                    <Badge variant="info" size="sm" className="bg-blue-600 text-white">
                        Live Session
                    </Badge>
                </Card.Title>
            </Card.Header>

            <Card.Body className="space-y-6">
                
                {/* Session Overview */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-700/50 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1">
                            <MessageSquare className="w-4 h-4 text-blue-400" />
                            <span className="text-xs text-gray-400">Messages</span>
                        </div>
                        <div className="text-lg font-semibold text-white">
                            {session.messages.length}
                        </div>
                        <div className="text-xs text-gray-400">
                            {assistantMessages.length} responses
                        </div>
                    </div>
                    
                    <div className="bg-gray-700/50 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1">
                            <Zap className="w-4 h-4 text-yellow-400" />
                            <span className="text-xs text-gray-400">Tokens</span>
                        </div>
                        <div className="text-lg font-semibold text-white">
                            {session.totalTokens.toLocaleString()}
                        </div>
                        <div className="text-xs text-gray-400">
                            {Math.round(session.totalTokens / (assistantMessages.length || 1))} avg/msg
                        </div>
                    </div>
                    
                    <div className="bg-gray-700/50 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1">
                            <DollarSign className="w-4 h-4 text-green-400" />
                            <span className="text-xs text-gray-400">Cost</span>
                        </div>
                        <div className="text-lg font-semibold text-white">
                            ${session.totalCost.toFixed(4)}
                        </div>
                        <div className="text-xs text-gray-400">
                            ${averageCostPerMessage.toFixed(4)} avg/msg
                        </div>
                    </div>
                    
                    <div className="bg-gray-700/50 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1">
                            <Clock className="w-4 h-4 text-purple-400" />
                            <span className="text-xs text-gray-400">Duration</span>
                        </div>
                        <div className="text-lg font-semibold text-white">
                            {sessionMinutes}m
                        </div>
                        <div className="text-xs text-gray-400">
                            Started {session.startTime.toLocaleTimeString()}
                        </div>
                    </div>
                </div>

                {/* Provider Breakdown */}
                {Object.keys(providerBreakdown).length > 0 && (
                    <div>
                        <h4 className="text-white font-medium mb-3 flex items-center">
                            <Database className="w-4 h-4 mr-2 text-blue-400" />
                            Provider Breakdown
                        </h4>
                        <div className="space-y-2">
                            {Object.entries(providerBreakdown).map(([provider, stats]) => (
                                <div key={provider} className="bg-gray-700/30 rounded-lg p-3">
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center space-x-2">
                                            <span className="text-lg">{getProviderIcon(provider)}</span>
                                            <span className="font-medium text-white">
                                                {provider.toUpperCase()}
                                            </span>
                                        </div>
                                        <div className="text-sm text-gray-400">
                                            {stats.messages} messages
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                            <span className="text-gray-400">Tokens:</span>
                                            <span className="text-white ml-2 font-medium">
                                                {stats.tokens.toLocaleString()}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-gray-400">Cost:</span>
                                            <span className="text-green-400 ml-2 font-medium">
                                                ${stats.cost.toFixed(4)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Context Analysis */}
                <div>
                    <div className="flex items-center justify-between mb-3">
                        <h4 className="text-white font-medium flex items-center">
                            <Database className="w-4 h-4 mr-2 text-green-400" />
                            Vector Context Analysis
                        </h4>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowContextDetails(!showContextDetails)}
                            rightIcon={showContextDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            className="text-gray-400 hover:text-white"
                        >
                            {showContextDetails ? 'Hide' : 'Show'} Details
                        </Button>
                    </div>
                    
                    <div className="bg-gray-700/30 rounded-lg p-3 space-y-2">
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Messages with context:</span>
                            <span className="text-white font-medium">
                                {contextSummary.messagesWithContext}
                            </span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Average context length:</span>
                            <span className="text-white font-medium">
                                {contextSummary.averageContextLength} chars
                            </span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Total context data:</span>
                            <span className="text-green-400 font-medium">
                                {(contextSummary.totalContextLength / 1024).toFixed(1)} KB
                            </span>
                        </div>
                    </div>

                    {showContextDetails && (
                        <div className="mt-3 space-y-2">
                            <div className="text-sm text-gray-400 mb-2">Context sources:</div>
                            <div className="space-y-1 text-xs">
                                <div className="bg-green-900/20 border border-green-500/30 rounded p-2">
                                    <span className="text-green-400 font-medium">✓ Financial Summary:</span>
                                    <span className="text-gray-300 ml-2">Net worth, assets, liabilities</span>
                                </div>
                                <div className="bg-blue-900/20 border border-blue-500/30 rounded p-2">
                                    <span className="text-blue-400 font-medium">✓ User Preferences:</span>
                                    <span className="text-gray-300 ml-2">Risk tolerance, investment style</span>
                                </div>
                                <div className="bg-purple-900/20 border border-purple-500/30 rounded p-2">
                                    <span className="text-purple-400 font-medium">✓ Active Goals:</span>
                                    <span className="text-gray-300 ml-2">Retirement, education targets</span>
                                </div>
                                <div className="bg-yellow-900/20 border border-yellow-500/30 rounded p-2">
                                    <span className="text-yellow-400 font-medium">✓ Vector Search:</span>
                                    <span className="text-gray-300 ml-2">Relevant context from database</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Message Breakdown */}
                <div>
                    <div className="flex items-center justify-between mb-3">
                        <h4 className="text-white font-medium flex items-center">
                            <MessageSquare className="w-4 h-4 mr-2 text-blue-400" />
                            Message History
                        </h4>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowMessageBreakdown(!showMessageBreakdown)}
                            rightIcon={showMessageBreakdown ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            className="text-gray-400 hover:text-white"
                        >
                            {showMessageBreakdown ? 'Hide' : 'Show'} Breakdown
                        </Button>
                    </div>
                    
                    {showMessageBreakdown && (
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                            {assistantMessages.slice(-5).map((message) => (
                                <div key={message.id} className="bg-gray-700/30 rounded p-2 text-xs">
                                    <div className="flex items-center justify-between mb-1">
                                        <div className="flex items-center space-x-2">
                                            <span>{getProviderIcon(message.provider)}</span>
                                            <span className="text-gray-400">
                                                {message.timestamp.toLocaleTimeString()}
                                            </span>
                                        </div>
                                        <div className="text-green-400 font-medium">
                                            ${message.cost.toFixed(4)}
                                        </div>
                                    </div>
                                    <div className="flex justify-between text-gray-400">
                                        <span>{message.model}</span>
                                        <span>{message.tokenCount} tokens</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Session Actions */}
                <div className="pt-4 border-t border-gray-700">
                    <div className="text-xs text-gray-400 text-center">
                        Session ID: {session.sessionId}
                    </div>
                </div>
            </Card.Body>
        </Card>
    );
};

export default ContextPanel;