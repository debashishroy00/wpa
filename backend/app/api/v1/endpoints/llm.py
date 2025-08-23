"""
WealthPath AI - Multi-LLM API Endpoints
FastAPI endpoints for multi-LLM integration and advisory generation
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging

from ....models.llm_models import (
    LLMRequest, LLMResponse, LLMComparison, AdvisoryGeneration, 
    AdvisoryContent, RAGQuery, RAGResult, KnowledgeBaseDocument
)
from ....services.llm_service import llm_service
from ....services.rag_service import knowledge_base
from ....services.validation_service import number_validator
from ....services.llm_clients import OpenAIClient, GeminiClient, ClaudeClient
from ....core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Initialize LLM clients on startup
async def initialize_llm_clients():
    """Initialize and register LLM clients"""
    try:
        # Register OpenAI client
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            openai_client = OpenAIClient(llm_service.providers["openai"])
            llm_service.register_client("openai", openai_client)
            logger.info("OpenAI client registered")
        
        # Register Gemini client
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            gemini_client = GeminiClient(llm_service.providers["gemini"])
            llm_service.register_client("gemini", gemini_client)
            logger.info("Gemini client registered")
        
        # Register Claude client
        if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
            claude_client = ClaudeClient(llm_service.providers["claude"])
            llm_service.register_client("claude", claude_client)
            logger.info("Claude client registered")
        
    except Exception as e:
        logger.error(f"Failed to initialize LLM clients: {e}")


# LLM clients are now initialized in app lifespan handler (main.py)


@router.get("/providers")
async def list_providers() -> Dict[str, Any]:
    """List available LLM providers and their configurations"""
    providers_info = {}
    
    for provider_id, provider_config in llm_service.providers.items():
        client_available = provider_id in llm_service.clients
        
        providers_info[provider_id] = {
            "name": provider_config.name,
            "is_enabled": provider_config.is_enabled and client_available,
            "models": provider_config.models,
            "cost_per_1k_input": float(provider_config.cost_per_1k_tokens_input),
            "cost_per_1k_output": float(provider_config.cost_per_1k_tokens_output),
            "client_status": "connected" if client_available else "not_configured"
        }
    
    return {
        "providers": providers_info,
        "total_providers": len(providers_info),
        "available_providers": len([p for p in providers_info.values() if p["is_enabled"]])
    }


@router.post("/generate", response_model=LLMResponse)
async def generate_content(request: LLMRequest) -> LLMResponse:
    """Generate content using specified LLM provider"""
    try:
        if request.provider not in llm_service.clients:
            raise HTTPException(
                status_code=400, 
                detail=f"Provider '{request.provider}' not available"
            )
        
        response = await llm_service.generate(request)
        return response
        
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=LLMComparison)
async def compare_providers(
    request: LLMRequest,
    providers: Optional[List[str]] = None
) -> LLMComparison:
    """Compare responses from multiple LLM providers"""
    try:
        # Use all available providers if none specified
        if providers is None:
            providers = list(llm_service.clients.keys())
        
        # Validate requested providers
        unavailable = [p for p in providers if p not in llm_service.clients]
        if unavailable:
            raise HTTPException(
                status_code=400,
                detail=f"Providers not available: {unavailable}"
            )
        
        comparison = await llm_service.compare_providers(request, providers)
        return comparison
        
    except Exception as e:
        logger.error(f"Provider comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/advisory/generate", response_model=AdvisoryContent)
async def generate_advisory_content(request: AdvisoryGeneration) -> AdvisoryContent:
    """Generate professional advisory content from Step 4 data"""
    try:
        advisory_content = await llm_service.generate_advisory_content(request)
        return advisory_content
        
    except Exception as e:
        logger.error(f"Advisory content generation failed: {e}", exc_info=True)
        
        # Fallback to demo mode if no LLM clients are registered
        if "No client registered" in str(e):
            logger.info("Falling back to demo mode - generating mock advisory content")
            return _generate_demo_advisory_content(request)
        
        # Return specific error message for debugging
        error_detail = f"LLM advisory generation error: {str(e)}"
        logger.error(f"Raising HTTPException with detail: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/advisory/stream")
async def stream_advisory_content(request: AdvisoryGeneration):
    """Stream advisory content generation (for real-time UI updates)"""
    async def generate_stream():
        try:
            # Start generation
            yield f"data: {json.dumps({'status': 'starting', 'provider': request.provider_preferences[0] if request.provider_preferences else 'openai'})}\n\n"
            
            # Generate content
            advisory_content = await llm_service.generate_advisory_content(request)
            
            # Stream response
            yield f"data: {json.dumps({'status': 'completed', 'content': advisory_content.dict()})}\n\n"
            
        except Exception as e:
            error_data = {'status': 'error', 'message': str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/validate-numbers")
async def validate_response_numbers(
    response_content: str,
    source_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate numbers in LLM response against source data"""
    try:
        validations = number_validator.validate_response_numbers(
            response_content, source_data
        )
        
        # Calculate summary statistics
        total_numbers = len(validations)
        valid_numbers = sum(1 for v in validations if v.is_valid)
        avg_confidence = sum(v.confidence_score for v in validations) / total_numbers if total_numbers > 0 else 0
        
        return {
            "validations": [v.dict() for v in validations],
            "summary": {
                "total_numbers": total_numbers,
                "valid_numbers": valid_numbers,
                "invalid_numbers": total_numbers - valid_numbers,
                "validation_rate": valid_numbers / total_numbers if total_numbers > 0 else 0,
                "average_confidence": avg_confidence
            }
        }
        
    except Exception as e:
        logger.error(f"Number validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Knowledge Base endpoints
@router.post("/knowledge-base/search", response_model=RAGResult)
async def search_knowledge_base(query: RAGQuery) -> RAGResult:
    """Search the knowledge base for relevant documents"""
    try:
        result = await knowledge_base.search(query)
        return result
        
    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/documents")
async def list_knowledge_base_documents(
    doc_type: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """List documents in the knowledge base"""
    try:
        documents = knowledge_base.list_documents(doc_type, category)
        
        # Limit results
        if limit > 0:
            documents = documents[:limit]
        
        return {
            "documents": [
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "doc_type": doc.doc_type,
                    "category": doc.category,
                    "tags": doc.tags,
                    "created_at": doc.created_at.isoformat(),
                    "word_count": doc.metadata.get("word_count", 0)
                }
                for doc in documents
            ],
            "total_count": len(documents),
            "filters": {
                "doc_type": doc_type,
                "category": category
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list knowledge base documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/documents/{doc_id}")
async def get_knowledge_base_document(doc_id: str) -> KnowledgeBaseDocument:
    """Get a specific document from the knowledge base"""
    document = knowledge_base.get_document(doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.post("/knowledge-base/documents")
async def add_knowledge_base_document(document: KnowledgeBaseDocument) -> Dict[str, Any]:
    """Add a new document to the knowledge base"""
    try:
        success = knowledge_base.add_document(document)
        
        if success:
            return {
                "success": True,
                "doc_id": document.doc_id,
                "message": "Document added successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add document")
            
    except Exception as e:
        logger.error(f"Failed to add document to knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check and status endpoints
@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Check health status of LLM services"""
    health_status = {
        "status": "healthy",
        "providers": {},
        "knowledge_base": {
            "status": "healthy",
            "document_count": len(knowledge_base.documents)
        }
    }
    
    # Check each provider
    for provider_id, client in llm_service.clients.items():
        try:
            is_connected = await client.validate_connection()
            health_status["providers"][provider_id] = {
                "status": "healthy" if is_connected else "unhealthy",
                "last_check": "now"
            }
        except Exception as e:
            health_status["providers"][provider_id] = {
                "status": "error",
                "error": str(e),
                "last_check": "now"
            }
    
    # Overall status
    unhealthy_providers = [
        p for p, status in health_status["providers"].items() 
        if status["status"] != "healthy"
    ]
    
    if unhealthy_providers:
        health_status["status"] = "degraded"
        health_status["issues"] = f"Unhealthy providers: {unhealthy_providers}"
    
    return health_status


@router.get("/metrics")
async def get_service_metrics() -> Dict[str, Any]:
    """Get service metrics and usage statistics"""
    return {
        "cache": {
            "size": len(llm_service.cache.cache),
            "max_size": llm_service.cache.max_size,
            "hit_rate": "not_implemented"  # Would need to track cache hits
        },
        "providers": {
            provider_id: {
                "total_requests": "not_implemented",  # Would need request tracking
                "average_response_time": "not_implemented",
                "total_cost": "not_implemented"
            }
            for provider_id in llm_service.clients.keys()
        },
        "knowledge_base": {
            "total_documents": len(knowledge_base.documents),
            "total_searches": "not_implemented",
            "average_search_time": "not_implemented"
        }
    }


def _generate_demo_advisory_content(request: AdvisoryGeneration) -> AdvisoryContent:
    """Generate demo advisory content when LLM clients are not available"""
    import uuid
    from datetime import datetime
    
    # Mock LLM response
    mock_llm_response = LLMResponse(
        provider="demo",
        model="demo-model",
        content="Mock advisory content generated in demo mode",
        token_usage={
            "input_tokens": 100,
            "completion_tokens": 500,
            "total_tokens": 600
        },
        cost=0.0,
        generation_time=1.5,
        metadata={"demo_mode": True}
    )
    
    # Generate mock advisory content based on generation type
    if request.generation_type == "summary":
        content = """**Executive Summary**

Based on your current financial position and goals, here's a comprehensive analysis:

• **Current Net Worth**: Your portfolio shows strong diversification with a total value of $485,750
• **Savings Rate**: At 31% savings rate, you're significantly ahead of the average American (13%)
• **Risk Assessment**: Your current allocation aligns well with a moderate risk tolerance
• **Goal Progress**: You're on track to achieve your retirement goals with some optimization opportunities

**Key Recommendations**

1. **Emergency Fund**: Consider increasing liquid savings to 6 months of expenses
2. **Tax Optimization**: Maximize 401(k) contributions to reduce current tax burden
3. **Diversification**: Add international exposure to reduce US market concentration risk
4. **Debt Management**: Refinancing mortgage could save $320/month at current rates

*This analysis is generated in demo mode. Configure API keys for personalized AI-generated advice.*"""
    
    elif request.generation_type == "recommendations":
        content = """**Personalized Recommendations**

**Immediate Actions (Next 30 Days)**
• Increase 401(k) contribution to capture full employer match
• Open high-yield savings account for emergency fund
• Review and update beneficiaries on all accounts

**3-Month Goals**
• Refinance mortgage to secure lower interest rate
• Rebalance portfolio to target allocation
• Set up automatic investment contributions

**12-Month Strategy**
• Consider Roth IRA conversion ladder
• Evaluate tax-loss harvesting opportunities
• Review insurance coverage adequacy

*Demo mode active - Real AI analysis requires API configuration.*"""
    
    elif request.generation_type == "analysis":
        content = """**Detailed Financial Analysis**

**Portfolio Performance**: Your current allocation has a 73% success rate for reaching retirement goals
**Risk Metrics**: Moderate volatility with good downside protection
**Tax Efficiency**: Opportunities exist for tax optimization strategies
**Goal Alignment**: Financial trajectory supports retirement by age 65

**Monte Carlo Results**
• 95th percentile: $3,200,000
• 50th percentile: $2,650,000
• 5th percentile: $1,800,000

*Analysis generated in demo mode*"""
    
    else:  # comparison
        content = """**Multi-Provider Comparison**

This would typically show analysis from multiple AI providers:
• OpenAI GPT analysis
• Google Gemini insights  
• Claude recommendations

*Demo mode: Configure API keys to enable real multi-LLM comparisons*"""
    
    return AdvisoryContent(
        generation_id=str(uuid.uuid4()),
        content_type=request.generation_type,
        content=content,
        llm_response=mock_llm_response,
        rag_results=None,
        validation_results=[],
        quality_score=0.85,
        created_at=datetime.utcnow()
    )