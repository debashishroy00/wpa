"""
Simplified chat endpoint using insights architecture.
~100 lines replacing complex chat_with_memory.py
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import json

from app.db.session import get_db
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.user import User
from app.services.trust_engine import TrustEngine
from app.services.llm_service import llm_service
from app.models.llm_models import LLMRequest
from app.services.vector_chat_memory_service import vector_chat_memory_service
from app.api.v1.endpoints.debug import store_llm_payload

logger = logging.getLogger(__name__)
router = APIRouter()


# Initialize LLM service with clients on first import
try:
    from app.services.llm_service import llm_service
    from app.services.llm_clients.openai_client import OpenAIClient
    from app.core.config import settings
    
    # Register OpenAI client if API key is available
    if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
        openai_client = OpenAIClient(llm_service.providers["openai"])
        llm_service.register_client("openai", openai_client)
        logger.info("OpenAI client registered for chat_simple")
    
    # Try Gemini client
    try:
        from app.services.llm_clients.gemini_client import GeminiClient
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            gemini_client = GeminiClient(llm_service.providers["gemini"])
            llm_service.register_client("gemini", gemini_client)
            logger.info("Gemini client registered for chat_simple")
    except ImportError:
        logger.info("Gemini client not available")

except ImportError as e:
    logger.warning(f"LLM service initialization failed: {e}")
    llm_service = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    provider: str = 'gemini'
    model_tier: str = 'dev'
    insight_level: str = 'balanced'  # direct, balanced, comprehensive

class ChatResponse(BaseModel):
    response: str
    confidence: str
    warnings: List[str] = []
    session_id: str
    calculation_id: Optional[str] = None
    calc_type: Optional[str] = None
    is_clarify: bool = False
    clarify: Optional[Dict[str, Any]] = None


def _format_context_for_prompt(conversation_context: Dict[str, Any]) -> str:
    """
    Format conversation context for LLM prompt
    """
    try:
        context_parts = []
        
        # Add session summary
        if conversation_context.get("session_summary"):
            context_parts.append(f"Conversation Summary: {conversation_context['session_summary']}")
        
        # Add recent conversation
        recent_conversation = conversation_context.get("recent_conversation", [])
        if recent_conversation:
            context_parts.append("Recent Conversation:")
            for turn in recent_conversation[-3:]:  # Last 3 turns
                user_msg = turn.get("user_message", "")[:100]  # Truncate for prompt
                ai_msg = turn.get("ai_response", "")[:100]
                context_parts.append(f"User: {user_msg}")
                context_parts.append(f"Assistant: {ai_msg}")
        
        # Add key topics
        key_topics = conversation_context.get("key_topics", [])
        if key_topics:
            context_parts.append(f"Discussion Topics: {', '.join(key_topics)}")
        
        return "\n".join(context_parts) if context_parts else ""
        
    except Exception as e:
        logger.error(f"Failed to format conversation context: {e}")
        return ""


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Handle chat with financial intelligence and conversational memory"""
    logger.info(f"🚀 chat_simple hit: '{request.message}'")
    logger.info(f"🎛️ mode: {request.insight_level}")
    try:
        # Initialize vector-based memory service (no database dependencies)
        persistent_session_id = f"simple_default_{current_user.id}"
        if request.session_id and request.session_id != persistent_session_id:
            logger.warning(f"Frontend provided session_id {request.session_id}, forcing persistent session {persistent_session_id} for memory continuity")
        
        # Get or create session using vector store
        session = vector_chat_memory_service.get_or_create_session(
            user_id=current_user.id,
            session_id=persistent_session_id
        )
        logger.info(f"🔗 Using vector-based session: {persistent_session_id}")
        
        # Get conversation context from vector store
        conversation_context = vector_chat_memory_service.get_conversation_context(session)
        logger.info("Vector chat memory context loaded", 
                   user_id=current_user.id,
                   session_id=persistent_session_id,
                   message_count=conversation_context.get("message_count", 0),
                   last_intent=conversation_context.get("last_intent"),
                   has_summary=bool(conversation_context.get("session_summary")))
        
        # Detect question type (rough intent)
        insight_type = _detect_insight_type(request.message)
        logger.info(f"🔍 Message: '{request.message}' -> Detected type: '{insight_type}'")

        # ALWAYS get complete financial context FIRST for financial questions
        complete_context = None
        context_facts = {}
        conversation_text = None
        
        if insight_type != "general_chat":
            logger.info(f"📊 Getting complete financial context FIRST...")
            try:
                from app.services.complete_financial_context_service import CompleteFinancialContextService
                
                # Step 1: Get complete financial context (WITHOUT memory first)
                context_service = CompleteFinancialContextService()
                foundation_context = context_service.build_complete_context(
                    user_id=current_user.id,
                    db=db,
                    user_query=request.message,
                    insight_level=request.insight_level
                )
                
                # Add user question to context (from working implementation)
                foundation_context = f"{foundation_context}\n\nUSER QUESTION: \"{request.message}\"\n\nIMPORTANT: Use the exact financial metrics provided above in your response."
                
                # Step 2: Add conversation memory to foundation context
                conversation_text = _format_context_for_prompt(conversation_context)
                
                # CRITICAL DEBUGGING - Force logging even at WARNING level
                print(f"MEMORY DEBUG - conversation_context keys: {list(conversation_context.keys())}")
                print(f"MEMORY DEBUG - recent_messages count: {len(conversation_context.get('recent_messages', []))}")
                print(f"MEMORY DEBUG - session message_count: {conversation_context.get('message_count', 0)}")
                print(f"MEMORY DEBUG - conversation_text length: {len(conversation_text) if conversation_text else 0}")
                
                if conversation_context.get('recent_messages'):
                    print(f"MEMORY DEBUG - first recent message: {conversation_context['recent_messages'][0] if conversation_context['recent_messages'] else 'EMPTY'}")
                
                logger.error("FORCE MEMORY DEBUG - conversation_context", extra=conversation_context)
                logger.error(f"FORCE MEMORY DEBUG - formatted text length: {len(conversation_text) if conversation_text else 0}")
                
                if conversation_text:
                    complete_context = f"""🧠 CONVERSATION MEMORY:
{conversation_text}

{foundation_context}"""
                    print(f"MEMORY SUCCESS - Enhanced context with {len(conversation_text)} chars of memory")
                else:
                    complete_context = foundation_context
                    print(f"MEMORY FAILURE - No conversation memory available, using foundation only")
                
                # Extract key facts from complete context for validation
                import re
                if complete_context:
                    # Core metrics
                    nw_match = re.search(r'Net Worth:\s*\$?([\d,]+)', complete_context)
                    if nw_match:
                        context_facts["net_worth"] = nw_match.group(1).replace(',', '')
                    
                    assets_match = re.search(r'Total Assets:\s*\$?([\d,]+)', complete_context)
                    if assets_match:
                        context_facts["total_assets"] = assets_match.group(1).replace(',', '')
                    
                    liab_match = re.search(r'Total Liabilities:\s*\$?([\d,]+)', complete_context)
                    if liab_match:
                        context_facts["total_liabilities"] = liab_match.group(1).replace(',', '')
                    
                    # Cash flow
                    income_match = re.search(r'Monthly Income:\s*\$?([\d,]+)', complete_context)
                    if income_match:
                        context_facts["monthly_income"] = income_match.group(1).replace(',', '')
                    
                    expense_match = re.search(r'Monthly Expenses:\s*\$?([\d,]+)', complete_context)
                    if expense_match:
                        context_facts["monthly_expenses"] = expense_match.group(1).replace(',', '')
                    
                    surplus_match = re.search(r'Monthly Surplus:\s*\$?([\d,]+)', complete_context)
                    if surplus_match:
                        context_facts["monthly_surplus"] = surplus_match.group(1).replace(',', '')
                    
                    savings_match = re.search(r'Savings Rate:\s*([\d.]+)%', complete_context)
                    if savings_match:
                        context_facts["savings_rate"] = savings_match.group(1)
                    
                    # Asset allocation
                    re_match = re.search(r'Real Estate:\s*([\d.]+)%', complete_context)
                    if re_match:
                        context_facts["real_estate_allocation"] = re_match.group(1)
                    
                    re_amt_match = re.search(r'Real Estate.*?\$?([\d,]+)', complete_context)
                    if re_amt_match:
                        context_facts["real_estate_amount"] = re_amt_match.group(1).replace(',', '')
                    
                    inv_match = re.search(r'Investments:\s*([\d.]+)%', complete_context)
                    if inv_match:
                        context_facts["investment_allocation"] = inv_match.group(1)
                    
                    inv_amt_match = re.search(r'Investments.*?\$?([\d,]+)', complete_context)
                    if inv_amt_match:
                        context_facts["investment_amount"] = inv_amt_match.group(1).replace(',', '')
                    
                    ret_match = re.search(r'Retirement.*?(\d+[\d,]*)', complete_context)
                    if ret_match:
                        context_facts["retirement_amount"] = ret_match.group(1).replace(',', '')
                    
                    cash_match = re.search(r'Cash.*?\$?([\d,]+)', complete_context)
                    if cash_match:
                        context_facts["cash_amount"] = cash_match.group(1).replace(',', '')
                    
                    # Goals
                    retirement_match = re.search(r'Retirement Goal:\s*\$?([\d,]+)', complete_context)
                    if retirement_match:
                        context_facts["retirement_goal"] = retirement_match.group(1).replace(',', '')
                    
                    progress_match = re.search(r'progress.*?([\d.]+)%', complete_context)
                    if progress_match:
                        context_facts["retirement_progress"] = progress_match.group(1)
                    
                    years_match = re.search(r'([\d.]+)\s*years.*?goal', complete_context)
                    if years_match:
                        context_facts["years_to_goal"] = years_match.group(1)
                
                # Filter out None values
                context_facts = {k: v for k, v in context_facts.items() if v is not None}
                
                logger.info(f"✅ Complete context loaded: {len(complete_context)} chars, Real Estate: {context_facts.get('real_estate_allocation', 'N/A')}%, Expenses: ${context_facts.get('monthly_expenses', 'N/A')}")
                    
            except Exception as e:
                logger.error(f"❌ Complete context failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Try AgenticRAG but pass the complete context to it
        use_agentic_rag = False  # Temporarily disable AgenticRAG until we can pass context to it
        
        if use_agentic_rag:
            try:
                logger.info(f"🤖 Using Agentic RAG with complete context...")
                # TODO: Modify AgenticRAG to accept and use complete_context
                pass
            except Exception as e:
                logger.error(f"❌ Agentic RAG failed: {e}, using direct LLM")
                # Continue to use direct LLM with complete context
        
        if insight_type != "general_chat":
            # Financial question - use pre-loaded COMPLETE context
            logger.info(f"🔬 Using pre-loaded complete financial context...")
            
            if complete_context:
                vector_context = str(complete_context)
                vector_context_items = [complete_context]
                logger.info(f"📊 Using complete context: {len(vector_context)} chars")
            else:
                vector_context = "Complete financial context unavailable."
                vector_context_items = []
                logger.error("❌ No complete context available")
            
            # Build prompt using COMPLETE context (conversation memory already included)
            enhanced_prompt = f"""You are a financial advisor with access to COMPLETE FINANCIAL CONTEXT
for {current_user.first_name}'s financial situation.

Use the complete financial data provided to give accurate, specific answers.
Reference specific numbers from the context in every response.

COMPLETE FINANCIAL CONTEXT (USE THIS AS PRIMARY DATA SOURCE):
{vector_context}

CRITICAL INSTRUCTIONS:
1. Use ONLY the specific data from the COMPLETE FINANCIAL CONTEXT above  
2. Reference exact dollar amounts and percentages from the context
3. Do NOT give generic advice - use the user's actual financial numbers
4. If real estate allocation is mentioned, use the percentage from the complete context
5. Build on previous conversation context when relevant (conversation history is included in the context above)
"""
            
            # Get LLM response
            # Choose a working provider if the requested one isn't registered
            chosen_provider = request.provider
            try:
                available = list(llm_service.clients.keys())
                if chosen_provider not in available and available:
                    # Prefer the original default order
                    for p in [request.provider, 'gemini', 'openai', 'claude']:
                        if p in available:
                            chosen_provider = p
                            break
            except Exception:
                pass

            # Map insight levels to LLM modes
            llm_mode_map = {
                "focused": "direct",
                "balanced": "balanced", 
                "comprehensive": "comprehensive"
            }
            llm_mode = llm_mode_map.get(request.insight_level, "balanced")
            
            # Override system prompt for stress testing questions
            stress_test_keywords = ['crash', 'drop', 'decline', 'lose', 'market down', 'recession', 'bear market']
            is_stress_test = any(keyword in request.message.lower() for keyword in stress_test_keywords)
            
            if is_stress_test:
                system_prompt = """You are a financial calculator that MUST perform calculations with the data provided.
                
CRITICAL OVERRIDE: For market crash/stress test questions, you HAVE ALL DATA NEEDED.
- Current investments: Use the investment amounts in the context
- Current real estate: Use the real estate amounts in the context  
- NEVER say "need more information" - calculate with the provided numbers
- ALWAYS show step-by-step arithmetic calculations
- Be decisive with specific recovery timelines"""
            else:
                system_prompt = "Financial advisor using the COMPLETE FINANCIAL CONTEXT and conversation memory."
            
            llm_request = LLMRequest(
                provider=chosen_provider,
                model_tier=request.model_tier,
                system_prompt=system_prompt,
                user_prompt=f"{enhanced_prompt}\n\nUser: {request.message}",
                mode=llm_mode
                # Temperature will be set by LLM service based on mode
            )
            response = await llm_service.generate(llm_request)
            
            # CRITICAL FIX: Store memory IMMEDIATELY after LLM response to fix timing issue
            print(f"TIMING FIX - Storing memory IMMEDIATELY after LLM response")
            vector_chat_memory_service.add_message_pair(
                user_id=current_user.id,
                user_message=request.message,
                ai_response=response.content,
                intent=insight_type
            )
            
            # Validate response specificity using pre-extracted context facts
            validation_score = _validate_response_specificity(
                response.content, context_facts, vector_context
            )
            logger.info(f"🔍 Response validation score: {validation_score['score']}/10")
            
            # Store enhanced LLM payload for debugging with validation data
            store_llm_payload(current_user.id, {
                "query": request.message,
                "provider": request.provider,
                "model_tier": request.model_tier,
                "insight_level": request.insight_level,
                "system_prompt": "Financial advisor using provided facts and user's financial history",
                "user_message": f"{enhanced_prompt}\n\nUser: {request.message}",
                "context_used": json.dumps({
                    "financial_data_included": True,
                    "conversation_context_included": bool(conversation_context.get("recent_messages")),
                    "vector_context_included": bool(vector_context_items),
                    "vector_context_items": len(vector_context_items) if vector_context_items else 0,
                    "facts_keys": list(context_facts.keys()) if context_facts else [],
                    "validation_score": validation_score['score'],
                    "validation_passed": validation_score['validation_passed'],
                    "complete_context_used": True,
                    "insight_level": request.insight_level
                }),
                "llm_response": response.content if hasattr(response, 'content') else str(response),
                "validation_details": validation_score
            })
            
            # Validate using complete context facts
            engine = TrustEngine()
            validated = engine.validate(response.content, context_facts or {})
            
            # Store chat interaction in vector store for future memory
            _store_chat_interaction(current_user.id, request.message, validated["response"], context_facts or {})
            
            # Memory is now stored immediately after LLM response (line 264-280) - no duplicate needed
            
            logger.info("Conversation saved to memory",
                       session_id=session.get("session_id"),
                       new_message_count=session.get("message_count"),
                       intent_detected=insight_type,
                       memory_context_included=bool(conversation_context.get("recent_messages")))
            
            return ChatResponse(
                response=validated["response"],
                confidence=validated["confidence"],
                warnings=validation_score.get("issues", []),
                session_id=session.get("session_id")
            )
        else:
            # General chat
            logger.info(f"💬 Processing as general chat (no financial context)")
            # Choose a working provider for general chat as well
            chosen_provider = request.provider
            try:
                available = list(llm_service.clients.keys())
                if chosen_provider not in available and available:
                    for p in [request.provider, 'gemini', 'openai', 'claude']:
                        if p in available:
                            chosen_provider = p
                            break
            except Exception:
                pass

            # Map insight levels to LLM modes for general chat
            llm_mode_map = {
                "focused": "direct",
                "balanced": "balanced", 
                "comprehensive": "comprehensive"
            }
            llm_mode = llm_mode_map.get(request.insight_level, "balanced")
            
            # Include conversation memory in general chat too
            if conversation_text:
                enhanced_prompt = f"""Previous conversation context:
{conversation_text}

Current question: {request.message}

Please respond naturally building on the conversation context above."""
                print(f"GENERAL CHAT MEMORY - Enhanced prompt with {len(conversation_text)} chars of context")
            else:
                enhanced_prompt = request.message
                print(f"GENERAL CHAT MEMORY - No context available, using raw message")
            
            llm_request = LLMRequest(
                provider=chosen_provider,
                model_tier=request.model_tier,
                system_prompt="You are a helpful assistant. Build on previous conversation context when provided.",
                user_prompt=enhanced_prompt,
                mode=llm_mode
                # Temperature will be set by LLM service based on mode
            )
            response = await llm_service.generate(llm_request)
            
            # Store LLM payload for debugging
            store_llm_payload(current_user.id, {
                "query": request.message,
                "provider": request.provider,
                "model_tier": request.model_tier,
                "system_prompt": "Helpful assistant",
                "user_message": request.message,
                "context_used": json.dumps({
                    "financial_data_included": False,
                    "conversation_context_included": False,
                    "vector_context_included": False,
                    "chat_type": "general_chat"
                }),
                "llm_response": response.content if hasattr(response, 'content') else str(response)
            })
            
            # Save conversation to memory (general chat)
            vector_chat_memory_service.add_message_pair(
                user_id=current_user.id,
                user_message=request.message,
                ai_response=response.content,
                intent="general_chat"
            )
            
            return ChatResponse(
                response=response.content,
                confidence="HIGH",
                warnings=[],
                session_id=session.get("session_id")
            )
            
    except Exception as e:
        import traceback
        logger.error(f"Chat error: {e}")
        logger.error(f"Chat error traceback: {traceback.format_exc()}")
        return ChatResponse(
            response="I couldn't process that. Please try again.",
            confidence="LOW",
            warnings=["error"],
            session_id=request.session_id or "new"
        )

def _detect_insight_type(message: str) -> str:
    """Detect question type with enhanced keyword matching and financial context"""
    msg = message.lower()
    
    # Enhanced weighted keywords for better categorization
    tax_words = {
        'tax': 1.0, 'taxes': 1.0, 'deduction': 1.0, 'deductions': 1.0,
        '401k': 0.95, '401(k)': 0.95, 'ira': 0.95, 'roth': 0.9,
        'contribution': 0.8, 'contributions': 0.8, 'withholding': 0.8,
        'optimize': 0.7, 'save on taxes': 1.0, 'tax efficiency': 1.0,
        'bracket': 0.9, 'marginal': 0.8, 'effective': 0.7
    }
    
    risk_words = {
        'risk': 1.0, 'risky': 0.9, 'volatility': 0.9, 'volatile': 0.9,
        'allocation': 0.95, 'diversify': 0.9, 'diversification': 0.9,
        'portfolio': 0.8, 'balance': 0.7, 'rebalance': 0.8,
        'conservative': 0.8, 'aggressive': 0.8, 'moderate': 0.7,
        'safe': 0.6, 'safety': 0.6, 'secure': 0.6
    }
    
    goal_words = {
        'retire': 1.0, 'retirement': 1.0, 'goal': 0.9, 'goals': 0.9,
        'fire': 1.0, 'target': 0.8, 'independence': 0.9, 'independent': 0.9,
        'ready': 0.7, 'on track': 0.9, 'progress': 0.8, 'timeline': 0.8,
        'enough': 0.7, 'sufficient': 0.7, 'plan': 0.6, 'planning': 0.6,
        'social security': 1.0, 'ss benefits': 0.95, 'benefits': 0.8
    }
    
    # General financial health indicators get routed to comprehensive analysis
    general_finance_words = {
        'financial health': 1.0, 'financial picture': 0.9, 'financial situation': 0.9,
        'finances': 0.95, 'financial': 0.8, 'complete finances': 1.0,
        'complete financial': 0.95, 'my finances': 0.9, 'show me my finances': 1.0,
        'net worth': 0.95, 'worth': 0.8, 'assets': 0.8, 'wealth': 0.8,
        'income': 0.7, 'expenses': 0.7, 'budget': 0.7, 'savings': 0.7,
        'debt': 0.8, 'liabilities': 0.8, 'emergency fund': 0.8,
        'how am i doing': 1.0, 'where do i stand': 0.9, 'status': 0.6,
        'overview': 0.7, 'summary': 0.7, 'complete': 0.6, 'full': 0.6,
        'assessment': 0.8, 'review': 0.7, 'show me': 0.5,
        'advice': 0.6, 'recommend': 0.6, 'suggestions': 0.6, 'help': 0.5
    }
    
    # Calculate scores with phrase matching for better accuracy
    scores = {
        'tax': _calculate_phrase_score(msg, tax_words),
        'risk': _calculate_phrase_score(msg, risk_words),
        'goals': _calculate_phrase_score(msg, goal_words),
        'general': _calculate_phrase_score(msg, general_finance_words)
    }
    
    # Find the highest scoring category
    best = max(scores, key=scores.get)
    
    # Minimum threshold to qualify as financial question
    if scores[best] >= 0.5:
        return best
    else:
        return "general_chat"

def _calculate_phrase_score(message: str, keyword_dict: dict) -> float:
    """Calculate weighted score for keywords/phrases in message"""
    total_score = 0.0
    for phrase, weight in keyword_dict.items():
        if phrase in message:
            total_score += weight
    return total_score

def _validate_response_specificity(response: str, facts: dict, context: str) -> dict:
    """Validate that response contains specific financial data, not generic advice"""
    validation_score = {
        "score": 0,
        "max_score": 10,
        "specific_numbers_found": 0,
        "generic_phrases_detected": 0,
        "facts_referenced": 0,
        "validation_passed": False,
        "issues": []
    }
    
    # Check for specific dollar amounts (high value)
    import re
    dollar_matches = re.findall(r'\$[\d,]+', response)
    validation_score["specific_numbers_found"] = len(dollar_matches)
    validation_score["score"] += min(len(dollar_matches) * 2, 6)  # Max 6 points for numbers
    
    # Check for percentage values
    percentage_matches = re.findall(r'\d+\.?\d*%', response)
    validation_score["score"] += min(len(percentage_matches), 2)  # Max 2 points for percentages
    
    # Penalize generic financial advice phrases
    generic_phrases = [
        'it depends', 'generally speaking', 'typically', 'usually',
        'you should consider', 'it might be wise', 'you may want to',
        'financial advisors often recommend', 'a common rule of thumb'
    ]
    
    for phrase in generic_phrases:
        if phrase.lower() in response.lower():
            validation_score["generic_phrases_detected"] += 1
            validation_score["score"] -= 1  # Penalty for generic advice
            validation_score["issues"].append(f"Generic phrase detected: '{phrase}'")
    
    # Check if key facts are referenced
    if facts:
        fact_keys = ['net_worth', 'monthly_income', 'monthly_expenses', 'retirement_goal', 'savings_rate']
        for key in fact_keys:
            if key in facts and str(facts[key]) in response:
                validation_score["facts_referenced"] += 1
    
    # Special reward for real estate allocation usage (critical fix from audit)
    real_estate_bonus = 0
    if facts and 'real_estate_allocation' in facts:
        real_estate_value = str(facts['real_estate_allocation'])
        if real_estate_value in response or f"{real_estate_value}%" in response:
            real_estate_bonus = 2  # Extra bonus for using real estate allocation
            validation_score["facts_referenced"] += 1
            validation_score["issues"].append(f"✅ Real estate allocation used: {real_estate_value}%")
    
    validation_score["score"] += validation_score["facts_referenced"] + real_estate_bonus  # Bonus for using facts
    
    # Determine if validation passed (adjusted thresholds)
    validation_score["validation_passed"] = (
        validation_score["score"] >= 4 and 
        validation_score["specific_numbers_found"] >= 1 and
        validation_score["generic_phrases_detected"] <= 2
    )
    
    if not validation_score["validation_passed"]:
        if validation_score["specific_numbers_found"] < 2:
            validation_score["issues"].append("Insufficient specific numbers (need at least 2)")
        if validation_score["generic_phrases_detected"] > 2:
            validation_score["issues"].append("Too many generic phrases")
        if validation_score["score"] < 5:
            validation_score["issues"].append(f"Overall score too low: {validation_score['score']}/10")
    
    return validation_score

def _store_chat_interaction(user_id: int, user_message: str, assistant_response: str, financial_facts: dict):
    """Store chat interaction in vector store for future memory and intelligence"""
    try:
        from app.services.simple_vector_store import get_vector_store
        import json
        from datetime import datetime
        
        vector_store = get_vector_store()
        
        # Store individual interaction
        interaction_id = f"user_{user_id}_chat_{int(datetime.now().timestamp())}"
        interaction_content = f"""User Question: {user_message}
        
Assistant Response: {assistant_response}
        
Financial Context: Net Worth: ${financial_facts.get('net_worth', 0):,.0f}, Monthly Income: ${financial_facts.get('monthly_income', 0):,.0f}"""
        
        vector_store.add_document(
            doc_id=interaction_id,
            content=interaction_content,
            metadata={
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "type": "chat_interaction",
                "user_message": user_message[:200],
                "assistant_response": assistant_response[:200]
            }
        )
        
        # Update or create user intelligence document
        intelligence_id = f"user_{user_id}_chat_intelligence"
        existing_intelligence = vector_store.get_document(intelligence_id)
        
        # Extract key information for intelligence
        intelligence_data = {
            "financial_decisions": [],
            "stated_preferences": [],
            "action_items": [],
            "last_updated": datetime.now().isoformat()
        }
        
        # Load existing intelligence if available
        if existing_intelligence and hasattr(existing_intelligence, 'content'):
            try:
                existing_data = json.loads(existing_intelligence.content)
                intelligence_data.update(existing_data)
            except json.JSONDecodeError:
                pass
        
        # Analyze current interaction for intelligence
        if any(word in user_message.lower() for word in ['buy', 'sell', 'invest', 'allocate']):
            decision = f"Considering: {user_message[:100]}"
            if decision not in intelligence_data["financial_decisions"]:
                intelligence_data["financial_decisions"].append(decision)
        
        if any(word in user_message.lower() for word in ['prefer', 'like', 'want', 'need']):
            preference = f"Preference: {user_message[:100]}"
            if preference not in intelligence_data["stated_preferences"]:
                intelligence_data["stated_preferences"].append(preference)
        
        if any(word in assistant_response.lower() for word in ['should', 'recommend', 'consider', 'next step']):
            action = f"Recommended: {assistant_response[:100]}"
            if action not in intelligence_data["action_items"]:
                intelligence_data["action_items"].append(action)
        
        # Keep only recent items (last 10)
        for key in ['financial_decisions', 'stated_preferences', 'action_items']:
            intelligence_data[key] = intelligence_data[key][-10:]
        
        # Store updated intelligence
        vector_store.add_document(
            doc_id=intelligence_id,
            content=json.dumps(intelligence_data),
            metadata={
                "user_id": user_id,
                "type": "chat_intelligence",
                "last_updated": intelligence_data["last_updated"]
            }
        )
        
        logger.info(f"💾 Chat interaction stored for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to store chat interaction: {str(e)}")
        # Don't fail the chat if storage fails
