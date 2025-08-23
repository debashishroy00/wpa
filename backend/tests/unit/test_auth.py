"""
WealthPath AI - Authentication Tests
"""
import pytest
from datetime import datetime, timedelta
from fastapi import status
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import verify_password, get_password_hash


@pytest.mark.auth
class TestAuthenticationEndpoints:
    """Test authentication endpoints"""
    
    def test_user_registration_success(self, client, random_user_data):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json=random_user_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == random_user_data["email"]
        assert data["full_name"] == random_user_data["full_name"]
        assert "id" in data
        assert "access_token" not in data  # Token only provided on login
    
    def test_user_registration_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,
            "password": "AnotherPassword123!",
            "full_name": "Another User"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()
    
    def test_user_registration_weak_password(self, client):
        """Test registration with weak password"""
        user_data = {
            "email": "weak@example.com",
            "password": "weak",
            "full_name": "Weak Password User"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_user_login_success(self, client, test_user):
        """Test successful user login"""
        login_data = {
            "username": test_user.email,
            "password": "TestPassword123!"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user.email
    
    def test_user_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        login_data = {
            "username": test_user.email,
            "password": "WrongPassword123!"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_user_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "Password123!"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_login_inactive_user(self, client, db_session):
        """Test login with inactive user"""
        inactive_user = User(
            email="inactive@example.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Inactive User",
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        login_data = {
            "username": inactive_user.email,
            "password": "Password123!"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "inactive" in response.json()["detail"].lower()
    
    def test_refresh_token_success(self, client, test_user):
        """Test refreshing access token"""
        # First login to get tokens
        login_data = {
            "username": test_user.email,
            "password": "TestPassword123!"
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        tokens = login_response.json()
        
        # Use refresh token to get new access token
        response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != tokens["access_token"]  # New token generated
    
    def test_get_current_user(self, client, auth_headers, test_user):
        """Test getting current user info"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["is_active"] is True
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_user_profile(self, client, auth_headers, test_user):
        """Test updating user profile"""
        update_data = {
            "full_name": "Updated Name",
            "annual_income": 100000,
            "risk_tolerance": 7,
            "retirement_age": 60
        }
        response = client.put("/api/v1/auth/me", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert float(data["annual_income"]) == update_data["annual_income"]
        assert data["risk_tolerance"] == update_data["risk_tolerance"]
        assert data["retirement_age"] == update_data["retirement_age"]
    
    def test_change_password(self, client, auth_headers):
        """Test changing user password"""
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword456!"
        }
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Password updated successfully"
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test changing password with wrong current password"""
        password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword456!"
        }
        response = client.post("/api/v1/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_logout(self, client, auth_headers):
        """Test user logout"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Successfully logged out"


@pytest.mark.auth
class TestPasswordSecurity:
    """Test password security functions"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False
    
    def test_password_complexity_requirements(self, client):
        """Test password complexity validation"""
        test_cases = [
            ("short", False),  # Too short
            ("NoDigitsHere!", False),  # No digits
            ("no_uppercase123!", False),  # No uppercase
            ("NO_LOWERCASE123!", False),  # No lowercase
            ("NoSpecialChars123", False),  # No special characters
            ("ValidPassword123!", True),  # Valid password
        ]
        
        for password, should_succeed in test_cases:
            user_data = {
                "email": f"test_{password}@example.com",
                "password": password,
                "full_name": "Test User"
            }
            response = client.post("/api/v1/auth/register", json=user_data)
            if should_succeed:
                assert response.status_code == status.HTTP_201_CREATED
            else:
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY