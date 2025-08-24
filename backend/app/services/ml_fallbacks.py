"""
Fallback implementations when ML packages are not available
Provides basic functionality without numpy, pandas, torch, etc.
"""

from typing import List, Dict, Any, Optional
import json


class NumpyFallback:
    """Basic numpy operations without numpy"""
    
    @staticmethod
    def array(data):
        """Convert to array fallback"""
        if isinstance(data, list):
            return NumpyFallback.ArrayFallback(data)
        elif hasattr(data, '__iter__'):
            return NumpyFallback.ArrayFallback(list(data))
        else:
            return NumpyFallback.ArrayFallback([data])
    
    @staticmethod
    def mean(data):
        """Calculate mean without numpy"""
        if not data:
            return 0
        return sum(data) / len(data)
    
    @staticmethod
    def dot(a, b):
        """Dot product fallback"""
        return sum(x * y for x, y in zip(a, b))
    
    @staticmethod
    def zeros(shape):
        """Create zeros array"""
        if isinstance(shape, int):
            return [0] * shape
        elif isinstance(shape, tuple) and len(shape) == 2:
            return [[0] * shape[1] for _ in range(shape[0])]
        else:
            return []
    
    @staticmethod
    def sum(data):
        """Sum fallback"""
        return sum(data) if data else 0
    
    @staticmethod
    def astype(data, dtype):
        """Type conversion fallback"""
        return data  # Just return as-is for fallback
    
    class ArrayFallback:
        def __init__(self, data):
            self.data = data
            self.shape = (len(data), len(data[0]) if data and hasattr(data[0], '__len__') else 1) if data else (0, 0)
        
        def astype(self, dtype):
            return self


class PandasFallback:
    """Basic pandas operations without pandas"""
    
    @staticmethod
    def DataFrame(data):
        """Simple DataFrame fallback using dict"""
        if isinstance(data, dict):
            return data
        elif isinstance(data, list) and data:
            # Convert list of dicts to dict of lists
            if isinstance(data[0], dict):
                result = {}
                for key in data[0].keys():
                    result[key] = [row.get(key) for row in data]
                return result
        return {"data": data}
    
    @staticmethod
    def Series(data):
        """Simple Series fallback using list"""
        return list(data) if hasattr(data, '__iter__') else [data]


class EmbeddingsFallback:
    """Fallback for embedding operations"""
    
    @staticmethod
    def encode(texts: List[str]) -> List[List[float]]:
        """Simple hash-based embedding fallback"""
        embeddings = []
        for text in texts:
            # Create a simple hash-based embedding
            hash_val = hash(text.lower())
            # Convert to a list of floats (384 dimensions like all-MiniLM-L6-v2)
            embedding = []
            for i in range(384):
                embedding.append((hash_val * (i + 1)) % 1000 / 1000.0)
            embeddings.append(embedding)
        return embeddings
    
    @staticmethod
    def similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """Simple cosine similarity fallback"""
        # Dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        
        # Magnitudes
        mag1 = sum(a * a for a in embedding1) ** 0.5
        mag2 = sum(b * b for b in embedding2) ** 0.5
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)


def get_ml_fallbacks():
    """Get fallback implementations for all ML packages"""
    return {
        'numpy': NumpyFallback(),
        'pandas': PandasFallback(), 
        'embeddings': EmbeddingsFallback()
    }


# Global fallback instances
try:
    # import numpy as np # DISABLED FOR DEPLOYMENT
    raise ImportError("ML packages disabled for deployment")
    HAS_NUMPY = True
except ImportError:
    np = NumpyFallback()
    HAS_NUMPY = False

try:
    # import pandas as pd # DISABLED FOR DEPLOYMENT
    raise ImportError("ML packages disabled for deployment")
    HAS_PANDAS = True
except ImportError:
    pd = PandasFallback()
    HAS_PANDAS = False

# Export common fallbacks
__all__ = ['np', 'pd', 'HAS_NUMPY', 'HAS_PANDAS', 'NumpyFallback', 'PandasFallback', 'EmbeddingsFallback']