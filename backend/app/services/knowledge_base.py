"""
Knowledge Base Service for Step 5 RAG System
Vector embeddings and semantic search for financial advice
"""
import os
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from dataclasses import dataclass
from datetime import datetime

# Vector embedding imports (will need to install)
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import pickle
except ImportError:
    # Fallback for development
    SentenceTransformer = None
    faiss = None


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
    embedding: Optional[np.ndarray] = None


@dataclass
class SearchResult:
    """Search result with relevance score"""
    document: KBDocument
    score: float
    relevance_explanation: str


class KnowledgeBaseService:
    """Vector-based knowledge base for financial advisory content"""
    
    def __init__(self, kb_path: str = None):
        self.kb_path = kb_path or "/mnt/c/projects/wpa/backend/knowledge_base"
        self.model_name = "all-MiniLM-L6-v2"  # Fast, good quality embeddings
        self.embeddings_cache_path = os.path.join(self.kb_path, ".embeddings_cache")
        self.index_path = os.path.join(self.kb_path, ".faiss_index")
        
        self.model = None
        self.documents: List[KBDocument] = []
        self.index = None
        self.document_map: Dict[str, KBDocument] = {}
        
        # Initialize if dependencies available
        if SentenceTransformer:
            self._initialize_model()
            self._load_or_build_index()
    
    def _initialize_model(self):
        """Initialize sentence transformer model"""
        try:
            self.model = SentenceTransformer(self.model_name)
        except Exception as e:
            print(f"Warning: Could not initialize embedding model: {e}")
            self.model = None
    
    def _load_or_build_index(self):
        """Load existing index or build new one from KB files"""
        if os.path.exists(self.embeddings_cache_path) and os.path.exists(self.index_path):
            self._load_index()
        else:
            self._build_index()
    
    def _load_index(self):
        """Load pre-built FAISS index and document cache"""
        try:
            if faiss:
                self.index = faiss.read_index(self.index_path)
            
            with open(self.embeddings_cache_path, 'rb') as f:
                cache_data = pickle.load(f)
                self.documents = cache_data['documents']
                self.document_map = {doc.id: doc for doc in self.documents}
            
            print(f"Loaded knowledge base with {len(self.documents)} documents")
        except Exception as e:
            print(f"Error loading index, rebuilding: {e}")
            self._build_index()
    
    def _build_index(self):
        """Build FAISS index from knowledge base files"""
        if not self.model:
            print("Warning: No embedding model available, using fallback")
            return
        
        print("Building knowledge base index...")
        
        # Scan knowledge base directory
        kb_files = []
        for root, dirs, files in os.walk(self.kb_path):
            for file in files:
                if file.endswith('.md') and not file.startswith('.'):
                    kb_files.append(os.path.join(root, file))
        
        # Process each file
        embeddings = []
        for file_path in kb_files:
            document = self._process_kb_file(file_path)
            if document:
                self.documents.append(document)
                self.document_map[document.id] = document
                
                # Generate embedding
                if self.model:
                    embedding = self.model.encode(document.content)
                    document.embedding = embedding
                    embeddings.append(embedding)
        
        # Build FAISS index
        if embeddings and faiss:
            embeddings_matrix = np.array(embeddings).astype('float32')
            dimension = embeddings_matrix.shape[1]
            
            # Use flat index for simplicity (can upgrade to IVF for large datasets)
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings_matrix)
            self.index.add(embeddings_matrix)
            
            # Save index and cache
            faiss.write_index(self.index, self.index_path)
            
            with open(self.embeddings_cache_path, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'model_name': self.model_name
                }, f)
        
        print(f"Built index with {len(self.documents)} documents")
    
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
        """Search knowledge base with semantic similarity"""
        
        if not self.model or not self.index:
            # Fallback to keyword search
            return self._fallback_search(query, filters, top_k)
        
        try:
            # Encode query
            query_embedding = self.model.encode([query])
            query_embedding = query_embedding.astype('float32')
            faiss.normalize_L2(query_embedding)
            
            # Search index
            scores, indices = self.index.search(query_embedding, min(top_k * 2, len(self.documents)))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1 or score < min_score:
                    continue
                
                document = self.documents[idx]
                
                # Apply filters
                if self._matches_filters(document, filters):
                    results.append(SearchResult(
                        document=document,
                        score=float(score),
                        relevance_explanation=self._explain_relevance(query, document, score)
                    ))
            
            return results[:top_k]
            
        except Exception as e:
            print(f"Search error: {e}")
            return self._fallback_search(query, filters, top_k)
    
    def _fallback_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[SearchResult]:
        """Fallback keyword-based search when embeddings unavailable"""
        query_terms = query.lower().split()
        results = []
        
        for document in self.documents:
            if not self._matches_filters(document, filters):
                continue
            
            # Simple keyword matching
            content_lower = document.content.lower()
            title_lower = document.title.lower()
            
            score = 0
            matches = 0
            for term in query_terms:
                title_matches = title_lower.count(term)
                content_matches = content_lower.count(term)
                
                score += title_matches * 3  # Title matches worth more
                score += content_matches
                if title_matches > 0 or content_matches > 0:
                    matches += 1
            
            if matches > 0:
                # Normalize score
                normalized_score = min(1.0, score / (len(query_terms) * 10))
                results.append(SearchResult(
                    document=document,
                    score=normalized_score,
                    relevance_explanation=f"Keyword matches: {matches}/{len(query_terms)} terms"
                ))
        
        # Sort by score and return top k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
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
        return [doc for doc in self.documents if doc.category == category]
    
    def list_categories(self) -> List[str]:
        """Get list of all categories"""
        return list(set(doc.category for doc in self.documents))
    
    def refresh_index(self):
        """Rebuild the index from current KB files"""
        self._build_index()
    
    def add_document(self, file_path: str) -> bool:
        """Add a new document to the knowledge base"""
        document = self._process_kb_file(file_path)
        if document and self.model:
            # Generate embedding
            embedding = self.model.encode(document.content)
            document.embedding = embedding
            
            # Add to collections
            self.documents.append(document)
            self.document_map[document.id] = document
            
            # Update index
            if self.index and faiss:
                embedding_matrix = np.array([embedding]).astype('float32')
                faiss.normalize_L2(embedding_matrix)
                self.index.add(embedding_matrix)
            
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
    
    # Test filters
    filtered_results = kb.search(
        "rebalancing portfolio", 
        filters={'category': 'playbooks'}, 
        top_k=2
    )
    print(f"\nFiltered results: {len(filtered_results)}")