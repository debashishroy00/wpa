"""
Insurance API Endpoints for WealthPath AI
CRUD operations for insurance policies
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal
import logging
import structlog

from app.db.session import get_db
from app.models.user import User
from app.models.insurance import UserInsurancePolicy, PolicyType
from app.schemas.insurance import (
    InsurancePolicyCreate, 
    InsurancePolicyUpdate, 
    InsurancePolicyResponse,
    InsurancePoliciesSummary
)
from app.api.v1.endpoints.auth import get_current_active_user

logger = structlog.get_logger()
router = APIRouter()


@router.get("/policies", response_model=List[InsurancePolicyResponse])
async def get_user_insurance_policies(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[InsurancePolicyResponse]:
    """Get all insurance policies for the current user"""
    try:
        policies = db.query(UserInsurancePolicy).filter(
            UserInsurancePolicy.user_id == current_user.id
        ).order_by(UserInsurancePolicy.policy_type, UserInsurancePolicy.policy_name).all()
        
        return [InsurancePolicyResponse.model_validate(policy.to_dict()) for policy in policies]
        
    except Exception as e:
        logger.error(f"Failed to fetch insurance policies for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch insurance policies"
        )


@router.get("/policies/summary", response_model=InsurancePoliciesSummary)
async def get_insurance_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> InsurancePoliciesSummary:
    """Get insurance policies summary with totals by type"""
    try:
        policies = db.query(UserInsurancePolicy).filter(
            UserInsurancePolicy.user_id == current_user.id
        ).all()
        
        total_annual_premiums = Decimal('0')
        coverage_by_type = {}
        
        for policy in policies:
            policy_type = policy.policy_type
            
            # Initialize policy type summary if not exists
            if policy_type not in coverage_by_type:
                coverage_by_type[policy_type] = {
                    "count": 0,
                    "total_coverage": Decimal('0'),
                    "total_premiums": Decimal('0'),
                    "policies": []
                }
            
            # Add to totals
            if policy.coverage_amount:
                coverage_by_type[policy_type]["total_coverage"] += policy.coverage_amount
            if policy.annual_premium:
                coverage_by_type[policy_type]["total_premiums"] += policy.annual_premium
                total_annual_premiums += policy.annual_premium
            
            coverage_by_type[policy_type]["count"] += 1
            coverage_by_type[policy_type]["policies"].append({
                "id": str(policy.id),
                "name": policy.policy_name,
                "coverage": float(policy.coverage_amount) if policy.coverage_amount else 0,
                "premium": float(policy.annual_premium) if policy.annual_premium else 0
            })
        
        # Convert Decimal to float for JSON serialization
        coverage_by_type_serialized = {}
        for policy_type, data in coverage_by_type.items():
            coverage_by_type_serialized[policy_type] = {
                "count": data["count"],
                "total_coverage": float(data["total_coverage"]),
                "total_premiums": float(data["total_premiums"]),
                "policies": data["policies"]
            }
        
        return InsurancePoliciesSummary(
            total_policies=len(policies),
            total_annual_premiums=total_annual_premiums,
            coverage_by_type=coverage_by_type_serialized,
            policies=[InsurancePolicyResponse.model_validate(policy.to_dict()) for policy in policies]
        )
        
    except Exception as e:
        logger.error(f"Failed to generate insurance summary for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate insurance summary"
        )


@router.get("/policies/{policy_id}", response_model=InsurancePolicyResponse)
async def get_insurance_policy(
    policy_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> InsurancePolicyResponse:
    """Get a specific insurance policy by ID"""
    try:
        policy = db.query(UserInsurancePolicy).filter(
            UserInsurancePolicy.id == policy_id,
            UserInsurancePolicy.user_id == current_user.id
        ).first()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance policy not found"
            )
        
        return InsurancePolicyResponse.model_validate(policy.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch insurance policy {policy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch insurance policy"
        )


@router.post("/policies", response_model=InsurancePolicyResponse)
async def create_insurance_policy(
    policy_data: InsurancePolicyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> InsurancePolicyResponse:
    """Create a new insurance policy"""
    try:
        # Create new policy
        new_policy = UserInsurancePolicy(
            user_id=current_user.id,
            policy_type=policy_data.policy_type.value,
            policy_name=policy_data.policy_name,
            coverage_amount=policy_data.coverage_amount,
            annual_premium=policy_data.annual_premium,
            beneficiary_primary=policy_data.beneficiary_primary,
            beneficiary_secondary=policy_data.beneficiary_secondary,
            policy_details=policy_data.policy_details
        )
        
        db.add(new_policy)
        db.commit()
        db.refresh(new_policy)
        
        logger.info(f"Created insurance policy {new_policy.id} for user {current_user.id}")
        
        return InsurancePolicyResponse.model_validate(new_policy.to_dict())
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create insurance policy for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create insurance policy"
        )


@router.put("/policies/{policy_id}", response_model=InsurancePolicyResponse)
async def update_insurance_policy(
    policy_id: str,
    policy_data: InsurancePolicyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> InsurancePolicyResponse:
    """Update an existing insurance policy"""
    try:
        # Find existing policy
        policy = db.query(UserInsurancePolicy).filter(
            UserInsurancePolicy.id == policy_id,
            UserInsurancePolicy.user_id == current_user.id
        ).first()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance policy not found"
            )
        
        # Update fields
        update_data = policy_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(policy, field, value)
        
        db.commit()
        db.refresh(policy)
        
        logger.info(f"Updated insurance policy {policy_id} for user {current_user.id}")
        
        return InsurancePolicyResponse.model_validate(policy.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update insurance policy {policy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update insurance policy"
        )


@router.delete("/policies/{policy_id}")
async def delete_insurance_policy(
    policy_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Delete an insurance policy"""
    try:
        # Find existing policy
        policy = db.query(UserInsurancePolicy).filter(
            UserInsurancePolicy.id == policy_id,
            UserInsurancePolicy.user_id == current_user.id
        ).first()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance policy not found"
            )
        
        db.delete(policy)
        db.commit()
        
        logger.info(f"Deleted insurance policy {policy_id} for user {current_user.id}")
        
        return {"message": "Insurance policy deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete insurance policy {policy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete insurance policy"
        )


@router.get("/policy-types", response_model=None)
async def get_policy_types() -> Dict[str, Any]:
    """Get available insurance policy types with descriptions"""
    return {
        "policy_types": [
            {"value": "life", "label": "Life Insurance", "description": "Term, whole, or universal life insurance"},
            {"value": "disability", "label": "Disability Insurance", "description": "Short-term or long-term disability coverage"},
            {"value": "health", "label": "Health Insurance", "description": "Medical, dental, and vision insurance"},
            {"value": "auto", "label": "Auto Insurance", "description": "Vehicle liability and comprehensive coverage"},
            {"value": "homeowners", "label": "Homeowners Insurance", "description": "Property and liability protection for homes"},
            {"value": "umbrella", "label": "Umbrella Insurance", "description": "Additional liability coverage beyond other policies"},
            {"value": "renters", "label": "Renters Insurance", "description": "Personal property and liability for renters"},
            {"value": "travel", "label": "Travel Insurance", "description": "Coverage for trips and travel-related incidents"}
        ]
    }