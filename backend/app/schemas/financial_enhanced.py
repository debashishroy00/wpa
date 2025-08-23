"""
Enhanced financial schemas with advisor-level details
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import date

class MortgageDetails(BaseModel):
    """Detailed mortgage information"""
    interest_rate: Optional[float] = Field(None, ge=0, le=20)
    monthly_payment: Optional[Decimal] = None
    lender: Optional[str] = None
    origination_date: Optional[date] = None
    term_years: Optional[int] = Field(None, ge=1, le=50)
    includes_pmi: Optional[bool] = False
    includes_escrow: Optional[bool] = True
    property_tax_monthly: Optional[Decimal] = None
    insurance_monthly: Optional[Decimal] = None

class RetirementDetails(BaseModel):
    """401k and retirement account details"""
    contribution_percent: Optional[float] = Field(None, ge=0, le=100)
    employer_match_percent: Optional[float] = Field(None, ge=0, le=100)
    employer_match_limit: Optional[float] = Field(None, ge=0, le=100)
    vesting_schedule: Optional[str] = None
    stock_percent: Optional[float] = Field(None, ge=0, le=100)
    bond_percent: Optional[float] = Field(None, ge=0, le=100)
    average_expense_ratio: Optional[float] = Field(None, ge=0, le=5)

class InvestmentDetails(BaseModel):
    """Investment account details"""
    stock_percentage: Optional[float] = Field(None, ge=0, le=100)
    bond_percentage: Optional[float] = Field(None, ge=0, le=100)
    etf_percentage: Optional[float] = Field(None, ge=0, le=100)
    cash_percentage: Optional[float] = Field(None, ge=0, le=100)
    average_expense_ratio: Optional[float] = Field(None, ge=0, le=5)
    platform: Optional[str] = None
    management_fee_percent: Optional[float] = Field(None, ge=0, le=5)

class Subscription(BaseModel):
    """Subscription/recurring expense"""
    name: str
    cost: Decimal
    category: Optional[str] = None
    usage_frequency: Optional[str] = Field(None, pattern="^(daily|weekly|monthly|rarely|never)$")
    can_cancel: bool = True

class EnhancedFinancialEntry(BaseModel):
    """Financial entry with detailed advisor-level data"""
    category: str
    subcategory: Optional[str] = None
    name: str
    amount: Decimal
    frequency: Optional[str] = "once"
    is_active: bool = True
    
    # Enhanced details stored in JSONB
    details: Optional[Dict[str, Any]] = {}
    
    # Type-specific details
    mortgage_details: Optional[MortgageDetails] = None
    retirement_details: Optional[RetirementDetails] = None
    investment_details: Optional[InvestmentDetails] = None
    subscriptions: Optional[List[Subscription]] = None

class AdvisorDataRequest(BaseModel):
    """Request to save advisor-level data"""
    # Mortgage
    mortgage_rate: Optional[float] = None
    mortgage_payment: Optional[float] = None
    mortgage_lender: Optional[str] = None
    mortgage_term_years: Optional[int] = None
    mortgage_start_date: Optional[str] = None
    
    # Retirement
    contribution_401k: Optional[float] = None
    employer_match: Optional[float] = None
    employer_match_limit: Optional[float] = None
    vesting_schedule: Optional[str] = None
    
    # Investments
    stock_percentage: Optional[float] = None
    bond_percentage: Optional[float] = None
    average_expense_ratio: Optional[float] = None
    investment_platform: Optional[str] = None
    
    # Subscriptions
    subscriptions: Optional[List[Subscription]] = None

class SmartRecommendation(BaseModel):
    """Enhanced recommendation with specific calculations"""
    id: str
    category: str
    title: str
    description: str
    
    # Specific calculations based on user data
    current_value: Optional[float] = None
    recommended_value: Optional[float] = None
    monthly_savings: Optional[float] = None
    annual_savings: Optional[float] = None
    
    # Implementation details
    action_steps: List[str]
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    time_to_implement: str
    
    # Validation requirements
    requires_validation: bool = False
    validation_question: Optional[str] = None
    validation_fields: Optional[List[str]] = None
    
    # Based on actual data vs assumptions
    confidence_level: str = Field("high", pattern="^(high|medium|low)$")
    assumptions_made: Optional[List[str]] = None