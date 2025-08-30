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

# NOTE: Newer models (estate_planning, insurance, investment_preferences) 
# are imported in their respective endpoint files to avoid circular dependencies