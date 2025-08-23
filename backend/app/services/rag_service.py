"""
WealthPath AI - RAG Knowledge Base System
Retrieval Augmented Generation with vector search and citations
"""
import asyncio
import json
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from datetime import datetime

from ..models.llm_models import (
    KnowledgeBaseDocument, Citation, RAGQuery, RAGResult
)

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for document embeddings"""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        self.documents: Dict[str, KnowledgeBaseDocument] = {}
        self.doc_ids: List[str] = []
    
    def add_documents(self, documents: List[KnowledgeBaseDocument]):
        """Add documents to vector store"""
        embeddings = []
        
        for doc in documents:
            if doc.embedding:
                embeddings.append(doc.embedding)
                self.documents[doc.doc_id] = doc
                self.doc_ids.append(doc.doc_id)
        
        if embeddings:
            embeddings_array = np.array(embeddings, dtype=np.float32)
            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings_array)
            self.index.add(embeddings_array)
            logger.info(f"Added {len(embeddings)} documents to vector store")
    
    def search(self, query_embedding: List[float], k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar documents"""
        if self.index.ntotal == 0:
            return []
        
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        scores, indices = self.index.search(query_array, min(k, self.index.ntotal))
        
        results = []
        for i, score in zip(indices[0], scores[0]):
            if i != -1 and i < len(self.doc_ids):
                doc_id = self.doc_ids[i]
                results.append((doc_id, float(score)))
        
        return results
    
    def get_document(self, doc_id: str) -> Optional[KnowledgeBaseDocument]:
        """Get document by ID"""
        return self.documents.get(doc_id)


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Initialized embedding service with model: {model_name}")
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()
    
    def encode_single(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        embedding = self.model.encode([text], convert_to_tensor=False)
        return embedding[0].tolist()


class KnowledgeBase:
    """Comprehensive knowledge base with document management and search"""
    
    def __init__(self, data_path: str = "/mnt/c/projects/wpa/knowledge_base"):
        self.data_path = Path(data_path)
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore(dimension=self.embedding_service.dimension)
        self.documents: Dict[str, KnowledgeBaseDocument] = {}
        self._load_documents()
    
    def _load_documents(self):
        """Load documents from knowledge base directory"""
        if not self.data_path.exists():
            logger.warning(f"Knowledge base directory not found: {self.data_path}")
            return
        
        documents = []
        
        # Load documents from different categories
        for category_dir in self.data_path.iterdir():
            if category_dir.is_dir():
                category = category_dir.name
                logger.info(f"Loading documents from category: {category}")
                
                for file_path in category_dir.glob("*.md"):
                    doc = self._load_document_file(file_path, category)
                    if doc:
                        documents.append(doc)
                        self.documents[doc.doc_id] = doc
        
        # Generate embeddings and add to vector store
        if documents:
            self._generate_embeddings(documents)
            self.vector_store.add_documents(documents)
            logger.info(f"Loaded {len(documents)} documents into knowledge base")
    
    def _load_document_file(self, file_path: Path, category: str) -> Optional[KnowledgeBaseDocument]:
        """Load a single document file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract metadata from content if present
            title = file_path.stem.replace('_', ' ').title()
            doc_type = self._determine_doc_type(file_path.name, content)
            tags = self._extract_tags(content)
            
            doc_id = hashlib.md5(f"{category}_{file_path.name}".encode()).hexdigest()[:16]
            
            document = KnowledgeBaseDocument(
                doc_id=doc_id,
                title=title,
                content=content,
                doc_type=doc_type,
                category=category,
                tags=tags,
                metadata={
                    "file_path": str(file_path),
                    "file_size": file_path.stat().st_size,
                    "word_count": len(content.split())
                }
            )
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {e}")
            return None
    
    def _determine_doc_type(self, filename: str, content: str) -> str:
        """Determine document type based on filename and content"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        if 'playbook' in filename_lower or 'guide' in filename_lower:
            return "playbook"
        elif 'regulation' in filename_lower or 'compliance' in filename_lower:
            return "regulation"
        elif 'research' in filename_lower or 'analysis' in filename_lower:
            return "research"
        elif 'template' in filename_lower or 'example' in filename_lower:
            return "template"
        else:
            # Analyze content for type hints
            if any(word in content_lower for word in ['regulation', 'compliance', 'sec', 'finra']):
                return "regulation"
            elif any(word in content_lower for word in ['study', 'research', 'analysis', 'findings']):
                return "research"
            else:
                return "playbook"
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from document content"""
        tags = []
        
        # Look for explicit tags in content
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if line.strip().startswith('Tags:') or line.strip().startswith('Keywords:'):
                tag_text = line.split(':', 1)[1].strip()
                tags.extend([tag.strip() for tag in tag_text.split(',')])
                break
        
        # Add implicit tags based on content
        content_lower = content.lower()
        tag_keywords = {
            'retirement': ['retirement', '401k', 'ira', 'pension'],
            'investment': ['investment', 'portfolio', 'asset allocation', 'diversification'],
            'tax': ['tax', 'taxation', 'deduction', 'tax-advantaged'],
            'estate': ['estate', 'inheritance', 'trust', 'will'],
            'insurance': ['insurance', 'life insurance', 'disability'],
            'debt': ['debt', 'mortgage', 'loan', 'credit'],
            'goals': ['goals', 'planning', 'objective', 'target'],
            'risk': ['risk', 'volatility', 'risk tolerance', 'conservative']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append(tag)
        
        return list(set(tags))  # Remove duplicates
    
    def _generate_embeddings(self, documents: List[KnowledgeBaseDocument]):
        """Generate embeddings for documents"""
        texts = []
        doc_indices = []
        
        for i, doc in enumerate(documents):
            # Create text for embedding (title + content preview)
            text = f"{doc.title}\n{doc.content[:1000]}"  # Use first 1000 chars
            texts.append(text)
            doc_indices.append(i)
        
        if texts:
            embeddings = self.embedding_service.encode(texts)
            for i, embedding in zip(doc_indices, embeddings):
                documents[i].embedding = embedding
    
    async def search(self, query: RAGQuery) -> RAGResult:
        """Search knowledge base and return relevant documents"""
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = self.embedding_service.encode_single(query.query)
        
        # Search vector store
        search_results = self.vector_store.search(
            query_embedding, 
            k=query.max_results * 2  # Get more results for filtering
        )
        
        # Filter and rank results
        filtered_docs = []
        citations = []
        
        for doc_id, score in search_results:
            if score < query.min_relevance_score:
                continue
            
            doc = self.vector_store.get_document(doc_id)
            if not doc:
                continue
            
            # Apply filters
            if query.doc_types and doc.doc_type not in query.doc_types:
                continue
            if query.categories and doc.category not in query.categories:
                continue
            if query.tags and not any(tag in doc.tags for tag in query.tags):
                continue
            
            filtered_docs.append(doc)
            
            # Create citation
            citation = Citation(
                doc_id=doc.doc_id,
                title=doc.title,
                excerpt=self._extract_relevant_excerpt(doc.content, query.query),
                relevance_score=score
            )
            citations.append(citation)
            
            if len(filtered_docs) >= query.max_results:
                break
        
        search_time = time.time() - start_time
        
        result = RAGResult(
            documents=filtered_docs,
            citations=citations,
            search_metadata={
                "query": query.query,
                "total_vector_results": len(search_results),
                "filtered_results": len(filtered_docs),
                "filters_applied": {
                    "doc_types": query.doc_types,
                    "categories": query.categories,
                    "tags": query.tags,
                    "min_relevance": query.min_relevance_score
                }
            },
            total_results=len(search_results),
            search_time=search_time
        )
        
        logger.info(f"RAG search completed in {search_time:.2f}s, returned {len(filtered_docs)} documents")
        return result
    
    def _extract_relevant_excerpt(self, content: str, query: str, max_length: int = 200) -> str:
        """Extract relevant excerpt from document content"""
        sentences = content.split('.')
        query_words = set(query.lower().split())
        
        best_sentence = ""
        max_overlap = 0
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = len(query_words.intersection(sentence_words))
            
            if overlap > max_overlap:
                max_overlap = overlap
                best_sentence = sentence.strip()
        
        if not best_sentence:
            # Fallback to first sentence or beginning of content
            best_sentence = sentences[0] if sentences else content[:max_length]
        
        # Truncate if too long
        if len(best_sentence) > max_length:
            best_sentence = best_sentence[:max_length] + "..."
        
        return best_sentence
    
    def add_document(self, document: KnowledgeBaseDocument) -> bool:
        """Add a new document to the knowledge base"""
        try:
            # Generate embedding if not present
            if not document.embedding:
                text = f"{document.title}\n{document.content[:1000]}"
                document.embedding = self.embedding_service.encode_single(text)
            
            # Add to stores
            self.documents[document.doc_id] = document
            self.vector_store.add_documents([document])
            
            logger.info(f"Added document to knowledge base: {document.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[KnowledgeBaseDocument]:
        """Get document by ID"""
        return self.documents.get(doc_id)
    
    def list_documents(self, 
                      doc_type: Optional[str] = None, 
                      category: Optional[str] = None) -> List[KnowledgeBaseDocument]:
        """List documents with optional filtering"""
        docs = list(self.documents.values())
        
        if doc_type:
            docs = [doc for doc in docs if doc.doc_type == doc_type]
        if category:
            docs = [doc for doc in docs if doc.category == category]
        
        return sorted(docs, key=lambda d: d.title)


# Global knowledge base instance
knowledge_base = KnowledgeBase()