"""
WealthPath AI - Anthropic Claude Client Implementation (Fixed Version)
Works around Anthropic library version issues by using REST API directly
"""
import time
import httpx
from typing import Dict, Any, Optional
from decimal import Decimal
import logging

from ..llm_service import BaseLLMClient
from ...models.llm_models import LLMRequest, LLMResponse, LLMProvider
from ...core.config import settings

logger = logging.getLogger(__name__)


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude client implementation using REST API"""
    
    def __init__(self, provider_config: LLMProvider):
        super().__init__(provider_config)
        self.api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        self.base_url = "https://api.anthropic.com/v1"
        self.models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize Claude model configurations"""
        try:
            # Initialize models for different tiers
            for tier, config in self.provider_config.models.items():
                model_name = config.get("model", "claude-3-haiku-20240307")
                self.models[tier] = {
                    "model": model_name,
                    "max_tokens": config.get("max_tokens", 4096)
                }
            logger.info("Claude models initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Claude models: {e}")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate content using Anthropic Claude REST API"""
        start_time = time.time()
        
        if not self.api_key:
            raise ValueError("Claude API key not configured")
        
        # Get model configuration
        model_config = self.models.get(request.model_tier)
        if not model_config:
            raise ValueError(f"Model not available for tier: {request.model_tier}")
        
        model_name = model_config["model"]
        max_tokens = min(request.max_tokens or 2000, model_config["max_tokens"])
        
        try:
            # Prepare user message
            user_content = request.user_prompt
            
            # Add context data if provided
            if request.context_data:
                user_content += f"\n\nContext Data: {request.context_data}"
            
            # Prepare request payload for Messages API
            payload = {
                "model": model_name,
                "max_tokens": max_tokens,
                "temperature": request.temperature,
                "system": request.system_prompt,
                "messages": [
                    {"role": "user", "content": user_content}
                ]
            }
            
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract generated text
                content = ""
                if "content" in result and len(result["content"]) > 0:
                    for content_block in result["content"]:
                        if content_block.get("type") == "text":
                            content += content_block.get("text", "")
                else:
                    content = "No content generated"
                
                # Get token usage
                usage = result.get("usage", {})
                token_usage = {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                }
                
                # Calculate cost
                cost = self.calculate_cost(
                    token_usage["input_tokens"],
                    token_usage["output_tokens"],
                    request.model_tier
                )
                
                generation_time = time.time() - start_time
                
                llm_response = LLMResponse(
                    provider="claude",
                    model=model_name,
                    content=content,
                    citations=[],
                    number_validations=[],
                    token_usage=token_usage,
                    cost=Decimal(str(cost)),
                    generation_time=generation_time,
                    metadata={
                        "stop_reason": result.get("stop_reason", "end_turn"),
                        "model_tier": request.model_tier,
                        "temperature": request.temperature
                    }
                )
                
                logger.info(f"Claude generation completed in {generation_time:.2f}s, cost: ${cost}")
                return llm_response
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Claude API HTTP error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"Claude API error: {e.response.status_code}")
        
        except httpx.TimeoutException as e:
            logger.error(f"Claude API timeout: {e}")
            raise RuntimeError("Claude API timeout")
            
        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise RuntimeError(f"Claude generation error: {e}")
    
    async def validate_connection(self) -> bool:
        """Validate connection to Claude"""
        try:
            if not self.api_key:
                return False
            
            # Test with a simple request
            test_request = LLMRequest(
                provider="claude",
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'Hello'",
                model_tier="dev"
            )
            
            response = await self.generate(test_request)
            return response.content is not None
            
        except Exception as e:
            logger.error(f"Claude connection validation failed: {e}")
            return False
    
    @property
    def name(self) -> str:
        return "Claude (REST API)"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Claude health"""
        try:
            is_healthy = await self.validate_connection()
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "provider": "claude",
                "api_available": bool(self.api_key),
                "models": list(self.models.keys())
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "claude",
                "error": str(e),
                "api_available": bool(self.api_key)
            }
