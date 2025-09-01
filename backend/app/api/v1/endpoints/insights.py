"""
Clean Insights API using new foundation.
Replaces complex calculations with facts + LLM reasoning.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
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

# Initialize LLM clients with better error handling
try:
    from app.services.llm_service import llm_service
    from app.core.config import settings
    
    # Check if providers are configured
    if not hasattr(llm_service, 'providers') or not llm_service.providers:
        logger.error("LLM providers not configured in llm_service")
    else:
        # Try OpenAI
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            try:
                from app.services.llm_clients.openai_client import OpenAIClient
                provider_config = llm_service.providers.get("openai")
                if provider_config:
                    client = OpenAIClient(provider_config)
                    llm_service.register_client("openai", client)
                    logger.info("✅ OpenAI client registered successfully (insights)")
                else:
                    logger.error("OpenAI provider config not found (insights)")
            except Exception as e:
                logger.error(f"Failed to register OpenAI (insights): {e}")
        
        # Try Gemini
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            try:
                from app.services.llm_clients.gemini_client import GeminiClient
                provider_config = llm_service.providers.get("gemini")
                if provider_config:
                    client = GeminiClient(provider_config)
                    llm_service.register_client("gemini", client)
                    logger.info("✅ Gemini client registered successfully (insights)")
                else:
                    logger.error("Gemini provider config not found (insights)")
            except Exception as e:
                logger.error(f"Failed to register Gemini (insights): {e}")
        
        # Log final status
        registered = list(llm_service.clients.keys()) if hasattr(llm_service, 'clients') else []
        logger.info(f"LLM clients registered (insights): {registered if registered else 'NONE'}")
        
except Exception as e:
    logger.error(f"Critical: LLM service initialization failed completely (insights): {e}")

class InsightRequest(BaseModel):
    question: str
    insight_type: Optional[str] = "general"  # tax, risk, goals, general

class InsightResponse(BaseModel):
    insight: str
    confidence: str
    facts_used: Dict[str, Any]
    assumptions: list
    warnings: list

@router.post("/analyze", response_model=InsightResponse)
async def analyze(
    request: InsightRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate insights using facts + LLM reasoning"""
    
    # Get facts
    math = IdentityMath()
    facts = math.compute_claims(current_user.id, db)
    
    if "error" in facts:
        raise HTTPException(400, facts["error"])
    
    # Build prompt
    prompt = core_prompts.format_prompt(
        prompt_type=request.insight_type,
        claims=facts,
        age=facts["_context"].get("age"),
        state=facts["_context"].get("state"),
        filing_status=facts["_context"].get("filing_status")
    )
    
    # Get LLM response
    llm_request = LLMRequest(
        provider="openai",  # Default provider
        system_prompt="Financial advisor using only provided facts",
        user_prompt=f"{prompt}\n\nQuestion: {request.question}",
        temperature=0.3
    )
    response = await llm_service.generate(llm_request)
    
    # Validate
    engine = TrustEngine()
    validated = engine.validate(response.content, facts)
    
    return InsightResponse(
        insight=validated["response"],
        confidence=validated["confidence"],
        facts_used={k: v for k, v in facts.items() if not k.startswith("_")},
        assumptions=validated["assumptions"],
        warnings=facts.get("_warnings", [])
    )