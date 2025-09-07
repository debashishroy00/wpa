/**
 * Conversation History Component for Session Management
 * Provides intelligent session switching and conversation tracking
 */
import React, { useState, useEffect } from 'react';
import { useUnifiedAuthStore } from '../../stores/unified-auth-store';
import { getApiBaseUrl } from '../../utils/api-simple';

interface ConversationSession {
  session_id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  session_summary: string | null;
  last_intent: string | null;
  user_id: string;
}

interface ConversationHistoryProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
  isVisible: boolean;
  onClose: () => void;
}

const ConversationHistory: React.FC<ConversationHistoryProps> = ({
  currentSessionId,
  onSessionSelect,
  onNewSession,
  isVisible,
  onClose
}) => {
  const [sessions, setSessions] = useState<ConversationSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const user = useUnifiedAuthStore((state) => state.user);
  const authToken = useUnifiedAuthStore((state) => state.getAccessToken());

  useEffect(() => {
    if (isVisible && user && authToken) {
      loadUserSessions();
    }
  }, [isVisible, user, authToken]);

  const loadUserSessions = async () => {
    if (!user || !authToken) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/v1/chat-memory/sessions/${user.id}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to load sessions: ${response.statusText}`);
      }

      const data = await response.json();
      setSessions(data.sessions || []);
      
    } catch (err) {
      console.error('Error loading sessions:', err);
      
      // Enhanced error handling
      let errorMessage = 'Failed to load conversation history';
      if (err.message && err.message.includes('401')) {
        errorMessage = 'Authentication expired. Please refresh and log in again.';
      } else if (err.message && err.message.includes('403')) {
        errorMessage = 'Access denied. Unable to load conversation history.';
      } else if (err instanceof TypeError) {
        errorMessage = 'Connection error. Please check your internet connection.';
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSessionSelect = (sessionId: string) => {
    onSessionSelect(sessionId);
    onClose();
  };

  const handleNewSession = () => {
    onNewSession();
    onClose();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 168) { // 7 days
      return `${Math.floor(diffInHours / 24)}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getIntentIcon = (intent: string | null) => {
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

  if (!isVisible) return null;

  return (
    <div className="conversation-history-overlay">
      <div className="conversation-history-modal">
        {/* Header */}
        <div className="conversation-history-header">
          <h2>Conversation History</h2>
          <button 
            className="close-button"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        {/* New Conversation Button */}
        <div className="new-session-section">
          <button 
            className="new-session-button"
            onClick={handleNewSession}
          >
            <span className="icon">✨</span>
            <span>Start New Conversation</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="sessions-container">
          {loading && (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <span>Loading conversations...</span>
            </div>
          )}

          {error && (
            <div className="error-state">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {!loading && !error && sessions.length === 0 && (
            <div className="empty-state">
              <span className="empty-icon">💬</span>
              <p>No previous conversations</p>
              <p className="empty-subtitle">Start a new conversation to begin!</p>
            </div>
          )}

          {!loading && !error && sessions.length > 0 && (
            <div className="sessions-list">
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className={`session-item ${session.session_id === currentSessionId ? 'current' : ''}`}
                  onClick={() => handleSessionSelect(session.session_id)}
                >
                  <div className="session-header">
                    <div className="session-info">
                      <span className="session-icon">
                        {getIntentIcon(session.last_intent)}
                      </span>
                      <div className="session-details">
                        <div className="session-title">
                          {session.session_summary || `Session ${session.session_id.slice(-8)}`}
                        </div>
                        <div className="session-meta">
                          {session.message_count} messages • {formatDate(session.updated_at)}
                        </div>
                      </div>
                    </div>
                    {session.session_id === currentSessionId && (
                      <div className="current-indicator">
                        <span className="current-dot"></span>
                        <span className="current-text">Current</span>
                      </div>
                    )}
                  </div>
                  
                  {session.last_intent && (
                    <div className="session-intent">
                      Last topic: {session.last_intent.replace('_', ' ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="conversation-history-footer">
          <div className="footer-info">
            <span className="info-icon">🧠</span>
            <span>Your conversation memory helps provide better financial advice</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationHistory;