"""
Clean Chat API Endpoints - Intent-Based Financial Advisory
Built from scratch with the new intent-based system
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import time
import structlog

from app.db.session import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user
from app.services.intent_service import IntentService, FinancialIntent
from app.services.vector_db_service import FinancialVectorDB
from app.services.prompt_builder_service import PromptBuilderService
from app.services.retirement_calculator import retirement_calculator
from app.services.complete_financial_context_service import CompleteFinancialContextService

logger = structlog.get_logger()
router = APIRouter()

# Pydantic Models
class ChatMessageRequest(BaseModel):
    user_id: int
    message: str
    session_id: str
    provider: str = 'gemini'
    model_tier: str = 'dev'
    include_context: bool = True
    insight_level: str = 'balanced'  # Options: 'focused', 'balanced', 'comprehensive'

class ChatMessageResponse(BaseModel):
    message: Dict[str, Any]
    tokens_used: Dict[str, int]
    cost_breakdown: Dict[str, float]
    suggested_questions: List[str]
    context_used: Optional[str] = None
    intent_detected: Optional[str] = None

# Initialize services
intent_service = IntentService()
vector_db = FinancialVectorDB()
prompt_builder = PromptBuilderService()

@router.get("/health")
async def chat_health():
    """Health check for chat system"""
    return {
        "status": "healthy",
        "service": "Intent-Based Chat API",
        "endpoints": ["/message", "/suggestions/{user_id}"],
        "system": "intent_based_advisory",
        "version": "2.0"
    }

def get_user_essentials(user_id: int, db: Session) -> Dict[str, Any]:
    """Get essential user data for context"""
    try:
        from app.models.user_profile import UserProfile
        
        # Get basic user info
        user = db.query(User).filter(User.id == user_id).first()
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        # Get financial summary using the financial summary service
        from app.services.financial_summary_service import financial_summary_service
        summary = financial_summary_service.get_user_financial_summary(user_id, db)
        
        essentials = {
            'name': f"{user.first_name} {user.last_name}".strip() if user and (user.first_name or user.last_name) else f"User {user_id}",
            'age': str(profile.age) if profile and profile.age else 'Unknown',
            'state': profile.state if profile and profile.state else 'Unknown',
            'net_worth': summary.get('netWorth', 0),
            'monthly_surplus': summary.get('monthlySurplus', 0),
            'risk_tolerance': profile.risk_tolerance if profile and profile.risk_tolerance else 'moderate'
        }
        
        logger.info(f"🎯 User essentials retrieved: {essentials['name']}, age {essentials['age']}, net worth ${essentials['net_worth']:,.0f}")
        return essentials
        
    except Exception as e:
        logger.warning(f"Failed to get user essentials: {str(e)}")
        return {
            'name': f"User {user_id}",
            'age': 'Unknown',
            'state': 'Unknown',
            'net_worth': 0,
            'monthly_surplus': 0,
            'risk_tolerance': 'moderate'
        }

async def call_llm_api(system_prompt: str, user_message: str, provider: str, model_tier: str, 
                      user_id: int, temperature: float = 0.1, force_json: bool = False, query: str = None) -> str:
    """Call LLM API with deterministic settings for no-math responses"""
    try:
        # Use the existing generate_llm_response function
        response = await call_real_llm_api(
            system_prompt=system_prompt,
            user_prompt=user_message,
            provider=provider,
            model_tier=model_tier,
            user_id=user_id,
            query=query
        )
        return response
        
    except Exception as e:
        logger.error(f"LLM API call failed: {str(e)}")
        return f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}"

async def call_real_llm_api(system_prompt: str, user_prompt: str, provider: str, model_tier: str, user_id: int = None, query: str = None) -> str:
    """Real LLM API calls using proper LLM service"""
    
    # Store payloads for debugging
    debug_payload = {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "provider": provider,
        "model_tier": model_tier,
        "user_id": user_id,
        "query": query,
        "timestamp": datetime.now().isoformat()
    }
    
    # Store for debugging (both global and debug endpoint)
    global last_llm_payload
    last_llm_payload = debug_payload
    
    # Also store in debug endpoint for frontend visibility
    if user_id:
        from app.api.v1.endpoints.debug import store_llm_payload
        store_llm_payload(user_id, debug_payload)
    
    try:
        # Use the proper LLM service instead of hardcoded implementations
        from ....services.llm_service import llm_service
        from ....models.llm_models import LLMRequest
        
        # Create proper LLM request
        llm_request = LLMRequest(
            provider=provider,
            model_tier=model_tier,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Call LLM service
        response = await llm_service.generate(llm_request)
        return response.content
            
    except Exception as e:
        logger.error(f"LLM API call failed for {provider}: {str(e)}")
        return f"❌ {provider.title()} API Error: {str(e)}"

def estimate_tokens(text: str) -> int:
    """Simple token estimation"""
    return int(len(text.split()) * 1.3)  # Rough approximation

def calculate_cost(input_tokens: int, output_tokens: int, provider: str, model_tier: str) -> Dict[str, float]:
    """Simple cost calculation"""
    # Simplified cost structure
    costs = {
        'gemini': {'dev': 0.001, 'prod': 0.002},
        'openai': {'dev': 0.002, 'prod': 0.004},
        'claude': {'dev': 0.003, 'prod': 0.006}
    }
    
    rate = costs.get(provider, costs['gemini']).get(model_tier, 0.001)
    total_cost = (input_tokens + output_tokens) * rate / 1000
    
    return {'total': total_cost}

def generate_suggestions() -> List[str]:
    """Generate suggested questions"""
    return [
        "What's my path to financial independence?",
        "Should I pay off debt or invest?",
        "How should I allocate my investments?",
        "What's my emergency fund status?",
        "How can I optimize my taxes?"
    ]

@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a message to the intent-based AI financial advisor
    """
    
    # Verify user access
    if current_user.id != request.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    try:
        # Capture timing for response quality metrics
        start_time = time.time()
        
        logger.info(f"🎯 Intent-based chat - User: {request.user_id}, Message: '{request.message}'")
        
        # Step 1: Detect financial intent first
        intent, search_terms, required_context = intent_service.detect_intent(request.message)
        logger.info(f"🎯 Intent detected: {intent.value}")
        
        # Step 2: Get COMPLETE financial context (RESTORE WORKING SYSTEM)
        from app.services.complete_financial_context_service import complete_financial_context
        
        # Build complete financial context (WORKING VERSION)
        system_prompt = complete_financial_context.build_complete_context(
            user_id=request.user_id, 
            db=db, 
            user_query=request.message,
            insight_level=request.insight_level
        )
        
        logger.info(f"🎯 Built complete context prompt: {len(system_prompt)} characters")
        
        # Step 3: Call LLM API with complete context as system prompt
        logger.info(f"🎯 Step 3: Calling LLM API...")
        response_content = await call_llm_api(
            system_prompt=system_prompt,
            user_message=request.message,  # ✅ FIXED: Pass the actual user question!
            provider=request.provider,
            model_tier=request.model_tier,
            user_id=request.user_id,
            temperature=0.1,  # Slight creativity for natural language
            force_json=False,  # Human-readable responses
            query=request.message  # Pass original user query for debugging
        )
        
        
        # RESPONSE QUALITY METRICS
        # ========================
        # Track key metrics for monitoring and optimization
        response_length = len(response_content) if response_content else 0
        response_time_ms = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
        
        # TESTING: Simple print to verify code execution
        print(f"🔍 RESPONSE METRICS: User {current_user.id}, Length: {response_length}, Time: {response_time_ms:.1f}ms")
        
        # Log metrics for analysis (structured)
        logger.info("Chat metrics", user_id=current_user.id, response_length=response_length, response_time_ms=f"{response_time_ms:.1f}")
        
        # Optional: Track if response mentions key metrics
        has_networth = '$' in response_content and 'worth' in response_content.lower()
        has_retirement = 'retirement' in response_content.lower() or 'goal' in response_content.lower()
        print(f"🔍 RESPONSE QUALITY: Has Net Worth: {has_networth}, Has Retirement: {has_retirement}")
        logger.info("Response quality", has_networth=has_networth, has_retirement=has_retirement, user_id=current_user.id)
        
        # Step 4: Validate response quality
        if 'Error loading' in system_prompt:
            logger.warning(f"Context loading error detected")
        
        # Ensure response uses specific financial data
        if len(response_content) < 200:
            logger.warning("Response too short - may not be using complete context")
        
        # Log successful generation
        logger.info(f"Professional report generated: {len(response_content)} chars")
        
        # Note: Conversation already stored immediately after LLM response above
        
        # Step 7: Calculate metrics
        input_tokens = int(estimate_tokens(system_prompt + request.message))
        output_tokens = int(estimate_tokens(response_content))
        total_tokens = input_tokens + output_tokens
        cost_breakdown = calculate_cost(input_tokens, output_tokens, request.provider, request.model_tier)
        
        # Step 8: Build response
        message = {
            "id": f"msg_{uuid.uuid4()}",
            "content": response_content,
            "role": "assistant",
            "timestamp": datetime.now().isoformat(),
            "provider": request.provider,
            "model": f"{request.provider}-{request.model_tier}",
            "session_id": request.session_id
        }
        
        # Context summary for debugging
        context_summary = f"Intent: {intent.value} | Complete context: ESSENTIAL + FINANCIAL HEALTH"
        
        logger.info(f"🎯 Response generated: {output_tokens} tokens, ${cost_breakdown['total']:.4f}")
        
        return ChatMessageResponse(
            message=message,
            tokens_used={
                "input": input_tokens,
                "output": output_tokens,
                "total": total_tokens
            },
            cost_breakdown=cost_breakdown,
            suggested_questions=generate_suggestions(),
            context_used=context_summary,
            intent_detected=intent.value
        )
        
    except Exception as e:
        logger.error(f"Chat message failed for user {request.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@router.get("/suggestions/{user_id}")
async def get_chat_suggestions(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get contextual chat suggestions"""
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "suggestions": generate_suggestions(),
        "categories": {
            "retirement": ["Am I on track for retirement?", "Should I contribute more to my 401k?"],
            "debt": ["Should I pay off my mortgage early?", "What's the best debt payoff strategy?"],
            "investment": ["How should I allocate my portfolio?", "Should I rebalance?"],
            "budget": ["Where is my money going?", "How can I save more?"],
            "tax": ["How can I reduce my taxes?", "Should I do Roth conversions?"]
        }
    }


# NEW INTELLIGENT CHAT ENDPOINT
class IntelligentChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    provider: str = 'gemini'
    model_tier: str = 'dev'

class IntelligentChatResponse(BaseModel):
    message: Dict[str, Any]
    tokens_used: Dict[str, int]
    cost_breakdown: Dict[str, float]
    intelligence_metrics: Dict[str, Any]
    suggested_questions: List[str]
    conversation_context: Dict[str, Any]


@router.post("/intelligent", response_model=IntelligentChatResponse)
async def chat_with_intelligence(
    request: IntelligentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Enhanced chat endpoint with intelligence extraction for vector store sync
    """
    
    start_time = time.time()
    
    try:
        # Generate session_id if not provided
        if not request.session_id:
            request.session_id = f"session_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        # Initialize services
        from app.services.chat_memory_service import ChatMemoryService
        from app.services.chat_intelligence_service import ChatIntelligenceService
        
        memory_service = ChatMemoryService(db)
        intelligence_service = ChatIntelligenceService(db)
        
        # Get or create chat session
        session = memory_service.get_or_create_session(
            user_id=current_user.id,
            session_id=request.session_id
        )
        
        # Get previous intelligence context
        intelligence_context = await intelligence_service.get_session_context(
            current_user.id, request.session_id
        )
        
        logger.info("Intelligence context loaded", 
                   has_context=intelligence_context['has_context'],
                   turns=intelligence_context['conversation_turns'])
        
        # Get conversation memory
        conversation_context = memory_service.get_conversation_context(session)
        
        # Enhanced intent detection
        from app.services.enhanced_intent_classifier import enhanced_intent_classifier
        detected_intents = enhanced_intent_classifier.classify_intents(request.message)
        primary_intent = enhanced_intent_classifier.get_primary_intent(detected_intents)
        
        # Vector-based context retrieval
        from app.services.vector_sync_service import vector_sync_service
        
        sync_result = vector_sync_service.sync_user_data(current_user.id, db)
        foundation_context = vector_sync_service.get_user_context(
            user_id=current_user.id,
            query=request.message,
            limit=3
        )
        
        # Build enhanced prompt with intelligence context
        enhanced_context_parts = [foundation_context]
        
        if intelligence_context['has_context']:
            intelligence_summary = intelligence_context['context_summary']
            enhanced_context_parts.insert(0, f"🧠 PREVIOUS CONVERSATION INTELLIGENCE:\n{intelligence_summary}\n")
        
        # Add conversation memory
        conversation_text = memory_service.format_context_for_prompt(conversation_context)
        if conversation_text:
            enhanced_context_parts.append(f"🧠 CONVERSATION MEMORY:\n{conversation_text}\n")
        
        enhanced_context_parts.append(f"\nUSER QUESTION: \"{request.message}\"\n\nIMPORTANT: Use the exact financial metrics provided above in your response.")
        
        optimized_context = '\n'.join(enhanced_context_parts)
        
        # Call LLM using the same approach as the working endpoint
        assistant_response = await call_llm_api(
            system_prompt=optimized_context,
            user_message=request.message,  # ✅ FIXED: Pass the actual user question!
            provider=request.provider,
            model_tier=request.model_tier,
            user_id=current_user.id,
            temperature=0.1,
            force_json=False,
            query=request.message
        )
        
        # Estimate tokens and cost
        input_tokens = int(estimate_tokens(optimized_context + request.message))
        output_tokens = int(estimate_tokens(assistant_response))
        total_tokens = input_tokens + output_tokens
        cost_breakdown = calculate_cost(input_tokens, output_tokens, request.provider, request.model_tier)
        
        # Process intelligence extraction
        intelligence_metrics = await intelligence_service.process_conversation_turn(
            user_id=current_user.id,
            session_id=request.session_id,
            user_message=request.message,
            ai_response=assistant_response
        )
        
        # Save conversation to memory
        memory_service.add_message_pair(
            session=session,
            user_message=request.message,
            assistant_response=assistant_response,
            intent_detected=primary_intent,
            context_used={
                "financial_data_included": bool(foundation_context and "Error loading" not in foundation_context),
                "conversation_context_included": bool(conversation_context.get("recent_messages")),
                "intelligence_context_included": intelligence_context['has_context']
            },
            tokens_used=total_tokens,
            model_used=request.model_tier,
            provider=request.provider
        )
        
        response_time = (time.time() - start_time) * 1000
        
        # Build enhanced conversation context
        conversation_response_context = {
            "message_count": conversation_context.get("message_count", 0) + 2,
            "session_summary": conversation_context.get("session_summary"),
            "last_intent": primary_intent,
            "response_time_ms": int(response_time),
            "conversation_turn": (conversation_context.get("message_count", 0) // 2) + 1,
            "intelligence_extracted": intelligence_metrics['insights_extracted'] > 0
        }
        
        # Build response message
        message = {
            "id": f"msg_{uuid.uuid4()}",
            "content": assistant_response,
            "role": "assistant",
            "timestamp": datetime.now().isoformat(),
            "provider": request.provider,
            "model": f"{request.provider}-{request.model_tier}",
            "session_id": request.session_id
        }
        
        return IntelligentChatResponse(
            message=message,
            tokens_used={
                "input": input_tokens,
                "output": output_tokens,
                "total": total_tokens
            },
            cost_breakdown=cost_breakdown,
            intelligence_metrics=intelligence_metrics,
            suggested_questions=generate_suggestions(),
            conversation_context=conversation_response_context
        )
        
    except Exception as e:
        logger.error("Intelligent chat failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intelligent chat processing failed: {str(e)}"
        )