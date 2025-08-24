"""
Lightweight Vector Service - Fallback for memory-constrained environments
Uses hnswlib or simple in-memory storage when ChromaDB is too heavy
"""

import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
import os

logger = structlog.get_logger()

# Try to import vector libraries, fallback to simple storage
try:
    import hnswlib
    import numpy as np
    VECTOR_BACKEND = "hnswlib"
except ImportError:
    VECTOR_BACKEND = "simple"
    logger.warning("hnswlib not available, using simple storage")

class LightweightVectorService:
    def __init__(self):
        self.storage_path = os.environ.get("VECTOR_STORAGE_PATH", "/tmp/vector_db")
        os.makedirs(self.storage_path, exist_ok=True)
        
        if VECTOR_BACKEND == "hnswlib":
            self._init_hnswlib()
        else:
            self._init_simple_storage()
        
        logger.info(f"LightweightVectorService initialized with {VECTOR_BACKEND} backend")
    
    def _init_hnswlib(self):
        """Initialize hnswlib index"""
        self.dim = 384  # Dimension for all-MiniLM-L6-v2
        self.max_elements = 10000
        
        index_path = os.path.join(self.storage_path, "index.bin")
        
        # Initialize or load index
        self.index = hnswlib.Index(space='cosine', dim=self.dim)
        
        if os.path.exists(index_path):
            self.index.load_index(index_path, max_elements=self.max_elements)
            logger.info("Loaded existing hnswlib index")
        else:
            self.index.init_index(max_elements=self.max_elements, ef_construction=200, M=16)
            logger.info("Created new hnswlib index")
        
        # Load metadata
        self.metadata = self._load_metadata()
    
    def _init_simple_storage(self):
        """Initialize simple JSON-based storage"""
        self.data_path = os.path.join(self.storage_path, "vectors.json")
        
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {"documents": {}, "metadata": {}}
    
    def _load_metadata(self) -> dict:
        """Load metadata from disk"""
        metadata_path = os.path.join(self.storage_path, "metadata.json")
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save metadata to disk"""
        metadata_path = os.path.join(self.storage_path, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f)
    
    def index_document(self, doc_id: str, content: str, metadata: dict):
        """Index a document"""
        if VECTOR_BACKEND == "hnswlib":
            # For hnswlib, we'd need embeddings (skipping for simplicity)
            # In production, use a lightweight embedding model
            pass
        else:
            # Simple storage
            self.data["documents"][doc_id] = {
                "content": content,
                "metadata": metadata,
                "indexed_at": datetime.utcnow().isoformat()
            }
            self._save_simple_storage()
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for relevant documents"""
        if VECTOR_BACKEND == "hnswlib":
            # Would need to compute query embedding and search
            return []
        else:
            # Simple keyword search
            results = []
            query_lower = query.lower()
            
            for doc_id, doc in self.data["documents"].items():
                if query_lower in doc["content"].lower():
                    results.append({
                        "id": doc_id,
                        "content": doc["content"],
                        "metadata": doc["metadata"],
                        "score": 1.0  # Simple match
                    })
            
            return results[:limit]
    
    def _save_simple_storage(self):
        """Save simple storage to disk"""
        with open(self.data_path, 'w') as f:
            json.dump(self.data, f)
    
    def get_document_count(self) -> int:
        """Get total document count"""
        if VECTOR_BACKEND == "simple":
            return len(self.data["documents"])
        else:
            return self.index.get_current_count()
    
    def clear_all(self):
        """Clear all stored data"""
        if VECTOR_BACKEND == "hnswlib":
            self._init_hnswlib()  # Reinitialize
        else:
            self.data = {"documents": {}, "metadata": {}}
            self._save_simple_storage()
        
        logger.info("Cleared all vector storage")

# Singleton instance
_instance = None

def get_vector_service() -> LightweightVectorService:
    """Get or create the vector service instance"""
    global _instance
    if _instance is None:
        _instance = LightweightVectorService()
    return _instance