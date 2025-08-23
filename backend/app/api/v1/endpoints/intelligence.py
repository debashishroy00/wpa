"""
WealthPath AI - Intelligence Analysis API Endpoints
Provides comprehensive goal analysis, conflict detection, and optimization scenarios
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4, UUID

from app.db.session import get_db
from app.models.user import User
from app.models.goals_v2 import Goal, UserPreferences
from app.models.financial import FinancialEntry, NetWorthSnapshot
from app.api.v1.endpoints.auth import get_current_active_user
from app.services.intelligence_engine import (
    IntelligenceEngine, 
    FinancialState,
    Scenario
)
from pydantic import BaseModel


router = APIRouter()


class IntelligenceAnalyzeRequest(BaseModel):
    include_simulations: bool = True
    scenario_count: int = 3
    optimization_level: str = "balanced"  # conservative | balanced | aggressive


class ConflictResolutionRequest(BaseModel):
    conflict_id: str
    selected_resolution: str
    parameters: Dict[str, Any] = {}


class MonteCarloRequest(BaseModel):
    scenario_id: str
    iterations: int = 1000
    variables: Dict[str, Any] = {}


@router.post("/analyze")
async def analyze_intelligence(
    request: IntelligenceAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Main intelligence analysis endpoint
    """
    try:
        # Get user's goals
        goals = db.query(Goal).filter(
            Goal.user_id == current_user.id,
            Goal.status == 'active'
        ).all()
        
        if not goals:
            raise HTTPException(status_code=400, detail="No active goals found. Please complete Step 3 first.")
        
        # Get user preferences
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        if not preferences:
            raise HTTPException(status_code=400, detail="User preferences not found. Please complete Step 3 first.")
        
        # Get current financial state from latest snapshot and entries
        financial_state = _get_financial_state(db, current_user.id)
        
        # Get advisor-level data for enhanced recommendations
        advisor_data = _get_advisor_data(db, current_user.id)
        print(f"🔍 DEBUG: Advisor data retrieved: {advisor_data}")  # DEBUG LOG
        
        # Initialize intelligence engine
        engine = IntelligenceEngine()
        
        # Run analysis
        analysis_result = engine.analyze_user_goals(
            user_id=current_user.id,
            goals=goals,
            financial_state=financial_state,
            preferences=preferences,
            advisor_data=advisor_data
        )
        
        # Store analysis result for caching/history
        analysis_id = str(uuid4())
        
        # Store in database (convert dicts to JSON)
        import json
        db.execute(text("""
            INSERT INTO intelligence_analyses (id, user_id, overall_score, success_probability, 
                                             gaps, conflicts, scenarios, recommendations)
            VALUES (:id, :user_id, :score, :probability, :gaps, :conflicts, :scenarios, :recommendations)
        """), {
            "id": analysis_id,
            "user_id": current_user.id,
            "score": analysis_result['overall_score'],
            "probability": analysis_result['success_probability'],
            "gaps": json.dumps(analysis_result['gaps']),
            "conflicts": json.dumps(analysis_result['conflicts']),
            "scenarios": json.dumps(analysis_result['scenarios']),
            "recommendations": json.dumps(analysis_result['recommendations'])
        })
        db.commit()
        
        # Add analysis ID to response
        analysis_result['analysis_id'] = analysis_id
        analysis_result['timestamp'] = datetime.now().isoformat()
        
        return analysis_result
        
    except Exception as e:
        import traceback
        print(f"Intelligence analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/resolve-conflict")
async def resolve_conflict(
    request: ConflictResolutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Apply conflict resolution and recalculate analysis
    """
    try:
        # Get the latest analysis
        latest_analysis = db.execute(text("""
            SELECT * FROM intelligence_analyses 
            WHERE user_id = :user_id 
            ORDER BY created_at DESC 
            LIMIT 1
        """), {"user_id": current_user.id}).fetchone()
        
        if not latest_analysis:
            raise HTTPException(status_code=404, detail="No analysis found")
        
        # Apply the resolution (this would modify goals or create recommendations)
        # For now, return a simplified response
        resolution_impact = {
            "success_rate_change": 0.11,
            "monthly_requirement_change": -1200,
            "affected_goals": [],
            "message": f"Applied {request.selected_resolution} resolution"
        }
        
        return {
            "status": "success",
            "impact": resolution_impact,
            "updated_analysis_id": latest_analysis.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resolution failed: {str(e)}")


@router.post("/simulate")
async def run_monte_carlo(
    request: MonteCarloRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Run Monte Carlo simulation for a scenario
    """
    try:
        # Get user data
        goals = db.query(Goal).filter(
            Goal.user_id == current_user.id,
            Goal.status == 'active'
        ).all()
        
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        financial_state = _get_financial_state(db, current_user.id)
        
        # Create engine and get scenarios
        engine = IntelligenceEngine()
        scenarios = engine.generate_scenarios(goals, financial_state, preferences)
        
        # Find the requested scenario
        scenario = next((s for s in scenarios if s.id == request.scenario_id), None)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        # Run simulation
        simulation_result = engine.run_monte_carlo_simulation(
            scenario=scenario,
            goals=goals,
            financial_state=financial_state,
            iterations=request.iterations
        )
        
        # Store simulation result
        simulation_id = str(uuid4())
        import json
        db.execute(text("""
            INSERT INTO monte_carlo_simulations (id, scenario_id, iterations, success_rate,
                                               p10_value, p25_value, p50_value, p75_value, p90_value, parameters)
            VALUES (:id, :scenario_id, :iterations, :success_rate, :p10, :p25, :p50, :p75, :p90, :parameters)
        """), {
            "id": simulation_id,
            "scenario_id": request.scenario_id,
            "iterations": request.iterations,
            "success_rate": simulation_result.success_rate,
            "p10": simulation_result.percentiles['p10'],
            "p25": simulation_result.percentiles['p25'],
            "p50": simulation_result.percentiles['p50'],
            "p75": simulation_result.percentiles['p75'],
            "p90": simulation_result.percentiles['p90'],
            "parameters": json.dumps(request.variables)
        })
        db.commit()
        
        return {
            "simulation_id": simulation_id,
            "iterations_run": request.iterations,
            "success_rate": simulation_result.success_rate,
            "confidence_intervals": simulation_result.percentiles,
            "mean": simulation_result.mean,
            "std_dev": simulation_result.std_dev,
            "failure_scenarios": {
                "market_volatility": 1.0 - simulation_result.success_rate,
                "insufficient_savings": max(0, 0.3 - simulation_result.success_rate),
                "timeline_pressure": max(0, 0.2 - simulation_result.success_rate)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/compare-scenarios")
async def compare_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Compare all scenarios for user
    """
    try:
        # Get user data
        goals = db.query(Goal).filter(
            Goal.user_id == current_user.id,
            Goal.status == 'active'
        ).all()
        
        if not goals:
            raise HTTPException(status_code=400, detail="No active goals found")
        
        preferences = db.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()
        
        financial_state = _get_financial_state(db, current_user.id)
        
        # Generate scenarios
        engine = IntelligenceEngine()
        scenarios = engine.generate_scenarios(goals, financial_state, preferences)
        
        # Calculate metrics for each scenario
        scenario_comparison = []
        for scenario in scenarios:
            monthly_required = sum(engine.calculate_monthly_requirement(goal, financial_state) for goal in goals)
            
            # Adjust based on scenario changes
            if 'timeline_adjustment' in [c['type'] for c in scenario.required_changes]:
                monthly_required *= 0.85  # Reduce due to timeline adjustments
            if 'income_optimization' in [c['type'] for c in scenario.required_changes]:
                monthly_required *= 0.90  # Reduce due to income increase
            
            scenario_comparison.append({
                "id": scenario.id,
                "name": scenario.name,
                "metrics": {
                    "success_rate": scenario.success_rate,
                    "monthly_required": round(monthly_required),
                    "risk_level": scenario.risk_score,
                    "lifestyle_impact": scenario.lifestyle_impact,
                    "preference_alignment": scenario.preference_alignment
                },
                "is_recommended": scenario.is_recommended,
                "required_changes": scenario.required_changes
            })
        
        # Determine best recommendation
        recommended_scenario = next((s for s in scenario_comparison if s["is_recommended"]), scenario_comparison[0])
        
        return {
            "scenarios": scenario_comparison,
            "recommendation": recommended_scenario["id"],
            "reasoning": "Best aligns with your risk tolerance and lifestyle priorities",
            "comparison_matrix": _generate_comparison_matrix(scenario_comparison)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario comparison failed: {str(e)}")


@router.get("/goal-timeline")
async def get_goal_timeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get timeline visualization data for goals
    """
    try:
        goals = db.query(Goal).filter(
            Goal.user_id == current_user.id,
            Goal.status == 'active'
        ).order_by(Goal.target_date).all()
        
        financial_state = _get_financial_state(db, current_user.id)
        
        timeline_data = []
        cumulative_savings_needed = 0
        
        for goal in goals:
            # Calculate requirements for this goal
            target_date = goal.target_date
            months_remaining = (target_date - datetime.now().date()).days / 30.44
            
            amount_needed = float(goal.target_amount)
            if goal.category == 'real_estate' and goal.params and 'down_payment_percentage' in goal.params:
                amount_needed = amount_needed * (goal.params['down_payment_percentage'] / 100)
            
            current_amount = float(goal.current_amount or 0)
            remaining_needed = amount_needed - current_amount
            
            cumulative_savings_needed += remaining_needed
            
            # Assess difficulty
            monthly_req = remaining_needed / max(1, months_remaining)
            difficulty = "high" if monthly_req > financial_state.monthly_surplus * 0.8 else "medium" if monthly_req > financial_state.monthly_surplus * 0.4 else "low"
            
            timeline_data.append({
                "goal_id": str(goal.goal_id),
                "name": goal.name,
                "category": goal.category,
                "target_date": target_date.isoformat(),
                "target_amount": amount_needed,
                "current_amount": current_amount,
                "remaining_needed": remaining_needed,
                "monthly_requirement": monthly_req,
                "difficulty": difficulty,
                "months_remaining": months_remaining,
                "cumulative_needed": cumulative_savings_needed
            })
        
        # Identify critical periods
        critical_periods = []
        goals_by_year = {}
        
        for goal_data in timeline_data:
            year = datetime.fromisoformat(goal_data["target_date"]).year
            if year not in goals_by_year:
                goals_by_year[year] = []
            goals_by_year[year].append(goal_data)
        
        for year, year_goals in goals_by_year.items():
            if len(year_goals) > 1:
                total_needed = sum(g["remaining_needed"] for g in year_goals)
                years_to_target = year - datetime.now().year
                available_savings = max(0, years_to_target * 12 * financial_state.monthly_surplus)
                
                if total_needed > available_savings:
                    critical_periods.append({
                        "year": year,
                        "type": "high_cash_requirement",
                        "total_needed": total_needed,
                        "available_savings": available_savings,
                        "shortfall": total_needed - available_savings,
                        "affected_goals": [g["name"] for g in year_goals]
                    })
        
        return {
            "timeline": timeline_data,
            "critical_periods": critical_periods,
            "overall_metrics": {
                "total_remaining_needed": sum(g["remaining_needed"] for g in timeline_data),
                "average_monthly_requirement": sum(g["monthly_requirement"] for g in timeline_data),
                "timeline_span_years": (max(g["months_remaining"] for g in timeline_data) / 12) if timeline_data else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline generation failed: {str(e)}")


def _get_advisor_data(db: Session, user_id: int) -> Dict:
    """Get advisor-level data for enhanced recommendations"""
    import json
    
    # Get all financial entries with details
    entries = db.execute(text("""
        SELECT 
            category,
            subcategory,
            description,
            amount,
            details
        FROM financial_entries
        WHERE user_id = :user_id
        AND is_active = true
        AND details IS NOT NULL
        AND details != '{}'
    """), {"user_id": user_id}).fetchall()
    
    advisor_data = {
        "mortgage": {},
        "retirement": {},
        "investments": {},
        "subscriptions": []
    }
    
    print(f"🔍 ADVISOR_DATA: Found {len(entries)} entries with details")
    
    for entry in entries:
        details = entry.details if isinstance(entry.details, dict) else json.loads(entry.details or '{}')
        print(f"🔍 ADVISOR_DATA: Processing {entry.description} - {entry.category} - Details: {details}")
        
        # Check for mortgage/loan entries 
        if ('mortgage' in entry.description.lower() or 'loan' in entry.description.lower()) and entry.category == 'liabilities':
            advisor_data["mortgage"] = {
                "balance": float(entry.amount),
                "interest_rate": details.get('interest_rate'),
                "monthly_payment": details.get('monthly_payment'),
                "term_years": details.get('term_years'),
                "start_date": details.get('start_date'),
                "lender": details.get('lender'),
                "original_loan_amount": details.get('original_loan_amount')
            }
            print(f"🔍 ADVISOR_DATA: Found mortgage data: {advisor_data['mortgage']}")
            
        # Check for 401k entries
        elif '401k' in entry.description.lower() and entry.category == 'assets':
            if not advisor_data["retirement"] or float(entry.amount) > advisor_data["retirement"].get("balance", 0):
                advisor_data["retirement"] = {
                    "balance": float(entry.amount),
                    "contribution_percent": details.get('contribution_percent'),
                    "employer_match": details.get('employer_match'),
                    "employer_match_limit": details.get('employer_match_limit'),
                    "vesting_schedule": details.get('vesting_schedule'),
                    "annual_salary": details.get('annual_salary')
                }
                print(f"🔍 ADVISOR_DATA: Found 401k data: {advisor_data['retirement']}")
            
        # Check for investment accounts
        elif entry.category == 'assets' and ('investment' in entry.description.lower() or 'mutual' in entry.description.lower() or 'etf' in entry.description.lower()):
            if not advisor_data["investments"] or float(entry.amount) > advisor_data["investments"].get("balance", 0):
                advisor_data["investments"] = {
                    "balance": float(entry.amount),
                    "stocks_percent": details.get('stocks_percent'),
                    "bonds_percent": details.get('bonds_percent'),
                    "average_expense_ratio": details.get('average_expense_ratio'),
                    "platform": details.get('platform'),
                    "platform_fees": details.get('platform_fees'),
                    "trade_fees": details.get('trade_fees')
                }
                print(f"🔍 ADVISOR_DATA: Found investment data: {advisor_data['investments']}")
    
    print(f"🔍 ADVISOR_DATA: Final advisor data: {advisor_data}")
    return advisor_data


def _get_financial_state(db: Session, user_id: int) -> FinancialState:
    """
    Get current financial state for user
    """
    # Get latest net worth snapshot
    latest_snapshot = db.query(NetWorthSnapshot).filter(
        NetWorthSnapshot.user_id == user_id
    ).order_by(desc(NetWorthSnapshot.snapshot_date)).first()
    
    if not latest_snapshot:
        # Fallback to calculating from entries
        return _calculate_financial_state_from_entries(db, user_id)
    
    # Get categorized totals
    result = db.execute(text("""
        WITH categorized_totals AS (
            SELECT 
                SUM(CASE WHEN category IN ('assets') THEN amount ELSE 0 END) as total_assets,
                SUM(CASE WHEN category IN ('liabilities') THEN amount ELSE 0 END) as total_liabilities,
                SUM(CASE WHEN category = 'income' AND frequency = 'monthly' THEN amount
                         WHEN category = 'income' AND frequency = 'annually' THEN amount/12
                         ELSE 0 END) as monthly_income,
                SUM(CASE WHEN category = 'expenses' AND frequency = 'monthly' THEN amount
                         WHEN category = 'expenses' AND frequency = 'annually' THEN amount/12  
                         ELSE 0 END) as monthly_expenses,
                SUM(CASE WHEN category = 'assets' AND subcategory IN ('checking_account', 'savings_account', 'money_market') 
                         THEN amount ELSE 0 END) as liquid_assets,
                SUM(CASE WHEN category = 'assets' AND subcategory IN ('brokerage_account', 'stocks', 'mutual_funds', 'etfs') 
                         THEN amount ELSE 0 END) as investment_assets
            FROM financial_entries 
            WHERE user_id = :user_id AND is_active = true
        )
        SELECT *, (monthly_income - monthly_expenses) as monthly_surplus
        FROM categorized_totals
    """), {"user_id": user_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=400, detail="No financial data found")
    
    return FinancialState(
        net_worth=float(latest_snapshot.net_worth),
        monthly_income=float(result.monthly_income or 0),
        monthly_expenses=float(result.monthly_expenses or 0),
        monthly_surplus=float(result.monthly_surplus or 0),
        liquid_assets=float(result.liquid_assets or 0),
        investment_assets=float(result.investment_assets or 0),
        risk_profile=6  # Default risk profile, should come from preferences
    )


def _calculate_financial_state_from_entries(db: Session, user_id: int) -> FinancialState:
    """
    Fallback: Calculate financial state from entries if no snapshot available
    """
    result = db.execute(text("""
        WITH categorized_totals AS (
            SELECT 
                SUM(CASE WHEN category = 'assets' THEN amount ELSE 0 END) as total_assets,
                SUM(CASE WHEN category = 'liabilities' THEN amount ELSE 0 END) as total_liabilities,
                SUM(CASE WHEN category = 'income' AND frequency = 'monthly' THEN amount
                         WHEN category = 'income' AND frequency = 'annually' THEN amount/12
                         ELSE 0 END) as monthly_income,
                SUM(CASE WHEN category = 'expenses' AND frequency = 'monthly' THEN amount
                         WHEN category = 'expenses' AND frequency = 'annually' THEN amount/12  
                         ELSE 0 END) as monthly_expenses,
                SUM(CASE WHEN category = 'assets' AND subcategory IN ('checking_account', 'savings_account') 
                         THEN amount ELSE 0 END) as liquid_assets,
                SUM(CASE WHEN category = 'assets' AND subcategory IN ('brokerage_account', 'stocks', 'mutual_funds') 
                         THEN amount ELSE 0 END) as investment_assets
            FROM financial_entries 
            WHERE user_id = :user_id AND is_active = true
        )
        SELECT *, 
               (total_assets - total_liabilities) as net_worth,
               (monthly_income - monthly_expenses) as monthly_surplus
        FROM categorized_totals
    """), {"user_id": user_id}).fetchone()
    
    if not result:
        # Return minimal state for new users
        return FinancialState(
            net_worth=0,
            monthly_income=0,
            monthly_expenses=0,
            monthly_surplus=0,
            liquid_assets=0,
            investment_assets=0,
            risk_profile=5
        )
    
    return FinancialState(
        net_worth=float(result.net_worth or 0),
        monthly_income=float(result.monthly_income or 0),
        monthly_expenses=float(result.monthly_expenses or 0),
        monthly_surplus=float(result.monthly_surplus or 0),
        liquid_assets=float(result.liquid_assets or 0),
        investment_assets=float(result.investment_assets or 0),
        risk_profile=6  # Default
    )


def _generate_comparison_matrix(scenarios: List[Dict]) -> Dict:
    """
    Generate a comparison matrix for scenarios
    """
    matrix = {
        "criteria": ["Success Rate", "Monthly Required", "Risk Level", "Lifestyle Impact"],
        "scenarios": {}
    }
    
    for scenario in scenarios:
        metrics = scenario["metrics"]
        matrix["scenarios"][scenario["id"]] = {
            "name": scenario["name"],
            "scores": [
                metrics["success_rate"] * 100,  # Convert to percentage
                100 - (metrics["monthly_required"] / 30000 * 100),  # Inverse score (lower is better)
                metrics["risk_level"] * 10,  # Scale to 100
                metrics["lifestyle_impact"] * 100  # Convert to percentage
            ]
        }
    
    return matrix