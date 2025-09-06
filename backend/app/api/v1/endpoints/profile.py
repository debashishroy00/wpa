"""
WealthPath AI - User Profile API Endpoints
Endpoints for managing user demographics, family, benefits, and tax information
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Any
from datetime import datetime, date

from app.db.session import get_db
from app.models.user import User
from app.models.user_profile import UserProfile, FamilyMember, UserBenefit, UserTaxInfo
from app.api.v1.endpoints.auth import get_current_active_user
from app.schemas.profile import (
    UserProfileCreate, UserProfileUpdate, UserProfileResponse,
    FamilyMemberCreate, FamilyMemberUpdate, FamilyMemberResponse,
    UserBenefitCreate, UserBenefitUpdate, UserBenefitResponse,
    UserTaxInfoCreate, UserTaxInfoUpdate, UserTaxInfoResponse,
    CompleteProfileResponse
)
import structlog

logger = structlog.get_logger()

router = APIRouter()

# ============== Test Endpoint ==============

@router.get("/test-data")
async def test_profile_data(db: Session = Depends(get_db)) -> Any:
    """Test endpoint to check profile data without authentication"""
    try:
        profiles = db.query(UserProfile).all()
        profile_data = []
        for profile in profiles:
            profile_data.append({
                "id": profile.id,
                "user_id": profile.user_id,
                "age": profile.age,
                "state": profile.state,
                "marital_status": profile.marital_status
            })
        return {"profiles": profile_data, "count": len(profile_data)}
    except Exception as e:
        logger.error(f"Error fetching test data: {e}")
        return {"error": str(e)}

# ============== User Profile Endpoints ==============

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get current user's profile"""
    logger.info(f"Fetching profile for user {current_user.id}")
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        logger.info(f"No profile found for user {current_user.id}, creating empty profile")
        # Create empty profile if it doesn't exist
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    else:
        logger.info(f"Found profile for user {current_user.id}: age={profile.age}, state={profile.state}")
    return profile

@router.post("/profile", response_model=UserProfileResponse)
async def create_or_update_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Create or update user profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if profile:
        # Update existing profile
        for field, value in profile_data.dict(exclude_unset=True).items():
            setattr(profile, field, value)
        profile.updated_at = datetime.utcnow()
    else:
        # Create new profile
        profile = UserProfile(
            user_id=current_user.id,
            **profile_data.dict()
        )
        db.add(profile)
    
    db.commit()
    db.refresh(profile)
    
    logger.info(f"Profile {'updated' if profile.id else 'created'} for user {current_user.id}")
    return profile

@router.patch("/profile", response_model=UserProfileResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Partially update user profile"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    for field, value in profile_data.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    
    return profile

# ============== Family Member Endpoints ==============

@router.get("/family", response_model=List[FamilyMemberResponse])
async def get_family_members(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get all family members for current user"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        return []
    
    return db.query(FamilyMember).filter(FamilyMember.profile_id == profile.id).all()

@router.post("/family", response_model=FamilyMemberResponse)
async def add_family_member(
    member_data: FamilyMemberCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Add a family member"""
    # Ensure user has a profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    member = FamilyMember(
        profile_id=profile.id,
        **member_data.dict()
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    logger.info(f"Family member added for user {current_user.id}: {member.relationship_type}")
    return member

@router.patch("/family/{member_id}", response_model=FamilyMemberResponse)
async def update_family_member(
    member_id: int,
    member_data: FamilyMemberUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update a family member"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.profile_id == profile.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    
    for field, value in member_data.dict(exclude_unset=True).items():
        setattr(member, field, value)
    
    member.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(member)
    
    return member

@router.delete("/family/{member_id}")
async def delete_family_member(
    member_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete a family member"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.profile_id == profile.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    
    db.delete(member)
    db.commit()
    
    return {"message": "Family member deleted successfully"}

# ============== Benefits Endpoints ==============

@router.get("/benefits", response_model=List[UserBenefitResponse])
async def get_benefits(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get all benefits for current user"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        return []
    
    return db.query(UserBenefit).filter(UserBenefit.profile_id == profile.id).all()

@router.post("/benefits", response_model=UserBenefitResponse)
async def add_benefit(
    benefit_data: UserBenefitCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Add a benefit"""
    # Ensure user has a profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    benefit = UserBenefit(
        profile_id=profile.id,
        **benefit_data.dict()
    )
    db.add(benefit)
    db.commit()
    db.refresh(benefit)
    
    logger.info(f"Benefit added for user {current_user.id}: {benefit.benefit_type}")
    return benefit

@router.patch("/benefits/{benefit_id}", response_model=UserBenefitResponse)
async def update_benefit(
    benefit_id: int,
    benefit_data: UserBenefitUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update a benefit"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    benefit = db.query(UserBenefit).filter(
        UserBenefit.id == benefit_id,
        UserBenefit.profile_id == profile.id
    ).first()
    
    if not benefit:
        raise HTTPException(status_code=404, detail="Benefit not found")
    
    for field, value in benefit_data.dict(exclude_unset=True).items():
        setattr(benefit, field, value)
    
    benefit.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(benefit)
    
    return benefit

@router.delete("/benefits/{benefit_id}")
async def delete_benefit(
    benefit_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete a benefit"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    benefit = db.query(UserBenefit).filter(
        UserBenefit.id == benefit_id,
        UserBenefit.profile_id == profile.id
    ).first()
    
    if not benefit:
        raise HTTPException(status_code=404, detail="Benefit not found")
    
    db.delete(benefit)
    db.commit()
    
    return {"message": "Benefit deleted successfully"}

# ============== Tax Info Endpoints ==============

@router.get("/tax-info", response_model=List[UserTaxInfoResponse])
async def get_tax_info(
    tax_year: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get tax information for current user"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        return []
    
    query = db.query(UserTaxInfo).filter(UserTaxInfo.profile_id == profile.id)
    if tax_year:
        query = query.filter(UserTaxInfo.tax_year == tax_year)
    
    return query.all()

@router.post("/tax-info", response_model=UserTaxInfoResponse)
async def add_tax_info(
    tax_data: UserTaxInfoCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Add tax information"""
    # Ensure user has a profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    # Check if tax info for this year already exists
    existing = db.query(UserTaxInfo).filter(
        UserTaxInfo.profile_id == profile.id,
        UserTaxInfo.tax_year == tax_data.tax_year
    ).first()
    
    if existing:
        # Update existing
        for field, value in tax_data.dict(exclude_unset=True).items():
            setattr(existing, field, value)
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new
    tax_info = UserTaxInfo(
        profile_id=profile.id,
        **tax_data.dict()
    )
    db.add(tax_info)
    db.commit()
    db.refresh(tax_info)
    
    logger.info(f"Tax info added for user {current_user.id}, year {tax_info.tax_year}")
    return tax_info

@router.patch("/tax-info/{tax_id}", response_model=UserTaxInfoResponse)
async def update_tax_info(
    tax_id: int,
    tax_data: UserTaxInfoUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update tax information"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    tax_info = db.query(UserTaxInfo).filter(
        UserTaxInfo.id == tax_id,
        UserTaxInfo.profile_id == profile.id
    ).first()
    
    if not tax_info:
        raise HTTPException(status_code=404, detail="Tax info not found")
    
    for field, value in tax_data.dict(exclude_unset=True).items():
        setattr(tax_info, field, value)
    
    tax_info.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tax_info)
    
    return tax_info

@router.delete("/tax-info/{tax_id}")
async def delete_tax_info(
    tax_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete tax information"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    tax_info = db.query(UserTaxInfo).filter(
        UserTaxInfo.id == tax_id,
        UserTaxInfo.profile_id == profile.id
    ).first()
    
    if not tax_info:
        raise HTTPException(status_code=404, detail="Tax info not found")
    
    db.delete(tax_info)
    db.commit()
    
    return {"message": "Tax info deleted successfully"}

# ============== Complete Profile Endpoint ==============

@router.get("/complete-profile", response_model=CompleteProfileResponse)
async def get_complete_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get complete user profile including family, benefits, tax info, estate planning, insurance, and investment preferences"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    family_members = db.query(FamilyMember).filter(FamilyMember.profile_id == profile.id).all()
    benefits = db.query(UserBenefit).filter(UserBenefit.profile_id == profile.id).all()
    tax_info = db.query(UserTaxInfo).filter(UserTaxInfo.profile_id == profile.id).order_by(UserTaxInfo.tax_year.desc()).first()
    
    # Get enhanced categories
    estate_documents = []
    insurance_policies = []
    investment_preferences = None
    
    try:
        # Estate planning documents
        from app.models.estate_planning import UserEstatePlanning
        estate_docs = db.query(UserEstatePlanning).filter(UserEstatePlanning.user_id == current_user.id).all()
        estate_documents = [doc.to_dict() for doc in estate_docs]
    except Exception as e:
        logger.warning(f"Could not fetch estate planning documents: {e}")
    
    try:
        # Insurance policies
        from app.models.insurance import UserInsurancePolicy
        insurance_docs = db.query(UserInsurancePolicy).filter(UserInsurancePolicy.user_id == current_user.id).all()
        insurance_policies = [policy.to_dict() for policy in insurance_docs]
    except Exception as e:
        logger.warning(f"Could not fetch insurance policies: {e}")
    
    try:
        # Investment preferences
        from app.models.investment_preferences import UserInvestmentPreferences
        inv_prefs = db.query(UserInvestmentPreferences).filter(UserInvestmentPreferences.user_id == current_user.id).first()
        if inv_prefs:
            investment_preferences = {
                'risk_tolerance_score': inv_prefs.risk_tolerance_score,
                'investment_timeline_years': inv_prefs.investment_timeline_years,
                'investment_philosophy': inv_prefs.investment_philosophy,
                'esg_preference_level': inv_prefs.esg_preference_level,
                'sector_preferences': inv_prefs.sector_preferences,
                'rebalancing_frequency': inv_prefs.rebalancing_frequency,
                'alternative_investment_interest': inv_prefs.alternative_investment_interest
            }
    except Exception as e:
        logger.warning(f"Could not fetch investment preferences: {e}")
    
    return CompleteProfileResponse(
        profile=profile,
        family_members=family_members,
        benefits=benefits,
        tax_info=tax_info,
        estate_documents=estate_documents,
        insurance_policies=insurance_policies,
        investment_preferences=investment_preferences
    )

# ============== Specialized Profile Data Endpoints ==============

from pydantic import BaseModel

class SocialSecurityUpdate(BaseModel):
    estimated_monthly_benefit: float
    planned_claiming_age: int
    full_retirement_age: int

class FourOhOneKUpdate(BaseModel):
    employer_match_formula: str
    vesting_schedule: str
    annual_salary: float
    annual_401k_limit: float

@router.post("/social-security")
async def update_social_security(
    data: SocialSecurityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update Social Security benefits information"""
    
    # Get or create user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()
    
    # Find or create Social Security benefit record
    benefit = db.query(UserBenefit).filter(
        UserBenefit.profile_id == profile.id,
        UserBenefit.benefit_type == "social_security"
    ).first()
    
    if not benefit:
        benefit = UserBenefit(
            profile_id=profile.id,
            benefit_type="social_security",
            benefit_name="Social Security"
        )
        db.add(benefit)
    
    # Update fields
    benefit.estimated_monthly_benefit = data.estimated_monthly_benefit
    benefit.full_retirement_age = data.full_retirement_age
    benefit.social_security_claiming_age = data.planned_claiming_age
    benefit.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(benefit)
    
    logger.info(f"Social Security data updated for user {current_user.id}")
    
    # Trigger vector store sync if available
    try:
        from app.services.vector_sync_service import sync_user_data
        sync_user_data(current_user.id, db)
    except ImportError:
        logger.info("Vector sync service not available - skipping sync")
    
    return {"status": "success", "message": "Social Security data updated"}

@router.post("/401k")  
async def update_401k_settings(
    data: FourOhOneKUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update 401(k) settings - SIMPLIFIED"""
    
    # Direct SQL approach to ensure it works
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    # Update or create 401k benefit using raw SQL to ensure it works
    result = db.execute(text("""
        UPDATE user_benefits 
        SET 
            employer_401k_match_formula = :formula,
            employer_401k_vesting_schedule = :schedule,
            employer_contribution = :salary,
            max_401k_contribution = :limit,
            updated_at = NOW()
        WHERE profile_id = :profile_id AND benefit_type = '401k'
        RETURNING id
    """), {
        'formula': data.employer_match_formula,
        'schedule': data.vesting_schedule, 
        'salary': data.annual_salary,
        'limit': data.annual_401k_limit,
        'profile_id': profile.id
    })
    
    updated_rows = result.fetchall()
    
    if not updated_rows:
        # Create new record
        db.execute(text("""
            INSERT INTO user_benefits 
            (profile_id, benefit_type, benefit_name, employer_401k_match_formula, 
             employer_401k_vesting_schedule, employer_contribution, max_401k_contribution, created_at, updated_at)
            VALUES 
            (:profile_id, '401k', '401(k) Plan', :formula, :schedule, :salary, :limit, NOW(), NOW())
        """), {
            'profile_id': profile.id,
            'formula': data.employer_match_formula,
            'schedule': data.vesting_schedule,
            'salary': data.annual_salary, 
            'limit': data.annual_401k_limit
        })
    
    db.commit()
    return {"status": "success", "message": "401(k) settings updated"}

@router.post("/sync-vector-store")
async def sync_vector_store(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Trigger vector store sync for complete financial context update"""
    
    try:
        from app.services.vector_sync_service import sync_user_data
        sync_user_data(current_user.id, db)
        logger.info(f"Vector store synced for user {current_user.id}")
        return {"status": "success", "message": "Vector store synced"}
    except ImportError:
        logger.info("Vector sync service not available")
        return {"status": "success", "message": "Sync service not available, data saved to database"}
    except Exception as e:
        logger.error(f"Error syncing vector store: {e}")
        return {"status": "error", "message": "Failed to sync vector store, but data was saved"}