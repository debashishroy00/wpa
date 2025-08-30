"""
WealthPath AI - Debug Endpoints
Direct visibility into vector database contents and LLM payloads
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict, List
import json
from datetime import datetime
import structlog

from app.db.session import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user
from app.services.vector_db_service import get_vector_db

logger = structlog.get_logger()

router = APIRouter()

# Store last LLM payload in memory for debugging
_last_llm_payloads = {}

def store_llm_payload(user_id: int, payload: Dict):
    """Store the last LLM payload for debugging"""
    _last_llm_payloads[user_id] = {
        **payload,
        "timestamp": datetime.utcnow().isoformat(),
        "stored_at": datetime.utcnow()
    }

def get_stored_llm_payload(user_id: int) -> Dict:
    """Get the last stored LLM payload"""
    return _last_llm_payloads.get(user_id)

@router.get("/vector-contents/{user_id}")
async def get_vector_contents(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get ALL vector database contents for a specific user.
    Shows exactly what documents are stored and their content.
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Use simple vector store instead of ChromaDB
        from app.services.simple_vector_store import get_vector_store
        import os
        
        vector_store = get_vector_store()
        
        # Check if storage file exists
        storage_exists = os.path.exists(vector_store.storage_path)
        
        # Get all documents for this user
        documents = []
        for doc_id, doc in vector_store.documents.items():
            if doc.metadata.get("user_id") == str(user_id):
                documents.append({
                    "id": doc.doc_id,
                    "content": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                    "metadata": doc.metadata,
                    "doc_type": doc.metadata.get("type", "unknown"),
                    "category": doc.metadata.get("category", "unknown"),
                    "created_at": getattr(doc, 'created_at', None)
                })
        
        # Get vector store stats
        stats = vector_store.get_stats()
        
        return {
            "status": "success",
            "user_id": user_id,
            "total_documents": len(documents),
            "last_updated": datetime.utcnow().isoformat(),
            "documents": documents,
            "debug_info": {
                "storage_type": "SimpleVectorStore",
                "storage_path": vector_store.storage_path,
                "storage_file_exists": storage_exists,
                "user_filter": {"user_id": str(user_id)},
                "vector_store_stats": stats,
                "total_docs_in_store": len(vector_store.documents)
            }
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting vector contents for user {user_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vector contents: {str(e)}"
        )

@router.get("/last-llm-payload/{user_id}")
async def get_last_llm_payload(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get the last LLM payload sent for this user.
    Shows exactly what system prompt, user message, and context was sent.
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        payload = get_stored_llm_payload(user_id)
        
        if not payload:
            return {
                "status": "no_data",
                "user_id": user_id,
                "message": "No LLM payload stored yet. Send a chat message first.",
                "last_check": datetime.utcnow().isoformat()
            }
        
        # Calculate sizes and analyze content
        system_prompt = payload.get("system_prompt", "")
        user_message = payload.get("user_message", "")
        
        analysis = {
            "has_goals": "goal" in system_prompt.lower() or "retirement" in system_prompt.lower(),
            "has_dti": "debt-to-income" in system_prompt.lower() or "dti" in system_prompt.lower(),
            "has_interest_rates": "22.99%" in system_prompt or "19.99%" in system_prompt,
            "system_prompt_size": len(system_prompt),
            "user_message_size": len(user_message),
            "total_size": len(system_prompt) + len(user_message)
        }
        
        # Extract DTI value if present
        import re
        dti_match = re.search(r'debt-to-income ratio:?\s*(\d+\.?\d*)%', system_prompt.lower())
        if dti_match:
            analysis["dti_value"] = dti_match.group(1) + "%"
        
        return {
            "status": "success",
            "user_id": user_id,
            "query": payload.get("query", ""),
            "timestamp": payload.get("timestamp", ""),
            "provider": payload.get("provider", ""),
            "system_prompt": system_prompt,
            "user_message": user_message,
            "context_used": payload.get("context_used", ""),
            "analysis": analysis,
            "raw_payload": payload
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error getting LLM payload for user {user_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get LLM payload: {str(e)}"
        )

@router.post("/clear-payloads")
async def clear_stored_payloads(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Clear all stored LLM payloads for debugging"""
    
    try:
        _last_llm_payloads.clear()
        return {
            "status": "success",
            "message": "All stored LLM payloads cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear payloads: {str(e)}"
        )

@router.post("/trigger-vector-sync/{user_id}")
async def trigger_vector_sync(
    user_id: int,
    force_rebuild: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Debug endpoint to trigger vector database sync for a specific user
    This will sync all 10 document types from PostgreSQL to vector store
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        from app.services.vector_sync_service import VectorSyncService
        import os
        
        # Initialize sync service (doesn't take db parameter)
        sync_service = VectorSyncService()
        
        logger.info(f"Starting vector sync for user {user_id}, force_rebuild={force_rebuild}")
        
        # Get vector store info before sync
        from app.services.simple_vector_store import get_vector_store
        vector_store = get_vector_store()
        pre_sync_stats = {
            "storage_exists": os.path.exists(vector_store.storage_path),
            "total_docs": len(vector_store.documents),
            "user_docs": len([d for d in vector_store.documents.values() 
                            if d.metadata.get("user_id") == str(user_id)])
        }
        
        # Perform sync
        if force_rebuild:
            logger.info(f"Force rebuilding vector data for user {user_id}")
            sync_service._clear_user_vector_data(user_id)
        
        sync_result = sync_service.sync_user_data(user_id)
        
        # Get vector store info after sync
        post_sync_stats = {
            "storage_exists": os.path.exists(vector_store.storage_path),
            "total_docs": len(vector_store.documents),
            "user_docs": len([d for d in vector_store.documents.values() 
                            if d.metadata.get("user_id") == str(user_id)])
        }
        
        return {
            "status": "success",
            "user_id": user_id,
            "force_rebuild": force_rebuild,
            "sync_result": sync_result,
            "pre_sync_stats": pre_sync_stats,
            "post_sync_stats": post_sync_stats,
            "documents_added": post_sync_stats["user_docs"] - pre_sync_stats["user_docs"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Vector sync failed for user {user_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector sync failed: {str(e)}"
        )