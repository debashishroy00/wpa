"""
Vector-Based Chat Memory Service
Clean implementation using only simple_vector_store for conversation memory
Replaces the database-heavy chat_memory_service.py
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json
import structlog
import uuid

from app.services.simple_vector_store import get_vector_store

logger = structlog.get_logger()


class VectorChatMemoryService:
    """
    Vector-only chat memory service for clean, simple conversation tracking
    
    Uses simple_vector_store with these document types per user:
    - user_{id}_conversation_context: Current session summary, intent, key facts
    - user_{id}_conversation_history: Recent conversation turns (last 10)
    """
    
    def __init__(self):
        self.max_history_turns = 10  # Keep last 10 conversation turns
        self.max_context_length = 2000  # Max chars for context summary
        self.vector_store = get_vector_store()  # Get the global vector store instance
    
    def get_or_create_session(self, user_id: int, session_id: str) -> Dict[str, Any]:
        """
        Get or create conversation session using vector store
        Returns session metadata and context
        """
        context_doc_id = f"user_{user_id}_conversation_context"
        history_doc_id = f"user_{user_id}_conversation_history"
        
        # Try to get existing context
        context_doc = self.vector_store.get_document(context_doc_id)
        if not context_doc:
            # Create new session context
            initial_context = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "last_intent": None,
                "session_summary": "New conversation started",
                "message_count": 0,
                "key_topics": [],
                "user_preferences": {}
            }
            
            self.vector_store.add_document(
                content=json.dumps(initial_context, indent=2),
                doc_id=context_doc_id,
                metadata={
                    "category": "chat_memory",
                    "user_id": user_id,
                    "doc_type": "conversation_context"
                }
            )
            
            # Create empty history
            self.vector_store.add_document(
                content="[]",  # Empty conversation history
                doc_id=history_doc_id,
                metadata={
                    "category": "chat_memory", 
                    "user_id": user_id,
                    "doc_type": "conversation_history"
                }
            )
            
            logger.info("Created new vector-based chat session", 
                       user_id=user_id, session_id=session_id)
            
            return initial_context
        
        # Parse existing context
        try:
            context = json.loads(context_doc.content)
            context["session_id"] = session_id  # Update with current session
            return context
        except json.JSONDecodeError:
            logger.error("Failed to parse conversation context", user_id=user_id)
            # Fallback to new session
            return self.get_or_create_session(user_id, f"fallback_{uuid.uuid4()}")
    
    def add_message_pair(self, user_id: int, user_message: str, ai_response: str, 
                        intent: Optional[str] = None) -> None:
        """
        Add user message and AI response pair to conversation memory
        """
        try:
            # Get current history
            history_doc_id = f"user_{user_id}_conversation_history"
            history_doc = self.vector_store.get_document(history_doc_id)
            
            if history_doc:
                try:
                    history = json.loads(history_doc.content)
                except json.JSONDecodeError:
                    history = []
            else:
                history = []
            
            # Add new conversation turn
            turn = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_message": user_message,
                "ai_response": ai_response,
                "intent": intent
            }
            
            history.append(turn)
            
            # Keep only recent turns
            if len(history) > self.max_history_turns:
                history = history[-self.max_history_turns:]
            
            # Update history document
            self.vector_store.update_document(
                doc_id=history_doc_id,
                content=json.dumps(history, indent=2)
            )
            
            # Update context summary
            self._update_conversation_context(user_id, turn, len(history))
            
            logger.info("Added conversation turn to vector store", 
                       user_id=user_id, intent=intent, history_length=len(history))
            
        except Exception as e:
            logger.error("Failed to add message pair to vector store", 
                        user_id=user_id, error=str(e))
            raise
    
    def get_conversation_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get conversation context for LLM prompt
        Combines context summary with recent conversation history
        """
        user_id = session_data.get("user_id")
        if not user_id:
            return {"error": "No user_id in session data"}
        
        try:
            # Get context summary
            context_doc_id = f"user_{user_id}_conversation_context"
            context_doc = self.vector_store.get_document(context_doc_id)
            
            # Get recent history
            history_doc_id = f"user_{user_id}_conversation_history"
            history_doc = self.vector_store.get_document(history_doc_id)
            
            context = {}
            
            if context_doc:
                try:
                    context_summary = json.loads(context_doc.content)
                    context.update({
                        "session_summary": context_summary.get("session_summary", ""),
                        "last_intent": context_summary.get("last_intent"),
                        "message_count": context_summary.get("message_count", 0),
                        "key_topics": context_summary.get("key_topics", [])
                    })
                except json.JSONDecodeError:
                    pass
            
            if history_doc:
                try:
                    history = json.loads(history_doc.content)
                    context["recent_conversation"] = history[-5:]  # Last 5 turns for LLM context
                except json.JSONDecodeError:
                    pass
            
            return context
            
        except Exception as e:
            logger.error("Failed to get conversation context", user_id=user_id, error=str(e))
            return {"error": f"Context retrieval failed: {str(e)}"}
    
    def _update_conversation_context(self, user_id: int, latest_turn: Dict[str, Any], 
                                   total_turns: int) -> None:
        """
        Update the conversation context summary with latest turn
        """
        try:
            context_doc_id = f"user_{user_id}_conversation_context"
            context_doc = self.vector_store.get_document(context_doc_id)
            
            if context_doc:
                try:
                    context = json.loads(context_doc.content)
                except json.JSONDecodeError:
                    context = {}
            else:
                context = {}
            
            # Update context with latest information
            context.update({
                "last_updated": datetime.utcnow().isoformat(),
                "message_count": total_turns,
                "last_intent": latest_turn.get("intent") or context.get("last_intent"),
                "last_user_message": latest_turn["user_message"][:200],  # Truncate for storage
                "last_ai_response": latest_turn["ai_response"][:200]
            })
            
            # Update session summary (keep it concise)
            if total_turns <= 2:
                context["session_summary"] = f"User discussing {latest_turn.get('intent', 'general topics')}"
            else:
                # Build a simple summary from intent
                intent = latest_turn.get("intent")
                if intent:
                    context["session_summary"] = f"Ongoing {intent} discussion ({total_turns} exchanges)"
                else:
                    context["session_summary"] = f"Conversation in progress ({total_turns} exchanges)"
            
            # Update key topics
            if "key_topics" not in context:
                context["key_topics"] = []
            
            intent = latest_turn.get("intent")
            if intent and intent not in context["key_topics"]:
                context["key_topics"].append(intent)
                # Keep only recent topics
                if len(context["key_topics"]) > 5:
                    context["key_topics"] = context["key_topics"][-5:]
            
            # Save updated context
            self.vector_store.update_document(
                doc_id=context_doc_id,
                content=json.dumps(context, indent=2)
            )
            
        except Exception as e:
            logger.error("Failed to update conversation context", user_id=user_id, error=str(e))
    
    def search_conversation_history(self, user_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search through conversation history for relevant past discussions
        """
        try:
            history_doc_id = f"user_{user_id}_conversation_history"
            history_doc = self.vector_store.get_document(history_doc_id)
            
            if not history_doc:
                return []
            
            history = json.loads(history_doc.content)
            query_lower = query.lower()
            
            # Simple keyword matching in conversation history
            relevant_turns = []
            for turn in history:
                user_msg = turn.get("user_message", "").lower()
                ai_msg = turn.get("ai_response", "").lower()
                
                if query_lower in user_msg or query_lower in ai_msg:
                    relevant_turns.append(turn)
            
            return relevant_turns[-limit:]  # Return most recent relevant turns
            
        except Exception as e:
            logger.error("Failed to search conversation history", 
                        user_id=user_id, error=str(e))
            return []
    
    def clear_session(self, user_id: int) -> bool:
        """
        Clear conversation memory for user (for testing or user request)
        """
        try:
            context_doc_id = f"user_{user_id}_conversation_context"
            history_doc_id = f"user_{user_id}_conversation_history"
            
            self.vector_store.delete_document(context_doc_id)
            self.vector_store.delete_document(history_doc_id)
            
            logger.info("Cleared conversation memory", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to clear conversation memory", 
                        user_id=user_id, error=str(e))
            return False


# Global instance
vector_chat_memory_service = VectorChatMemoryService()