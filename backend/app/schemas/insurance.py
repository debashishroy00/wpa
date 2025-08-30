"""
Insurance Pydantic Schemas for WealthPath AI
Request/response models for insurance policy management
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime
from enum import Enum


class PolicyType(str, Enum):
    """Insurance policy types"""
    LIFE = "life"
    DISABILITY = "disability" 
    HEALTH = "health"
    AUTO = "auto"
    HOMEOWNERS = "homeowners"
    UMBRELLA = "umbrella"
    RENTERS = "renters"
    TRAVEL = "travel"


class InsurancePolicyBase(BaseModel):
    """Base insurance policy schema"""
    policy_type: PolicyType
    policy_name: str = Field(..., min_length=1, max_length=100)
    coverage_amount: Optional[Decimal] = Field(None, ge=0, le=99999999999.99)
    annual_premium: Optional[Decimal] = Field(None, ge=0, le=999999.99)
    beneficiary_primary: Optional[str] = Field(None, max_length=100)
    beneficiary_secondary: Optional[str] = Field(None, max_length=100)
    policy_details: Optional[Dict[str, Any]] = None


class InsurancePolicyCreate(InsurancePolicyBase):
    """Schema for creating insurance policies"""
    pass


class InsurancePolicyUpdate(BaseModel):
    """Schema for updating insurance policies"""
    policy_name: Optional[str] = Field(None, min_length=1, max_length=100)
    coverage_amount: Optional[Decimal] = Field(None, ge=0, le=99999999999.99)
    annual_premium: Optional[Decimal] = Field(None, ge=0, le=999999.99)
    beneficiary_primary: Optional[str] = Field(None, max_length=100)
    beneficiary_secondary: Optional[str] = Field(None, max_length=100)
    policy_details: Optional[Dict[str, Any]] = None


class InsurancePolicyResponse(InsurancePolicyBase):
    """Schema for insurance policy responses"""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InsurancePoliciesSummary(BaseModel):
    """Summary of all insurance policies for a user"""
    total_policies: int
    total_annual_premiums: Decimal
    coverage_by_type: Dict[str, Dict[str, Any]]
    policies: List[InsurancePolicyResponse]


# Specialized schemas for different policy types

class LifeInsurancePolicyDetails(BaseModel):
    """Life insurance specific details"""
    policy_type_detail: Optional[str] = Field(None, description="term, whole, universal")
    term_years: Optional[int] = Field(None, ge=1, le=100)
    cash_value: Optional[Decimal] = Field(None, ge=0)
    rider_disability: Optional[bool] = False
    rider_accidental_death: Optional[bool] = False
    rider_waiver_of_premium: Optional[bool] = False


class DisabilityInsurancePolicyDetails(BaseModel):
    """Disability insurance specific details"""
    coverage_type: Optional[str] = Field(None, description="short_term, long_term")
    benefit_period: Optional[str] = Field(None, description="2_years, 5_years, age_65")
    elimination_period: Optional[int] = Field(None, ge=0, le=365, description="Days")
    benefit_percentage: Optional[int] = Field(None, ge=1, le=100)
    cost_of_living_adjustment: Optional[bool] = False
    own_occupation_coverage: Optional[bool] = False


class HealthInsurancePolicyDetails(BaseModel):
    """Health insurance specific details"""
    plan_type: Optional[str] = Field(None, description="HMO, PPO, HDHP, EPO")
    deductible: Optional[Decimal] = Field(None, ge=0)
    out_of_pocket_max: Optional[Decimal] = Field(None, ge=0)
    hsa_eligible: Optional[bool] = False
    family_coverage: Optional[bool] = False
    prescription_coverage: Optional[bool] = True


class AutoInsurancePolicyDetails(BaseModel):
    """Auto insurance specific details"""
    vehicle_year: Optional[int] = Field(None, ge=1900, le=2030)
    vehicle_make: Optional[str] = Field(None, max_length=50)
    vehicle_model: Optional[str] = Field(None, max_length=50)
    liability_coverage: Optional[str] = Field(None, description="e.g., 100/300/100")
    comprehensive_deductible: Optional[Decimal] = Field(None, ge=0)
    collision_deductible: Optional[Decimal] = Field(None, ge=0)
    uninsured_motorist: Optional[bool] = True


class HomeownersInsurancePolicyDetails(BaseModel):
    """Homeowners insurance specific details"""
    dwelling_coverage: Optional[Decimal] = Field(None, ge=0)
    personal_property_coverage: Optional[Decimal] = Field(None, ge=0)
    liability_coverage: Optional[Decimal] = Field(None, ge=0)
    deductible: Optional[Decimal] = Field(None, ge=0)
    flood_coverage: Optional[bool] = False
    earthquake_coverage: Optional[bool] = False


class UmbrellaInsurancePolicyDetails(BaseModel):
    """Umbrella insurance specific details"""
    underlying_auto_required: Optional[Decimal] = Field(None, ge=0)
    underlying_homeowners_required: Optional[Decimal] = Field(None, ge=0)
    worldwide_coverage: Optional[bool] = True