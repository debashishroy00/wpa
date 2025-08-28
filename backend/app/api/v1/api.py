"""
WealthPath AI - API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, financial, goals, goal_templates, projections, goals_v2, intelligence, advisor_data, plan_engine, advisory, financial_clean, vector_db, chat_with_memory, debug, profile, verification_test, admin, embeddings, monitoring, health, calculation_debug
# LLM endpoints removed during cleanup

# Create API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(financial.router, prefix="/financial", tags=["financial"])
api_router.include_router(goals_v2.router, tags=["goals-v2"])
api_router.include_router(goal_templates.router, prefix="/goal-templates", tags=["goal-templates"])
api_router.include_router(projections.router, prefix="/projections", tags=["projections"])
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["intelligence"])
api_router.include_router(advisor_data.router, prefix="/advisor", tags=["advisor-data"])
api_router.include_router(plan_engine.router, prefix="/plan-engine", tags=["plan-engine"])
api_router.include_router(advisory.router, prefix="/advisory", tags=["advisory"])
# LLM endpoint route removed during cleanup
api_router.include_router(financial_clean.router, prefix="/financial", tags=["financial-clean"])
api_router.include_router(vector_db.router, prefix="/vector", tags=["vector-database"])
# Chat with Memory - Primary chat endpoint
api_router.include_router(chat_with_memory.router, prefix="/chat-memory", tags=["chat-memory"])
# Step 7: Debug endpoints for visibility
api_router.include_router(debug.router, prefix="/debug", tags=["step7-debug"])
# Profile endpoints for user demographics, family, benefits, and tax info
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
# Verification test endpoints for system health and fixes validation
api_router.include_router(verification_test.router, prefix="/verify", tags=["verification"])
# Admin endpoints for system administration (isolated)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
# Hybrid embedding system endpoints
api_router.include_router(embeddings.router, prefix="/embeddings", tags=["hybrid-embeddings"])
# Monitoring endpoints for production dashboard
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
# Health check endpoints for production deployment
api_router.include_router(health.router, prefix="/health", tags=["health"])
# Calculation debug endpoints (no auth required)
api_router.include_router(calculation_debug.router, prefix="/calc-debug", tags=["calculation-debug"])