"""
Chat Intelligence Model for extracting and storing conversation insights
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid


class ChatIntelligence(Base):
    """
    Chat intelligence extraction to capture high-value financial insights
    from conversations for vector store sync
    """
    __tablename__ = "chat_intelligence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)  # Links to ChatSession.session_id
    
    # Extracted insights (2-3KB total)
    key_decisions = Column(ARRAY(Text), default=list, nullable=False)  # AI recommendations made
    action_items = Column(ARRAY(Text), default=list, nullable=False)   # Next steps for user
    financial_insights = Column(JSONB, default=dict, nullable=False)   # Patterns, preferences, amounts
    topics_discussed = Column(ARRAY(String(100)), default=list, nullable=False)  # Categories
    
    # Session metadata
    conversation_turns = Column(Integer, default=0, nullable=False)
    last_intent = Column(String(50), nullable=True)  # retirement, investment, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_intelligence")
    
    def __repr__(self):
        return f"<ChatIntelligence(id={self.id}, user_id={self.user_id}, turns={self.conversation_turns}, topics={len(self.topics_discussed)})>"
    
    def to_vector_summary(self) -> str:
        """
        Generate embedding-optimized summary for vector store
        Format: 2-3KB structured text for efficient similarity search
        """
        parts = []
        
        # Core insights
        if self.key_decisions:
            parts.append(f"Key Financial Decisions: {'; '.join(self.key_decisions[:5])}")
        
        if self.action_items:
            parts.append(f"Recommended Actions: {'; '.join(self.action_items[:5])}")
            
        # Financial context
        if self.financial_insights:
            insights = []
            for key, value in self.financial_insights.items():
                if isinstance(value, (int, float)):
                    insights.append(f"{key}: ${value:,.2f}")
                elif isinstance(value, str):
                    insights.append(f"{key}: {value}")
            if insights:
                parts.append(f"Financial Context: {'; '.join(insights[:5])}")
        
        # Topics and intent
        if self.topics_discussed:
            parts.append(f"Discussion Topics: {', '.join(set(self.topics_discussed))}")
            
        if self.last_intent:
            parts.append(f"Primary Focus: {self.last_intent}")
            
        # Metadata
        parts.append(f"Conversation Depth: {self.conversation_turns} exchanges")
        
        return '\n'.join(parts)