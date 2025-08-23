"""
WealthPath AI - Simple Cache Module
Basic caching for projection results (can be extended with Redis later)
"""
import json
import time
from typing import Any, Optional
import structlog

logger = structlog.get_logger()


class SimpleCache:
    """
    Simple in-memory cache implementation
    TODO: Replace with Redis for production deployment
    """
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get cached value if not expired"""
        if key not in self._cache:
            return None
        
        # Check expiry
        if key in self._expiry and time.time() > self._expiry[key]:
            del self._cache[key]
            del self._expiry[key]
            return None
        
        return self._cache[key]
    
    async def setex(self, key: str, ttl: int, value: str):
        """Set value with TTL (time to live) in seconds"""
        self._cache[key] = value
        self._expiry[key] = time.time() + ttl
        
        logger.debug(f"Cached value for key: {key}, TTL: {ttl}s")
    
    async def delete(self, *keys: str):
        """Delete one or more keys"""
        for key in keys:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
    
    async def keys(self, pattern: str) -> list:
        """Get keys matching pattern (basic implementation)"""
        matching_keys = []
        for key in self._cache.keys():
            if pattern.replace('*', '') in key:
                matching_keys.append(key)
        return matching_keys
    
    def clear_all(self):
        """Clear all cached data"""
        self._cache.clear()
        self._expiry.clear()
        logger.info("Cache cleared")


# Initialize cache instance
redis_client = SimpleCache()

logger.info("Simple cache initialized (consider Redis for production)")