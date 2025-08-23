"""
WealthPath AI - Google Gemini Client Implementation
Google Gemini integration for advisory content generation
"""
import time
import google.generativeai as genai
from typing import Dict, Any, Optional
from decimal import Decimal
import logging

from ..llm_service import BaseLLMClient
from ...models.llm_models import LLMRequest, LLMResponse, LLMProvider
from ...core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Google Gemini client implementation"""
    
    def __init__(self, provider_config: LLMProvider):
        super().__init__(provider_config)
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if api_key:
            genai.configure(api_key=api_key)
        self.models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize Gemini models"""
        try:
            # Initialize models for different tiers
            for tier, config in self.provider_config.models.items():
                model_name = config.get("model", "gemini-1.5-flash")
                self.models[tier] = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=config.get("max_tokens", 8192),
                        temperature=0.3,
                        top_p=0.95,
                        top_k=64
                    )
                )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini models: {e}")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate content using Google Gemini"""
        start_time = time.time()
        
        # Get model for requested tier
        model = self.models.get(request.model_tier)
        if not model:
            raise ValueError(f"Model not available for tier: {request.model_tier}")
        
        model_config = self.provider_config.models.get(request.model_tier, {})
        model_name = model_config.get("model", "gemini-1.5-flash")
        
        try:
            # Prepare prompt
            prompt_parts = [
                f"System: {request.system_prompt}",
                f"User: {request.user_prompt}"
            ]
            
            # Add context data if provided
            if request.context_data:
                prompt_parts.append(f"Context Data: {request.context_data}")
            
            full_prompt = "\n\n".join(prompt_parts)
            
            # Update generation config for this request
            model._generation_config['temperature'] = request.temperature
            max_tokens = min(request.max_tokens or 2000, model_config.get("max_tokens", 8192))
            model._generation_config['max_output_tokens'] = max_tokens
            
            # Generate response
            response = await model.generate_content_async(full_prompt)
            
            # Check for safety issues
            if not response.text:
                safety_ratings = response.prompt_feedback.safety_ratings if response.prompt_feedback else []
                blocked_reasons = [rating.category.name for rating in safety_ratings 
                                 if rating.probability.name in ['HIGH', 'MEDIUM']]
                if blocked_reasons:
                    raise RuntimeError(f"Content blocked by safety filters: {blocked_reasons}")
                else:
                    raise RuntimeError("Empty response from Gemini")
            
            content = response.text
            
            # Estimate token usage (Gemini doesn't provide exact counts in all cases)
            input_tokens = self._estimate_tokens(full_prompt)
            output_tokens = self._estimate_tokens(content)
            
            token_usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
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
                    "model_tier": request.model_tier,
                    "temperature": request.temperature,
                    "safety_ratings": self._extract_safety_ratings(response) if response.prompt_feedback else {}
                }
            )
            
            logger.info(f"Gemini generation completed in {generation_time:.2f}s, cost: ${cost}")
            return llm_response
            
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise RuntimeError(f"Gemini generation failed: {e}")
    
    async def validate_connection(self) -> bool:
        """Validate connection to Gemini"""
        try:
            # Use the dev tier model for testing
            model = self.models.get("dev")
            if not model:
                return False
            
            response = await model.generate_content_async("test")
            return bool(response.text)
        except Exception as e:
            logger.error(f"Gemini connection validation failed: {e}")
            return False
    
    def _extract_safety_ratings(self, response) -> Dict[str, Any]:
        """Extract safety ratings from response"""
        if not response.prompt_feedback or not response.prompt_feedback.safety_ratings:
            return {}
        
        ratings = {}
        for rating in response.prompt_feedback.safety_ratings:
            ratings[rating.category.name] = {
                "probability": rating.probability.name,
                "blocked": rating.blocked if hasattr(rating, 'blocked') else False
            }
        return ratings
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Rough estimation for Gemini: ~3.5 characters per token
        return int(len(text) / 3.5)