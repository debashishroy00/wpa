"""
WealthPath AI - User Schemas
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from enum import Enum


class UserStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    deleted = "deleted"


class UserBase(BaseModel):
    """
    Base user schema with common fields
    """
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    """
    User creation schema
    """
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    """
    User update schema
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserResponse(UserBase):
    """
    User response schema (excludes sensitive data)
    """
    id: int
    is_active: bool
    status: UserStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class UserProfile(BaseModel):
    """
    Extended user profile schema
    """
    date_of_birth: Optional[datetime] = None
    location: Optional[str] = None
    timezone: str = "UTC"
    risk_tolerance: int = 5
    investment_experience: str = "beginner"
    annual_income: Optional[int] = None
    employment_status: Optional[str] = None
    currency: str = "USD"
    language: str = "en"
    
    @validator('risk_tolerance')
    def validate_risk_tolerance(cls, v):
        if not 1 <= v <= 10:
            raise ValueError('Risk tolerance must be between 1 and 10')
        return v
    
    @validator('investment_experience')
    def validate_investment_experience(cls, v):
        allowed_values = ["beginner", "intermediate", "advanced"]
        if v not in allowed_values:
            raise ValueError(f'Investment experience must be one of {allowed_values}')
        return v


class UserPreferences(BaseModel):
    """
    User preferences schema
    """
    user_id: int
    risk_tolerance: int = 5
    notifications_enabled: bool = True
    data_sharing_consent: bool = False
    marketing_consent: bool = False
    analytics_consent: bool = True
    email_notifications: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    
    @validator('risk_tolerance')
    def validate_risk_tolerance(cls, v):
        if not 1 <= v <= 10:
            raise ValueError('Risk tolerance must be between 1 and 10')
        return v
    
    class Config:
        orm_mode = True


class UserActivity(BaseModel):
    """
    User activity log schema
    """
    id: int
    user_id: Optional[int]
    action: str
    resource: Optional[str] = None
    result: str = "success"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


class UserStats(BaseModel):
    """
    User statistics schema
    """
    user_id: int
    total_goals: int = 0
    active_goals: int = 0
    completed_goals: int = 0
    total_net_worth: float = 0.0
    financial_accounts_connected: int = 0
    last_activity: Optional[datetime] = None
    account_age_days: int = 0