"""
WealthPath AI - Financial Data Tests
"""
import pytest
from datetime import datetime
from decimal import Decimal
from fastapi import status
from sqlalchemy.orm import Session

from app.models.financial import (
    FinancialAccount, FinancialAsset, FinancialLiability,
    FinancialIncome, FinancialExpense
)


@pytest.mark.financial
class TestFinancialAccountEndpoints:
    """Test financial account endpoints"""
    
    def test_create_account(self, client, auth_headers, random_financial_account):
        """Test creating a financial account"""
        response = client.post(
            "/api/v1/financial/accounts",
            json=random_financial_account,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == random_financial_account["name"]
        assert data["institution"] == random_financial_account["institution"]
        assert float(data["balance"]) == random_financial_account["balance"]
    
    def test_get_accounts(self, client, auth_headers, sample_financial_data):
        """Test getting all accounts"""
        response = client.get("/api/v1/financial/accounts", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2  # Two accounts created in fixture
        assert all("balance" in account for account in data)
    
    def test_get_account_by_id(self, client, auth_headers, sample_financial_data):
        """Test getting specific account"""
        account_id = sample_financial_data["accounts"][0].id
        response = client.get(f"/api/v1/financial/accounts/{account_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == account_id
        assert data["name"] == sample_financial_data["accounts"][0].name
    
    def test_update_account(self, client, auth_headers, sample_financial_data):
        """Test updating account"""
        account_id = sample_financial_data["accounts"][0].id
        update_data = {
            "balance": 10000.00,
            "name": "Updated Account Name"
        }
        response = client.put(
            f"/api/v1/financial/accounts/{account_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert float(data["balance"]) == update_data["balance"]
        assert data["name"] == update_data["name"]
    
    def test_delete_account(self, client, auth_headers, sample_financial_data):
        """Test deleting account"""
        account_id = sample_financial_data["accounts"][0].id
        response = client.delete(f"/api/v1/financial/accounts/{account_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Verify account is deleted
        get_response = client.get(f"/api/v1/financial/accounts/{account_id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_unauthorized_access(self, client):
        """Test accessing accounts without authentication"""
        response = client.get("/api/v1/financial/accounts")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.financial
class TestFinancialAssetEndpoints:
    """Test financial asset endpoints"""
    
    def test_create_asset(self, client, auth_headers):
        """Test creating a financial asset"""
        asset_data = {
            "name": "Test Investment",
            "asset_type": "stocks",
            "current_value": 15000.00,
            "purchase_price": 12000.00,
            "purchase_date": datetime.now().isoformat()
        }
        response = client.post(
            "/api/v1/financial/assets",
            json=asset_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == asset_data["name"]
        assert float(data["current_value"]) == asset_data["current_value"]
    
    def test_get_assets(self, client, auth_headers, sample_financial_data):
        """Test getting all assets"""
        response = client.get("/api/v1/financial/assets", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["asset_type"] == "stocks"
    
    def test_update_asset_value(self, client, auth_headers, sample_financial_data):
        """Test updating asset value"""
        asset_id = sample_financial_data["assets"][0].id
        update_data = {"current_value": 30000.00}
        response = client.put(
            f"/api/v1/financial/assets/{asset_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert float(data["current_value"]) == update_data["current_value"]


@pytest.mark.financial
class TestFinancialLiabilityEndpoints:
    """Test financial liability endpoints"""
    
    def test_create_liability(self, client, auth_headers):
        """Test creating a financial liability"""
        liability_data = {
            "name": "Car Loan",
            "liability_type": "auto_loan",
            "current_balance": 25000.00,
            "original_amount": 30000.00,
            "interest_rate": 4.5,
            "minimum_payment": 450.00,
            "due_date": 15
        }
        response = client.post(
            "/api/v1/financial/liabilities",
            json=liability_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == liability_data["name"]
        assert float(data["current_balance"]) == liability_data["current_balance"]
        assert float(data["interest_rate"]) == liability_data["interest_rate"]
    
    def test_get_liabilities(self, client, auth_headers, sample_financial_data):
        """Test getting all liabilities"""
        response = client.get("/api/v1/financial/liabilities", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["liability_type"] == "credit_card"
    
    def test_calculate_total_debt(self, client, auth_headers, sample_financial_data):
        """Test calculating total debt"""
        response = client.get("/api/v1/financial/liabilities/summary", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_debt" in data
        assert float(data["total_debt"]) == 2000.00  # From sample data


@pytest.mark.financial
class TestFinancialIncomeEndpoints:
    """Test financial income endpoints"""
    
    def test_create_income(self, client, auth_headers):
        """Test creating income source"""
        income_data = {
            "source": "Freelance Work",
            "income_type": "freelance",
            "amount": 2000.00,
            "frequency": "monthly",
            "is_active": True
        }
        response = client.post(
            "/api/v1/financial/income",
            json=income_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["source"] == income_data["source"]
        assert float(data["amount"]) == income_data["amount"]
    
    def test_get_income_sources(self, client, auth_headers, sample_financial_data):
        """Test getting all income sources"""
        response = client.get("/api/v1/financial/income", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["income_type"] == "salary"
    
    def test_calculate_total_income(self, client, auth_headers, sample_financial_data):
        """Test calculating total monthly income"""
        response = client.get("/api/v1/financial/income/summary", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "monthly_income" in data
        assert float(data["monthly_income"]) == 6250.00  # From sample data


@pytest.mark.financial
class TestFinancialExpenseEndpoints:
    """Test financial expense endpoints"""
    
    def test_create_expense(self, client, auth_headers):
        """Test creating expense"""
        expense_data = {
            "category": "transportation",
            "description": "Gas and maintenance",
            "amount": 300.00,
            "frequency": "monthly",
            "is_essential": True,
            "is_active": True
        }
        response = client.post(
            "/api/v1/financial/expenses",
            json=expense_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["category"] == expense_data["category"]
        assert float(data["amount"]) == expense_data["amount"]
    
    def test_get_expenses(self, client, auth_headers, sample_financial_data):
        """Test getting all expenses"""
        response = client.get("/api/v1/financial/expenses", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "housing"
    
    def test_get_expenses_by_category(self, client, auth_headers, sample_financial_data):
        """Test filtering expenses by category"""
        response = client.get(
            "/api/v1/financial/expenses?category=housing",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert all(expense["category"] == "housing" for expense in data)
    
    def test_calculate_total_expenses(self, client, auth_headers, sample_financial_data):
        """Test calculating total monthly expenses"""
        response = client.get("/api/v1/financial/expenses/summary", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "monthly_expenses" in data
        assert "essential_expenses" in data
        assert float(data["monthly_expenses"]) == 1500.00  # From sample data


@pytest.mark.financial
class TestFinancialSummary:
    """Test financial summary and calculations"""
    
    def test_get_financial_summary(self, client, auth_headers, sample_financial_data):
        """Test getting complete financial summary"""
        response = client.get("/api/v1/financial/summary", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check all required fields
        assert "total_assets" in data
        assert "total_liabilities" in data
        assert "net_worth" in data
        assert "monthly_income" in data
        assert "monthly_expenses" in data
        assert "monthly_cash_flow" in data
        assert "data_quality_score" in data
        
        # Verify calculations
        assert float(data["total_assets"]) == 45000.00  # 5000 + 15000 + 25000
        assert float(data["total_liabilities"]) == 2000.00
        assert float(data["net_worth"]) == 43000.00  # assets - liabilities
        assert float(data["monthly_cash_flow"]) == 4750.00  # income - expenses
    
    def test_data_quality_scoring(self, client, auth_headers, sample_financial_data):
        """Test data quality score calculation"""
        response = client.get("/api/v1/financial/data-quality", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "overall_score" in data
        assert "dq1_accounts" in data
        assert "dq2_income_expenses" in data
        assert "dq3_assets_liabilities" in data
        assert "dq4_goals" in data
        
        # Check score ranges
        assert 0 <= data["overall_score"] <= 100
        assert data["dq1_accounts"] == 100  # Has accounts in sample data
        assert data["dq2_income_expenses"] == 100  # Has income and expenses
        assert data["dq3_assets_liabilities"] == 100  # Has assets and liabilities