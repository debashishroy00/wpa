"""
Investment Preferences Schemas for API serialization
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class InvestmentPreferencesBase(BaseModel):
    """Base schema for investment preferences"""
    risk_tolerance_score: Optional[int] = Field(None, ge=1, le=10, description="Risk tolerance score (1-10)")
    investment_timeline_years: Optional[int] = Field(None, ge=1, le=50, description="Investment timeline in years")
    rebalancing_frequency: Optional[str] = Field(None, description="Rebalancing frequency")
    investment_philosophy: Optional[str] = Field(None, description="Investment philosophy")
    esg_preference_level: Optional[int] = Field(None, ge=1, le=5, description="ESG preference level (1-5)")
    international_allocation_target: Optional[float] = Field(None, ge=0, le=100, description="International allocation target %")
    alternative_investment_interest: Optional[bool] = Field(False, description="Interest in alternative investments")
    cryptocurrency_allocation: Optional[float] = Field(0, ge=0, le=100, description="Cryptocurrency allocation %")
    individual_stock_tolerance: Optional[bool] = Field(False, description="Tolerance for individual stocks")
    tax_loss_harvesting_enabled: Optional[bool] = Field(False, description="Tax loss harvesting enabled")
    dollar_cost_averaging_preference: Optional[bool] = Field(True, description="Dollar cost averaging preference")
    sector_preferences: Optional[Dict[str, Any]] = Field(None, description="Sector allocation preferences")


class InvestmentPreferencesCreate(InvestmentPreferencesBase):
    """Schema for creating investment preferences"""
    pass


class InvestmentPreferencesUpdate(InvestmentPreferencesBase):
    """Schema for updating investment preferences"""
    pass


class InvestmentPreferencesResponse(InvestmentPreferencesBase):
    """Schema for investment preferences response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class RiskAssessmentResponse(BaseModel):
    """Schema for risk assessment analysis"""
    risk_profile: str
    risk_score: Optional[int]
    timeline_category: str
    recommended_allocation: Dict[str, float]
    
    class Config:
        from_attributes = True