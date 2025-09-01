"""
Simplified chat endpoint using insights architecture.
~100 lines replacing complex chat_with_memory.py
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.db.session import get_db
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.user import User
from app.services.identity_math import IdentityMath
from app.services.trust_engine import TrustEngine
from app.services.core_prompts import core_prompts
from app.services.llm_service import llm_service
from app.models.llm_models import LLMRequest
from app.services.chat_memory_service import ChatMemoryService

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

class ChatResponse(BaseModel):
    response: str
    confidence: str
    warnings: List[str] = []
    session_id: str

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Handle chat with financial intelligence and conversational memory"""
    logger.info(f"🚀 chat_simple endpoint hit with message: '{request.message}'")
    try:
        # Initialize memory service
        memory_service = ChatMemoryService(db)
        
        # Get or create chat session
        session = memory_service.get_or_create_session(
            user_id=current_user.id,
            session_id=request.session_id or f"simple_{current_user.id}_{int(__import__('time').time())}"
        )
        
        # Get conversation context
        conversation_context = memory_service.get_conversation_context(session)
        logger.info(f"💬 Conversation context: {conversation_context.get('message_count', 0)} messages")
        
        # Detect question type
        insight_type = _detect_insight_type(request.message)
        logger.info(f"🔍 Message: '{request.message}' -> Detected type: '{insight_type}'")
        
        if insight_type != "general_chat":
            # Financial question - use facts + LLM
            logger.info(f"🔬 Processing financial question with IdentityMath...")
            math = IdentityMath()
            facts = math.compute_claims(current_user.id, db)
            logger.info(f"📊 Got facts: {len(facts)} fields")
            
            if "error" in facts:
                logger.error(f"❌ IdentityMath error: {facts['error']}")
                return ChatResponse(
                    response="Please update your financial profile first.",
                    confidence="LOW",
                    warnings=["missing_data"],
                    session_id=request.session_id or "new"
                )
            
            # Search vector store for relevant context
            try:
                from app.services.simple_vector_store import SimpleVectorStore
                vector_store = SimpleVectorStore()
                
                # Search with financial keywords for broader results
                search_query = f"{request.message} financial goals income expenses assets retirement"
                search_results = vector_store.search(query=search_query, limit=5)
                
                vector_context_items = []
                logger.info(f"🔍 Vector search found {len(search_results)} results")
                
                for doc_id, score, doc in search_results:
                    # Check if document belongs to current user
                    if hasattr(doc, 'metadata') and doc.metadata.get('user_id') == current_user.id:
                        content = doc.content
                        if content:
                            # Truncate very long content
                            if len(content) > 500:
                                content = content[:500] + "..."
                            vector_context_items.append(f"- {content}")
                            logger.info(f"📄 Added doc {doc_id} (score: {score:.2f})")
                
                if vector_context_items:
                    vector_context = "\n".join(vector_context_items)
                    logger.info(f"📚 Vector context: {len(vector_context)} chars from {len(vector_context_items)} relevant docs")
                else:
                    vector_context = "No relevant historical context found for your user account."
                    logger.warning("📚 No user-specific documents found in vector search")
                    
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
                import traceback
                logger.error(f"Vector search traceback: {traceback.format_exc()}")
                vector_context = "Vector search unavailable."
            
            # Build prompt with facts + vector context
            prompt = core_prompts.format_prompt(
                prompt_type=insight_type,
                claims=facts,
                age=facts["_context"].get("age"),
                state=facts["_context"].get("state"),
                filing_status=facts["_context"].get("filing_status")
            )
            
            # Add conversation memory to foundation context
            conversation_text = memory_service.format_context_for_prompt(conversation_context)
            if conversation_text:
                enhanced_prompt = f"""🧠 CONVERSATION MEMORY:
{conversation_text}

{prompt}

RELEVANT CONTEXT FROM YOUR FINANCIAL HISTORY:
{vector_context}

INSTRUCTIONS: Use the above context to provide personalized, specific advice based on the user's actual financial history and conversation context, not generic recommendations.
"""
            else:
                enhanced_prompt = f"""
{prompt}

RELEVANT CONTEXT FROM YOUR FINANCIAL HISTORY:
{vector_context}

INSTRUCTIONS: Use the above context to provide personalized, specific advice based on the user's actual financial history and preferences, not generic recommendations.
"""
            
            # Get LLM response
            llm_request = LLMRequest(
                provider="openai",  # Default provider
                system_prompt="Financial advisor using provided facts and user's financial history",
                user_prompt=f"{enhanced_prompt}\n\nUser: {request.message}",
                temperature=0.3
            )
            response = await llm_service.generate(llm_request)
            
            # Validate
            engine = TrustEngine()
            validated = engine.validate(response.content, facts)
            
            # Save conversation to memory
            memory_service.add_message_pair(
                session=session,
                user_message=request.message,
                assistant_response=validated["response"],
                intent_detected=insight_type,
                context_used={
                    "financial_data_included": True,
                    "conversation_context_included": bool(conversation_context.get("recent_messages")),
                    "vector_context_included": bool(vector_context_items)
                },
                tokens_used=0,  # Simple endpoint doesn't track tokens
                model_used="openai",
                provider="openai"
            )
            
            return ChatResponse(
                response=validated["response"],
                confidence=validated["confidence"],
                warnings=facts.get("_warnings", []),
                session_id=session.session_id
            )
        else:
            # General chat
            logger.info(f"💬 Processing as general chat (no financial context)")
            llm_request = LLMRequest(
                provider="openai",  # Default provider
                system_prompt="Helpful assistant",
                user_prompt=request.message,
                temperature=0.7
            )
            response = await llm_service.generate(llm_request)
            
            # Save conversation to memory
            memory_service.add_message_pair(
                session=session,
                user_message=request.message,
                assistant_response=response.content,
                intent_detected="general_chat",
                context_used={
                    "financial_data_included": False,
                    "conversation_context_included": bool(conversation_context.get("recent_messages")),
                    "vector_context_included": False
                },
                tokens_used=0,
                model_used="openai",
                provider="openai"
            )
            
            return ChatResponse(
                response=response.content,
                confidence="HIGH",
                warnings=[],
                session_id=session.session_id
            )
            
    except Exception as e:
        logger.error(f"Chat error: {e}")
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
        'enough': 0.7, 'sufficient': 0.7, 'plan': 0.6, 'planning': 0.6
    }
    
    # General financial health indicators get routed to comprehensive analysis
    general_finance_words = {
        'financial health': 1.0, 'financial picture': 0.9, 'financial situation': 0.9,
        'net worth': 0.95, 'worth': 0.8, 'assets': 0.8, 'wealth': 0.8,
        'income': 0.7, 'expenses': 0.7, 'budget': 0.7, 'savings': 0.7,
        'debt': 0.8, 'liabilities': 0.8, 'emergency fund': 0.8,
        'how am i doing': 1.0, 'where do i stand': 0.9, 'status': 0.6,
        'overview': 0.7, 'summary': 0.7, 'assessment': 0.8, 'review': 0.7,
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