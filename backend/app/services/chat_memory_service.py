"""
Chat Memory Service - Enhanced with Universal Calculation Handler
Handles conversation history, session summaries, context management, and financial calculations
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json
import re
import structlog

from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.services.calculation_validator import calculation_validator
from app.services.formula_library import formula_library

logger = structlog.get_logger()


class ChatMemoryService:
    """
    Manages conversational memory for intelligent, context-aware responses
    
    Enhanced Features:
    - Store conversation history
    - Maintain rolling session summary  
    - Include last N message pairs in context
    - Track intent progression
    - Universal calculation handling with validation
    - Dynamic formula injection
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.max_history_messages = 10  # Keep last 5 exchanges (10 messages)
        self.max_context_messages = 6   # Include last 3 exchanges in prompt (6 messages)
        
        # Enhanced conversational advisor prompt for calculations
        self.ENHANCED_MATH_PROMPT = """
You are a warm, friendly financial advisor having a conversation with a client. When they ask calculation questions, help them think through it together.

## ANSWER-FIRST APPROACH:
For yes/no or direct questions, lead with the answer:
✅ "Yes, you can easily afford this. Here's why..."
✅ "Absolutely - you have more than enough. With your $2.8M..."
✅ "No, I'd recommend paying off debt first because..."
NOT: "[Long explanation]... therefore yes"

## CONVERSATIONAL STYLE:
- Start naturally but GET TO THE POINT quickly
- Give direct answers first, then explain
- Keep simple questions under 200 words when possible
- For complex questions, aim for under 300 words
- Weave calculations into natural sentences, not formal steps
- Connect results to their personal financial picture
- Use "you/your" (not "the user")

## AVOID ROBOTIC LANGUAGE:
❌ "Step 1: Calculate X"
❌ "IDENTIFY:", "EXTRACT:", "SHOW:"
❌ "Formula = Numbers"
❌ Pure mathematical notation without context
❌ Over-explaining simple questions

## RESPONSE STRUCTURE:
1. **Direct Answer** (first sentence)
2. **Quick Calculation** (if needed, woven naturally)
3. **Personal Context** (why this matters for them)
4. **Brief Insight** (one actionable takeaway)

## EXAMPLE TRANSFORMATIONS:

❌ WRONG (Over-explained):
"Let me help you figure this out. Looking at your expenses and using the 4% rule... [300 words]... therefore you need $2.4 million."

✅ RIGHT (Direct):
"Yes, you can absolutely afford retirement. With your $2.8 million portfolio, you're already above the $2.4 million needed for your $8,000 monthly expenses ($96K annually ÷ 4% = $2.4M). You're in great shape!"

## CALCULATION ACCURACY:
- Always show your math but weave it naturally into explanations
- Use proper currency formatting and rounding
- Explain assumptions clearly
- Put key results in **bold** for emphasis
- Give specific numbers, not vague ranges

## LOGICAL VALIDATION:
Before answering, check for obvious logical inconsistencies:
- If someone asks "Can I afford X?" and X is much smaller than their assets: Answer is YES
- If someone asks about impact and they have large surplus: Answer is MINIMAL impact
- If someone has significantly more than needed: Don't overthink, give direct positive answer
- Use common sense ratios and proportions from their actual data

Remember: Be direct, be helpful, be concise. Answer their question clearly first, then explain why.
"""
    
    def get_or_create_session(self, user_id: int, session_id: str) -> ChatSession:
        """Get existing session or create new one"""
        session = self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.session_id == session_id,
            ChatSession.is_active == True
        ).first()
        
        if not session:
            session = ChatSession(
                user_id=user_id,
                session_id=session_id,
                conversation_history=[],
                message_count=0,
                total_tokens_used=0
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            logger.info("Created new chat session", 
                       user_id=user_id, session_id=session_id, db_id=session.id)
        
        return session
    
    def add_message_pair(
        self, 
        session: ChatSession,
        user_message: str,
        assistant_response: str,
        intent_detected: Optional[str] = None,
        context_used: Optional[Dict] = None,
        tokens_used: int = 0,
        model_used: str = "gemini",
        provider: str = "gemini"
    ) -> None:
        """Add a user message + assistant response pair to the session"""
        
        # Convert enum to string value for database storage
        intent_str = intent_detected.value if hasattr(intent_detected, 'value') else intent_detected
        
        # Create individual message records
        user_msg = ChatMessage(
            session_id=session.id,
            user_id=session.user_id,
            role="user",
            content=user_message,
            intent_detected=intent_str
        )
        
        assistant_msg = ChatMessage(
            session_id=session.id,
            user_id=session.user_id,
            role="assistant", 
            content=assistant_response,
            intent_detected=intent_str,
            context_used=context_used,
            tokens_used=tokens_used,
            model_used=model_used,
            provider=provider
        )
        
        self.db.add(user_msg)
        self.db.add(assistant_msg)
        
        # Update session conversation history (lightweight for quick context)
        message_pair = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user_message,
            "assistant": assistant_response,
            "intent": intent_str,  # Use string value for JSON serialization
            "tokens": tokens_used
        }
        
        # Manage history size - keep only recent messages
        history = session.conversation_history or []
        history.append(message_pair)
        
        if len(history) > self.max_history_messages:
            # Remove oldest message pairs, keeping newest
            history = history[-self.max_history_messages:]
        
        # Update session
        session.conversation_history = history
        session.message_count += 2  # user + assistant
        session.total_tokens_used += tokens_used
        session.last_message_at = datetime.now(timezone.utc)
        session.last_intent = intent_str  # Use string value for database
        
        # Update session summary every few messages
        if session.message_count % 6 == 0:  # Every 3 exchanges
            session.session_summary = self._generate_session_summary(history)
            
        self.db.commit()
        
        logger.info("Added message pair to session", 
                   session_id=session.session_id,
                   message_count=session.message_count,
                   intent=intent_detected,
                   tokens=tokens_used)
    
    def get_conversation_context(self, session: ChatSession) -> Dict[str, Any]:
        """
        Build conversation context for the LLM prompt
        
        Returns:
            - recent_messages: Last N message pairs for immediate context
            - session_summary: High-level summary of what's been discussed
            - message_count: Total messages in session
            - last_intent: Most recent intent detected
        """
        # Refresh session from database to get latest conversation_history
        self.db.refresh(session)
        history = session.conversation_history or []
        
        # Get recent messages for immediate context
        recent_messages = history[-self.max_context_messages:] if history else []
        
        return {
            "recent_messages": recent_messages,
            "session_summary": session.session_summary,
            "message_count": session.message_count,
            "last_intent": session.last_intent,
            "total_tokens": session.total_tokens_used,
            "session_started": session.created_at.isoformat() if session.created_at else None
        }
    
    def _generate_session_summary(self, history: List[Dict]) -> str:
        """
        Generate a rolling summary of the conversation
        
        For Phase 1, this is a simple rule-based summary.
        Phase 2 can use an LLM to generate more sophisticated summaries.
        """
        if not history:
            return ""
        
        if len(history) <= 2:
            # Too early for a summary
            return ""
        
        # Extract intents and key topics
        intents = [msg.get("intent") for msg in history if msg.get("intent")]
        intent_counts = {}
        for intent in intents:
            if intent:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Build summary
        summary_parts = []
        
        if intent_counts:
            top_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:2]
            intent_names = [intent[0].replace("_", " ").title() for intent, _ in top_intents]
            summary_parts.append(f"Discussed: {', '.join(intent_names)}")
        
        summary_parts.append(f"Conversation has {len(history)} exchanges")
        
        if len(history) >= 3:
            summary_parts.append("Building on previous financial analysis")
        
        return ". ".join(summary_parts) + "."
    
    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format conversation context for inclusion in LLM prompt
        
        This creates a concise context block that provides conversational continuity
        without overwhelming the prompt.
        """
        if not context or not context.get("recent_messages"):
            return ""
        
        context_parts = []
        
        # Session summary if available
        if context.get("session_summary"):
            context_parts.append(f"CONVERSATION CONTEXT: {context['session_summary']}")
        
        # Recent message history
        recent = context.get("recent_messages", [])[-4:]  # Last 2 exchanges max
        if recent:
            context_parts.append("RECENT DISCUSSION:")
            for msg in recent:
                user_text = msg.get("user", "")[:100]  # Truncate long messages
                assistant_text = msg.get("assistant", "")[:150]
                context_parts.append(f"User: {user_text}")
                context_parts.append(f"Assistant: {assistant_text}")
        
        # Current context stats
        if context.get("message_count", 0) > 2:
            context_parts.append(f"[This is message #{context.get('message_count', 0) // 2 + 1} in our conversation]")
        
        return "\n".join(context_parts)
    
    def clear_session(self, session_id: str, user_id: int) -> bool:
        """Clear/deactivate a chat session"""
        session = self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
            logger.info("Cleared chat session", session_id=session_id, user_id=user_id)
            return True
        
        return False
    
    def get_user_sessions(self, user_id: int, limit: int = 10) -> List[ChatSession]:
        """Get recent chat sessions for a user"""
        return self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        ).order_by(ChatSession.updated_at.desc()).limit(limit).all()
    
    # ===== ENHANCED CALCULATION METHODS =====
    
    def requires_calculation(self, message: str) -> bool:
        """Detect if message needs financial calculations - AGGRESSIVE MODE"""
        calculation_triggers = [
            'how much', 'how many', 'when can', 'calculate', 'what is',
            'years to', 'need for', '%', 'percent', 'rule', 'ratio',
            'compare', 'difference', 'total', 'amount', 'worth', 'value',
            'retire', '4%', 'fire', 'payoff', 'pay off', 'savings rate',
            'compound', 'interest', 'return', 'growth', 'future value',
            'present value', 'annualized', 'monthly', 'annual', 'portfolio',
            'save', 'reach', 'versus', 'vs', 'or', 'better', 'achieve',
            'difference between', 'if i', 'can i', 'should i', 'will i'
        ]
        
        message_lower = message.lower()
        
        # Check for ANY numerical question indicators
        has_number = any(char.isdigit() for char in message)
        has_dollar = '$' in message
        has_calculation_word = any(trigger in message_lower for trigger in calculation_triggers)
        
        # Be aggressive - if it mentions numbers OR money OR calculation words
        return has_calculation_word or has_number or has_dollar
    
    def enhance_context_with_calculations(self, context: str, message: str, user_data: Dict) -> Tuple[str, bool]:
        """
        Enhance context with calculation capabilities if needed
        ALWAYS includes user's actual financial data for consistency
        
        Returns:
            Tuple[enhanced_context, is_calculation_mode]
        """
        # ALWAYS prepend user's actual financial data to ensure visibility
        from ..utils.safe_conversion import safe_float
        
        # Extract and format user's financial data
        monthly_income = safe_float(user_data.get('monthly_income'), 0)
        monthly_expenses = safe_float(user_data.get('monthly_expenses'), 0)
        monthly_savings = monthly_income - monthly_expenses if monthly_income > 0 else 0
        net_worth = safe_float(user_data.get('net_worth'), 0)
        portfolio_value = safe_float(user_data.get('investment_total') or user_data.get('total_assets'), 0)
        
        # MANDATORY data prefix - ALWAYS include
        data_context = f"""
🔢 USER'S ACTUAL FINANCIAL DATA (ALWAYS USE THESE EXACT NUMBERS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Portfolio Value: ${portfolio_value:,.0f}
• Monthly Income: ${monthly_income:,.0f}
• Monthly Expenses: ${monthly_expenses:,.0f}
• Monthly Savings: ${monthly_savings:,.0f}
• Net Worth: ${net_worth:,.0f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT: You HAVE access to the user's complete financial data above. 
Never ask for data that's already provided. Use these exact numbers in calculations.
"""
        
        # Check if calculation is needed
        is_calculation_mode = self.requires_calculation(message)
        
        if is_calculation_mode:
            logger.info("Calculation mode ACTIVATED", 
                       message_preview=message[:100],
                       portfolio_value=portfolio_value,
                       has_numbers=any(char.isdigit() for char in message))
            
            # For calculations, use enhanced prompt with lower temperature guidance
            enhanced_context = data_context + "\n" + self.ENHANCED_MATH_PROMPT
            
            # Add specific calculation notice
            enhanced_context = f"""
⚠️ CALCULATION REQUIRED: This question requires mathematical computation.
{enhanced_context}

MANDATORY: You MUST show calculations step-by-step using the user's actual data above.
"""
            
            # Add relevant formulas based on message content
            calculation_context = formula_library.create_calculation_context(message, user_data)
            enhanced_context += "\n\n" + calculation_context
            
            return enhanced_context, True
        else:
            # Even for non-calculation queries, include the data for reference
            return data_context + "\n" + context, False
    
    def validate_response_calculations(self, response: str, message: str) -> Dict:
        """
        Validate mathematical calculations in the response
        
        Returns validation results with any errors found
        """
        try:
            validation = calculation_validator.validate_math(response)
            
            if not validation['valid'] and validation['calculation_count'] > 0:
                logger.warning(
                    "Calculation errors detected",
                    message_preview=message[:100],
                    errors=validation['errors'],
                    accuracy_rate=validation['accuracy_rate']
                )
            
            return validation
            
        except Exception as e:
            logger.error("Calculation validation failed", error=str(e))
            return {
                'valid': True,  # Don't block response on validation failure
                'errors': [],
                'calculation_count': 0,
                'validation_error': str(e)
            }
    
    def validate_response_logic(self, response: str, message: str, user_data: Dict) -> Dict:
        """
        Validate logical consistency of responses against user's actual financial situation
        Works for any user with any values - no hardcoding
        """
        try:
            from ..utils.safe_conversion import safe_float
            import re
            
            # Extract user's financial position
            portfolio_value = safe_float(user_data.get('investment_total') or user_data.get('total_assets'), 0)
            net_worth = safe_float(user_data.get('net_worth'), 0)
            monthly_savings = safe_float(user_data.get('monthly_income', 0) - user_data.get('monthly_expenses', 0), 0)
            
            # Extract any dollar amounts mentioned in the question
            dollar_amounts = re.findall(r'\$?([\d,]+(?:,\d{3})*(?:\.\d{2})?)', message)
            amounts = []
            for amount_str in dollar_amounts:
                try:
                    amount = safe_float(amount_str.replace(',', ''), 0)
                    if amount > 0:
                        amounts.append(amount)
                except:
                    continue
            
            # Check for logical inconsistencies
            issues = []
            
            # Check 1: "Can I afford" questions
            if any(phrase in message.lower() for phrase in ['can i afford', 'will i have enough', 'do i have enough']):
                if amounts and portfolio_value > 0:
                    max_requested = max(amounts)
                    # If they have significantly more than requested, answer should be positive
                    if portfolio_value >= max_requested * 5:  # 5x buffer for safety
                        if response.strip().lower().startswith('no'):
                            issues.append(f"Logic error: User has ${portfolio_value:,.0f} but response says 'No' to ${max_requested:,.0f} request")
            
            # Check 2: Timeline questions with large surpluses
            if any(phrase in message.lower() for phrase in ['timeline', 'when can', 'how long']):
                if amounts and portfolio_value > 0:
                    requested = max(amounts) if amounts else 0
                    if portfolio_value >= requested * 2:  # Already have 2x what they need
                        if any(phrase in response.lower() for phrase in ['many years', 'long time', 'difficult']):
                            issues.append(f"Logic error: User already has ${portfolio_value:,.0f}, close to or exceeding ${requested:,.0f}")
            
            # Check 3: Impact questions with small relative amounts
            if any(phrase in message.lower() for phrase in ['impact', 'what happens if', 'affect']):
                if amounts and portfolio_value > 0:
                    impact_amount = max(amounts)
                    # If impact is less than 5% of portfolio, should be minimal
                    if impact_amount < portfolio_value * 0.05:
                        if any(phrase in response.lower() for phrase in ['significant', 'major', 'substantial']):
                            issues.append(f"Logic error: ${impact_amount:,.0f} impact on ${portfolio_value:,.0f} portfolio should be minimal")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'portfolio_value': portfolio_value,
                'requested_amounts': amounts,
                'validation_type': 'logical_consistency'
            }
            
        except Exception as e:
            logger.error(f"Logic validation failed: {str(e)}")
            return {
                'valid': True,  # Don't block response on validation failure
                'issues': [],
                'validation_error': str(e)
            }
    
    def create_calculation_correction_prompt(self, original_response: str, errors: List[Dict]) -> str:
        """Create a correction prompt for calculation errors"""
        corrections = []
        for error in errors[:3]:  # Limit to first 3 errors
            correction = calculation_validator.suggest_correction(error)
            corrections.append(correction)
        
        correction_prompt = f"""
The previous response contained calculation errors. Please provide a corrected version:

ERRORS FOUND:
{chr(10).join('• ' + c for c in corrections)}

ORIGINAL RESPONSE:
{original_response}

Please provide the corrected response with accurate calculations.
"""
        
        return correction_prompt