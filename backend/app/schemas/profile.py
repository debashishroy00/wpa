"""
WealthPath AI - Profile Schemas
Pydantic models for user profile, family, benefits, and tax information
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ============== User Profile Schemas ==============

class UserProfileBase(BaseModel):
    age: Optional[int] = Field(None, ge=0, le=120)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    marital_status: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(default="USA", max_length=100)
    employment_status: Optional[str] = Field(None, max_length=50)
    occupation: Optional[str] = Field(None, max_length=100)
    risk_tolerance: Optional[str] = Field(None, max_length=20)
    
    # Contact Information
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    emergency_contact: Optional[str] = Field(None, max_length=100)
    emergency_phone: Optional[str] = Field(None, max_length=20)
    
    # Additional Information
    notes: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


# ============== Family Member Schemas ==============

class FamilyMemberBase(BaseModel):
    relationship_type: str = Field(..., max_length=50)  # spouse, child, parent, other_dependent
    name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=120)
    date_of_birth: Optional[date] = None
    
    # Financial Information (for spouse/partner)
    income: Optional[Decimal] = None
    retirement_savings: Optional[Decimal] = None
    
    # For children/dependents
    education_fund_target: Optional[Decimal] = None
    education_fund_current: Optional[Decimal] = None
    expected_college_year: Optional[int] = Field(None, ge=2020, le=2100)
    
    # For aging parents
    requires_financial_support: Optional[bool] = False
    monthly_support_amount: Optional[Decimal] = None
    care_cost_estimate: Optional[Decimal] = None
    
    # Additional details
    notes: Optional[str] = None


class FamilyMemberCreate(FamilyMemberBase):
    pass


class FamilyMemberUpdate(BaseModel):
    relationship_type: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=120)
    date_of_birth: Optional[date] = None
    income: Optional[Decimal] = None
    retirement_savings: Optional[Decimal] = None
    education_fund_target: Optional[Decimal] = None
    education_fund_current: Optional[Decimal] = None
    expected_college_year: Optional[int] = Field(None, ge=2020, le=2100)
    requires_financial_support: Optional[bool] = None
    monthly_support_amount: Optional[Decimal] = None
    care_cost_estimate: Optional[Decimal] = None
    notes: Optional[str] = None


class FamilyMemberResponse(FamilyMemberBase):
    id: int
    profile_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


# ============== User Benefit Schemas ==============

class UserBenefitBase(BaseModel):
    benefit_type: str = Field(..., max_length=50)  # social_security, pension, 401k_match, health_insurance, etc.
    benefit_name: Optional[str] = Field(None, max_length=100)
    
    # Social Security specific
    estimated_monthly_benefit: Optional[Decimal] = None
    full_retirement_age: Optional[int] = Field(None, ge=62, le=70)
    early_retirement_reduction: Optional[Decimal] = Field(None, ge=0, le=100)
    delayed_retirement_increase: Optional[Decimal] = Field(None, ge=0, le=100)
    spouse_benefit_eligible: Optional[bool] = False
    spouse_benefit_amount: Optional[Decimal] = None
    
    # Pension specific
    pension_type: Optional[str] = Field(None, max_length=50)  # defined_benefit, defined_contribution
    vesting_schedule: Optional[str] = Field(None, max_length=100)
    vested_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    expected_monthly_payout: Optional[Decimal] = None
    lump_sum_option: Optional[bool] = False
    
    # Employer benefits
    employer_match_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    employer_match_limit: Optional[Decimal] = None
    health_insurance_premium: Optional[Decimal] = None
    employer_contribution: Optional[Decimal] = None
    
    # Government benefits
    benefit_start_date: Optional[date] = None
    benefit_end_date: Optional[date] = None
    
    # Additional details
    notes: Optional[str] = None


class UserBenefitCreate(UserBenefitBase):
    pass


class UserBenefitUpdate(BaseModel):
    benefit_type: Optional[str] = Field(None, max_length=50)
    benefit_name: Optional[str] = Field(None, max_length=100)
    estimated_monthly_benefit: Optional[Decimal] = None
    full_retirement_age: Optional[int] = Field(None, ge=62, le=70)
    early_retirement_reduction: Optional[Decimal] = Field(None, ge=0, le=100)
    delayed_retirement_increase: Optional[Decimal] = Field(None, ge=0, le=100)
    spouse_benefit_eligible: Optional[bool] = None
    spouse_benefit_amount: Optional[Decimal] = None
    pension_type: Optional[str] = Field(None, max_length=50)
    vesting_schedule: Optional[str] = Field(None, max_length=100)
    vested_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    expected_monthly_payout: Optional[Decimal] = None
    lump_sum_option: Optional[bool] = None
    employer_match_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    employer_match_limit: Optional[Decimal] = None
    health_insurance_premium: Optional[Decimal] = None
    employer_contribution: Optional[Decimal] = None
    benefit_start_date: Optional[date] = None
    benefit_end_date: Optional[date] = None
    notes: Optional[str] = None


class UserBenefitResponse(UserBenefitBase):
    id: int
    profile_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


# ============== User Tax Info Schemas ==============

class UserTaxInfoBase(BaseModel):
    tax_year: int = Field(default_factory=lambda: datetime.now().year, ge=2000, le=2100)
    filing_status: Optional[str] = Field(None, max_length=50)  # single, married_filing_jointly, etc.
    
    # Tax brackets and rates
    federal_tax_bracket: Optional[Decimal] = Field(None, ge=0, le=100)
    state_tax_bracket: Optional[Decimal] = Field(None, ge=0, le=100)
    effective_tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    marginal_tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    
    # Income
    adjusted_gross_income: Optional[Decimal] = None
    taxable_income: Optional[Decimal] = None
    
    # Tax-advantaged accounts
    traditional_401k_contribution: Optional[Decimal] = None
    roth_401k_contribution: Optional[Decimal] = None
    traditional_ira_contribution: Optional[Decimal] = None
    roth_ira_contribution: Optional[Decimal] = None
    hsa_contribution: Optional[Decimal] = None
    
    # Contribution limits
    max_401k_contribution: Optional[Decimal] = None
    max_ira_contribution: Optional[Decimal] = None
    max_hsa_contribution: Optional[Decimal] = None
    
    # Deductions and credits
    standard_deduction: Optional[Decimal] = None
    itemized_deductions: Optional[Decimal] = None
    tax_credits: Optional[Decimal] = None
    
    # Tax planning
    has_tax_professional: Optional[bool] = False
    tax_professional_name: Optional[str] = Field(None, max_length=100)
    tax_strategy_notes: Optional[str] = None
    estimated_quarterly_payments: Optional[bool] = False
    quarterly_payment_amount: Optional[Decimal] = None
    
    # Additional details
    notes: Optional[str] = None


class UserTaxInfoCreate(UserTaxInfoBase):
    pass


class UserTaxInfoUpdate(BaseModel):
    tax_year: Optional[int] = Field(None, ge=2000, le=2100)
    filing_status: Optional[str] = Field(None, max_length=50)
    federal_tax_bracket: Optional[Decimal] = Field(None, ge=0, le=100)
    state_tax_bracket: Optional[Decimal] = Field(None, ge=0, le=100)
    effective_tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    marginal_tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    adjusted_gross_income: Optional[Decimal] = None
    taxable_income: Optional[Decimal] = None
    traditional_401k_contribution: Optional[Decimal] = None
    roth_401k_contribution: Optional[Decimal] = None
    traditional_ira_contribution: Optional[Decimal] = None
    roth_ira_contribution: Optional[Decimal] = None
    hsa_contribution: Optional[Decimal] = None
    max_401k_contribution: Optional[Decimal] = None
    max_ira_contribution: Optional[Decimal] = None
    max_hsa_contribution: Optional[Decimal] = None
    standard_deduction: Optional[Decimal] = None
    itemized_deductions: Optional[Decimal] = None
    tax_credits: Optional[Decimal] = None
    has_tax_professional: Optional[bool] = None
    tax_professional_name: Optional[str] = Field(None, max_length=100)
    tax_strategy_notes: Optional[str] = None
    estimated_quarterly_payments: Optional[bool] = None
    quarterly_payment_amount: Optional[Decimal] = None
    notes: Optional[str] = None


class UserTaxInfoResponse(UserTaxInfoBase):
    id: int
    profile_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


# ============== Complete Profile Response ==============

class CompleteProfileResponse(BaseModel):
    profile: Optional[UserProfileResponse]
    family_members: List[FamilyMemberResponse]
    benefits: List[UserBenefitResponse]
    tax_info: Optional[UserTaxInfoResponse]
    
    model_config = {"from_attributes": True}