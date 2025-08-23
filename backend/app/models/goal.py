"""
WealthPath AI - Goal Management Models
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, Numeric, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from decimal import Decimal

from app.db.session import Base


class GoalType(enum.Enum):
    early_retirement = "early_retirement"
    home_purchase = "home_purchase"
    education = "education"
    emergency_fund = "emergency_fund"
    debt_payoff = "debt_payoff"
    custom = "custom"


class GoalStatus(enum.Enum):
    draft = "draft"
    active = "active"
    achieved = "achieved"
    paused = "paused"
    abandoned = "abandoned"


class ActionPriority(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ActionStatus(enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class FinancialGoal(Base):
    """
    User financial goals and targets
    """
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Goal Information
    goal_type = Column(SQLEnum(GoalType), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Financial Targets
    target_amount = Column(Numeric(12, 2), nullable=False)
    current_amount = Column(Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    target_date = Column(DateTime, nullable=False)
    
    # Goal Parameters (JSON stored as Text)
    parameters = Column(Text, nullable=True)  # JSON string with goal-specific parameters
    
    # Progress Tracking
    progress_percentage = Column(Numeric(5, 2), default=Decimal('0.00'), nullable=False)  # 0.00 to 100.00
    monthly_target = Column(Numeric(12, 2), nullable=True)  # Required monthly contribution
    
    # AI Analysis Results
    feasibility_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    success_probability = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    risk_level = Column(String(10), nullable=True)  # low, medium, high
    
    # Status and Lifecycle
    status = Column(SQLEnum(GoalStatus), default=GoalStatus.draft, nullable=False)
    priority = Column(Integer, default=1, nullable=False)  # 1 (highest) to 10 (lowest)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    achieved_at = Column(DateTime(timezone=True), nullable=True)
    last_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="financial_goals")
    scenarios = relationship("GoalScenario", back_populates="goal")
    action_plans = relationship("ActionPlan", back_populates="goal")
    milestones = relationship("GoalMilestone", back_populates="goal")

    def __repr__(self):
        return f"<FinancialGoal(id={self.id}, type='{self.goal_type.value}', target=${self.target_amount})>"


class GoalScenario(Base):
    """
    Different scenarios and projections for goal achievement
    """
    __tablename__ = "goal_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("financial_goals.id"), nullable=False, index=True)
    
    # Scenario Information
    scenario_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_baseline = Column(Boolean, default=False, nullable=False)
    
    # Scenario Assumptions (JSON)
    assumptions = Column(Text, nullable=False)  # JSON with rates, contributions, etc.
    
    # Scenario Results
    projected_end_value = Column(Numeric(12, 2), nullable=True)
    projected_end_date = Column(DateTime, nullable=True)
    required_monthly_amount = Column(Numeric(12, 2), nullable=True)
    success_probability = Column(Numeric(3, 2), nullable=True)
    
    # Analysis Metadata
    confidence_score = Column(Numeric(3, 2), nullable=True)
    model_version = Column(String(20), nullable=True)
    calculation_method = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    goal = relationship("FinancialGoal", back_populates="scenarios")

    def __repr__(self):
        return f"<GoalScenario(id={self.id}, goal_id={self.goal_id}, name='{self.scenario_name}')>"


class ActionPlan(Base):
    """
    Specific actions recommended to achieve goals
    """
    __tablename__ = "action_plans"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("financial_goals.id"), nullable=False, index=True)
    
    # Action Information
    action_type = Column(String(50), nullable=False, index=True)  # savings_increase, portfolio_rebalance, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Action Details
    target_value = Column(Numeric(12, 2), nullable=True)  # Dollar amount if applicable
    target_percentage = Column(Numeric(5, 2), nullable=True)  # Percentage if applicable
    frequency = Column(String(20), nullable=True)  # monthly, quarterly, annually
    
    # Prioritization
    priority = Column(SQLEnum(ActionPriority), default=ActionPriority.medium, nullable=False)
    impact_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    difficulty_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    
    # Timing
    target_start_date = Column(DateTime, nullable=True)
    target_completion_date = Column(DateTime, nullable=True)
    estimated_duration_days = Column(Integer, nullable=True)
    
    # Status
    status = Column(SQLEnum(ActionStatus), default=ActionStatus.pending, nullable=False)
    completion_percentage = Column(Numeric(5, 2), default=Decimal('0.00'), nullable=False)
    
    # Tracking
    notes = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    goal = relationship("FinancialGoal", back_populates="action_plans")

    def __repr__(self):
        return f"<ActionPlan(id={self.id}, goal_id={self.goal_id}, type='{self.action_type}')>"


class GoalMilestone(Base):
    """
    Intermediate milestones for goal tracking
    """
    __tablename__ = "goal_milestones"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("financial_goals.id"), nullable=False, index=True)
    
    # Milestone Information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    target_amount = Column(Numeric(12, 2), nullable=False)
    target_date = Column(DateTime, nullable=False)
    
    # Progress
    current_amount = Column(Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    is_achieved = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    achieved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    goal = relationship("FinancialGoal", back_populates="milestones")

    def __repr__(self):
        return f"<GoalMilestone(id={self.id}, goal_id={self.goal_id}, target=${self.target_amount})>"


class GoalPerformanceMetric(Base):
    """
    Performance tracking for goals over time
    """
    __tablename__ = "goal_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("financial_goals.id"), nullable=False, index=True)
    
    # Performance Data
    actual_amount = Column(Numeric(12, 2), nullable=False)
    target_amount = Column(Numeric(12, 2), nullable=False)
    variance_amount = Column(Numeric(12, 2), nullable=False)
    variance_percentage = Column(Numeric(5, 2), nullable=False)
    
    # Projection Updates
    updated_target_date = Column(DateTime, nullable=True)
    updated_success_probability = Column(Numeric(3, 2), nullable=True)
    days_ahead_behind = Column(Integer, default=0, nullable=False)
    
    # Snapshot Metadata
    measurement_date = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    goal = relationship("FinancialGoal")

    def __repr__(self):
        return f"<GoalPerformanceMetric(id={self.id}, goal_id={self.goal_id}, variance={self.variance_percentage}%)>"