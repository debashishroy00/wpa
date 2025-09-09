from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class SnapshotCreate(BaseModel):
    """Schema for creating a snapshot"""
    name: Optional[str] = None


class SnapshotEntryResponse(BaseModel):
    """Schema for snapshot entry response"""
    id: int
    category: str
    subcategory: Optional[str]
    name: str
    institution: Optional[str]
    account_type: Optional[str]
    amount: Decimal
    interest_rate: Optional[Decimal]

    class Config:
        from_attributes = True


class SnapshotGoalResponse(BaseModel):
    """Schema for snapshot goal response"""
    id: int
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: Optional[date]
    completion_percentage: Optional[Decimal]

    class Config:
        from_attributes = True


class SnapshotResponse(BaseModel):
    """Schema for snapshot response"""
    id: int
    user_id: int
    snapshot_date: date
    snapshot_name: Optional[str]
    net_worth: Optional[Decimal]
    total_assets: Optional[Decimal]
    total_liabilities: Optional[Decimal]
    monthly_income: Optional[Decimal]
    monthly_expenses: Optional[Decimal]
    savings_rate: Optional[Decimal]
    age: Optional[int]
    employment_status: Optional[str]
    notes: Optional[str]
    created_at: datetime
    entries: List[SnapshotEntryResponse] = []
    goals: List[SnapshotGoalResponse] = []

    class Config:
        from_attributes = True


class TimelineData(BaseModel):
    """Schema for timeline chart data"""
    dates: List[str]
    net_worth: List[float]
    assets: List[float]
    liabilities: List[float]