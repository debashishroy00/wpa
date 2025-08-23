"""
WealthPath AI - Authentication Schemas
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime

from app.schemas.user import UserResponse


class UserLogin(BaseModel):
    """
    User login request schema
    """
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """
    User registration request schema
    """
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @validator('password')
    def validate_password_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('email')
    def validate_email_format(cls, v):
        # Additional email validation can be added here
        return v.lower()


class Token(BaseModel):
    """
    JWT token response schema
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """
    Token data for refresh requests
    """
    token: str


class PasswordResetRequest(BaseModel):
    """
    Password reset request schema
    """
    email: EmailStr


class PasswordReset(BaseModel):
    """
    Password reset with token schema
    """
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class PasswordChange(BaseModel):
    """
    Password change for authenticated users
    """
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class LoginResponse(BaseModel):
    """
    Login success response
    """
    message: str = "Login successful"
    user: UserResponse
    tokens: Token


class LogoutResponse(BaseModel):
    """
    Logout response
    """
    message: str = "Successfully logged out"