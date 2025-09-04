"""
WealthPath AI - Projections Stub
Simple stub to prevent frontend 404 errors
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.get("/comprehensive")
async def get_comprehensive_projection(
    years: int = Query(20, description="Number of years to project"),
    include_monte_carlo: bool = Query(False, description="Include Monte Carlo simulation"),
    monte_carlo_iterations: int = Query(1000, description="Number of Monte Carlo iterations"),
    force_recalculate: bool = Query(False, description="Force recalculation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Stub endpoint for comprehensive projections
    Returns a basic projection structure
    """
    
    # Generate basic projection data
    projection_data = []
    current_year = datetime.now().year
    base_value = 2565545  # Starting net worth
    
    for year in range(years + 1):
        growth_rate = 1.06  # 6% annual growth
        value = base_value * (growth_rate ** year)
        projection_data.append({
            "year": current_year + year,
            "age": 55 + year,
            "net_worth": value,
            "assets": value * 1.1,
            "liabilities": value * 0.1,
            "income": 184164,
            "expenses": 89808,
            "savings": 94356
        })
    
    response = {
        "success": True,
        "projection": {
            "years": projection_data,
            "summary": {
                "starting_net_worth": base_value,
                "ending_net_worth": projection_data[-1]["net_worth"],
                "total_growth": projection_data[-1]["net_worth"] - base_value,
                "average_annual_growth": 0.06,
                "retirement_feasibility": "high"
            },
            "milestones": [
                {
                    "age": 65,
                    "description": "Traditional retirement age",
                    "net_worth": base_value * (1.06 ** 10),
                    "achieved": True
                }
            ]
        },
        "metadata": {
            "calculated_at": datetime.now().isoformat(),
            "years_projected": years,
            "include_monte_carlo": include_monte_carlo
        }
    }
    
    if include_monte_carlo:
        response["monte_carlo"] = {
            "iterations": monte_carlo_iterations,
            "percentiles": {
                "p10": projection_data[-1]["net_worth"] * 0.7,
                "p25": projection_data[-1]["net_worth"] * 0.85,
                "p50": projection_data[-1]["net_worth"],
                "p75": projection_data[-1]["net_worth"] * 1.15,
                "p90": projection_data[-1]["net_worth"] * 1.3
            },
            "success_rate": 0.85
        }
    
    return response

@router.get("/retirement")
async def get_retirement_projection(
    target_age: int = Query(65, description="Target retirement age"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Stub endpoint for retirement projections"""
    return {
        "success": True,
        "projection": {
            "retirement_age": target_age,
            "years_to_retirement": target_age - 55,
            "projected_net_worth": 4500000,
            "retirement_feasible": True,
            "monthly_retirement_income": 15000,
            "success_probability": 0.85
        }
    }

@router.get("/scenarios")
async def get_projection_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Stub endpoint for projection scenarios"""
    return {
        "success": True,
        "scenarios": [
            {
                "name": "Conservative",
                "growth_rate": 0.04,
                "final_value": 3500000
            },
            {
                "name": "Moderate",
                "growth_rate": 0.06,
                "final_value": 4500000
            },
            {
                "name": "Aggressive",
                "growth_rate": 0.08,
                "final_value": 5500000
            }
        ]
    }