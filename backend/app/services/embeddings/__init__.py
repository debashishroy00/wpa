"""
WealthPath AI - Hybrid Embedding System
Production-grade embedding architecture with intelligent routing and caching.
"""

from .base import EmbeddingProvider, EmbeddingResult, EmbeddingConfig
from .cache import EmbeddingCache, CacheKey
from .router import EmbeddingRouter
from .local_provider import LocalEmbeddingProvider
from .openai_provider import OpenAIEmbeddingProvider
from .hybrid_service import HybridEmbeddingService

__all__ = [
    'EmbeddingProvider',
    'EmbeddingResult', 
    'EmbeddingConfig',
    'EmbeddingCache',
    'CacheKey',
    'EmbeddingRouter',
    'LocalEmbeddingProvider',
    'OpenAIEmbeddingProvider', 
    'HybridEmbeddingService'
]