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

logger = logging.getLogger(__name__)
router = APIRouter()

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
    response = await llm_service.generate(
        system_prompt="Financial advisor using only provided facts",
        user_prompt=f"{prompt}\n\nQuestion: {request.question}",
        temperature=0.3
    )
    
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