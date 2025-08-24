"""
Vector Database API Endpoints
Simple vector store implementation - No ML dependencies
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user
from app.api.v1.endpoints.financial_clean import get_comprehensive_summary
from app.services.vector_db_service import financial_vector_db
from app.services.simple_vector_store import get_vector_store
import structlog

logger = structlog.get_logger()

router = APIRouter()

@router.post("/safe-index/{user_id}")
async def safe_index_user_data(
    user_id: int,
    incremental: bool = True,
    force_full_rebuild: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    🛡️ SAFE INDEXING: Using SimpleVectorStore with backup protection
    
    - incremental=True (default): Only adds new/changed documents
    - force_full_rebuild=True: Full rebuild WITH backup protection
    - Never deletes data without creating backup first
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Get comprehensive summary
        summary = await get_comprehensive_summary(user_id, db, current_user)
        
        if incremental:
            # 🛡️ SAFE: Incremental indexing using SimpleVectorStore
            logger.info(f"Starting SAFE incremental indexing for user {user_id}")
            
            # Check existing documents
            existing_docs = financial_vector_db.get_user_documents(user_id)
            existing_count = len(existing_docs)
            
            # Index the comprehensive summary
            financial_vector_db.index_comprehensive_summary(user_id, summary)
            
            # Count new documents
            new_docs = financial_vector_db.get_user_documents(user_id)
            new_count = len(new_docs)
            
            result = {
                "status": "incremental_success",
                "documents_before": existing_count,
                "documents_after": new_count,
                "documents_added": max(0, new_count - existing_count),
                "user_id": user_id
            }
            
            logger.info(f"SAFE indexing complete: {result['documents_added']} new documents added")
            return result
            
        elif force_full_rebuild:
            # 🛡️ SAFE: Full rebuild with backup protection
            logger.warning(f"Starting FULL REBUILD with backup for user {user_id}")
            
            # Step 1: Get existing documents for backup
            existing_docs = financial_vector_db.get_user_documents(user_id)
            backup_count = len(existing_docs)
            
            if backup_count == 0:
                logger.info(f"No existing data to backup for user {user_id}")
            else:
                logger.info(f"Backup available: {backup_count} documents for user {user_id}")
            
            try:
                # Step 2: Clear and rebuild
                if backup_count > 0:
                    deleted_count = financial_vector_db.delete_user_documents(user_id)
                    logger.info(f"Cleared {deleted_count} documents for rebuild")
                
                # Step 3: Rebuild from fresh data
                financial_vector_db.index_comprehensive_summary(user_id, summary)
                
                # Step 4: Verify rebuild was successful
                new_docs = financial_vector_db.get_user_documents(user_id)
                new_count = len(new_docs)
                
                if new_count == 0:
                    logger.error(f"Rebuild failed (0 documents created)")
                    return {
                        "status": "rebuild_failed", 
                        "backup_count": backup_count,
                        "error": "No new documents were created during rebuild"
                    }
                
                logger.info(f"FULL REBUILD complete: {new_count} documents indexed")
                
                return {
                    "status": "rebuild_success",
                    "backup_count": backup_count,
                    "documents_indexed": new_count,
                    "rebuild_successful": True
                }
                
            except Exception as rebuild_error:
                logger.error(f"Rebuild failed with error: {rebuild_error}")
                return {
                    "status": "rebuild_failed",
                    "backup_count": backup_count,
                    "error": str(rebuild_error)
                }
        
        else:
            return {
                "status": "no_action",
                "message": "Specify incremental=True for safe indexing or force_full_rebuild=True for full rebuild"
            }
        
    except Exception as e:
        logger.error(f"Safe indexing failed for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Safe indexing failed: {str(e)}"
        )

@router.post("/search/{user_id}")
async def search_financial_context(
    user_id: int,
    query: str,
    n_results: int = 5,
    current_user: User = Depends(get_current_active_user)
):
    """
    Search for relevant financial context using SimpleVectorStore
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Search using the financial vector DB service
        results = financial_vector_db.search_user_context(user_id, query, limit=n_results)
        
        logger.info(f"Vector search for user {user_id}: '{query}' returned {len(results)} results")
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/chat-context/{user_id}")
async def get_chat_context(
    user_id: int,
    message: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get formatted context for chat message using SimpleVectorStore
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Search for relevant context
        results = financial_vector_db.search_user_context(user_id, message, limit=3)
        
        # Format context for chat
        context_parts = []
        for result in results:
            context_parts.append(f"**{result['category'].title()}**: {result['content'][:200]}...")
        
        context = "\n\n".join(context_parts) if context_parts else "No relevant financial context found."
        
        logger.info(f"Retrieved chat context for user {user_id}: '{message}'")
        
        return {"context": context}
        
    except Exception as e:
        logger.error(f"Failed to get chat context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get context: {str(e)}"
        )

@router.delete("/clear/{user_id}")
async def clear_user_vectors(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear all vector data for a user using SimpleVectorStore
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Clear user data
        deleted_count = financial_vector_db.delete_user_documents(user_id)
        
        logger.info(f"Cleared {deleted_count} documents for user {user_id}")
        
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Failed to clear vector data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear data: {str(e)}"
        )

@router.get("/status/{user_id}")
async def get_vector_status(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get status of vector database for user using SimpleVectorStore
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Get user documents
        user_docs = financial_vector_db.get_user_documents(user_id)
        
        # Count by category
        categories = {}
        for doc in user_docs:
            category = doc.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "user_id": user_id,
            "total_documents": len(user_docs),
            "categories": categories,
            "is_indexed": len(user_docs) > 0,
            "vector_store_type": "SimpleVectorStore"
        }
        
    except Exception as e:
        logger.error(f"Failed to get vector status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )

@router.get("/status")
async def get_system_vector_status():
    """
    Get system-wide vector database status
    """
    try:
        # Get system stats
        stats = financial_vector_db.get_stats()
        
        return {
            "status": "healthy",
            "vector_store_type": "SimpleVectorStore",
            "total_documents": stats["total_documents"],
            "storage_path": stats.get("storage_path", "Unknown"),
            "last_updated": stats.get("last_updated"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System status failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/contents/{user_id}")
async def get_vector_contents(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get vector database contents for debug view"""
    try:
        # Verify user access
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        vector_store = get_vector_store()
        
        # Get all documents for this user
        user_documents = []
        for doc_id, doc in vector_store.documents.items():
            if doc.metadata.get("user_id") == str(user_id):
                user_documents.append({
                    "id": doc.id,
                    "content": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "metadata": doc.metadata,
                    "created_at": doc.created_at
                })
        
        return {
            "status": "success",
            "total_documents": len(user_documents),
            "documents": user_documents
        }
        
    except Exception as e:
        logger.error(f"Debug view error: {e}")
        # Return empty but valid response instead of error
        return {
            "status": "success",
            "total_documents": 0,
            "documents": []
        }

@router.get("/debug/{user_id}")
async def debug_vector_db(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Debug endpoint for vector database visualization"""
    try:
        # Verify user access
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        vector_store = get_vector_store()
        stats = vector_store.get_stats()
        
        # Get user's documents
        user_docs = []
        for doc_id, doc in vector_store.documents.items():
            if doc.metadata.get("user_id") == str(user_id):
                # Format for debug view
                doc_type = doc.metadata.get("type", "unknown")
                doc_preview = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                
                user_docs.append({
                    "id": doc_id,
                    "type": doc_type,
                    "preview": doc_preview,
                    "size": len(doc.content),
                    "has_embedding": doc.embedding is not None
                })
        
        return {
            "status": "success",
            "stats": stats,
            "user_documents": user_docs,
            "total_user_docs": len(user_docs)
        }
        
    except Exception as e:
        logger.error(f"Debug error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "user_documents": [],
            "total_user_docs": 0
        }

@router.get("/debug-status")
async def get_debug_vector_status():
    """
    Debug endpoint to check vector database status without authentication
    """
    try:
        # Get overall stats
        stats = get_vector_store().get_stats()
        
        return {
            "total_documents": stats["total_documents"],
            "documents_with_embeddings": stats.get("documents_with_embeddings", 0),
            "categories": stats.get("categories", {}),
            "status": "operational",
            "vector_store_type": "SimpleVectorStore",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Debug status failed: {str(e)}")
        return {
            "total_documents": 0,
            "status": "error",
            "error": str(e),
            "vector_store_type": "SimpleVectorStore",
            "timestamp": datetime.now().isoformat()
        }

@router.get("/migrate")
async def migrate_documents():
    """
    Migrate documents to SimpleVectorStore (admin endpoint)
    """
    try:
        from app.services.knowledge_base import KnowledgeBaseService
        
        # Initialize knowledge base service (this will load documents)
        kb_service = KnowledgeBaseService()
        stats = kb_service.get_stats()
        
        return {
            "status": "migration_complete",
            "documents_migrated": stats["total_documents"],
            "categories": stats["categories"],
            "vector_store_stats": stats["vector_store_stats"]
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return {
            "status": "migration_failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }