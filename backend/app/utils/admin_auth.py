"""
Admin Authentication Utilities - Safe and Non-Invasive
This module provides admin access verification without affecting existing auth
"""
import structlog
from typing import Optional

logger = structlog.get_logger()

def verify_admin_access(email: Optional[str]) -> bool:
    """
    Verify if user has admin access (safe implementation)
    Defaults to False if any error occurs
    """
    try:
        if not email:
            return False
        
        # For now, hardcode debashishroy@gmail.com as admin as requested
        admin_emails = ['debashishroy@gmail.com']
        
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