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
        
        if insight_type != "general_chat":
            # Financial question - use facts + LLM
            math = IdentityMath()
            facts = math.compute_claims(current_user.id, db)
            
            if "error" in facts:
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
            response = await llm_service.generate(
                system_prompt="Financial advisor using only provided facts",
                user_prompt=f"{prompt}\n\nUser: {request.message}",
                temperature=0.3
            )
            
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
            response = await llm_service.generate(
                system_prompt="Helpful assistant",
                user_prompt=request.message,
                temperature=0.7
            )
            
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
    finance_words = {'worth': 1, 'assets': 0.9, 'income': 0.8, 'debt': 0.8}
    
    scores = {
        'tax': sum(w for k, w in tax_words.items() if k in msg),
        'risk': sum(w for k, w in risk_words.items() if k in msg),
        'goals': sum(w for k, w in goal_words.items() if k in msg),
        'general': sum(w for k, w in finance_words.items() if k in msg)
    }
    
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general_chat"