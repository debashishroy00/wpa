"""
WealthPath AI - API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, financial, goals, goal_templates, goals_v2, advisor_data, plan_engine, advisory, financial_clean, vector_db, debug, profile, admin, embeddings, insights, chat_simple
# Temporarily disabled endpoints that import removed services:
# intelligence, chat_with_memory (imports removed services)
# Temporarily disabled endpoints that import removed services:
# projections, verification_test, tax
# Keep original LLM endpoints for Step 5 (working yesterday)
from app.api.v1.endpoints import llm
# Import the missing endpoints
from app.api.v1.endpoints import estate_planning, insurance, investment_preferences

# Create API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(financial.router, prefix="/financial", tags=["financial"])
api_router.include_router(goals_v2.router, tags=["goals-v2"])
api_router.include_router(goal_templates.router, prefix="/goal-templates", tags=["goal-templates"])
# api_router.include_router(projections.router, prefix="/projections", tags=["projections"])  # Disabled - imports removed projection_service
# api_router.include_router(intelligence.router, prefix="/intelligence", tags=["intelligence"])  # Disabled - imports removed services
api_router.include_router(advisor_data.router, prefix="/advisor", tags=["advisor-data"])
api_router.include_router(plan_engine.router, prefix="/plan-engine", tags=["plan-engine"])
api_router.include_router(advisory.router, prefix="/advisory", tags=["advisory"])
# Step 5: Original LLM endpoints (working yesterday)
api_router.include_router(llm.router, prefix="/llm", tags=["step5-llm"])
api_router.include_router(financial_clean.router, prefix="/financial", tags=["financial-clean"])
api_router.include_router(vector_db.router, prefix="/vector", tags=["vector-database"])
# Step 6: New chat endpoints (separate from Step 5)
api_router.include_router(chat.router, prefix="/chat", tags=["step6-chat"])
# Step 7: Debug endpoints for visibility
api_router.include_router(debug.router, prefix="/debug", tags=["step7-debug"])
# Profile endpoints for user demographics, family, benefits, and tax info
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
# Verification test endpoints for system health and fixes validation
# api_router.include_router(verification_test.router, prefix="/verify", tags=["verification"])  # Disabled - imports removed services
# Admin endpoints for system administration (isolated)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
# Hybrid embedding system endpoints
api_router.include_router(embeddings.router, prefix="/embeddings", tags=["hybrid-embeddings"])
# Estate planning, insurance, and investment preferences endpoints
api_router.include_router(estate_planning.router, prefix="/estate-planning", tags=["estate-planning"])
api_router.include_router(insurance.router, prefix="/insurance", tags=["insurance"])
api_router.include_router(investment_preferences.router, prefix="/investment-preferences", tags=["investment-preferences"])
# Tax optimization endpoints
# api_router.include_router(tax.router, prefix="/tax", tags=["tax-optimization"])  # Disabled - imports removed tax_calculations
# New foundation-based insights endpoints
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
# Simplified chat endpoint using new architecture
api_router.include_router(chat_simple.router, prefix="/chat-simple", tags=["chat-simple"])