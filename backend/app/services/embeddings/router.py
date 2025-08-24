"""
Intelligent routing logic for embedding requests.
Decides between API and local providers based on context, cost, and system state.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from .base import (
    EmbeddingProvider,
    EmbeddingContext,
    EmbeddingRequest,
    EmbeddingResult
)

logger = structlog.get_logger(__name__)

class RoutingReason(str, Enum):
    """Reasons for routing decisions"""
    CONTEXT_REALTIME = "context_realtime"
    CONTEXT_QUALITY = "context_quality"
    CONTEXT_BATCH = "context_batch"
    CONTEXT_SENSITIVE = "context_sensitive"
    COST_LIMIT = "cost_limit"
    API_DEGRADED = "api_degraded"
    RATE_LIMIT = "rate_limit"
    LARGE_BATCH = "large_batch"
    FALLBACK = "fallback"
    USER_PREFERENCE = "user_preference"
    CIRCUIT_BREAKER = "circuit_breaker"

@dataclass
class RoutingDecision:
    """Result of routing decision"""
    provider: EmbeddingProvider
    reason: RoutingReason
    confidence: float  # 0.0 to 1.0
    cost_estimate: float
    expected_latency_ms: float
    fallback_provider: Optional[EmbeddingProvider] = None

@dataclass
class RoutingConfig:
    """Configuration for routing decisions"""
    # Cost limits
    daily_api_budget_usd: float = 10.0
    cost_per_request_threshold: float = 0.01
    
    # Performance thresholds
    realtime_latency_threshold_ms: float = 1000
    batch_size_threshold: int = 100
    
    # Quality requirements
    quality_contexts: List[EmbeddingContext] = None
    
    # PII detection patterns
    pii_patterns: List[str] = None
    
    # API health thresholds
    api_error_rate_threshold: float = 0.1  # 10%
    api_latency_threshold_ms: float = 5000
    
    def __post_init__(self):
        if self.quality_contexts is None:
            self.quality_contexts = [
                EmbeddingContext.ANALYSIS,
                EmbeddingContext.SEARCH
            ]
        
        if self.pii_patterns is None:
            self.pii_patterns = [
                r'\b\d{3}-\d{2}-\d{4}\b',        # SSN
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b\d{3}-\d{3}-\d{4}\b',        # Phone number
                r'\b\d{5}(-\d{4})?\b'            # ZIP code
            ]

class PIIDetector:
    """Detect personally identifiable information in text"""
    
    def __init__(self, patterns: List[str]):
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def contains_pii(self, text: str) -> Tuple[bool, List[str]]:
        """Check if text contains PII and return detected types"""
        detected_types = []
        
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(text):
                detected_types.append(f"pattern_{i}")
        
        return len(detected_types) > 0, detected_types

class EmbeddingRouter:
    """Intelligent router for embedding requests"""
    
    def __init__(self, config: RoutingConfig = None):
        self.config = config or RoutingConfig()
        self.pii_detector = PIIDetector(self.config.pii_patterns)
        
        # Tracking
        self.daily_api_cost = 0.0
        self.api_request_count = 0
        self.api_error_count = 0
        self.api_latency_history = []
        
        logger.info("Embedding router initialized", config=self.config)
    
    def route_request(
        self,
        request: EmbeddingRequest,
        api_health: Dict[str, Any],
        local_health: Dict[str, Any]
    ) -> RoutingDecision:
        """Make routing decision for embedding request"""
        
        # Check user preference first
        if request.preferred_provider:
            return RoutingDecision(
                provider=request.preferred_provider,
                reason=RoutingReason.USER_PREFERENCE,
                confidence=1.0,
                cost_estimate=self._estimate_cost(request, request.preferred_provider),
                expected_latency_ms=self._estimate_latency(request, request.preferred_provider)
            )
        
        # Check for PII - force local if detected
        pii_detected = any(
            self.pii_detector.contains_pii(text)[0] 
            for text in request.texts
        )
        
        if pii_detected:
            return RoutingDecision(
                provider=EmbeddingProvider.LOCAL,
                reason=RoutingReason.CONTEXT_SENSITIVE,
                confidence=1.0,
                cost_estimate=0.0,
                expected_latency_ms=self._estimate_latency(request, EmbeddingProvider.LOCAL)
            )
        
        # Check API health - fallback to local if unhealthy
        if not self._is_api_healthy(api_health):
            return RoutingDecision(
                provider=EmbeddingProvider.LOCAL,
                reason=RoutingReason.API_DEGRADED,
                confidence=0.8,
                cost_estimate=0.0,
                expected_latency_ms=self._estimate_latency(request, EmbeddingProvider.LOCAL)
            )
        
        # Check cost limits
        if self._would_exceed_budget(request):
            return RoutingDecision(
                provider=EmbeddingProvider.LOCAL,
                reason=RoutingReason.COST_LIMIT,
                confidence=0.9,
                cost_estimate=0.0,
                expected_latency_ms=self._estimate_latency(request, EmbeddingProvider.LOCAL)
            )
        
        # Large batch - prefer local for cost efficiency
        if request.is_large_batch:
            return RoutingDecision(
                provider=EmbeddingProvider.LOCAL,
                reason=RoutingReason.LARGE_BATCH,
                confidence=0.8,
                cost_estimate=0.0,
                expected_latency_ms=self._estimate_latency(request, EmbeddingProvider.LOCAL),
                fallback_provider=EmbeddingProvider.OPENAI
            )
        
        # Context-based routing
        return self._route_by_context(request)
    
    def _route_by_context(self, request: EmbeddingRequest) -> RoutingDecision:
        """Route based on request context"""
        context = request.context
        
        if context == EmbeddingContext.REALTIME:
            # Prefer local for speed, fallback to API if local slow
            local_latency = self._estimate_latency(request, EmbeddingProvider.LOCAL)
            
            if local_latency <= self.config.realtime_latency_threshold_ms:
                return RoutingDecision(
                    provider=EmbeddingProvider.LOCAL,
                    reason=RoutingReason.CONTEXT_REALTIME,
                    confidence=0.7,
                    cost_estimate=0.0,
                    expected_latency_ms=local_latency,
                    fallback_provider=EmbeddingProvider.OPENAI
                )
            else:
                return RoutingDecision(
                    provider=EmbeddingProvider.OPENAI,
                    reason=RoutingReason.CONTEXT_REALTIME,
                    confidence=0.6,
                    cost_estimate=self._estimate_cost(request, EmbeddingProvider.OPENAI),
                    expected_latency_ms=self._estimate_latency(request, EmbeddingProvider.OPENAI)
                )
        
        elif context == EmbeddingContext.BATCH:
            # Prefer local for cost efficiency
            return RoutingDecision(
                provider=EmbeddingProvider.LOCAL,
                reason=RoutingReason.CONTEXT_BATCH,
                confidence=0.8,
                cost_estimate=0.0,
                expected_latency_ms=self._estimate_latency(request, EmbeddingProvider.LOCAL),
                fallback_provider=EmbeddingProvider.OPENAI
            )
        
        elif context in self.config.quality_contexts:
            # Prefer API for quality
            return RoutingDecision(
                provider=EmbeddingProvider.OPENAI,
                reason=RoutingReason.CONTEXT_QUALITY,
                confidence=0.8,
                cost_estimate=self._estimate_cost(request, EmbeddingProvider.OPENAI),
                expected_latency_ms=self._estimate_latency(request, EmbeddingProvider.OPENAI),
                fallback_provider=EmbeddingProvider.LOCAL
            )
        
        else:
            # Default to local (cost-effective)
            return RoutingDecision(
                provider=EmbeddingProvider.LOCAL,
                reason=RoutingReason.FALLBACK,
                confidence=0.5,
                cost_estimate=0.0,
                expected_latency_ms=self._estimate_latency(request, EmbeddingProvider.LOCAL),
                fallback_provider=EmbeddingProvider.OPENAI
            )
    
    def _is_api_healthy(self, api_health: Dict[str, Any]) -> bool:
        """Check if API is healthy enough to use"""
        if api_health.get("status") != "healthy":
            return False
        
        # Check circuit breaker
        circuit_state = api_health.get("circuit_breaker", {})
        if circuit_state.get("state") == "open":
            return False
        
        # Check error rate
        if self.api_request_count > 10:  # Need some sample size
            error_rate = self.api_error_count / self.api_request_count
            if error_rate > self.config.api_error_rate_threshold:
                return False
        
        # Check latency
        if self.api_latency_history:
            avg_latency = sum(self.api_latency_history[-10:]) / min(10, len(self.api_latency_history))
            if avg_latency > self.config.api_latency_threshold_ms:
                return False
        
        return True
    
    def _would_exceed_budget(self, request: EmbeddingRequest) -> bool:
        """Check if request would exceed daily budget"""
        estimated_cost = self._estimate_cost(request, EmbeddingProvider.OPENAI)
        
        # Check daily budget
        if self.daily_api_cost + estimated_cost > self.config.daily_api_budget_usd:
            return True
        
        # Check per-request threshold
        if estimated_cost > self.config.cost_per_request_threshold:
            return True
        
        return False
    
    def _estimate_cost(self, request: EmbeddingRequest, provider: EmbeddingProvider) -> float:
        """Estimate cost for request"""
        if provider == EmbeddingProvider.LOCAL:
            return 0.0
        
        # Rough token estimation for OpenAI
        total_tokens = sum(len(text.split()) * 1.3 for text in request.texts)
        cost_per_1k = 0.00002  # text-embedding-3-small default
        
        return (total_tokens / 1000) * cost_per_1k
    
    def _estimate_latency(self, request: EmbeddingRequest, provider: EmbeddingProvider) -> float:
        """Estimate latency for request"""
        text_count = len(request.texts)
        
        if provider == EmbeddingProvider.LOCAL:
            # Local latency estimation (ms)
            base_latency = 100  # Model overhead
            per_text_latency = 50  # Per text processing
            return base_latency + (text_count * per_text_latency)
        
        else:  # OpenAI API
            # API latency estimation (ms)
            base_latency = 200  # Network overhead
            per_text_latency = 20  # API processing per text
            return base_latency + (text_count * per_text_latency)
    
    def record_request_result(self, result: EmbeddingResult) -> None:
        """Record result for routing optimization"""
        if result.provider == EmbeddingProvider.OPENAI:
            self.api_request_count += 1
            
            if result.cost_usd:
                self.daily_api_cost += result.cost_usd
            
            self.api_latency_history.append(result.latency_ms)
            if len(self.api_latency_history) > 100:
                self.api_latency_history.pop(0)
    
    def record_request_error(self, provider: EmbeddingProvider, error: Exception) -> None:
        """Record error for routing optimization"""
        if provider == EmbeddingProvider.OPENAI:
            self.api_error_count += 1
        
        logger.warning(
            "Embedding request error recorded",
            provider=provider.value,
            error=str(error)
        )
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "daily_api_cost": round(self.daily_api_cost, 4),
            "api_request_count": self.api_request_count,
            "api_error_count": self.api_error_count,
            "api_error_rate": self.api_error_count / max(1, self.api_request_count),
            "average_api_latency": (
                sum(self.api_latency_history) / len(self.api_latency_history)
                if self.api_latency_history else 0
            ),
            "budget_utilization": self.daily_api_cost / self.config.daily_api_budget_usd,
            "recent_latency_samples": len(self.api_latency_history)
        }
    
    def reset_daily_stats(self) -> None:
        """Reset daily statistics (call this daily)"""
        self.daily_api_cost = 0.0
        # Keep error rates and latency for trend analysis
        logger.info("Daily routing stats reset")
    
    def update_config(self, new_config: RoutingConfig) -> None:
        """Update routing configuration"""
        self.config = new_config
        self.pii_detector = PIIDetector(self.config.pii_patterns)
        logger.info("Routing configuration updated")