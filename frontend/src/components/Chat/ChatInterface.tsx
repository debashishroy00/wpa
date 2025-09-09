/**
 * WealthPath AI - Chat Interface Component
 * Message display and input handling
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Clock, Loader2, DollarSign } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';

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

interface ChatInterfaceProps {
    messages: Message[];
    loading: boolean;
    onSendMessage: (message: string) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
    messages,
    loading,
    onSendMessage
}) => {
    const [inputMessage, setInputMessage] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Removed auto-scrolling - let user control scrolling like Claude

    const scrollToBottom = () => {
        // Only scroll if the chat container is visible and has messages
        if (messagesEndRef.current && messages.length > 0) {
            const chatContainer = messagesEndRef.current.closest('.overflow-y-auto');
            if (chatContainer && chatContainer.scrollHeight > chatContainer.clientHeight) {
                messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
            }
        }
    };

    const handleSend = () => {
        if (inputMessage.trim() && !loading) {
            onSendMessage(inputMessage.trim());
            setInputMessage('');
            
            // Reset textarea height to single line
            if (textareaRef.current) {
                textareaRef.current.style.height = '52px'; // Back to min height
                textareaRef.current.setAttribute('rows', '1');
            }
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInputMessage(e.target.value);
        
        // Auto-resize textarea like Claude chat
        const textarea = e.target;
        textarea.style.height = 'auto';
        const newHeight = Math.min(textarea.scrollHeight, 200); // Max 200px height
        textarea.style.height = newHeight + 'px';
        
        // Adjust rows based on content
        const lineHeight = 24; // Approximate line height
        const rows = Math.max(1, Math.min(8, Math.ceil(newHeight / lineHeight)));
        textarea.setAttribute('rows', rows.toString());
    };

    const formatTimestamp = (timestamp: Date) => {
        return timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    };

    const getProviderIcon = (provider: string) => {
        const icons = { openai: '⚡', gemini: '💰', claude: '🎯' };
        return icons[provider as keyof typeof icons] || '🤖';
    };

    return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg h-[65vh] flex flex-col">
            
            {/* Messages Area - Maximized */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                    <div className="text-center text-gray-500 mt-8">
                        <Bot className="w-8 h-8 mx-auto mb-3 opacity-50" />
                        <p className="text-sm">Start a conversation with your AI Financial Advisor</p>
                    </div>
                ) : (
                    messages.map((message) => (
                        <div
                            key={message.id}
                            className="group"
                        >
                            <div
                                className={`w-full rounded-lg p-4 ${
                                    message.role === 'user'
                                        ? 'bg-blue-600 text-white'
                                        : message.role === 'assistant'
                                        ? 'bg-gray-700 text-gray-100'
                                        : 'bg-yellow-900/30 border border-yellow-500/30 text-yellow-200 text-center'
                                }`}
                            >
                                {/* Message Header */}
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center space-x-2 text-sm opacity-75">
                                        {message.role === 'user' ? (
                                            <User className="w-4 h-4" />
                                        ) : (
                                            <Bot className="w-4 h-4" />
                                        )}
                                        <span className="font-medium">
                                            {message.role === 'user' ? 'You' : 'AI Advisor'}
                                        </span>
                                        <Clock className="w-3 h-3" />
                                        <span>{formatTimestamp(message.timestamp)}</span>
                                    </div>
                                    
                                    {/* Message Metadata (visible on hover) */}
                                    {message.role === 'assistant' && (
                                        <div className="opacity-0 group-hover:opacity-100 transition-opacity text-xs text-gray-400 flex items-center space-x-2">
                                            <span>{getProviderIcon(message.provider)}</span>
                                            <span>{message.model}</span>
                                            {message.cost > 0 && (
                                                <>
                                                    <DollarSign className="w-3 h-3" />
                                                    <span>${message.cost.toFixed(4)}</span>
                                                </>
                                            )}
                                            <span>{message.tokenCount} tokens</span>
                                        </div>
                                    )}
                                </div>

                                {/* Message Content */}
                                <div className="prose prose-sm prose-invert max-w-none">
                                    {message.role === 'assistant' ? (
                                        <div 
                                            className="text-gray-100 leading-relaxed"
                                            dangerouslySetInnerHTML={{ 
                                                __html: formatAssistantMessage(message.content) 
                                            }}
                                        />
                                    ) : (
                                        <p className="whitespace-pre-wrap">{message.content}</p>
                                    )}
                                </div>

                                {/* Context Indicator */}
                                {message.context && (
                                    <div className="mt-3 pt-2 border-t border-gray-600 text-xs text-gray-400">
                                        <span className="opacity-60">
                                            Context: {(() => {
                                                try {
                                                    const contextData = typeof message.context === 'string' 
                                                        ? JSON.parse(message.context) 
                                                        : message.context;
                                                    
                                                    if (contextData.complete_context_used) {
                                                        return 'Complete Financial Context';
                                                    }
                                                } catch (e) {
                                                    // If parsing fails, check for string indicators
                                                    if (message.context.includes('complete_context_used')) {
                                                        return 'Complete Financial Context';
                                                    }
                                                }
                                                
                                                // Fallback to original format
                                                const dataPoints = message.context.split('\n').length;
                                                return `Vector database + ${dataPoints} data points`;
                                            })()}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}

                {/* Typing Indicator */}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-700 text-gray-100 rounded-lg p-4 max-w-[80%]">
                            <div className="flex items-center space-x-2">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span className="text-sm">AI Advisor is thinking...</span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area - Claude-style */}
            <div className="border-t border-gray-700 p-4">
                <div className="relative">
                    <textarea
                        ref={textareaRef}
                        value={inputMessage}
                        onChange={handleInputChange}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask about your finances, goals, or investments..."
                        className="w-full bg-gray-700 border border-gray-600 rounded-xl px-4 py-3 pr-12 text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[52px] max-h-[200px] text-base leading-6"
                        disabled={loading}
                        rows={1}
                    />
                    <button
                        onClick={handleSend}
                        disabled={!inputMessage.trim() || loading}
                        className="absolute right-2 bottom-2 p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg transition-colors duration-200 flex items-center justify-center"
                    >
                        {loading ? (
                            <Loader2 className="w-5 h-5 text-white animate-spin" />
                        ) : (
                            <Send className="w-5 h-5 text-white" />
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

// Format assistant message with basic markdown support
const formatAssistantMessage = (content: string): string => {
    return content
        // Format bold text
        .replace(/\*\*([^*\n]+)\*\*/g, '<strong class="text-white">$1</strong>')
        
        // Format financial amounts
        .replace(/\$[\d,]+\.?\d*/g, '<span class="text-green-400 font-semibold">$&</span>')
        
        // Format percentages
        .replace(/\b\d+\.?\d*%/g, '<span class="text-blue-400 font-semibold">$&</span>')
        
        // Convert line breaks to HTML
        .replace(/\n\n/g, '</p><p class="mb-2">')
        .replace(/\n/g, '<br/>')
        
        // Wrap in paragraph tags
        .replace(/^/, '<p class="mb-2">')
        .replace(/$/, '</p>');
};

export default ChatInterface;