"""
Investment Preferences Models for WealthPath AI
Handles risk assessment, asset allocation preferences, and investment strategy configuration
"""
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.db.session import Base


class RebalancingFrequency(str, Enum):
    """Rebalancing frequency options"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    THRESHOLD = "threshold"  # Based on drift percentage


class InvestmentPhilosophy(str, Enum):
    """Investment philosophy options"""
    PASSIVE = "passive"
    ACTIVE = "active"
    HYBRID = "hybrid"
    VALUE = "value"
    GROWTH = "growth"
    MOMENTUM = "momentum"


class UserInvestmentPreferences(Base):
    """User investment preferences and risk assessment model"""
    __tablename__ = "user_investment_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    
    # Risk Assessment (1-10 scale)
    risk_tolerance_score = Column(Integer, nullable=True)  # 1=Conservative, 10=Aggressive
    investment_timeline_years = Column(Integer, nullable=True)  # Years until retirement/goal
    
    # Investment Strategy Preferences
    rebalancing_frequency = Column(String(20), nullable=True)  # Using enum values
    investment_philosophy = Column(String(50), nullable=True)  # Using enum values
    
    # ESG and Social Preferences (1-5 scale)
    esg_preference_level = Column(Integer, nullable=True)  # 1=Not important, 5=Very important
    
    # Asset Allocation Preferences (percentages)
    international_allocation_target = Column(Numeric(5, 2), nullable=True)  # % of portfolio
    alternative_investment_interest = Column(Boolean, default=False)
    cryptocurrency_allocation = Column(Numeric(5, 2), nullable=True, default=0)  # % of portfolio
    individual_stock_tolerance = Column(Boolean, default=False)
    
    # Tax Strategy Preferences
    tax_loss_harvesting_enabled = Column(Boolean, default=False)
    dollar_cost_averaging_preference = Column(Boolean, default=True)
    
    # Sector/Industry Preferences (JSON)
    sector_preferences = Column(JSONB, nullable=True)  # {"technology": 0.2, "healthcare": 0.15, ...}
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships (using viewonly to prevent circular issues)
    user = relationship(
        "User", 
        lazy="select",
        viewonly=True
    )

    def __repr__(self):
        return f"<UserInvestmentPreferences(user_id={self.user_id}, risk_score={self.risk_tolerance_score})>"

    @property
    def risk_profile(self) -> str:
        """Get risk profile description based on risk tolerance score"""
        if not self.risk_tolerance_score:
            return "Unknown"
        
        if self.risk_tolerance_score <= 3:
            return "Conservative"
        elif self.risk_tolerance_score <= 6:
            return "Moderate"
        elif self.risk_tolerance_score <= 8:
            return "Moderate-Aggressive"
        else:
            return "Aggressive"

    @property
    def investment_timeline_category(self) -> str:
        """Get investment timeline category description"""
        if not self.investment_timeline_years:
            return "Unknown"
        
        if self.investment_timeline_years <= 5:
            return "Short-term"
        elif self.investment_timeline_years <= 15:
            return "Medium-term"
        else:
            return "Long-term"

    def get_recommended_allocation(self) -> dict:
        """Get recommended asset allocation based on preferences"""
        if not self.risk_tolerance_score or not self.investment_timeline_years:
            return {"stocks": 60, "bonds": 30, "alternatives": 10}
        
        # Age-based adjustment: 100 - age rule, modified by risk tolerance
        base_stock_allocation = min(90, max(20, 100 - (65 - self.investment_timeline_years)))
        
        # Risk tolerance adjustment
        if self.risk_tolerance_score <= 3:
            stock_allocation = base_stock_allocation - 20
        elif self.risk_tolerance_score <= 6:
            stock_allocation = base_stock_allocation - 10
        elif self.risk_tolerance_score <= 8:
            stock_allocation = base_stock_allocation
        else:
            stock_allocation = min(95, base_stock_allocation + 10)
        
        stock_allocation = max(10, min(95, stock_allocation))
        bond_allocation = max(5, 100 - stock_allocation - (self.cryptocurrency_allocation or 0))
        
        return {
            "stocks": stock_allocation,
            "bonds": bond_allocation,
            "alternatives": max(0, 100 - stock_allocation - bond_allocation),
            "international": self.international_allocation_target or 20,
            "crypto": self.cryptocurrency_allocation or 0
        }