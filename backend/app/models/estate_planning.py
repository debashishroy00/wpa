"""
Estate Planning Models for WealthPath AI
Handles legal documents, trusts, wills, beneficiaries, and estate planning status
"""
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.db.base import Base


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


class UserEstatePlanning(Base):
    """
    User estate planning documents model
    Tracks wills, trusts, power of attorney, healthcare directives, and beneficiary designations
    """
    __tablename__ = "user_estate_planning"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Document information
    document_type = Column(String(50), nullable=False)  # DocumentType enum values
    document_name = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False)  # DocumentStatus enum values
    last_updated = Column(Date, nullable=True)
    next_review_date = Column(Date, nullable=True)
    
    # Contact and location information
    attorney_contact = Column(String(200), nullable=True)
    document_location = Column(String(200), nullable=True)  # Physical/digital storage location
    
    # Flexible storage for document-specific details
    document_details = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to user (temporarily disabled to fix SQLAlchemy issues)
    # user = relationship("User", back_populates="estate_planning_documents")
    
    def __repr__(self):
        return f"<UserEstatePlanning(id={self.id}, user_id={self.user_id}, type={self.document_type}, name={self.document_name})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "document_type": self.document_type,
            "document_name": self.document_name,
            "status": self.status,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "next_review_date": self.next_review_date.isoformat() if self.next_review_date else None,
            "attorney_contact": self.attorney_contact,
            "document_location": self.document_location,
            "document_details": self.document_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Sample document_details structures for different estate planning document types:
"""
WILL:
{
    "executor_primary": "John Doe",
    "executor_secondary": "Jane Smith", 
    "guardian_children": "Mary Johnson",
    "will_type": "simple" | "complex" | "pour_over",
    "special_bequests": [
        {"item": "Family home", "beneficiary": "Spouse"},
        {"item": "Investment accounts", "beneficiary": "Children equally"}
    ]
}

TRUST:
{
    "trust_type": "revocable" | "irrevocable",
    "trustee_primary": "John Doe",
    "trustee_successor": "Jane Smith",
    "beneficiaries": [
        {"name": "Spouse", "percentage": 50},
        {"name": "Child 1", "percentage": 25},
        {"name": "Child 2", "percentage": 25}
    ],
    "trust_assets": ["Real estate", "Investment accounts", "Life insurance"],
    "distribution_terms": "Income to spouse for life, remainder to children at age 30"
}

POWER_OF_ATTORNEY:
{
    "poa_type": "financial" | "healthcare" | "durable" | "limited",
    "agent_primary": "Spouse Name",
    "agent_secondary": "Adult Child Name",
    "powers_granted": ["Banking", "Investment management", "Real estate", "Tax matters"],
    "effective_date": "2024-01-01",
    "termination_conditions": "Upon incapacitation or death"
}

HEALTHCARE_DIRECTIVE:
{
    "healthcare_agent": "Spouse Name",
    "backup_agent": "Adult Child Name",
    "living_will_preferences": {
        "life_support": "Do not use extraordinary measures",
        "feeding_tube": "Use if recovery possible within 6 months",
        "pain_medication": "Use as needed for comfort"
    },
    "organ_donation": true,
    "hipaa_authorization": ["Spouse", "Children"]
}

BENEFICIARY_DESIGNATION:
{
    "account_type": "401k" | "ira" | "life_insurance" | "bank_account" | "investment_account",
    "account_provider": "Fidelity",
    "account_number": "****1234",
    "primary_beneficiaries": [
        {"name": "Spouse", "percentage": 100, "relationship": "spouse"}
    ],
    "contingent_beneficiaries": [
        {"name": "Child 1", "percentage": 50, "relationship": "child"},
        {"name": "Child 2", "percentage": 50, "relationship": "child"}
    ]
}
"""