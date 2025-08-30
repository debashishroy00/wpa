"""
Investment Preferences API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.session import get_db
from app.models.user import User
from app.models.investment_preferences import UserInvestmentPreferences
from app.schemas.investment_preferences import (
    InvestmentPreferencesResponse,
    InvestmentPreferencesCreate,
    InvestmentPreferencesUpdate,
    RiskAssessmentResponse
)
from app.api.v1.endpoints.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=InvestmentPreferencesResponse)
async def get_investment_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's investment preferences"""
    preferences = db.query(UserInvestmentPreferences).filter(
        UserInvestmentPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment preferences not found"
        )
    
    return preferences


@router.post("/", response_model=InvestmentPreferencesResponse)
async def create_investment_preferences(
    preferences_data: InvestmentPreferencesCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create investment preferences for current user"""
    # Check if preferences already exist
    existing_preferences = db.query(UserInvestmentPreferences).filter(
        UserInvestmentPreferences.user_id == current_user.id
    ).first()
    
    if existing_preferences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Investment preferences already exist. Use PUT to update."
        )
    
    preferences = UserInvestmentPreferences(
        user_id=current_user.id,
        **preferences_data.dict(exclude_unset=True)
    )
    
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    
    return preferences


@router.put("/", response_model=InvestmentPreferencesResponse)
async def update_investment_preferences(
    preferences_data: InvestmentPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update investment preferences for current user"""
    preferences = db.query(UserInvestmentPreferences).filter(
        UserInvestmentPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create if doesn't exist
        preferences = UserInvestmentPreferences(
            user_id=current_user.id,
            **preferences_data.dict(exclude_unset=True)
        )
        db.add(preferences)
    else:
        # Update existing
        update_data = preferences_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    
    return preferences


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_investment_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete investment preferences for current user"""
    preferences = db.query(UserInvestmentPreferences).filter(
        UserInvestmentPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment preferences not found"
        )
    
    db.delete(preferences)
    db.commit()


@router.get("/risk-assessment", response_model=RiskAssessmentResponse)
async def get_risk_assessment(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get risk assessment and recommendations"""
    preferences = db.query(UserInvestmentPreferences).filter(
        UserInvestmentPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment preferences not found. Complete risk assessment first."
        )
    
    return RiskAssessmentResponse(
        risk_profile=preferences.risk_profile,
        risk_score=preferences.risk_tolerance_score,
        timeline_category=preferences.investment_timeline_category,
        recommended_allocation=preferences.get_recommended_allocation()
    )