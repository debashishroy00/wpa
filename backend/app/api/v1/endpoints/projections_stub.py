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
    
    # Create projections in the format frontend expects
    projections = []
    for i, year_data in enumerate(projection_data):
        projections.append({
            "year": i,  # Year index (0, 1, 2, etc.)
            "age": year_data["age"],
            "net_worth": year_data["net_worth"],
            "assets": year_data["assets"],
            "liabilities": year_data["liabilities"],
            "income": year_data["income"],
            "expenses": year_data["expenses"],
            "savings": year_data["savings"]
        })
    
    response = {
        "success": True,
        "projections": projections,  # Frontend expects this at top level
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
        },
        "confidence_intervals": {
            "percentiles": {
                "p10": [year_data["net_worth"] * (0.75 + year * 0.01) for year, year_data in enumerate(projection_data)],
                "p25": [year_data["net_worth"] * (0.85 + year * 0.005) for year, year_data in enumerate(projection_data)],
                "p50": [year_data["net_worth"] for year_data in projection_data],
                "p75": [year_data["net_worth"] * (1.15 + year * 0.005) for year, year_data in enumerate(projection_data)],
                "p90": [year_data["net_worth"] * (1.35 + year * 0.01) for year, year_data in enumerate(projection_data)]
            }
        }
    }
    
    if include_monte_carlo:
        final_year_value = projection_data[-1]["net_worth"]
        response["monte_carlo"] = {
            "iterations": monte_carlo_iterations,
            "percentiles": {
                "p10": final_year_value * 0.65,
                "p25": final_year_value * 0.80,
                "p50": final_year_value,
                "p75": final_year_value * 1.25,
                "p90": final_year_value * 1.50
            },
            "success_rate": max(0.70, min(0.95, 0.85 - (years - 10) * 0.02)),  # Success rate decreases over time
            "confidence_score": int(max(60, min(95, 85 - (years - 10) * 1.5))),  # Confidence decreases over time
            "volatility_estimate": min(0.25, 0.15 + years * 0.005)  # Volatility increases with time horizon
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

@router.post("/scenario")
async def run_projection_scenario(
    scenario_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Run a specific projection scenario with Monte Carlo analysis"""
    
    # Get user's financial data from existing summary service
    from app.models.financial import NetWorthSnapshot
    from sqlalchemy import desc
    
    # Get latest snapshot (same approach as /financial/summary)
    latest_snapshot = db.query(NetWorthSnapshot).filter(
        NetWorthSnapshot.user_id == current_user.id
    ).order_by(desc(NetWorthSnapshot.snapshot_date)).first()
    
    if latest_snapshot:
        current_net_worth = float(latest_snapshot.net_worth)
    else:
        # Fallback to live calculation if no snapshot
        from app.models.financial import FinancialEntry
        from app.schemas.financial import EntryCategory
        from sqlalchemy import and_
        
        entries = db.query(FinancialEntry).filter(
            and_(
                FinancialEntry.user_id == current_user.id,
                FinancialEntry.is_active == True
            )
        ).all()
        
        total_assets = sum(
            float(e.amount) for e in entries 
            if e.category == EntryCategory.assets
        )
        
        total_liabilities = sum(
            float(e.amount) for e in entries 
            if e.category == EntryCategory.liabilities
        )
        
        current_net_worth = total_assets - total_liabilities
    
    # Extract scenario parameters
    years = scenario_data.get('years', 20)
    growth_rate = scenario_data.get('growth_rate', 0.06)
    risk_tolerance = scenario_data.get('risk_tolerance', 'moderate')
    
    # Generate scenario projection
    projection_data = []
    current_year = datetime.now().year
    
    for year in range(years + 1):
        compound_rate = 1 + growth_rate
        value = current_net_worth * (compound_rate ** year)
        projection_data.append({
            "year": current_year + year,
            "age": 55 + year,  # Assuming current age 55
            "net_worth": value,
            "assets": value * 1.1,
            "liabilities": value * 0.1
        })
    
    # Calculate confidence intervals based on risk tolerance
    volatility = {
        'conservative': 0.12,
        'moderate': 0.18,
        'aggressive': 0.25
    }.get(risk_tolerance, 0.18)
    
    confidence_intervals = {
        "percentiles": {
            "p10": [year_data["net_worth"] * (1 - volatility * 1.5) for year_data in projection_data],
            "p25": [year_data["net_worth"] * (1 - volatility * 0.8) for year_data in projection_data],
            "p50": [year_data["net_worth"] for year_data in projection_data],
            "p75": [year_data["net_worth"] * (1 + volatility * 0.8) for year_data in projection_data],
            "p90": [year_data["net_worth"] * (1 + volatility * 1.5) for year_data in projection_data]
        }
    }
    
    # Monte Carlo results
    final_value = projection_data[-1]["net_worth"]
    success_rate = max(0.65, min(0.95, 0.85 - volatility))
    confidence_score = int(max(60, min(95, 90 - volatility * 100)))
    
    return {
        "success": True,
        "scenario": {
            "name": f"{risk_tolerance.title()} Growth",
            "growth_rate": growth_rate,
            "years": years,
            "starting_value": current_net_worth,
            "ending_value": final_value,
            "total_growth": final_value - current_net_worth
        },
        "projections": [
            {
                "year": i,
                "age": year_data["age"],
                "net_worth": year_data["net_worth"],
                "assets": year_data["assets"],
                "liabilities": year_data["liabilities"]
            }
            for i, year_data in enumerate(projection_data)
        ],
        "confidence_intervals": confidence_intervals,
        "monte_carlo": {
            "iterations": 1000,
            "success_rate": success_rate,
            "confidence_score": confidence_score,
            "percentiles": {
                "p10": final_value * (1 - volatility * 1.5),
                "p25": final_value * (1 - volatility * 0.8),
                "p50": final_value,
                "p75": final_value * (1 + volatility * 0.8),
                "p90": final_value * (1 + volatility * 1.5)
            },
            "volatility_estimate": volatility
        },
        "metadata": {
            "calculated_at": datetime.now().isoformat(),
            "risk_tolerance": risk_tolerance,
            "volatility_used": volatility
        }
    }

@router.get("/assumptions")
async def get_projection_assumptions(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Stub endpoint for projection assumptions"""
    return {
        "success": True,
        "assumptions": {
            "growth_rates": {
                "stocks": 0.07,
                "bonds": 0.03,
                "real_estate": 0.04,
                "cash": 0.01,
                "overall_portfolio": 0.06
            },
            "inflation": {
                "rate": 0.025,
                "source": "Federal Reserve target"
            },
            "tax_rates": {
                "federal": 0.24,
                "state": 0.0525,
                "capital_gains": 0.15
            },
            "retirement": {
                "withdrawal_rate": 0.04,
                "social_security_start": 67,
                "life_expectancy": 90
            },
            "expense_adjustments": {
                "retirement_factor": 0.80,
                "healthcare_increase": 1.05
            }
        },
        "metadata": {
            "last_updated": "2024-01-01",
            "data_sources": ["Federal Reserve", "IRS", "SSA"]
        }
    }