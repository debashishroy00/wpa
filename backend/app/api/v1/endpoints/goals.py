"""
WealthPath AI - Goal Management Endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timezone
from decimal import Decimal
import structlog
import json

from app.db.session import get_db
from app.models.user import User
from app.models.goal import (
    FinancialGoal, GoalScenario, ActionPlan, GoalMilestone,
    GoalType, GoalStatus, ActionPriority, ActionStatus
)
from app.schemas.goals import (
    FinancialGoalCreate, FinancialGoalUpdate, FinancialGoalResponse,
    GoalScenarioCreate, GoalScenarioResponse,
    ActionPlanCreate, ActionPlanResponse,
    GoalMilestoneCreate, GoalMilestoneResponse,
    GoalAnalytics, GoalProgressSummary
)
from app.api.v1.endpoints.auth import get_current_active_user

logger = structlog.get_logger()
router = APIRouter()


# FINANCIAL GOALS CRUD OPERATIONS

@router.get("/", response_model=List[FinancialGoalResponse])
def get_user_goals(
    status: Optional[GoalStatus] = Query(None, description="Filter by goal status"),
    goal_type: Optional[GoalType] = Query(None, description="Filter by goal type"),
    limit: int = Query(50, ge=1, le=100, description="Limit number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all user financial goals with filtering
    """
    query = db.query(FinancialGoal).filter(
        FinancialGoal.user_id == current_user.id
    )
    
    # Apply filters
    if status:
        query = query.filter(FinancialGoal.status == status)
    if goal_type:
        query = query.filter(FinancialGoal.goal_type == goal_type)
    
    # Order by priority (1 = highest) then created date
    goals = query.order_by(
        FinancialGoal.priority.asc(),
        FinancialGoal.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return [_format_goal_response(goal) for goal in goals]


@router.post("/", response_model=FinancialGoalResponse, status_code=status.HTTP_201_CREATED)
def create_financial_goal(
    goal_data: FinancialGoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new financial goal with AI analysis
    """
    # Create the financial goal
    db_goal = FinancialGoal(
        user_id=current_user.id,
        goal_type=goal_data.goal_type,
        name=goal_data.name,
        description=goal_data.description,
        target_amount=goal_data.target_amount,
        current_amount=goal_data.current_amount or Decimal('0.00'),
        target_date=goal_data.target_date,
        parameters=json.dumps(goal_data.parameters) if goal_data.parameters else None,
        priority=goal_data.priority or 1,
        status=GoalStatus.draft
    )
    
    # Calculate initial analysis
    db_goal.monthly_target = _calculate_monthly_target(
        db_goal.target_amount - db_goal.current_amount,
        db_goal.target_date
    )
    
    # Basic feasibility analysis
    feasibility = _analyze_goal_feasibility(db_goal, current_user, db)
    db_goal.feasibility_score = feasibility['score']
    db_goal.success_probability = feasibility['probability']
    db_goal.risk_level = feasibility['risk_level']
    
    db_goal.last_analyzed_at = datetime.now(timezone.utc)
    
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    
    # Create baseline scenario
    _create_baseline_scenario(db_goal, db)
    
    logger.info(
        "Financial goal created",
        user_id=current_user.id,
        goal_id=db_goal.id,
        goal_type=goal_data.goal_type.value,
        target_amount=float(goal_data.target_amount)
    )
    
    return _format_goal_response(db_goal)


@router.get("/{goal_id}", response_model=FinancialGoalResponse)
def get_financial_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get specific financial goal by ID
    """
    goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == current_user.id
        )
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found"
        )
    
    return _format_goal_response(goal)


@router.put("/{goal_id}", response_model=FinancialGoalResponse)
def update_financial_goal(
    goal_id: int,
    goal_update: FinancialGoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update financial goal
    """
    db_goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == current_user.id
        )
    ).first()
    
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found"
        )
    
    # Update fields if provided
    update_data = goal_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'parameters' and value is not None:
            setattr(db_goal, field, json.dumps(value))
        else:
            setattr(db_goal, field, value)
    
    # Recalculate monthly target if target changed
    if 'target_amount' in update_data or 'target_date' in update_data:
        db_goal.monthly_target = _calculate_monthly_target(
            db_goal.target_amount - db_goal.current_amount,
            db_goal.target_date
        )
        
        # Re-analyze feasibility
        feasibility = _analyze_goal_feasibility(db_goal, current_user, db)
        db_goal.feasibility_score = feasibility['score']
        db_goal.success_probability = feasibility['probability']
        db_goal.risk_level = feasibility['risk_level']
        db_goal.last_analyzed_at = datetime.now(timezone.utc)
    
    db_goal.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_goal)
    
    logger.info(
        "Financial goal updated",
        user_id=current_user.id,
        goal_id=goal_id,
        updated_fields=list(update_data.keys())
    )
    
    return _format_goal_response(db_goal)


@router.delete("/{goal_id}")
def delete_financial_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete financial goal (soft delete - set to abandoned)
    """
    db_goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == current_user.id
        )
    ).first()
    
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found"
        )
    
    db_goal.status = GoalStatus.abandoned
    db_goal.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    
    logger.info("Financial goal deleted", user_id=current_user.id, goal_id=goal_id)
    return {"message": "Financial goal deleted successfully"}


# GOAL ANALYTICS AND PROGRESS

@router.get("/analytics/summary", response_model=GoalAnalytics)
def get_goals_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get comprehensive goal analytics summary
    """
    goals = db.query(FinancialGoal).filter(
        FinancialGoal.user_id == current_user.id
    ).all()
    
    if not goals:
        return GoalAnalytics(
            user_id=current_user.id,
            total_goals=0,
            active_goals=0,
            achieved_goals=0,
            total_target_amount=Decimal('0.00'),
            total_current_amount=Decimal('0.00'),
            overall_progress=Decimal('0.00'),
            goals_on_track=0,
            high_risk_goals=0,
            average_feasibility=Decimal('0.00')
        )
    
    # Calculate analytics
    active_goals = [g for g in goals if g.status == GoalStatus.active]
    achieved_goals = [g for g in goals if g.status == GoalStatus.achieved]
    
    total_target = sum(g.target_amount for g in goals)
    total_current = sum(g.current_amount for g in goals)
    overall_progress = (total_current / total_target * 100) if total_target > 0 else Decimal('0.00')
    
    goals_on_track = len([g for g in active_goals if g.success_probability and g.success_probability >= 0.7])
    high_risk_goals = len([g for g in active_goals if g.risk_level == 'high'])
    
    feasibility_scores = [g.feasibility_score for g in goals if g.feasibility_score]
    avg_feasibility = sum(feasibility_scores) / len(feasibility_scores) if feasibility_scores else Decimal('0.00')
    
    return GoalAnalytics(
        user_id=current_user.id,
        total_goals=len(goals),
        active_goals=len(active_goals),
        achieved_goals=len(achieved_goals),
        total_target_amount=total_target,
        total_current_amount=total_current,
        overall_progress=overall_progress,
        goals_on_track=goals_on_track,
        high_risk_goals=high_risk_goals,
        average_feasibility=avg_feasibility
    )


@router.get("/{goal_id}/progress", response_model=GoalProgressSummary)
def get_goal_progress(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get detailed progress summary for a specific goal
    """
    goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == current_user.id
        )
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found"
        )
    
    # Calculate progress metrics
    progress_percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else Decimal('0.00')
    remaining_amount = goal.target_amount - goal.current_amount
    
    # Time calculations
    today = datetime.now(timezone.utc).date()
    target_date = goal.target_date.date() if isinstance(goal.target_date, datetime) else goal.target_date
    days_remaining = (target_date - today).days if target_date > today else 0
    months_remaining = max(1, days_remaining / 30.44)  # Average days per month
    
    # Required monthly contribution
    required_monthly = remaining_amount / months_remaining if months_remaining > 0 else remaining_amount
    
    return GoalProgressSummary(
        goal_id=goal.id,
        progress_percentage=progress_percentage,
        current_amount=goal.current_amount,
        target_amount=goal.target_amount,
        remaining_amount=remaining_amount,
        days_remaining=days_remaining,
        months_remaining=months_remaining,
        required_monthly_contribution=required_monthly,
        is_on_track=goal.success_probability >= 0.7 if goal.success_probability else False,
        risk_level=goal.risk_level,
        feasibility_score=goal.feasibility_score
    )


@router.get("/{goal_id}/scenarios", response_model=List[GoalScenarioResponse])
def get_goal_scenarios(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all scenarios for a specific goal
    """
    goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == current_user.id
        )
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found"
        )
    
    scenarios = db.query(GoalScenario).filter(
        GoalScenario.goal_id == goal_id
    ).order_by(GoalScenario.is_baseline.desc(), GoalScenario.created_at.desc()).all()
    
    return [_format_scenario_response(scenario) for scenario in scenarios]


@router.post("/{goal_id}/analyze")
def trigger_goal_analysis(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Trigger comprehensive AI analysis for goal
    """
    goal = db.query(FinancialGoal).filter(
        and_(
            FinancialGoal.id == goal_id,
            FinancialGoal.user_id == current_user.id
        )
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found"
        )
    
    # Re-run feasibility analysis
    feasibility = _analyze_goal_feasibility(goal, current_user, db)
    goal.feasibility_score = feasibility['score']
    goal.success_probability = feasibility['probability']
    goal.risk_level = feasibility['risk_level']
    goal.last_analyzed_at = datetime.now(timezone.utc)
    
    db.commit()
    
    logger.info("Goal analysis triggered", user_id=current_user.id, goal_id=goal_id)
    
    return {
        "goal_id": goal_id,
        "analysis_completed": True,
        "feasibility_score": float(feasibility['score']),
        "success_probability": float(feasibility['probability']),
        "risk_level": feasibility['risk_level'],
        "analyzed_at": goal.last_analyzed_at.isoformat()
    }


# HELPER FUNCTIONS

def _calculate_monthly_target(remaining_amount: Decimal, target_date: datetime) -> Decimal:
    """Calculate required monthly contribution"""
    today = datetime.now(timezone.utc).date()
    target_date_val = target_date.date() if isinstance(target_date, datetime) else target_date
    days_remaining = max(1, (target_date_val - today).days)
    months_remaining = max(1, days_remaining / 30.44)
    return remaining_amount / months_remaining


def _analyze_goal_feasibility(goal: FinancialGoal, user: User, db: Session) -> dict:
    """Basic feasibility analysis for goal"""
    # Simple heuristic-based analysis
    months_to_goal = max(1, (goal.target_date.date() - datetime.now(timezone.utc).date()).days / 30.44)
    monthly_required = goal.monthly_target
    
    # Estimate feasibility based on monthly requirement vs typical savings rates
    # This is a simplified model - would be enhanced with ML in production
    feasibility_score = min(1.0, max(0.1, 1.0 - (float(monthly_required) / 5000)))  # Assume $5k monthly limit
    success_probability = feasibility_score * 0.9  # Slightly lower than feasibility
    
    if feasibility_score >= 0.8:
        risk_level = "low"
    elif feasibility_score >= 0.6:
        risk_level = "medium"
    else:
        risk_level = "high"
    
    return {
        'score': Decimal(str(feasibility_score)),
        'probability': Decimal(str(success_probability)),
        'risk_level': risk_level
    }


def _create_baseline_scenario(goal: FinancialGoal, db: Session):
    """Create baseline scenario for new goal"""
    baseline_assumptions = {
        'monthly_contribution': float(goal.monthly_target),
        'interest_rate': 0.07,  # 7% annual return assumption
        'inflation_rate': 0.03,  # 3% annual inflation
        'contribution_growth': 0.03  # 3% annual contribution growth
    }
    
    scenario = GoalScenario(
        goal_id=goal.id,
        scenario_name="Baseline Projection",
        description="Conservative baseline scenario with standard assumptions",
        is_baseline=True,
        assumptions=json.dumps(baseline_assumptions),
        projected_end_value=goal.target_amount,
        projected_end_date=goal.target_date,
        required_monthly_amount=goal.monthly_target,
        success_probability=goal.success_probability,
        confidence_score=Decimal('0.75'),
        model_version="1.0",
        calculation_method="compound_growth"
    )
    
    db.add(scenario)
    db.commit()


def _format_goal_response(goal: FinancialGoal) -> FinancialGoalResponse:
    """Format goal model as response"""
    return FinancialGoalResponse(
        id=goal.id,
        user_id=goal.user_id,
        goal_type=goal.goal_type,
        name=goal.name,
        description=goal.description,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        target_date=goal.target_date,
        parameters=json.loads(goal.parameters) if goal.parameters else {},
        progress_percentage=goal.progress_percentage,
        monthly_target=goal.monthly_target,
        feasibility_score=goal.feasibility_score,
        success_probability=goal.success_probability,
        risk_level=goal.risk_level,
        status=goal.status,
        priority=goal.priority,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
        achieved_at=goal.achieved_at,
        last_analyzed_at=goal.last_analyzed_at
    )


def _format_scenario_response(scenario: GoalScenario) -> GoalScenarioResponse:
    """Format scenario model as response"""
    return GoalScenarioResponse(
        id=scenario.id,
        goal_id=scenario.goal_id,
        scenario_name=scenario.scenario_name,
        description=scenario.description,
        is_baseline=scenario.is_baseline,
        assumptions=json.loads(scenario.assumptions),
        projected_end_value=scenario.projected_end_value,
        projected_end_date=scenario.projected_end_date,
        required_monthly_amount=scenario.required_monthly_amount,
        success_probability=scenario.success_probability,
        confidence_score=scenario.confidence_score,
        model_version=scenario.model_version,
        created_at=scenario.created_at
    )