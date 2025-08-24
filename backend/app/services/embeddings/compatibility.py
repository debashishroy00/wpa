"""
Backward compatibility adapter for existing embedding functionality.
Ensures zero-disruption migration while providing enhanced capabilities.
"""

from typing import List, Dict, Any, Optional, Union
import asyncio
import structlog

from .hybrid_service import HybridEmbeddingService
from .base import EmbeddingContext, EmbeddingProvider
from app.core.config import settings

logger = structlog.get_logger(__name__)

class EmbeddingCompatibilityAdapter:
    """
    Adapter that makes the hybrid embedding system compatible with existing interfaces.
    Provides the same API surface while adding enhanced capabilities behind the scenes.
    """
    
    def __init__(self):
        self._hybrid_service: Optional[HybridEmbeddingService] = None
        self._initialized = False
        
        # Feature flag check
        self._use_hybrid = getattr(settings, 'USE_HYBRID_EMBEDDINGS', False)
        
        logger.info(
            "Embedding compatibility adapter initialized",
            hybrid_enabled=self._use_hybrid
        )
    
    async def _get_service(self) -> HybridEmbeddingService:
        """Lazy initialization of hybrid service"""
        if not self._hybrid_service:
            self._hybrid_service = HybridEmbeddingService()
            await self._hybrid_service.initialize()
        return self._hybrid_service
    
    # Original vector_db_service.py compatible methods
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for single text (original interface).
        Returns raw embedding vector for backward compatibility.
        """
        service = await self._get_service()
        
        # Trigger shadow mode comparison if enabled
        if getattr(settings, 'EMBEDDING_SHADOW_MODE', False) and self._use_hybrid:
            from .shadow_mode import run_shadow_comparison
            from .base import EmbeddingContext
            
            # Run shadow comparison in background
            asyncio.create_task(
                run_shadow_comparison(
                    text=text,
                    legacy_embedding_func=self._generate_legacy_embedding,
                    context=EmbeddingContext.REALTIME
                )
            )
        
        result = await service.embed_single(text)
        return result.embedding
    
    async def _generate_legacy_embedding(self, text: str) -> List[float]:
        """Generate embedding using the current system (for shadow comparison)"""
        service = await self._get_service()
        result = await service.embed_single(text)
        return result.embedding
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (original interface).
        Returns list of raw embedding vectors for backward compatibility.
        """
        service = await self._get_service()
        results = await service.generate_embeddings(texts, context=EmbeddingContext.BATCH)
        return [result.embedding for result in results]
    
    async def search_similar_embeddings(
        self,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings (original interface).
        Note: This would typically interact with a vector database.
        For now, returns empty list to maintain compatibility.
        """
        # TODO: Implement when vector database integration is needed
        logger.debug("Similar embedding search called", limit=limit)
        return []
    
    # Enhanced methods (optional, for gradual migration)
    
    async def generate_embedding_with_metadata(
        self,
        text: str,
        context: str = "realtime",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Enhanced embedding generation with metadata.
        Returns full result including metrics and provider info.
        """
        service = await self._get_service()
        
        # Map string context to enum
        context_map = {
            "realtime": EmbeddingContext.REALTIME,
            "batch": EmbeddingContext.BATCH,
            "analysis": EmbeddingContext.ANALYSIS,
            "search": EmbeddingContext.SEARCH,
            "sensitive": EmbeddingContext.SENSITIVE
        }
        
        embedding_context = context_map.get(context.lower(), EmbeddingContext.REALTIME)
        
        result = await service.embed_single(text, context=embedding_context, **kwargs)
        
        return {
            "embedding": result.embedding,
            "dimension": result.dimension,
            "provider": result.provider.value,
            "model": result.model,
            "latency_ms": result.latency_ms,
            "cached": result.cached,
            "cost_usd": result.cost_usd,
            "tokens_used": result.tokens_used
        }
    
    async def batch_generate_embeddings_with_metadata(
        self,
        texts: List[str],
        context: str = "batch",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Enhanced batch embedding generation with metadata.
        """
        service = await self._get_service()
        
        context_map = {
            "realtime": EmbeddingContext.REALTIME,
            "batch": EmbeddingContext.BATCH,
            "analysis": EmbeddingContext.ANALYSIS,
            "search": EmbeddingContext.SEARCH,
            "sensitive": EmbeddingContext.SENSITIVE
        }
        
        embedding_context = context_map.get(context.lower(), EmbeddingContext.BATCH)
        
        results = await service.generate_embeddings(texts, context=embedding_context, **kwargs)
        
        return [
            {
                "embedding": result.embedding,
                "dimension": result.dimension,
                "provider": result.provider.value,
                "model": result.model,
                "latency_ms": result.latency_ms,
                "cached": result.cached,
                "cost_usd": result.cost_usd,
                "tokens_used": result.tokens_used
            }
            for result in results
        ]
    
    # Service management methods
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            service = await self._get_service()
            return await service.health_check()
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "hybrid_enabled": self._use_hybrid
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        try:
            service = await self._get_service()
            return await service.get_metrics()
        except Exception as e:
            return {
                "error": str(e),
                "hybrid_enabled": self._use_hybrid
            }
    
    async def clear_cache(self) -> Dict[str, str]:
        """Clear embedding cache"""
        try:
            service = await self._get_service()
            if service.cache:
                await service.cache.clear()
                return {"status": "cache_cleared"}
            else:
                return {"status": "no_cache_available"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Global instance for backward compatibility
_embedding_adapter: Optional[EmbeddingCompatibilityAdapter] = None

def get_embedding_service() -> EmbeddingCompatibilityAdapter:
    """
    Get the global embedding service instance.
    Maintains singleton pattern for backward compatibility.
    """
    global _embedding_adapter
    if _embedding_adapter is None:
        _embedding_adapter = EmbeddingCompatibilityAdapter()
    return _embedding_adapter

# Legacy function aliases for existing code
async def generate_embedding(text: str) -> List[float]:
    """Legacy function for backward compatibility"""
    service = get_embedding_service()
    return await service.generate_embedding(text)

async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Legacy function for backward compatibility"""
    service = get_embedding_service()
    return await service.generate_embeddings(texts)

# Migration helper
class MigrationHelper:
    """Helper class for migrating existing code to the hybrid system"""
    
    @staticmethod
    def wrap_existing_function(original_func):
        """
        Decorator to wrap existing embedding functions.
        Provides shadow mode testing and gradual migration.
        """
        async def wrapper(*args, **kwargs):
            # Always call original function first
            original_result = await original_func(*args, **kwargs)
            
            # If shadow mode enabled, also call hybrid system for comparison
            if getattr(settings, 'EMBEDDING_SHADOW_MODE', False):
                try:
                    adapter = get_embedding_service()
                    # Call hybrid system but don't use result yet
                    if len(args) > 0 and isinstance(args[0], str):
                        # Single text
                        hybrid_result = await adapter.generate_embedding(args[0])
                        logger.info(
                            "Shadow mode comparison",
                            original_dimension=len(original_result) if isinstance(original_result, list) else "unknown",
                            hybrid_dimension=len(hybrid_result),
                            match=original_result == hybrid_result
                        )
                    elif len(args) > 0 and isinstance(args[0], list):
                        # Multiple texts
                        hybrid_result = await adapter.generate_embeddings(args[0])
                        logger.info(
                            "Shadow mode batch comparison",
                            original_count=len(original_result) if isinstance(original_result, list) else "unknown",
                            hybrid_count=len(hybrid_result),
                            match=original_result == hybrid_result
                        )
                except Exception as e:
                    logger.warning("Shadow mode comparison failed", error=str(e))
            
            return original_result
        
        return wrapper
    
    @staticmethod
    def migration_status() -> Dict[str, Any]:
        """Get migration status and recommendations"""
        return {
            "hybrid_available": True,
            "feature_flag": getattr(settings, 'USE_HYBRID_EMBEDDINGS', False),
            "shadow_mode": getattr(settings, 'EMBEDDING_SHADOW_MODE', False),
            "recommendations": [
                "1. Enable EMBEDDING_SHADOW_MODE=true to test hybrid system",
                "2. Monitor logs for compatibility issues",
                "3. Enable USE_HYBRID_EMBEDDINGS=true when ready",
                "4. Gradually migrate to enhanced API methods"
            ]
        }