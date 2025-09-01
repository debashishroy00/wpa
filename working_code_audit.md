=== COMPLETE WORKING CODE AUDIT ===
Generated: Mon, Sep  1, 2025  1:00:36 AM
## CHAT_WITH_MEMORY.PY COMPLETE CODE
### LLM Registration Section:
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

### How it calls LLM:
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
        

## IS CHAT_WITH_MEMORY ACTIVE?
# intelligence, chat_with_memory (imports removed services)

## CURRENT API ROUTES
from app.api.v1.endpoints import auth, users, financial, goals, goal_templates, goals_v2, advisor_data, plan_engine, advisory, financial_clean, vector_db, debug, profile, admin, embeddings, insights, chat_simple
# intelligence, chat_with_memory (imports removed services)
# Create API router
api_router = APIRouter()
# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(financial.router, prefix="/financial", tags=["financial"])
api_router.include_router(goals_v2.router, tags=["goals-v2"])
api_router.include_router(goal_templates.router, prefix="/goal-templates", tags=["goal-templates"])
# api_router.include_router(projections.router, prefix="/projections", tags=["projections"])  # Disabled - imports removed projection_service
# api_router.include_router(intelligence.router, prefix="/intelligence", tags=["intelligence"])  # Disabled - imports removed services
api_router.include_router(advisor_data.router, prefix="/advisor", tags=["advisor-data"])
api_router.include_router(plan_engine.router, prefix="/plan-engine", tags=["plan-engine"])
api_router.include_router(advisory.router, prefix="/advisory", tags=["advisory"])
# api_router.include_router(llm.router, prefix="/llm", tags=["step5-llm"])  # Disabled - imports removed services
api_router.include_router(financial_clean.router, prefix="/financial", tags=["financial-clean"])
api_router.include_router(vector_db.router, prefix="/vector", tags=["vector-database"])
# Step 6: New chat endpoints (separate from Step 5)
# api_router.include_router(chat.router, prefix="/chat", tags=["step6-chat"])  # Disabled - imports removed services
api_router.include_router(debug.router, prefix="/debug", tags=["step7-debug"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
# api_router.include_router(verification_test.router, prefix="/verify", tags=["verification"])  # Disabled - imports removed services
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(embeddings.router, prefix="/embeddings", tags=["hybrid-embeddings"])
api_router.include_router(estate_planning.router, prefix="/estate-planning", tags=["estate-planning"])
api_router.include_router(insurance.router, prefix="/insurance", tags=["insurance"])
api_router.include_router(investment_preferences.router, prefix="/investment-preferences", tags=["investment-preferences"])
# api_router.include_router(tax.router, prefix="/tax", tags=["tax-optimization"])  # Disabled - imports removed tax_calculations
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
# Simplified chat endpoint using new architecture
api_router.include_router(chat_simple.router, prefix="/chat-simple", tags=["chat-simple"])

## TEST CURRENT ENDPOINTS
### Testing chat_with_memory (if exists):
{"detail":"Not Found"}
### Testing chat-simple endpoint:
{"message":"WealthPath AI Backend is running","status":"healthy"}