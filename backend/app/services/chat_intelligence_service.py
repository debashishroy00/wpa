"""
Chat Intelligence Service for extracting and managing conversation insights
"""
import re
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.chat_intelligence import ChatIntelligence
from app.models.user import User


class ChatIntelligenceService:
    """
    Service for extracting financial insights from chat conversations
    """
    
    # Financial topics for classification
    FINANCIAL_TOPICS = {
        'retirement': ['retirement', '401k', '403b', 'ira', 'pension', 'social security', 'retirement planning'],
        'investment': ['invest', 'stock', 'bond', 'etf', 'mutual fund', 'portfolio', 'asset allocation'],
        'debt': ['debt', 'loan', 'mortgage', 'credit card', 'payment', 'refinance'],
        'tax': ['tax', 'ira', 'deduction', 'refund', 'filing', 'withholding'],
        'insurance': ['insurance', 'life insurance', 'health insurance', 'disability'],
        'estate': ['estate', 'will', 'trust', 'inheritance', 'beneficiary'],
        'budget': ['budget', 'spending', 'saving', 'expense', 'income', 'cash flow']
    }
    
    # Patterns for extracting financial decisions
    DECISION_PATTERNS = [
        r'(?:recommend|suggest|should|consider|optimal|best) (.{1,200})',
        r'(?:i think you should|you might want to|my recommendation is) (.{1,200})',
        r'(?:strategy would be|approach is|plan is) to (.{1,200})'
    ]
    
    # Patterns for extracting action items
    ACTION_PATTERNS = [
        r'(?:next step|you should|need to|make sure to|don\'t forget to) (.{1,100})',
        r'(?:review|check|verify|update|contact|call) (.{1,100})',
        r'(?:consider|evaluate|look into|research) (.{1,100})'
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_conversation_turn(
        self, 
        user_id: int, 
        session_id: str, 
        user_message: str, 
        ai_response: str
    ) -> Dict:
        """
        Process a conversation turn and extract/update intelligence
        """
        # Get or create intelligence record
        intelligence = self.db.query(ChatIntelligence).filter(
            and_(
                ChatIntelligence.user_id == user_id,
                ChatIntelligence.session_id == session_id
            )
        ).first()
        
        if not intelligence:
            intelligence = ChatIntelligence(
                user_id=user_id,
                session_id=session_id,
                key_decisions=[],
                action_items=[],
                financial_insights={},
                topics_discussed=[],
                conversation_turns=0  # Initialize to 0 to prevent NoneType error
            )
            self.db.add(intelligence)
        
        # Extract insights from this turn
        turn_insights = self._extract_insights(user_message, ai_response)
        
        # Update intelligence record
        self._merge_insights(intelligence, turn_insights)
        intelligence.conversation_turns = (intelligence.conversation_turns or 0) + 1
        intelligence.last_intent = self._classify_intent(user_message)
        
        self.db.commit()
        self.db.refresh(intelligence)
        
        return {
            'intelligence_id': str(intelligence.id),
            'insights_extracted': len(turn_insights['decisions']) + len(turn_insights['actions']),
            'total_turns': intelligence.conversation_turns,
            'topics': intelligence.topics_discussed,
            'last_intent': intelligence.last_intent
        }
    
    def _extract_insights(self, user_message: str, ai_response: str) -> Dict:
        """
        Extract insights from a conversation turn
        """
        insights = {
            'decisions': [],
            'actions': [],
            'financial_data': {},
            'topics': []
        }
        
        # Extract decisions from AI response
        for pattern in self.DECISION_PATTERNS:
            matches = re.finditer(pattern, ai_response, re.IGNORECASE)
            for match in matches:
                decision = match.group(1).strip()
                if len(decision) > 10:  # Filter out very short matches
                    insights['decisions'].append(decision[:200])  # Truncate
        
        # Extract action items from AI response
        for pattern in self.ACTION_PATTERNS:
            matches = re.finditer(pattern, ai_response, re.IGNORECASE)
            for match in matches:
                action = match.group(1).strip()
                if len(action) > 5:
                    insights['actions'].append(action[:100])  # Truncate
        
        # Extract financial amounts
        combined_text = f"{user_message} {ai_response}"
        insights['financial_data'] = self._extract_financial_amounts(combined_text)
        
        # Classify topics discussed
        insights['topics'] = self._extract_topics(combined_text)
        
        return insights
    
    def _extract_financial_amounts(self, text: str) -> Dict:
        """
        Extract financial amounts and percentages from text
        """
        financial_data = {}
        
        # Extract dollar amounts
        dollar_pattern = r'\$([0-9,]+(?:\.[0-9]{2})?)'
        amounts = re.findall(dollar_pattern, text)
        if amounts:
            # Store largest amounts (up to 5)
            amounts_float = [float(a.replace(',', '')) for a in amounts if a]
            amounts_float.sort(reverse=True)
            for i, amount in enumerate(amounts_float[:5]):
                financial_data[f'amount_{i+1}'] = amount
        
        # Extract percentages
        percent_pattern = r'([0-9]+(?:\.[0-9]+)?)\s*%'
        percentages = re.findall(percent_pattern, text)
        if percentages:
            for i, pct in enumerate(percentages[:3]):  # Top 3
                financial_data[f'percentage_{i+1}'] = float(pct)
        
        # Extract age mentions (for retirement planning)
        age_pattern = r'(?:age|turn|when i\'m)\s+([0-9]{2})'
        ages = re.findall(age_pattern, text, re.IGNORECASE)
        if ages:
            financial_data['target_age'] = int(ages[0])
        
        return financial_data
    
    def _extract_topics(self, text: str) -> List[str]:
        """
        Extract financial topics from text
        """
        topics = set()
        text_lower = text.lower()
        
        for topic, keywords in self.FINANCIAL_TOPICS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    topics.add(topic)
                    break
        
        return list(topics)
    
    def _classify_intent(self, user_message: str) -> Optional[str]:
        """
        Classify the user's primary intent from their message
        """
        message_lower = user_message.lower()
        
        # Score each topic based on keyword matches
        topic_scores = {}
        for topic, keywords in self.FINANCIAL_TOPICS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                topic_scores[topic] = score
        
        # Return topic with highest score
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        
        return None
    
    def _merge_insights(self, intelligence: ChatIntelligence, new_insights: Dict):
        """
        Merge new insights into existing intelligence record
        """
        # Add new decisions (avoid duplicates)
        for decision in new_insights['decisions']:
            if decision not in intelligence.key_decisions:
                intelligence.key_decisions.append(decision)
        
        # Keep only last 10 decisions to manage size
        if len(intelligence.key_decisions) > 10:
            intelligence.key_decisions = intelligence.key_decisions[-10:]
        
        # Add new actions (avoid duplicates)
        for action in new_insights['actions']:
            if action not in intelligence.action_items:
                intelligence.action_items.append(action)
        
        # Keep only last 10 actions
        if len(intelligence.action_items) > 10:
            intelligence.action_items = intelligence.action_items[-10:]
        
        # Update financial insights
        for key, value in new_insights['financial_data'].items():
            intelligence.financial_insights[key] = value
        
        # Add new topics
        for topic in new_insights['topics']:
            if topic not in intelligence.topics_discussed:
                intelligence.topics_discussed.append(topic)
    
    async def get_session_context(self, user_id: int, session_id: str) -> Dict:
        """
        Get previous context for a conversation session
        """
        intelligence = self.db.query(ChatIntelligence).filter(
            and_(
                ChatIntelligence.user_id == user_id,
                ChatIntelligence.session_id == session_id
            )
        ).first()
        
        if not intelligence:
            return {
                'has_context': False,
                'conversation_turns': 0,
                'topics': [],
                'context_summary': ''
            }
        
        # Build context summary
        context_parts = []
        
        if intelligence.key_decisions:
            context_parts.append(f"Previous recommendations: {'; '.join(intelligence.key_decisions[:3])}")
        
        if intelligence.action_items:
            context_parts.append(f"Pending actions: {'; '.join(intelligence.action_items[:3])}")
        
        if intelligence.topics_discussed:
            context_parts.append(f"Topics covered: {', '.join(intelligence.topics_discussed)}")
        
        if intelligence.last_intent:
            context_parts.append(f"Last focus: {intelligence.last_intent}")
        
        return {
            'has_context': True,
            'conversation_turns': intelligence.conversation_turns,
            'topics': intelligence.topics_discussed,
            'last_intent': intelligence.last_intent,
            'key_decisions': intelligence.key_decisions,
            'action_items': intelligence.action_items,
            'financial_insights': intelligence.financial_insights,
            'context_summary': '\n'.join(context_parts)
        }
    
    async def get_user_intelligence_summary(self, user_id: int, limit: int = 5) -> Dict:
        """
        Get a summary of user's recent intelligence across all sessions
        """
        recent_intelligence = self.db.query(ChatIntelligence).filter(
            ChatIntelligence.user_id == user_id
        ).order_by(desc(ChatIntelligence.updated_at)).limit(limit).all()
        
        if not recent_intelligence:
            return {'sessions': 0, 'total_insights': 0, 'top_topics': []}
        
        # Aggregate insights
        all_topics = []
        total_decisions = 0
        total_actions = 0
        
        for intel in recent_intelligence:
            all_topics.extend(intel.topics_discussed)
            total_decisions += len(intel.key_decisions)
            total_actions += len(intel.action_items)
        
        # Count topic frequency
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Sort topics by frequency
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'sessions': len(recent_intelligence),
            'total_insights': total_decisions + total_actions,
            'total_decisions': total_decisions,
            'total_actions': total_actions,
            'top_topics': [topic for topic, count in top_topics],
            'recent_sessions': [
                {
                    'session_id': intel.session_id,
                    'turns': intel.conversation_turns,
                    'topics': intel.topics_discussed,
                    'last_intent': intel.last_intent,
                    'updated_at': intel.updated_at.isoformat()
                }
                for intel in recent_intelligence
            ]
        }