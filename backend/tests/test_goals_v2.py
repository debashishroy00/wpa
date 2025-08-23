"""
WealthPath AI - Goals V2 API Tests
Comprehensive tests for goal management endpoints
"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import status

from app.models.goals_v2 import Goal, GoalProgress, UserPreferences
from app.schemas.goals_v2 import GoalCategory, GoalStatus


class TestGoalsAPI:
    """Test cases for Goals V2 API endpoints"""

    def test_create_goal(self, client: TestClient, auth_headers: dict):
        """Test creating a new goal"""
        goal_data = {
            "category": "retirement",
            "name": "Retirement Fund",
            "description": "Long-term retirement savings",
            "target_amount": 1000000.00,
            "target_date": "2045-12-31",
            "priority": 1,
            "params": {
                "retirement_age": 65,
                "annual_spending": 50000,
                "current_age": 30
            }
        }
        
        response = await client.post(
            "/api/v1/goals",
            json=goal_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == goal_data["name"]
        assert data["category"] == goal_data["category"]
        assert Decimal(data["target_amount"]) == Decimal(str(goal_data["target_amount"]))
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_goals(self, client: AsyncClient, auth_headers: dict):
        """Test retrieving user goals"""
        response = await client.get("/api/v1/goals", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_goals_summary(self, client: AsyncClient, auth_headers: dict):
        """Test getting goals summary"""
        response = await client.get("/api/v1/goals/summary", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "active_goals" in data
        assert "achieved_goals" in data
        assert "total_target" in data
        assert "average_progress" in data

    @pytest.mark.asyncio
    async def test_get_goal_conflicts(self, client: AsyncClient, auth_headers: dict):
        """Test getting goal conflicts analysis"""
        response = await client.get("/api/v1/goals/analysis/conflicts", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_goal_categories(self, client: AsyncClient):
        """Test getting available goal categories"""
        response = await client.get("/api/v1/categories")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "retirement" in data
        assert "education" in data
        assert "real_estate" in data

    @pytest.mark.asyncio
    async def test_get_goal_templates(self, client: AsyncClient):
        """Test getting goal templates"""
        response = await client.get("/api/v1/templates")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_create_goal_validation_errors(self, client: AsyncClient, auth_headers: dict):
        """Test goal creation validation"""
        # Test missing required fields
        invalid_goal = {
            "category": "retirement",
            # Missing name, target_amount, etc.
        }
        
        response = await client.post(
            "/api/v1/goals",
            json=invalid_goal,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_goal(self, client: TestClient, auth_headers: dict, test_goal_v2):
        """Test updating an existing goal"""
        goal_id = test_goal_v2.goal_id
        
        update_data = {
            "name": "Updated Retirement Fund",
            "target_amount": 1200000.00,
            "change_reason": "Increased target due to inflation"
        }
        
        response = await client.put(
            f"/api/v1/goals/{goal_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert Decimal(data["target_amount"]) == Decimal(str(update_data["target_amount"]))

    @pytest.mark.asyncio
    async def test_record_progress(self, client: AsyncClient, auth_headers: dict, test_goal):
        """Test recording progress towards a goal"""
        goal_id = test_goal.goal_id
        
        progress_data = {
            "current_amount": 50000.00,
            "notes": "Monthly contribution"
        }
        
        response = await client.post(
            f"/api/v1/goals/{goal_id}/progress",
            json=progress_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert Decimal(data["current_amount"]) == Decimal(str(progress_data["current_amount"]))

    @pytest.mark.asyncio
    async def test_get_goal_progress(self, client: AsyncClient, auth_headers: dict, test_goal):
        """Test retrieving goal progress history"""
        goal_id = test_goal.goal_id
        
        response = await client.get(
            f"/api/v1/goals/{goal_id}/progress",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_delete_goal(self, client: AsyncClient, auth_headers: dict, test_goal):
        """Test deleting a goal (soft delete)"""
        goal_id = test_goal.goal_id
        
        response = await client.delete(
            f"/api/v1/goals/{goal_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify goal is marked as cancelled
        get_response = await client.get(
            f"/api/v1/goals/{goal_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_user_preferences(self, client: AsyncClient, auth_headers: dict):
        """Test user preferences management"""
        # Test getting default preferences
        response = await client.get("/api/v1/preferences", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Test updating preferences
        update_data = {
            "risk_tolerance": "moderate",
            "investment_experience": "intermediate",
            "time_horizon": "long_term",
            "liquidity_needs": "low"
        }
        
        response = await client.put(
            "/api/v1/preferences",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["risk_tolerance"] == update_data["risk_tolerance"]

    @pytest.mark.asyncio
    async def test_batch_update_goals(self, client: AsyncClient, auth_headers: dict, test_goals):
        """Test batch updating multiple goals"""
        goal_ids = [str(goal.goal_id) for goal in test_goals[:2]]
        
        batch_data = {
            "goal_ids": goal_ids,
            "updates": {
                "priority": 2
            },
            "batch_reason": "Adjusting priorities"
        }
        
        response = await client.put(
            "/api/v1/goals/batch",
            json=batch_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        for goal in data:
            assert goal["priority"] == 2

    @pytest.mark.asyncio
    async def test_goal_history_audit_trail(self, client: AsyncClient, auth_headers: dict, test_goal):
        """Test goal history and audit trail"""
        goal_id = test_goal.goal_id
        
        # Make an update to create history
        await client.put(
            f"/api/v1/goals/{goal_id}",
            json={"name": "Updated Goal Name", "change_reason": "Testing audit trail"},
            headers=auth_headers
        )
        
        # Get history
        response = await client.get(
            f"/api/v1/goals/{goal_id}/history",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestGoalValidation:
    """Test cases for goal validation logic"""

    def test_retirement_goal_validation(self):
        """Test retirement goal parameter validation"""
        from app.schemas.goals_v2 import GoalCreate
        
        # Valid retirement goal
        valid_data = {
            "category": "retirement",
            "name": "Test Retirement",
            "target_amount": 1000000,
            "target_date": date.today() + timedelta(days=365*30),
            "params": {
                "retirement_age": 65,
                "annual_spending": 50000,
                "current_age": 30
            }
        }
        
        goal = GoalCreate(**valid_data)
        assert goal.category == "retirement"
        assert goal.params["retirement_age"] == 65

    def test_education_goal_validation(self):
        """Test education goal parameter validation"""
        from app.schemas.goals_v2 import GoalCreate
        
        valid_data = {
            "category": "education",
            "name": "College Fund",
            "target_amount": 200000,
            "target_date": date.today() + timedelta(days=365*10),
            "params": {
                "degree_type": "undergraduate",
                "institution_type": "public",
                "start_year": 2030
            }
        }
        
        goal = GoalCreate(**valid_data)
        assert goal.category == "education"
        assert goal.params["degree_type"] == "undergraduate"


class TestGoalCalculations:
    """Test cases for goal calculation logic"""

    def test_progress_percentage_calculation(self, db_session, test_user):
        """Test progress percentage calculation"""
        # Create goal
        goal = Goal(
            user_id=test_user.id,
            category="retirement",
            name="Test Goal",
            target_amount=Decimal("100000.00"),
            target_date=date.today() + timedelta(days=365*5)
        )
        db_session.add(goal)
        db_session.commit()
        
        # Add progress
        progress = GoalProgress(
            goal_id=goal.goal_id,
            current_amount=Decimal("25000.00"),
            percentage_complete=Decimal("25.00")
        )
        db_session.add(progress)
        db_session.commit()
        
        # Test calculation
        assert goal.progress_percentage == Decimal("25.00")