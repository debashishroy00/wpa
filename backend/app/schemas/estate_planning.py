"""
Estate Planning Pydantic Schemas for WealthPath AI
Request/response models for estate planning document management
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from enum import Enum


class DocumentType(str, Enum):
    """Estate planning document types"""
    WILL = "will"
    TRUST = "trust" 
    POWER_OF_ATTORNEY = "power_of_attorney"
    HEALTHCARE_DIRECTIVE = "healthcare_directive"
    BENEFICIARY_DESIGNATION = "beneficiary_designation"


class DocumentStatus(str, Enum):
    """Document status tracking"""
    CURRENT = "current"
    NEEDS_UPDATE = "needs_update"
    MISSING = "missing"
    IN_PROGRESS = "in_progress"


class EstatePlanningDocumentBase(BaseModel):
    """Base estate planning document schema"""
    document_type: DocumentType
    document_name: str = Field(..., min_length=1, max_length=100)
    status: DocumentStatus
    last_updated: Optional[date] = None
    next_review_date: Optional[date] = None
    attorney_contact: Optional[str] = Field(None, max_length=200)
    document_location: Optional[str] = Field(None, max_length=200)
    document_details: Optional[Dict[str, Any]] = None


class EstatePlanningDocumentCreate(EstatePlanningDocumentBase):
    """Schema for creating estate planning documents"""
    pass


class EstatePlanningDocumentUpdate(BaseModel):
    """Schema for updating estate planning documents"""
    document_name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[DocumentStatus] = None
    last_updated: Optional[date] = None
    next_review_date: Optional[date] = None
    attorney_contact: Optional[str] = Field(None, max_length=200)
    document_location: Optional[str] = Field(None, max_length=200)
    document_details: Optional[Dict[str, Any]] = None


class EstatePlanningDocumentResponse(EstatePlanningDocumentBase):
    """Schema for estate planning document responses"""
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EstatePlanningSummary(BaseModel):
    """Summary of all estate planning documents for a user"""
    total_documents: int
    documents_by_status: Dict[str, Dict[str, Any]]
    documents_by_type: Dict[str, Dict[str, Any]]
    documents: List[EstatePlanningDocumentResponse]
    upcoming_reviews: List[EstatePlanningDocumentResponse]
    gaps_identified: List[str]


# Specialized schemas for different document types

class WillDocumentDetails(BaseModel):
    """Will document specific details"""
    executor_primary: Optional[str] = Field(None, description="Primary executor name")
    executor_secondary: Optional[str] = Field(None, description="Secondary executor name")
    guardian_children: Optional[str] = Field(None, description="Guardian for minor children")
    will_type: Optional[str] = Field(None, description="simple, complex, or pour_over")
    special_bequests: Optional[List[Dict[str, str]]] = Field(None, description="Special bequests list")


class TrustDocumentDetails(BaseModel):
    """Trust document specific details"""
    trust_type: Optional[str] = Field(None, description="revocable or irrevocable")
    trustee_primary: Optional[str] = Field(None, description="Primary trustee name")
    trustee_successor: Optional[str] = Field(None, description="Successor trustee name")
    beneficiaries: Optional[List[Dict[str, Any]]] = Field(None, description="Beneficiaries with percentages")
    trust_assets: Optional[List[str]] = Field(None, description="Assets in trust")
    distribution_terms: Optional[str] = Field(None, description="Distribution terms and conditions")


class PowerOfAttorneyDetails(BaseModel):
    """Power of Attorney document specific details"""
    poa_type: Optional[str] = Field(None, description="financial, healthcare, durable, or limited")
    agent_primary: Optional[str] = Field(None, description="Primary agent name")
    agent_secondary: Optional[str] = Field(None, description="Secondary agent name")
    powers_granted: Optional[List[str]] = Field(None, description="List of powers granted")
    effective_date: Optional[str] = Field(None, description="When POA becomes effective")
    termination_conditions: Optional[str] = Field(None, description="Conditions for termination")


class HealthcareDirectiveDetails(BaseModel):
    """Healthcare Directive document specific details"""
    healthcare_agent: Optional[str] = Field(None, description="Healthcare agent name")
    backup_agent: Optional[str] = Field(None, description="Backup healthcare agent")
    living_will_preferences: Optional[Dict[str, str]] = Field(None, description="Living will preferences")
    organ_donation: Optional[bool] = Field(None, description="Organ donation preference")
    hipaa_authorization: Optional[List[str]] = Field(None, description="HIPAA authorized persons")


class BeneficiaryDesignationDetails(BaseModel):
    """Beneficiary Designation document specific details"""
    account_type: Optional[str] = Field(None, description="401k, ira, life_insurance, bank_account, investment_account")
    account_provider: Optional[str] = Field(None, description="Financial institution name")
    account_number: Optional[str] = Field(None, description="Account number (masked)")
    primary_beneficiaries: Optional[List[Dict[str, Any]]] = Field(None, description="Primary beneficiaries")
    contingent_beneficiaries: Optional[List[Dict[str, Any]]] = Field(None, description="Contingent beneficiaries")


class EstatePlanningGapAnalysis(BaseModel):
    """Estate planning gap analysis results"""
    missing_documents: List[str]
    outdated_documents: List[str] 
    upcoming_reviews: List[str]
    recommendations: List[str]
    priority_actions: List[str]