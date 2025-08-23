"""
WealthPath AI - OpenAI Client Implementation
OpenAI GPT integration for advisory content generation
"""
import time
import openai
from typing import Dict, Any, Optional
from decimal import Decimal
import logging

from ..llm_service import BaseLLMClient
from ...models.llm_models import LLMRequest, LLMResponse, LLMProvider
from ...core.config import settings

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client implementation"""
    
    def __init__(self, provider_config: LLMProvider):
        super().__init__(provider_config)
        self.client = openai.AsyncOpenAI(
            api_key=getattr(settings, 'OPENAI_API_KEY', None)
        )
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate content using OpenAI GPT"""
        start_time = time.time()
        
        # Get model configuration
        model_config = self.provider_config.models.get(request.model_tier, {})
        model_name = model_config.get("model", "gpt-3.5-turbo")
        max_tokens = min(request.max_tokens or 2000, model_config.get("max_tokens", 4096))
        
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt}
            ]
            
            # Add context data if provided
            if request.context_data:
                context_message = f"Context Data: {request.context_data}"
                messages.append({"role": "user", "content": context_message})
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=request.temperature,
                presence_penalty=0.0,
                frequency_penalty=0.0
            )
            
            # Extract response data
            content = response.choices[0].message.content
            token_usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            # Calculate cost
            cost = self.calculate_cost(
                token_usage["input_tokens"],
                token_usage["output_tokens"],
                request.model_tier
            )
            
            generation_time = time.time() - start_time
            
            llm_response = LLMResponse(
                provider=self.provider_id,
                model=model_name,
                content=content,
                citations=[],  # Citations will be added by RAG system
                number_validations=[],  # Will be populated by validation service
                token_usage=token_usage,
                cost=cost,
                generation_time=generation_time,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "model_tier": request.model_tier,
                    "temperature": request.temperature
                }
            )
            
            logger.info(f"OpenAI generation completed in {generation_time:.2f}s, cost: ${cost}")
            return llm_response
            
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise RuntimeError(f"OpenAI rate limit exceeded: {e}")
        
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API error: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected OpenAI error: {e}")
            raise RuntimeError(f"OpenAI generation failed: {e}")
    
    async def validate_connection(self) -> bool:
        """Validate connection to OpenAI"""
        try:
            # Make a minimal test request
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI connection validation failed: {e}")
            return False
    
    def _extract_citations(self, content: str, context_data: Dict[str, Any]) -> list:
        """Extract citations from generated content"""
        # Placeholder implementation - would be enhanced with RAG system
        return []
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Rough estimation: ~4 characters per token for English
        return len(text) // 4