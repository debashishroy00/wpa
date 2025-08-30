"""
Estate Planning API Endpoints for WealthPath AI
CRUD operations for estate planning documents
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal
from datetime import date, timedelta
import logging
import structlog

from app.db.session import get_db
from app.models.user import User
from app.models.estate_planning import UserEstatePlanning, DocumentType, DocumentStatus
from app.schemas.estate_planning import (
    EstatePlanningDocumentCreate, 
    EstatePlanningDocumentUpdate, 
    EstatePlanningDocumentResponse,
    EstatePlanningSummary,
    EstatePlanningGapAnalysis
)
from app.api.v1.endpoints.auth import get_current_active_user

logger = structlog.get_logger()
router = APIRouter()


@router.get("/documents", response_model=List[EstatePlanningDocumentResponse])
async def get_estate_planning_documents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[EstatePlanningDocumentResponse]:
    """Get all estate planning documents for the current user"""
    try:
        documents = db.query(UserEstatePlanning).filter(
            UserEstatePlanning.user_id == current_user.id
        ).order_by(UserEstatePlanning.document_type, UserEstatePlanning.document_name).all()
        
        return [EstatePlanningDocumentResponse.model_validate(doc.to_dict()) for doc in documents]
        
    except Exception as e:
        logger.error(f"Failed to fetch estate planning documents for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch estate planning documents"
        )


@router.get("/summary", response_model=EstatePlanningSummary)
async def get_estate_planning_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> EstatePlanningSummary:
    """Get estate planning summary with gap analysis"""
    try:
        documents = db.query(UserEstatePlanning).filter(
            UserEstatePlanning.user_id == current_user.id
        ).all()
        
        # Group by status
        documents_by_status = {}
        for doc in documents:
            status_key = doc.status
            if status_key not in documents_by_status:
                documents_by_status[status_key] = {
                    "count": 0,
                    "documents": []
                }
            documents_by_status[status_key]["count"] += 1
            documents_by_status[status_key]["documents"].append({
                "id": str(doc.id),
                "name": doc.document_name,
                "type": doc.document_type
            })
        
        # Group by type
        documents_by_type = {}
        for doc in documents:
            type_key = doc.document_type
            if type_key not in documents_by_type:
                documents_by_type[type_key] = {
                    "count": 0,
                    "documents": []
                }
            documents_by_type[type_key]["count"] += 1
            documents_by_type[type_key]["documents"].append({
                "id": str(doc.id),
                "name": doc.document_name,
                "status": doc.status
            })
        
        # Find documents needing review soon (within 90 days)
        upcoming_reviews = []
        today = date.today()
        for doc in documents:
            if doc.next_review_date and doc.next_review_date <= today + timedelta(days=90):
                upcoming_reviews.append(doc)
        
        # Identify gaps
        gaps_identified = []
        existing_types = {doc.document_type for doc in documents}
        essential_types = {
            DocumentType.WILL.value,
            DocumentType.POWER_OF_ATTORNEY.value,
            DocumentType.HEALTHCARE_DIRECTIVE.value
        }
        
        for essential_type in essential_types:
            if essential_type not in existing_types:
                gaps_identified.append(f"Missing {essential_type.replace('_', ' ').title()}")
        
        # Check for outdated documents
        current_docs = [doc for doc in documents if doc.status == DocumentStatus.CURRENT.value]
        if len(current_docs) < len(documents):
            gaps_identified.append("Some documents need updates")
        
        return EstatePlanningSummary(
            total_documents=len(documents),
            documents_by_status=documents_by_status,
            documents_by_type=documents_by_type,
            documents=[EstatePlanningDocumentResponse.model_validate(doc.to_dict()) for doc in documents],
            upcoming_reviews=[EstatePlanningDocumentResponse.model_validate(doc.to_dict()) for doc in upcoming_reviews],
            gaps_identified=gaps_identified
        )
        
    except Exception as e:
        logger.error(f"Failed to generate estate planning summary for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate estate planning summary"
        )


@router.get("/documents/{document_id}", response_model=EstatePlanningDocumentResponse)
async def get_estate_planning_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> EstatePlanningDocumentResponse:
    """Get a specific estate planning document by ID"""
    try:
        document = db.query(UserEstatePlanning).filter(
            UserEstatePlanning.id == document_id,
            UserEstatePlanning.user_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estate planning document not found"
            )
        
        return EstatePlanningDocumentResponse.model_validate(document.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch estate planning document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch estate planning document"
        )


@router.post("/documents", response_model=EstatePlanningDocumentResponse)
async def create_estate_planning_document(
    document_data: EstatePlanningDocumentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> EstatePlanningDocumentResponse:
    """Create a new estate planning document"""
    try:
        # Create new document
        new_document = UserEstatePlanning(
            user_id=current_user.id,
            document_type=document_data.document_type.value,
            document_name=document_data.document_name,
            status=document_data.status.value,
            last_updated=document_data.last_updated,
            next_review_date=document_data.next_review_date,
            attorney_contact=document_data.attorney_contact,
            document_location=document_data.document_location,
            document_details=document_data.document_details
        )
        
        db.add(new_document)
        db.commit()
        db.refresh(new_document)
        
        logger.info(f"Created estate planning document {new_document.id} for user {current_user.id}")
        
        return EstatePlanningDocumentResponse.model_validate(new_document.to_dict())
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create estate planning document for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create estate planning document"
        )


@router.put("/documents/{document_id}", response_model=EstatePlanningDocumentResponse)
async def update_estate_planning_document(
    document_id: str,
    document_data: EstatePlanningDocumentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> EstatePlanningDocumentResponse:
    """Update an existing estate planning document"""
    try:
        # Find existing document
        document = db.query(UserEstatePlanning).filter(
            UserEstatePlanning.id == document_id,
            UserEstatePlanning.user_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estate planning document not found"
            )
        
        # Update fields
        update_data = document_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(document, field):
                setattr(document, field, value)
        
        db.commit()
        db.refresh(document)
        
        logger.info(f"Updated estate planning document {document_id} for user {current_user.id}")
        
        return EstatePlanningDocumentResponse.model_validate(document.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update estate planning document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update estate planning document"
        )


@router.delete("/documents/{document_id}")
async def delete_estate_planning_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Delete an estate planning document"""
    try:
        # Find existing document
        document = db.query(UserEstatePlanning).filter(
            UserEstatePlanning.id == document_id,
            UserEstatePlanning.user_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estate planning document not found"
            )
        
        db.delete(document)
        db.commit()
        
        logger.info(f"Deleted estate planning document {document_id} for user {current_user.id}")
        
        return {"message": "Estate planning document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete estate planning document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete estate planning document"
        )


@router.get("/document-types", response_model=None)
async def get_document_types() -> Dict[str, Any]:
    """Get available estate planning document types with descriptions"""
    return {
        "document_types": [
            {"value": "will", "label": "Will", "description": "Last will and testament document"},
            {"value": "trust", "label": "Trust", "description": "Revocable or irrevocable trust documents"},
            {"value": "power_of_attorney", "label": "Power of Attorney", "description": "Financial and healthcare power of attorney"},
            {"value": "healthcare_directive", "label": "Healthcare Directive", "description": "Living will and healthcare proxy"},
            {"value": "beneficiary_designation", "label": "Beneficiary Designations", "description": "Account and policy beneficiary forms"}
        ],
        "statuses": [
            {"value": "current", "label": "Current", "description": "Document is up-to-date"},
            {"value": "needs_update", "label": "Needs Update", "description": "Document requires revision"},
            {"value": "missing", "label": "Missing", "description": "Document does not exist"},
            {"value": "in_progress", "label": "In Progress", "description": "Document is being prepared"}
        ]
    }


@router.get("/gap-analysis", response_model=EstatePlanningGapAnalysis)
async def get_estate_planning_gap_analysis(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> EstatePlanningGapAnalysis:
    """Get comprehensive estate planning gap analysis"""
    try:
        documents = db.query(UserEstatePlanning).filter(
            UserEstatePlanning.user_id == current_user.id
        ).all()
        
        existing_types = {doc.document_type for doc in documents}
        missing_documents = []
        outdated_documents = []
        upcoming_reviews = []
        
        # Check for missing essential documents
        essential_documents = {
            "will": "Last Will and Testament",
            "power_of_attorney": "Power of Attorney",
            "healthcare_directive": "Healthcare Directive"
        }
        
        for doc_type, doc_name in essential_documents.items():
            if doc_type not in existing_types:
                missing_documents.append(doc_name)
        
        # Check for outdated documents
        for doc in documents:
            if doc.status in [DocumentStatus.NEEDS_UPDATE.value, DocumentStatus.MISSING.value]:
                outdated_documents.append(doc.document_name)
        
        # Check for upcoming reviews
        today = date.today()
        for doc in documents:
            if doc.next_review_date and doc.next_review_date <= today + timedelta(days=90):
                upcoming_reviews.append(doc.document_name)
        
        # Generate recommendations
        recommendations = []
        priority_actions = []
        
        if missing_documents:
            recommendations.append("Consider creating missing essential estate planning documents")
            priority_actions.extend([f"Create {doc}" for doc in missing_documents])
        
        if outdated_documents:
            recommendations.append("Update outdated estate planning documents")
            priority_actions.extend([f"Review and update {doc}" for doc in outdated_documents])
        
        if upcoming_reviews:
            recommendations.append("Schedule reviews for documents due for updates")
        
        if not missing_documents and not outdated_documents:
            recommendations.append("Your estate planning appears to be well-maintained")
        
        return EstatePlanningGapAnalysis(
            missing_documents=missing_documents,
            outdated_documents=outdated_documents,
            upcoming_reviews=upcoming_reviews,
            recommendations=recommendations,
            priority_actions=priority_actions
        )
        
    except Exception as e:
        logger.error(f"Failed to generate gap analysis for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate estate planning gap analysis"
        )