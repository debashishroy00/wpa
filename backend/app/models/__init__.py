# Database models package

# Import all models to ensure they're registered with SQLAlchemy
from .user import User, UserSession, UserActivityLog
from .user_profile import UserProfile, FamilyMember, UserBenefit, UserTaxInfo
from .financial import FinancialAccount, FinancialEntry
from .goal import FinancialGoal, GoalScenario, ActionPlan, GoalMilestone, GoalPerformanceMetric
from .goals_v2 import Goal, GoalHistory, GoalRelationship, GoalProgress, UserPreferences
from .projection import ProjectionAssumptions, ProjectionSnapshot
from .analytics import UserInteraction, ModelPrediction
from .chat_intelligence import ChatIntelligence

__all__ = [
    "User", "UserProfile", "UserSession", "UserActivityLog",
    "FamilyMember", "UserBenefit", "UserTaxInfo",
    "FinancialAccount", "FinancialEntry", 
    "FinancialGoal", "GoalScenario", "ActionPlan", "GoalMilestone", "GoalPerformanceMetric",
    "Goal", "GoalHistory", "GoalRelationship", "GoalProgress", "UserPreferences",
    "ProjectionAssumptions", "ProjectionSnapshot",
    "UserInteraction", "ModelPrediction",
    "ChatIntelligence"
]