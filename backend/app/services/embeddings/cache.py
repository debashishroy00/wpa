"""
Two-tier caching system for embeddings:
L1: In-memory LRU cache for hot embeddings
L2: Redis for persistent cache across service restarts
"""

import json
import hashlib
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from functools import lru_cache
import asyncio
import redis.asyncio as aioredis
import structlog
from collections import OrderedDict

from .base import EmbeddingResult, EmbeddingProvider
from app.core.config import settings

logger = structlog.get_logger(__name__)

@dataclass
class CacheKey:
    """Cache key for embeddings"""
    text_hash: str
    model: str
    provider: str
    dimension: int
    
    def __str__(self) -> str:
        return f"emb:{self.provider}:{self.model}:{self.dimension}:{self.text_hash}"
    
    @classmethod
    def from_text(
        cls, 
        text: str, 
        model: str, 
        provider: EmbeddingProvider,
        dimension: int
    ) -> 'CacheKey':
        """Create cache key from text"""
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
        return cls(
            text_hash=text_hash,
            model=model,
            provider=provider.value,
            dimension=dimension
        )

class LRUCache:
    """Thread-safe LRU cache for hot embeddings"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[EmbeddingResult]:
        """Get item from cache"""
        async with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                
                # Mark as cache hit
                value.cache_hit = True
                value.cached = True
                return value
            return None
    
    async def set(self, key: str, value: EmbeddingResult) -> None:
        """Set item in cache"""
        async with self._lock:
            if key in self.cache:
                # Update existing
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # Remove oldest
                self.cache.popitem(last=False)
            
            # Add/update
            value.cached = True
            self.cache[key] = value
    
    async def clear(self) -> None:
        """Clear all items"""
        async with self._lock:
            self.cache.clear()
    
    @property
    def size(self) -> int:
        """Current cache size"""
        return len(self.cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "utilization": len(self.cache) / self.max_size
        }

class RedisCache:
    """Redis-based persistent cache for embeddings"""
    
    def __init__(self, redis_url: str, ttl_api: int = 7 * 24 * 3600, ttl_local: int = 24 * 3600):
        self.redis_url = redis_url
        self.ttl_api = ttl_api  # 7 days for API embeddings
        self.ttl_local = ttl_local  # 24 hours for local
        self.redis: Optional[aioredis.Redis] = None
    
    async def initialize(self) -> None:
        """Initialize Redis connection"""
        try:
            self.redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False  # We handle JSON encoding
            )
            # Test connection
            await self.redis.ping()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.error("Failed to initialize Redis cache", error=str(e))
            self.redis = None
    
    async def get(self, key: str) -> Optional[EmbeddingResult]:
        """Get embedding from Redis"""
        if not self.redis:
            return None
        
        try:
            data = await self.redis.get(str(key))
            if data:
                embedding_data = json.loads(data)
                # Reconstruct EmbeddingResult
                result = EmbeddingResult(
                    embedding=embedding_data['embedding'],
                    provider=EmbeddingProvider(embedding_data['provider']),
                    model=embedding_data['model'],
                    dimension=embedding_data['dimension'],
                    latency_ms=0.0,  # Cache hit has no latency
                    tokens_used=embedding_data.get('tokens_used'),
                    cost_usd=embedding_data.get('cost_usd'),
                    cached=True,
                    cache_hit=True
                )
                return result
        except Exception as e:
            logger.error("Redis cache get error", key=key, error=str(e))
        
        return None
    
    async def set(
        self, 
        key: str, 
        value: EmbeddingResult, 
        custom_ttl: Optional[int] = None
    ) -> None:
        """Set embedding in Redis with TTL"""
        if not self.redis:
            return
        
        try:
            # Choose TTL based on provider
            if custom_ttl:
                ttl = custom_ttl
            elif value.provider == EmbeddingProvider.OPENAI:
                ttl = self.ttl_api
            else:
                ttl = self.ttl_local
            
            # Serialize embedding result
            embedding_data = {
                'embedding': value.embedding,
                'provider': value.provider.value,
                'model': value.model,
                'dimension': value.dimension,
                'tokens_used': value.tokens_used,
                'cost_usd': value.cost_usd,
                'cached_at': time.time()
            }
            
            await self.redis.setex(
                str(key), 
                ttl, 
                json.dumps(embedding_data)
            )
        except Exception as e:
            logger.error("Redis cache set error", key=key, error=str(e))
    
    async def delete(self, key: str) -> None:
        """Delete key from Redis"""
        if not self.redis:
            return
        
        try:
            await self.redis.delete(str(key))
        except Exception as e:
            logger.error("Redis cache delete error", key=key, error=str(e))
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        if not self.redis:
            return 0
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error("Redis cache clear pattern error", pattern=pattern, error=str(e))
            return 0
    
    async def stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        if not self.redis:
            return {"available": False}
        
        try:
            info = await self.redis.info()
            return {
                "available": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(1, 
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
            }
        except Exception as e:
            logger.error("Redis stats error", error=str(e))
            return {"available": False, "error": str(e)}

class EmbeddingCache:
    """Two-tier cache combining LRU + Redis"""
    
    def __init__(
        self, 
        l1_size: int = 1000,
        redis_url: Optional[str] = None,
        ttl_api: int = 7 * 24 * 3600,
        ttl_local: int = 24 * 3600
    ):
        self.l1_cache = LRUCache(max_size=l1_size)
        
        # Initialize Redis cache if URL provided
        if redis_url:
            self.l2_cache = RedisCache(redis_url, ttl_api, ttl_local)
        else:
            self.l2_cache = None
        
        # WealthPath AI specific financial terms for cache warming
        self.financial_terms = [
            # Core Financial Planning
            "retirement planning", "financial planning", "wealth management", "investment strategy",
            "asset allocation", "portfolio diversification", "risk assessment", "financial goals",
            
            # Retirement & Benefits  
            "401k contribution", "roth ira", "traditional ira", "pension planning",
            "social security benefits", "medicare planning", "retirement income", "withdrawal strategy",
            "required minimum distribution", "catch up contributions", "employer match",
            
            # Investment & Portfolio Management
            "investment portfolio", "mutual funds", "exchange traded funds", "index funds", 
            "bond investments", "stock market", "market volatility", "bear market", "bull market",
            "compound interest", "dollar cost averaging", "portfolio rebalancing", "expense ratio",
            "dividend yield", "capital gains", "tax loss harvesting", "asset location",
            
            # Tax Strategy
            "tax optimization", "tax planning", "backdoor roth", "roth conversion",
            "tax deferred accounts", "tax free growth", "capital gains tax", "ordinary income",
            "tax bracket management", "charitable giving", "donor advised fund",
            
            # Debt Management
            "debt consolidation", "mortgage refinancing", "student loan forgiveness",
            "debt to income ratio", "credit utilization", "credit score improvement",
            "debt avalanche", "debt snowball", "interest rate optimization",
            
            # Insurance & Protection
            "life insurance", "disability insurance", "long term care insurance",
            "umbrella insurance", "health insurance", "medicare supplement",
            "insurance needs analysis", "beneficiary planning",
            
            # Estate & Legacy Planning
            "estate planning", "will and testament", "trust planning", "probate avoidance",
            "power of attorney", "healthcare directive", "beneficiary designations",
            "estate tax planning", "generation skipping trust", "charitable remainder trust",
            
            # Family Financial Planning
            "529 education savings", "coverdell esa", "utma ugma accounts",
            "dependent care fsa", "family financial planning", "child tax credit",
            "education tax credits", "financial aid planning",
            
            # Business & Self-Employed
            "sep ira", "simple ira", "solo 401k", "defined benefit plan",
            "business succession planning", "key person insurance", "buy sell agreement",
            "self employment tax", "quarterly estimated taxes",
            
            # Advanced Strategies
            "tax alpha generation", "factor investing", "alternative investments",
            "real estate investment trust", "master limited partnership",
            "qualified small business stock", "section 1202 exclusion",
            
            # Market & Economic Terms
            "inflation protection", "interest rate risk", "sequence of returns risk",
            "monte carlo simulation", "safe withdrawal rate", "glide path",
            "efficient frontier", "modern portfolio theory", "behavioral finance",
            
            # Financial Health & Analysis
            "net worth calculation", "cash flow analysis", "emergency fund",
            "financial stress test", "retirement readiness", "financial independence",
            "fire movement", "coast fire", "barista fire", "lean fire", "fat fire",
            
            # Specific Financial Products
            "target date funds", "lifecycle funds", "balanced funds", "growth funds",
            "value investing", "growth investing", "dividend investing", "income investing",
            "bond ladder", "cd ladder", "treasury bills", "i bonds", "tips bonds",
            
            # Regulatory & Compliance
            "fiduciary standard", "suitability standard", "investment adviser",
            "broker dealer", "registered investment advisor", "fee only advisor",
            "securities regulation", "finra rules", "sec regulations"
        ]
    
    async def initialize(self) -> None:
        """Initialize cache components"""
        if self.l2_cache:
            await self.l2_cache.initialize()
        logger.info("Embedding cache initialized")
    
    async def get(self, key: CacheKey) -> Optional[EmbeddingResult]:
        """Get embedding from cache (L1 first, then L2)"""
        key_str = str(key)
        
        # Try L1 cache first
        result = await self.l1_cache.get(key_str)
        if result:
            logger.debug("L1 cache hit", key=key_str)
            return result
        
        # Try L2 cache (Redis)
        if self.l2_cache:
            result = await self.l2_cache.get(key_str)
            if result:
                logger.debug("L2 cache hit", key=key_str)
                # Populate L1 cache for future requests
                await self.l1_cache.set(key_str, result)
                return result
        
        logger.debug("Cache miss", key=key_str)
        return None
    
    async def set(
        self, 
        key: CacheKey, 
        value: EmbeddingResult,
        custom_ttl: Optional[int] = None
    ) -> None:
        """Set embedding in both caches"""
        key_str = str(key)
        
        # Set in L1 cache
        await self.l1_cache.set(key_str, value)
        
        # Set in L2 cache if available
        if self.l2_cache:
            await self.l2_cache.set(key_str, value, custom_ttl)
        
        logger.debug("Cached embedding", key=key_str, provider=value.provider.value)
    
    async def warm_cache(
        self, 
        embedding_service,
        provider: EmbeddingProvider = EmbeddingProvider.LOCAL
    ) -> None:
        """Warm cache with common financial terms"""
        logger.info("Starting cache warming", terms=len(self.financial_terms))
        
        try:
            # Generate embeddings for financial terms
            for term in self.financial_terms:
                key = CacheKey.from_text(
                    text=term,
                    model="all-MiniLM-L6-v2",  # Default local model
                    provider=provider,
                    dimension=384
                )
                
                # Check if already cached
                if await self.get(key):
                    continue
                
                # Generate and cache embedding
                result = await embedding_service.embed_single(term)
                await self.set(key, result)
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
            
            logger.info("Cache warming completed")
        except Exception as e:
            logger.error("Cache warming failed", error=str(e))
    
    async def clear(self, pattern: Optional[str] = None) -> None:
        """Clear cache (optionally by pattern)"""
        await self.l1_cache.clear()
        
        if self.l2_cache and pattern:
            await self.l2_cache.clear_pattern(pattern)
        
        logger.info("Cache cleared", pattern=pattern)
    
    async def stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        l1_stats = self.l1_cache.stats()
        
        stats = {
            "l1_cache": l1_stats,
            "l2_cache": None
        }
        
        if self.l2_cache:
            stats["l2_cache"] = await self.l2_cache.stats()
        
        return stats