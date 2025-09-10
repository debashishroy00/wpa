from sqlalchemy import Column, Integer, String, DateTime, Numeric, Date, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class FinancialSnapshot(Base):
    """Main snapshot table storing point-in-time financial state"""
    __tablename__ = "financial_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    snapshot_date = Column(Date, default=func.current_date())
    snapshot_name = Column(String(255), nullable=True)
    
    # Summary metrics
    net_worth = Column(Numeric(15, 2), nullable=True)
    total_assets = Column(Numeric(15, 2), nullable=True)
    total_liabilities = Column(Numeric(15, 2), nullable=True)
    monthly_income = Column(Numeric(10, 2), nullable=True)
    monthly_expenses = Column(Numeric(10, 2), nullable=True)
    savings_rate = Column(Numeric(5, 2), nullable=True)
    
    # Context
    age = Column(Integer, nullable=True)
    employment_status = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="financial_snapshots")
    entries = relationship("SnapshotEntry", back_populates="snapshot", cascade="all, delete-orphan")
    goals = relationship("SnapshotGoal", back_populates="snapshot", cascade="all, delete-orphan")


class SnapshotEntry(Base):
    """Detailed financial entries for each snapshot"""
    __tablename__ = "snapshot_entries"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("financial_snapshots.id"), nullable=False)
    
    # From financial_entries table
    category = Column(String(50), nullable=False)
    subcategory = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=True)
    account_type = Column(String(50), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    
    # Additional context
    interest_rate = Column(Numeric(5, 2), nullable=True)
    
    # Relationships
    snapshot = relationship("FinancialSnapshot", back_populates="entries")


class SnapshotGoal(Base):
    """Goal progress at time of snapshot"""
    __tablename__ = "snapshot_goals"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("financial_snapshots.id"), nullable=False)
    
    goal_name = Column(String(255), nullable=False)
    target_amount = Column(Numeric(15, 2), nullable=False)
    current_amount = Column(Numeric(15, 2), nullable=False)
    target_date = Column(Date, nullable=True)
    completion_percentage = Column(Numeric(5, 2), nullable=True)
    
    # Relationships
    snapshot = relationship("FinancialSnapshot", back_populates="goals")