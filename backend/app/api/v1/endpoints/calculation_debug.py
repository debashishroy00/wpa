"""
Calculation Debug Endpoint - Bypass authentication to test calculation pipeline
This endpoint helps diagnose why calculations aren't working in the chat system
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel
import time
import structlog

from app.db.session import get_db
from app.services.chat_memory_service import ChatMemoryService
from app.services.calculation_validator import calculation_validator
from app.services.formula_library import formula_library

logger = structlog.get_logger()

router = APIRouter()

class CalculationDebugRequest(BaseModel):
    message: str
    user_data: Dict[str, Any] = {}

class CalculationDebugResponse(BaseModel):
    message: str
    calculation_detected: bool
    enhanced_prompt_applied: bool
    formula_context_added: bool
    enhanced_context: str
    is_calculation_mode: bool
    detected_topics: List[str]
    validation_test: Dict[str, Any]
    diagnostics: Dict[str, Any]

@router.post("/debug-calculation", response_model=CalculationDebugResponse)
async def debug_calculation_pipeline(
    request: CalculationDebugRequest,
    db: Session = Depends(get_db)
):
    """
    Debug calculation pipeline without authentication
    Tests each step of the calculation handling process
    """
    
    logger.info("Calculation debug request", message=request.message[:100])
    
    # Initialize services
    memory_service = ChatMemoryService(db)
    
    # Step 1: Test calculation detection
    calculation_detected = memory_service.requires_calculation(request.message)
    logger.info("Calculation detection", detected=calculation_detected)
    
    # Step 2: Test context enhancement
    base_context = "You are a helpful financial advisor."
    enhanced_context, is_calculation_mode = memory_service.enhance_context_with_calculations(
        base_context, request.message, request.user_data
    )
    
    enhanced_prompt_applied = len(enhanced_context) > len(base_context)
    formula_context_added = "CALCULATION FRAMEWORK" in enhanced_context
    
    # Step 3: Test formula library
    detected_topics = formula_library.detect_calculation_topics(request.message)
    calculation_context = formula_library.create_calculation_context(request.message, request.user_data)
    
    # Step 4: Test validation (simulate a calculation response)
    test_calculation_response = """
**Step 1:** Annual expenses = $5,000/month × 12 = $60,000
**Step 2:** 4% Rule portfolio = $60,000 ÷ 0.04 = $1,500,000
**Result:** You need **$1,500,000** to retire using the 4% rule.
"""
    
    validation_test = memory_service.validate_response_calculations(
        test_calculation_response, request.message
    )
    
    # Gather diagnostics
    diagnostics = {
        "base_context_length": len(base_context),
        "enhanced_context_length": len(enhanced_context),
        "context_growth_factor": len(enhanced_context) / len(base_context) if len(base_context) > 0 else 0,
        "calculation_context_length": len(calculation_context),
        "enhanced_math_prompt_present": "CALCULATION FRAMEWORK" in enhanced_context,
        "formula_examples_present": "Formula:" in enhanced_context or "Example:" in enhanced_context,
        "step_format_example_present": "**Step" in enhanced_context,
        "timestamp": time.time()
    }
    
    response = CalculationDebugResponse(
        message=request.message,
        calculation_detected=calculation_detected,
        enhanced_prompt_applied=enhanced_prompt_applied,
        formula_context_added=formula_context_added,
        enhanced_context=enhanced_context,
        is_calculation_mode=is_calculation_mode,
        detected_topics=detected_topics,
        validation_test=validation_test,
        diagnostics=diagnostics
    )
    
    logger.info("Calculation debug completed", 
                calculation_detected=calculation_detected,
                is_calculation_mode=is_calculation_mode,
                detected_topics=detected_topics)
    
    return response

@router.post("/test-llm-direct")
async def test_llm_direct(request: CalculationDebugRequest):
    """
    Test LLM call directly with calculation context
    This bypasses all authentication and session management
    """
    
    try:
        # Import LLM service
        from app.services.llm_service import llm_service
        from app.models.llm_models import LLMRequest
        
        # Check if we have registered clients
        if not llm_service.clients:
            return {
                "error": "No LLM clients registered",
                "available_providers": list(llm_service.providers.keys())
            }
        
        # Initialize services  
        from app.db.session import SessionLocal
        memory_service = ChatMemoryService(SessionLocal())
        
        # Build enhanced context
        base_context = "You are a helpful financial advisor."
        enhanced_context, is_calculation_mode = memory_service.enhance_context_with_calculations(
            base_context, request.message, request.user_data
        )
        
        # Create LLM request
        llm_request = LLMRequest(
            provider="openai" if "openai" in llm_service.clients else list(llm_service.clients.keys())[0],
            model_tier="dev",
            system_prompt=enhanced_context,
            user_prompt=request.message,
            context_data=request.user_data,
            temperature=0.1,
            max_tokens=2000
        )
        
        # Generate response
        start_time = time.time()
        llm_response = await llm_service.generate(llm_request)
        response_time = time.time() - start_time
        
        # Validate calculations in response
        validation = memory_service.validate_response_calculations(
            llm_response.content, request.message
        )
        
        return {
            "success": True,
            "response_time": response_time,
            "calculation_mode": is_calculation_mode,
            "llm_response": {
                "provider": llm_response.provider,
                "model": llm_response.model,
                "content": llm_response.content,
                "token_usage": llm_response.token_usage,
                "cost": float(llm_response.cost)
            },
            "validation": validation,
            "context_used": {
                "system_prompt_length": len(enhanced_context),
                "has_calculation_framework": "CALCULATION FRAMEWORK" in enhanced_context,
                "has_step_examples": "**Step" in enhanced_context
            }
        }
        
    except Exception as e:
        logger.error("Direct LLM test failed", error=str(e))
        return {
            "error": str(e),
            "success": False
        }

@router.get("/calculation-health")
def calculation_health_check():
    """
    Health check specifically for calculation components
    """
    
    try:
        # Test each component
        from app.services.calculation_validator import calculation_validator
        from app.services.formula_library import formula_library
        from app.services.llm_service import llm_service
        
        # Test calculation validator
        validator_test = calculation_validator.validate_math("$100,000 ÷ 0.04 = $2,500,000")
        
        # Test formula library
        topics = formula_library.detect_calculation_topics("How much for retirement using 4% rule?")
        
        # Test LLM service
        llm_clients_available = len(llm_service.clients) > 0
        
        return {
            "status": "healthy",
            "components": {
                "calculation_validator": {
                    "available": True,
                    "test_result": validator_test
                },
                "formula_library": {
                    "available": True,
                    "detected_topics": topics
                },
                "llm_service": {
                    "available": llm_clients_available,
                    "registered_clients": list(llm_service.clients.keys())
                }
            },
            "overall_ready": all([
                validator_test.get('valid', False),
                len(topics) > 0,
                llm_clients_available
            ])
        }
        
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e)
        }