"""
Main hybrid embedding service that orchestrates all components.
Provides unified interface while maintaining backward compatibility.
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
import structlog

from .base import (
    EmbeddingProvider,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingContext,
    EmbeddingMetrics
)
from .cache import EmbeddingCache, CacheKey
from .router import EmbeddingRouter, RoutingConfig
from .local_provider import LocalEmbeddingProvider
from .openai_provider import OpenAIEmbeddingProvider
from .monitoring import EmbeddingMonitor
from app.core.config import settings

logger = structlog.get_logger(__name__)

class FeatureFlags:
    """Feature flags for hybrid embedding system"""
    
    def __init__(self):
        # Main feature flag - controls entire hybrid system
        self.USE_HYBRID_EMBEDDINGS = getattr(settings, 'USE_HYBRID_EMBEDDINGS', False)
        
        # Component feature flags
        self.ENABLE_CACHING = getattr(settings, 'EMBEDDING_ENABLE_CACHING', True)
        self.ENABLE_ROUTING = getattr(settings, 'EMBEDDING_ENABLE_ROUTING', True)
        self.ENABLE_MONITORING = getattr(settings, 'EMBEDDING_ENABLE_MONITORING', True)
        self.ENABLE_SHADOW_MODE = getattr(settings, 'EMBEDDING_SHADOW_MODE', False)
        
        # Provider flags
        self.ENABLE_OPENAI = getattr(settings, 'EMBEDDING_ENABLE_OPENAI', True)
        self.ENABLE_LOCAL = getattr(settings, 'EMBEDDING_ENABLE_LOCAL', True)
        
        # Quality comparison
        self.ENABLE_QUALITY_COMPARISON = getattr(settings, 'EMBEDDING_QUALITY_COMPARISON', False)
        
        logger.info("Feature flags initialized", flags=self.to_dict())
    
    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary for logging"""
        return {
            attr: getattr(self, attr)
            for attr in dir(self)
            if not attr.startswith('_') and attr.isupper()
        }

class HybridEmbeddingService:
    """Main hybrid embedding service with intelligent routing and caching"""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        redis_url: Optional[str] = None,
        routing_config: Optional[RoutingConfig] = None
    ):
        # Feature flags
        self.feature_flags = FeatureFlags()
        
        # Core components (always initialize for backward compatibility)
        self.cache: Optional[EmbeddingCache] = None
        self.router: Optional[EmbeddingRouter] = None
        self.monitor: Optional[EmbeddingMonitor] = None
        
        # Providers
        self.local_provider: Optional[LocalEmbeddingProvider] = None
        self.openai_provider: Optional[OpenAIEmbeddingProvider] = None
        
        # Legacy metrics (for backward compatibility)
        self.legacy_metrics = EmbeddingMetrics()
        
        # Configuration
        self.openai_api_key = openai_api_key or getattr(settings, 'OPENAI_API_KEY', None)
        self.redis_url = redis_url or getattr(settings, 'REDIS_URL', None)
        self.routing_config = routing_config or RoutingConfig()
        
        # Initialization state
        self._initialized = False
        self._initializing = False
        self._init_lock = asyncio.Lock()
        
        logger.info(
            "Hybrid embedding service created",
            hybrid_enabled=self.feature_flags.USE_HYBRID_EMBEDDINGS,
            openai_available=bool(self.openai_api_key),
            redis_available=bool(self.redis_url)
        )
    
    async def initialize(self) -> None:
        """Initialize all components based on feature flags"""
        if self._initialized or self._initializing:
            return
        
        async with self._init_lock:
            if self._initialized:
                return
            
            self._initializing = True
            
            try:
                # Always initialize basic components for backward compatibility
                await self._initialize_core_components()
                
                # Initialize hybrid system if enabled
                if self.feature_flags.USE_HYBRID_EMBEDDINGS:
                    await self._initialize_hybrid_system()
                
                self._initialized = True
                logger.info("Hybrid embedding service fully initialized")
                
            except Exception as e:
                logger.error("Failed to initialize hybrid embedding service", error=str(e))
                # Fall back to basic functionality
                self._initialized = True
                raise
            finally:
                self._initializing = False
    
    async def _initialize_core_components(self) -> None:
        """Initialize core components (always needed)"""
        # Local provider (for backward compatibility and fallback)
        if self.feature_flags.ENABLE_LOCAL:
            self.local_provider = LocalEmbeddingProvider()
            await self.local_provider.initialize()
            logger.info("Local embedding provider initialized")
    
    async def _initialize_hybrid_system(self) -> None:
        """Initialize full hybrid system components"""
        # OpenAI provider
        if self.feature_flags.ENABLE_OPENAI and self.openai_api_key:
            self.openai_provider = OpenAIEmbeddingProvider(self.openai_api_key)
            await self.openai_provider.initialize()
            logger.info("OpenAI embedding provider initialized")
        
        # Cache system
        if self.feature_flags.ENABLE_CACHING:
            self.cache = EmbeddingCache(
                l1_size=1000,
                redis_url=self.redis_url if self.feature_flags.ENABLE_CACHING else None
            )
            await self.cache.initialize()
            logger.info("Embedding cache initialized")
        
        # Router
        if self.feature_flags.ENABLE_ROUTING:
            self.router = EmbeddingRouter(self.routing_config)
            logger.info("Embedding router initialized")
        
        # Monitor
        if self.feature_flags.ENABLE_MONITORING:
            self.monitor = EmbeddingMonitor()
            logger.info("Embedding monitor initialized")
        
        # Warm cache if enabled
        if self.cache and self.local_provider:
            await self.cache.warm_cache(self)
    
    async def generate_embeddings(
        self,
        texts: Union[str, List[str]],
        context: EmbeddingContext = EmbeddingContext.REALTIME,
        preferred_provider: Optional[EmbeddingProvider] = None,
        force_fresh: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[EmbeddingResult]:
        """Main embedding generation method with hybrid intelligence"""
        if not self._initialized:
            await self.initialize()
        
        # Convert single text to list
        if isinstance(texts, str):
            texts = [texts]
        
        # Create request object
        request = EmbeddingRequest(
            texts=texts,
            context=context,
            preferred_provider=preferred_provider,
            force_fresh=force_fresh,
            metadata=metadata
        )
        
        # Use hybrid system if enabled, otherwise fallback to simple mode
        if self.feature_flags.USE_HYBRID_EMBEDDINGS:
            return await self._generate_hybrid_embeddings(request)
        else:
            return await self._generate_simple_embeddings(request)
    
    async def _generate_hybrid_embeddings(self, request: EmbeddingRequest) -> List[EmbeddingResult]:
        """Generate embeddings using full hybrid system"""
        results = []
        
        for text in request.texts:
            result = await self._generate_single_hybrid_embedding(text, request)
            results.append(result)
        
        return results
    
    async def _generate_single_hybrid_embedding(
        self,
        text: str,
        request: EmbeddingRequest
    ) -> EmbeddingResult:
        """Generate single embedding using hybrid system"""
        
        # Step 1: Check cache (if enabled and not forcing fresh)
        if self.cache and not request.force_fresh:
            cache_key = CacheKey.from_text(
                text=text,
                model="default",  # Will be determined by router
                provider=request.preferred_provider or EmbeddingProvider.LOCAL,
                dimension=384  # Default dimension
            )
            
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                if self.monitor:
                    self.monitor.record_embedding_result(cached_result, cache_level="hybrid")
                return cached_result
        
        # Step 2: Route request (if enabled)
        routing_decision = None
        if self.router and not request.preferred_provider:
            # Get provider health
            local_health = await self._get_provider_health(EmbeddingProvider.LOCAL)
            openai_health = await self._get_provider_health(EmbeddingProvider.OPENAI)
            
            routing_decision = self.router.route_request(request, openai_health, local_health)
            chosen_provider = routing_decision.provider
        else:
            # Use preferred provider or default to local
            chosen_provider = request.preferred_provider or EmbeddingProvider.LOCAL
        
        # Step 3: Generate embedding
        try:
            result = await self._generate_with_provider(text, chosen_provider)
            
            # Step 4: Cache result (if enabled)
            if self.cache and result:
                cache_key = CacheKey.from_text(
                    text=text,
                    model=result.model,
                    provider=result.provider,
                    dimension=result.dimension
                )
                await self.cache.set(cache_key, result)
            
            # Step 5: Record metrics (if enabled)
            if self.monitor:
                self.monitor.record_embedding_result(result, routing_decision)
            
            if self.router:
                self.router.record_request_result(result)
            
            # Step 6: Quality comparison (if enabled)
            if (self.feature_flags.ENABLE_QUALITY_COMPARISON and 
                self.monitor and
                chosen_provider == EmbeddingProvider.LOCAL and
                self.openai_provider):
                
                asyncio.create_task(self._compare_quality(text, result))
            
            return result
            
        except Exception as e:
            # Record error
            if self.monitor:
                self.monitor.record_error(chosen_provider, e)
            if self.router:
                self.router.record_request_error(chosen_provider, e)
            
            # Try fallback provider if available
            if routing_decision and routing_decision.fallback_provider:
                try:
                    fallback_result = await self._generate_with_provider(
                        text, 
                        routing_decision.fallback_provider
                    )
                    logger.warning(
                        "Used fallback provider", 
                        primary=chosen_provider.value,
                        fallback=routing_decision.fallback_provider.value,
                        error=str(e)
                    )
                    return fallback_result
                except Exception as fallback_error:
                    logger.error("Fallback provider also failed", error=str(fallback_error))
            
            raise
    
    async def _generate_simple_embeddings(self, request: EmbeddingRequest) -> List[EmbeddingResult]:
        """Generate embeddings using simple mode (backward compatibility)"""
        if not self.local_provider:
            raise RuntimeError("Local provider not available")
        
        results = await self.local_provider.generate_embeddings(request.texts)
        
        # Update legacy metrics
        for result in results:
            self.legacy_metrics.record_request(result)
        
        return results
    
    async def _generate_with_provider(self, text: str, provider: EmbeddingProvider) -> EmbeddingResult:
        """Generate embedding with specific provider"""
        if provider == EmbeddingProvider.LOCAL:
            if not self.local_provider:
                raise RuntimeError("Local provider not available")
            return await self.local_provider.embed_single(text)
        
        elif provider == EmbeddingProvider.OPENAI:
            if not self.openai_provider:
                raise RuntimeError("OpenAI provider not available")
            return await self.openai_provider.embed_single(text)
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _get_provider_health(self, provider: EmbeddingProvider) -> Dict[str, Any]:
        """Get health status for provider"""
        try:
            if provider == EmbeddingProvider.LOCAL and self.local_provider:
                health = await self.local_provider.health_check()
            elif provider == EmbeddingProvider.OPENAI and self.openai_provider:
                health = await self.openai_provider.health_check()
            else:
                health = {"status": "unavailable"}
            
            if self.monitor:
                self.monitor.update_health_status(provider, health)
            
            return health
            
        except Exception as e:
            error_health = {"status": "unhealthy", "error": str(e)}
            if self.monitor:
                self.monitor.update_health_status(provider, error_health)
            return error_health
    
    async def _compare_quality(self, text: str, local_result: EmbeddingResult) -> None:
        """Compare local and API quality in background"""
        try:
            if not self.openai_provider:
                return
            
            api_result = await self.openai_provider.embed_single(text)
            
            if self.monitor:
                self.monitor.record_quality_comparison(local_result, api_result)
                
        except Exception as e:
            logger.debug("Quality comparison failed", error=str(e))
    
    # Backward compatibility methods
    
    async def embed_single(self, text: str, **kwargs) -> EmbeddingResult:
        """Backward compatible single text embedding"""
        results = await self.generate_embeddings([text], **kwargs)
        return results[0]
    
    async def embed_batch(self, texts: List[str], **kwargs) -> List[EmbeddingResult]:
        """Backward compatible batch embedding"""
        return await self.generate_embeddings(texts, context=EmbeddingContext.BATCH, **kwargs)
    
    # Health and status methods
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        health = {
            "status": "healthy",
            "hybrid_enabled": self.feature_flags.USE_HYBRID_EMBEDDINGS,
            "feature_flags": self.feature_flags.to_dict(),
            "providers": {},
            "components": {}
        }
        
        # Check providers
        if self.local_provider:
            health["providers"]["local"] = await self.local_provider.health_check()
        
        if self.openai_provider:
            health["providers"]["openai"] = await self.openai_provider.health_check()
        
        # Check components
        if self.cache:
            cache_stats = await self.cache.stats()
            health["components"]["cache"] = {"status": "healthy", "stats": cache_stats}
        
        if self.router:
            routing_stats = self.router.get_routing_stats()
            health["components"]["router"] = {"status": "healthy", "stats": routing_stats}
        
        if self.monitor:
            monitor_health = self.monitor.get_health_summary()
            health["components"]["monitor"] = monitor_health
        
        # Determine overall status
        provider_statuses = [p.get("status") for p in health["providers"].values()]
        if any(status == "unhealthy" for status in provider_statuses):
            health["status"] = "degraded"
        
        return health
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics"""
        metrics = {
            "hybrid_enabled": self.feature_flags.USE_HYBRID_EMBEDDINGS,
            "legacy_metrics": {
                "total_requests": self.legacy_metrics.total_requests,
                "cache_hit_rate": self.legacy_metrics.cache_hit_rate,
                "average_latency": self.legacy_metrics.average_latency
            }
        }
        
        if self.monitor:
            metrics["detailed"] = self.monitor.get_performance_report()
            metrics["cost_projection"] = self.monitor.get_cost_projection()
        
        return metrics
    
    async def reset_daily_metrics(self) -> None:
        """Reset daily metrics (call this daily)"""
        if self.router:
            self.router.reset_daily_stats()
        
        if self.monitor:
            self.monitor.reset_metrics(keep_performance_samples=True)
        
        logger.info("Daily metrics reset completed")