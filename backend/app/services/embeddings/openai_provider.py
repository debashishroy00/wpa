"""
OpenAI embedding provider with circuit breaker and retry logic.
Implements rate limiting, cost tracking, and resilient error handling.
"""

import time
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import openai
import structlog

from .base import (
    BaseEmbeddingProvider,
    EmbeddingResult,
    EmbeddingProvider, 
    EmbeddingConfig,
    EmbeddingDimension
)

logger = structlog.get_logger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, bypass calls
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 3      # Failures before opening
    success_threshold: int = 2      # Successes to close from half-open
    timeout_seconds: int = 60       # Time to wait before half-open
    reset_timeout: int = 300        # Time to reset failure count

class CircuitBreaker:
    """Circuit breaker for OpenAI API calls"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_success_time = 0
        
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        now = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if we should transition to half-open
            if now - self.last_failure_time >= self.config.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker transitioning to half-open")
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful request"""
        now = time.time()
        self.last_success_time = now
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker closed - service recovered")
        elif self.state == CircuitState.CLOSED:
            # Reset failure count after successful operation
            if now - self.last_failure_time >= self.config.reset_timeout:
                self.failure_count = 0
    
    def record_failure(self):
        """Record failed request"""
        now = time.time()
        self.last_failure_time = now
        self.failure_count += 1
        
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    "Circuit breaker opened",
                    failure_count=self.failure_count,
                    threshold=self.config.failure_threshold
                )
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.info("Circuit breaker reopened after half-open failure")
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time
        }

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate_per_minute: int):
        self.rate_per_minute = rate_per_minute
        self.tokens = rate_per_minute
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from bucket"""
        async with self._lock:
            now = time.time()
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(
                self.rate_per_minute,
                self.tokens + elapsed * (self.rate_per_minute / 60)
            )
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider with resilience features"""
    
    # Model configurations
    MODEL_CONFIGS = {
        "text-embedding-3-small": {
            "dimension": 1536,
            "max_tokens": 8192,
            "cost_per_1k_tokens": 0.00002,  # $0.00002 per 1K tokens
            "rate_limit_rpm": 3000
        },
        "text-embedding-3-large": {
            "dimension": 3072,
            "max_tokens": 8192,
            "cost_per_1k_tokens": 0.00013,  # $0.00013 per 1K tokens
            "rate_limit_rpm": 3000
        },
        "text-embedding-ada-002": {
            "dimension": 1536,
            "max_tokens": 8192,
            "cost_per_1k_tokens": 0.0001,   # $0.0001 per 1K tokens
            "rate_limit_rpm": 3000
        }
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True
    ):
        # Validate model
        if model not in self.MODEL_CONFIGS:
            raise ValueError(f"Unknown model: {model}. Available: {list(self.MODEL_CONFIGS.keys())}")
        
        model_info = self.MODEL_CONFIGS[model]
        
        config = EmbeddingConfig(
            provider=EmbeddingProvider.OPENAI,
            model=model,
            dimension=model_info["dimension"],
            max_tokens=model_info["max_tokens"],
            cost_per_1k_tokens=model_info["cost_per_1k_tokens"],
            supports_batch=True,
            max_batch_size=2048,  # OpenAI batch limit
            rate_limit_rpm=model_info["rate_limit_rpm"],
            timeout_seconds=30
        )
        
        super().__init__(config)
        
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(CircuitBreakerConfig())
        
        # Rate limiter
        self.rate_limiter = RateLimiter(model_info["rate_limit_rpm"])
        
        # Cost tracking
        self.total_tokens = 0
        self.total_cost = 0.0
        
        logger.info(
            "OpenAI embedding provider initialized",
            model=model,
            dimension=config.dimension,
            cost_per_1k_tokens=config.cost_per_1k_tokens
        )
    
    @property
    def name(self) -> str:
        return f"openai_{self.model.replace('-', '_')}"
    
    async def initialize(self) -> None:
        """Initialize the provider"""
        self._initialized = True
        logger.info("OpenAI embedding provider ready")
    
    async def generate_embeddings(
        self,
        texts: List[str],
        **kwargs
    ) -> List[EmbeddingResult]:
        """Generate embeddings with circuit breaker and retry logic"""
        if not self._initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            raise Exception("OpenAI API circuit breaker is open")
        
        # Rate limiting
        if not await self.rate_limiter.acquire(len(texts)):
            raise Exception("Rate limit exceeded for OpenAI API")
        
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                # Make API call
                response = await self._call_openai_api(texts)
                
                # Process response
                results = self._process_response(response, texts, start_time)
                
                # Record success
                self.circuit_breaker.record_success()
                
                # Update cost tracking
                total_tokens = sum(r.tokens_used or 0 for r in results)
                total_cost = sum(r.cost_usd or 0 for r in results)
                self.total_tokens += total_tokens
                self.total_cost += total_cost
                
                logger.debug(
                    "Generated OpenAI embeddings",
                    count=len(texts),
                    tokens=total_tokens,
                    cost_usd=round(total_cost, 6),
                    latency_ms=round((time.time() - start_time) * 1000, 2)
                )
                
                return results
                
            except Exception as e:
                is_last_attempt = attempt == self.max_retries - 1
                
                # Check if we should retry
                if self._is_retryable_error(e) and not is_last_attempt:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        "OpenAI API call failed, retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        delay_seconds=delay,
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
                    continue
                
                # Record failure and raise
                self.circuit_breaker.record_failure()
                logger.error(
                    "OpenAI embedding generation failed",
                    attempts=attempt + 1,
                    error=str(e)
                )
                raise
    
    async def _call_openai_api(self, texts: List[str]) -> Any:
        """Make the actual OpenAI API call"""
        return await self.client.embeddings.create(
            input=texts,
            model=self.model,
            encoding_format="float"
        )
    
    def _process_response(
        self,
        response: Any,
        texts: List[str],
        start_time: float
    ) -> List[EmbeddingResult]:
        """Process OpenAI API response"""
        latency_ms = (time.time() - start_time) * 1000
        
        results = []
        for i, embedding_data in enumerate(response.data):
            tokens = self._estimate_tokens(texts[i])
            cost = (tokens / 1000) * self.config.cost_per_1k_tokens
            
            result = EmbeddingResult(
                embedding=embedding_data.embedding,
                provider=EmbeddingProvider.OPENAI,
                model=self.model,
                dimension=len(embedding_data.embedding),
                latency_ms=latency_ms / len(texts),  # Average per text
                tokens_used=tokens,
                cost_usd=cost,
                cached=False,
                cache_hit=False
            )
            results.append(result)
        
        return results
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Rough estimation: 1 token ~= 4 characters
        return max(1, len(text) // 4)
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable"""
        error_str = str(error).lower()
        
        # Rate limit errors
        if "rate limit" in error_str or "429" in error_str:
            return True
        
        # Temporary server errors
        if any(code in error_str for code in ["500", "502", "503", "504"]):
            return True
        
        # Timeout errors
        if "timeout" in error_str:
            return True
        
        # Connection errors
        if "connection" in error_str:
            return True
        
        return False
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter"""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        
        if self.jitter:
            # Add random jitter (±25%)
            import random
            jitter_factor = 0.25 * random.random()
            delay *= (1 + jitter_factor - 0.125)
        
        return delay
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health"""
        try:
            # Quick test with minimal text
            test_result = await self.embed_single("health check")
            
            circuit_state = self.circuit_breaker.get_state()
            
            return {
                "status": "healthy",
                "model": self.model,
                "dimension": self.config.dimension,
                "test_latency_ms": round(test_result.latency_ms, 2),
                "circuit_breaker": circuit_state,
                "total_tokens": self.total_tokens,
                "total_cost_usd": round(self.total_cost, 6),
                "rate_limit_rpm": self.config.rate_limit_rpm
            }
            
        except Exception as e:
            circuit_state = self.circuit_breaker.get_state()
            
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model,
                "circuit_breaker": circuit_state
            }
    
    def get_cost_statistics(self) -> Dict[str, Any]:
        """Get detailed cost statistics"""
        return {
            "model": self.model,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "cost_per_1k_tokens": self.config.cost_per_1k_tokens,
            "projected_monthly_cost": round(self.total_cost * 30, 2),  # Rough projection
            "average_tokens_per_request": self.total_tokens / max(1, self.total_tokens // 100)
        }
    
    async def reset_circuit_breaker(self) -> None:
        """Manually reset circuit breaker"""
        self.circuit_breaker.state = CircuitState.CLOSED
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.success_count = 0
        logger.info("Circuit breaker manually reset")