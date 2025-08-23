"""
WealthPath AI - Goal Templates Endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import structlog

from app.db.session import get_db
from app.models.user import User
from app.models.goal import GoalType
from app.schemas.goals import GoalTemplate, TargetSuggestion, TargetAnalysisRequest
from app.api.v1.endpoints.auth import get_current_active_user

logger = structlog.get_logger()
router = APIRouter()

# Predefined goal templates
GOAL_TEMPLATES = {
    "early_retirement": [
        {
            "id": "early_retirement_age_50",
            "template_type": GoalType.early_retirement,
            "name": "Early Retirement at 50",
            "description": "Achieve financial independence to retire at age 50 with 25x annual expenses",
            "category": "retirement",
            "suggested_timeline_months": 240,  # 20 years
            "tags": ["popular", "FIRE", "aggressive"],
            "is_popular": True,
            "difficulty_level": "advanced",
            "default_parameters": {
                "retirement_age": 50,
                "withdrawal_rate": 0.04,
                "annual_expenses_multiplier": 25,
                "inflation_rate": 0.03,
                "expected_return": 0.07
            },
            "calculation_rules": {
                "target_calculation": "annual_expenses * 25",
                "monthly_savings": "(target - current) / months_remaining / (1 + expected_return)^years",
                "success_factors": ["consistent_savings", "market_returns", "expense_control"]
            }
        },
        {
            "id": "early_retirement_age_55",
            "template_type": GoalType.early_retirement,
            "name": "Early Retirement at 55",
            "description": "Build wealth for comfortable early retirement at 55",
            "category": "retirement",
            "suggested_timeline_months": 300,  # 25 years
            "tags": ["popular", "moderate"],
            "is_popular": True,
            "difficulty_level": "intermediate",
            "default_parameters": {
                "retirement_age": 55,
                "withdrawal_rate": 0.035,
                "annual_expenses_multiplier": 28,
                "inflation_rate": 0.03,
                "expected_return": 0.06
            },
            "calculation_rules": {
                "target_calculation": "annual_expenses * 28",
                "monthly_savings": "(target - current) / months_remaining / (1 + expected_return)^years",
                "success_factors": ["steady_growth", "diversification", "long_horizon"]
            }
        }
    ],
    "home_purchase": [
        {
            "id": "first_home_20_percent_down",
            "template_type": GoalType.home_purchase,
            "name": "First Home Purchase (20% Down)",
            "description": "Save for a 20% down payment plus closing costs for your first home",
            "category": "real_estate",
            "suggested_timeline_months": 60,  # 5 years
            "tags": ["first_home", "popular"],
            "is_popular": True,
            "difficulty_level": "intermediate",
            "default_parameters": {
                "down_payment_percentage": 0.20,
                "closing_costs_percentage": 0.03,
                "home_price_growth": 0.04,
                "emergency_buffer": 0.15
            },
            "calculation_rules": {
                "target_calculation": "home_price * (down_payment_percentage + closing_costs_percentage + emergency_buffer)",
                "monthly_savings": "target / months_remaining * (1 + home_price_growth)^years",
                "success_factors": ["stable_income", "credit_score", "market_timing"]
            }
        },
        {
            "id": "home_upgrade",
            "template_type": GoalType.home_purchase,
            "name": "Home Upgrade",
            "description": "Save for upgrading to a larger or better home",
            "category": "real_estate",
            "suggested_timeline_months": 84,  # 7 years
            "tags": ["upgrade", "family"],
            "is_popular": False,
            "difficulty_level": "intermediate",
            "default_parameters": {
                "price_difference": 1.5,  # 50% more expensive
                "down_payment_percentage": 0.20,
                "closing_costs_percentage": 0.03,
                "current_equity": 0.30
            },
            "calculation_rules": {
                "target_calculation": "(new_home_price - current_equity) * down_payment_percentage + closing_costs",
                "monthly_savings": "target / months_remaining",
                "success_factors": ["equity_growth", "income_stability", "market_conditions"]
            }
        }
    ],
    "education": [
        {
            "id": "college_education_4_year",
            "template_type": GoalType.education,
            "name": "College Education Fund",
            "description": "Save for a 4-year college education at a public university",
            "category": "education",
            "suggested_timeline_months": 216,  # 18 years
            "tags": ["college", "popular", "529_plan"],
            "is_popular": True,
            "difficulty_level": "intermediate",
            "default_parameters": {
                "annual_tuition_growth": 0.05,
                "years_of_education": 4,
                "current_annual_cost": 25000,
                "room_board_multiplier": 1.4
            },
            "calculation_rules": {
                "target_calculation": "current_annual_cost * room_board_multiplier * years_of_education * (1 + tuition_growth)^years_to_college",
                "monthly_savings": "target / months_remaining / (1 + investment_return)^years",
                "success_factors": ["early_start", "tax_advantages", "compound_growth"]
            }
        },
        {
            "id": "graduate_school",
            "template_type": GoalType.education,
            "name": "Graduate School Fund",
            "description": "Save for MBA or professional graduate degree",
            "category": "education",
            "suggested_timeline_months": 60,  # 5 years
            "tags": ["graduate", "career_advancement"],
            "is_popular": False,
            "difficulty_level": "intermediate",
            "default_parameters": {
                "program_duration_years": 2,
                "annual_tuition": 60000,
                "living_expenses": 30000,
                "opportunity_cost_factor": 0.5
            },
            "calculation_rules": {
                "target_calculation": "(annual_tuition + living_expenses) * program_duration_years",
                "monthly_savings": "target / months_remaining",
                "success_factors": ["career_planning", "ROI_analysis", "scholarship_opportunities"]
            }
        }
    ],
    "emergency_fund": [
        {
            "id": "emergency_fund_6_months",
            "template_type": GoalType.emergency_fund,
            "name": "6-Month Emergency Fund",
            "description": "Build an emergency fund covering 6 months of living expenses",
            "category": "security",
            "suggested_timeline_months": 24,  # 2 years
            "tags": ["essential", "popular", "foundation"],
            "is_popular": True,
            "difficulty_level": "beginner",
            "default_parameters": {
                "months_of_expenses": 6,
                "monthly_expenses": 4000,
                "liquidity_requirement": 1.0,
                "yield_expectation": 0.02
            },
            "calculation_rules": {
                "target_calculation": "monthly_expenses * months_of_expenses",
                "monthly_savings": "target / months_remaining",
                "success_factors": ["consistency", "liquidity", "discipline"]
            }
        },
        {
            "id": "emergency_fund_12_months",
            "template_type": GoalType.emergency_fund,
            "name": "12-Month Emergency Fund",
            "description": "Build a robust emergency fund covering a full year of expenses",
            "category": "security",
            "suggested_timeline_months": 36,  # 3 years
            "tags": ["comprehensive", "conservative"],
            "is_popular": False,
            "difficulty_level": "intermediate",
            "default_parameters": {
                "months_of_expenses": 12,
                "monthly_expenses": 4000,
                "liquidity_requirement": 0.8,
                "yield_expectation": 0.025
            },
            "calculation_rules": {
                "target_calculation": "monthly_expenses * months_of_expenses",
                "monthly_savings": "target / months_remaining",
                "success_factors": ["job_stability", "risk_management", "peace_of_mind"]
            }
        }
    ],
    "debt_payoff": [
        {
            "id": "credit_card_payoff",
            "template_type": GoalType.debt_payoff,
            "name": "Credit Card Debt Payoff",
            "description": "Eliminate high-interest credit card debt",
            "category": "debt_reduction",
            "suggested_timeline_months": 24,  # 2 years
            "tags": ["high_priority", "debt_freedom"],
            "is_popular": True,
            "difficulty_level": "intermediate",
            "default_parameters": {
                "average_interest_rate": 0.18,
                "minimum_payment_ratio": 0.02,
                "avalanche_method": True,
                "extra_payment_target": 0.10
            },
            "calculation_rules": {
                "target_calculation": "current_debt_balance",
                "monthly_payment": "max(minimum_payment, target / months_remaining * (1 + interest_rate/12))",
                "success_factors": ["payment_discipline", "interest_savings", "debt_avalanche"]
            }
        },
        {
            "id": "student_loan_payoff",
            "template_type": GoalType.debt_payoff,
            "name": "Student Loan Early Payoff",
            "description": "Pay off student loans ahead of schedule",
            "category": "debt_reduction",
            "suggested_timeline_months": 120,  # 10 years
            "tags": ["education_debt", "long_term"],
            "is_popular": False,
            "difficulty_level": "intermediate",
            "default_parameters": {
                "average_interest_rate": 0.05,
                "tax_deduction_benefit": 0.22,
                "refinance_consideration": True,
                "extra_payment_percentage": 0.20
            },
            "calculation_rules": {
                "target_calculation": "remaining_principal",
                "monthly_payment": "standard_payment * (1 + extra_payment_percentage)",
                "success_factors": ["interest_rate_optimization", "tax_planning", "career_growth"]
            }
        }
    ]
}


@router.get("/", response_model=List[GoalTemplate])
def get_goal_templates(
    goal_type: Optional[GoalType] = Query(None, description="Filter by goal type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty_level: Optional[str] = Query(None, description="Filter by difficulty"),
    popular_only: bool = Query(False, description="Show only popular templates"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get available goal templates with filtering
    """
    all_templates = []
    
    # Flatten all templates
    for templates_by_type in GOAL_TEMPLATES.values():
        all_templates.extend(templates_by_type)
    
    # Apply filters
    filtered_templates = all_templates
    
    if goal_type:
        filtered_templates = [t for t in filtered_templates if t["template_type"] == goal_type]
    
    if category:
        filtered_templates = [t for t in filtered_templates if t["category"] == category]
    
    if difficulty_level:
        filtered_templates = [t for t in filtered_templates if t["difficulty_level"] == difficulty_level]
    
    if popular_only:
        filtered_templates = [t for t in filtered_templates if t["is_popular"]]
    
    return [GoalTemplate(**template) for template in filtered_templates]


@router.get("/{template_id}", response_model=GoalTemplate)
def get_goal_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get specific goal template by ID
    """
    # Search for template across all types
    for templates_by_type in GOAL_TEMPLATES.values():
        for template in templates_by_type:
            if template["id"] == template_id:
                return GoalTemplate(**template)
    
    from fastapi import HTTPException, status
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Goal template not found"
    )


@router.post("/suggest-target", response_model=TargetSuggestion)
def suggest_goal_target(
    request: TargetAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    AI-powered target suggestion for goals
    """
    # Get relevant templates
    relevant_templates = GOAL_TEMPLATES.get(request.goal_type.value, [])
    
    if not relevant_templates:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No templates available for goal type: {request.goal_type.value}"
        )
    
    # Select best template based on user profile
    selected_template = _select_best_template(relevant_templates, request)
    
    # Calculate suggested amounts based on template and user data
    suggestion = _calculate_target_suggestion(selected_template, request, current_user)
    
    logger.info(
        "Target suggestion generated",
        user_id=current_user.id,
        goal_type=request.goal_type.value,
        suggested_amount=float(suggestion.suggested_amount)
    )
    
    return suggestion


@router.get("/categories/list")
def get_template_categories(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all available template categories
    """
    categories = set()
    for templates_by_type in GOAL_TEMPLATES.values():
        for template in templates_by_type:
            categories.add(template["category"])
    
    return {
        "categories": sorted(list(categories)),
        "goal_types": [goal_type.value for goal_type in GoalType],
        "difficulty_levels": ["beginner", "intermediate", "advanced"]
    }


# HELPER FUNCTIONS

def _select_best_template(templates: List[dict], request: TargetAnalysisRequest) -> dict:
    """Select the most appropriate template based on user profile"""
    # Simple scoring algorithm - would be more sophisticated in production
    best_template = templates[0]
    best_score = 0
    
    for template in templates:
        score = 0
        
        # Age-based scoring
        if request.user_age:
            if request.goal_type == GoalType.early_retirement:
                # Younger users get more aggressive templates
                if request.user_age < 35 and "aggressive" in template.get("tags", []):
                    score += 3
                elif request.user_age >= 35 and "moderate" in template.get("tags", []):
                    score += 2
        
        # Risk tolerance scoring
        if request.risk_tolerance:
            if request.risk_tolerance >= 7 and template["difficulty_level"] == "advanced":
                score += 2
            elif 4 <= request.risk_tolerance <= 6 and template["difficulty_level"] == "intermediate":
                score += 2
            elif request.risk_tolerance <= 3 and template["difficulty_level"] == "beginner":
                score += 2
        
        # Income-based scoring
        if request.annual_income:
            # Higher income can handle more aggressive goals
            if request.annual_income >= 100000 and "aggressive" in template.get("tags", []):
                score += 1
        
        # Popular templates get slight boost
        if template.get("is_popular", False):
            score += 1
        
        if score > best_score:
            best_score = score
            best_template = template
    
    return best_template


def _calculate_target_suggestion(template: dict, request: TargetAnalysisRequest, user: User) -> TargetSuggestion:
    """Calculate target amount and timeline based on template and user data"""
    from decimal import Decimal
    import math
    
    # Base calculations from template
    params = template["default_parameters"]
    
    # Calculate target amount based on goal type and user data
    if request.goal_type == GoalType.early_retirement:
        # Base on annual expenses or income
        annual_expenses = float(request.annual_income or 75000) * 0.7  # Assume 70% of income for expenses
        suggested_amount = Decimal(str(annual_expenses * params.get("annual_expenses_multiplier", 25)))
        
    elif request.goal_type == GoalType.home_purchase:
        # Base on income multiples (typical 3-5x annual income)
        income_multiple = 4.0  # Conservative multiple
        home_price = float(request.annual_income or 75000) * income_multiple
        down_payment = home_price * params.get("down_payment_percentage", 0.20)
        closing_costs = home_price * params.get("closing_costs_percentage", 0.03)
        suggested_amount = Decimal(str(down_payment + closing_costs))
        
    elif request.goal_type == GoalType.education:
        # Fixed based on current education costs
        annual_cost = params.get("current_annual_cost", 25000)
        years = params.get("years_of_education", 4)
        inflation_growth = params.get("annual_tuition_growth", 0.05)
        years_to_start = 18  # Default assumption
        
        # Apply inflation growth
        future_annual_cost = annual_cost * ((1 + inflation_growth) ** years_to_start)
        suggested_amount = Decimal(str(future_annual_cost * years))
        
    elif request.goal_type == GoalType.emergency_fund:
        # Base on expenses (income * 70%)
        monthly_expenses = float(request.annual_income or 75000) * 0.7 / 12
        months = params.get("months_of_expenses", 6)
        suggested_amount = Decimal(str(monthly_expenses * months))
        
    elif request.goal_type == GoalType.debt_payoff:
        # Would typically use actual debt amounts - using placeholder
        suggested_amount = Decimal(str(float(request.annual_income or 75000) * 0.2))  # 20% of income as debt
        
    else:
        suggested_amount = Decimal("50000")  # Default fallback
    
    # Adjust timeline based on template and user capacity
    base_months = template["suggested_timeline_months"]
    
    # Adjust based on current savings and income
    if request.current_savings and request.annual_income:
        savings_rate = float(request.current_savings) / float(request.annual_income)
        if savings_rate > 0.2:  # High saver
            timeline_months = int(base_months * 0.8)  # 20% faster
        elif savings_rate < 0.05:  # Low saver
            timeline_months = int(base_months * 1.3)  # 30% longer
        else:
            timeline_months = base_months
    else:
        timeline_months = base_months
    
    # Calculate confidence based on feasibility
    monthly_required = float(suggested_amount) / timeline_months
    monthly_capacity = float(request.annual_income or 75000) * 0.2 / 12  # 20% savings rate
    
    if monthly_required <= monthly_capacity * 0.5:
        confidence = Decimal("0.90")  # Very achievable
    elif monthly_required <= monthly_capacity:
        confidence = Decimal("0.75")  # Achievable
    elif monthly_required <= monthly_capacity * 1.5:
        confidence = Decimal("0.60")  # Challenging
    else:
        confidence = Decimal("0.40")  # Very challenging
    
    # Generate reasoning
    reasoning = f"Based on {template['name']} template and your profile, this target represents a balanced approach. "
    if confidence >= Decimal("0.8"):
        reasoning += "This goal appears very achievable with your current financial capacity."
    elif confidence >= Decimal("0.6"):
        reasoning += "This goal is achievable with disciplined saving and planning."
    else:
        reasoning += "This goal is ambitious and may require lifestyle adjustments or extended timeline."
    
    return TargetSuggestion(
        goal_type=request.goal_type,
        suggested_amount=suggested_amount,
        suggested_timeline_months=timeline_months,
        confidence_score=confidence,
        reasoning=reasoning,
        assumptions={
            "annual_return": params.get("expected_return", 0.07),
            "inflation_rate": params.get("inflation_rate", 0.03),
            "savings_rate": 0.20,
            "template_used": template["name"]
        },
        alternative_scenarios=[
            {
                "name": "Conservative",
                "timeline_months": int(timeline_months * 1.5),
                "monthly_required": monthly_required * 0.67,
                "success_probability": 0.85
            },
            {
                "name": "Aggressive", 
                "timeline_months": int(timeline_months * 0.75),
                "monthly_required": monthly_required * 1.33,
                "success_probability": 0.60
            }
        ]
    )