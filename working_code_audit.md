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
