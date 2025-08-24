"""
Monitoring and observability for the hybrid embedding system.
Tracks metrics, performance, costs, and quality across all providers.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import structlog

from .base import EmbeddingProvider, EmbeddingResult, EmbeddingContext
from .router import RoutingDecision, RoutingReason

logger = structlog.get_logger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for embedding operations"""
    total_requests: int = 0
    total_embeddings: int = 0
    total_latency_ms: float = 0.0
    latency_samples: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def add_sample(self, latency_ms: float, embedding_count: int = 1):
        """Add a latency sample"""
        self.total_requests += 1
        self.total_embeddings += embedding_count
        self.total_latency_ms += latency_ms
        self.latency_samples.append(latency_ms)
    
    @property
    def average_latency_ms(self) -> float:
        """Calculate average latency"""
        return self.total_latency_ms / max(1, self.total_requests)
    
    @property
    def p50_latency_ms(self) -> float:
        """50th percentile latency"""
        if not self.latency_samples:
            return 0.0
        return statistics.median(self.latency_samples)
    
    @property
    def p95_latency_ms(self) -> float:
        """95th percentile latency"""
        if len(self.latency_samples) < 20:
            return self.average_latency_ms
        return statistics.quantiles(self.latency_samples, n=20)[18]  # 95th percentile
    
    @property
    def p99_latency_ms(self) -> float:
        """99th percentile latency"""
        if len(self.latency_samples) < 100:
            return self.p95_latency_ms
        return statistics.quantiles(self.latency_samples, n=100)[98]  # 99th percentile

@dataclass
class CostMetrics:
    """Cost tracking metrics"""
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    requests_by_provider: Dict[str, int] = field(default_factory=dict)
    cost_by_provider: Dict[str, float] = field(default_factory=dict)
    
    def add_cost(self, provider: EmbeddingProvider, cost_usd: float, tokens: int = 0):
        """Add cost data"""
        self.total_cost_usd += cost_usd
        self.total_tokens += tokens
        
        provider_str = provider.value
        self.requests_by_provider[provider_str] = self.requests_by_provider.get(provider_str, 0) + 1
        self.cost_by_provider[provider_str] = self.cost_by_provider.get(provider_str, 0.0) + cost_usd
    
    @property
    def average_cost_per_request(self) -> float:
        """Average cost per request"""
        total_requests = sum(self.requests_by_provider.values())
        return self.total_cost_usd / max(1, total_requests)
    
    @property
    def cost_per_1k_tokens(self) -> float:
        """Cost per 1000 tokens"""
        return (self.total_cost_usd * 1000) / max(1, self.total_tokens)

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    l1_hits: int = 0
    l2_hits: int = 0
    cache_misses: int = 0
    
    def record_hit(self, cache_level: str):
        """Record cache hit"""
        self.total_requests += 1
        self.cache_hits += 1
        if cache_level == "l1":
            self.l1_hits += 1
        elif cache_level == "l2":
            self.l2_hits += 1
    
    def record_miss(self):
        """Record cache miss"""
        self.total_requests += 1
        self.cache_misses += 1
    
    @property
    def hit_rate(self) -> float:
        """Overall cache hit rate"""
        return self.cache_hits / max(1, self.total_requests)
    
    @property
    def l1_hit_rate(self) -> float:
        """L1 cache hit rate"""
        return self.l1_hits / max(1, self.total_requests)
    
    @property
    def l2_hit_rate(self) -> float:
        """L2 cache hit rate"""
        return self.l2_hits / max(1, self.total_requests)

@dataclass
class QualityMetrics:
    """Embedding quality comparison metrics"""
    comparisons: int = 0
    similarity_scores: List[float] = field(default_factory=list)
    quality_threshold: float = 0.95
    
    def add_comparison(self, similarity_score: float):
        """Add quality comparison result"""
        self.comparisons += 1
        self.similarity_scores.append(similarity_score)
        
        # Keep only recent comparisons
        if len(self.similarity_scores) > 1000:
            self.similarity_scores.pop(0)
    
    @property
    def average_similarity(self) -> float:
        """Average similarity between providers"""
        return statistics.mean(self.similarity_scores) if self.similarity_scores else 0.0
    
    @property
    def quality_degradation_rate(self) -> float:
        """Rate of quality degradation (similarity < threshold)"""
        if not self.similarity_scores:
            return 0.0
        
        degraded = sum(1 for score in self.similarity_scores if score < self.quality_threshold)
        return degraded / len(self.similarity_scores)

class EmbeddingMonitor:
    """Comprehensive monitoring for embedding system"""
    
    def __init__(self):
        # Performance metrics by provider
        self.performance_metrics = {
            provider.value: PerformanceMetrics()
            for provider in EmbeddingProvider
        }
        
        # Cost tracking
        self.cost_metrics = CostMetrics()
        
        # Cache metrics
        self.cache_metrics = CacheMetrics()
        
        # Quality metrics
        self.quality_metrics = QualityMetrics()
        
        # Routing decision tracking
        self.routing_decisions = defaultdict(int)
        self.routing_success_rate = defaultdict(list)
        
        # Error tracking
        self.errors_by_provider = defaultdict(int)
        self.recent_errors = deque(maxlen=100)
        
        # Health status
        self.last_health_check = {}
        
        logger.info("Embedding monitoring system initialized")
    
    def record_embedding_result(
        self,
        result: EmbeddingResult,
        routing_decision: Optional[RoutingDecision] = None,
        cache_level: Optional[str] = None
    ):
        """Record embedding result for monitoring"""
        provider = result.provider.value
        
        # Performance metrics
        self.performance_metrics[provider].add_sample(
            result.latency_ms,
            1  # Single embedding
        )
        
        # Cost metrics
        self.cost_metrics.add_cost(
            result.provider,
            result.cost_usd or 0.0,
            result.tokens_used or 0
        )
        
        # Cache metrics
        if result.cache_hit:
            self.cache_metrics.record_hit(cache_level or "unknown")
        else:
            self.cache_metrics.record_miss()
        
        # Routing decision tracking
        if routing_decision:
            self.routing_decisions[routing_decision.reason.value] += 1
            
            # Track routing success (did we use the decided provider?)
            success = (routing_decision.provider == result.provider)
            self.routing_success_rate[routing_decision.reason.value].append(success)
            
            # Keep only recent samples
            recent_samples = self.routing_success_rate[routing_decision.reason.value]
            if len(recent_samples) > 100:
                recent_samples.pop(0)
        
        logger.debug(
            "Embedding result recorded",
            provider=provider,
            latency_ms=result.latency_ms,
            cost_usd=result.cost_usd,
            cached=result.cache_hit
        )
    
    def record_error(
        self,
        provider: EmbeddingProvider,
        error: Exception,
        context: Optional[str] = None
    ):
        """Record embedding error"""
        provider_str = provider.value
        self.errors_by_provider[provider_str] += 1
        
        error_info = {
            "timestamp": time.time(),
            "provider": provider_str,
            "error": str(error),
            "context": context
        }
        self.recent_errors.append(error_info)
        
        logger.error(
            "Embedding error recorded",
            provider=provider_str,
            error=str(error),
            context=context
        )
    
    def record_quality_comparison(
        self,
        local_result: EmbeddingResult,
        api_result: EmbeddingResult
    ):
        """Record quality comparison between providers"""
        similarity = local_result.cosine_similarity(api_result)
        self.quality_metrics.add_comparison(similarity)
        
        logger.debug(
            "Quality comparison recorded",
            similarity=similarity,
            local_provider=local_result.provider.value,
            api_provider=api_result.provider.value
        )
    
    def update_health_status(self, provider: EmbeddingProvider, health_data: Dict[str, Any]):
        """Update health status for provider"""
        self.last_health_check[provider.value] = {
            "timestamp": time.time(),
            "data": health_data
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            "timestamp": time.time(),
            "performance": {},
            "costs": {
                "total_cost_usd": round(self.cost_metrics.total_cost_usd, 6),
                "total_tokens": self.cost_metrics.total_tokens,
                "average_cost_per_request": round(self.cost_metrics.average_cost_per_request, 6),
                "cost_per_1k_tokens": round(self.cost_metrics.cost_per_1k_tokens, 6),
                "cost_by_provider": {
                    provider: round(cost, 6)
                    for provider, cost in self.cost_metrics.cost_by_provider.items()
                },
                "requests_by_provider": dict(self.cost_metrics.requests_by_provider)
            },
            "cache": {
                "hit_rate": round(self.cache_metrics.hit_rate, 3),
                "l1_hit_rate": round(self.cache_metrics.l1_hit_rate, 3),
                "l2_hit_rate": round(self.cache_metrics.l2_hit_rate, 3),
                "total_requests": self.cache_metrics.total_requests,
                "cache_hits": self.cache_metrics.cache_hits,
                "cache_misses": self.cache_metrics.cache_misses
            },
            "quality": {
                "average_similarity": round(self.quality_metrics.average_similarity, 3),
                "quality_degradation_rate": round(self.quality_metrics.quality_degradation_rate, 3),
                "comparisons": self.quality_metrics.comparisons,
                "quality_threshold": self.quality_metrics.quality_threshold
            },
            "routing": {
                "decisions": dict(self.routing_decisions),
                "success_rates": {
                    reason: round(statistics.mean(successes), 3) if successes else 0.0
                    for reason, successes in self.routing_success_rate.items()
                }
            },
            "errors": {
                "total_by_provider": dict(self.errors_by_provider),
                "recent_errors": list(self.recent_errors)[-10:]  # Last 10 errors
            },
            "health": self.last_health_check
        }
        
        # Add performance metrics for each provider
        for provider, metrics in self.performance_metrics.items():
            if metrics.total_requests > 0:
                report["performance"][provider] = {
                    "total_requests": metrics.total_requests,
                    "total_embeddings": metrics.total_embeddings,
                    "average_latency_ms": round(metrics.average_latency_ms, 2),
                    "p50_latency_ms": round(metrics.p50_latency_ms, 2),
                    "p95_latency_ms": round(metrics.p95_latency_ms, 2),
                    "p99_latency_ms": round(metrics.p99_latency_ms, 2)
                }
        
        return report
    
    def get_cost_projection(self, days: int = 30) -> Dict[str, Any]:
        """Project costs based on current usage"""
        if self.cost_metrics.total_cost_usd == 0:
            return {
                "projection_days": days,
                "projected_cost_usd": 0.0,
                "daily_average": 0.0,
                "confidence": "low"
            }
        
        # Simple linear projection based on current usage
        # In production, you'd want more sophisticated time-series analysis
        total_requests = sum(self.cost_metrics.requests_by_provider.values())
        
        if total_requests == 0:
            return {
                "projection_days": days,
                "projected_cost_usd": 0.0,
                "daily_average": 0.0,
                "confidence": "low"
            }
        
        daily_average = self.cost_metrics.total_cost_usd  # Assume current total is daily
        projected_cost = daily_average * days
        
        confidence = "high" if total_requests > 100 else "medium" if total_requests > 10 else "low"
        
        return {
            "projection_days": days,
            "projected_cost_usd": round(projected_cost, 2),
            "daily_average": round(daily_average, 4),
            "confidence": confidence,
            "based_on_requests": total_requests
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get system health summary"""
        now = time.time()
        health_summary = {
            "overall_status": "healthy",
            "providers": {},
            "issues": []
        }
        
        # Check each provider health
        for provider_str, health_info in self.last_health_check.items():
            age_seconds = now - health_info["timestamp"]
            health_data = health_info["data"]
            
            provider_health = {
                "status": health_data.get("status", "unknown"),
                "last_check_seconds_ago": round(age_seconds),
                "details": health_data
            }
            
            # Check for issues
            if health_data.get("status") != "healthy":
                health_summary["issues"].append(f"{provider_str} is {health_data.get('status')}")
                if health_summary["overall_status"] == "healthy":
                    health_summary["overall_status"] = "degraded"
            
            if age_seconds > 300:  # 5 minutes
                health_summary["issues"].append(f"{provider_str} health check is stale")
                if health_summary["overall_status"] == "healthy":
                    health_summary["overall_status"] = "degraded"
            
            health_summary["providers"][provider_str] = provider_health
        
        # Check error rates
        total_requests = sum(metrics.total_requests for metrics in self.performance_metrics.values())
        total_errors = sum(self.errors_by_provider.values())
        
        if total_requests > 0:
            error_rate = total_errors / total_requests
            if error_rate > 0.1:  # 10% error rate
                health_summary["issues"].append(f"High error rate: {error_rate:.1%}")
                health_summary["overall_status"] = "unhealthy"
        
        return health_summary
    
    def reset_metrics(self, keep_performance_samples: bool = True):
        """Reset metrics (typically called daily)"""
        if not keep_performance_samples:
            for metrics in self.performance_metrics.values():
                metrics.latency_samples.clear()
        
        # Reset cost metrics
        self.cost_metrics = CostMetrics()
        
        # Reset routing decisions
        self.routing_decisions.clear()
        
        # Keep health checks and recent errors
        logger.info("Monitoring metrics reset", keep_samples=keep_performance_samples)