"""
WealthPath AI - Goal Management Tests
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import status

from app.models.goal import GoalType, GoalStatus


@pytest.mark.goals
class TestGoalManagementEndpoints:
    """Test goal management endpoints"""
    
    def test_create_goal(self, client, auth_headers, random_goal):
        """Test creating a financial goal"""
        response = client.post(
            "/api/v1/goals/",
            json=random_goal,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == random_goal["name"]
        assert data["goal_type"] == random_goal["goal_type"]
        assert float(data["target_amount"]) == random_goal["target_amount"]
        assert "feasibility_score" in data
        assert "success_probability" in data
        assert "risk_level" in data
    
    def test_get_goals(self, client, auth_headers, sample_goal):
        """Test getting all user goals"""
        response = client.get("/api/v1/goals/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(goal["id"] == sample_goal.id for goal in data)
    
    def test_get_goal_by_id(self, client, auth_headers, sample_goal):
        """Test getting specific goal"""
        response = client.get(f"/api/v1/goals/{sample_goal.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_goal.id
        assert data["name"] == sample_goal.name
        assert float(data["target_amount"]) == float(sample_goal.target_amount)
    
    def test_update_goal(self, client, auth_headers, sample_goal):
        """Test updating goal"""
        update_data = {
            "current_amount": 10000.00,
            "status": "active"
        }
        response = client.put(
            f"/api/v1/goals/{sample_goal.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert float(data["current_amount"]) == update_data["current_amount"]
        assert data["status"] == update_data["status"]
    
    def test_delete_goal(self, client, auth_headers, sample_goal):
        """Test deleting goal (soft delete)"""
        response = client.delete(f"/api/v1/goals/{sample_goal.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Verify goal is marked as abandoned
        get_response = client.get(f"/api/v1/goals/{sample_goal.id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["status"] == "abandoned"
    
    def test_filter_goals_by_status(self, client, auth_headers, test_user, db_session):
        """Test filtering goals by status"""
        # Create multiple goals with different statuses
        goals = [
            {"status": GoalStatus.active, "name": "Active Goal"},
            {"status": GoalStatus.draft, "name": "Draft Goal"},
            {"status": GoalStatus.paused, "name": "Paused Goal"}
        ]
        
        for goal_data in goals:
            goal = FinancialGoal(
                user_id=test_user.id,
                goal_type=GoalType.emergency_fund,
                name=goal_data["name"],
                target_amount=Decimal("10000.00"),
                current_amount=Decimal("0.00"),
                target_date=datetime.now() + timedelta(days=365),
                status=goal_data["status"]
            )
            db_session.add(goal)
        db_session.commit()
        
        # Test filtering by active status
        response = client.get("/api/v1/goals/?status=active", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(goal["status"] == "active" for goal in data)
    
    def test_filter_goals_by_type(self, client, auth_headers, test_user, db_session):
        """Test filtering goals by type"""
        # Create goals of different types
        goal_types = [GoalType.early_retirement, GoalType.home_purchase, GoalType.education]
        
        for goal_type in goal_types:
            goal = FinancialGoal(
                user_id=test_user.id,
                goal_type=goal_type,
                name=f"{goal_type.value} Goal",
                target_amount=Decimal("50000.00"),
                current_amount=Decimal("0.00"),
                target_date=datetime.now() + timedelta(days=730),
                status=GoalStatus.active
            )
            db_session.add(goal)
        db_session.commit()
        
        # Test filtering by home_purchase type
        response = client.get("/api/v1/goals/?goal_type=home_purchase", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(goal["goal_type"] == "home_purchase" for goal in data)


@pytest.mark.goals
class TestGoalAnalytics:
    """Test goal analytics and progress endpoints"""
    
    def test_get_goal_analytics(self, client, auth_headers, sample_goal):
        """Test getting goal analytics summary"""
        response = client.get("/api/v1/goals/analytics/summary", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "total_goals" in data
        assert "active_goals" in data
        assert "achieved_goals" in data
        assert "total_target_amount" in data
        assert "total_current_amount" in data
        assert "overall_progress" in data
        assert "goals_on_track" in data
        assert "high_risk_goals" in data
        assert "average_feasibility" in data
        
        assert data["total_goals"] >= 1  # At least the sample goal
    
    def test_get_goal_progress(self, client, auth_headers, sample_goal):
        """Test getting goal progress details"""
        response = client.get(f"/api/v1/goals/{sample_goal.id}/progress", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "progress_percentage" in data
        assert "current_amount" in data
        assert "target_amount" in data
        assert "remaining_amount" in data
        assert "days_remaining" in data
        assert "months_remaining" in data
        assert "required_monthly_contribution" in data
        assert "is_on_track" in data
        
        # Verify calculations
        assert float(data["remaining_amount"]) == float(sample_goal.target_amount - sample_goal.current_amount)
        assert data["days_remaining"] > 0
    
    def test_get_goal_scenarios(self, client, auth_headers, sample_goal):
        """Test getting goal scenarios"""
        response = client.get(f"/api/v1/goals/{sample_goal.id}/scenarios", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should have at least baseline scenario
        assert len(data) >= 1
        baseline = next((s for s in data if s["is_baseline"]), None)
        assert baseline is not None
        assert baseline["scenario_name"] == "Baseline Projection"
    
    def test_trigger_goal_analysis(self, client, auth_headers, sample_goal):
        """Test triggering goal analysis"""
        response = client.post(f"/api/v1/goals/{sample_goal.id}/analyze", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["goal_id"] == sample_goal.id
        assert data["analysis_completed"] is True
        assert "feasibility_score" in data
        assert "success_probability" in data
        assert "risk_level" in data
        assert "analyzed_at" in data


@pytest.mark.goals
class TestGoalTemplates:
    """Test goal template endpoints"""
    
    def test_get_goal_templates(self, client, auth_headers):
        """Test getting all goal templates"""
        response = client.get("/api/v1/goal-templates/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data) > 0
        # Check template structure
        for template in data:
            assert "id" in template
            assert "template_type" in template
            assert "name" in template
            assert "description" in template
            assert "suggested_timeline_months" in template
            assert "default_parameters" in template
            assert "calculation_rules" in template
    
    def test_get_template_by_id(self, client, auth_headers):
        """Test getting specific goal template"""
        template_id = "emergency_fund_6_months"
        response = client.get(f"/api/v1/goal-templates/{template_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == template_id
        assert data["template_type"] == "emergency_fund"
        assert "6-Month" in data["name"]
    
    def test_filter_templates_by_type(self, client, auth_headers):
        """Test filtering templates by goal type"""
        response = client.get(
            "/api/v1/goal-templates/?goal_type=home_purchase",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data) > 0
        assert all(t["template_type"] == "home_purchase" for t in data)
    
    def test_filter_templates_by_difficulty(self, client, auth_headers):
        """Test filtering templates by difficulty"""
        response = client.get(
            "/api/v1/goal-templates/?difficulty_level=beginner",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data) > 0
        assert all(t["difficulty_level"] == "beginner" for t in data)
    
    def test_get_popular_templates(self, client, auth_headers):
        """Test getting popular templates only"""
        response = client.get(
            "/api/v1/goal-templates/?popular_only=true",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data) > 0
        assert all(t["is_popular"] is True for t in data)
    
    def test_suggest_goal_target(self, client, auth_headers):
        """Test AI-powered target suggestion"""
        request_data = {
            "goal_type": "home_purchase",
            "user_age": 30,
            "annual_income": 75000,
            "current_savings": 15000,
            "risk_tolerance": 6
        }
        response = client.post(
            "/api/v1/goal-templates/suggest-target",
            json=request_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["goal_type"] == request_data["goal_type"]
        assert "suggested_amount" in data
        assert "suggested_timeline_months" in data
        assert "confidence_score" in data
        assert "reasoning" in data
        assert "assumptions" in data
        assert "alternative_scenarios" in data
        
        # Check alternative scenarios
        assert len(data["alternative_scenarios"]) >= 2
        for scenario in data["alternative_scenarios"]:
            assert "name" in scenario
            assert "timeline_months" in scenario
            assert "monthly_required" in scenario
            assert "success_probability" in scenario
    
    def test_get_template_categories(self, client, auth_headers):
        """Test getting template categories"""
        response = client.get("/api/v1/goal-templates/categories/list", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "categories" in data
        assert "goal_types" in data
        assert "difficulty_levels" in data
        
        assert len(data["categories"]) > 0
        assert len(data["goal_types"]) > 0
        assert "beginner" in data["difficulty_levels"]
        assert "intermediate" in data["difficulty_levels"]
        assert "advanced" in data["difficulty_levels"]


# Import necessary models for tests
from app.models.goal import FinancialGoal