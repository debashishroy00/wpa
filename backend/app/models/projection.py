"""
WealthPath AI - Advanced Financial Projection Models
Comprehensive multi-factor projection system with Monte Carlo simulation
"""
from sqlalchemy import Column, Integer, Float, JSON, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from decimal import Decimal
from app.db.session import Base


class ProjectionAssumptions(Base):
    """
    User-configurable projection assumptions for financial modeling
    """
    __tablename__ = "projection_assumptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Growth Rates - Income Sources
    salary_growth_rate = Column(Float, default=0.04, nullable=False)  # 4% annual
    rental_income_growth = Column(Float, default=0.03, nullable=False)  # 3% annual
    business_income_growth = Column(Float, default=0.06, nullable=False)  # 6% annual
    
    # Asset Appreciation Rates
    real_estate_appreciation = Column(Float, default=0.04, nullable=False)  # 4% annual
    stock_market_return = Column(Float, default=0.08, nullable=False)  # 8% annual expected
    retirement_account_return = Column(Float, default=0.065, nullable=False)  # 6.5% conservative
    cash_equivalent_return = Column(Float, default=0.02, nullable=False)  # 2% savings/CDs
    
    # Expense Growth Factors
    inflation_rate = Column(Float, default=0.025, nullable=False)  # 2.5% CPI inflation
    lifestyle_inflation = Column(Float, default=0.01, nullable=False)  # 1% lifestyle creep
    healthcare_inflation = Column(Float, default=0.05, nullable=False)  # 5% medical costs
    
    # Volatility Parameters for Monte Carlo
    stock_volatility = Column(Float, default=0.15, nullable=False)  # 15% standard deviation
    real_estate_volatility = Column(Float, default=0.02, nullable=False)  # 2% std dev
    income_volatility = Column(Float, default=0.05, nullable=False)  # 5% salary variance
    
    # Tax Considerations
    effective_tax_rate = Column(Float, default=0.25, nullable=False)  # 25% effective rate
    capital_gains_rate = Column(Float, default=0.15, nullable=False)  # 15% long-term cap gains
    
    # Advanced Parameters
    rebalancing_frequency = Column(Integer, default=12, nullable=False)  # Monthly rebalancing
    sequence_risk_factor = Column(Float, default=0.02, nullable=False)  # Sequence of returns risk
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship
    user = relationship("User", back_populates="projection_assumptions")


class ProjectionSnapshot(Base):
    """
    Historical snapshots of projection calculations for tracking accuracy
    """
    __tablename__ = "projection_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Projection Parameters
    projection_years = Column(Integer, nullable=False)  # 5, 10, 20, 30
    scenario_type = Column(String(20), nullable=False)  # pessimistic, expected, optimistic
    
    # Calculated Results (JSON for flexibility)
    projected_values = Column(JSON, nullable=False)  # Year-by-year net worth progression
    confidence_intervals = Column(JSON, nullable=False)  # P10, P25, P50, P75, P90 bands
    growth_components = Column(JSON, nullable=False)  # Breakdown by source (savings, appreciation, etc.)
    
    # Key Milestones
    key_milestones = Column(JSON, nullable=False)  # Financial independence dates, targets
    
    # Assumptions Snapshot (for historical accuracy)
    assumptions_used = Column(JSON, nullable=False)  # Copy of assumptions at time of calculation
    
    # Performance Metrics
    monte_carlo_iterations = Column(Integer, default=1000, nullable=False)
    calculation_time_ms = Column(Integer, nullable=False)  # Performance tracking
    
    # Input Data Snapshot
    starting_financials = Column(JSON, nullable=False)  # Net worth, income, expenses at time of calc
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="projection_snapshots")


class ProjectionSensitivity(Base):
    """
    Sensitivity analysis results for different assumption variations
    """
    __tablename__ = "projection_sensitivity"
    
    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("projection_snapshots.id"), nullable=False)
    
    # Factor being analyzed
    factor_name = Column(String(50), nullable=False)  # stock_market_return, salary_growth_rate, etc.
    base_value = Column(Float, nullable=False)  # Original assumption value
    
    # Sensitivity Results
    sensitivity_results = Column(JSON, nullable=False)  # Impact of +/- variations
    impact_ranking = Column(Integer, nullable=False)  # 1 = most impactful factor
    
    # Statistical Measures
    correlation_coefficient = Column(Float, nullable=False)  # How correlated to final outcome
    elasticity = Column(Float, nullable=False)  # % change in outcome per % change in factor
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship
    projection_snapshot = relationship("ProjectionSnapshot")


# Add relationships to User model (this would be added to existing user.py)
"""
Add these to the User model:

projection_assumptions = relationship("ProjectionAssumptions", back_populates="user")
projection_snapshots = relationship("ProjectionSnapshot", back_populates="user")
"""