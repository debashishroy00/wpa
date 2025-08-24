"""
WealthPath AI - Simple Embedding System
Minimal embedding architecture for simple vector store.
"""

from .base import EmbeddingProvider, EmbeddingResult, EmbeddingConfig
from .cache import EmbeddingCache, CacheKey
from .router import EmbeddingRouter
from .openai_provider import OpenAIEmbeddingProvider

# DEAD_CODE_REMOVED: Local and hybrid providers deleted
# from .local_provider import LocalEmbeddingProvider  # DELETED
# from .hybrid_service import HybridEmbeddingService  # DELETED

__all__ = [
    'EmbeddingProvider',
    'EmbeddingResult', 
    'EmbeddingConfig',
    'EmbeddingCache',
    'CacheKey',
    'EmbeddingRouter',
    'OpenAIEmbeddingProvider'
]