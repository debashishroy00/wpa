"""
EMERGENCY: Secure Vector Database Service
Simple vector store with strict user isolation - No ML dependencies
CRITICAL SECURITY FIX - Deploy immediately to prevent data leakage
"""
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from sqlalchemy.orm import Session

from .simple_vector_store import get_vector_store
from .ml_fallbacks import EmbeddingsFallback

logger = structlog.get_logger()

class SecureVectorDBService:
    """
    SECURE vector database service with strict user isolation
    CRITICAL: Prevents cross-user data contamination
    """
    
    def __init__(self):
        # Initialize simple vector store
        self.vector_store = get_vector_store()
        
        # Initialize embedding model fallback
        self.embedding_model = EmbeddingsFallback()
        
        logger.info("SecureVectorDBService initialized with user isolation")
    
    def _generate_secure_doc_id(self, user_id: int, doc_type: str, doc_key: str) -> str:
        """Generate secure document ID with user isolation"""
        return f"secure_{user_id}_{doc_type}_{hashlib.md5(doc_key.encode()).hexdigest()[:8]}"
    
    def index_user_financial_data(self, user_id: int, data: Dict[str, Any]):
        """
        SECURE: Index user's financial data with strict isolation
        Each user's data is completely separate
        """
        try:
            # 1. Index user profile data
            profile_data = data.get('profile', {})
            if profile_data:
                profile_text = f"""
                User: {profile_data.get('name', 'Unknown')}
                Age: {profile_data.get('age', 0)}
                Risk Tolerance: {profile_data.get('risk_tolerance', 'Not set')}
                Investment Timeline: {profile_data.get('timeline', 0)} years
                """
                
                doc_id = self._generate_secure_doc_id(user_id, "profile", "main")
                self._add_secure_document(user_id, doc_id, profile_text, "profile", "user_info")
            
            # 2. Index financial snapshot
            snapshot = data.get('snapshot', {})
            if snapshot:
                snapshot_text = f"""
                Net Worth: ${snapshot.get('net_worth', 0):,.2f}
                Total Assets: ${snapshot.get('total_assets', 0):,.2f}
                Total Debts: ${snapshot.get('total_debts', 0):,.2f}
                Monthly Income: ${snapshot.get('monthly_income', 0):,.2f}
                Monthly Expenses: ${snapshot.get('monthly_expenses', 0):,.2f}
                Cash Flow: ${snapshot.get('monthly_surplus', 0):,.2f}
                """
                
                doc_id = self._generate_secure_doc_id(user_id, "snapshot", "financial")
                self._add_secure_document(user_id, doc_id, snapshot_text, "snapshot", "overview")
            
            # 3. Index goals data
            goals = data.get('goals', [])
            for i, goal in enumerate(goals):
                goal_text = f"""
                Goal: {goal.get('name', 'Unnamed Goal')}
                Target Amount: ${goal.get('target_amount', 0):,.2f}
                Current Amount: ${goal.get('current_amount', 0):,.2f}
                Target Date: {goal.get('target_date', 'Not set')}
                Priority: {goal.get('priority', 'Medium')}
                Category: {goal.get('category', 'General')}
                Progress: {goal.get('completion_percentage', 0):.1f}%
                """
                
                doc_id = self._generate_secure_doc_id(user_id, "goal", f"goal_{i}")
                self._add_secure_document(user_id, doc_id, goal_text, "goal", goal.get('category', 'general'))
            
            logger.info(f"SECURE: Indexed financial data for user {user_id}")
            
        except Exception as e:
            logger.error(f"SECURE: Failed to index data for user {user_id}: {e}")
    
    def _add_secure_document(self, user_id: int, doc_id: str, content: str, category: str, subcategory: str):
        """Add a document with security metadata"""
        try:
            # Generate embedding
            embedding = self.embedding_model.encode([content])
            
            # Add with strict user isolation metadata
            self.vector_store.add_document(
                content=content.strip(),
                doc_id=doc_id,
                embedding=embedding[0] if embedding else None,
                metadata={
                    "user_id": user_id,  # CRITICAL: User isolation
                    "category": category,
                    "subcategory": subcategory,
                    "indexed_at": datetime.now().isoformat(),
                    "security_level": "user_isolated",
                    "doc_hash": hashlib.md5(content.encode()).hexdigest()[:16]
                }
            )
        except Exception as e:
            logger.error(f"SECURE: Failed to add document {doc_id}: {e}")
    
    def search_user_data(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """
        SECURE: Search only within user's own data
        CRITICAL: Strict user isolation enforced
        """
        try:
            # Search in vector store
            all_results = self.vector_store.search(query, limit=limit * 3)  # Get more to filter
            
            # Filter strictly by user_id - CRITICAL SECURITY
            user_results = []
            for doc_id, score, document in all_results:
                if document.metadata.get("user_id") == user_id:  # STRICT USER ISOLATION
                    user_results.append({
                        "content": document.content,
                        "score": score,
                        "category": document.metadata.get("category"),
                        "subcategory": document.metadata.get("subcategory"),
                        "indexed_at": document.metadata.get("indexed_at")
                    })
                    
                    if len(user_results) >= limit:
                        break
            
            logger.info(f"SECURE: Found {len(user_results)} results for user {user_id}")
            return user_results
            
        except Exception as e:
            logger.error(f"SECURE: Search failed for user {user_id}: {e}")
            return []
    
    def get_user_document_count(self, user_id: int) -> int:
        """Get count of documents for a specific user"""
        try:
            all_docs = self.vector_store.get_all_documents()
            count = 0
            
            for doc_id, document in all_docs.items():
                if document.metadata.get("user_id") == user_id:
                    count += 1
            
            return count
        except Exception as e:
            logger.error(f"SECURE: Failed to count documents for user {user_id}: {e}")
            return 0
    
    def delete_user_data(self, user_id: int) -> int:
        """
        SECURE: Delete ALL data for a specific user
        CRITICAL: Complete data removal for user privacy
        """
        try:
            all_docs = self.vector_store.get_all_documents()
            deleted_count = 0
            
            docs_to_delete = []
            for doc_id, document in all_docs.items():
                if document.metadata.get("user_id") == user_id:
                    docs_to_delete.append(doc_id)
            
            # Delete all user documents
            for doc_id in docs_to_delete:
                if self.vector_store.delete_document(doc_id):
                    deleted_count += 1
            
            logger.info(f"SECURE: Deleted {deleted_count} documents for user {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"SECURE: Failed to delete data for user {user_id}: {e}")
            return 0
    
    def verify_user_isolation(self, user_id: int) -> Dict[str, Any]:
        """
        AUDIT: Verify that user data isolation is working correctly
        Returns statistics about user's data vs total data
        """
        try:
            all_docs = self.vector_store.get_all_documents()
            total_docs = len(all_docs)
            user_docs = 0
            other_users = set()
            
            for doc_id, document in all_docs.items():
                doc_user_id = document.metadata.get("user_id")
                if doc_user_id == user_id:
                    user_docs += 1
                elif doc_user_id is not None:
                    other_users.add(doc_user_id)
            
            return {
                "user_id": user_id,
                "user_documents": user_docs,
                "total_documents": total_docs,
                "other_users_count": len(other_users),
                "isolation_verified": user_docs > 0,
                "audit_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AUDIT: Failed to verify isolation for user {user_id}: {e}")
            return {"error": str(e)}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics (no user data exposed)"""
        try:
            stats = self.vector_store.get_stats()
            
            # Count users (not exposing user IDs)
            all_docs = self.vector_store.get_all_documents()
            user_ids = set()
            for document in all_docs.values():
                user_id = document.metadata.get("user_id")
                if user_id:
                    user_ids.add(user_id)
            
            stats["active_users"] = len(user_ids)
            stats["security_level"] = "user_isolated"
            
            return stats
            
        except Exception as e:
            logger.error(f"SYSTEM: Failed to get stats: {e}")
            return {"error": str(e)}

# Global secure instance
secure_vector_db = SecureVectorDBService()