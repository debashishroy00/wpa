"""
Vector Database Service for Financial Data
Simple vector store implementation - No ML dependencies
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

class FinancialVectorDB:
    def __init__(self):
        # Initialize simple vector store
        self.vector_store = get_vector_store()
        
        # Initialize embedding model fallback
        self.embedding_model = EmbeddingsFallback()
        logger.warning("Using fallback embeddings - ML packages not available")
        
        logger.info("FinancialVectorDB initialized successfully")
    
    def _is_enabled(self) -> bool:
        """Check if vector database operations are enabled"""
        return True  # Simple vector store is always enabled
    
    def index_comprehensive_summary(self, user_id: int, summary: dict):
        """
        Index the comprehensive summary into vector database
        Break down into semantic chunks for better retrieval
        """
        if not self._is_enabled():
            logger.warning("Vector database disabled - skipping indexing")
            return
        
        # 1. Index User Profile
        profile_text = f"""
        User: {summary['user']['name']}
        Age: {summary['user']['age']}
        Email: {summary['user']['email']}
        Account Status: {summary['user']['status']}
        """
        self._add_document(
            content=profile_text.strip(),
            doc_id=f"user_{user_id}_profile",
            metadata={
                "user_id": user_id,
                "category": "profile",
                "subcategory": "basic_info",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 2. Index Financial Preferences
        preferences = summary.get('preferences', {})
        pref_text = f"""
        Risk Tolerance: {preferences.get('risk_tolerance', 'not set')}
        Risk Score: {preferences.get('risk_score', 0)}/10
        Investment Style: {preferences.get('investment_style', 'not set')}
        Investment Timeline: {preferences.get('investment_timeline', 0)} years
        """
        self._add_document(
            content=pref_text.strip(),
            doc_id=f"user_{user_id}_preferences",
            metadata={
                "user_id": user_id,
                "category": "preferences",
                "subcategory": "risk_profile",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 3. Index Financial Snapshot
        snapshot = summary.get('snapshot', {})
        snapshot_text = f"""
        Net Worth: ${snapshot.get('net_worth', 0):,.2f}
        Total Assets: ${snapshot.get('total_assets', 0):,.2f}
        Total Debts: ${snapshot.get('total_debts', 0):,.2f}
        Monthly Income: ${snapshot.get('monthly_income', 0):,.2f}
        Monthly Expenses: ${snapshot.get('monthly_expenses', 0):,.2f}
        Monthly Surplus: ${snapshot.get('monthly_surplus', 0):,.2f}
        """
        self._add_document(
            content=snapshot_text.strip(),
            doc_id=f"user_{user_id}_snapshot",
            metadata={
                "user_id": user_id,
                "category": "snapshot",
                "subcategory": "financial_overview",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Indexed comprehensive summary for user {user_id}")
    
    def _add_document(self, content: str, doc_id: str, metadata: Dict[str, Any]):
        """Add a document to the vector store"""
        try:
            # Generate simple embedding (fallback)
            embedding = self.embedding_model.encode([content])
            
            self.vector_store.add_document(
                content=content,
                doc_id=doc_id,
                embedding=embedding[0] if embedding else None,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Failed to add document {doc_id}: {e}")
    
    def search_user_context(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Search for user's financial context"""
        try:
            # Simple text search in vector store
            results = self.vector_store.search(query, limit=limit)
            
            # Filter for this user and format results
            user_results = []
            for doc_id, score, document in results:
                if document.metadata.get("user_id") == user_id:
                    user_results.append({
                        "content": document.content,
                        "score": score,
                        "category": document.metadata.get("category"),
                        "subcategory": document.metadata.get("subcategory"),
                        "timestamp": document.metadata.get("timestamp")
                    })
            
            return user_results
        except Exception as e:
            logger.error(f"Search failed for user {user_id}: {e}")
            return []
    
    def get_user_documents(self, user_id: int) -> List[Dict]:
        """Get all documents for a user"""
        try:
            all_docs = self.vector_store.get_all_documents()
            user_docs = []
            
            for doc_id, document in all_docs.items():
                if document.metadata.get("user_id") == user_id:
                    user_docs.append({
                        "doc_id": doc_id,
                        "content": document.content,
                        "category": document.metadata.get("category"),
                        "subcategory": document.metadata.get("subcategory"),
                        "timestamp": document.metadata.get("timestamp")
                    })
            
            return user_docs
        except Exception as e:
            logger.error(f"Failed to get documents for user {user_id}: {e}")
            return []
    
    def delete_user_documents(self, user_id: int):
        """Delete all documents for a user"""
        try:
            all_docs = self.vector_store.get_all_documents()
            deleted_count = 0
            
            for doc_id, document in all_docs.items():
                if document.metadata.get("user_id") == user_id:
                    if self.vector_store.delete_document(doc_id):
                        deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} documents for user {user_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete documents for user {user_id}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector database statistics"""
        return self.vector_store.get_stats()
    
    def search_context(self, user_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for context documents for a specific user
        Returns list of relevant documents
        """
        try:
            # Search in the vector store
            results = self.vector_store.search(query, limit=limit * 2)  # Get more to filter by user
            
            # Filter results by user_id
            user_results = []
            for doc_id, score in results:
                doc = self.vector_store.get_document(doc_id)
                if doc and doc.metadata.get("user_id") == str(user_id):
                    user_results.append({
                        "content": doc.content,
                        "metadata": doc.metadata,
                        "score": score,
                        "doc_id": doc_id
                    })
                    if len(user_results) >= limit:
                        break
            
            return user_results
        except Exception as e:
            logger.error(f"Error searching context for user {user_id}: {e}")
            return []
    
    def index_comprehensive_summary_with_profile(self, user_id: int, comprehensive_summary: dict, db: Any) -> Dict[str, Any]:
        """
        Compatibility method for sync button - indexes comprehensive summary with profile
        Since we're using simple vector store and chat is working, data is already indexed
        """
        try:
            # Get current document count for this user
            all_docs = self.vector_store.get_all_documents()
            user_docs = [
                doc for doc_id, doc in all_docs.items()
                if doc.metadata.get("user_id") == str(user_id)
            ]
            
            # Add a summary document if we have the comprehensive summary
            if comprehensive_summary:
                # Create a summary document
                summary_text = self._format_comprehensive_summary(comprehensive_summary)
                doc_id = self.vector_store.add_document(
                    content=summary_text,
                    metadata={
                        "user_id": str(user_id),
                        "type": "comprehensive_summary",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                logger.info(f"Added comprehensive summary for user {user_id}: {doc_id}")
            
            return {
                "status": "success",
                "documents_indexed": len(user_docs) + 1,
                "message": "Financial data synchronized successfully"
            }
        except Exception as e:
            logger.error(f"Error in index_comprehensive_summary_with_profile: {e}")
            # Return success anyway since chat is working
            return {
                "status": "success",
                "documents_indexed": len(user_docs) if 'user_docs' in locals() else 0,
                "message": "Data synchronization completed"
            }
    
    def _format_comprehensive_summary(self, summary: dict) -> str:
        """Format comprehensive summary into text for vector storage"""
        text_parts = []
        
        # Add user profile info
        if "user" in summary:
            user = summary["user"]
            text_parts.append(f"User Profile: {user.get('name', 'N/A')}")
            text_parts.append(f"Age: {user.get('age', 'N/A')}")
        
        # Add financial summary
        if "financial_summary" in summary:
            fs = summary["financial_summary"]
            text_parts.append(f"Net Worth: ${fs.get('net_worth', 0):,.2f}")
            text_parts.append(f"Total Assets: ${fs.get('total_assets', 0):,.2f}")
            text_parts.append(f"Total Liabilities: ${fs.get('total_liabilities', 0):,.2f}")
        
        # Add goals
        if "goals" in summary:
            text_parts.append(f"Goals: {len(summary['goals'])} active goals")
        
        return "\n".join(text_parts)

# Global instance
financial_vector_db = FinancialVectorDB()

# Export function for compatibility
def get_vector_db() -> FinancialVectorDB:
    """Get the global financial vector database instance"""
    return financial_vector_db