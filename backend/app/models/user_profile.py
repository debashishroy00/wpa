"""
WealthPath AI - User Profile Models
Comprehensive user profile including demographics, family, benefits, and tax information
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, TIMESTAMP, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import uuid
from datetime import datetime
from typing import Optional

class UserProfile(Base):
    """
    Main user profile table for demographics and personal information
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Personal Information
    age = Column(Integer)
    date_of_birth = Column(Date)
    gender = Column(String(20))
    marital_status = Column(String(50))  # single, married, divorced, widowed
    state = Column(String(100))
    country = Column(String(100), default="USA")
    employment_status = Column(String(50))  # employed, self-employed, retired, unemployed
    occupation = Column(String(100))
    risk_tolerance = Column(String(20))  # conservative, moderate, aggressive
    
    # Financial Goals
    retirement_age = Column(Integer, default=64)
    retirement_goal = Column(Numeric(12, 2), default=3500000)
    emergency_fund_months = Column(Integer, default=6)
    
    # Social Security estimates (moved from UserBenefit for easy access)
    social_security_age = Column(Integer, default=67)
    social_security_monthly = Column(Numeric(12, 2), default=4000)
    
    # Risk profile (1-10 scale)
    risk_tolerance_score = Column(Integer, default=7)
    
    # Preferences
    preferences = Column(JSON, default={})
    
    # Contact Information
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    zip_code = Column(String(20))
    emergency_contact = Column(String(100))
    emergency_phone = Column(String(20))
    
    # Additional Information
    notes = Column(Text)  # For storing misc profile information like names until proper fields are added
    
    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")
    family_members = relationship("FamilyMember", back_populates="profile", cascade="all, delete-orphan")
    benefits = relationship("UserBenefit", back_populates="profile", cascade="all, delete-orphan")
    tax_info = relationship("UserTaxInfo", back_populates="profile", cascade="all, delete-orphan")


class FamilyMember(Base):
    """
    Family members including spouse, children, and dependents
    """
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    relationship_type = Column(String(50), nullable=False)  # spouse, child, parent, other_dependent
    name = Column(String(100))
    age = Column(Integer)
    date_of_birth = Column(Date)
    
    # Financial Information (for spouse/partner)
    income = Column(Numeric(12, 2))
    retirement_savings = Column(Numeric(12, 2))
    
    # For children/dependents
    education_fund_target = Column(Numeric(12, 2))
    education_fund_current = Column(Numeric(12, 2))
    expected_college_year = Column(Integer)
    
    # For aging parents
    requires_financial_support = Column(Boolean, default=False)
    monthly_support_amount = Column(Numeric(12, 2))
    care_cost_estimate = Column(Numeric(12, 2))
    
    # Additional details
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="family_members")


class UserBenefit(Base):
    """
    User benefits including Social Security, pensions, and employer benefits
    """
    __tablename__ = "user_benefits"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    benefit_type = Column(String(50), nullable=False)  # social_security, pension, 401k_match, health_insurance, etc.
    benefit_name = Column(String(100))
    
    # Social Security specific
    estimated_monthly_benefit = Column(Numeric(12, 2))
    full_retirement_age = Column(Integer)
    early_retirement_reduction = Column(Numeric(5, 2))  # percentage
    delayed_retirement_increase = Column(Numeric(5, 2))  # percentage
    spouse_benefit_eligible = Column(Boolean, default=False)
    spouse_benefit_amount = Column(Numeric(12, 2))
    
    # Pension specific
    pension_type = Column(String(50))  # defined_benefit, defined_contribution
    vesting_schedule = Column(String(100))
    vested_percentage = Column(Numeric(5, 2))
    expected_monthly_payout = Column(Numeric(12, 2))
    lump_sum_option = Column(Boolean, default=False)
    
    # Employer benefits
    employer_match_percentage = Column(Numeric(5, 2))
    employer_match_limit = Column(Numeric(12, 2))
    health_insurance_premium = Column(Numeric(12, 2))
    employer_contribution = Column(Numeric(12, 2))
    
    # Government benefits
    benefit_start_date = Column(Date)
    benefit_end_date = Column(Date)
    
    # Additional details
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="benefits")


class UserTaxInfo(Base):
    """
    User tax information and planning details
    """
    __tablename__ = "user_tax_info"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    tax_year = Column(Integer, nullable=False, default=datetime.now().year)
    filing_status = Column(String(50))  # single, married_filing_jointly, married_filing_separately, head_of_household
    
    # Tax brackets and rates
    federal_tax_bracket = Column(Numeric(5, 2))  # percentage
    state_tax_bracket = Column(Numeric(5, 2))  # percentage
    effective_tax_rate = Column(Numeric(5, 2))  # percentage
    marginal_tax_rate = Column(Numeric(5, 2))  # percentage
    
    # Income
    adjusted_gross_income = Column(Numeric(12, 2))
    taxable_income = Column(Numeric(12, 2))
    
    # Tax-advantaged accounts
    traditional_401k_contribution = Column(Numeric(12, 2))
    roth_401k_contribution = Column(Numeric(12, 2))
    traditional_ira_contribution = Column(Numeric(12, 2))
    roth_ira_contribution = Column(Numeric(12, 2))
    hsa_contribution = Column(Numeric(12, 2))
    
    # Contribution limits
    max_401k_contribution = Column(Numeric(12, 2))
    max_ira_contribution = Column(Numeric(12, 2))
    max_hsa_contribution = Column(Numeric(12, 2))
    
    # Deductions and credits
    standard_deduction = Column(Numeric(12, 2))
    itemized_deductions = Column(Numeric(12, 2))
    tax_credits = Column(Numeric(12, 2))
    
    # Tax planning
    has_tax_professional = Column(Boolean, default=False)
    tax_professional_name = Column(String(100))
    tax_strategy_notes = Column(Text)
    estimated_quarterly_payments = Column(Boolean, default=False)
    quarterly_payment_amount = Column(Numeric(12, 2))
    
    # Additional details
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="tax_info")