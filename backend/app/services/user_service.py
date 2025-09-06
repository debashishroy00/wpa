"""
WealthPath AI - User Service
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
import structlog

from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.auth import UserRegister
from app.core.security import get_password_hash, verify_password

logger = structlog.get_logger()


class UserService:
    """
    Service class for user operations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                logger.debug("User retrieved by ID", user_id=user_id)
            return user
        except Exception as e:
            logger.error("Error retrieving user by ID", user_id=user_id, error=str(e))
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address
        """
        try:
            user = self.db.query(User).filter(User.email == email.lower()).first()
            if user:
                logger.debug("User retrieved by email", email=email)
            return user
        except Exception as e:
            logger.error("Error retrieving user by email", email=email, error=str(e))
            return None
    
    def create_user(self, user_data: UserRegister) -> User:
        """
        Create new user account
        """
        try:
            # Hash password
            hashed_password = get_password_hash(user_data.password)
            
            # Create user
            db_user = User(
                email=user_data.email.lower(),
                password_hash=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                is_active=True
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            # Create user profile
            self.create_user_profile(db_user.id)
            
            logger.info("User created successfully", user_id=db_user.id, email=user_data.email)
            return db_user
        
        except Exception as e:
            logger.error("Error creating user", email=user_data.email, error=str(e))
            self.db.rollback()
            raise e
    
    def create_user_profile(self, user_id: int) -> UserProfile:
        """
        Create default user profile
        """
        try:
            db_profile = UserProfile(
                user_id=user_id,
                risk_tolerance="moderate",
                risk_tolerance_score=5
            )
            
            self.db.add(db_profile)
            self.db.commit()
            self.db.refresh(db_profile)
            
            logger.info("User profile created", user_id=user_id)
            return db_profile
        
        except Exception as e:
            logger.error("Error creating user profile", user_id=user_id, error=str(e))
            self.db.rollback()
            raise e
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password
        """
        try:
            user = self.get_user_by_email(email)
            if not user:
                logger.warning("Authentication failed - user not found", email=email)
                return None
            
            if not verify_password(password, user.password_hash):
                logger.warning("Authentication failed - invalid password", email=email)
                return None
            
            logger.info("User authenticated successfully", user_id=user.id, email=email)
            return user
        
        except Exception as e:
            logger.error("Error during authentication", email=email, error=str(e))
            return None
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """
        Update user information
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.warning("Update failed - user not found", user_id=user_id)
                return None
            
            # Update fields
            if user_update.first_name is not None:
                user.first_name = user_update.first_name
            if user_update.last_name is not None:
                user.last_name = user_update.last_name
            if user_update.phone_number is not None:
                user.phone_number = user_update.phone_number
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info("User updated successfully", user_id=user_id)
            return user
        
        except Exception as e:
            logger.error("Error updating user", user_id=user_id, error=str(e))
            self.db.rollback()
            return None
    
    def update_user_password(self, user_id: int, new_password_hash: str) -> bool:
        """
        Update user password
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.warning("Password update failed - user not found", user_id=user_id)
                return False
            
            user.password_hash = new_password_hash
            self.db.commit()
            
            logger.info("User password updated successfully", user_id=user_id)
            return True
        
        except Exception as e:
            logger.error("Error updating user password", user_id=user_id, error=str(e))
            self.db.rollback()
            return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate user account
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.warning("Deactivation failed - user not found", user_id=user_id)
                return False
            
            user.is_active = False
            self.db.commit()
            
            logger.info("User deactivated successfully", user_id=user_id)
            return True
        
        except Exception as e:
            logger.error("Error deactivating user", user_id=user_id, error=str(e))
            self.db.rollback()
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete user account (GDPR compliance)
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.warning("Deletion failed - user not found", user_id=user_id)
                return False
            
            # In production, this should be a soft delete or data anonymization
            # For GDPR compliance, we need to handle related data properly
            user.is_active = False
            user.status = "deleted"
            user.email = f"deleted_{user.id}@wealthpath.deleted"
            
            self.db.commit()
            
            logger.info("User marked for deletion", user_id=user_id)
            return True
        
        except Exception as e:
            logger.error("Error deleting user", user_id=user_id, error=str(e))
            self.db.rollback()
            return False
    
    def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """
        Get user profile
        """
        try:
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile:
                logger.debug("User profile retrieved", user_id=user_id)
            return profile
        
        except Exception as e:
            logger.error("Error retrieving user profile", user_id=user_id, error=str(e))
            return None
    
    def update_user_profile(self, user_id: int, profile_data: dict) -> Optional[UserProfile]:
        """
        Update user profile
        """
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                logger.warning("Profile update failed - profile not found", user_id=user_id)
                return None
            
            # Update profile fields
            for key, value in profile_data.items():
                if hasattr(profile, key) and value is not None:
                    setattr(profile, key, value)
            
            self.db.commit()
            self.db.refresh(profile)
            
            logger.info("User profile updated successfully", user_id=user_id)
            return profile
        
        except Exception as e:
            logger.error("Error updating user profile", user_id=user_id, error=str(e))
            self.db.rollback()
            return None
    
    def is_email_available(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if email is available for use
        """
        try:
            query = self.db.query(User).filter(User.email == email.lower())
            if exclude_user_id:
                query = query.filter(User.id != exclude_user_id)
            
            existing_user = query.first()
            return existing_user is None
        
        except Exception as e:
            logger.error("Error checking email availability", email=email, error=str(e))
            return False