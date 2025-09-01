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

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize LLM clients on import (same pattern as chat_with_memory.py)
try:
    from app.services.llm_clients.openai_client import OpenAIClient
    from app.services.llm_clients.gemini_client import GeminiClient
    from app.core.config import settings
    
    # Register OpenAI client if API key is available
    if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
        openai_client = OpenAIClient(llm_service.providers["openai"])
        llm_service.register_client("openai", openai_client)
        logger.info("OpenAI client registered for chat_simple")
    
    # Register Gemini client if API key is available
    if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
        gemini_client = GeminiClient(llm_service.providers["gemini"])
        llm_service.register_client("gemini", gemini_client)
        logger.info("Gemini client registered for chat_simple")
        
except ImportError as e:
    logger.warning(f"LLM client registration failed: {e}")

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
    """Handle chat with financial intelligence"""
    try:
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
            
            # Build prompt with facts
            prompt = core_prompts.format_prompt(
                prompt_type=insight_type,
                claims=facts,
                age=facts["_context"].get("age"),
                state=facts["_context"].get("state"),
                filing_status=facts["_context"].get("filing_status")
            )
            
            # Get LLM response
            llm_request = LLMRequest(
                provider="openai",  # Default provider
                system_prompt="Financial advisor using only provided facts",
                user_prompt=f"{prompt}\n\nUser: {request.message}",
                temperature=0.3
            )
            response = await llm_service.generate(llm_request)
            
            # Validate
            engine = TrustEngine()
            validated = engine.validate(response.content, facts)
            
            return ChatResponse(
                response=validated["response"],
                confidence=validated["confidence"],
                warnings=facts.get("_warnings", []),
                session_id=request.session_id or "new"
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
            
            return ChatResponse(
                response=response.content,
                confidence="HIGH",
                warnings=[],
                session_id=request.session_id or "new"
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
    """Detect question type with weighted keywords"""
    msg = message.lower()
    
    # Weighted keywords
    tax_words = {'tax': 1, 'deduction': 1, '401k': 0.9, 'ira': 0.9}
    risk_words = {'risk': 1, 'allocation': 0.9, 'diversify': 0.8}
    goal_words = {'retire': 1, 'goal': 0.9, 'fire': 0.9, 'target': 0.8}
    finance_words = {'worth': 1, 'assets': 0.9, 'income': 0.8, 'debt': 0.8, 'financial': 0.9, 'health': 0.8, 'score': 0.7, 'picture': 0.6}
    
    scores = {
        'tax': sum(w for k, w in tax_words.items() if k in msg),
        'risk': sum(w for k, w in risk_words.items() if k in msg),
        'goals': sum(w for k, w in goal_words.items() if k in msg),
        'general': sum(w for k, w in finance_words.items() if k in msg)
    }
    
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general_chat"