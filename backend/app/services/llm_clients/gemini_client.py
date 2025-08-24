"""
WealthPath AI - Google Gemini Client Implementation (Fixed Version)
Works around Google Gemini library import issues by using REST API directly
"""
import time
import httpx
from typing import Dict, Any, Optional
from decimal import Decimal
import logging
import json

from ..llm_service import BaseLLMClient
from ...models.llm_models import LLMRequest, LLMResponse, LLMProvider
from ...core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Google Gemini client implementation using REST API"""
    
    def __init__(self, provider_config: LLMProvider):
        super().__init__(provider_config)
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize Gemini model configurations"""
        try:
            # Initialize models for different tiers
            for tier, config in self.provider_config.models.items():
                model_name = config.get("model", "gemini-1.5-flash")
                self.models[tier] = {
                    "model": model_name,
                    "max_tokens": config.get("max_tokens", 8192),
                    "temperature": 0.3,
                    "top_p": 0.95,
                    "top_k": 64
                }
            logger.info("Gemini models initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini models: {e}")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate content using Google Gemini REST API"""
        start_time = time.time()
        
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        
        # Get model configuration
        model_config = self.models.get(request.model_tier)
        if not model_config:
            raise ValueError(f"Model not available for tier: {request.model_tier}")
        
        model_name = model_config["model"]
        
        try:
            # Prepare request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"{request.system_prompt}\n\nUser: {request.user_prompt}"
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": model_config["temperature"],
                    "topK": model_config["top_k"],
                    "topP": model_config["top_p"],
                    "maxOutputTokens": model_config["max_tokens"]
                }
            }
            
            # Make API request
            url = f"{self.base_url}/models/{model_name}:generateContent"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    params={"key": self.api_key},
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract generated text
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        generated_text = candidate["content"]["parts"][0]["text"]
                    else:
                        generated_text = "No content generated"
                else:
                    generated_text = "No response from Gemini"
                
                generation_time = time.time() - start_time
                
                # Estimate token usage (rough estimate)
                input_tokens = len(request.system_prompt.split()) + len(request.user_prompt.split())
                output_tokens = len(generated_text.split())
                total_tokens = input_tokens + output_tokens
                
                # Estimate cost (Gemini pricing is roughly $0.001 per 1K tokens)
                cost = (total_tokens / 1000) * 0.001
                
                llm_response = LLMResponse(
                    provider="gemini",
                    model=model_name,
                    content=generated_text,
                    citations=[],
                    number_validations=[],
                    token_usage={
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens
                    },
                    cost=Decimal(str(cost)),
                    generation_time=generation_time,
                    metadata={
                        "model_tier": request.model_tier,
                        "temperature": model_config["temperature"]
                    }
                )
                
                logger.info(f"Gemini generation completed in {generation_time:.2f}s, cost: ${cost}")
                return llm_response
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini API HTTP error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"Gemini API error: {e.response.status_code}")
        
        except httpx.TimeoutException as e:
            logger.error(f"Gemini API timeout: {e}")
            raise RuntimeError("Gemini API timeout")
            
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise RuntimeError(f"Gemini generation error: {e}")
    
    async def validate_connection(self) -> bool:
        """Validate connection to Gemini"""
        try:
            if not self.api_key:
                return False
            
            # Test with a simple request
            test_request = LLMRequest(
                provider="gemini",
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'Hello'",
                model_tier="dev"
            )
            
            response = await self.generate(test_request)
            return response.content is not None and len(response.content) > 0
            
        except Exception as e:
            logger.error(f"Gemini connection validation failed: {e}")
            return False
    
    @property
    def name(self) -> str:
        return "Gemini (REST API)"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Gemini health"""
        try:
            is_healthy = await self.validate_connection()
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "provider": "gemini",
                "api_available": bool(self.api_key),
                "models": list(self.models.keys())
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "gemini",
                "error": str(e),
                "api_available": bool(self.api_key)
            }