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

## Startup Initialization
backend/app/api/v1/endpoints/chat_with_memory.py:# Initialize LLM service with clients on first import
backend/app/api/v1/endpoints/chat_with_memory.py:    logger.warning(f"LLM service initialization failed: {e}")
backend/app/api/v1/endpoints/chat_with_memory.py:            raise RuntimeError("LLM service not initialized")
backend/app/api/v1/endpoints/llm.py:# Initialize LLM clients on startup
backend/app/api/v1/endpoints/llm.py:async def initialize_llm_clients():
backend/app/api/v1/endpoints/llm.py:    """Initialize and register LLM clients"""
backend/app/api/v1/endpoints/llm.py:        logger.error(f"Failed to initialize LLM clients: {e}")
backend/app/api/v1/endpoints/llm.py:# LLM clients are now initialized in app lifespan handler (main.py)
backend/app/main.py:    # Initialize LLM clients
backend/app/main.py:        logger.warning(f"LLM service initialization skipped: {e}")

## Working LLM Calls
backend/app/api/v1/endpoints/calculation_debug.py:        llm_response = await llm_service.generate(llm_request)
backend/app/api/v1/endpoints/calculation_debug.py-        response_time = time.time() - start_time
backend/app/api/v1/endpoints/calculation_debug.py-        
backend/app/api/v1/endpoints/calculation_debug.py-        # Validate calculations in response
backend/app/api/v1/endpoints/calculation_debug.py-        validation = memory_service.validate_response_calculations(
backend/app/api/v1/endpoints/calculation_debug.py-            llm_response.content, request.message
--
backend/app/api/v1/endpoints/chat_simple.py:            response = await llm_service.generate(llm_request)
backend/app/api/v1/endpoints/chat_simple.py-            
backend/app/api/v1/endpoints/chat_simple.py-            # Validate
backend/app/api/v1/endpoints/chat_simple.py-            engine = TrustEngine()
backend/app/api/v1/endpoints/chat_simple.py-            validated = engine.validate(response.content, facts)
backend/app/api/v1/endpoints/chat_simple.py-            
--
backend/app/api/v1/endpoints/chat_simple.py:            response = await llm_service.generate(llm_request)
backend/app/api/v1/endpoints/chat_simple.py-            
backend/app/api/v1/endpoints/chat_simple.py-            return ChatResponse(
backend/app/api/v1/endpoints/chat_simple.py-                response=response.content,
backend/app/api/v1/endpoints/chat_simple.py-                confidence="HIGH",
backend/app/api/v1/endpoints/chat_simple.py-                warnings=[],
--
backend/app/api/v1/endpoints/chat_with_memory.py:        response_data = await call_llm_with_memory(
backend/app/api/v1/endpoints/chat_with_memory.py-            prompt_context=optimized_context,
backend/app/api/v1/endpoints/chat_with_memory.py-            provider=request.provider,
backend/app/api/v1/endpoints/chat_with_memory.py-            model_tier=request.model_tier,
backend/app/api/v1/endpoints/chat_with_memory.py-            has_conversation_memory=bool(conversation_context.get("message_count", 0) > 0),
backend/app/api/v1/endpoints/chat_with_memory.py-            user_message=request.message,
--
backend/app/api/v1/endpoints/chat_with_memory.py:async def call_llm_with_memory(
backend/app/api/v1/endpoints/chat_with_memory.py-    prompt_context: str,
backend/app/api/v1/endpoints/chat_with_memory.py-    provider: str = "gemini",
backend/app/api/v1/endpoints/chat_with_memory.py-    model_tier: str = "dev",
backend/app/api/v1/endpoints/chat_with_memory.py-    insight_level: str = "balanced",
backend/app/api/v1/endpoints/chat_with_memory.py-    is_calculation_mode: bool = False,
--
backend/app/api/v1/endpoints/chat_with_memory.py:        llm_response = await llm_service.generate(llm_request)
backend/app/api/v1/endpoints/chat_with_memory.py-        
backend/app/api/v1/endpoints/chat_with_memory.py-        # Convert to expected format
backend/app/api/v1/endpoints/chat_with_memory.py-        response = {
backend/app/api/v1/endpoints/chat_with_memory.py-            "message": {
backend/app/api/v1/endpoints/chat_with_memory.py-                "role": "assistant",
--
backend/app/api/v1/endpoints/chat_with_memory.py:        response_data = await call_llm_with_memory(
backend/app/api/v1/endpoints/chat_with_memory.py-            prompt_context=optimized_context,
backend/app/api/v1/endpoints/chat_with_memory.py-            provider=request.provider,
backend/app/api/v1/endpoints/chat_with_memory.py-            model_tier=request.model_tier,
backend/app/api/v1/endpoints/chat_with_memory.py-            has_conversation_memory=True,
backend/app/api/v1/endpoints/chat_with_memory.py-            user_message=request.message,
--
backend/app/api/v1/endpoints/insights.py:    response = await llm_service.generate(llm_request)
backend/app/api/v1/endpoints/insights.py-    
backend/app/api/v1/endpoints/insights.py-    # Validate
backend/app/api/v1/endpoints/insights.py-    engine = TrustEngine()
backend/app/api/v1/endpoints/insights.py-    validated = engine.validate(response.content, facts)
backend/app/api/v1/endpoints/insights.py-    
--
backend/app/api/v1/endpoints/llm.py:        response = await llm_service.generate(request)
backend/app/api/v1/endpoints/llm.py-        return response
backend/app/api/v1/endpoints/llm.py-        
backend/app/api/v1/endpoints/llm.py-    except Exception as e:
backend/app/api/v1/endpoints/llm.py-        logger.error(f"Content generation failed: {e}")
backend/app/api/v1/endpoints/llm.py-        raise HTTPException(status_code=500, detail=str(e))
--
backend/app/api/v1/endpoints/llm.py:        advisory_content = await llm_service.generate_advisory_content(request)
backend/app/api/v1/endpoints/llm.py-        return advisory_content
backend/app/api/v1/endpoints/llm.py-        
backend/app/api/v1/endpoints/llm.py-    except Exception as e:
backend/app/api/v1/endpoints/llm.py-        logger.error(f"Advisory content generation failed: {e}", exc_info=True)
backend/app/api/v1/endpoints/llm.py-        
--
backend/app/api/v1/endpoints/llm.py:            advisory_content = await llm_service.generate_advisory_content(request)
backend/app/api/v1/endpoints/llm.py-            
backend/app/api/v1/endpoints/llm.py-            # Stream response
backend/app/api/v1/endpoints/llm.py-            yield f"data: {json.dumps({'status': 'completed', 'content': advisory_content.dict()})}\n\n"
backend/app/api/v1/endpoints/llm.py-            
backend/app/api/v1/endpoints/llm.py-        except Exception as e:
