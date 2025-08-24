"""
Shadow mode implementation for zero-risk testing of hybrid embedding system.
Runs new system in parallel with legacy system, comparing results.
"""

import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timezone
import structlog

from .compatibility import get_embedding_service
from .base import EmbeddingResult, EmbeddingContext
from app.core.config import settings

logger = structlog.get_logger(__name__)

@dataclass
class ShadowComparison:
    """Comparison result between legacy and hybrid systems"""
    text: str
    text_hash: str
    timestamp: float
    
    # Legacy system results
    legacy_embedding: List[float]
    legacy_latency_ms: float
    legacy_error: Optional[str] = None
    
    # Hybrid system results
    hybrid_embedding: List[float]
    hybrid_provider: str
    hybrid_model: str
    hybrid_latency_ms: float
    hybrid_cached: bool
    hybrid_cost_usd: Optional[float] = None
    hybrid_error: Optional[str] = None
    
    # Comparison metrics
    cosine_similarity: Optional[float] = None
    dimension_match: bool = False
    latency_difference_ms: float = 0.0
    cost_impact: float = 0.0
    
    def __post_init__(self):
        """Calculate comparison metrics"""
        try:
            if self.legacy_embedding and self.hybrid_embedding:
                # Calculate cosine similarity
                legacy_vec = np.array(self.legacy_embedding, dtype=np.float32)
                hybrid_vec = np.array(self.hybrid_embedding, dtype=np.float32)
                
                # Handle dimension mismatch by padding smaller vector
                if len(legacy_vec) != len(hybrid_vec):
                    max_dim = max(len(legacy_vec), len(hybrid_vec))
                    if len(legacy_vec) < max_dim:
                        legacy_vec = np.pad(legacy_vec, (0, max_dim - len(legacy_vec)))
                    if len(hybrid_vec) < max_dim:
                        hybrid_vec = np.pad(hybrid_vec, (0, max_dim - len(hybrid_vec)))
                
                # Calculate similarity
                similarity = np.dot(legacy_vec, hybrid_vec) / (
                    np.linalg.norm(legacy_vec) * np.linalg.norm(hybrid_vec)
                )
                self.cosine_similarity = float(similarity)
                self.dimension_match = len(self.legacy_embedding) == len(self.hybrid_embedding)
            
            # Calculate performance differences
            self.latency_difference_ms = self.hybrid_latency_ms - self.legacy_latency_ms
            self.cost_impact = self.hybrid_cost_usd or 0.0
            
        except Exception as e:
            logger.error("Failed to calculate comparison metrics", error=str(e))
            self.cosine_similarity = None

class ShadowModeCollector:
    """Collects and analyzes shadow mode data"""
    
    def __init__(self):
        self.comparisons: List[ShadowComparison] = []
        self.max_comparisons = 10000  # Keep last 10k comparisons
        self.start_time = time.time()
        
        # Aggregated statistics
        self.total_comparisons = 0
        self.quality_issues = 0
        self.performance_improvements = 0
        self.cost_savings = 0.0
        
    def add_comparison(self, comparison: ShadowComparison):
        """Add a new comparison result"""
        self.comparisons.append(comparison)
        self.total_comparisons += 1
        
        # Keep only recent comparisons
        if len(self.comparisons) > self.max_comparisons:
            self.comparisons.pop(0)
        
        # Update aggregated stats
        if comparison.cosine_similarity and comparison.cosine_similarity < 0.95:
            self.quality_issues += 1
        
        if comparison.latency_difference_ms < 0:  # Hybrid is faster
            self.performance_improvements += 1
        
        if comparison.hybrid_cost_usd:
            # Assume legacy would cost same as OpenAI API
            estimated_legacy_cost = len(comparison.text.split()) * 1.3 / 1000 * 0.00002
            self.cost_savings += max(0, estimated_legacy_cost - comparison.hybrid_cost_usd)
        
        # Log significant findings
        if comparison.cosine_similarity and comparison.cosine_similarity < 0.9:
            logger.warning(
                "Low similarity in shadow mode",
                similarity=comparison.cosine_similarity,
                text_preview=comparison.text[:50],
                legacy_dim=len(comparison.legacy_embedding),
                hybrid_dim=len(comparison.hybrid_embedding),
                hybrid_provider=comparison.hybrid_provider
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive shadow mode statistics"""
        if not self.comparisons:
            return {"status": "no_data", "comparisons": 0}
        
        # Calculate similarity statistics
        similarities = [c.cosine_similarity for c in self.comparisons if c.cosine_similarity is not None]
        latency_diffs = [c.latency_difference_ms for c in self.comparisons]
        
        # Provider usage
        provider_usage = {}
        for comp in self.comparisons:
            provider_usage[comp.hybrid_provider] = provider_usage.get(comp.hybrid_provider, 0) + 1
        
        # Cache efficiency
        cached_requests = sum(1 for c in self.comparisons if c.hybrid_cached)
        cache_hit_rate = cached_requests / len(self.comparisons) if self.comparisons else 0
        
        return {
            "status": "active",
            "runtime_hours": (time.time() - self.start_time) / 3600,
            "total_comparisons": self.total_comparisons,
            "recent_comparisons": len(self.comparisons),
            
            "quality_metrics": {
                "average_similarity": np.mean(similarities) if similarities else 0,
                "min_similarity": np.min(similarities) if similarities else 0,
                "similarity_std": np.std(similarities) if similarities else 0,
                "quality_issues": self.quality_issues,
                "quality_issue_rate": self.quality_issues / max(1, self.total_comparisons)
            },
            
            "performance_metrics": {
                "average_latency_diff_ms": np.mean(latency_diffs) if latency_diffs else 0,
                "performance_improvements": self.performance_improvements,
                "improvement_rate": self.performance_improvements / max(1, self.total_comparisons),
                "cache_hit_rate": cache_hit_rate
            },
            
            "cost_metrics": {
                "total_cost_savings": round(self.cost_savings, 4),
                "average_cost_per_embedding": round(self.cost_savings / max(1, self.total_comparisons), 6),
                "projected_monthly_savings": round(self.cost_savings * 30, 2)
            },
            
            "provider_usage": provider_usage,
            "dimension_matches": sum(1 for c in self.comparisons if c.dimension_match),
            "error_count": sum(1 for c in self.comparisons if c.hybrid_error or c.legacy_error)
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get alerts based on shadow mode data"""
        alerts = []
        stats = self.get_statistics()
        
        if stats.get("total_comparisons", 0) < 10:
            return alerts  # Need more data
        
        # Quality alerts
        quality_metrics = stats.get("quality_metrics", {})
        if quality_metrics.get("average_similarity", 1.0) < 0.95:
            alerts.append({
                "level": "warning",
                "type": "quality_degradation",
                "message": f"Average similarity below 95%: {quality_metrics['average_similarity']:.3f}",
                "impact": "high"
            })
        
        if quality_metrics.get("quality_issue_rate", 0) > 0.1:
            alerts.append({
                "level": "error", 
                "type": "quality_issues",
                "message": f"High quality issue rate: {quality_metrics['quality_issue_rate']:.1%}",
                "impact": "high"
            })
        
        # Performance alerts
        performance_metrics = stats.get("performance_metrics", {})
        if performance_metrics.get("average_latency_diff_ms", 0) > 200:
            alerts.append({
                "level": "warning",
                "type": "performance_degradation", 
                "message": f"Hybrid system slower by {performance_metrics['average_latency_diff_ms']:.0f}ms on average",
                "impact": "medium"
            })
        
        if performance_metrics.get("cache_hit_rate", 0) < 0.7:
            alerts.append({
                "level": "info",
                "type": "cache_efficiency",
                "message": f"Cache hit rate below target: {performance_metrics['cache_hit_rate']:.1%}",
                "impact": "low"
            })
        
        return alerts

# Global shadow mode collector
_shadow_collector: Optional[ShadowModeCollector] = None

def get_shadow_collector() -> ShadowModeCollector:
    """Get global shadow mode collector"""
    global _shadow_collector
    if _shadow_collector is None:
        _shadow_collector = ShadowModeCollector()
    return _shadow_collector

async def run_shadow_comparison(
    text: str,
    legacy_embedding_func,
    context: EmbeddingContext = EmbeddingContext.REALTIME
) -> Optional[ShadowComparison]:
    """
    Run shadow mode comparison between legacy and hybrid systems.
    This function should be called from existing embedding code.
    """
    if not getattr(settings, 'EMBEDDING_SHADOW_MODE', False):
        return None
    
    import hashlib
    text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
    
    comparison = ShadowComparison(
        text=text,
        text_hash=text_hash,
        timestamp=time.time(),
        legacy_embedding=[],
        legacy_latency_ms=0.0,
        hybrid_embedding=[],
        hybrid_provider="unknown",
        hybrid_model="unknown", 
        hybrid_latency_ms=0.0,
        hybrid_cached=False
    )
    
    try:
        # Run legacy system
        legacy_start = time.time()
        legacy_result = await legacy_embedding_func(text)
        comparison.legacy_latency_ms = (time.time() - legacy_start) * 1000
        comparison.legacy_embedding = legacy_result if isinstance(legacy_result, list) else []
        
    except Exception as e:
        comparison.legacy_error = str(e)
        logger.error("Legacy embedding failed in shadow mode", error=str(e))
    
    try:
        # Run hybrid system
        hybrid_start = time.time()
        hybrid_service = get_embedding_service()
        hybrid_result = await hybrid_service.generate_embedding_with_metadata(
            text=text,
            context=context.value if hasattr(context, 'value') else str(context)
        )
        
        comparison.hybrid_latency_ms = (time.time() - hybrid_start) * 1000
        comparison.hybrid_embedding = hybrid_result.get("embedding", [])
        comparison.hybrid_provider = hybrid_result.get("provider", "unknown")
        comparison.hybrid_model = hybrid_result.get("model", "unknown")
        comparison.hybrid_cached = hybrid_result.get("cached", False)
        comparison.hybrid_cost_usd = hybrid_result.get("cost_usd")
        
    except Exception as e:
        comparison.hybrid_error = str(e)
        logger.error("Hybrid embedding failed in shadow mode", error=str(e))
    
    # Add to collector
    collector = get_shadow_collector()
    collector.add_comparison(comparison)
    
    # Log summary periodically
    if collector.total_comparisons % 100 == 0:
        stats = collector.get_statistics()
        logger.info(
            "Shadow mode checkpoint",
            comparisons=collector.total_comparisons,
            avg_similarity=stats["quality_metrics"]["average_similarity"],
            cache_hit_rate=stats["performance_metrics"]["cache_hit_rate"],
            cost_savings=stats["cost_metrics"]["total_cost_savings"]
        )
    
    return comparison

# Decorator for easy integration with existing functions
def shadow_mode_wrapper(legacy_func):
    """Decorator to add shadow mode testing to existing embedding functions"""
    async def wrapper(text: str, *args, **kwargs):
        # Always run legacy function
        result = await legacy_func(text, *args, **kwargs)
        
        # Run shadow comparison in background if enabled
        if getattr(settings, 'EMBEDDING_SHADOW_MODE', False):
            asyncio.create_task(
                run_shadow_comparison(
                    text=text,
                    legacy_embedding_func=lambda t: legacy_func(t, *args, **kwargs),
                    context=EmbeddingContext.REALTIME
                )
            )
        
        return result
    
    return wrapper