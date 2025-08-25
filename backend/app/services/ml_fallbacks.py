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
    
    @staticmethod
    def sin(x):
        """Sine function fallback"""
        import math
        if isinstance(x, list):
            return [math.sin(val) for val in x]
        return math.sin(x)
    
    @staticmethod
    def sqrt(x):
        """Square root fallback"""
        import math
        if isinstance(x, list):
            return [math.sqrt(val) if val >= 0 else 0 for val in x]
        return math.sqrt(x) if x >= 0 else 0
    
    @staticmethod
    def std(data, axis=None):
        """Standard deviation fallback"""
        if not data:
            return 0
        mean_val = NumpyFallback.mean(data)
        variance = sum((x - mean_val) ** 2 for x in data) / len(data)
        return variance ** 0.5
    
    @staticmethod
    def percentile(data, q, axis=None):
        """Percentile fallback"""
        if not data:
            return []
        if isinstance(data[0], list):
            # Handle 2D array-like data
            result = []
            for col in range(len(data[0])):
                col_data = sorted([row[col] for row in data])
                idx = int((q / 100) * (len(col_data) - 1))
                result.append(col_data[idx])
            return result
        else:
            # Handle 1D data
            sorted_data = sorted(data)
            idx = int((q / 100) * (len(sorted_data) - 1))
            return sorted_data[idx]
    
    @property  
    def pi(self):
        """Pi constant"""
        import math
        return math.pi
    
    class RandomFallback:
        """Random number generation fallback"""
        @staticmethod
        def normal(mean=0.0, std=1.0, size=None):
            import random
            if size is None:
                return random.gauss(mean, std)
            elif isinstance(size, int):
                return [random.gauss(mean, std) for _ in range(size)]
            else:
                # Handle tuple size
                return [[random.gauss(mean, std) for _ in range(size[1])] for _ in range(size[0])]
        
        @staticmethod
        def uniform(low=0.0, high=1.0, size=None):
            import random
            if size is None:
                return random.uniform(low, high)
            elif isinstance(size, int):
                return [random.uniform(low, high) for _ in range(size)]
            else:
                return [[random.uniform(low, high) for _ in range(size[1])] for _ in range(size[0])]
    
    random = RandomFallback()
    
    class LinalgFallback:
        """Linear algebra fallbacks"""
        @staticmethod
        def norm(x):
            """Vector norm fallback"""
            if isinstance(x, list):
                return sum(val * val for val in x) ** 0.5
            return abs(x)
        
        @staticmethod
        def pad(array, pad_width, mode='constant', constant_values=0):
            """Simple padding fallback"""
            if isinstance(array, list):
                if isinstance(pad_width, tuple) and len(pad_width) == 2:
                    left_pad, right_pad = pad_width
                    return [constant_values] * left_pad + array + [constant_values] * right_pad
                else:
                    return [constant_values] * pad_width + array + [constant_values] * pad_width
            return array
    
    linalg = LinalgFallback()
    
    @staticmethod
    def pad(array, pad_width, mode='constant', constant_values=0):
        """Pad array fallback"""
        return NumpyFallback.linalg.pad(array, pad_width, mode, constant_values)
    
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