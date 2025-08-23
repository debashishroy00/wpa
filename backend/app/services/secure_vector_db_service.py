"""
EMERGENCY: Secure Vector Database Service
Replaces existing vector DB service with strict user isolation
CRITICAL SECURITY FIX - Deploy immediately to prevent data leakage
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from sqlalchemy.orm import Session

logger = structlog.get_logger()

class SecureVectorDBService:
    """
    SECURE vector database service with strict user isolation
    CRITICAL: Prevents cross-user data contamination
    """
    
    def __init__(self):
        # Initialize ChromaDB with in-memory storage (no file permissions needed)
        self.client = chromadb.Client()
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create separate collection for user data with strict isolation
        self.user_collection = self.client.get_or_create_collection(
            name="user_financial_data_secure",
            metadata={"description": "User financial data with strict isolation"}
        )
        
        # Shared knowledge base collection (no user data)
        self.knowledge_collection = self.client.get_or_create_collection(
            name="knowledge_base_secure", 
            metadata={"description": "Shared financial knowledge - no user data"}
        )
        
        logger.info("🔒 SecureVectorDBService initialized with strict user isolation")
    
    def search_user_context(self, user_id: int, query: str, n_results: int = 10) -> List[Dict]:
        """
        SECURE search that ONLY returns data for the specified user
        CRITICAL: Implements strict user_id filtering to prevent data leakage
        """
        try:
            logger.info(f"🔒 SECURE SEARCH - User {user_id}, Query: '{query}'")
            
            # SECURITY CHECK: Validate user_id
            if not isinstance(user_id, int) or user_id <= 0:
                logger.error(f"🚨 SECURITY VIOLATION: Invalid user_id {user_id}")
                return []
            
            # Search with STRICT user filtering
            results = self.user_collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"user_id": user_id}  # CRITICAL: Only return this user's data
            )
            
            # Additional security validation - verify ALL results belong to this user
            validated_results = []
            contamination_detected = False
            
            if results and results.get('documents'):
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    
                    # SECURITY CHECK: Verify user_id in metadata
                    if metadata.get('user_id') != user_id:
                        contamination_detected = True
                        logger.error(f"🚨 CONTAMINATION DETECTED: Document belongs to user {metadata.get('user_id')}, not {user_id}")
                        continue  # Skip contaminated result
                    
                    validated_results.append({
                        'content': doc,
                        'user_id': metadata.get('user_id'),
                        'category': metadata.get('category'),
                        'subcategory': metadata.get('subcategory'),
                        'timestamp': metadata.get('timestamp'),
                        'distance': results['distances'][0][i] if results.get('distances') else 1.0
                    })
            
            if contamination_detected:
                logger.error(f"🚨 SECURITY ALERT: Cross-user contamination detected for user {user_id}")
            
            logger.info(f"🔒 SECURE SEARCH COMPLETE - User {user_id}: {len(validated_results)} validated results")
            return validated_results
            
        except Exception as e:
            logger.error(f"🚨 SECURE SEARCH ERROR for user {user_id}: {str(e)}")
            return []
    
    def index_user_data(self, user_id: int, documents: List[str], metadatas: List[Dict]) -> bool:
        """
        SECURE indexing with user isolation
        CRITICAL: Ensures all documents are tagged with correct user_id
        """
        try:
            logger.info(f"🔒 SECURE INDEXING - User {user_id}: {len(documents)} documents")
            
            # SECURITY CHECK: Validate all metadata has correct user_id
            validated_metadatas = []
            for metadata in metadatas:
                if metadata.get('user_id') != user_id:
                    logger.error(f"🚨 SECURITY VIOLATION: Metadata user_id {metadata.get('user_id')} != {user_id}")
                    return False
                
                # Ensure required fields
                secure_metadata = {
                    'user_id': user_id,
                    'category': metadata.get('category', 'unknown'),
                    'subcategory': metadata.get('subcategory', 'unknown'),
                    'timestamp': metadata.get('timestamp', datetime.now().isoformat()),
                    'indexed_at': datetime.now().isoformat()
                }
                validated_metadatas.append(secure_metadata)
            
            # Generate secure document IDs with user prefix
            ids = [f"user_{user_id}_{hashlib.md5(doc.encode()).hexdigest()[:12]}" for doc in documents]
            
            # Index with security validation
            self.user_collection.add(
                documents=documents,
                metadatas=validated_metadatas,
                ids=ids
            )
            
            logger.info(f"🔒 SECURE INDEXING COMPLETE - User {user_id}: {len(documents)} documents indexed")
            return True
            
        except Exception as e:
            logger.error(f"🚨 SECURE INDEXING ERROR for user {user_id}: {str(e)}")
            return False
    
    def search_knowledge_base(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search shared knowledge base (no user data)
        SAFE: Contains only general financial knowledge
        """
        try:
            logger.info(f"🔍 KNOWLEDGE BASE SEARCH: '{query}'")
            
            results = self.knowledge_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            knowledge_results = []
            if results and results.get('documents'):
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    
                    knowledge_results.append({
                        'content': doc,
                        'category': metadata.get('category', 'knowledge'),
                        'source': metadata.get('source', 'knowledge_base'),
                        'distance': results['distances'][0][i] if results.get('distances') else 1.0
                    })
            
            logger.info(f"🔍 KNOWLEDGE SEARCH COMPLETE: {len(knowledge_results)} results")
            return knowledge_results
            
        except Exception as e:
            logger.error(f"🚨 KNOWLEDGE SEARCH ERROR: {str(e)}")
            return []
    
    def validate_user_isolation(self, user_id: int) -> Dict:
        """
        CRITICAL: Validate that user can only access their own data
        Returns security validation report
        """
        try:
            logger.info(f"🔒 VALIDATING USER ISOLATION for User {user_id}")
            
            # Test 1: Search for all data
            all_results = self.search_user_context(user_id, "", 1000)
            
            # Test 2: Check user_id consistency
            contamination_count = 0
            for result in all_results:
                if result.get('user_id') != user_id:
                    contamination_count += 1
            
            # Test 3: Try to search for other users' data
            other_user_search = self.user_collection.query(
                query_texts=["financial data"],
                n_results=1000,
                where={"user_id": {"$ne": user_id}}  # NOT this user
            )
            
            other_user_count = len(other_user_search.get('documents', [{}])[0]) if other_user_search else 0
            
            validation_report = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "total_user_documents": len(all_results),
                "contamination_count": contamination_count,
                "other_users_visible": other_user_count,
                "isolation_status": "SECURE" if contamination_count == 0 else "COMPROMISED",
                "privacy_violation": contamination_count > 0 or other_user_count > 0
            }
            
            if validation_report["privacy_violation"]:
                logger.error(f"🚨 PRIVACY VIOLATION DETECTED for User {user_id}: {validation_report}")
            else:
                logger.info(f"✅ USER ISOLATION VALIDATED for User {user_id}")
            
            return validation_report
            
        except Exception as e:
            logger.error(f"🚨 ISOLATION VALIDATION ERROR for user {user_id}: {str(e)}")
            return {"error": str(e), "isolation_status": "ERROR"}
    
    def emergency_purge_contaminated_data(self) -> Dict:
        """
        EMERGENCY: Remove all potentially contaminated data
        Use only if cross-user contamination is detected
        """
        try:
            logger.warning("🚨 EMERGENCY PURGE: Removing potentially contaminated data")
            
            # Get current document count
            before_count = self.user_collection.count()
            
            # Delete the contaminated collection
            self.client.delete_collection("user_financial_data_secure")
            
            # Recreate clean collection
            self.user_collection = self.client.get_or_create_collection(
                name="user_financial_data_secure",
                metadata={"description": "User financial data with strict isolation - CLEANED"}
            )
            
            after_count = self.user_collection.count()
            
            purge_report = {
                "action": "emergency_purge",
                "timestamp": datetime.now().isoformat(),
                "documents_removed": before_count,
                "documents_remaining": after_count,
                "status": "PURGED_CLEAN"
            }
            
            logger.warning(f"🚨 EMERGENCY PURGE COMPLETE: {purge_report}")
            return purge_report
            
        except Exception as e:
            logger.error(f"🚨 EMERGENCY PURGE FAILED: {str(e)}")
            return {"error": str(e), "status": "PURGE_FAILED"}
    
    def get_security_status(self) -> Dict:
        """
        Get overall security status of vector database
        """
        try:
            # Get collection stats
            user_docs = self.user_collection.count()
            knowledge_docs = self.knowledge_collection.count()
            
            # Check for any documents without user_id (security risk)
            all_user_data = self.user_collection.get()
            
            docs_without_user_id = 0
            if all_user_data and all_user_data.get('metadatas'):
                for metadata in all_user_data['metadatas']:
                    if not metadata.get('user_id'):
                        docs_without_user_id += 1
            
            security_status = {
                "timestamp": datetime.now().isoformat(),
                "user_documents": user_docs,
                "knowledge_documents": knowledge_docs,
                "docs_without_user_id": docs_without_user_id,
                "security_level": "HIGH" if docs_without_user_id == 0 else "COMPROMISED",
                "requires_attention": docs_without_user_id > 0
            }
            
            logger.info(f"🔒 SECURITY STATUS: {security_status}")
            return security_status
            
        except Exception as e:
            logger.error(f"🚨 SECURITY STATUS ERROR: {str(e)}")
            return {"error": str(e), "security_level": "UNKNOWN"}


# Global secure instance - REPLACES old vector service
secure_vector_service = SecureVectorDBService()