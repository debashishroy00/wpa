"""
Abstract base classes for embedding providers.
Defines the contract all embedding implementations must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import hashlib
import time
import numpy as np

class EmbeddingProvider(str, Enum):
    """Supported embedding providers"""
    OPENAI = "openai"
    LOCAL = "local"
    FALLBACK = "fallback"

class EmbeddingDimension(int, Enum):
    """Standard embedding dimensions"""
    OPENAI_SMALL = 1536  # text-embedding-3-small
    OPENAI_LARGE = 3072  # text-embedding-3-large
    MINILM_L6_V2 = 384   # all-MiniLM-L6-v2

@dataclass
class EmbeddingResult:
    """Result from embedding generation"""
    embedding: List[float]
    provider: EmbeddingProvider
    model: str
    dimension: int
    latency_ms: float
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    cached: bool = False
    cache_hit: bool = False
    
    def to_numpy(self) -> np.ndarray:
        """Convert embedding to numpy array"""
        return np.array(self.embedding, dtype=np.float32)
    
    def cosine_similarity(self, other: 'EmbeddingResult') -> float:
        """Calculate cosine similarity with another embedding"""
        if self.dimension != other.dimension:
            raise ValueError(f"Dimension mismatch: {self.dimension} vs {other.dimension}")
        
        a = self.to_numpy()
        b = other.to_numpy()
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

@dataclass
class EmbeddingConfig:
    """Configuration for embedding providers"""
    provider: EmbeddingProvider
    model: str
    dimension: int
    max_tokens: int
    cost_per_1k_tokens: float
    supports_batch: bool = True
    max_batch_size: int = 100
    rate_limit_rpm: int = 1000
    timeout_seconds: int = 30

class EmbeddingContext(str, Enum):
    """Context for embedding requests - affects routing decisions"""
    REALTIME = "realtime"      # User-facing, needs low latency
    BATCH = "batch"            # Bulk processing, cost-sensitive  
    ANALYSIS = "analysis"      # High quality needed
    SEARCH = "search"          # Similarity search
    SENSITIVE = "sensitive"    # Contains PII, must stay local

@dataclass
class EmbeddingRequest:
    """Request for embedding generation"""
    texts: Union[str, List[str]]
    context: EmbeddingContext = EmbeddingContext.REALTIME
    preferred_provider: Optional[EmbeddingProvider] = None
    force_fresh: bool = False  # Skip cache
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if isinstance(self.texts, str):
            self.texts = [self.texts]
    
    @property
    def is_batch(self) -> bool:
        return len(self.texts) > 1
    
    @property
    def is_large_batch(self) -> bool:
        return len(self.texts) > 100
    
    def get_text_hash(self, text: str) -> str:
        """Generate hash for caching"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

class BaseEmbeddingProvider(ABC):
    """Abstract base class for all embedding providers"""
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._initialized = False
        self._model_loaded = False
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging/metrics"""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (load models, setup clients, etc.)"""
        pass
    
    @abstractmethod
    async def generate_embeddings(
        self, 
        texts: List[str],
        **kwargs
    ) -> List[EmbeddingResult]:
        """Generate embeddings for list of texts"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health and availability"""
        pass
    
    async def embed_single(self, text: str, **kwargs) -> EmbeddingResult:
        """Convenience method for single text embedding"""
        results = await self.generate_embeddings([text], **kwargs)
        return results[0]
    
    def estimate_cost(self, texts: List[str]) -> float:
        """Estimate cost for embedding texts"""
        total_tokens = sum(len(text.split()) for text in texts)
        return (total_tokens / 1000) * self.config.cost_per_1k_tokens
    
    def supports_batch_size(self, size: int) -> bool:
        """Check if provider can handle batch size"""
        return size <= self.config.max_batch_size

class EmbeddingMetrics:
    """Metrics collection for embedding operations"""
    
    def __init__(self):
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        self.provider_usage = {}
        self.latency_history = []
    
    def record_request(self, result: EmbeddingResult):
        """Record metrics for an embedding result"""
        self.total_requests += 1
        if result.tokens_used:
            self.total_tokens += result.tokens_used
        if result.cost_usd:
            self.total_cost += result.cost_usd
        
        if result.cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        provider = result.provider.value
        self.provider_usage[provider] = self.provider_usage.get(provider, 0) + 1
        self.latency_history.append(result.latency_ms)
        
        # Keep only last 1000 latency measurements
        if len(self.latency_history) > 1000:
            self.latency_history.pop(0)
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0
    
    @property
    def average_latency(self) -> float:
        """Calculate average latency"""
        return sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0.0
    
    def get_percentile_latency(self, percentile: int) -> float:
        """Get percentile latency (50, 95, 99)"""
        if not self.latency_history:
            return 0.0
        sorted_latencies = sorted(self.latency_history)
        index = int(len(sorted_latencies) * percentile / 100) - 1
        return sorted_latencies[max(0, index)]