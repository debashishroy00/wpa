=== LLM INTEGRATION AUDIT ===
Generated: Sun, Aug 31, 2025 11:41:32 PM

## LLM Client Registration
backend/app/api/v1/endpoints/auth.py:@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
backend/app/api/v1/endpoints/auth.py:def register(
backend/app/api/v1/endpoints/auth.py:        logger.info("User registered successfully", user_id=user.id, email=user.email)
backend/app/api/v1/endpoints/calculation_debug.py:        # Check if we have registered clients
backend/app/api/v1/endpoints/calculation_debug.py:                "error": "No LLM clients registered",
backend/app/api/v1/endpoints/calculation_debug.py:                    "registered_clients": list(llm_service.clients.keys())
backend/app/api/v1/endpoints/chat_with_memory.py:    from app.services.llm_clients.openai_client import OpenAIClient
backend/app/api/v1/endpoints/chat_with_memory.py:        openai_client = OpenAIClient(llm_service.providers["openai"])
backend/app/api/v1/endpoints/chat_with_memory.py:        llm_service.register_client("openai", openai_client)
backend/app/api/v1/endpoints/chat_with_memory.py:        logger.info("OpenAI client registered for chat memory")
backend/app/api/v1/endpoints/chat_with_memory.py:        from app.services.llm_clients.gemini_client import GeminiClient
backend/app/api/v1/endpoints/chat_with_memory.py:            gemini_client = GeminiClient(llm_service.providers["gemini"])
backend/app/api/v1/endpoints/chat_with_memory.py:            llm_service.register_client("gemini", gemini_client)
backend/app/api/v1/endpoints/chat_with_memory.py:            logger.info("Gemini client registered for chat memory")
backend/app/api/v1/endpoints/llm.py:from ....services.llm_clients import OpenAIClient, GeminiClient, ClaudeClient
backend/app/api/v1/endpoints/llm.py:    """Initialize and register LLM clients"""
backend/app/api/v1/endpoints/llm.py:            openai_client = OpenAIClient(llm_service.providers["openai"])
backend/app/api/v1/endpoints/llm.py:            llm_service.register_client("openai", openai_client)
backend/app/api/v1/endpoints/llm.py:            logger.info("OpenAI client registered")
backend/app/api/v1/endpoints/llm.py:            gemini_client = GeminiClient(llm_service.providers["gemini"])
backend/app/api/v1/endpoints/llm.py:            llm_service.register_client("gemini", gemini_client)
backend/app/api/v1/endpoints/llm.py:            logger.info("Gemini client registered")
backend/app/api/v1/endpoints/llm.py:            llm_service.register_client("claude", claude_client)
backend/app/api/v1/endpoints/llm.py:            logger.info("Claude client registered")
backend/app/api/v1/endpoints/llm.py:        # Fallback to demo mode if no LLM clients are registered
backend/app/api/v1/endpoints/llm.py:        if "No client registered" in str(e):
backend/app/db/base.py:# Import all models so they are registered with SQLAlchemy
backend/app/models/__init__.py:# Import all models to ensure they're registered with SQLAlchemy
backend/app/services/embeddings/alerts.py:        """Send alert to all registered handlers"""
backend/app/services/embeddings/cache.py:            "broker dealer", "registered investment advisor", "fee only advisor",
backend/app/services/llm_clients/gemini_client.py:class GeminiClient(BaseLLMClient):
backend/app/services/llm_clients/openai_client.py:class OpenAIClient(BaseLLMClient):
backend/app/services/llm_clients/__init__.py:from .openai_client import OpenAIClient
backend/app/services/llm_clients/__init__.py:    from .gemini_client import GeminiClient
backend/app/services/llm_clients/__init__.py:    class GeminiClient:
backend/app/services/llm_clients/__init__.py:__all__ = ['OpenAIClient', 'GeminiClient', 'ClaudeClient']
backend/app/services/llm_service.py:    def register_client(self, provider_id: str, client: BaseLLMClient):
backend/app/services/llm_service.py:            raise ValueError(f"No client registered for provider: {request.provider}")
