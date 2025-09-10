"""
WealthPath AI - User Models
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class UserStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    deleted = "deleted"


class User(Base):
    """
    User model for authentication and profile management
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.active, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    
    # Relationships  
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    sessions = relationship("UserSession", back_populates="user")
    financial_accounts = relationship("FinancialAccount", back_populates="user")
    financial_entries = relationship("FinancialEntry", back_populates="user")
    financial_goals = relationship("FinancialGoal", back_populates="user")
    model_predictions = relationship("ModelPrediction", back_populates="user")
    interactions = relationship("UserInteraction", back_populates="user")
    projection_assumptions = relationship("ProjectionAssumptions", back_populates="user")
    projection_snapshots = relationship("ProjectionSnapshot", back_populates="user")
    
    # New V2 Goals relationships
    goals = relationship("Goal", back_populates="user")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    
    # Estate planning, insurance, and investment preferences relationships
    # Using simple relationships with lazy loading - models imported in endpoints
    estate_planning_documents = relationship(
        "UserEstatePlanning", 
        back_populates="user",
        lazy="dynamic"  # Load as query object
    )
    insurance_policies = relationship(
        "UserInsurancePolicy", 
        back_populates="user",
        lazy="dynamic"
    )
    investment_preferences = relationship(
        "UserInvestmentPreferences", 
        back_populates="user", 
        uselist=False,
        lazy="select"
    )
    
    # Chat intelligence relationship
    chat_intelligence = relationship(
        "ChatIntelligence",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Financial snapshots relationship
    financial_snapshots = relationship(
        "FinancialSnapshot",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', status='{self.status.value}')>"




class UserSession(Base):
    """
    User session tracking for JWT token management
    """
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Token Information
    token_hash = Column(String(255), nullable=False, index=True)  # Hash of JWT for security
    token_type = Column(String(20), default="refresh", nullable=False)  # access, refresh
    
    # Session Details
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, type='{self.token_type}')>"


class UserActivityLog(Base):
    """
    User activity logging for security and analytics
    """
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)  # Can be null for anonymous events
    
    # Activity Information
    action = Column(String(100), nullable=False, index=True)  # login, logout, profile_update, etc.
    resource = Column(String(100), nullable=True)  # What was accessed/modified
    result = Column(String(20), default="success", nullable=False)  # success, failure, error
    
    # Request Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(36), nullable=True)  # UUID for request correlation
    
    # Additional Data
    extra_data = Column(Text, nullable=True)  # JSON string for additional context
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<UserActivityLog(id={self.id}, user_id={self.user_id}, action='{self.action}')>"