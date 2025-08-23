"""
Step 4: Deterministic Plan Engine API Endpoints
Pure calculation endpoints with no subjective language
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
from decimal import Decimal

from app.db.session import get_db
from app.models.plan_engine import PlanInput, PlanOutput
from app.services.plan_engine import DeterministicPlanEngine
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User


router = APIRouter()


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


@router.post("/calculate", response_model=PlanOutput)
async def calculate_plan(
    plan_input: PlanInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PlanOutput:
    """
    Calculate deterministic financial plan
    No subjective language - pure calculations only
    """
    try:
        engine = DeterministicPlanEngine()
        plan_output = engine.calculate_plan(plan_input)
        
        # Add client info for LLM context using authenticated user
        from app.models.plan_engine import ClientInfo
        if current_user:
            annual_income = float(sum(plan_input.current_state.income.values()))
            client_info = ClientInfo(
                name=f"{current_user.first_name} {current_user.last_name}".strip() if current_user.first_name else current_user.email,
                age=plan_input.goals.current_age or 35,
                current_income=annual_income,
                user_id=current_user.id
            )
            plan_output.client_info = client_info
            print(f"✅ Added client_info to plan output: {client_info.name}, age {client_info.age}, income ${client_info.current_income:,.0f}")
        
        # Log calculation for audit trail (temporarily disabled due to DB session error)
        try:
            _log_calculation(db, current_user.id, plan_input, plan_output)
        except Exception as log_error:
            # Don't fail the entire calculation due to logging issues
            print(f"Logging error (non-critical): {log_error}")
        
        return plan_output
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Plan calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/validate-input")
async def validate_input(
    plan_input: PlanInput,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate input data before calculation
    Returns validation results and any warnings
    """
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check allocation sums to 100%
    if plan_input.current_state.current_allocation:
        total = sum(plan_input.current_state.current_allocation.values())
        if abs(total - 1.0) > 0.01:
            validation_results["errors"].append(f"allocation_sum_error: {total}")
            validation_results["valid"] = False
    
    # Check debt to income ratio
    total_debt = sum(plan_input.current_state.liabilities.values())
    total_income = sum(plan_input.current_state.income.values())
    if total_income > 0:
        dti = float(total_debt) / float(total_income)
        if dti > plan_input.constraints.max_debt_to_income:
            validation_results["warnings"].append(f"high_dti: {dti:.2f}")
    
    # Check emergency fund adequacy
    monthly_expenses = sum(plan_input.current_state.expenses.values())
    cash_reserves = sum(
        v for k, v in plan_input.current_state.assets.items()
        if 'cash' in k.lower() or 'savings' in k.lower()
    )
    months_coverage = float(cash_reserves) / float(monthly_expenses) if monthly_expenses > 0 else 0
    if months_coverage < 3:
        validation_results["warnings"].append(f"low_emergency_fund: {months_coverage:.1f}_months")
    
    # Check if goals are achievable
    years_to_goal = plan_input.goals.retirement_age - (plan_input.goals.current_age or 40)
    if years_to_goal < 5:
        validation_results["warnings"].append("short_time_horizon")
    
    gap = plan_input.goals.target_net_worth - plan_input.current_state.net_worth
    required_annual_growth = float(gap) / years_to_goal if years_to_goal > 0 else float(gap)
    annual_capacity = float(total_income) - float(monthly_expenses * 12)
    
    if required_annual_growth > annual_capacity * 2:
        validation_results["warnings"].append("aggressive_target")
    
    return validation_results


@router.get("/limits")
async def get_contribution_limits(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current contribution limits and tax brackets
    Returns IRS limits and thresholds
    """
    return {
        "contribution_limits": {
            "401k": 23000,
            "401k_catch_up": 7500,
            "ira": 7000,
            "ira_catch_up": 1000,
            "hsa_individual": 4150,
            "hsa_family": 8300,
            "hsa_catch_up": 1000,
            "saver_credit_agi_single": 36500,
            "saver_credit_agi_married": 73000
        },
        "tax_brackets_single": {
            "10%": 11600,
            "12%": 47150,
            "22%": 100525,
            "24%": 191950,
            "32%": 243725,
            "35%": 609350,
            "37%": 99999999
        },
        "tax_brackets_married": {
            "10%": 23200,
            "12%": 94300,
            "22%": 201050,
            "24%": 383900,
            "32%": 487450,
            "35%": 731200,
            "37%": 99999999
        },
        "standard_deduction": {
            "single": 14600,
            "married": 29200,
            "head_of_household": 21900
        },
        "social_security": {
            "wage_base": 168600,
            "rate_employee": 0.062,
            "rate_employer": 0.062,
            "medicare_rate": 0.0145,
            "medicare_additional": 0.009,
            "medicare_threshold_single": 200000,
            "medicare_threshold_married": 250000
        }
    }


@router.post("/stress-test")
async def run_stress_test(
    plan_input: PlanInput,
    scenarios: Dict[str, float] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Run stress tests on the financial plan
    Tests multiple adverse scenarios
    """
    if scenarios is None:
        scenarios = {
            "market_drop_20": -0.20,
            "market_drop_30": -0.30,
            "market_drop_40": -0.40,
            "market_drop_50": -0.50,
            "job_loss_6mo": -0.50,  # Income reduction
            "inflation_5pct": 0.05,
            "inflation_7pct": 0.07,
            "rate_increase_2pct": 0.02
        }
    
    engine = DeterministicPlanEngine()
    base_plan = engine.calculate_plan(plan_input)
    
    stress_results = {
        "base_success_rate": base_plan.gap_analysis.monte_carlo_success_rate,
        "scenarios": {}
    }
    
    for scenario_name, impact in scenarios.items():
        # Modify input based on scenario
        stressed_input = _apply_stress_scenario(plan_input, scenario_name, impact)
        stressed_plan = engine.calculate_plan(stressed_input)
        
        stress_results["scenarios"][scenario_name] = {
            "impact": impact,
            "success_rate": stressed_plan.gap_analysis.monte_carlo_success_rate,
            "success_rate_change": stressed_plan.gap_analysis.monte_carlo_success_rate - base_plan.gap_analysis.monte_carlo_success_rate,
            "net_worth_impact": float(stressed_plan.gap_analysis.current_amount - base_plan.gap_analysis.current_amount)
        }
    
    return stress_results


def _apply_stress_scenario(plan_input: PlanInput, scenario: str, impact: float) -> PlanInput:
    """Apply stress scenario to input data"""
    import copy
    stressed = copy.deepcopy(plan_input)
    
    if "market_drop" in scenario:
        # Reduce asset values
        for asset in stressed.current_state.assets:
            if 'real_estate' not in asset.lower():
                stressed.current_state.assets[asset] = Decimal(float(stressed.current_state.assets[asset]) * (1 + impact))
    
    elif "job_loss" in scenario:
        # Reduce income
        for income_source in stressed.current_state.income:
            if 'salary' in income_source.lower():
                stressed.current_state.income[income_source] = Decimal(float(stressed.current_state.income[income_source]) * (1 + impact))
    
    elif "inflation" in scenario:
        # Increase expenses
        for expense in stressed.current_state.expenses:
            stressed.current_state.expenses[expense] = Decimal(float(stressed.current_state.expenses[expense]) * (1 + abs(impact)))
    
    elif "rate_increase" in scenario:
        # Increase debt rates (reflected in constraints)
        stressed.constraints.tax_bracket = min(1.0, stressed.constraints.tax_bracket + abs(impact))
    
    # Recalculate net worth
    stressed.current_state.net_worth = sum(stressed.current_state.assets.values()) - sum(stressed.current_state.liabilities.values())
    
    return stressed


def _log_calculation(db: Session, user_id: int, plan_input: PlanInput, plan_output: PlanOutput):
    """Log calculation for audit trail"""
    # This would store in a calculations audit table
    # For now, just a placeholder
    pass


@router.get("/historical-returns")
async def get_historical_returns(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get historical return data for asset classes
    Used for Monte Carlo simulations
    """
    return {
        "asset_classes": {
            "us_stocks": {
                "annual_mean": 0.10,
                "annual_std": 0.16,
                "worst_year": -0.37,
                "best_year": 0.32,
                "data_source": "sp500_1928_2024"
            },
            "intl_stocks": {
                "annual_mean": 0.08,
                "annual_std": 0.18,
                "worst_year": -0.43,
                "best_year": 0.39,
                "data_source": "msci_eafe_1970_2024"
            },
            "bonds": {
                "annual_mean": 0.04,
                "annual_std": 0.05,
                "worst_year": -0.13,
                "best_year": 0.16,
                "data_source": "agg_bond_1976_2024"
            },
            "reits": {
                "annual_mean": 0.08,
                "annual_std": 0.19,
                "worst_year": -0.37,
                "best_year": 0.38,
                "data_source": "nareit_1972_2024"
            },
            "cash": {
                "annual_mean": 0.02,
                "annual_std": 0.01,
                "worst_year": 0.00,
                "best_year": 0.05,
                "data_source": "treasury_bills_1928_2024"
            },
            "commodities": {
                "annual_mean": 0.05,
                "annual_std": 0.20,
                "worst_year": -0.35,
                "best_year": 0.32,
                "data_source": "gsci_1970_2024"
            },
            "crypto": {
                "annual_mean": 0.15,
                "annual_std": 0.60,
                "worst_year": -0.73,
                "best_year": 3.02,
                "data_source": "bitcoin_2014_2024"
            }
        },
        "correlations": {
            "us_stocks_intl_stocks": 0.85,
            "us_stocks_bonds": -0.10,
            "us_stocks_reits": 0.65,
            "bonds_reits": 0.20,
            "stocks_commodities": 0.30,
            "stocks_crypto": 0.40
        }
    }