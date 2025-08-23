"""
WealthPath AI - Goal Management Schemas
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, field_validator
from datetime import datetime
from decimal import Decimal
from enum import Enum

from app.models.goal import GoalType, GoalStatus, ActionPriority, ActionStatus


# Base Goal Schemas

class FinancialGoalBase(BaseModel):
    """Base schema for financial goals"""
    goal_type: GoalType
    name: str
    description: Optional[str] = None
    target_amount: Decimal
    current_amount: Optional[Decimal] = None
    target_date: datetime
    parameters: Optional[Dict[str, Any]] = None
    priority: Optional[int] = 1
    
    @field_validator('target_amount')
    @classmethod
    def validate_target_amount(cls, v):
        if v <= 0:
            raise ValueError('Target amount must be positive')
        return v
    
    @field_validator('current_amount')
    @classmethod
    def validate_current_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError('Current amount cannot be negative')
        return v
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Priority must be between 1 (highest) and 10 (lowest)')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Goal name must be at least 3 characters')
        return v.strip()


class FinancialGoalCreate(FinancialGoalBase):
    """Schema for creating financial goals"""
    pass


class FinancialGoalUpdate(BaseModel):
    """Schema for updating financial goals"""
    name: Optional[str] = None
    description: Optional[str] = None
    target_amount: Optional[Decimal] = None
    current_amount: Optional[Decimal] = None
    target_date: Optional[datetime] = None
    parameters: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    status: Optional[GoalStatus] = None


class FinancialGoalResponse(FinancialGoalBase):
    """Schema for financial goal responses"""
    id: int
    user_id: int
    progress_percentage: Decimal
    monthly_target: Optional[Decimal] = None
    feasibility_score: Optional[Decimal] = None
    success_probability: Optional[Decimal] = None
    risk_level: Optional[str] = None
    status: GoalStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    achieved_at: Optional[datetime] = None
    last_analyzed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Goal Scenario Schemas

class GoalScenarioBase(BaseModel):
    """Base schema for goal scenarios"""
    scenario_name: str
    description: Optional[str] = None
    assumptions: Dict[str, Any]


class GoalScenarioCreate(GoalScenarioBase):
    """Schema for creating goal scenarios"""
    goal_id: int


class GoalScenarioResponse(GoalScenarioBase):
    """Schema for goal scenario responses"""
    id: int
    goal_id: int
    is_baseline: bool
    projected_end_value: Optional[Decimal] = None
    projected_end_date: Optional[datetime] = None
    required_monthly_amount: Optional[Decimal] = None
    success_probability: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = None
    model_version: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


# Action Plan Schemas

class ActionPlanBase(BaseModel):
    """Base schema for action plans"""
    action_type: str
    title: str
    description: str
    target_value: Optional[Decimal] = None
    target_percentage: Optional[Decimal] = None
    frequency: Optional[str] = None
    priority: ActionPriority = ActionPriority.medium
    target_start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    estimated_duration_days: Optional[int] = None


class ActionPlanCreate(ActionPlanBase):
    """Schema for creating action plans"""
    goal_id: int


class ActionPlanResponse(ActionPlanBase):
    """Schema for action plan responses"""
    id: int
    goal_id: int
    impact_score: Optional[Decimal] = None
    difficulty_score: Optional[Decimal] = None
    status: ActionStatus
    completion_percentage: Decimal
    notes: Optional[str] = None
    completion_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Goal Milestone Schemas

class GoalMilestoneBase(BaseModel):
    """Base schema for goal milestones"""
    name: str
    description: Optional[str] = None
    target_amount: Decimal
    target_date: datetime
    
    @field_validator('target_amount')
    @classmethod
    def validate_target_amount(cls, v):
        if v <= 0:
            raise ValueError('Target amount must be positive')
        return v


class GoalMilestoneCreate(GoalMilestoneBase):
    """Schema for creating goal milestones"""
    goal_id: int


class GoalMilestoneResponse(GoalMilestoneBase):
    """Schema for goal milestone responses"""
    id: int
    goal_id: int
    current_amount: Decimal
    is_achieved: bool
    created_at: datetime
    achieved_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Analytics and Progress Schemas

class GoalAnalytics(BaseModel):
    """Schema for goal analytics summary"""
    user_id: int
    total_goals: int
    active_goals: int
    achieved_goals: int
    total_target_amount: Decimal
    total_current_amount: Decimal
    overall_progress: Decimal
    goals_on_track: int
    high_risk_goals: int
    average_feasibility: Decimal


class GoalProgressSummary(BaseModel):
    """Schema for detailed goal progress"""
    goal_id: int
    progress_percentage: Decimal
    current_amount: Decimal
    target_amount: Decimal
    remaining_amount: Decimal
    days_remaining: int
    months_remaining: float
    required_monthly_contribution: Decimal
    is_on_track: bool
    risk_level: Optional[str] = None
    feasibility_score: Optional[Decimal] = None


# Goal Template Schemas

class GoalTemplateBase(BaseModel):
    """Base schema for goal templates"""
    template_type: GoalType
    name: str
    description: str
    suggested_timeline_months: int
    default_parameters: Dict[str, Any]
    calculation_rules: Dict[str, Any]


class GoalTemplate(GoalTemplateBase):
    """Schema for goal template responses"""
    id: str
    category: str
    tags: List[str]
    is_popular: bool
    difficulty_level: str  # beginner, intermediate, advanced
    
    
# Target Setting Assistant Schemas

class TargetSuggestion(BaseModel):
    """Schema for AI-generated target suggestions"""
    goal_type: GoalType
    suggested_amount: Decimal
    suggested_timeline_months: int
    confidence_score: Decimal
    reasoning: str
    assumptions: Dict[str, Any]
    alternative_scenarios: List[Dict[str, Any]]


class TargetAnalysisRequest(BaseModel):
    """Schema for target analysis requests"""
    goal_type: GoalType
    user_age: Optional[int] = None
    annual_income: Optional[Decimal] = None
    current_savings: Optional[Decimal] = None
    risk_tolerance: Optional[int] = None  # 1-10 scale
    additional_context: Optional[Dict[str, Any]] = None


# Bulk Operations Schemas

class BulkGoalOperation(BaseModel):
    """Schema for bulk goal operations"""
    goal_ids: List[int]
    operation: str  # activate, pause, analyze, delete
    parameters: Optional[Dict[str, Any]] = None


class BulkGoalResponse(BaseModel):
    """Schema for bulk operation responses"""
    operation: str
    total_goals: int
    successful_operations: int
    failed_operations: int
    errors: List[Dict[str, str]]
    results: List[Dict[str, Any]]