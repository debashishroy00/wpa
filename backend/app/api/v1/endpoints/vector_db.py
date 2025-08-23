"""
Vector Database API Endpoints
Handles indexing and searching of financial data embeddings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

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
    Index user's comprehensive financial data into vector database
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
        
        # Clear existing data first
        vector_db.clear_user_data(user_id)
        
        # Index into vector database with profile data
        result = vector_db.index_comprehensive_summary_with_profile(user_id, summary, db)
        
        logger.info(f"Successfully indexed {result['documents_indexed']} documents for user {user_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to index user data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index financial data: {str(e)}"
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