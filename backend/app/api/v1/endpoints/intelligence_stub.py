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
    Enhanced stub endpoint that uses real goals from database
    """
    from app.models.goals_v2 import Goal
    from datetime import datetime
    
    # Get real goals from database
    goals = db.query(Goal).filter(
        Goal.user_id == current_user.id,
        Goal.status == 'active'
    ).all()
    
    if not goals:
        # Return empty structure if no goals
        return {
            "analysis_id": "stub-analysis",
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0,
            "success_probability": 0.0,
            "goals": [],
            "gaps": {
                "monthly_shortfall": 0,
                "total_capital_needed": 0,
                "current_trajectory": 0,
                "gap_amount": 0
            },
            "conflicts": [],
            "scenarios": [],
            "recommendations": {"immediate": [], "short_term": [], "long_term": []}
        }
    
    # Convert real goals to analysis format
    analysis_goals = []
    total_target = 0
    total_current = 0
    total_monthly_required = 0
    
    for goal in goals:
        target_amount = float(goal.target_amount)
        current_amount = float(goal.current_amount or 0)
        housing_benefit = 0  # Initialize for all goals
        investable_assets = 0  # Initialize for all goals
        
        # Enhanced retirement calculation with housing benefit
        if goal.category == 'retirement':
            # Get financial data for more accurate calculation
            from app.models.financial import FinancialEntry
            from sqlalchemy import func
            
            # Calculate investable assets for retirement
            investable_assets = db.query(func.sum(FinancialEntry.amount)).filter(
                FinancialEntry.user_id == current_user.id,
                FinancialEntry.is_active == True,
                FinancialEntry.category == 'assets',
                FinancialEntry.subcategory.in_([
                    'retirement_accounts', 
                    'investment_accounts',
                    'real_estate'  # Rental properties only
                ])
            ).scalar() or 0
            
            # Calculate housing benefit from mortgage elimination
            mortgage_payment = db.query(FinancialEntry.amount).filter(
                FinancialEntry.user_id == current_user.id,
                FinancialEntry.is_active == True,
                FinancialEntry.description.like('%Mortgage%'),
                FinancialEntry.category == 'expenses'
            ).first()
            
            housing_benefit = 0
            if mortgage_payment:
                # Annual mortgage * 25 (4% withdrawal rule inverse)
                annual_mortgage = float(mortgage_payment[0]) * 12
                housing_benefit = annual_mortgage / 0.04  # $649,200 for $2,164/month
            
            # More accurate retirement position
            current_amount = investable_assets + housing_benefit
            
            # Use calculated amount if greater than stored amount
            if current_amount < float(goal.current_amount or 0):
                current_amount = float(goal.current_amount or 0)
        
        # Calculate months remaining
        target_date = goal.target_date
        months_remaining = max(1, (target_date - datetime.now().date()).days / 30.44)
        
        # Calculate monthly required
        remaining_needed = target_amount - current_amount
        monthly_required = remaining_needed / months_remaining
        
        # Calculate feasibility score based on progress
        progress = (current_amount / target_amount) * 100 if target_amount > 0 else 0
        feasibility_score = min(100, max(20, progress + 30))  # Base score with progress bonus
        
        goal_data = {
            "goal_id": str(goal.goal_id),
            "name": goal.name,
            "category": goal.category,
            "target_amount": target_amount,
            "current_amount": round(current_amount, 2),
            "target_date": target_date.isoformat(),
            "feasibility_score": round(feasibility_score),
            "monthly_required": round(monthly_required, 2),
            "risk_aligned": feasibility_score >= 70
        }
        
        # Add calculation breakdown for retirement goals
        if goal.category == 'retirement' and housing_benefit > 0:
            goal_data["calculation_breakdown"] = {
                "investable_assets": round(investable_assets, 2),
                "housing_benefit": round(housing_benefit, 2),
                "total_position": round(current_amount, 2),
                "explanation": "Includes investable assets plus the retirement value of mortgage elimination"
            }
        
        analysis_goals.append(goal_data)
        
        total_target += target_amount
        total_current += current_amount
        total_monthly_required += monthly_required
    
    # Calculate gaps
    estimated_monthly_income = 12000  # Fallback estimate
    estimated_monthly_expenses = 8000
    monthly_surplus = estimated_monthly_income - estimated_monthly_expenses
    monthly_shortfall = max(0, total_monthly_required - monthly_surplus)
    
    # Calculate overall score
    avg_feasibility = sum(g["feasibility_score"] for g in analysis_goals) / len(analysis_goals)
    overall_score = round(avg_feasibility * 0.8)  # Slightly conservative
    success_probability = overall_score / 100
    
    return {
        "analysis_id": "stub-analysis",
        "timestamp": datetime.now().isoformat(),
        "overall_score": overall_score,
        "success_probability": success_probability,
        "goals": analysis_goals,
        "gaps": {
            "monthly_shortfall": round(monthly_shortfall, 2),
            "total_capital_needed": round(total_target - total_current, 2),
            "current_trajectory": round(total_current, 2),
            "gap_amount": round(total_target - total_current, 2)
        },
        "conflicts": [
            {
                "id": "cash_flow_gap",
                "type": "cash_flow",
                "severity": "high" if monthly_shortfall > 2000 else "medium" if monthly_shortfall > 500 else "low",
                "description": f"Monthly funding gap of ${monthly_shortfall:,.0f}" if monthly_shortfall > 0 else "Goals appear fundable with current cash flow",
                "affected_goals": [g["name"] for g in analysis_goals],
                "resolution_options": []
            }
        ] if monthly_shortfall > 0 else [],
        "scenarios": [
            {
                "id": "conservative",
                "name": "Conservative Approach",
                "description": "Lower risk, steady progress",
                "is_recommended": False,
                "success_rate": max(60, overall_score - 15),
                "monthly_requirement_change": 0,
                "timeline_impact": 12,
                "required_changes": [],
                "projected_outcomes": {"total_savings": total_target * 0.85, "goal_completion_rate": 75, "risk_score": 3}
            },
            {
                "id": "balanced",
                "name": "Balanced Optimization",
                "description": "Moderate risk with optimization opportunities",
                "is_recommended": True,
                "success_rate": overall_score,
                "monthly_requirement_change": -500,
                "timeline_impact": 0,
                "required_changes": [],
                "projected_outcomes": {"total_savings": total_target, "goal_completion_rate": overall_score, "risk_score": 5}
            },
            {
                "id": "aggressive", 
                "name": "Aggressive Growth",
                "description": "Higher risk, faster progress",
                "is_recommended": False,
                "success_rate": min(95, overall_score + 10),
                "monthly_requirement_change": -1000,
                "timeline_impact": -6,
                "required_changes": [],
                "projected_outcomes": {"total_savings": total_target * 1.15, "goal_completion_rate": 90, "risk_score": 8}
            }
        ],
        "recommendations": {
            "immediate": [
                {
                    "id": "review_budget",
                    "title": "Review Monthly Budget",
                    "description": "Analyze expenses to optimize goal funding",
                    "impact": "Medium",
                    "potential_savings": 750,
                    "priority": "high"
                }
            ] if monthly_shortfall > 0 else [],
            "short_term": [
                {
                    "id": "optimize_investments",
                    "title": "Optimize Investment Strategy", 
                    "description": "Review asset allocation and fees",
                    "impact": "High",
                    "potential_improvement": "5-15%",
                    "priority": "medium"
                }
            ],
            "long_term": [
                {
                    "id": "goal_timing",
                    "title": "Review Goal Timing",
                    "description": "Consider adjusting target dates for better cash flow",
                    "impact": "High",
                    "timeline_flexibility": "6-18 months",
                    "priority": "medium"
                }
            ]
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