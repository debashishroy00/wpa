"""
Insurance Models for WealthPath AI
Handles insurance policies including life, disability, health, property insurance
"""
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.db.session import Base


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


class UserInsurancePolicy(Base):
    """
    User insurance policies model
    Stores all types of insurance coverage information
    """
    __tablename__ = "user_insurance_policies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Core policy information
    policy_type = Column(String(50), nullable=False)  # PolicyType enum values
    policy_name = Column(String(100), nullable=False)
    coverage_amount = Column(Numeric(12, 2), nullable=True)
    annual_premium = Column(Numeric(8, 2), nullable=True)
    
    # Beneficiary information (mainly for life insurance)
    beneficiary_primary = Column(String(100), nullable=True)
    beneficiary_secondary = Column(String(100), nullable=True)
    
    # Flexible storage for policy-specific details
    policy_details = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to user  
    user = relationship(
        "User", 
        back_populates="insurance_policies",
        lazy="select"
    )
    
    def __repr__(self):
        return f"<UserInsurancePolicy(id={self.id}, user_id={self.user_id}, type={self.policy_type}, name={self.policy_name})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "policy_type": self.policy_type,
            "policy_name": self.policy_name,
            "coverage_amount": float(self.coverage_amount) if self.coverage_amount else None,
            "annual_premium": float(self.annual_premium) if self.annual_premium else None,
            "beneficiary_primary": self.beneficiary_primary,
            "beneficiary_secondary": self.beneficiary_secondary,
            "policy_details": self.policy_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Sample policy_details structures for different insurance types:
"""
LIFE INSURANCE:
{
    "policy_type_detail": "term" | "whole" | "universal",
    "term_years": 20,
    "cash_value": 5000.00,
    "rider_disability": true,
    "rider_accidental_death": true
}

DISABILITY INSURANCE:
{
    "coverage_type": "short_term" | "long_term",
    "benefit_period": "2_years" | "5_years" | "age_65",
    "elimination_period": 90,
    "benefit_percentage": 60,
    "cost_of_living_adjustment": true
}

HEALTH INSURANCE:
{
    "plan_type": "HMO" | "PPO" | "HDHP",
    "deductible": 2000.00,
    "out_of_pocket_max": 8000.00,
    "hsa_eligible": true,
    "family_coverage": true
}

AUTO INSURANCE:
{
    "vehicle_year": 2020,
    "vehicle_make": "Toyota",
    "vehicle_model": "Camry",
    "liability_coverage": "100/300/100",
    "comprehensive_deductible": 500,
    "collision_deductible": 500
}

HOMEOWNERS INSURANCE:
{
    "dwelling_coverage": 400000.00,
    "personal_property_coverage": 200000.00,
    "liability_coverage": 300000.00,
    "deductible": 1000.00,
    "flood_coverage": false
}
"""