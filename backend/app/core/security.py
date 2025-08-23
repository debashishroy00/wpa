"""
WealthPath AI - Security and Authentication
"""
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
import secrets
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
ALGORITHM = settings.JWT_ALGORITHM


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.utcnow(),
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=ALGORITHM
    )
    
    logger.info("Access token created", subject=str(subject), expires_at=expire)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    # Add random jti for token blacklisting capability
    jti = secrets.token_urlsafe(32)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.utcnow(),
        "jti": jti,
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=ALGORITHM
    )
    
    logger.info("Refresh token created", subject=str(subject), jti=jti, expires_at=expire)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Verify JWT token and return subject
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        
        # Check token type
        if payload.get("type") != token_type:
            logger.warning("Invalid token type", expected=token_type, actual=payload.get("type"))
            return None
        
        # Get subject
        subject = payload.get("sub")
        if subject is None:
            logger.warning("Token missing subject")
            return None
        
        logger.debug("Token verified successfully", subject=subject, type=token_type)
        return str(subject)
    
    except JWTError as e:
        logger.warning("JWT verification failed", error=str(e), token_type=token_type)
        return None


def get_password_hash(password: str) -> str:
    """
    Hash password using bcrypt
    """
    hashed = pwd_context.hash(password)
    logger.debug("Password hashed successfully")
    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    """
    is_valid = pwd_context.verify(plain_password, hashed_password)
    logger.debug("Password verification", is_valid=is_valid)
    return is_valid


def generate_password_reset_token(email: str) -> str:
    """
    Generate password reset token
    """
    delta = timedelta(hours=24)  # 24 hour expiry for reset tokens
    expire = datetime.utcnow() + delta
    
    to_encode = {
        "exp": expire,
        "sub": email,
        "type": "password_reset",
        "iat": datetime.utcnow(),
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=ALGORITHM
    )
    
    logger.info("Password reset token created", email=email, expires_at=expire)
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token and return email
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        
        # Check token type
        if payload.get("type") != "password_reset":
            logger.warning("Invalid password reset token type")
            return None
        
        email = payload.get("sub")
        if email is None:
            logger.warning("Password reset token missing email")
            return None
        
        logger.info("Password reset token verified", email=email)
        return str(email)
    
    except JWTError as e:
        logger.warning("Password reset token verification failed", error=str(e))
        return None


def create_api_key() -> str:
    """
    Generate secure API key
    """
    api_key = secrets.token_urlsafe(32)
    logger.info("API key generated")
    return api_key


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength and return requirements status
    """
    requirements = {
        "min_length": len(password) >= 8,
        "has_uppercase": any(c.isupper() for c in password),
        "has_lowercase": any(c.islower() for c in password),
        "has_digit": any(c.isdigit() for c in password),
        "has_special": any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password),
    }
    
    is_valid = all(requirements.values())
    
    return {
        "is_valid": is_valid,
        "requirements": requirements,
        "score": sum(requirements.values()) / len(requirements) * 100
    }


class SecurityError(HTTPException):
    """
    Custom security exception
    """
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=detail)


class TokenExpiredError(SecurityError):
    """
    Token expired exception
    """
    def __init__(self):
        super().__init__(
            detail="Token has expired", 
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class InvalidTokenError(SecurityError):
    """
    Invalid token exception
    """
    def __init__(self):
        super().__init__(
            detail="Invalid token", 
            status_code=status.HTTP_401_UNAUTHORIZED
        )