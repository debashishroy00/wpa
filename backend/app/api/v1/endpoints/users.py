"""
WealthPath AI - User Management Endpoints
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserPreferences
from app.services.user_service import UserService
from app.api.v1.endpoints.auth import get_current_active_user

logger = structlog.get_logger()
router = APIRouter()


@router.get("/profile", response_model=UserResponse)
def get_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user profile
    """
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update user profile
    """
    user_service = UserService(db)
    
    try:
        updated_user = user_service.update_user(current_user.id, user_update)
        logger.info("User profile updated", user_id=current_user.id)
        return updated_user
    
    except Exception as e:
        logger.error("Profile update failed", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.get("/preferences", response_model=UserPreferences)
def get_user_preferences(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get user preferences
    """
    # TODO: Implement user preferences model and service
    return {
        "user_id": current_user.id,
        "risk_tolerance": 5,
        "notifications_enabled": True,
        "data_sharing_consent": True
    }


@router.put("/preferences", response_model=UserPreferences)
def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update user preferences
    """
    # TODO: Implement user preferences update
    logger.info("User preferences updated", user_id=current_user.id)
    return preferences


@router.delete("/account")
def delete_user_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete user account (GDPR compliance)
    """
    user_service = UserService(db)
    
    try:
        user_service.delete_user(current_user.id)
        logger.info("User account deleted", user_id=current_user.id)
        return {"message": "Account deleted successfully"}
    
    except Exception as e:
        logger.error("Account deletion failed", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account deletion failed"
        )


# ============================================================================ 
# NEW CLEAN API ENDPOINT FOR PHASE 1
# ============================================================================

@router.get("/{user_id}/profile", response_model=dict)
def get_user_complete_profile(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get complete user profile with calculated age
    Clean API for rebuild - returns everything needed for LLM
    """
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to user data"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate age if birth_year is available
    from datetime import datetime
    current_year = datetime.now().year
    age = None
    
    # Check if user has birth_year attribute or can be calculated from goals
    birth_year = getattr(user, 'birth_year', None)
    if birth_year:
        age = current_year - birth_year
    else:
        # Try to calculate from retirement goals (assuming retirement at 65)
        from app.models.goal import FinancialGoal as Goal
        retirement_goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.goal_type == 'early_retirement'
        ).first()
        
        if retirement_goals and retirement_goals.target_date:
            try:
                retirement_year = int(retirement_goals.target_date.split('-')[0])
                age = 65 - (retirement_year - current_year)
            except:
                pass
    
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "name": f"{user.first_name} {user.last_name}".strip(),
        "email": user.email,
        "age": age,
        "birth_year": birth_year,
        "location": getattr(user, 'location', None),
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "is_active": user.is_active,
        "is_verified": getattr(user, 'is_verified', True)
    }