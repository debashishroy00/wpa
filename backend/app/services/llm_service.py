"""
WealthPath AI - Multi-LLM Service Architecture
Base classes and service implementation for multi-LLM integration
"""
import asyncio
import time
import json
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
import logging

from ..models.llm_models import (
    LLMRequest, LLMResponse, LLMProvider, Citation, NumberValidation,
    LLMComparison, AdvisoryGeneration, AdvisoryContent
)
from ..core.config import settings

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, provider_config: LLMProvider):
        self.provider_config = provider_config
        self.provider_id = provider_config.provider_id
        
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate content using the LLM"""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate connection to the LLM provider"""
        pass
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, model_tier: str = "dev") -> Decimal:
        """Calculate generation cost based on token usage"""
        model_config = self.provider_config.models.get(model_tier, {})
        cost_input = self.provider_config.cost_per_1k_tokens_input * Decimal(input_tokens) / Decimal(1000)
        cost_output = self.provider_config.cost_per_1k_tokens_output * Decimal(output_tokens) / Decimal(1000)
        return cost_input + cost_output


class NumberValidator:
    """Validates numbers in LLM responses against source data"""
    
    def __init__(self):
        self.validation_methods = [
            self._exact_match_validation,
            self._range_validation,
            self._calculation_validation,
            self._format_validation
        ]
    
    def validate_numbers(self, 
                        response_content: str, 
                        source_data: Dict[str, Any]) -> List[NumberValidation]:
        """Validate all numbers in response against source data"""
        validations = []
        
        # Extract numbers from response
        import re
        number_pattern = r'\b\d+(?:,\d{3})*(?:\.\d{2})?\b'
        numbers = re.findall(number_pattern, response_content.replace('$', '').replace('%', ''))
        
        for number_str in numbers:
            try:
                number = float(number_str.replace(',', ''))
                validation = self._validate_single_number(number, source_data)
                if validation:
                    validations.append(validation)
            except ValueError:
                continue
                
        return validations
    
    def _validate_single_number(self, 
                               number: float, 
                               source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Validate a single number against source data"""
        for method in self.validation_methods:
            validation = method(number, source_data)
            if validation and validation.is_valid:
                return validation
        
        # If no validation method succeeded, mark as invalid
        return NumberValidation(
            original_number=number,
            validated_number=number,
            is_valid=False,
            confidence_score=0.0,
            validation_method="no_match",
            error_message="Number not found in source data"
        )
    
    def _exact_match_validation(self, 
                               number: float, 
                               source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Check for exact matches in source data"""
        def search_dict(data, target):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)) and abs(value - target) < 0.01:
                        return True
                    elif isinstance(value, (dict, list)):
                        if search_dict(value, target):
                            return True
            elif isinstance(data, list):
                for item in data:
                    if search_dict(item, target):
                        return True
            return False
        
        if search_dict(source_data, number):
            return NumberValidation(
                original_number=number,
                validated_number=number,
                is_valid=True,
                confidence_score=1.0,
                validation_method="exact_match"
            )
        return None
    
    def _range_validation(self, 
                         number: float, 
                         source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Check if number falls within expected ranges"""
        # Implementation for range validation
        return None
    
    def _calculation_validation(self, 
                               number: float, 
                               source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Check if number can be derived from calculations"""
        # Implementation for calculation validation
        return None
    
    def _format_validation(self, 
                          number: float, 
                          source_data: Dict[str, Any]) -> Optional[NumberValidation]:
        """Check if number format is appropriate"""
        # Implementation for format validation
        return None


class ResponseCache:
    """In-memory cache for LLM responses"""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_hours * 3600
    
    def _generate_key(self, request: LLMRequest) -> str:
        """Generate cache key from request"""
        key_data = {
            "provider": request.provider,
            "model_tier": request.model_tier,
            "system_prompt": request.system_prompt,
            "user_prompt": request.user_prompt,
            "context_data": request.context_data,
            "temperature": request.temperature
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, request: LLMRequest) -> Optional[LLMResponse]:
        """Get cached response"""
        key = self._generate_key(request)
        entry = self.cache.get(key)
        
        if entry is None:
            return None
        
        # Check TTL
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            del self.cache[key]
            return None
        
        return entry["response"]
    
    def set(self, request: LLMRequest, response: LLMResponse):
        """Cache response"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
        
        key = self._generate_key(request)
        self.cache[key] = {
            "response": response,
            "timestamp": time.time()
        }


class MultiLLMService:
    """Main service for managing multiple LLM providers"""
    
    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.providers: Dict[str, LLMProvider] = {}
        self.number_validator = NumberValidator()
        self.cache = ResponseCache()
        self.load_provider_configs()
    
    def load_provider_configs(self):
        """Load LLM provider configurations"""
        # OpenAI Configuration
        self.providers["openai"] = LLMProvider(
            provider_id="openai",
            name="OpenAI GPT",
            cost_per_1k_tokens_input=Decimal("0.0015"),
            cost_per_1k_tokens_output=Decimal("0.002"),
            models={
                "dev": {
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 4096,
                    "context_window": 16385
                },
                "prod": {
                    "model": "gpt-4-turbo-preview", 
                    "max_tokens": 4096,
                    "context_window": 128000
                }
            }
        )
        
        # Gemini Configuration
        self.providers["gemini"] = LLMProvider(
            provider_id="gemini",
            name="Google Gemini",
            cost_per_1k_tokens_input=Decimal("0.00075"),
            cost_per_1k_tokens_output=Decimal("0.0015"),
            models={
                "dev": {
                    "model": "gemini-1.5-flash",
                    "max_tokens": 8192,
                    "context_window": 1048576
                },
                "prod": {
                    "model": "gemini-1.5-pro",
                    "max_tokens": 8192,
                    "context_window": 2097152
                }
            }
        )
        
        # Claude Configuration  
        self.providers["claude"] = LLMProvider(
            provider_id="claude",
            name="Anthropic Claude",
            cost_per_1k_tokens_input=Decimal("0.003"),
            cost_per_1k_tokens_output=Decimal("0.015"),
            models={
                "dev": {
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 4096,
                    "context_window": 200000
                },
                "prod": {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4096,
                    "context_window": 200000
                }
            }
        )
    
    def register_client(self, provider_id: str, client: BaseLLMClient):
        """Register an LLM client"""
        self.clients[provider_id] = client
        logger.info(f"Registered LLM client for provider: {provider_id}")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate content using specified provider with mode support"""
        # Extract mode from request (default to balanced)
        mode = getattr(request, 'mode', 'balanced')
        
        # Adjust temperature based on mode
        original_temp = request.temperature or 0.3
        request.temperature = self._get_temperature_for_mode(mode, original_temp)
        
        # Adjust system prompt based on mode
        request.system_prompt = self._enhance_prompt_for_mode(request.system_prompt, mode)
        
        # Check cache first
        cached_response = self.cache.get(request)
        if cached_response:
            logger.info(f"Returning cached response for {request.provider} (mode: {mode})")
            return cached_response
        
        # Get client
        client = self.clients.get(request.provider)
        if not client:
            raise ValueError(f"No client registered for provider: {request.provider}")
        
        # Generate response
        start_time = time.time()
        response = await client.generate(request)
        
        # Validate numbers if context data provided
        if request.context_data:
            validations = self.number_validator.validate_numbers(
                response.content, request.context_data
            )
            response.number_validations = validations
        
        # Cache response
        self.cache.set(request, response)
        
        logger.info(f"Generated response using {request.provider} in {time.time() - start_time:.2f}s (mode: {mode}, temp: {request.temperature})")
        return response
    
    async def compare_providers(self, 
                               request: LLMRequest, 
                               providers: Optional[List[str]] = None) -> LLMComparison:
        """Generate responses from multiple providers for comparison"""
        if providers is None:
            providers = list(self.clients.keys())
        
        # Generate requests for each provider
        tasks = []
        for provider in providers:
            provider_request = request.model_copy()
            provider_request.provider = provider
            tasks.append(self.generate(provider_request))
        
        # Execute in parallel
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful responses
        successful_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, LLMResponse):
                successful_responses.append(response)
            else:
                logger.error(f"Provider {providers[i]} failed: {response}")
        
        if not successful_responses:
            raise RuntimeError("All providers failed to generate responses")
        
        # Calculate comparison metrics
        total_cost = sum(r.cost for r in successful_responses)
        fastest_provider = min(successful_responses, key=lambda r: r.generation_time).provider
        most_cost_effective = min(successful_responses, key=lambda r: r.cost).provider
        
        # Calculate consensus score (simplified)
        consensus_score = 0.8  # Placeholder implementation
        
        comparison = LLMComparison(
            request_id=hashlib.md5(f"{time.time()}{request.user_prompt}".encode()).hexdigest()[:8],
            responses=successful_responses,
            total_cost=total_cost,
            fastest_provider=fastest_provider,
            most_cost_effective=most_cost_effective,
            consensus_score=consensus_score
        )
        
        logger.info(f"Compared {len(successful_responses)} providers in {time.time() - start_time:.2f}s")
        return comparison
    
    async def generate_advisory_content(self, 
                                       generation_request: AdvisoryGeneration) -> AdvisoryContent:
        """Generate advisory content with Step 4/5 architecture"""
        # Prepare LLM request
        system_prompt = self._build_advisory_system_prompt(generation_request)
        user_prompt = self._build_advisory_user_prompt(generation_request)
        
        # Select provider
        provider = (generation_request.provider_preferences[0] 
                   if generation_request.provider_preferences 
                   else "openai")
        
        llm_request = LLMRequest(
            provider=provider,
            model_tier="prod",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context_data=generation_request.step4_data,
            temperature=0.1,  # Lower temperature for more consistent structured output
            max_tokens=4000   # Increased tokens to prevent content truncation
        )
        
        # Generate response
        if generation_request.enable_comparison:
            comparison = await self.compare_providers(
                llm_request, generation_request.provider_preferences
            )
            # Use best response based on criteria
            llm_response = min(comparison.responses, key=lambda r: r.cost)
        else:
            llm_response = await self.generate(llm_request)
        
        # Create advisory content
        generation_id = hashlib.md5(f"{time.time()}{provider}".encode()).hexdigest()[:8]
        
        advisory_content = AdvisoryContent(
            generation_id=generation_id,
            content_type=generation_request.generation_type,
            content=llm_response.content,
            llm_response=llm_response,
            validation_results=llm_response.number_validations,
            quality_score=self._calculate_quality_score(llm_response)
        )
        
        return advisory_content
    
    def _build_advisory_system_prompt(self, request: AdvisoryGeneration) -> str:
        """Build system prompt for advisory generation"""
        base_prompt = """You are a senior fiduciary financial advisor providing comprehensive wealth management guidance. 
        Your role is to transform technical financial calculations into professional advisory recommendations.
        
        CRITICAL REQUIREMENTS:
        1. NEVER modify, estimate, or guess any numbers from the provided data
        2. Use ONLY the exact numbers provided in the Step 4 data
        3. Generate COMPLETE sections - do not truncate any content
        4. Include specific dollar amounts, percentages, and timelines in every recommendation
        5. Cite sources as [plan engine] for calculations and [KB-XXX] for research references
        6. Maintain professional, confident tone appropriate for high-net-worth clients
        
        MANDATORY STRUCTURE - Generate ALL sections completely:
        ## Executive Summary (2-3 detailed paragraphs with specific numbers)
        ## Immediate Actions (Next 30 Days) (5-7 specific actions with dollar impacts)
        ## 12-Month Strategy (4 quarterly milestones with measurable targets)
        ## Risk Management (stress scenarios and contingency plans)
        ## Tax Considerations (specific tax optimization strategies)
        
        IMPORTANT: Generate ALL sections completely. Do not truncate. Include specific dollar amounts and timelines."""
        
        return base_prompt
    
    def _build_advisory_user_prompt(self, request: AdvisoryGeneration) -> str:
        """Build user prompt for advisory generation"""
        data_summary = json.dumps(request.step4_data, indent=2)
        
        prompt = f"""Based on the following deterministic financial analysis, generate a comprehensive 
        professional advisory report:

        STEP 4 CALCULATIONS:
        {data_summary}
        
        Generate a complete advisory report with EXACTLY these sections:

        ## Executive Summary
        - Interpret the Monte Carlo success rate and what it means for goal achievement
        - Explain the financial gap and required monthly savings [plan engine]
        - Highlight the top 3 strategic opportunities with specific dollar impacts
        
        ## Immediate Actions (Next 30 Days)
        For each action, include:
        - Specific action with exact dollar amount/percentage
        - Implementation timeline (within 30 days)
        - Expected financial impact [plan engine]
        - Account type and contribution limits where applicable
        
        ## 12-Month Strategy
        - Q1 milestone with specific target [plan engine]
        - Q2 milestone with measurable outcome
        - Q3 milestone with portfolio targets
        - Q4 milestone with goal achievement metrics
        
        ## Risk Management
        - Primary risk from the analysis
        - Specific mitigation strategies with numbers
        - Stress test scenarios and contingencies
        
        ## Tax Considerations
        - Tax-advantaged account optimization opportunities
        - Specific annual tax savings amounts [plan engine]
        - Implementation strategies with dollar impacts
        
        REQUIREMENTS:
        - Use ONLY exact numbers from the Step 4 data above
        - Include specific dollar amounts and percentages in every recommendation
        - Cite calculations as [plan engine] and research as [KB-XXX]
        - Make every recommendation actionable with clear next steps
        - Generate ALL sections completely - do not truncate content"""
        
        return prompt
    
    def _calculate_quality_score(self, response: LLMResponse) -> float:
        """Calculate content quality score"""
        score = 1.0
        
        # Penalize for validation errors
        if response.number_validations:
            invalid_count = sum(1 for v in response.number_validations if not v.is_valid)
            if invalid_count > 0:
                score -= (invalid_count / len(response.number_validations)) * 0.3
        
        # Adjust for response length (too short or too long)
        content_length = len(response.content)
        if content_length < 200:
            score -= 0.2
        elif content_length > 2000:
            score -= 0.1
        
        return max(0.0, min(1.0, score))


# Global service instance
llm_service = MultiLLMService()