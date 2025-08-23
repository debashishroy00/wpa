"""
Session Management Service
Provides conversation memory and context persistence
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ConversationSessionService:
    """Manages conversation sessions with memory and context persistence"""
    
    def __init__(self):
        # In-memory storage (would use Redis in production)
        self.sessions: Dict[int, Dict] = {}
        self.session_timeout = timedelta(hours=2)  # 2 hour timeout
    
    def get_or_create_session(self, user_id: int) -> Dict[str, Any]:
        """Get existing session or create new one"""
        
        # Clean expired sessions first
        self._cleanup_expired_sessions()
        
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                'user_id': user_id,
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'conversation_history': [],
                'context_cache': {},
                'topics_discussed': set(),
                'last_financial_summary': None
            }
            logger.info(f"Created new session for user {user_id}")
        else:
            # Update last activity
            self.sessions[user_id]['last_activity'] = datetime.now()
        
        return self.sessions[user_id]
    
    def add_exchange(self, user_id: int, user_message: str, ai_response: str, intent: str = None):
        """Add conversation exchange to session history"""
        
        session = self.get_or_create_session(user_id)
        
        exchange = {
            'timestamp': datetime.now(),
            'user_message': user_message,
            'ai_response': ai_response[:500],  # Store summary only
            'intent': intent,
            'response_length': len(ai_response)
        }
        
        session['conversation_history'].append(exchange)
        
        # Keep only last 10 exchanges to manage memory
        if len(session['conversation_history']) > 10:
            session['conversation_history'] = session['conversation_history'][-10:]
        
        # Track topics
        if intent:
            session['topics_discussed'].add(intent)
        
        logger.info(f"Added exchange to session for user {user_id}, intent: {intent}")
    
    def get_conversation_context(self, user_id: int, include_last_n: int = 3) -> str:
        """Get recent conversation context for prompt"""
        
        session = self.get_or_create_session(user_id)
        history = session.get('conversation_history', [])
        
        if not history:
            return ""
        
        recent_exchanges = history[-include_last_n:]
        
        context = "\nRECENT CONVERSATION CONTEXT:\n"
        context += "=" * 35 + "\n"
        
        for exchange in recent_exchanges:
            context += f"User: {exchange['user_message']}\n"
            context += f"Assistant: {exchange['ai_response'][:100]}...\n"
            if exchange.get('intent'):
                context += f"(Intent: {exchange['intent']})\n"
            context += "\n"
        
        # Add topics summary
        topics = session.get('topics_discussed', set())
        if topics:
            context += f"Topics discussed in this session: {', '.join(topics)}\n\n"
        
        return context
    
    def cache_financial_context(self, user_id: int, context_data: Dict[str, Any]):
        """Cache financial context to avoid repeated database calls"""
        
        session = self.get_or_create_session(user_id)
        session['context_cache'] = {
            'data': context_data,
            'cached_at': datetime.now(),
            'cache_valid_until': datetime.now() + timedelta(minutes=30)
        }
    
    def get_cached_financial_context(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached financial context if still valid"""
        
        session = self.get_or_create_session(user_id)
        cache = session.get('context_cache', {})
        
        if not cache:
            return None
        
        # Check if cache is still valid
        if datetime.now() > cache.get('cache_valid_until', datetime.min):
            logger.info(f"Cache expired for user {user_id}")
            return None
        
        logger.info(f"Using cached context for user {user_id}")
        return cache.get('data')
    
    def has_discussed_topic(self, user_id: int, topic: str) -> bool:
        """Check if topic has been discussed in this session"""
        
        session = self.get_or_create_session(user_id)
        return topic in session.get('topics_discussed', set())
    
    def get_session_summary(self, user_id: int) -> Dict[str, Any]:
        """Get session summary for debugging"""
        
        if user_id not in self.sessions:
            return {'exists': False}
        
        session = self.sessions[user_id]
        
        return {
            'exists': True,
            'created_at': session['created_at'],
            'last_activity': session['last_activity'],
            'exchanges_count': len(session.get('conversation_history', [])),
            'topics_discussed': list(session.get('topics_discussed', set())),
            'has_cached_context': bool(session.get('context_cache')),
            'cache_valid': (
                session.get('context_cache', {}).get('cache_valid_until', datetime.min) > datetime.now()
                if session.get('context_cache') else False
            )
        }
    
    def clear_session(self, user_id: int):
        """Clear session data for user"""
        
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"Cleared session for user {user_id}")
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions to free memory"""
        
        cutoff_time = datetime.now() - self.session_timeout
        expired_users = []
        
        for user_id, session in self.sessions.items():
            if session.get('last_activity', datetime.min) < cutoff_time:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.sessions[user_id]
            logger.info(f"Cleaned up expired session for user {user_id}")
    
    def get_contextual_suggestions(self, user_id: int) -> List[str]:
        """Get contextual suggestions based on conversation history"""
        
        session = self.get_or_create_session(user_id)
        topics = session.get('topics_discussed', set())
        
        # Base suggestions
        suggestions = ["What's my financial health score?", "Am I on track for retirement?"]
        
        # Add contextual suggestions based on topics
        if 'retirement' in topics:
            suggestions.extend([
                "Should I consider early retirement?",
                "How can I optimize my retirement strategy?"
            ])
        
        if 'investment' in topics:
            suggestions.extend([
                "Should I rebalance my portfolio?",
                "What's my asset allocation breakdown?"
            ])
        
        if 'debt' in topics:
            suggestions.extend([
                "Should I pay off debt or invest?",
                "What's my debt-to-income ratio?"
            ])
        
        return suggestions[:5]  # Limit to 5 suggestions


# Global instance
session_service = ConversationSessionService()