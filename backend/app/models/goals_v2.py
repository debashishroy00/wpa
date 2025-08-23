"""
WealthPath AI - Goals and Preferences Models V2
Comprehensive goal management system with audit trail and relationships
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, TIMESTAMP, Boolean, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import uuid
from datetime import datetime
from typing import Optional, Dict, Any


class Goal(Base):
    """
    Main goals table with comprehensive tracking and audit
    """
    __tablename__ = "goals"

    goal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    target_amount = Column(Numeric(18, 2), nullable=False)
    target_date = Column(Date, nullable=False, index=True)
    priority = Column(Integer, nullable=False, default=3, index=True)
    status = Column(String(20), nullable=False, default='active', index=True)
    params = Column(JSONB, nullable=False, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="goals")
    history = relationship("GoalHistory", back_populates="goal", cascade="all, delete-orphan")
    progress = relationship("GoalProgress", back_populates="goal", cascade="all, delete-orphan")
    parent_relationships = relationship("GoalRelationship", foreign_keys="GoalRelationship.parent_goal_id", cascade="all, delete-orphan")
    child_relationships = relationship("GoalRelationship", foreign_keys="GoalRelationship.child_goal_id", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Goal(id={self.goal_id}, name='{self.name}', category='{self.category}')>"

    @property
    def latest_progress(self) -> Optional['GoalProgress']:
        """Get the most recent progress entry"""
        if self.progress:
            return max(self.progress, key=lambda p: p.recorded_at)
        return None

    @property
    def progress_percentage(self) -> float:
        """Get current progress percentage"""
        latest = self.latest_progress
        return float(latest.percentage_complete) if latest else 0.0

    @property
    def current_amount(self) -> float:
        """Get current amount saved towards goal"""
        latest = self.latest_progress
        return float(latest.current_amount) if latest else 0.0


class GoalHistory(Base):
    """
    Audit trail for all goal changes
    """
    __tablename__ = "goals_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.goal_id", ondelete="CASCADE"), nullable=False, index=True)
    changed_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    change_type = Column(String(20), nullable=False)
    reason = Column(String(500))
    diff = Column(JSONB, nullable=False)
    actor = Column(String(255), nullable=False)

    # Relationships
    goal = relationship("Goal", back_populates="history")

    def __repr__(self):
        return f"<GoalHistory(id={self.history_id}, goal_id={self.goal_id}, type='{self.change_type}')>"


class GoalRelationship(Base):
    """
    Relationships between goals (dependencies, conflicts, etc.)
    """
    __tablename__ = "goal_relationships"

    relationship_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.goal_id", ondelete="CASCADE"), nullable=False)
    child_goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.goal_id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    parent_goal = relationship("Goal", foreign_keys=[parent_goal_id])
    child_goal = relationship("Goal", foreign_keys=[child_goal_id])

    __table_args__ = (
        UniqueConstraint('parent_goal_id', 'child_goal_id', 'relationship_type', name='unique_goal_relationship'),
    )

    def __repr__(self):
        return f"<GoalRelationship(parent={self.parent_goal_id}, child={self.child_goal_id}, type='{self.relationship_type}')>"


class GoalProgress(Base):
    """
    Progress tracking for goals
    """
    __tablename__ = "goal_progress"

    progress_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.goal_id", ondelete="CASCADE"), nullable=False, index=True)
    current_amount = Column(Numeric(18, 2), nullable=False)
    percentage_complete = Column(Numeric(5, 2), nullable=False)
    recorded_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    notes = Column(Text)
    source = Column(String(50), nullable=False, default='manual')

    # Relationships
    goal = relationship("Goal", back_populates="progress")

    def __repr__(self):
        return f"<GoalProgress(id={self.progress_id}, goal_id={self.goal_id}, percentage={self.percentage_complete}%)>"


class UserPreferences(Base):
    """
    User preferences for financial planning
    """
    __tablename__ = "user_preferences"

    preference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    risk_tolerance = Column(String(20), nullable=False, default='moderate')
    investment_timeline = Column(Integer, nullable=False, default=20)
    financial_knowledge = Column(String(20), nullable=False, default='intermediate')
    retirement_age = Column(Integer)
    annual_income_goal = Column(Numeric(18, 2))
    emergency_fund_months = Column(Integer, nullable=False, default=6)
    debt_payoff_priority = Column(String(20), nullable=False, default='balanced')
    notification_preferences = Column(JSONB, nullable=False, default={})
    goal_categories_enabled = Column(JSONB, nullable=False, default=["retirement", "emergency_fund", "education", "real_estate"])
    
    # Enhanced preference fields
    risk_score = Column(Integer)
    investment_style = Column(String(20))
    stocks_preference = Column(Integer)
    bonds_preference = Column(Integer)
    real_estate_preference = Column(Integer)
    crypto_preference = Column(Integer)
    retirement_lifestyle = Column(String(20))
    work_flexibility = Column(JSONB, default={})
    esg_investing = Column(Boolean, default=False)
    
    # Tax-related fields
    tax_filing_status = Column(String(30))
    federal_tax_bracket = Column(Numeric(5, 4))
    state_tax_rate = Column(Numeric(5, 4))
    state = Column(String(2))
    tax_optimization_priority = Column(String(20))
    tax_loss_harvesting = Column(Boolean, default=False)
    roth_ira_eligible = Column(Boolean, default=True)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, risk_tolerance='{self.risk_tolerance}')>"

    @property
    def enabled_categories(self) -> list:
        """Get list of enabled goal categories"""
        return self.goal_categories_enabled if self.goal_categories_enabled else []

    def is_category_enabled(self, category: str) -> bool:
        """Check if a goal category is enabled for this user"""
        return category in self.enabled_categories