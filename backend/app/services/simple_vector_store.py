"""
WealthPath AI - Simple JSON Vector Store
Pure Python in-memory vector store with JSON persistence
No ML dependencies - ChromaDB replacement
"""
import json
import os
import math
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SimpleDocument:
    """Simple document structure for the vector store"""
    
    def __init__(self, doc_id: str, content: str, embedding: Optional[List[float]] = None, metadata: Optional[Dict] = None):
        self.doc_id = doc_id
        self.content = content
        self.embedding = embedding or []
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for JSON serialization"""
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimpleDocument':
        """Create document from dictionary"""
        doc = cls(
            doc_id=data["doc_id"],
            content=data["content"],
            embedding=data.get("embedding", []),
            metadata=data.get("metadata", {})
        )
        doc.created_at = data.get("created_at", doc.created_at)
        doc.updated_at = data.get("updated_at", doc.updated_at)
        return doc


class SimpleVectorStore:
    """Simple in-memory vector store with JSON persistence"""
    
    def __init__(self, storage_path: str = "/tmp/vector_store.json"):
        self.storage_path = storage_path
        self.documents: Dict[str, SimpleDocument] = {}
        self.load_from_disk()
        logger.info(f"SimpleVectorStore initialized with {len(self.documents)} documents")
    
    def add_document(self, content: str, doc_id: Optional[str] = None, 
                    embedding: Optional[List[float]] = None, 
                    metadata: Optional[Dict] = None) -> str:
        """Add a document to the vector store"""
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        doc = SimpleDocument(
            doc_id=doc_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        self.documents[doc_id] = doc
        self.save_to_disk()
        
        logger.info(f"Added document {doc_id} to vector store")
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[SimpleDocument]:
        """Get a document by ID"""
        return self.documents.get(doc_id)
    
    def update_document(self, doc_id: str, content: Optional[str] = None,
                       embedding: Optional[List[float]] = None,
                       metadata: Optional[Dict] = None) -> bool:
        """Update an existing document"""
        if doc_id not in self.documents:
            return False
        
        doc = self.documents[doc_id]
        
        if content is not None:
            doc.content = content
        if embedding is not None:
            doc.embedding = embedding
        if metadata is not None:
            doc.metadata.update(metadata)
        
        doc.updated_at = datetime.utcnow().isoformat()
        self.save_to_disk()
        
        logger.info(f"Updated document {doc_id}")
        return True
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self.save_to_disk()
            logger.info(f"Deleted document {doc_id}")
            return True
        return False
    
    def search(self, query: str, limit: int = 10) -> List[Tuple[str, float, SimpleDocument]]:
        """Simple text-based search"""
        query_lower = query.lower()
        results = []
        
        for doc_id, doc in self.documents.items():
            # Simple keyword matching score
            content_lower = doc.content.lower()
            
            # Count keyword matches
            query_words = query_lower.split()
            matches = sum(1 for word in query_words if word in content_lower)
            
            if matches > 0:
                # Simple scoring: matches / total_query_words
                score = matches / len(query_words)
                results.append((doc_id, score, doc))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
    
    def search_by_embedding(self, query_embedding: List[float], limit: int = 10) -> List[Tuple[str, float, SimpleDocument]]:
        """Similarity search using cosine similarity"""
        if not query_embedding:
            return []
        
        results = []
        
        for doc_id, doc in self.documents.items():
            if not doc.embedding:
                continue
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, doc.embedding)
            
            if similarity > 0.0:  # Only include positive similarities
                results.append((doc_id, similarity, doc))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors using pure Python"""
        if len(vec1) != len(vec2):
            return 0.0
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        # Avoid division by zero
        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def get_all_documents(self) -> Dict[str, SimpleDocument]:
        """Get all documents"""
        return self.documents.copy()
    
    def count_documents(self) -> int:
        """Get total document count"""
        return len(self.documents)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics"""
        total_docs = len(self.documents)
        docs_with_embeddings = sum(1 for doc in self.documents.values() if doc.embedding)
        
        # Category breakdown
        categories = {}
        for doc in self.documents.values():
            category = doc.metadata.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_documents": total_docs,
            "documents_with_embeddings": docs_with_embeddings,
            "categories": categories,
            "storage_path": self.storage_path,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def save_to_disk(self) -> bool:
        """Save documents to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            data = {
                "documents": {doc_id: doc.to_dict() for doc_id, doc in self.documents.items()},
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.utcnow().isoformat(),
                    "document_count": len(self.documents)
                }
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved {len(self.documents)} documents to {self.storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save to disk: {e}")
            return False
    
    def load_from_disk(self) -> bool:
        """Load documents from JSON file"""
        if not os.path.exists(self.storage_path):
            logger.info(f"Storage file {self.storage_path} doesn't exist, starting with empty store")
            return True
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents_data = data.get("documents", {})
            self.documents = {
                doc_id: SimpleDocument.from_dict(doc_data)
                for doc_id, doc_data in documents_data.items()
            }
            
            logger.info(f"Loaded {len(self.documents)} documents from {self.storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load from disk: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all documents from the store"""
        self.documents.clear()
        self.save_to_disk()
        logger.info("Cleared all documents from vector store")
        return True


# Global instance
_vector_store_instance: Optional[SimpleVectorStore] = None


def get_vector_store(storage_path: Optional[str] = None) -> SimpleVectorStore:
    """Get the global vector store instance"""
    global _vector_store_instance
    
    if _vector_store_instance is None:
        if storage_path is None:
            storage_path = os.getenv("VECTOR_STORE_PATH", "/tmp/vector_store.json")
        _vector_store_instance = SimpleVectorStore(storage_path)
    
    return _vector_store_instance


def reset_vector_store():
    """Reset the global instance (useful for testing)"""
    global _vector_store_instance
    _vector_store_instance = None