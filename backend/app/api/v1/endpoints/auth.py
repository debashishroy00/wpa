"""
WealthPath AI - Authentication Endpoints
"""
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import structlog

from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, TokenData, UserLogin, UserRegister
from app.schemas.user import UserResponse
from app.services.user_service import UserService

logger = structlog.get_logger()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        user_id = security.verify_token(token, "access")
        if user_id is None:
            raise credentials_exception
        
        # Get user from database
        user_service = UserService(db)
        user = user_service.get_user_by_id(int(user_id))
        if user is None:
            raise credentials_exception
        
        return user
    
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise credentials_exception


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user (not suspended/deleted)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register new user
    """
    user_service = UserService(db)
    
    # Check if user already exists
    existing_user = user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Validate password strength
    password_validation = security.validate_password_strength(user_data.password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Password does not meet security requirements",
                "requirements": password_validation["requirements"]
            }
        )
    
    # Create user
    try:
        user = user_service.create_user(user_data)
        logger.info("User registered successfully", user_id=user.id, email=user.email)
        return user
    
    except Exception as e:
        logger.error("User registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user_service = UserService(db)
    
    # Authenticate user
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning("Login attempt failed", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = security.create_access_token(
        subject=user.id, 
        expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(
        subject=user.id, 
        expires_delta=refresh_token_expires
    )
    
    logger.info("User logged in successfully", user_id=user.id, email=user.email)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    token_data: TokenData,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token
    """
    # Verify refresh token
    user_id = security.verify_token(token_data.token, "refresh")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user_service = UserService(db)
    user = user_service.get_user_by_id(int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    new_access_token = security.create_access_token(
        subject=user.id, 
        expires_delta=access_token_expires
    )
    new_refresh_token = security.create_refresh_token(
        subject=user.id, 
        expires_delta=refresh_token_expires
    )
    
    logger.info("Tokens refreshed successfully", user_id=user.id)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }


@router.post("/logout")
def logout(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    Logout user (in future versions, this will blacklist the token)
    """
    logger.info("User logged out", user_id=current_user.id, email=current_user.email)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    Get current user information
    """
    return current_user


@router.post("/password-reset-request")
def request_password_reset(
    email: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Request password reset (sends email with reset token)
    """
    user_service = UserService(db)
    user = user_service.get_user_by_email(email)
    
    if user:
        # Generate reset token
        reset_token = security.generate_password_reset_token(email)
        
        # In production, send email with reset link
        # For now, we'll just log it (development only)
        logger.info("Password reset requested", email=email, token=reset_token)
        
        # Always return success to prevent email enumeration
        return {"message": "Password reset email sent if account exists"}
    
    # Return same message even if user doesn't exist (security)
    logger.warning("Password reset requested for non-existent user", email=email)
    return {"message": "Password reset email sent if account exists"}


@router.post("/password-reset")
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Reset password using reset token
    """
    # Verify reset token
    email = security.verify_password_reset_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Validate new password
    password_validation = security.validate_password_strength(new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Password does not meet security requirements",
                "requirements": password_validation["requirements"]
            }
        )
    
    # Update password
    user_service = UserService(db)
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    hashed_password = security.get_password_hash(new_password)
    user_service.update_user_password(user.id, hashed_password)
    
    logger.info("Password reset successfully", user_id=user.id, email=email)
    return {"message": "Password reset successfully"}