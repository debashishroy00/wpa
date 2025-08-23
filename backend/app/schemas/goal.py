"""
WealthPath AI - Goal Management Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime
from decimal import Decimal
from enum import Enum


class GoalType(str, Enum):
    early_retirement = "early_retirement"
    home_purchase = "home_purchase"
    education = "education"
    emergency_fund = "emergency_fund"
    debt_payoff = "debt_payoff"
    custom = "custom"


class GoalStatus(str, Enum):
    draft = "draft"
    active = "active"
    achieved = "achieved"
    paused = "paused"
    abandoned = "abandoned"


class ActionPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ActionStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class GoalBase(BaseModel):
    """
    Base schema for financial goals
    """
    goal_type: GoalType
    name: str
    description: Optional[str] = None
    target_amount: Decimal
    target_date: datetime
    
    @validator('target_amount')
    def validate_target_amount(cls, v):
        if v <= 0:
            raise ValueError('Target amount must be positive')
        return v
    
    @validator('target_date')
    def validate_target_date(cls, v):
        if v <= datetime.now():
            raise ValueError('Target date must be in the future')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Goal name must be at least 3 characters')
        return v.strip()


class GoalCreate(GoalBase):
    """
    Schema for creating goals
    """
    parameters: Optional[Dict[str, Any]] = None
    priority: Optional[int] = 1
    
    @validator('priority')
    def validate_priority(cls, v):
        if v is not None and not 1 <= v <= 10:
            raise ValueError('Priority must be between 1 and 10')
        return v


class GoalUpdate(BaseModel):
    """
    Schema for updating goals
    """
    name: Optional[str] = None
    description: Optional[str] = None
    target_amount: Optional[Decimal] = None
    target_date: Optional[datetime] = None
    status: Optional[GoalStatus] = None
    priority: Optional[int] = None
    
    @validator('target_amount')
    def validate_target_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Target amount must be positive')
        return v
    
    @validator('target_date')
    def validate_target_date(cls, v):
        if v is not None and v <= datetime.now():
            raise ValueError('Target date must be in the future')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v is not None and not 1 <= v <= 10:
            raise ValueError('Priority must be between 1 and 10')
        return v


class GoalResponse(GoalBase):
    """
    Schema for goal responses
    """
    id: str
    user_id: int
    current_amount: Decimal
    progress_percentage: Decimal
    monthly_target: Optional[Decimal] = None
    status: GoalStatus
    priority: int
    
    # AI Analysis Results
    feasibility_score: Optional[Decimal] = None
    success_probability: Optional[Decimal] = None
    risk_level: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    achieved_at: Optional[datetime] = None
    last_analyzed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class GoalAnalysis(BaseModel):
    """
    Schema for goal analysis results
    """
    goal_id: str
    gap_analysis: Dict[str, Any]
    success_probability: Decimal
    recommendations: List[Dict[str, Any]]
    scenarios: List[Dict[str, Any]] = []
    
    # Analysis metadata
    analysis_date: datetime
    model_version: str = "1.0"
    confidence_score: Decimal


class GapAnalysis(BaseModel):
    """
    Schema for detailed gap analysis
    """
    current_value: Decimal
    target_value: Decimal
    gap_amount: Decimal
    gap_percentage: Decimal
    years_remaining: Decimal
    months_remaining: int
    
    # Required actions
    required_monthly_savings: Decimal
    required_annual_return: Optional[Decimal] = None
    current_savings_rate: Optional[Decimal] = None
    target_savings_rate: Optional[Decimal] = None


class ActionPlanBase(BaseModel):
    """
    Base schema for action plans
    """
    action_type: str
    title: str
    description: str
    priority: ActionPriority = ActionPriority.medium
    target_value: Optional[Decimal] = None
    target_percentage: Optional[Decimal] = None


class ActionPlanCreate(ActionPlanBase):
    """
    Schema for creating action plans
    """
    goal_id: str
    target_start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None


class ActionPlanResponse(ActionPlanBase):
    """
    Schema for action plan responses
    """
    id: str
    goal_id: str
    status: ActionStatus
    completion_percentage: Decimal
    impact_score: Optional[Decimal] = None
    difficulty_score: Optional[Decimal] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class GoalMilestone(BaseModel):
    """
    Schema for goal milestones
    """
    id: str
    goal_id: str
    name: str
    description: Optional[str] = None
    target_amount: Decimal
    target_date: datetime
    current_amount: Decimal
    is_achieved: bool = False
    achieved_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class GoalScenario(BaseModel):
    """
    Schema for goal scenarios and projections
    """
    id: str
    goal_id: str
    scenario_name: str
    description: Optional[str] = None
    is_baseline: bool = False
    
    # Scenario assumptions
    assumptions: Dict[str, Any]
    
    # Results
    projected_end_value: Optional[Decimal] = None
    projected_end_date: Optional[datetime] = None
    required_monthly_amount: Optional[Decimal] = None
    success_probability: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = None
    
    class Config:
        orm_mode = True


class GoalPerformance(BaseModel):
    """
    Schema for goal performance metrics
    """
    goal_id: str
    actual_amount: Decimal
    target_amount: Decimal
    variance_amount: Decimal
    variance_percentage: Decimal
    days_ahead_behind: int
    updated_target_date: Optional[datetime] = None
    updated_success_probability: Optional[Decimal] = None
    measurement_date: datetime
    
    class Config:
        orm_mode = True


class GoalRecommendation(BaseModel):
    """
    Schema for AI-generated goal recommendations
    """
    type: str
    title: str
    description: str
    priority: ActionPriority
    impact_score: Decimal
    difficulty_score: Optional[Decimal] = None
    estimated_benefit: Optional[Decimal] = None
    
    # Implementation details
    action_steps: List[str] = []
    required_resources: List[str] = []
    timeline: Optional[str] = None
    
    # Confidence and validation
    confidence_score: Decimal
    reasoning: str


class TargetSettingRequest(BaseModel):
    """
    Schema for Target Setting Assistant requests
    """
    current_spending: Decimal
    location: str
    age: Optional[int] = None
    income: Optional[Decimal] = None
    lifestyle_preference: str = "comfortable"  # modest, comfortable, luxury
    
    @validator('lifestyle_preference')
    def validate_lifestyle(cls, v):
        allowed = ["modest", "comfortable", "luxury"]
        if v not in allowed:
            raise ValueError(f'Lifestyle preference must be one of {allowed}')
        return v


class TargetSettingResponse(BaseModel):
    """
    Schema for Target Setting Assistant responses
    """
    recommended_target: Decimal
    monthly_spending: Decimal
    annual_spending: Decimal
    confidence_score: Decimal
    peer_percentile: int
    
    # Calculation breakdown
    calculation_details: Dict[str, Any]
    comparison_data: Dict[str, Any]
    
    # Validation
    assumptions: List[str]
    caveats: List[str]