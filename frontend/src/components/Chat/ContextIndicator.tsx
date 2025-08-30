/**
 * Real-Time Context Indicator Component
 * Shows conversation memory state, intent detection, and token optimization
 */
import React from 'react';
import '../../../styles/context-indicator.css';

interface TokenOptimization {
  original_tokens: number;
  final_tokens: number;
  trimmed: boolean;
}

interface ConversationContext {
  message_count: number;
  session_summary?: string;
  last_intent?: string;
  conversation_turn: number;
  detected_intents?: string[];
  token_optimization?: TokenOptimization;
  phase?: string;
}

interface ContextIndicatorProps {
  conversationContext: ConversationContext | null;
  currentIntent?: string;
  isLoading?: boolean;
  className?: string;
}

const ContextIndicator: React.FC<ContextIndicatorProps> = ({
  conversationContext,
  currentIntent,
  isLoading = false,
  className = ''
}) => {
  // Don't show indicator for first message
  if (!conversationContext || conversationContext.conversation_turn <= 1) {
    return null;
  }

  const getIntentIcon = (intent: string | undefined) => {
    const icons = {
      'retirement': '🎯',
      'allocation': '📊',
      'debt': '💳',
      'tax': '📋',
      'real_estate': '🏠',
      'emergency': '⚡',
      'risk': '⚖️',
      'returns': '📈',
      'optimization': '⚡',
      'cash_flow': '💰',
      'general': '💭'
    };
    
    return icons[intent as keyof typeof icons] || '💭';
  };

  const getIntentDisplayName = (intent: string | undefined) => {
    const displayNames = {
      'retirement': 'Retirement Planning',
      'allocation': 'Asset Allocation',
      'debt': 'Debt Management',
      'tax': 'Tax Strategy',
      'real_estate': 'Real Estate',
      'emergency': 'Emergency Fund',
      'risk': 'Risk Assessment',
      'returns': 'Performance Analysis',
      'optimization': 'Portfolio Optimization',
      'cash_flow': 'Cash Flow',
      'general': 'General Advice'
    };
    
    return displayNames[intent as keyof typeof displayNames] || 'Financial Advice';
  };

  const getPhaseIndicator = () => {
    const phase = conversationContext.phase;
    if (!phase || phase === '1') return null;
    
    return (
      <div className="phase-indicator">
        <span className="phase-icon">🧠</span>
        <span className="phase-text">
          {phase === '2' ? 'Enhanced Intelligence' : `Phase ${phase}`}
        </span>
      </div>
    );
  };

  const getTokenOptimizationIndicator = () => {
    const tokenOpt = conversationContext.token_optimization;
    if (!tokenOpt) return null;
    
    return (
      <div className={`token-indicator ${tokenOpt.trimmed ? 'optimized' : 'normal'}`}>
        <span className="token-icon">
          {tokenOpt.trimmed ? '⚡' : '📊'}
        </span>
        <span className="token-text">
          {tokenOpt.trimmed 
            ? `Optimized: ${tokenOpt.final_tokens} tokens`
            : `${tokenOpt.final_tokens} tokens`
          }
        </span>
        {tokenOpt.trimmed && (
          <span className="savings-text">
            (saved {tokenOpt.original_tokens - tokenOpt.final_tokens})
          </span>
        )}
      </div>
    );
  };

  const getMemoryStrength = () => {
    const turnCount = conversationContext.conversation_turn;
    const messageCount = conversationContext.message_count;
    
    if (turnCount <= 2) return 'building';
    if (turnCount <= 5) return 'growing';
    if (turnCount <= 10) return 'strong';
    return 'comprehensive';
  };

  const memoryStrength = getMemoryStrength();
  const primaryIntent = currentIntent || conversationContext.last_intent;
  const detectedIntents = conversationContext.detected_intents || [];

  return (
    <div className={`context-indicator ${className} ${isLoading ? 'loading' : ''}`}>
      {/* Memory Status */}
      <div className="memory-status">
        <div className={`memory-strength ${memoryStrength}`}>
          <span className="memory-icon">🧠</span>
          <span className="memory-text">
            Turn {conversationContext.conversation_turn}
          </span>
          <div className={`memory-bar ${memoryStrength}`}>
            <div className="memory-fill"></div>
          </div>
        </div>
        
        <div className="memory-details">
          <span className="detail-item">
            {conversationContext.message_count} messages
          </span>
          <span className="detail-separator">•</span>
          <span className="detail-item">
            Memory {memoryStrength}
          </span>
        </div>
      </div>

      {/* Intent Detection */}
      {primaryIntent && (
        <div className="intent-status">
          <div className="primary-intent">
            <span className="intent-icon">
              {getIntentIcon(primaryIntent)}
            </span>
            <span className="intent-text">
              {getIntentDisplayName(primaryIntent)}
            </span>
          </div>
          
          {detectedIntents.length > 1 && (
            <div className="multi-intent-indicator">
              <span className="multi-icon">🎯</span>
              <span className="multi-text">
                +{detectedIntents.length - 1} related topics
              </span>
            </div>
          )}
        </div>
      )}

      {/* Performance Indicators */}
      <div className="performance-indicators">
        {getPhaseIndicator()}
        {getTokenOptimizationIndicator()}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="processing-indicator">
          <div className="processing-spinner"></div>
          <span className="processing-text">Analyzing context...</span>
        </div>
      )}
    </div>
  );
};

export default ContextIndicator;