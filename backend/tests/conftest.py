"""
WealthPath AI - Testing Configuration and Fixtures
"""
import os
import pytest
import asyncio
from typing import Generator, Any
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.financial import (
    FinancialAccount, FinancialEntry, AccountBalance,
    EntryCategory, FrequencyType
)
from app.models.goal import FinancialGoal, GoalType, GoalStatus
from app.models.goals_v2 import Goal, GoalProgress, UserPreferences
from app.core.security import create_access_token, get_password_hash
from faker import Faker

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

fake = Faker()


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator:
    """Create a test client with the testing database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user"""
    user = User(
        email="test@wealthpath.ai",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        annual_income=Decimal("75000.00"),
        risk_tolerance=5,
        retirement_age=65
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """Generate an access token for the test user"""
    return create_access_token(
        subject=test_user.email,
        expires_delta=timedelta(minutes=30)
    )


@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    """Return authorization headers for authenticated requests"""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def sample_financial_data(test_user: User, db_session: Session) -> dict:
    """Create sample financial data for testing"""
    from app.models.financial import AccountType
    
    # Create accounts
    checking = FinancialAccount(
        user_id=test_user.id,
        name="Test Checking",
        institution="Test Bank",
        account_type=AccountType.checking,
        current_balance=Decimal("5000.00"),
        is_active=True
    )
    savings = FinancialAccount(
        user_id=test_user.id,
        name="Test Savings",
        institution="Test Bank",
        account_type=AccountType.savings,
        current_balance=Decimal("15000.00"),
        is_active=True
    )
    
    # Create financial entries (income and expenses)
    income_entry = FinancialEntry(
        user_id=test_user.id,
        account_id=checking.id,
        category=EntryCategory.income_salary,
        amount=Decimal("6250.00"),
        description="Monthly Salary",
        frequency=FrequencyType.monthly,
        is_recurring=True
    )
    
    expense_entry = FinancialEntry(
        user_id=test_user.id,
        account_id=checking.id,
        category=EntryCategory.expense_housing,
        amount=Decimal("-1500.00"),  # Negative for expense
        description="Monthly Rent",
        frequency=FrequencyType.monthly,
        is_recurring=True
    )
    
    db_session.add_all([checking, savings])
    db_session.commit()
    
    db_session.add_all([income_entry, expense_entry])
    db_session.commit()
    
    return {
        "accounts": [checking, savings],
        "entries": [income_entry, expense_entry]
    }


@pytest.fixture
def sample_goal(test_user: User, db_session: Session) -> FinancialGoal:
    """Create a sample financial goal for testing"""
    goal = FinancialGoal(
        user_id=test_user.id,
        goal_type=GoalType.emergency_fund,
        name="Emergency Fund",
        description="6 months of expenses",
        target_amount=Decimal("24000.00"),
        current_amount=Decimal("5000.00"),
        target_date=datetime.now() + timedelta(days=365),
        status=GoalStatus.active,
        priority=1
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    return goal


@pytest.fixture
def random_user_data() -> dict:
    """Generate random user data for testing"""
    return {
        "email": fake.email(),
        "password": fake.password(length=12, special_chars=True, digits=True),
        "full_name": fake.name(),
        "annual_income": float(fake.random_int(min=30000, max=200000, step=5000)),
        "risk_tolerance": fake.random_int(min=1, max=10),
        "retirement_age": fake.random_int(min=55, max=70)
    }


@pytest.fixture
def random_financial_account() -> dict:
    """Generate random financial account data"""
    return {
        "name": f"{fake.company()} {fake.random_element(['Checking', 'Savings', 'Investment'])}",
        "institution": fake.company(),
        "account_type": fake.random_element(["checking", "savings", "investment", "retirement"]),
        "current_balance": float(fake.random_int(min=100, max=100000, step=100)),
        "account_number_last4": str(fake.random_int(min=1000, max=9999)),
        "is_active": True
    }


@pytest.fixture
def random_goal() -> dict:
    """Generate random goal data"""
    goal_types = ["early_retirement", "home_purchase", "education", "emergency_fund", "debt_payoff"]
    return {
        "goal_type": fake.random_element(goal_types),
        "name": fake.sentence(nb_words=3),
        "description": fake.text(max_nb_chars=200),
        "target_amount": float(fake.random_int(min=1000, max=1000000, step=1000)),
        "current_amount": float(fake.random_int(min=0, max=50000, step=500)),
        "target_date": (datetime.now() + timedelta(days=fake.random_int(min=180, max=3650))).isoformat(),
        "priority": fake.random_int(min=1, max=5)
    }


# Goals V2 Fixtures

@pytest.fixture
def test_goal_v2(test_user: User, db_session: Session) -> Goal:
    """Create a test goal using Goals V2 system"""
    goal = Goal(
        user_id=test_user.id,
        category="retirement",
        name="Test Retirement Goal V2",
        description="Test retirement savings goal",
        target_amount=Decimal("1000000.00"),
        target_date=datetime.now().date() + timedelta(days=365*30),
        priority=1,
        status="active",
        params={
            "retirement_age": 65,
            "annual_spending": 50000,
            "current_age": 30
        }
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    
    # Add initial progress
    progress = GoalProgress(
        goal_id=goal.goal_id,
        current_amount=Decimal("100000.00"),
        percentage_complete=Decimal("10.00"),
        source="manual"
    )
    db_session.add(progress)
    db_session.commit()
    
    return goal


@pytest.fixture
def test_goals_v2(test_user: User, db_session: Session) -> list[Goal]:
    """Create multiple test goals using Goals V2 system"""
    goals = []
    
    # Retirement goal
    retirement_goal = Goal(
        user_id=test_user.id,
        category="retirement",
        name="Retirement Fund V2",
        description="Long-term retirement savings",
        target_amount=Decimal("1000000.00"),
        target_date=datetime.now().date() + timedelta(days=365*30),
        priority=1,
        status="active",
        params={
            "retirement_age": 65,
            "annual_spending": 50000,
            "current_age": 30
        }
    )
    goals.append(retirement_goal)
    
    # Education goal
    education_goal = Goal(
        user_id=test_user.id,
        category="education",
        name="College Fund V2",
        description="Child's college education",
        target_amount=Decimal("200000.00"),
        target_date=datetime.now().date() + timedelta(days=365*10),
        priority=2,
        status="active",
        params={
            "degree_type": "undergraduate",
            "institution_type": "public",
            "start_year": 2035
        }
    )
    goals.append(education_goal)
    
    # Add all goals to session
    for goal in goals:
        db_session.add(goal)
    
    db_session.commit()
    
    # Refresh and add progress
    for goal in goals:
        db_session.refresh(goal)
        progress = GoalProgress(
            goal_id=goal.goal_id,
            current_amount=goal.target_amount * Decimal("0.1"),
            percentage_complete=Decimal("10.00"),
            source="manual"
        )
        db_session.add(progress)
    
    db_session.commit()
    return goals


@pytest.fixture
def test_user_preferences_v2(test_user: User, db_session: Session) -> UserPreferences:
    """Create test user preferences using Goals V2 system"""
    preferences = UserPreferences(
        user_id=test_user.id,
        risk_tolerance="moderate",
        investment_experience="intermediate",
        time_horizon="long_term",
        liquidity_needs="low",
        goal_prioritization="balanced"
    )
    db_session.add(preferences)
    db_session.commit()
    db_session.refresh(preferences)
    return preferences


# Async event loop configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()