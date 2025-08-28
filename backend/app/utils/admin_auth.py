"""
Admin Authentication Utilities - Safe and Non-Invasive
This module provides admin access verification without affecting existing auth
"""
import structlog
import os
from typing import Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

logger = structlog.get_logger()

def verify_admin_access(email: Optional[str]) -> bool:
    """
    Verify if user has admin access (safe implementation)
    Defaults to False if any error occurs
    """
    try:
        if not email:
            return False
        
        # Get admin emails from environment variable or use empty list
        admin_emails_str = os.getenv('ADMIN_EMAILS', '')
        admin_emails = [e.strip().lower() for e in admin_emails_str.split(',') if e.strip()]
        
        is_admin = email.lower() in admin_emails
        
        if is_admin:
            logger.info("Admin access verified", email=email)
        else:
            logger.info("Admin access denied", email=email)
            
        return is_admin
        
    except Exception as e:
        # Fail safely - if there's any error, assume not admin
        logger.error("Admin verification failed safely", email=email, error=str(e))
        return False

def get_admin_role(email: Optional[str]) -> str:
    """
    Get role for user (safe implementation)
    Returns 'admin' or 'user'
    """
    try:
        return 'admin' if verify_admin_access(email) else 'user'
    except Exception:
        return 'user'

def is_admin_feature_enabled() -> bool:
    """
    Check if admin features should be available
    Can be extended with environment variables or feature flags
    """
    try:
        # Could check environment variables here if needed
        # For now, always enabled
        return True
    except Exception:
        return False

def require_admin(current_user=None):
    """
    FastAPI dependency to require admin access
    Returns the user if they have admin access, raises HTTPException otherwise
    """
    try:
        # If no user provided, check for admin emails in environment
        if current_user is None:
            admin_emails_str = os.getenv('ADMIN_EMAILS', '')
            if not admin_emails_str:
                raise HTTPException(status_code=403, detail="Admin access required")
            return None  # Allow if admin emails are configured
        
        # If user object provided, check their email
        user_email = getattr(current_user, 'email', None)
        if not user_email:
            raise HTTPException(status_code=403, detail="Admin access required - no email")
            
        if not verify_admin_access(user_email):
            raise HTTPException(status_code=403, detail="Admin access required")
            
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Admin check failed", error=str(e))
        raise HTTPException(status_code=403, detail="Admin access required")