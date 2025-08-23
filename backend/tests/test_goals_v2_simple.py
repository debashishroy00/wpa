"""
WealthPath AI - Goals V2 API Tests
Basic tests for goal management endpoints
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from fastapi import status

from app.models.goals_v2 import Goal


class TestGoalsV2API:
    """Test cases for Goals V2 API endpoints"""

    def test_get_goals_summary(self, client, auth_headers):
        """Test getting goals summary"""
        response = client.get("/api/v1/goals/summary", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "active_goals" in data
        assert "achieved_goals" in data
        assert "total_target" in data
        assert "average_progress" in data

    def test_get_goal_categories(self, client):
        """Test getting available goal categories"""
        response = client.get("/api/v1/categories")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "retirement" in data
        assert "education" in data
        assert "real_estate" in data

    def test_get_goal_templates(self, client):
        """Test getting goal templates"""
        response = client.get("/api/v1/templates")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_create_goal(self, client, auth_headers):
        """Test creating a new goal"""
        goal_data = {
            "category": "retirement",
            "name": "Test Retirement Fund",
            "description": "Long-term retirement savings",
            "target_amount": 1000000.00,
            "target_date": "2055-12-31",
            "priority": 1,
            "params": {
                "retirement_age": 65,
                "annual_spending": 50000,
                "current_age": 30
            }
        }
        
        response = client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == goal_data["name"]
        assert data["category"] == goal_data["category"]
        assert float(data["target_amount"]) == goal_data["target_amount"]
        assert data["status"] == "active"

    def test_get_goals(self, client, auth_headers):
        """Test retrieving user goals"""
        response = client.get("/api/v1/goals", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_create_goal_validation_errors(self, client, auth_headers):
        """Test goal creation validation"""
        # Test missing required fields
        invalid_goal = {
            "category": "retirement",
            # Missing name, target_amount, etc.
        }
        
        response = client.post(
            "/api/v1/goals",
            json=invalid_goal,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_goal(self, client, auth_headers, test_goal_v2):
        """Test updating an existing goal"""
        goal_id = str(test_goal_v2.goal_id)
        
        update_data = {
            "name": "Updated Retirement Fund",
            "target_amount": 1200000.00,
            "change_reason": "Increased target due to inflation"
        }
        
        response = client.put(
            f"/api/v1/goals/{goal_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert float(data["target_amount"]) == update_data["target_amount"]

    def test_record_progress(self, client, auth_headers, test_goal_v2):
        """Test recording progress towards a goal"""
        goal_id = str(test_goal_v2.goal_id)
        
        progress_data = {
            "current_amount": 50000.00,
            "notes": "Monthly contribution"
        }
        
        response = client.post(
            f"/api/v1/goals/{goal_id}/progress",
            json=progress_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert float(data["current_amount"]) == progress_data["current_amount"]

    def test_get_goal_progress(self, client, auth_headers, test_goal_v2):
        """Test retrieving goal progress history"""
        goal_id = str(test_goal_v2.goal_id)
        
        response = client.get(
            f"/api/v1/goals/{goal_id}/progress",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_delete_goal(self, client, auth_headers, test_goal_v2):
        """Test deleting a goal (soft delete)"""
        goal_id = str(test_goal_v2.goal_id)
        
        response = client.delete(
            f"/api/v1/goals/{goal_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify goal is marked as cancelled
        get_response = client.get(
            f"/api/v1/goals/{goal_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["status"] == "cancelled"

    def test_user_preferences(self, client, auth_headers):
        """Test user preferences management"""
        # Test getting default preferences
        response = client.get("/api/v1/preferences", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Test updating preferences
        update_data = {
            "risk_tolerance": "moderate",
            "investment_experience": "intermediate",
            "time_horizon": "long_term",
            "liquidity_needs": "low"
        }
        
        response = client.put(
            "/api/v1/preferences",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["risk_tolerance"] == update_data["risk_tolerance"]

    def test_batch_update_goals(self, client, auth_headers, test_goals_v2):
        """Test batch updating multiple goals"""
        goal_ids = [str(goal.goal_id) for goal in test_goals_v2[:2]]
        
        batch_data = {
            "goal_ids": goal_ids,
            "updates": {
                "priority": 2
            },
            "batch_reason": "Adjusting priorities"
        }
        
        response = client.put(
            "/api/v1/goals/batch",
            json=batch_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        for goal in data:
            assert goal["priority"] == 2