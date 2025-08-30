"""
WealthPath AI - Database Base and Imports
"""
from app.db.session import Base  # noqa

# Import all models so they are registered with SQLAlchemy
from app.models.user import User  # noqa
from app.models.financial import FinancialAccount, FinancialEntry, AccountBalance  # noqa
from app.models.goal import FinancialGoal, GoalScenario, ActionPlan  # noqa
from app.models.analytics import ModelPrediction, UserInteraction  # noqa
from app.models.projection import ProjectionAssumptions, ProjectionSnapshot, ProjectionSensitivity  # noqa

# Import newer models with proper relationship dependencies
from app.models.estate_planning import UserEstatePlanning  # noqa
from app.models.insurance import UserInsurancePolicy  # noqa
from app.models.investment_preferences import UserInvestmentPreferences  # noqa