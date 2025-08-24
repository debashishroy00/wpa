"""
Vector Database API Endpoints
Handles indexing and searching of financial data embeddings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user
from app.api.v1.endpoints.financial_clean import get_comprehensive_summary
from app.services.vector_db_service import get_vector_db
import structlog

logger = structlog.get_logger()

router = APIRouter()

@router.post("/index/{user_id}")
async def index_user_data(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    🚨 CRITICAL: This endpoint is DISABLED due to destructive data loss pattern
    DANGEROUS: Deletes all user data before reindexing - caused loss of 41 documents
    USE: /safe-index/{user_id} instead
    """
    
    # 🚨 EMERGENCY DISABLE - PREVENTS DATA LOSS
    raise HTTPException(
        status_code=503,
        detail="🚨 ENDPOINT DISABLED: This endpoint uses destructive delete-then-rebuild pattern that caused data loss (48→7 documents). Use /safe-index/{user_id} instead for safe incremental indexing."
    )
    
    # 🚨 DANGEROUS CODE BELOW - DO NOT UNCOMMENT WITHOUT FIXING THE DESIGN
    # 
    # # Verify user access
    # if current_user.id != user_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Access denied"
    #     )
    # 
    # try:
    #     # Get comprehensive summary
    #     summary = await get_comprehensive_summary(user_id, db, current_user)
    #     
    #     # Get vector database instance
    #     vector_db = get_vector_db()
    #     
    #     # 🚨 DESTRUCTIVE OPERATION - DELETES ALL USER DATA:
    #     vector_db.clear_user_data(user_id)  # <-- THIS CAUSED THE DATA LOSS!
    #     
    #     # Index into vector database with profile data
    #     result = vector_db.index_comprehensive_summary_with_profile(user_id, summary, db)
    #     
    #     logger.info(f"Successfully indexed {result['documents_indexed']} documents for user {user_id}")
    #     
    #     return result
    #     
    # except Exception as e:
    #     logger.error(f"Failed to index user data: {str(e)}")
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"Failed to index financial data: {str(e)}"
    #     )

@router.post("/safe-index/{user_id}")
async def safe_index_user_data(
    user_id: int,
    incremental: bool = True,
    force_full_rebuild: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    🛡️ SAFE INDEXING: Preserves existing data with backup protection
    
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
        
        # Get vector database instance
        vector_db = get_vector_db()
        
        if incremental:
            # 🛡️ SAFE: Incremental indexing - only add new/changed documents
            logger.info(f"Starting SAFE incremental indexing for user {user_id}")
            
            # Get existing documents to avoid duplicates
            existing_docs = vector_db.collection.get(where={"user_id": user_id})
            existing_ids = set(existing_docs.get('ids', []))
            
            # Index new documents only
            result = vector_db.index_comprehensive_summary_with_profile_incremental(
                user_id, summary, db, existing_ids
            )
            
            logger.info(f"SAFE indexing complete: {result.get('documents_added', 0)} new documents added")
            
        elif force_full_rebuild:
            # 🛡️ SAFE: Full rebuild with backup protection
            logger.warning(f"Starting FULL REBUILD with backup for user {user_id}")
            
            # Step 1: Create backup
            backup_data = vector_db.collection.get(where={"user_id": user_id})
            backup_count = len(backup_data.get('ids', []))
            
            if backup_count == 0:
                logger.info(f"No existing data to backup for user {user_id}")
            else:
                logger.info(f"Created backup of {backup_count} documents for user {user_id}")
            
            try:
                # Step 2: Clear and rebuild
                if backup_count > 0:
                    vector_db.clear_user_data(user_id)
                
                # Step 3: Rebuild from fresh data
                result = vector_db.index_comprehensive_summary_with_profile(user_id, summary, db)
                
                new_count = result.get('documents_indexed', 0)
                
                # Step 4: Verify rebuild was successful
                if new_count == 0:
                    # 🚨 ROLLBACK: Restore from backup if rebuild failed
                    if backup_count > 0:
                        logger.error(f"Rebuild failed (0 documents), restoring backup of {backup_count} documents")
                        
                        vector_db.collection.add(
                            ids=backup_data['ids'],
                            documents=backup_data['documents'],
                            metadatas=backup_data['metadatas']
                        )
                        
                        return {
                            "status": "rollback_completed", 
                            "backup_restored": backup_count,
                            "error": "Rebuild failed, restored from backup"
                        }
                
                logger.info(f"FULL REBUILD complete: {new_count} documents indexed")
                result.update({"backup_count": backup_count, "rebuild_successful": True})
                
            except Exception as rebuild_error:
                # 🚨 EMERGENCY ROLLBACK
                if backup_count > 0:
                    logger.error(f"Rebuild failed with error: {rebuild_error}")
                    logger.info(f"Restoring backup of {backup_count} documents")
                    
                    try:
                        # Clear failed state
                        vector_db.clear_user_data(user_id)
                        
                        # Restore backup
                        vector_db.collection.add(
                            ids=backup_data['ids'],
                            documents=backup_data['documents'], 
                            metadatas=backup_data['metadatas']
                        )
                        
                        return {
                            "status": "emergency_rollback_completed",
                            "backup_restored": backup_count,
                            "original_error": str(rebuild_error)
                        }
                    except Exception as rollback_error:
                        logger.critical(f"CRITICAL: Both rebuild and rollback failed! Backup data exists but couldn't restore. Rebuild error: {rebuild_error}, Rollback error: {rollback_error}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"CRITICAL: Data restoration failed. Contact admin immediately. Backup exists but couldn't restore."
                        )
                raise rebuild_error
        
        else:
            return {
                "status": "no_action",
                "message": "Specify incremental=True for safe indexing or force_full_rebuild=True for full rebuild with backup"
            }
        
        return result
        
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
    Search for relevant financial context based on query
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Get vector database instance
        vector_db = get_vector_db()
        
        # Search for relevant context
        results = vector_db.search_context(user_id, query, n_results)
        
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
    Get formatted context for chat message
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Get vector database instance
        vector_db = get_vector_db()
        
        # Get formatted context
        context = vector_db.get_chat_context(user_id, message)
        
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
    Clear all vector data for a user (for reindexing)
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Get vector database instance
        vector_db = get_vector_db()
        
        # Clear user data
        result = vector_db.clear_user_data(user_id)
        
        logger.info(f"Cleared {result['deleted_count']} documents for user {user_id}")
        
        return result
        
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
    Get status of vector database for user
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Get vector database instance
        vector_db = get_vector_db()
        
        # Get all documents for this user
        user_docs = vector_db.collection.get(where={"user_id": user_id})
        
        # Count by category
        categories = {}
        for metadata in user_docs.get('metadatas', []):
            category = metadata.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "user_id": user_id,
            "total_documents": len(user_docs.get('ids', [])),
            "categories": categories,
            "is_indexed": len(user_docs.get('ids', [])) > 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get vector status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )

@router.get("/debug-status")
async def get_debug_vector_status():
    """
    Debug endpoint to check vector database status without authentication
    """
    try:
        vector_db = get_vector_db()
        user_docs = vector_db.collection.get(where={"user_id": 1})
        
        return {
            "total_documents": len(user_docs.get('ids', [])),
            "status": "operational",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Debug status failed: {str(e)}")
        return {
            "total_documents": 0,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }