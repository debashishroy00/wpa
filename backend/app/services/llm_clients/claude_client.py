"""
WealthPath AI - Anthropic Claude Client Implementation  
Anthropic Claude integration for advisory content generation
"""
import time
import anthropic
from typing import Dict, Any, Optional
from decimal import Decimal
import logging

from ..llm_service import BaseLLMClient
from ...models.llm_models import LLMRequest, LLMResponse, LLMProvider
from ...core.config import settings

logger = logging.getLogger(__name__)


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude client implementation"""
    
    def __init__(self, provider_config: LLMProvider):
        super().__init__(provider_config)
        self.client = anthropic.AsyncAnthropic(
            api_key=getattr(settings, 'ANTHROPIC_API_KEY', None)
        )
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate content using Anthropic Claude"""
        start_time = time.time()
        
        # Get model configuration
        model_config = self.provider_config.models.get(request.model_tier, {})
        model_name = model_config.get("model", "claude-3-haiku-20240307")
        max_tokens = min(request.max_tokens or 2000, model_config.get("max_tokens", 4096))
        
        try:
            # Prepare user message
            user_content = request.user_prompt
            
            # Add context data if provided
            if request.context_data:
                user_content += f"\n\nContext Data: {request.context_data}"
            
            # Call Claude API
            response = await self.client.messages.create(
                model=model_name,
                max_tokens=max_tokens,
                temperature=request.temperature,
                system=request.system_prompt,
                messages=[
                    {"role": "user", "content": user_content}
                ]
            )
            
            # Extract response data
            content = ""
            for content_block in response.content:
                if content_block.type == "text":
                    content += content_block.text
            
            # Get token usage
            token_usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
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
                    "stop_reason": response.stop_reason,
                    "stop_sequence": response.stop_sequence,
                    "model_tier": request.model_tier,
                    "temperature": request.temperature
                }
            )
            
            logger.info(f"Claude generation completed in {generation_time:.2f}s, cost: ${cost}")
            return llm_response
            
        except anthropic.RateLimitError as e:
            logger.error(f"Claude rate limit exceeded: {e}")
            raise RuntimeError(f"Claude rate limit exceeded: {e}")
        
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise RuntimeError(f"Claude API error: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected Claude error: {e}")
            raise RuntimeError(f"Claude generation failed: {e}")
    
    async def validate_connection(self) -> bool:
        """Validate connection to Claude"""
        try:
            # Make a minimal test request
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return bool(response.content)
        except Exception as e:
            logger.error(f"Claude connection validation failed: {e}")
            return False
    
    def _handle_tool_use(self, response) -> str:
        """Handle tool use in Claude responses"""
        content = ""
        for content_block in response.content:
            if content_block.type == "text":
                content += content_block.text
            elif content_block.type == "tool_use":
                # Handle tool use if needed in future
                logger.info(f"Tool use detected: {content_block.name}")
        return content