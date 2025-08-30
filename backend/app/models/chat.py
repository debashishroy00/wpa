"""
Chat Session Models for conversational memory
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class ChatSession(Base):
    """
    Chat session model to track conversation state and history
    """
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, unique=True, index=True)  # UUID from frontend
    
    # Session metadata
    title = Column(String(255), nullable=True)  # Optional session title
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Conversational memory (Phase 1 implementation)
    conversation_history = Column(JSONB, default=list, nullable=False)  # List of message objects
    session_summary = Column(Text, nullable=True)  # Rolling summary (2-4 sentences)
    last_intent = Column(String(50), nullable=True)  # Last detected intent (retirement, cash, etc.)
    
    # Statistics
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens_used = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, session_id='{self.session_id}', messages={self.message_count})>"


class ChatMessage(Base):
    """
    Individual chat message for detailed tracking and analytics
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Metadata
    intent_detected = Column(String(50), nullable=True)  # Detected intent for this message
    context_used = Column(JSONB, nullable=True)  # What context was used for this response
    tokens_used = Column(Integer, default=0, nullable=False)
    response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds
    
    # LLM details
    model_used = Column(String(50), nullable=True)  # Which model generated this response
    provider = Column(String(20), nullable=True)  # openai, gemini, claude, etc.
    temperature = Column(String(10), nullable=True)  # Temperature setting used
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}', content='{self.content[:50]}...', intent='{self.intent_detected}')>"


# Add this to User model relationship (you'll need to add to user.py)
"""
Add to User model in user.py:
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
"""