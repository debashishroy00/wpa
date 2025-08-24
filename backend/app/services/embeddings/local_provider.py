"""
Local embedding provider using sentence-transformers.
Implements lazy loading and efficient batch processing.
"""

import time
import asyncio
from typing import List, Dict, Any, Optional
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
import structlog

from .base import (
    BaseEmbeddingProvider, 
    EmbeddingResult, 
    EmbeddingProvider, 
    EmbeddingConfig,
    EmbeddingDimension
)

logger = structlog.get_logger(__name__)

class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """Local embedding provider using sentence-transformers"""
    
    # Model registry with metadata
    MODEL_REGISTRY = {
        "all-MiniLM-L6-v2": {
            "dimension": 384,
            "max_tokens": 512,
            "cost_per_1k_tokens": 0.0,  # Free for local
            "description": "Balanced performance and size",
            "speed": "fast",
            "quality": "good"
        },
        "all-mpnet-base-v2": {
            "dimension": 768,
            "max_tokens": 514,  
            "cost_per_1k_tokens": 0.0,
            "description": "Higher quality embeddings",
            "speed": "medium", 
            "quality": "excellent"
        },
        "paraphrase-multilingual-MiniLM-L12-v2": {
            "dimension": 384,
            "max_tokens": 512,
            "cost_per_1k_tokens": 0.0,
            "description": "Multilingual support",
            "speed": "fast",
            "quality": "good"
        }
    }
    
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        batch_size: int = 32
    ):
        # Validate model
        if model_name not in self.MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(self.MODEL_REGISTRY.keys())}")
        
        model_info = self.MODEL_REGISTRY[model_name]
        
        config = EmbeddingConfig(
            provider=EmbeddingProvider.LOCAL,
            model=model_name,
            dimension=model_info["dimension"],
            max_tokens=model_info["max_tokens"],
            cost_per_1k_tokens=model_info["cost_per_1k_tokens"],
            supports_batch=True,
            max_batch_size=batch_size,
            rate_limit_rpm=0,  # No rate limit for local
            timeout_seconds=120  # Longer timeout for model loading
        )
        
        super().__init__(config)
        
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = batch_size
        self.model: Optional[SentenceTransformer] = None
        self._loading_lock = asyncio.Lock()
        
        logger.info(
            "Local embedding provider initialized",
            model=model_name,
            device=self.device,
            dimension=config.dimension
        )
    
    @property
    def name(self) -> str:
        return f"local_{self.model_name}"
    
    async def initialize(self) -> None:
        """Initialize without loading the model (lazy loading)"""
        self._initialized = True
        logger.info("Local embedding provider ready (model will load on first use)")
    
    async def _load_model(self) -> None:
        """Lazy load the sentence transformer model"""
        if self.model is not None:
            return
        
        async with self._loading_lock:
            # Double check after acquiring lock
            if self.model is not None:
                return
            
            logger.info("Loading sentence transformer model", model=self.model_name)
            start_time = time.time()
            
            try:
                # Load model in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                self.model = await loop.run_in_executor(
                    None,
                    self._load_model_sync
                )
                
                load_time = time.time() - start_time
                self._model_loaded = True
                
                logger.info(
                    "Model loaded successfully",
                    model=self.model_name,
                    device=self.device,
                    load_time_seconds=round(load_time, 2)
                )
                
            except Exception as e:
                logger.error("Failed to load model", model=self.model_name, error=str(e))
                raise
    
    def _load_model_sync(self) -> SentenceTransformer:
        """Synchronous model loading (runs in thread pool)"""
        model = SentenceTransformer(self.model_name, device=self.device)
        
        # Warm up the model with a test sentence
        model.encode("test sentence", convert_to_numpy=True)
        
        return model
    
    async def generate_embeddings(
        self, 
        texts: List[str], 
        **kwargs
    ) -> List[EmbeddingResult]:
        """Generate embeddings for list of texts"""
        if not self._initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        # Load model if not already loaded
        await self._load_model()
        
        start_time = time.time()
        
        try:
            # Run embedding generation in thread pool
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self._encode_texts,
                texts
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Create results
            results = []
            for i, embedding in enumerate(embeddings):
                result = EmbeddingResult(
                    embedding=embedding.tolist(),
                    provider=EmbeddingProvider.LOCAL,
                    model=self.model_name,
                    dimension=len(embedding),
                    latency_ms=latency_ms / len(texts),  # Average per text
                    tokens_used=self._estimate_tokens(texts[i]),
                    cost_usd=0.0,  # Local is free
                    cached=False,
                    cache_hit=False
                )
                results.append(result)
            
            logger.debug(
                "Generated embeddings",
                count=len(texts),
                latency_ms=round(latency_ms, 2),
                avg_latency_per_text=round(latency_ms / len(texts), 2)
            )
            
            return results
            
        except Exception as e:
            logger.error("Embedding generation failed", error=str(e), text_count=len(texts))
            raise
    
    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        """Synchronous text encoding (runs in thread pool)"""
        return self.model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True  # Normalize for better similarity search
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (words * 1.3)"""
        return int(len(text.split()) * 1.3)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health"""
        try:
            if self.model is None:
                # Quick check without loading model
                return {
                    "status": "healthy",
                    "model_loaded": False,
                    "device": self.device,
                    "cuda_available": torch.cuda.is_available(),
                    "model": self.model_name
                }
            
            # Test embedding generation
            start_time = time.time()
            await self.embed_single("health check")
            latency = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "model_loaded": True,
                "device": self.device,
                "cuda_available": torch.cuda.is_available(),
                "model": self.model_name,
                "test_latency_ms": round(latency, 2),
                "dimension": self.config.dimension
            }
            
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e),
                "model": self.model_name
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information"""
        if self.model_name not in self.MODEL_REGISTRY:
            return {}
        
        info = self.MODEL_REGISTRY[self.model_name].copy()
        info.update({
            "model_name": self.model_name,
            "provider": "local",
            "device": self.device,
            "loaded": self._model_loaded,
            "batch_size": self.batch_size
        })
        
        return info
    
    async def benchmark(self, test_texts: Optional[List[str]] = None) -> Dict[str, Any]:
        """Benchmark the model performance"""
        if test_texts is None:
            test_texts = [
                "This is a test sentence for benchmarking.",
                "Financial planning requires careful consideration of risk and return.",
                "Investment portfolios should be diversified across asset classes.",
                "Retirement planning starts with understanding your income needs.",
                "Tax-advantaged accounts can help optimize your investment returns."
            ]
        
        # Single text benchmark
        start_time = time.time()
        await self.embed_single(test_texts[0])
        single_latency = (time.time() - start_time) * 1000
        
        # Batch benchmark
        start_time = time.time()
        await self.generate_embeddings(test_texts)
        batch_latency = (time.time() - start_time) * 1000
        
        return {
            "model": self.model_name,
            "device": self.device,
            "single_text_latency_ms": round(single_latency, 2),
            "batch_latency_ms": round(batch_latency, 2),
            "texts_per_second": round(len(test_texts) / (batch_latency / 1000), 2),
            "avg_latency_per_text_ms": round(batch_latency / len(test_texts), 2),
            "test_texts_count": len(test_texts)
        }