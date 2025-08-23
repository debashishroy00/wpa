"""
WealthPath AI - Goals and Preferences Schemas V2
Comprehensive validation schemas for goal management
"""
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, Dict, Any, List, Union
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
import json


class GoalCategory:
    """Valid goal categories"""
    RETIREMENT = "retirement"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    BUSINESS = "business"
    TRAVEL = "travel"
    EMERGENCY_FUND = "emergency_fund"
    DEBT_PAYOFF = "debt_payoff"
    MAJOR_PURCHASE = "major_purchase"
    OTHER = "other"
    
    @classmethod
    def all(cls):
        return [
            cls.RETIREMENT, cls.EDUCATION, cls.REAL_ESTATE, cls.BUSINESS,
            cls.TRAVEL, cls.EMERGENCY_FUND, cls.DEBT_PAYOFF, cls.MAJOR_PURCHASE, cls.OTHER
        ]


class GoalStatus:
    """Valid goal statuses"""
    ACTIVE = "active"
    PAUSED = "paused"
    ACHIEVED = "achieved"
    CANCELLED = "cancelled"
    
    @classmethod
    def all(cls):
        return [cls.ACTIVE, cls.PAUSED, cls.ACHIEVED, cls.CANCELLED]


# Base schemas
class GoalBase(BaseModel):
    category: str = Field(..., description="Goal category")
    name: str = Field(..., min_length=1, max_length=255, description="Goal name")
    target_amount: Decimal = Field(..., ge=0, description="Target amount in dollars")
    target_date: date = Field(..., description="Target completion date")
    priority: int = Field(3, ge=1, le=10, description="Priority (1=highest, 10=lowest)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Category-specific parameters")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }

    @validator('category')
    def validate_category(cls, v):
        if v not in GoalCategory.all():
            raise ValueError(f'Category must be one of {GoalCategory.all()}')
        return v

    @validator('target_date')
    def validate_target_date(cls, v):
        if v <= date.today():
            raise ValueError('Target date must be in the future')
        return v

    @validator('params')
    def validate_params(cls, v, values):
        category = values.get('category')
        if not category:
            return v
            
        # Category-specific validation
        if category == GoalCategory.RETIREMENT:
            required = ['retirement_age', 'annual_spending', 'current_age']
            for field in required:
                if field not in v:
                    raise ValueError(f'{field} is required for retirement goals')
            
            if not isinstance(v.get('retirement_age'), int) or v['retirement_age'] < 50 or v['retirement_age'] > 80:
                raise ValueError('retirement_age must be between 50 and 80')
                
            if not isinstance(v.get('current_age'), int) or v['current_age'] < 18 or v['current_age'] > 80:
                raise ValueError('current_age must be between 18 and 80')
                
            if v['current_age'] >= v['retirement_age']:
                raise ValueError('current_age must be less than retirement_age')
                
        elif category == GoalCategory.EDUCATION:
            required = ['degree_type', 'institution_type', 'start_year']
            for field in required:
                if field not in v:
                    raise ValueError(f'{field} is required for education goals')
                    
        elif category == GoalCategory.REAL_ESTATE:
            required = ['property_type', 'down_payment_percentage']
            for field in required:
                if field not in v:
                    raise ValueError(f'{field} is required for real estate goals')
                    
            if not isinstance(v.get('down_payment_percentage'), (int, float)) or v['down_payment_percentage'] < 5 or v['down_payment_percentage'] > 50:
                raise ValueError('down_payment_percentage must be between 5 and 50')
                
        elif category == GoalCategory.EMERGENCY_FUND:
            required = ['months_of_expenses']
            for field in required:
                if field not in v:
                    raise ValueError(f'{field} is required for emergency fund goals')
                    
            if not isinstance(v.get('months_of_expenses'), int) or v['months_of_expenses'] < 3 or v['months_of_expenses'] > 12:
                raise ValueError('months_of_expenses must be between 3 and 12')
                
        return v


class GoalCreate(GoalBase):
    @validator('target_amount')
    def validate_min_amount(cls, v):
        if v < Decimal('100'):
            raise ValueError('Target amount must be at least $100')
        return v


class GoalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    target_amount: Optional[Decimal] = Field(None, ge=0)
    target_date: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    change_reason: Optional[str] = Field(None, max_length=500, description="Reason for the change (for audit trail)")

    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in GoalStatus.all():
            raise ValueError(f'Status must be one of {GoalStatus.all()}')
        return v

    @validator('target_date')
    def validate_target_date(cls, v):
        if v is not None and v <= date.today():
            raise ValueError('Target date must be in the future')
        return v


class GoalResponse(GoalBase):
    goal_id: UUID
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    progress_percentage: Optional[float] = None
    current_amount: Optional[Decimal] = None
    days_until_target: Optional[int] = None
    
    class Config:
        orm_mode = True
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }
        
    @validator('days_until_target', pre=True, always=True)
    def calculate_days_until_target(cls, v, values):
        target_date = values.get('target_date')
        if target_date:
            delta = target_date - date.today()
            return delta.days
        return None


# Progress tracking schemas
class GoalProgressBase(BaseModel):
    current_amount: Decimal = Field(..., ge=0, description="Current amount saved")
    notes: Optional[str] = Field(None, max_length=1000, description="Progress notes")


class GoalProgressCreate(GoalProgressBase):
    pass


class GoalProgressResponse(GoalProgressBase):
    progress_id: UUID
    goal_id: UUID
    percentage_complete: Decimal
    recorded_at: datetime
    source: str
    
    class Config:
        orm_mode = True


# User preferences schemas
class UserPreferencesBase(BaseModel):
    risk_tolerance: str = Field("moderate", description="Risk tolerance level")
    investment_timeline: int = Field(20, ge=1, le=50, description="Investment timeline in years")
    financial_knowledge: str = Field("intermediate", description="Financial knowledge level")
    retirement_age: Optional[int] = Field(None, ge=50, le=80, description="Planned retirement age")
    annual_income_goal: Optional[Decimal] = Field(None, ge=0, description="Annual income goal")
    emergency_fund_months: int = Field(6, ge=1, le=12, description="Months of emergency fund")
    debt_payoff_priority: str = Field("balanced", description="Debt payoff strategy")
    notification_preferences: Dict[str, Any] = Field(default_factory=dict, description="Notification settings")
    goal_categories_enabled: List[str] = Field(default_factory=lambda: ["retirement", "emergency_fund", "education", "real_estate"], description="Enabled goal categories")
    
    # Enhanced preference fields
    risk_score: Optional[int] = Field(None, ge=1, le=10, description="Risk tolerance score (1-10)")
    investment_style: Optional[str] = Field(None, description="Investment style preference")
    stocks_preference: Optional[int] = Field(None, ge=1, le=10, description="Stocks preference (1-10)")
    bonds_preference: Optional[int] = Field(None, ge=1, le=10, description="Bonds preference (1-10)")
    real_estate_preference: Optional[int] = Field(None, ge=1, le=10, description="Real estate preference (1-10)")
    crypto_preference: Optional[int] = Field(None, ge=1, le=10, description="Crypto preference (1-10)")
    retirement_lifestyle: Optional[str] = Field(None, description="Retirement lifestyle preference")
    work_flexibility: Optional[Dict[str, Any]] = Field(None, description="Work flexibility options")
    esg_investing: Optional[bool] = Field(None, description="ESG/sustainable investing preference")
    
    # Tax-related fields
    tax_filing_status: Optional[str] = Field(None, description="Tax filing status")
    federal_tax_bracket: Optional[float] = Field(None, ge=0, le=1, description="Federal tax bracket as decimal")
    state_tax_rate: Optional[float] = Field(None, ge=0, le=1, description="State tax rate as decimal")
    state: Optional[str] = Field(None, min_length=2, max_length=2, description="State abbreviation")
    tax_optimization_priority: Optional[str] = Field(None, description="Tax optimization priority level")
    tax_loss_harvesting: Optional[bool] = Field(None, description="Tax loss harvesting preference")
    roth_ira_eligible: Optional[bool] = Field(None, description="Roth IRA eligibility status")

    @validator('risk_tolerance')
    def validate_risk_tolerance(cls, v):
        valid = ['conservative', 'moderate', 'aggressive']
        if v not in valid:
            raise ValueError(f'Risk tolerance must be one of {valid}')
        return v

    @validator('financial_knowledge')
    def validate_financial_knowledge(cls, v):
        valid = ['beginner', 'intermediate', 'advanced']
        if v not in valid:
            raise ValueError(f'Financial knowledge must be one of {valid}')
        return v

    @validator('debt_payoff_priority')
    def validate_debt_strategy(cls, v):
        valid = ['avalanche', 'snowball', 'balanced']
        if v not in valid:
            raise ValueError(f'Debt payoff priority must be one of {valid}')
        return v

    @validator('goal_categories_enabled')
    def validate_goal_categories(cls, v):
        valid_categories = GoalCategory.all()
        for category in v:
            if category not in valid_categories:
                raise ValueError(f'Invalid goal category: {category}. Must be one of {valid_categories}')
        return v

    @validator('investment_style')
    def validate_investment_style(cls, v):
        if v is not None:
            valid = ['conservative', 'moderate', 'aggressive']
            if v not in valid:
                raise ValueError(f'Investment style must be one of {valid}')
        return v

    @validator('retirement_lifestyle')
    def validate_retirement_lifestyle(cls, v):
        if v is not None:
            valid = ['downsize', 'maintain', 'upgrade']
            if v not in valid:
                raise ValueError(f'Retirement lifestyle must be one of {valid}')
        return v

    @validator('tax_filing_status')
    def validate_tax_filing_status(cls, v):
        if v is not None:
            valid = ['single', 'married_filing_jointly', 'married_filing_separately', 'head_of_household', 'qualifying_widow']
            if v not in valid:
                raise ValueError(f'Tax filing status must be one of {valid}')
        return v

    @validator('tax_optimization_priority')
    def validate_tax_optimization_priority(cls, v):
        if v is not None:
            valid = ['aggressive', 'moderate', 'conservative', 'none']
            if v not in valid:
                raise ValueError(f'Tax optimization priority must be one of {valid}')
        return v


class UserPreferencesCreate(UserPreferencesBase):
    pass


class UserPreferencesUpdate(BaseModel):
    risk_tolerance: Optional[str] = None
    investment_timeline: Optional[int] = Field(None, ge=1, le=50)
    financial_knowledge: Optional[str] = None
    retirement_age: Optional[int] = Field(None, ge=50, le=80)
    annual_income_goal: Optional[Decimal] = Field(None, ge=0)
    emergency_fund_months: Optional[int] = Field(None, ge=1, le=12)
    debt_payoff_priority: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    goal_categories_enabled: Optional[List[str]] = None
    
    # Enhanced preference fields
    risk_score: Optional[int] = Field(None, ge=1, le=10)
    investment_style: Optional[str] = None
    stocks_preference: Optional[int] = Field(None, ge=1, le=10)
    bonds_preference: Optional[int] = Field(None, ge=1, le=10)
    real_estate_preference: Optional[int] = Field(None, ge=1, le=10)
    crypto_preference: Optional[int] = Field(None, ge=1, le=10)
    retirement_lifestyle: Optional[str] = None
    work_flexibility: Optional[Dict[str, Any]] = None
    esg_investing: Optional[bool] = None
    
    # Tax-related fields
    tax_filing_status: Optional[str] = None
    federal_tax_bracket: Optional[float] = Field(None, ge=0, le=1)
    state_tax_rate: Optional[float] = Field(None, ge=0, le=1)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    tax_optimization_priority: Optional[str] = None
    tax_loss_harvesting: Optional[bool] = None
    roth_ira_eligible: Optional[bool] = None

    @validator('risk_tolerance')
    def validate_risk_tolerance(cls, v):
        if v is not None:
            valid = ['conservative', 'moderate', 'aggressive']
            if v not in valid:
                raise ValueError(f'Risk tolerance must be one of {valid}')
        return v

    @validator('financial_knowledge')
    def validate_financial_knowledge(cls, v):
        if v is not None:
            valid = ['beginner', 'intermediate', 'advanced']
            if v not in valid:
                raise ValueError(f'Financial knowledge must be one of {valid}')
        return v

    @validator('investment_style')
    def validate_investment_style(cls, v):
        if v is not None:
            valid = ['conservative', 'moderate', 'aggressive']
            if v not in valid:
                raise ValueError(f'Investment style must be one of {valid}')
        return v

    @validator('retirement_lifestyle')
    def validate_retirement_lifestyle(cls, v):
        if v is not None:
            valid = ['downsize', 'maintain', 'upgrade']
            if v not in valid:
                raise ValueError(f'Retirement lifestyle must be one of {valid}')
        return v


class UserPreferencesResponse(UserPreferencesBase):
    preference_id: UUID
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# Analysis and reporting schemas
class GoalConflict(BaseModel):
    goal1_id: UUID
    goal1_name: str
    goal2_id: UUID
    goal2_name: str
    conflict_type: str
    severity: str


class GoalSummary(BaseModel):
    active_goals: int
    achieved_goals: int
    total_target: Decimal
    nearest_deadline: Optional[date]
    average_progress: float


class GoalHistory(BaseModel):
    history_id: UUID
    changed_at: datetime
    change_type: str
    reason: Optional[str]
    diff: Dict[str, Any]
    actor: str
    
    class Config:
        orm_mode = True


# Batch operations
class GoalBatchUpdate(BaseModel):
    goal_ids: List[UUID]
    updates: GoalUpdate
    batch_reason: str = Field(..., description="Reason for batch update")


class GoalTemplate(BaseModel):
    """Template for creating common goals"""
    name: str
    category: str
    template_params: Dict[str, Any]
    description: str
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Retirement at 65",
                "category": "retirement",
                "template_params": {
                    "retirement_age": 65,
                    "annual_spending": 50000,
                    "current_age": 30
                },
                "description": "Standard retirement goal template"
            }
        }