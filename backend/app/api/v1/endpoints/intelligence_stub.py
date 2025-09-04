"""
WealthPath AI - Intelligence Analysis Stub
Simple stub to prevent frontend 404 errors
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from app.db.session import get_db
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.user import User

router = APIRouter()

class IntelligenceAnalyzeRequest(BaseModel):
    include_simulations: bool = True
    scenario_count: int = 3
    optimization_level: str = "balanced"

@router.post("/analyze")
async def analyze_intelligence(
    request: IntelligenceAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Stub endpoint to prevent frontend 404 errors
    Returns a basic response structure
    """
    return {
        "success": True,
        "analysis": {
            "goal_alignment": {
                "score": 0.85,
                "status": "on_track",
                "conflicts": [],
                "recommendations": []
            },
            "scenarios": [],
            "optimizations": [],
            "risk_analysis": {
                "overall_risk": "moderate",
                "factors": []
            }
        },
        "metadata": {
            "analyzed_at": "2024-01-01T00:00:00Z",
            "version": "1.0.0-stub"
        }
    }

@router.get("/status")
async def intelligence_status(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Status check endpoint"""
    return {
        "status": "operational",
        "service": "intelligence-stub",
        "message": "Intelligence service is running in stub mode"
    }