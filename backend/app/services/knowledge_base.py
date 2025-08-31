"""
Knowledge Base Service for Step 5 RAG System
Simple vector store with JSON persistence - No ML dependencies
"""
import os
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from .simple_vector_store import get_vector_store, SimpleDocument
# smart_context_selector was removed during cleanup - using simplified context selection


@dataclass
class KBDocument:
    """Knowledge base document with metadata"""
    id: str
    title: str
    content: str
    category: str
    kb_id: str
    file_path: str
    last_updated: str
    tags: List[str]
    embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    """Search result with relevance score"""
    document: KBDocument
    score: float
    relevance_explanation: str


class KnowledgeBaseService:
    """Simple knowledge base using JSON vector store"""
    
    def __init__(self, kb_path: str = None):
        self.kb_path = kb_path or "/mnt/c/projects/wpa/backend/knowledge_base" 
        self.vector_store = get_vector_store()
        # Simplified context selection - smart_context_selector was removed during cleanup
        self.context_selector = None
        self.document_map: Dict[str, KBDocument] = {}
        
        # Load documents from file system if needed
        self._load_documents_from_filesystem()
    
    def _load_documents_from_filesystem(self):
        """Load documents from filesystem into vector store if needed"""
        if self.vector_store.count_documents() > 0:
            print(f"Vector store already has {self.vector_store.count_documents()} documents")
            self._update_document_map()
            return
        
        if not os.path.exists(self.kb_path):
            print(f"Warning: Knowledge base path {self.kb_path} does not exist")
            return
        
        print("Loading documents from filesystem...")
        
        # Scan knowledge base directory
        kb_files = []
        for root, dirs, files in os.walk(self.kb_path):
            for file in files:
                if file.endswith('.md') and not file.startswith('.'):
                    kb_files.append(os.path.join(root, file))
        
        # Process each file
        for file_path in kb_files:
            kb_document = self._process_kb_file(file_path)
            if kb_document:
                # Add to vector store
                self.vector_store.add_document(
                    content=kb_document.content,
                    doc_id=kb_document.id,
                    embedding=kb_document.embedding,
                    metadata={
                        "title": kb_document.title,
                        "category": kb_document.category,
                        "kb_id": kb_document.kb_id,
                        "file_path": kb_document.file_path,
                        "last_updated": kb_document.last_updated,
                        "tags": kb_document.tags
                    }
                )
                self.document_map[kb_document.id] = kb_document
        
        print(f"Loaded {len(kb_files)} documents into vector store")
    
    def _update_document_map(self):
        """Update document map from vector store"""
        for doc_id, simple_doc in self.vector_store.get_all_documents().items():
            kb_doc = KBDocument(
                id=doc_id,
                title=simple_doc.metadata.get("title", "Untitled"),
                content=simple_doc.content,
                category=simple_doc.metadata.get("category", "general"),
                kb_id=simple_doc.metadata.get("kb_id", doc_id[:8]),
                file_path=simple_doc.metadata.get("file_path", ""),
                last_updated=simple_doc.metadata.get("last_updated", simple_doc.created_at[:10]),
                tags=simple_doc.metadata.get("tags", []),
                embedding=simple_doc.embedding
            )
            self.document_map[doc_id] = kb_doc
    
    def _process_kb_file(self, file_path: str) -> Optional[KBDocument]:
        """Process a knowledge base markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from markdown
            metadata = self._extract_metadata(content)
            
            # Generate document ID
            relative_path = os.path.relpath(file_path, self.kb_path)
            doc_id = hashlib.md5(relative_path.encode()).hexdigest()[:8]
            
            # Determine category from path
            path_parts = Path(relative_path).parts
            category = path_parts[0] if len(path_parts) > 1 else 'general'
            
            document = KBDocument(
                id=doc_id,
                title=metadata.get('title', Path(file_path).stem.replace('_', ' ').title()),
                content=content,
                category=category,
                kb_id=metadata.get('kb_id', f"{category.upper()}-{doc_id[:3]}"),
                file_path=relative_path,
                last_updated=metadata.get('last_updated', datetime.now().isoformat()[:10]),
                tags=metadata.get('tags', [])
            )
            
            return document
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from markdown file headers"""
        metadata = {}
        lines = content.split('\n')
        
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if line.startswith('**KB-ID:'):
                metadata['kb_id'] = line.split(':', 1)[1].strip().replace('**', '')
            elif line.startswith('**Category:'):
                metadata['category'] = line.split(':', 1)[1].strip().replace('**', '')
            elif line.startswith('**Last Updated:'):
                metadata['last_updated'] = line.split(':', 1)[1].strip().replace('**', '')
            elif line.startswith('**Tags:'):
                tags_str = line.split(':', 1)[1].strip().replace('**', '')
                metadata['tags'] = [tag.strip() for tag in tags_str.split(',')]
            elif line.startswith('# '):
                metadata['title'] = line[2:].strip()
        
        return metadata
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        min_score: float = 0.1
    ) -> List[SearchResult]:
        """Search knowledge base using simple vector store and smart context selection"""
        
        # Get smart filtering recommendations
        # Use simplified filtering since context_selector was removed
        filter_recommendations = {'categories': ['financial', 'tax', 'investment']}
        
        try:
            # First try text search
            text_results = self.vector_store.search(query, limit=top_k * 2)
            
            results = []
            for doc_id, score, simple_doc in text_results:
                if score < min_score:
                    continue
                
                # Convert to KB document
                kb_doc = self._simple_doc_to_kb_doc(simple_doc)
                
                # Apply filters
                if self._matches_filters(kb_doc, filters):
                    # Boost score if matches smart context recommendations
                    if self._matches_smart_context(kb_doc, filter_recommendations):
                        score = min(1.0, score * 1.3)  # 30% boost for relevant categories
                    
                    results.append(SearchResult(
                        document=kb_doc,
                        score=score,
                        relevance_explanation=self._explain_relevance(query, kb_doc, score)
                    ))
            
            # If we have embeddings available, also try embedding search
            if hasattr(self, 'embeddings_available') and self.embeddings_available:
                # This would require OpenAI embeddings - implement later if needed
                pass
            
            return results[:top_k]
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def _simple_doc_to_kb_doc(self, simple_doc: SimpleDocument) -> KBDocument:
        """Convert SimpleDocument to KBDocument"""
        return KBDocument(
            id=simple_doc.doc_id,
            title=simple_doc.metadata.get("title", "Untitled"),
            content=simple_doc.content,
            category=simple_doc.metadata.get("category", "general"),
            kb_id=simple_doc.metadata.get("kb_id", simple_doc.doc_id[:8]),
            file_path=simple_doc.metadata.get("file_path", ""),
            last_updated=simple_doc.metadata.get("last_updated", simple_doc.created_at[:10]),
            tags=simple_doc.metadata.get("tags", []),
            embedding=simple_doc.embedding
        )
    
    def _matches_smart_context(self, document: KBDocument, filter_recommendations: Dict[str, Any]) -> bool:
        """Check if document matches smart context recommendations"""
        if not filter_recommendations.get("categories"):
            return False
        
        return document.category in filter_recommendations["categories"]
    
    def _matches_filters(self, document: KBDocument, filters: Optional[Dict[str, Any]]) -> bool:
        """Check if document matches search filters"""
        if not filters:
            return True
        
        # Category filter
        if 'category' in filters:
            if document.category != filters['category']:
                return False
        
        # Tag filter
        if 'tags' in filters:
            required_tags = filters['tags'] if isinstance(filters['tags'], list) else [filters['tags']]
            if not any(tag in document.tags for tag in required_tags):
                return False
        
        # KB ID filter
        if 'kb_id' in filters:
            if document.kb_id != filters['kb_id']:
                return False
        
        return True
    
    def _explain_relevance(self, query: str, document: KBDocument, score: float) -> str:
        """Generate explanation for why document is relevant"""
        if score > 0.8:
            return f"High relevance to '{query}' - closely matches document topic"
        elif score > 0.6:
            return f"Good relevance to '{query}' - document contains related concepts"
        elif score > 0.4:
            return f"Moderate relevance to '{query}' - document may contain useful context"
        else:
            return f"Low relevance to '{query}' - document tangentially related"
    
    def get_document_by_id(self, doc_id: str) -> Optional[KBDocument]:
        """Retrieve document by ID"""
        return self.document_map.get(doc_id)
    
    def get_documents_by_category(self, category: str) -> List[KBDocument]:
        """Get all documents in a category"""
        results = []
        for simple_doc in self.vector_store.get_all_documents().values():
            if simple_doc.metadata.get("category") == category:
                results.append(self._simple_doc_to_kb_doc(simple_doc))
        return results
    
    def list_categories(self) -> List[str]:
        """Get list of all categories"""
        categories = set()
        for simple_doc in self.vector_store.get_all_documents().values():
            category = simple_doc.metadata.get("category", "general")
            categories.add(category)
        return list(categories)
    
    def refresh_index(self):
        """Rebuild the index from current KB files"""
        self.vector_store.clear_all()
        self.document_map.clear()
        self._load_documents_from_filesystem()
    
    def add_document(self, file_path: str) -> bool:
        """Add a new document to the knowledge base"""
        document = self._process_kb_file(file_path)
        if document:
            # Add to vector store
            doc_id = self.vector_store.add_document(
                content=document.content,
                doc_id=document.id,
                embedding=document.embedding,
                metadata={
                    "title": document.title,
                    "category": document.category,
                    "kb_id": document.kb_id,
                    "file_path": document.file_path,
                    "last_updated": document.last_updated,
                    "tags": document.tags
                }
            )
            self.document_map[doc_id] = document
            return True
        return False
    
    def get_related_documents(self, doc_id: str, top_k: int = 3) -> List[SearchResult]:
        """Find documents related to a given document"""
        document = self.get_document_by_id(doc_id)
        if not document:
            return []
        
        # Use document title and first paragraph as query
        lines = document.content.split('\n')
        query_text = document.title
        for line in lines:
            if line.strip() and not line.startswith('#') and not line.startswith('**'):
                query_text += " " + line.strip()
                break
        
        results = self.search(query_text, top_k=top_k + 1)
        
        # Remove the original document from results
        return [result for result in results if result.document.id != doc_id][:top_k]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            "total_documents": self.vector_store.count_documents(),
            "categories": self.list_categories(),
            "vector_store_stats": self.vector_store.get_stats()
        }


# Example usage and testing
if __name__ == "__main__":
    kb = KnowledgeBaseService()
    
    # Test search
    results = kb.search("asset allocation for retirement planning", top_k=3)
    for result in results:
        print(f"Score: {result.score:.3f}")
        print(f"Title: {result.document.title}")
        print(f"KB-ID: {result.document.kb_id}")
        print(f"Explanation: {result.relevance_explanation}")
        print("---")
    
    # Test category listing
    print("Categories:", kb.list_categories())
    
    # Test stats
    print("Stats:", kb.get_stats())