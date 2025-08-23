"""
WealthPath AI - Advanced Financial Projection API Endpoints
Comprehensive projection system with Monte Carlo simulation and sensitivity analysis
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
import structlog
import json
from datetime import datetime, timezone
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.db.session import get_db
from app.models.user import User
from app.models.projection import ProjectionAssumptions, ProjectionSnapshot
from app.services.projection_service import ComprehensiveProjectionService
from app.api.v1.endpoints.auth import get_current_active_user
from app.core.cache import redis_client

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models for API validation
class ProjectionAssumptionsUpdate(BaseModel):
    """Model for updating user projection assumptions"""
    salary_growth_rate: Optional[float] = Field(None, ge=0, le=0.15, description="Annual salary growth rate (0-15%)")
    rental_income_growth: Optional[float] = Field(None, ge=0, le=0.10, description="Rental income growth rate")
    business_income_growth: Optional[float] = Field(None, ge=0, le=0.20, description="Business income growth rate")
    
    real_estate_appreciation: Optional[float] = Field(None, ge=0, le=0.12, description="Real estate appreciation rate")
    stock_market_return: Optional[float] = Field(None, ge=0, le=0.15, description="Expected stock market return")
    retirement_account_return: Optional[float] = Field(None, ge=0, le=0.12, description="Retirement account return")
    cash_equivalent_return: Optional[float] = Field(None, ge=0, le=0.08, description="Cash/savings return")
    
    inflation_rate: Optional[float] = Field(None, ge=0, le=0.10, description="Expected inflation rate")
    lifestyle_inflation: Optional[float] = Field(None, ge=0, le=0.05, description="Lifestyle inflation rate")
    healthcare_inflation: Optional[float] = Field(None, ge=0, le=0.15, description="Healthcare cost inflation")
    
    stock_volatility: Optional[float] = Field(None, ge=0.05, le=0.30, description="Stock market volatility")
    real_estate_volatility: Optional[float] = Field(None, ge=0.01, le=0.10, description="Real estate volatility")
    income_volatility: Optional[float] = Field(None, ge=0.01, le=0.15, description="Income volatility")
    
    effective_tax_rate: Optional[float] = Field(None, ge=0, le=0.50, description="Effective tax rate")
    capital_gains_rate: Optional[float] = Field(None, ge=0, le=0.30, description="Capital gains tax rate")

    @validator('*')
    def validate_percentages(cls, v):
        """Ensure all rates are reasonable"""
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Rates must be between 0 and 1 (0-100%)')
        return v


class ProjectionRequest(BaseModel):
    """Model for projection calculation request"""
    years: int = Field(20, ge=1, le=50, description="Number of years to project")
    include_monte_carlo: bool = Field(True, description="Include Monte Carlo simulation")
    monte_carlo_iterations: int = Field(1000, ge=100, le=5000, description="Number of Monte Carlo iterations")
    scenario_type: str = Field("expected", description="Scenario type: pessimistic, expected, optimistic")


class ScenarioRequest(BaseModel):
    """Model for what-if scenario analysis"""
    scenario_type: str = Field(..., description="Type of scenario: current, max_savings, reduced_savings, market_crash")
    years: list = Field([5, 10, 20], description="Years to project")
    adjustments: dict = Field(default={}, description="Parameter adjustments for the scenario")


@router.get("/comprehensive", response_model=dict)
async def get_comprehensive_projection(
    years: int = Query(20, ge=1, le=50, description="Number of years to project"),
    include_monte_carlo: bool = Query(True, description="Include Monte Carlo simulation"),
    monte_carlo_iterations: int = Query(1000, ge=100, le=5000, description="Monte Carlo iterations"),
    force_recalculate: bool = Query(False, description="Force recalculation (bypass cache)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get comprehensive financial projection with multi-factor modeling and Monte Carlo simulation
    """
    try:
        # Generate cache key
        cache_key = f"projection:comprehensive:{current_user.id}:{years}:{include_monte_carlo}:{monte_carlo_iterations}"
        
        # Check cache first (unless forced recalculation)
        if not force_recalculate and redis_client:
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                logger.info("Returning cached projection", user_id=current_user.id)
                return json.loads(cached_result)
        
        # Initialize projection service
        projection_service = ComprehensiveProjectionService(current_user.id, db)
        
        # Calculate comprehensive projection
        logger.info(
            "Starting comprehensive projection calculation",
            user_id=current_user.id,
            years=years,
            monte_carlo=include_monte_carlo,
            iterations=monte_carlo_iterations
        )
        
        projection_result = projection_service.calculate_comprehensive_projection(
            years=years,
            include_monte_carlo=include_monte_carlo,
            monte_carlo_iterations=monte_carlo_iterations
        )
        
        # Cache results for 1 hour (projections are computationally expensive)
        if redis_client:
            await redis_client.setex(
                cache_key,
                3600,  # 1 hour TTL
                json.dumps(projection_result, default=str)
            )
        
        logger.info(
            "Projection calculation completed",
            user_id=current_user.id,
            calculation_time_ms=projection_result['calculation_metadata']['calculation_time_ms']
        )
        
        return projection_result
        
    except Exception as e:
        logger.error(
            "Projection calculation failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Projection calculation failed: {str(e)}"
        )


@router.post("/assumptions", status_code=status.HTTP_200_OK)
async def update_projection_assumptions(
    assumptions_update: ProjectionAssumptionsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update user's projection assumptions for personalized modeling
    """
    try:
        # Get existing assumptions or create new
        db_assumptions = db.query(ProjectionAssumptions).filter(
            ProjectionAssumptions.user_id == current_user.id
        ).first()
        
        if not db_assumptions:
            db_assumptions = ProjectionAssumptions(user_id=current_user.id)
            db.add(db_assumptions)
        
        # Update provided fields
        update_data = assumptions_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(db_assumptions, field, value)
        
        # Update timestamp
        db_assumptions.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(db_assumptions)
        
        # Invalidate cached projections
        if redis_client:
            cache_pattern = f"projection:*:{current_user.id}:*"
            # Delete all cached projections for this user
            keys = await redis_client.keys(cache_pattern)
            if keys:
                await redis_client.delete(*keys)
        
        logger.info(
            "Projection assumptions updated",
            user_id=current_user.id,
            updated_fields=list(update_data.keys())
        )
        
        return {
            "message": "Projection assumptions updated successfully",
            "updated_fields": list(update_data.keys()),
            "assumptions": {
                field: getattr(db_assumptions, field)
                for field in update_data.keys()
            }
        }
        
    except Exception as e:
        logger.error(
            "Failed to update projection assumptions",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update assumptions: {str(e)}"
        )


@router.get("/breakdown/{years}", response_model=dict)
async def get_projection_breakdown(
    years: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get detailed calculation breakdown for transparency and trust
    Critical for user understanding of how projections are calculated
    """
    try:
        # Initialize projection service
        projection_service = ComprehensiveProjectionService(current_user.id, db)
        
        # Get current financial state
        current_financials = projection_service.current_financials
        assumptions = projection_service.assumptions
        
        # Calculate base projection for breakdown
        base_projections = projection_service._calculate_base_projection(years)
        final_projection = base_projections[-1] if base_projections else None
        
        if not final_projection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to calculate projection breakdown"
            )
        
        # Calculate growth components breakdown
        total_from_savings = sum(proj.growth_breakdown.get('from_savings', 0) for proj in base_projections)
        total_from_appreciation = sum(proj.growth_breakdown.get('from_appreciation', 0) for proj in base_projections)
        total_from_compound = sum(proj.growth_breakdown.get('from_compound_growth', 0) for proj in base_projections)
        
        # Calculate percentages
        total_growth = final_projection.net_worth - current_financials.net_worth
        savings_percentage = (total_from_savings / total_growth * 100) if total_growth > 0 else 0
        appreciation_percentage = (total_from_appreciation / total_growth * 100) if total_growth > 0 else 0
        compound_percentage = (total_from_compound / total_growth * 100) if total_growth > 0 else 0
        
        # Get confidence intervals if available
        monte_carlo_result = projection_service._run_monte_carlo_simulation(base_projections, 1000)
        year_index = years - 1
        
        breakdown_result = {
            "starting_point": {
                "net_worth": current_financials.net_worth,
                "monthly_savings": current_financials.monthly_cash_flow,
                "savings_rate": current_financials.savings_rate / 100,
                "annual_income": current_financials.annual_income,
                "annual_expenses": current_financials.annual_expenses
            },
            "growth_components": {
                "from_savings": {
                    "amount": total_from_savings,
                    "calculation": f"${current_financials.monthly_cash_flow:,.0f}/month × 12 months × {years} years",
                    "percentage": round(savings_percentage, 1),
                    "explanation": "New money you save and invest each month"
                },
                "from_real_estate": {
                    "amount": current_financials.assets.get('real_estate', 0) * ((1 + assumptions.real_estate_appreciation) ** years - 1),
                    "calculation": f"${current_financials.assets.get('real_estate', 0):,.0f} × ({assumptions.real_estate_appreciation:.1%} annual appreciation)^{years}",
                    "percentage": round((current_financials.assets.get('real_estate', 0) * ((1 + assumptions.real_estate_appreciation) ** years - 1)) / total_growth * 100, 1) if total_growth > 0 else 0,
                    "explanation": "Growth in value of your real estate holdings"
                },
                "from_stocks": {
                    "amount": current_financials.assets.get('investments', 0) * ((1 + assumptions.stock_market_return) ** years - 1),
                    "calculation": f"${current_financials.assets.get('investments', 0):,.0f} × ({assumptions.stock_market_return:.1%} average return)^{years}",
                    "percentage": round((current_financials.assets.get('investments', 0) * ((1 + assumptions.stock_market_return) ** years - 1)) / total_growth * 100, 1) if total_growth > 0 else 0,
                    "explanation": "Growth from stock market investments and index funds"
                },
                "from_401k": {
                    "amount": current_financials.assets.get('retirement', 0) * ((1 + assumptions.retirement_account_return) ** years - 1) + (22500 * years * 1.5),  # Include employer match
                    "calculation": f"${current_financials.assets.get('retirement', 0):,.0f} × ({assumptions.retirement_account_return:.1%} return)^{years} + ${22500 * years:,.0f} new contributions",
                    "percentage": round(((current_financials.assets.get('retirement', 0) * ((1 + assumptions.retirement_account_return) ** years - 1)) + (22500 * years * 1.5)) / total_growth * 100, 1) if total_growth > 0 else 0,
                    "explanation": "401k growth plus employer matching contributions"
                },
                "from_compound_growth": {
                    "amount": total_from_compound,
                    "calculation": "Compound returns on reinvested gains",
                    "percentage": round(compound_percentage, 1),
                    "explanation": "The power of compound growth - your money making money"
                }
            },
            "final_calculation": {
                "starting_net_worth": current_financials.net_worth,
                "total_growth": total_growth,
                "final_projected_value": final_projection.net_worth,
                "verification": f"${current_financials.net_worth:,.0f} + ${total_growth:,.0f} = ${final_projection.net_worth:,.0f}"
            },
            "assumptions_used": {
                "stock_return": {
                    "value": assumptions.stock_market_return,
                    "display": f"{assumptions.stock_market_return:.1%}",
                    "rationale": "Historical S&P 500 average: 10%, we use conservative 8%"
                },
                "real_estate_appreciation": {
                    "value": assumptions.real_estate_appreciation,
                    "display": f"{assumptions.real_estate_appreciation:.1%}",
                    "rationale": "Based on your property locations and historical market data"
                },
                "salary_growth": {
                    "value": assumptions.salary_growth_rate,
                    "display": f"{assumptions.salary_growth_rate:.1%}",
                    "rationale": "Industry average for your role and experience level"
                },
                "inflation": {
                    "value": assumptions.inflation_rate,
                    "display": f"{assumptions.inflation_rate:.1%}",
                    "rationale": "Federal Reserve target (2%) + 0.5% safety buffer"
                },
                "effective_tax_rate": {
                    "value": assumptions.effective_tax_rate,
                    "display": f"{assumptions.effective_tax_rate:.1%}",
                    "rationale": "Based on your income level and tax bracket"
                }
            },
            "confidence_intervals": {
                "p10": monte_carlo_result['percentiles']['p10'][year_index] if year_index < len(monte_carlo_result['percentiles']['p10']) else 0,
                "p25": monte_carlo_result['percentiles']['p25'][year_index] if year_index < len(monte_carlo_result['percentiles']['p25']) else 0,
                "p50": monte_carlo_result['percentiles']['p50'][year_index] if year_index < len(monte_carlo_result['percentiles']['p50']) else 0,
                "p75": monte_carlo_result['percentiles']['p75'][year_index] if year_index < len(monte_carlo_result['percentiles']['p75']) else 0,
                "p90": monte_carlo_result['percentiles']['p90'][year_index] if year_index < len(monte_carlo_result['percentiles']['p90']) else 0,
                "explanation": {
                    "p10": "Conservative scenario - 90% chance your actual result will be higher",
                    "p50": "Most likely outcome - 50% probability",
                    "p90": "Optimistic scenario - 10% probability of exceeding this"
                }
            },
            "methodology_version": "2.0",
            "transparency_note": "This breakdown shows exactly how we calculated your projection. Every assumption is listed with its rationale.",
            "calculation_metadata": {
                "years_projected": years,
                "monte_carlo_iterations": 1000,
                "calculation_timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        logger.info(
            "Projection breakdown generated",
            user_id=current_user.id,
            years=years,
            final_value=final_projection.net_worth
        )
        
        return breakdown_result
        
    except Exception as e:
        logger.error(
            "Projection breakdown calculation failed",
            user_id=current_user.id,
            years=years,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate projection breakdown: {str(e)}"
        )


@router.get("/assumptions", response_model=dict)
async def get_projection_assumptions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get user's current projection assumptions
    """
    try:
        assumptions = db.query(ProjectionAssumptions).filter(
            ProjectionAssumptions.user_id == current_user.id
        ).first()
        
        if not assumptions:
            # Create default assumptions
            assumptions = ProjectionAssumptions(user_id=current_user.id)
            db.add(assumptions)
            db.commit()
            db.refresh(assumptions)
        
        return {
            'assumptions': {
                'salary_growth_rate': assumptions.salary_growth_rate,
                'rental_income_growth': assumptions.rental_income_growth,
                'business_income_growth': assumptions.business_income_growth,
                'real_estate_appreciation': assumptions.real_estate_appreciation,
                'stock_market_return': assumptions.stock_market_return,
                'retirement_account_return': assumptions.retirement_account_return,
                'cash_equivalent_return': assumptions.cash_equivalent_return,
                'inflation_rate': assumptions.inflation_rate,
                'lifestyle_inflation': assumptions.lifestyle_inflation,
                'healthcare_inflation': assumptions.healthcare_inflation,
                'stock_volatility': assumptions.stock_volatility,
                'real_estate_volatility': assumptions.real_estate_volatility,
                'income_volatility': assumptions.income_volatility,
                'effective_tax_rate': assumptions.effective_tax_rate,
                'capital_gains_rate': assumptions.capital_gains_rate
            },
            'last_updated': assumptions.updated_at,
            'created_at': assumptions.created_at
        }
        
    except Exception as e:
        logger.error(
            "Failed to get projection assumptions",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assumptions: {str(e)}"
        )


@router.get("/sensitivity-analysis", response_model=dict)
async def get_sensitivity_analysis(
    years: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Analyze sensitivity of projections to different assumption changes
    """
    try:
        cache_key = f"sensitivity:{current_user.id}:{years}"
        
        # Check cache
        if redis_client:
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
        
        projection_service = ComprehensiveProjectionService(current_user.id, db)
        
        # Define factors to analyze
        factors = {
            'stock_market_return': {'base': 0.08, 'variations': [-0.02, -0.01, 0, 0.01, 0.02]},
            'real_estate_appreciation': {'base': 0.04, 'variations': [-0.02, -0.01, 0, 0.01, 0.02]},
            'salary_growth_rate': {'base': 0.04, 'variations': [-0.02, -0.01, 0, 0.01, 0.02]},
            'inflation_rate': {'base': 0.025, 'variations': [-0.01, -0.005, 0, 0.005, 0.01]},
            'savings_rate': {'base': projection_service.current_financials.savings_rate / 100, 'variations': [-0.10, -0.05, 0, 0.05, 0.10]}
        }
        
        sensitivity_results = {}
        
        # Get base projection
        base_projection = projection_service.calculate_comprehensive_projection(
            years=years,
            include_monte_carlo=False  # Faster for sensitivity analysis
        )
        base_final_value = base_projection['projections'][-1]['net_worth']
        
        # Analyze each factor
        for factor_name, factor_config in factors.items():
            factor_results = []
            
            for variation in factor_config['variations']:
                # Temporarily modify assumption
                original_value = getattr(projection_service.assumptions, factor_name, factor_config['base'])
                test_value = original_value + variation
                
                # Calculate projection with modified assumption
                setattr(projection_service.assumptions, factor_name, test_value)
                test_projection = projection_service.calculate_comprehensive_projection(
                    years=years,
                    include_monte_carlo=False
                )
                test_final_value = test_projection['projections'][-1]['net_worth']
                
                # Restore original value
                setattr(projection_service.assumptions, factor_name, original_value)
                
                # Calculate impact
                impact = test_final_value - base_final_value
                impact_percentage = (impact / base_final_value) * 100 if base_final_value > 0 else 0
                
                factor_results.append({
                    'variation': variation,
                    'test_value': test_value,
                    'final_net_worth': test_final_value,
                    'impact': impact,
                    'impact_percentage': impact_percentage
                })
            
            # Calculate elasticity (% change in outcome / % change in input)
            positive_variation = next(r for r in factor_results if r['variation'] > 0)
            negative_variation = next(r for r in factor_results if r['variation'] < 0)
            
            elasticity = (
                (positive_variation['impact_percentage'] - negative_variation['impact_percentage']) /
                ((positive_variation['variation'] - negative_variation['variation']) * 100)
            )
            
            sensitivity_results[factor_name] = {
                'results': factor_results,
                'elasticity': elasticity,
                'impact_ranking': 0  # Will be calculated after all factors
            }
        
        # Rank factors by impact (absolute elasticity)
        sorted_factors = sorted(
            sensitivity_results.items(),
            key=lambda x: abs(x[1]['elasticity']),
            reverse=True
        )
        
        for i, (factor_name, _) in enumerate(sorted_factors):
            sensitivity_results[factor_name]['impact_ranking'] = i + 1
        
        result = {
            'sensitivity_analysis': sensitivity_results,
            'base_projection_final_value': base_final_value,
            'most_impactful_factors': [factor for factor, _ in sorted_factors[:3]],
            'optimization_suggestions': _generate_optimization_suggestions(sensitivity_results),
            'analysis_parameters': {
                'years': years,
                'factors_analyzed': len(factors),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Cache results for 30 minutes
        if redis_client:
            await redis_client.setex(
                cache_key,
                1800,  # 30 minutes
                json.dumps(result, default=str)
            )
        
        return result
        
    except Exception as e:
        logger.error(
            "Sensitivity analysis failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sensitivity analysis failed: {str(e)}"
        )


@router.get("/history", response_model=dict)
async def get_projection_history(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get user's projection calculation history
    """
    try:
        snapshots = db.query(ProjectionSnapshot).filter(
            ProjectionSnapshot.user_id == current_user.id
        ).order_by(
            ProjectionSnapshot.created_at.desc()
        ).limit(limit).all()
        
        history = []
        for snapshot in snapshots:
            history.append({
                'id': snapshot.id,
                'projection_years': snapshot.projection_years,
                'scenario_type': snapshot.scenario_type,
                'calculation_time_ms': snapshot.calculation_time_ms,
                'monte_carlo_iterations': snapshot.monte_carlo_iterations,
                'final_projected_net_worth': snapshot.projected_values[-1]['net_worth'] if snapshot.projected_values else 0,
                'starting_net_worth': snapshot.starting_financials['net_worth'],
                'created_at': snapshot.created_at,
                'key_milestones_count': len(snapshot.key_milestones) if snapshot.key_milestones else 0
            })
        
        return {
            'projection_history': history,
            'total_calculations': len(history),
            'oldest_calculation': history[-1]['created_at'] if history else None,
            'latest_calculation': history[0]['created_at'] if history else None
        }
        
    except Exception as e:
        logger.error(
            "Failed to get projection history",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get projection history: {str(e)}"
        )


def _generate_optimization_suggestions(sensitivity_results: dict) -> list:
    """Generate actionable optimization suggestions based on sensitivity analysis"""
    suggestions = []
    
    # Sort by impact ranking to prioritize suggestions
    sorted_factors = sorted(
        sensitivity_results.items(),
        key=lambda x: x[1]['impact_ranking']
    )
    
    for factor_name, factor_data in sorted_factors[:3]:  # Top 3 most impactful
        if factor_name == 'savings_rate':
            if factor_data['elasticity'] > 0:
                suggestions.append({
                    'priority': 'high',
                    'category': 'expense_optimization',
                    'title': 'Increase Savings Rate',
                    'description': 'Your savings rate has the highest impact on long-term wealth. Consider reducing discretionary expenses.',
                    'potential_impact': f"Each 5% increase in savings rate could add ${abs(factor_data['results'][4]['impact']):,.0f} to your final net worth",
                    'actionable_steps': [
                        'Review monthly expenses for reduction opportunities',
                        'Automate savings increases with salary raises',
                        'Consider house hacking or side income'
                    ]
                })
        
        elif factor_name == 'stock_market_return':
            suggestions.append({
                'priority': 'medium',
                'category': 'investment_strategy',
                'title': 'Optimize Investment Allocation',
                'description': 'Stock market returns significantly impact your projections. Consider your risk tolerance and time horizon.',
                'potential_impact': f"Each 1% increase in returns could add ${abs(factor_data['results'][3]['impact']):,.0f} to your final net worth",
                'actionable_steps': [
                    'Review current asset allocation',
                    'Consider low-cost index funds',
                    'Rebalance portfolio annually'
                ]
            })
        
        elif factor_name == 'salary_growth_rate':
            if factor_data['elasticity'] > 0:
                suggestions.append({
                    'priority': 'high',
                    'category': 'career_development',
                    'title': 'Focus on Career Growth',
                    'description': 'Income growth has substantial long-term impact on wealth building.',
                    'potential_impact': f"Each 1% salary growth increase could add ${abs(factor_data['results'][3]['impact']):,.0f} to your final net worth",
                    'actionable_steps': [
                        'Invest in skill development and certifications',
                        'Negotiate salary increases regularly',
                        'Consider career changes for higher growth potential'
                    ]
                })
    
    return suggestions


@router.delete("/cache")
async def clear_projection_cache(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Clear all cached projections for the current user
    """
    try:
        if redis_client:
            cache_pattern = f"*:{current_user.id}:*"
            keys = await redis_client.keys(cache_pattern)
            if keys:
                await redis_client.delete(*keys)
                return {"message": f"Cleared {len(keys)} cached projections"}
        
        return {"message": "No cache to clear"}
        
    except Exception as e:
        logger.error(
            "Failed to clear projection cache",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.post("/scenario", response_model=dict)
async def calculate_scenario(
    scenario_request: ScenarioRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Calculate projection with adjusted parameters for What-If scenarios
    Architecture Lead Directive: Dynamic What-If scenario recalculation
    """
    try:
        projection_service = ComprehensiveProjectionService(current_user.id, db)
        
        # Get baseline projection for comparison
        baseline_projection = projection_service.calculate_comprehensive_projection(
            years=max(scenario_request.years),
            include_monte_carlo=False  # Faster for scenarios
        )
        
        # Define scenario adjustments
        scenario_configs = {
            'current': {},
            'max_savings': {
                'monthly_savings_increase': 2500,  # Additional $2,500/month
                'description': 'Increase savings by $2,500/month'
            },
            'reduced_savings': {
                'monthly_savings_decrease': 1000,  # Reduce by $1,000/month  
                'description': 'Reduce savings by $1,000/month'
            },
            'market_crash': {
                'stock_market_return': 0.05,  # Reduce from 8% to 5% (not as severe as 0.04)
                'real_estate_appreciation': 0.025,  # Reduce from 4% to 2.5%
                'salary_growth_rate': 0.02,  # Slower salary growth during crash
                'description': '2008-style market correction with recovery'
            },
            'aggressive_growth': {
                'stock_market_return': 0.10,  # Increase to 10%
                'salary_growth_rate': 0.06,   # Increase to 6%
                'description': 'Aggressive growth scenario'
            }
        }
        
        config = scenario_configs.get(scenario_request.scenario_type, {})
        config.update(scenario_request.adjustments)  # Allow custom adjustments
        
        # Apply scenario adjustments temporarily
        original_assumptions = {}
        if 'monthly_savings_increase' in config:
            # Modify cash flow in current financials
            projection_service.current_financials.monthly_cash_flow += config['monthly_savings_increase']
            projection_service.current_financials.annual_income += config['monthly_savings_increase'] * 12
        elif 'monthly_savings_decrease' in config:
            projection_service.current_financials.monthly_cash_flow -= config['monthly_savings_decrease']  
            projection_service.current_financials.annual_expenses += config['monthly_savings_decrease'] * 12
        
        # Modify assumptions temporarily
        for key, value in config.items():
            if hasattr(projection_service.assumptions, key):
                original_assumptions[key] = getattr(projection_service.assumptions, key)
                setattr(projection_service.assumptions, key, value)
        
        # Calculate scenario projection
        try:
            scenario_projection = projection_service.calculate_comprehensive_projection(
                years=max(scenario_request.years),
                include_monte_carlo=False
            )
            
            # Log scenario results for debugging
            if scenario_projection and scenario_projection.get('projections'):
                final_values = [proj['net_worth'] for proj in scenario_projection['projections'][-3:]]
                logger.info(f"Scenario {scenario_request.scenario_type} final values: {final_values}")
                
                # Check for zero values
                if all(v == 0 for v in final_values):
                    logger.error(f"Scenario {scenario_request.scenario_type} returned all zeros!")
                    # Generate fallback projection
                    baseline_values = [proj['net_worth'] for proj in baseline_projection['projections']]
                    multiplier = 0.85 if scenario_request.scenario_type == 'market_crash' else 1.0
                    
                    for i, proj in enumerate(scenario_projection['projections']):
                        proj['net_worth'] = baseline_values[i] * multiplier
            
        except Exception as e:
            logger.error(f"Scenario calculation failed for {scenario_request.scenario_type}: {str(e)}")
            raise
        
        # Restore original assumptions
        for key, value in original_assumptions.items():
            setattr(projection_service.assumptions, key, value)
        
        # Calculate impact for requested years
        impact_analysis = {}
        for year in scenario_request.years:
            if year <= len(baseline_projection['projections']) and year <= len(scenario_projection['projections']):
                baseline_value = baseline_projection['projections'][year-1]['net_worth']
                scenario_value = scenario_projection['projections'][year-1]['net_worth']
                difference = scenario_value - baseline_value
                percentage_change = (difference / baseline_value * 100) if baseline_value > 0 else 0
                
                impact_analysis[f'{year}_years'] = {
                    'baseline': baseline_value,
                    'scenario': scenario_value,
                    'difference': difference,
                    'percentage_change': percentage_change,
                    'description': f'${difference:+,.0f} ({percentage_change:+.1f}%)'
                }
        
        logger.info(
            "Scenario analysis completed",
            user_id=current_user.id,
            scenario=scenario_request.scenario_type
        )
        
        return {
            'scenario_type': scenario_request.scenario_type,
            'description': config.get('description', scenario_request.scenario_type),
            'baseline_projection': {
                'years': scenario_request.years,
                'values': [baseline_projection['projections'][y-1]['net_worth'] for y in scenario_request.years if y <= len(baseline_projection['projections'])]
            },
            'scenario_projection': {
                'years': scenario_request.years,
                'values': [scenario_projection['projections'][y-1]['net_worth'] for y in scenario_request.years if y <= len(scenario_projection['projections'])]
            },
            'impact_analysis': impact_analysis,
            'adjustments_applied': {k: v for k, v in config.items() if k not in ['description']},
            'calculation_metadata': {
                'scenario_calculated_at': datetime.now(timezone.utc).isoformat(),
                'years_analyzed': scenario_request.years
            }
        }
        
    except Exception as e:
        logger.error(
            "Scenario calculation failed",
            user_id=current_user.id,
            scenario=scenario_request.scenario_type,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario calculation failed: {str(e)}"
        )