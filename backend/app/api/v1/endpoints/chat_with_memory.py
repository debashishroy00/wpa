"""
Chat API with Memory - Phase 1: Conversational Continuity
Enhanced chat endpoint that maintains conversation history and context
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
from app.models.chat import ChatSession, ChatMessage
from app.api.v1.endpoints.auth import get_current_active_user
from app.services.chat_memory_service import ChatMemoryService
from app.services.chat_intelligence_service import ChatIntelligenceService
from app.services.complete_financial_context_service import CompleteFinancialContextService
from app.services.token_manager import token_manager
from app.services.enhanced_intent_classifier import enhanced_intent_classifier
# Basic calculations now handled by CompleteFinancialContextService and formula_library
from app.services.basic_response_verifier import BasicResponseVerifier
from app.services.retirement_response_formatter import retirement_formatter
# TaxOptimizationService removed - using TaxIntelligenceFormatter instead
from app.models.architecture_contracts import UserFinancialData, ToolsOutput

logger = structlog.get_logger()

# Initialize LLM service with clients on first import
try:
    from app.services.llm_service import llm_service
    from app.services.llm_clients.openai_client import OpenAIClient
    from app.core.config import settings
    
    # Register OpenAI client if API key is available
    if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
        openai_client = OpenAIClient(llm_service.providers["openai"])
        llm_service.register_client("openai", openai_client)
        logger.info("OpenAI client registered for chat memory")
    
    # Try Gemini client
    try:
        from app.services.llm_clients.gemini_client import GeminiClient
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            gemini_client = GeminiClient(llm_service.providers["gemini"])
            llm_service.register_client("gemini", gemini_client)
            logger.info("Gemini client registered for chat memory")
    except ImportError:
        logger.info("Gemini client not available")

except ImportError as e:
    logger.warning(f"LLM service initialization failed: {e}")
    llm_service = None

# Import existing services (adjust imports based on what's available)
# Intent service deprecated - using enhanced_intent_classifier

# Vector DB not used in primary chat flow

# Removed deprecated services

router = APIRouter()

# Deprecated: Helper functions moved to vector_sync_service.py for unified data flow

# MEMORY SYSTEM STATUS ENDPOINT
@router.get("/debug/memory-status/{user_id}")
async def check_memory_status(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """🔍 Check if chat memory system is actually being used"""
    try:
        memory_service = ChatMemoryService(db)
        
        # Get recent sessions for user
        sessions = memory_service.get_user_sessions(user_id, limit=5)
        
        if sessions:
            latest_session = sessions[0]
            conversation_context = memory_service.get_conversation_context(latest_session)
            
            # Check if context includes actual history
            conversation_text = memory_service.format_context_for_prompt(conversation_context)
            
            # Get actual messages from session
            from app.models.chat import ChatMessage
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == latest_session.id
            ).order_by(ChatMessage.created_at.desc()).limit(10).all()
            
            return {
                "memory_system_active": True,
                "total_sessions": len(sessions),
                "latest_session": {
                    "id": latest_session.session_id,
                    "message_count": latest_session.message_count,
                    "has_summary": bool(latest_session.session_summary),
                    "last_intent": latest_session.last_intent
                },
                "conversation_context": {
                    "recent_messages_count": len(conversation_context.get('recent_messages', [])),
                    "has_summary": bool(conversation_context.get('session_summary')),
                    "total_tokens": conversation_context.get('total_tokens', 0)
                },
                "formatted_context": {
                    "length": len(conversation_text) if conversation_text else 0,
                    "includes_history": "CONVERSATION MEMORY:" in conversation_text if conversation_text else False,
                    "preview": conversation_text[:300] + "..." if conversation_text and len(conversation_text) > 300 else conversation_text
                },
                "database_messages": [
                    {
                        "role": msg.role,
                        "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                        "created_at": msg.created_at.isoformat()
                    } for msg in messages[:5]
                ]
            }
        else:
            return {
                "memory_system_active": True,
                "total_sessions": 0,
                "issue": "No sessions found - memory not being used or sessions not persisting"
            }
            
    except Exception as e:
        return {
            "memory_system_active": False,
            "error": str(e),
            "diagnosis": "Memory system may not be initialized properly"
        }

# CRITICAL DEBUG ENDPOINT TO TRACE DATA PIPELINE FAILURE
@router.get("/debug/data-pipeline/{user_id}")
async def debug_data_pipeline(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """🚨 EMERGENCY DEBUG: Check why user data isn't reaching LLM"""
    try:
        logger.critical(f"🔍 DEBUGGING DATA PIPELINE FOR USER {user_id}")
        
        # Step 1: Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        user_exists = user is not None
        logger.critical(f"User exists in DB: {user_exists}")
        
        # Step 2: Check financial summary service
        from app.services.financial_summary_service import financial_summary_service
        financial_summary = financial_summary_service.get_user_financial_summary(user_id, db)
        logger.critical(f"Financial summary loaded: {financial_summary is not None}")
        logger.critical(f"Financial summary keys: {list(financial_summary.keys()) if financial_summary else 'None'}")
        
        # Step 3: Check complete financial context
        from app.services.complete_financial_context_service import complete_financial_context
        try:
            financial_context = complete_financial_context.build_complete_context(
                user_id=user_id,
                db=db,
                user_query="What is 4% of my portfolio?",
                insight_level="detailed"
            )
            context_has_data = len(financial_context) > 100
            context_has_portfolio = any(char.isdigit() for char in financial_context) and "$" in financial_context and not all(val == "0" for val in financial_context.split() if val.replace("$", "").replace(",", "").isdigit())
            logger.critical(f"Financial context length: {len(financial_context)}")
            logger.critical(f"Context has real portfolio data: {context_has_portfolio}")
        except Exception as e:
            financial_context = f"ERROR: {str(e)}"
            context_has_data = False
            context_has_portfolio = False
            logger.error(f"Financial context build failed: {str(e)}")
        
        # Step 4: Check session context service  
        from app.services.session_context_service import session_context_service
        session = session_context_service.get_or_create_session(user_id, f"debug_{int(time.time())}", db)
        context_dict = session_context_service.get_context_for_validation(f"debug_{int(time.time())}")
        session_has_data = bool(context_dict.get('net_worth', 0) > 0)
        logger.critical(f"Session context has real data: {session_has_data}")
        
        # Step 5: Check memory service enhancement
        memory_service = ChatMemoryService(db)
        test_user_data = {
            'monthly_income': financial_summary.get('monthlyIncome', 0) if financial_summary else 0,
            'monthly_expenses': financial_summary.get('monthlyExpenses', 0) if financial_summary else 0,
            'total_assets': financial_summary.get('totalAssets', 0) if financial_summary else 0,
            'investment_total': financial_summary.get('investmentTotal', 0) if financial_summary else 0,
            'net_worth': financial_summary.get('netWorth', 0) if financial_summary else 0
        }
        
        enhanced_context, is_calc_mode = memory_service.enhance_context_with_calculations(
            financial_context, "What is 4% of my portfolio?", test_user_data
        )
        enhanced_has_data = any(char.isdigit() for char in enhanced_context) and "$" in enhanced_context and not all(val == "0" for val in enhanced_context.split() if val.replace("$", "").replace(",", "").isdigit())
        logger.critical(f"Enhanced context includes real data: {enhanced_has_data}")
        
        return {
            "🚨": "DATA PIPELINE DIAGNOSTIC",
            "user_exists": user_exists,
            "financial_summary_loaded": financial_summary is not None,
            "financial_summary_data": {
                "monthlyIncome": financial_summary.get('monthlyIncome', 0) if financial_summary else 0,
                "monthlyExpenses": financial_summary.get('monthlyExpenses', 0) if financial_summary else 0,
                "netWorth": financial_summary.get('netWorth', 0) if financial_summary else 0,
                "totalAssets": financial_summary.get('totalAssets', 0) if financial_summary else 0,
                "investmentTotal": financial_summary.get('investmentTotal', 0) if financial_summary else 0,
            },
            "financial_context": {
                "loaded": context_has_data,
                "has_real_data": context_has_portfolio,
                "length": len(financial_context),
                "preview": financial_context[:500] + "..." if len(financial_context) > 500 else financial_context
            },
            "session_context_has_data": session_has_data,
            "enhanced_context_has_data": enhanced_has_data,
            "test_user_data": test_user_data,
            "calculation_mode_detected": is_calc_mode,
            "🔧": "DATA LOCATIONS TO CHECK",
            "possible_issues": [
                "User profile not set up" if not user_exists else "✅ User exists",
                "Financial summary service returns empty data" if financial_summary is None else "✅ Financial summary loaded", 
                "Complete context service not including data" if not context_has_portfolio else "✅ Context has real data",
                "Session context service not loading user facts" if not session_has_data else "✅ Session context loaded",
                "Enhanced context not preserving data" if not enhanced_has_data else "✅ Enhanced context preserved data"
            ]
        }
        
    except Exception as e:
        logger.error(f"Debug endpoint failed: {str(e)}")
        return {"error": str(e), "status": "debug_failed"}

# Pydantic Models
class ChatMessageRequest(BaseModel):
    user_id: int
    message: str
    session_id: str
    provider: str = 'gemini'
    model_tier: str = 'dev'
    include_context: bool = True
    insight_level: str = 'balanced'

class ChatMessageResponse(BaseModel):
    message: Dict[str, Any]
    tokens_used: Dict[str, int]
    cost_breakdown: Dict[str, float]
    suggested_questions: List[str]
    context_used: Optional[str] = None
    intent_detected: Optional[str] = None
    conversation_context: Optional[Dict[str, Any]] = None  # New: conversation memory info

# Services initialized on demand

@router.get("/health")
def health_check():
    """Health check for chat with memory service"""
    return {
        "status": "healthy",
        "service": "chat_with_memory",
        "version": "1.0.0",
        "features": {
            "conversation_memory": True,
            "session_summaries": True,
            "intent_detection": True,  # Using enhanced_intent_classifier
            "foundation_calculations": True,
            "response_verification": True
        }
    }

@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message_with_memory(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a message with conversational memory and context awareness
    """
    
    # Verify user access
    if current_user.id != request.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    start_time = time.time()
    
    # DEBUG: Confirm endpoint is being called
    print(f"[CHAT DEBUG] Endpoint called for user_id: {request.user_id}, message: '{request.message[:50]}...'")
    logger.info(f"DEBUG: Chat endpoint called for user_id: {request.user_id}, message: '{request.message[:50]}...'")
    
    try:
        # Initialize memory service
        memory_service = ChatMemoryService(db)
        
        # Get or create chat session
        session = memory_service.get_or_create_session(
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Get conversation context
        conversation_context = memory_service.get_conversation_context(session)
        
        logger.info("Chat with memory request", 
                   user_id=request.user_id,
                   session_id=request.session_id,
                   message_count=conversation_context.get("message_count", 0),
                   last_intent=conversation_context.get("last_intent"))
        
        # Step 1: Enhanced multi-intent detection
        detected_intents = enhanced_intent_classifier.classify_intents(request.message)
        primary_intent = enhanced_intent_classifier.get_primary_intent(detected_intents)
        context_weight = enhanced_intent_classifier.get_intent_context_weight(primary_intent)
        
        logger.info("Enhanced intent analysis", 
                   detected_intents=detected_intents,
                   primary_intent=primary_intent,
                   context_weight=context_weight)
        
        # Step 2: COMPLETE FINANCIAL CONTEXT - Use rich financial data instead of vector store
        # Use complete financial context instead of vector store
        context_service = CompleteFinancialContextService()
        foundation_context = context_service.build_complete_context(
            user_id=request.user_id,
            db=db,
            user_query=request.message,
            insight_level=request.insight_level if hasattr(request, 'insight_level') else 'balanced'
        )
        
        # Add user question to context
        foundation_context = f"{foundation_context}\n\nUSER QUESTION: \"{request.message}\"\n\nIMPORTANT: Use the exact financial metrics provided above in your response."
        
        logger.info(f"Vector-based context retrieved for user {request.user_id}")
        
        # Step 4: Add conversation memory to foundation context
        conversation_text = memory_service.format_context_for_prompt(conversation_context)
        if conversation_text:
            optimized_context = f"""🧠 CONVERSATION MEMORY:
{conversation_text}

{foundation_context}"""
        else:
            optimized_context = foundation_context
        
        token_stats = {'final_tokens': len(optimized_context.split())}
        logger.info("Context built successfully", final_tokens=token_stats['final_tokens'])
        
        # Step 4: Call LLM with simplified context
        response_data = await call_llm_with_memory(
            prompt_context=optimized_context,
            provider=request.provider,
            model_tier=request.model_tier,
            has_conversation_memory=bool(conversation_context.get("message_count", 0) > 0),
            user_message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            primary_intent=primary_intent
        )
        
        # Get response data
        assistant_response = response_data.get("message", {}).get("content", "")
        tokens_used = response_data.get("tokens_used", {}).get("total", 0)
        
        # Step 5.1: Apply retirement response formatting if applicable
        logger.info(f"Checking retirement query for message: '{request.message[:50]}...'")
        if retirement_formatter.is_retirement_query(request.message):
            try:
                # Get user financial data for enhancement
                from app.services.financial_summary_service import financial_summary_service
                financial_summary = financial_summary_service.get_user_financial_summary(request.user_id, db)
                
                # Enhance response with retirement metrics
                assistant_response = retirement_formatter.enhance_response(assistant_response, financial_summary)
                
                # Update response data
                response_data["message"]["content"] = assistant_response
                
                logger.info(f"Applied retirement response formatting for user {request.user_id}")
                
            except Exception as e:
                logger.warning(f"Retirement response formatting failed: {str(e)}")
                # Continue with original response
        
        # Step 5.2: Apply tax optimization intelligence if applicable
        # Step 5.2: Tax Intelligence Enhancement (NEW CLEAN ARCHITECTURE)
        logger.info(f"Checking tax query for message: '{request.message[:50]}...'")
        
        # Use new clean tax intelligence formatter
        from app.services.tax_intelligence_formatter import TaxIntelligenceFormatter
        
        formatter = TaxIntelligenceFormatter(db)
        
        if formatter.is_tax_question(request.message):
            logger.info(f"🔥 TAX QUESTION DETECTED: '{request.message}'")
            try:
                # Get user financial data 
                from app.services.financial_summary_service import financial_summary_service
                financial_summary = financial_summary_service.get_user_financial_summary(request.user_id, db)
                
                if financial_summary:
                    # Build financial context 
                    financial_context = {
                        'monthly_income': financial_summary.get('monthlyIncome', 0),
                        'monthly_expenses': financial_summary.get('monthlyExpenses', 0),
                        'total_assets': financial_summary.get('totalAssets', 0),
                        'investment_total': financial_summary.get('investmentTotal', 0),
                        'mortgage_balance': financial_summary.get('mortgageBalance', 0),
                        'annual_401k': financial_summary.get('annual401k', 0),
                        'tax_bracket': financial_summary.get('taxBracket', 24),
                        'age': financial_summary.get('age', 35),
                        'state': 'NC',
                        'filing_status': 'married'
                    }
                    
                    # Get intelligent tax insights using NEW architecture
                    tax_enhancement = await formatter.format_tax_insights(
                        user_id=request.user_id,
                        question=request.message,
                        financial_context=financial_context
                    )
                    
                    if tax_enhancement:
                        # Enhance response with REAL calculations
                        assistant_response = assistant_response + "\n\n" + tax_enhancement
                        response_data["message"]["content"] = assistant_response
                        
                        logger.info(f"🎯 TAX ENHANCEMENT APPLIED for user {request.user_id}, enhancement length: {len(tax_enhancement)} chars")
                    else:
                        logger.warning(f"❌ Tax enhancement was empty for user {request.user_id}")
                
                else:
                    # Quick opportunity check without full profile
                    quick_enhancement = formatter.format_quick_opportunities(request.user_id, {})
                    if quick_enhancement:
                        assistant_response = assistant_response + quick_enhancement
                        response_data["message"]["content"] = assistant_response
                        
            except Exception as e:
                logger.warning(f"Tax intelligence enhancement failed: {str(e)}")
                # Continue with original response - no hardcoded fallbacks
        
        # Step 5.3: Response verification (skip for now since we're not using vector sync)
        if assistant_response:
            try:
                # Build basic ToolsOutput for verification (simplified)
                tools_output_for_verification = ToolsOutput(
                    savings_rate=0,
                    liquidity_months=0,
                    debt_to_income_ratio=0,
                    net_worth=0,
                    years_to_retirement=30
                )
                
                verifier = BasicResponseVerifier()
                verification_results = verifier.verify_response_numbers(assistant_response, tools_output_for_verification)
                
                # Log verification results
                logger.info(f"Response Verification: {verification_results['summary']}")
                if verification_results['matches']:
                    logger.info(f"Number Matches: {verification_results['matches']}")
                if verification_results['mismatches']:
                    logger.warning(f"Number Mismatches: {verification_results['mismatches']}")
                if verification_results['found_numbers']:
                    logger.debug(f"Found Numbers: {verification_results['found_numbers']}")
                    
            except Exception as e:
                logger.error(f"Response verification failed: {str(e)}")
        
        # Save conversation to memory
        memory_service.add_message_pair(
            session=session,
            user_message=request.message,
            assistant_response=assistant_response,
            intent_detected=primary_intent,
            context_used={
                "financial_data_included": bool(foundation_context and "Error loading" not in foundation_context),
                "conversation_context_included": bool(conversation_context.get("recent_messages")),
                "session_summary_used": bool(conversation_context.get("session_summary"))
            },
            tokens_used=tokens_used,
            model_used=request.model_tier,
            provider=request.provider
        )
        
        # Generate response
        response_time = (time.time() - start_time) * 1000
        
        # Build simplified conversation context
        conversation_response_context = {
            "message_count": conversation_context.get("message_count", 0) + 2,
            "session_summary": conversation_context.get("session_summary"),
            "last_intent": primary_intent,
            "response_time_ms": int(response_time),
            "conversation_turn": (conversation_context.get("message_count", 0) // 2) + 1
        }
        
        return ChatMessageResponse(
            message=response_data.get("message", {}),
            tokens_used=response_data.get("tokens_used", {}),
            cost_breakdown=response_data.get("cost_breakdown", {}),
            suggested_questions=generate_contextual_suggestions(primary_intent, conversation_context, detected_intents),
            context_used=f"Enhanced context: {token_stats['final_tokens']} tokens (Cleaned Phase)",
            intent_detected=primary_intent,
            conversation_context=conversation_response_context
        )
        
    except Exception as e:
        logger.error("Chat with memory failed", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )

def get_intent_guidance(intent: str) -> str:
    """Provide intent-specific guidance for focused responses"""
    guidance_map = {
        "retirement": "Focus on retirement timeline, savings rate, and withdrawal strategies",
        "cash_flow": "Analyze income, expenses, and monthly cash flow optimization", 
        "debt": "Prioritize debt payoff strategies and interest rate optimization",
        "investment": "Discuss asset allocation, risk tolerance, and investment strategy",
        "emergency_fund": "Evaluate emergency fund adequacy and liquidity",
        "tax": "Focus on tax optimization and planning strategies"
    }
    return guidance_map.get(intent, "Provide comprehensive financial guidance")

async def call_llm_with_memory(
    prompt_context: str,
    provider: str = "gemini",
    model_tier: str = "dev",
    insight_level: str = "balanced",
    is_calculation_mode: bool = False,
    temperature: Optional[float] = None,
    has_conversation_memory: bool = False,
    user_message: str = "",
    user_id: int = 0,
    session_id: str = "",
    primary_intent: str = ""
) -> Dict[str, Any]:
    """
    Call LLM with the enhanced conversational prompt using the real LLM service
    Uses lower temperature for calculations to ensure accuracy
    """
    from app.services.llm_service import llm_service
    from app.models.llm_models import LLMRequest
    
    try:
        # Check if LLM service is available
        if llm_service is None:
            raise RuntimeError("LLM service not initialized")
        
        # Use custom temperature or default based on calculation mode and memory context
        if temperature is None:
            if is_calculation_mode:
                temperature = 0.3
            elif has_conversation_memory:
                # Lower temperature for conversation continuity
                temperature = 0.4  
            else:
                temperature = 0.7
        
        # Adjust system prompt for calculation mode
        if is_calculation_mode:
            system_prompt = """You are a warm, experienced financial advisor having a conversation with a client about their finances. 
            When they ask calculation questions, work through the math together naturally - don't sound like a calculator.
            
            CRITICAL GUIDELINES:
            - ANSWER FIRST: For yes/no questions, start with "Yes" or "No" in the first sentence
            - BE DIRECT: Give the answer, then briefly explain why
            - BE CONCISE: Keep responses under 200 words for simple questions
            - ALWAYS use their actual financial data that's provided in the context
            - NEVER ask for data that's already given to you
            - Weave calculations into natural explanations, avoiding robotic formats
            - Connect the numbers to their personal situation and goals"""
        else:
            system_prompt = "You are a warm, intelligent financial advisor with conversational memory. Provide personalized, context-aware financial advice in a friendly, professional tone."
            
        # Create LLM request
        llm_request = LLMRequest(
            provider=provider,
            model_tier=model_tier,
            system_prompt=system_prompt,
            user_prompt=prompt_context,
            temperature=temperature,
            max_tokens=2000
        )
        
        # Generate response using the actual LLM service
        llm_response = await llm_service.generate(llm_request)
        
        # Convert to expected format
        response = {
            "message": {
                "role": "assistant",
                "content": llm_response.content,
                "timestamp": datetime.now().isoformat()
            },
            "tokens_used": {
                "input": llm_response.token_usage.get("input_tokens", 0),
                "output": llm_response.token_usage.get("output_tokens", 0),
                "total": llm_response.token_usage.get("total_tokens", 0)
            },
            "cost_breakdown": {
                "input_cost": float(llm_response.cost) * 0.6,  # Rough split
                "output_cost": float(llm_response.cost) * 0.4,
                "total_cost": float(llm_response.cost)
            }
        }
        
        # Store debug payload for Step 7 debug view
        try:
            from app.api.v1.endpoints.debug import store_llm_payload
            debug_payload = {
                "request": {
                    "provider": provider,
                    "model_tier": model_tier,
                    "user_message": user_message,
                    "system_prompt": system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt,
                    "context": prompt_context[:1000] + "..." if len(prompt_context) > 1000 else prompt_context,
                },
                "response": {
                    "content": llm_response.content,
                    "tokens": llm_response.token_usage,
                    "cost": float(llm_response.cost)
                },
                "metadata": {
                    "intent_detected": primary_intent,
                    "session_id": session_id,
                    "vector_sync_used": True
                }
            }
            logger.info(f"Storing debug payload for user {user_id}")
            store_llm_payload(user_id, debug_payload)
            logger.info(f"Debug payload stored successfully for user {user_id}")
        except Exception as debug_error:
            logger.error(f"Failed to store debug payload: {debug_error}")
            import traceback
            logger.error(f"Debug payload traceback: {traceback.format_exc()}")
        
        return response
        
    except Exception as e:
        logger.error(f"LLM call failed: {str(e)}")
        # Fallback response
        return {
            "message": {
                "role": "assistant",
                "content": f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            },
            "tokens_used": {"input": 0, "output": 50, "total": 50},
            "cost_breakdown": {"input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0}
        }

def generate_contextual_suggestions(
    intent: Optional[str], 
    conversation_context: Dict,
    detected_intents: List[str] = None
) -> List[str]:
    """Generate contextually relevant follow-up questions"""
    
    base_suggestions = [
        "What's my current financial health score?",
        "How should I prioritize my financial goals?",
        "What's the best way to optimize my cash flow?"
    ]
    
    # Add intent-specific suggestions
    if intent == "retirement":
        base_suggestions.extend([
            "When can I realistically retire?",
            "How much should I save monthly for retirement?",
            "What's my optimal retirement withdrawal rate?"
        ])
    elif intent == "debt":
        base_suggestions.extend([
            "Which debt should I pay off first?",
            "Should I consolidate my debt?",
            "What's my debt-to-income ratio?"
        ])
    elif intent == "investment":
        base_suggestions.extend([
            "How should I allocate my investment portfolio?",
            "What's my risk tolerance?",
            "Should I rebalance my investments?"
        ])
    
    # Limit suggestions and add conversation-aware ones
    suggestions = base_suggestions[:4]
    
    if conversation_context.get("message_count", 0) > 2:
        suggestions.append("Can you elaborate on your previous recommendation?")
    
    return suggestions

@router.get("/sessions/{user_id}")
async def get_user_chat_sessions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent chat sessions for a user"""
    
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    memory_service = ChatMemoryService(db)
    sessions = memory_service.get_user_sessions(user_id, limit=10)
    
    return {
        "user_id": user_id,
        "sessions": [
            {
                "session_id": session.session_id,
                "message_count": session.message_count,
                "last_message": session.last_message_at.isoformat() if session.last_message_at else None,
                "session_summary": session.session_summary,
                "last_intent": session.last_intent,
                "created_at": session.created_at.isoformat()
            }
            for session in sessions
        ]
    }

@router.get("/session/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all messages for a specific session"""
    
    # Get session and verify ownership
    memory_service = ChatMemoryService(db)
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Get messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "intent_detected": msg.intent_detected,
                "tokens_used": msg.tokens_used,
                "created_at": msg.created_at.isoformat(),
                "provider": msg.provider,
                "model_used": msg.model_used
            }
            for msg in messages
        ]
    }

@router.post("/sessions/new")
async def create_new_session(
    title: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new chat session"""
    
    import uuid
    session_id = f"session_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    memory_service = ChatMemoryService(db)
    session = memory_service.get_or_create_session(
        user_id=current_user.id,
        session_id=session_id
    )
    
    if title:
        session.title = title
        db.commit()
    
    return {
        "session_id": session_id,
        "created_at": session.created_at.isoformat(),
        "title": title,
        "message_count": 0
    }

@router.delete("/sessions/{session_id}")
async def clear_chat_session(
    session_id: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Clear a specific chat session"""
    
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    memory_service = ChatMemoryService(db)
    success = memory_service.clear_session(session_id, user_id)
    
    return {
        "success": success,
        "message": "Session cleared successfully" if success else "Session not found"
    }

# NEW INTELLIGENT CHAT ENDPOINT
class IntelligentChatRequest(BaseModel):
    message: str
    session_id: str = None
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
        detected_intents = enhanced_intent_classifier.classify_intents(request.message)
        primary_intent = enhanced_intent_classifier.get_primary_intent(detected_intents)
        
        # Complete financial context retrieval (fixed for frontend)
        context_service = CompleteFinancialContextService()
        foundation_context = context_service.build_complete_context(
            user_id=current_user.id,
            db=db,
            user_query=request.message,
            insight_level='balanced'
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
        
        # Call LLM
        response_data = await call_llm_with_memory(
            prompt_context=optimized_context,
            provider=request.provider,
            model_tier=request.model_tier,
            has_conversation_memory=True,
            user_message=request.message,
            user_id=current_user.id,
            session_id=request.session_id,
            primary_intent=primary_intent
        )
        
        # Get response data
        assistant_response = response_data.get("message", {}).get("content", "")
        tokens_used = response_data.get("tokens_used", {}).get("total", 0)
        
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
            tokens_used=tokens_used,
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
        
        return IntelligentChatResponse(
            message=response_data.get("message", {}),
            tokens_used=response_data.get("tokens_used", {}),
            cost_breakdown=response_data.get("cost_breakdown", {}),
            intelligence_metrics=intelligence_metrics,
            suggested_questions=generate_contextual_suggestions(primary_intent, conversation_context, detected_intents),
            conversation_context=conversation_response_context
        )
        
    except Exception as e:
        logger.error("Intelligent chat failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intelligent chat processing failed: {str(e)}"
        )