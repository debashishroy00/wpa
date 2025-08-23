"""
WealthPath AI - Integration Tests for Critical User Flows
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import status


@pytest.mark.integration
class TestCompleteUserOnboarding:
    """Test complete user onboarding flow"""
    
    def test_full_onboarding_flow(self, client):
        """Test the complete onboarding process from registration to goal creation"""
        
        # Step 1: Register new user
        user_data = {
            "email": "onboarding@example.com",
            "password": "SecurePass123!",
            "full_name": "Onboarding User",
            "annual_income": 85000,
            "risk_tolerance": 6,
            "retirement_age": 65
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["id"]
        
        # Step 2: Login to get tokens
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Step 3: Add financial accounts
        accounts = [
            {
                "name": "Main Checking",
                "institution": "Bank of America",
                "account_type": "checking",
                "balance": 8000.00
            },
            {
                "name": "High Yield Savings",
                "institution": "Ally Bank",
                "account_type": "savings",
                "balance": 25000.00
            }
        ]
        account_ids = []
        for account in accounts:
            response = client.post("/api/v1/financial/accounts", json=account, headers=headers)
            assert response.status_code == status.HTTP_201_CREATED
            account_ids.append(response.json()["id"])
        
        # Step 4: Add income sources
        income_data = {
            "source": "Primary Job",
            "income_type": "salary",
            "amount": 7083.33,  # Monthly from 85k annual
            "frequency": "monthly",
            "is_active": True
        }
        income_response = client.post("/api/v1/financial/income", json=income_data, headers=headers)
        assert income_response.status_code == status.HTTP_201_CREATED
        
        # Step 5: Add expenses
        expenses = [
            {"category": "housing", "description": "Rent", "amount": 2000.00, "frequency": "monthly", "is_essential": True},
            {"category": "transportation", "description": "Car Payment", "amount": 450.00, "frequency": "monthly", "is_essential": True},
            {"category": "food", "description": "Groceries", "amount": 600.00, "frequency": "monthly", "is_essential": True},
            {"category": "entertainment", "description": "Subscriptions", "amount": 150.00, "frequency": "monthly", "is_essential": False}
        ]
        for expense in expenses:
            response = client.post("/api/v1/financial/expenses", json=expense, headers=headers)
            assert response.status_code == status.HTTP_201_CREATED
        
        # Step 6: Add assets
        asset_data = {
            "name": "401k",
            "asset_type": "retirement",
            "current_value": 45000.00,
            "purchase_price": 35000.00,
            "purchase_date": (datetime.now() - timedelta(days=730)).isoformat()
        }
        asset_response = client.post("/api/v1/financial/assets", json=asset_data, headers=headers)
        assert asset_response.status_code == status.HTTP_201_CREATED
        
        # Step 7: Check financial summary
        summary_response = client.get("/api/v1/financial/summary", headers=headers)
        assert summary_response.status_code == status.HTTP_200_OK
        summary = summary_response.json()
        assert float(summary["total_assets"]) == 78000.00  # 8000 + 25000 + 45000
        assert float(summary["monthly_income"]) == 7083.33
        assert float(summary["monthly_expenses"]) == 3200.00
        assert float(summary["monthly_cash_flow"]) > 0
        
        # Step 8: Check data quality score
        dq_response = client.get("/api/v1/financial/data-quality", headers=headers)
        assert dq_response.status_code == status.HTTP_200_OK
        dq_score = dq_response.json()
        assert dq_score["overall_score"] >= 75  # Good data quality
        
        # Step 9: Get goal templates
        templates_response = client.get("/api/v1/goal-templates/?goal_type=emergency_fund", headers=headers)
        assert templates_response.status_code == status.HTTP_200_OK
        templates = templates_response.json()
        assert len(templates) > 0
        
        # Step 10: Create financial goal based on template
        goal_data = {
            "goal_type": "emergency_fund",
            "name": "6-Month Emergency Fund",
            "description": "Build emergency savings",
            "target_amount": 19200.00,  # 6 months of expenses
            "current_amount": 5000.00,
            "target_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "priority": 1
        }
        goal_response = client.post("/api/v1/goals/", json=goal_data, headers=headers)
        assert goal_response.status_code == status.HTTP_201_CREATED
        goal = goal_response.json()
        assert "feasibility_score" in goal
        assert "success_probability" in goal
        assert "monthly_target" in goal
        
        # Step 11: Check goal progress
        progress_response = client.get(f"/api/v1/goals/{goal['id']}/progress", headers=headers)
        assert progress_response.status_code == status.HTTP_200_OK
        progress = progress_response.json()
        assert progress["progress_percentage"] > 0
        assert progress["required_monthly_contribution"] > 0


@pytest.mark.integration
class TestFinancialPlanningFlow:
    """Test complete financial planning workflow"""
    
    def test_financial_planning_with_multiple_goals(self, client, test_user, auth_headers, sample_financial_data, db_session):
        """Test creating and managing multiple financial goals with analysis"""
        
        # Step 1: Get current financial summary
        summary_response = client.get("/api/v1/financial/summary", headers=auth_headers)
        assert summary_response.status_code == status.HTTP_200_OK
        initial_summary = summary_response.json()
        monthly_cash_flow = float(initial_summary["monthly_cash_flow"])
        
        # Step 2: Request AI target suggestions for different goals
        goal_suggestions = []
        goal_types = ["emergency_fund", "home_purchase", "early_retirement"]
        
        for goal_type in goal_types:
            suggestion_request = {
                "goal_type": goal_type,
                "user_age": 35,
                "annual_income": float(test_user.annual_income),
                "current_savings": float(initial_summary["total_assets"]),
                "risk_tolerance": test_user.risk_tolerance
            }
            response = client.post(
                "/api/v1/goal-templates/suggest-target",
                json=suggestion_request,
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_200_OK
            goal_suggestions.append(response.json())
        
        # Step 3: Create goals based on suggestions
        created_goals = []
        for i, suggestion in enumerate(goal_suggestions):
            goal_data = {
                "goal_type": suggestion["goal_type"],
                "name": f"{suggestion['goal_type'].replace('_', ' ').title()} Goal",
                "description": f"AI-suggested {suggestion['goal_type']} goal",
                "target_amount": float(suggestion["suggested_amount"]),
                "current_amount": 0.00,
                "target_date": (datetime.now() + timedelta(days=suggestion["suggested_timeline_months"] * 30)).isoformat(),
                "priority": i + 1
            }
            response = client.post("/api/v1/goals/", json=goal_data, headers=auth_headers)
            assert response.status_code == status.HTTP_201_CREATED
            created_goals.append(response.json())
        
        # Step 4: Get analytics for all goals
        analytics_response = client.get("/api/v1/goals/analytics/summary", headers=auth_headers)
        assert analytics_response.status_code == status.HTTP_200_OK
        analytics = analytics_response.json()
        assert analytics["total_goals"] >= len(created_goals)
        assert analytics["active_goals"] >= len(created_goals)
        
        # Step 5: Analyze feasibility of all goals together
        total_monthly_required = sum(float(goal["monthly_target"]) for goal in created_goals if goal.get("monthly_target"))
        feasible = total_monthly_required <= monthly_cash_flow
        
        # Step 6: Prioritize goals if not all feasible
        if not feasible:
            # Update goal priorities based on importance
            priority_order = ["emergency_fund", "home_purchase", "early_retirement"]
            for goal in created_goals:
                priority = priority_order.index(goal["goal_type"]) + 1
                update_response = client.put(
                    f"/api/v1/goals/{goal['id']}",
                    json={"priority": priority},
                    headers=auth_headers
                )
                assert update_response.status_code == status.HTTP_200_OK
        
        # Step 7: Create scenarios for the highest priority goal
        high_priority_goal = min(created_goals, key=lambda g: g.get("priority", 999))
        analyze_response = client.post(
            f"/api/v1/goals/{high_priority_goal['id']}/analyze",
            headers=auth_headers
        )
        assert analyze_response.status_code == status.HTTP_200_OK
        
        scenarios_response = client.get(
            f"/api/v1/goals/{high_priority_goal['id']}/scenarios",
            headers=auth_headers
        )
        assert scenarios_response.status_code == status.HTTP_200_OK
        scenarios = scenarios_response.json()
        assert len(scenarios) >= 1  # At least baseline scenario


@pytest.mark.integration
class TestDataQualityImprovementFlow:
    """Test data quality improvement workflow"""
    
    def test_progressive_data_quality_improvement(self, client):
        """Test improving data quality score through progressive data entry"""
        
        # Setup: Create user and login
        user_data = {
            "email": "dataquality@example.com",
            "password": "QualityPass123!",
            "full_name": "Data Quality User"
        }
        client.post("/api/v1/auth/register", json=user_data)
        login_response = client.post("/api/v1/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # Step 1: Check initial data quality (should be low)
        dq_response = client.get("/api/v1/financial/data-quality", headers=headers)
        assert dq_response.status_code == status.HTTP_200_OK
        initial_dq = dq_response.json()
        assert initial_dq["overall_score"] == 0  # No data yet
        
        # Step 2: Add accounts (DQ1)
        account = {
            "name": "Checking Account",
            "institution": "Chase",
            "account_type": "checking",
            "balance": 5000.00
        }
        client.post("/api/v1/financial/accounts", json=account, headers=headers)
        
        dq_response = client.get("/api/v1/financial/data-quality", headers=headers)
        dq_after_accounts = dq_response.json()
        assert dq_after_accounts["dq1_accounts"] == 100
        assert dq_after_accounts["overall_score"] > initial_dq["overall_score"]
        
        # Step 3: Add income and expenses (DQ2)
        income = {
            "source": "Job",
            "income_type": "salary",
            "amount": 5000.00,
            "frequency": "monthly",
            "is_active": True
        }
        expense = {
            "category": "housing",
            "description": "Rent",
            "amount": 1500.00,
            "frequency": "monthly",
            "is_essential": True,
            "is_active": True
        }
        client.post("/api/v1/financial/income", json=income, headers=headers)
        client.post("/api/v1/financial/expenses", json=expense, headers=headers)
        
        dq_response = client.get("/api/v1/financial/data-quality", headers=headers)
        dq_after_income_expenses = dq_response.json()
        assert dq_after_income_expenses["dq2_income_expenses"] == 100
        assert dq_after_income_expenses["overall_score"] > dq_after_accounts["overall_score"]
        
        # Step 4: Add assets and liabilities (DQ3)
        asset = {
            "name": "Investment Portfolio",
            "asset_type": "stocks",
            "current_value": 20000.00,
            "purchase_price": 15000.00,
            "purchase_date": datetime.now().isoformat()
        }
        liability = {
            "name": "Student Loan",
            "liability_type": "student_loan",
            "current_balance": 10000.00,
            "original_amount": 25000.00,
            "interest_rate": 4.5,
            "minimum_payment": 250.00
        }
        client.post("/api/v1/financial/assets", json=asset, headers=headers)
        client.post("/api/v1/financial/liabilities", json=liability, headers=headers)
        
        dq_response = client.get("/api/v1/financial/data-quality", headers=headers)
        dq_after_assets_liabilities = dq_response.json()
        assert dq_after_assets_liabilities["dq3_assets_liabilities"] == 100
        assert dq_after_assets_liabilities["overall_score"] > dq_after_income_expenses["overall_score"]
        
        # Step 5: Add goals (DQ4)
        goal = {
            "goal_type": "emergency_fund",
            "name": "Emergency Savings",
            "target_amount": 15000.00,
            "current_amount": 2000.00,
            "target_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "priority": 1
        }
        client.post("/api/v1/goals/", json=goal, headers=headers)
        
        dq_response = client.get("/api/v1/financial/data-quality", headers=headers)
        final_dq = dq_response.json()
        assert final_dq["dq4_goals"] == 100
        assert final_dq["overall_score"] == 100  # Perfect score with all data


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceAndScaling:
    """Test performance with large datasets"""
    
    def test_handle_multiple_accounts_performance(self, client, test_user, auth_headers, db_session):
        """Test system performance with many financial accounts"""
        import time
        
        # Create 50 accounts
        start_time = time.time()
        for i in range(50):
            account = {
                "name": f"Account {i}",
                "institution": f"Bank {i % 10}",
                "account_type": ["checking", "savings", "investment"][i % 3],
                "balance": float(1000 + i * 100)
            }
            response = client.post("/api/v1/financial/accounts", json=account, headers=auth_headers)
            assert response.status_code == status.HTTP_201_CREATED
        
        creation_time = time.time() - start_time
        assert creation_time < 30  # Should complete within 30 seconds
        
        # Test retrieval performance
        start_time = time.time()
        response = client.get("/api/v1/financial/accounts", headers=auth_headers)
        retrieval_time = time.time() - start_time
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 50
        assert retrieval_time < 0.5  # Should retrieve in under 500ms
        
        # Test summary calculation performance
        start_time = time.time()
        response = client.get("/api/v1/financial/summary", headers=auth_headers)
        summary_time = time.time() - start_time
        
        assert response.status_code == status.HTTP_200_OK
        assert summary_time < 1.0  # Summary should calculate in under 1 second