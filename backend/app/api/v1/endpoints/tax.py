"""
Tax Optimization API Endpoints
Provides dedicated tax analysis and optimization recommendations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import structlog

from app.db.session import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user
from app.services.tax_optimization_service import TaxOptimizationService
from app.services.tax_calculations import TaxCalculations, tax_calculations
from app.services.financial_summary_service import financial_summary_service
from app.services.llm_service import llm_service

logger = structlog.get_logger()

router = APIRouter()

# Pydantic Models
class TaxAnalysisRequest(BaseModel):
    filing_status: str = 'married'
    state: str = 'NC'
    include_advanced_strategies: bool = True

class TaxStrategyRequest(BaseModel):
    strategy_type: str  # 'roth_conversion', 'bunching', 'tax_loss_harvesting', 'retirement_optimization'
    
class TaxCalculationRequest(BaseModel):
    calculation_type: str  # 'marginal_rate', 'itemization', 'bunching', 'retirement_optimization', 'quarterly_payments'
    parameters: Dict[str, Any] = {}

class DeductionAnalysisRequest(BaseModel):
    mortgage_interest: float = 0
    property_taxes: float = 0
    state_local_taxes: float = 0
    charitable: float = 0
    other_deductions: float = 0
    filing_status: str = 'married'

class RetirementContributionRequest(BaseModel):
    current_401k: float = 0
    current_traditional_ira: float = 0
    current_roth_ira: float = 0
    age: int = 35
    annual_income: float = 0

# Tax Analysis Endpoints
@router.get("/health")
def tax_service_health():
    """Health check for tax optimization service"""
    return {
        "status": "healthy",
        "service": "tax_optimization",
        "version": "1.0.0",
        "features": {
            "tax_opportunity_analysis": True,
            "itemization_vs_standard": True,
            "retirement_optimization": True,
            "tax_loss_harvesting": True,
            "deduction_bunching": True,
            "roth_conversion_analysis": True,
            "quarterly_payment_calculation": True
        }
    }

@router.post("/analyze")
async def analyze_tax_opportunities(
    request: TaxAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Comprehensive tax opportunity analysis based on user's financial profile
    """
    try:
        # Get user's financial data
        financial_summary = financial_summary_service.get_user_financial_summary(current_user.id, db)
        
        if not financial_summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Financial data not found. Please complete your financial profile first."
            )
        
        # Build financial context for tax analysis
        financial_context = {
            'monthly_income': financial_summary.get('monthlyIncome', 0),
            'monthly_expenses': financial_summary.get('monthlyExpenses', 0),
            'total_assets': financial_summary.get('totalAssets', 0),
            'investment_total': financial_summary.get('investmentTotal', 0),
            'mortgage_balance': financial_summary.get('mortgageBalance', 0),
            'annual_401k': financial_summary.get('annual401k', 0),
            'tax_bracket': financial_summary.get('taxBracket', 24),
            'age': financial_summary.get('age', 35),
            'state': request.state,
            'filing_status': request.filing_status
        }
        
        # Get comprehensive tax analysis using unified service
        tax_analysis = tax_calculations.analyze_comprehensive_tax_opportunities(
            user_id=current_user.id,
            financial_context=financial_context,
            db=db
        )
        
        if 'error' in tax_analysis:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=tax_analysis['error']
            )
        
        return {
            "user_id": current_user.id,
            "analysis_date": datetime.now().isoformat(),
            "financial_profile": {
                "annual_income": financial_context['monthly_income'] * 12,
                "tax_bracket": financial_context['tax_bracket'],
                "filing_status": request.filing_status,
                "state": request.state
            },
            "tax_analysis": tax_analysis,
            "disclaimer": "Tax analysis is based on current financial data and 2024 tax rules. Consult a tax professional for personalized advice."
        }
        
    except Exception as e:
        logger.error("Tax analysis failed", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tax analysis failed: {str(e)}"
        )

@router.post("/strategy/{strategy_type}")
async def get_specific_strategy_analysis(
    strategy_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Deep dive analysis for specific tax strategies
    """
    try:
        # Get user's financial data
        financial_summary = financial_summary_service.get_user_financial_summary(current_user.id, db)
        
        if not financial_summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Financial data not found"
            )
        
        # Build financial context
        financial_context = {
            'monthly_income': financial_summary.get('monthlyIncome', 0),
            'total_assets': financial_summary.get('totalAssets', 0),
            'investment_total': financial_summary.get('investmentTotal', 0),
            'mortgage_balance': financial_summary.get('mortgageBalance', 0),
            'annual_401k': financial_summary.get('annual401k', 0),
            'tax_bracket': financial_summary.get('taxBracket', 24),
            'age': financial_summary.get('age', 35),
            'traditional_ira': financial_summary.get('traditionalIra', 0),
            'state': 'NC',
            'filing_status': 'married'
        }
        
        # Initialize tax service
        tax_service = TaxOptimizationService(db, llm_service)
        
        # Get specific strategy analysis
        strategy_analysis = await tax_service.calculate_specific_strategy(
            user_id=current_user.id,
            strategy_type=strategy_type,
            financial_context=financial_context
        )
        
        return {
            "strategy_type": strategy_type,
            "user_id": current_user.id,
            "analysis": strategy_analysis,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Strategy analysis failed", error=str(e), strategy_type=strategy_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategy analysis failed: {str(e)}"
        )

@router.post("/calculate/marginal-rate")
async def calculate_marginal_tax_rate(
    annual_income: float,
    filing_status: str = 'married',
    state: str = 'NC',
    current_user: User = Depends(get_current_active_user)
):
    """
    Calculate marginal and effective tax rates for given income
    """
    try:
        tax_calc = TaxCalculations()
        tax_analysis = tax_calc.calculate_marginal_tax_rate(
            income=annual_income,
            filing_status=filing_status,
            state=state
        )
        
        return {
            "annual_income": annual_income,
            "filing_status": filing_status,
            "state": state,
            "tax_analysis": tax_analysis,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Marginal rate calculation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tax rate calculation failed: {str(e)}"
        )

@router.post("/calculate/itemization")
async def analyze_itemization_vs_standard(
    request: DeductionAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze whether to itemize deductions or take standard deduction
    """
    try:
        deductions = {
            'mortgage_interest': request.mortgage_interest,
            'property_taxes': request.property_taxes,
            'state_local_taxes': request.state_local_taxes,
            'charitable': request.charitable,
            'other': request.other_deductions
        }
        
        itemization_analysis = tax_calculations.should_itemize_analysis(
            deductions=deductions,
            filing_status=request.filing_status
        )
        
        return {
            "deductions_provided": deductions,
            "filing_status": request.filing_status,
            "analysis": itemization_analysis,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Itemization analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Itemization analysis failed: {str(e)}"
        )

@router.post("/calculate/bunching")
async def analyze_bunching_strategy(
    request: DeductionAnalysisRequest,
    marginal_rate: float = 24,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze deduction bunching strategy potential
    """
    try:
        base_deductions = {
            'mortgage_interest': request.mortgage_interest,
            'property_taxes': request.property_taxes,
            'state_local_taxes': request.state_local_taxes,
            'charitable': request.charitable,
            'other': request.other_deductions
        }
        
        bunching_analysis = tax_calculations.bunching_strategy_analysis(
            base_deductions=base_deductions,
            filing_status=request.filing_status,
            marginal_rate=marginal_rate
        )
        
        return {
            "base_deductions": base_deductions,
            "marginal_tax_rate": marginal_rate,
            "bunching_analysis": bunching_analysis,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Bunching analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bunching analysis failed: {str(e)}"
        )

@router.post("/calculate/retirement-optimization")
async def optimize_retirement_contributions(
    request: RetirementContributionRequest,
    marginal_rate: float = 24,
    current_user: User = Depends(get_current_active_user)
):
    """
    Optimize retirement contributions for maximum tax benefit
    """
    try:
        current_contributions = {
            '401k': request.current_401k,
            'traditional_ira': request.current_traditional_ira,
            'roth_ira': request.current_roth_ira
        }
        
        retirement_optimization = tax_calculations.retirement_contribution_optimization(
            current_contributions=current_contributions,
            income=request.annual_income,
            age=request.age,
            marginal_rate=marginal_rate
        )
        
        return {
            "current_contributions": current_contributions,
            "annual_income": request.annual_income,
            "age": request.age,
            "marginal_tax_rate": marginal_rate,
            "optimization": retirement_optimization,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Retirement optimization failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retirement optimization failed: {str(e)}"
        )

@router.post("/calculate/tax-loss-harvesting")
async def analyze_tax_loss_harvesting(
    portfolio_value: float,
    current_gains: float = 0,
    marginal_rate: float = 24,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze tax-loss harvesting opportunities
    """
    try:
        harvesting_analysis = tax_calculations.tax_loss_harvesting_analysis(
            portfolio_value=portfolio_value,
            current_gains=current_gains,
            marginal_rate=marginal_rate
        )
        
        return {
            "portfolio_value": portfolio_value,
            "current_gains": current_gains,
            "marginal_tax_rate": marginal_rate,
            "harvesting_analysis": harvesting_analysis,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Tax loss harvesting analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tax loss harvesting analysis failed: {str(e)}"
        )

@router.post("/calculate/quarterly-payments")
async def calculate_quarterly_payments(
    annual_income: float,
    withholding: float = 0,
    filing_status: str = 'married',
    current_user: User = Depends(get_current_active_user)
):
    """
    Calculate if quarterly estimated payments are needed
    """
    try:
        quarterly_analysis = tax_calculations.estimated_quarterly_payments(
            annual_income=annual_income,
            withholding=withholding,
            filing_status=filing_status
        )
        
        return {
            "annual_income": annual_income,
            "current_withholding": withholding,
            "filing_status": filing_status,
            "quarterly_analysis": quarterly_analysis,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Quarterly payment calculation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quarterly payment calculation failed: {str(e)}"
        )

@router.get("/opportunities")
async def get_tax_opportunities_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a quick summary of tax optimization opportunities
    """
    try:
        # Get user's financial data
        financial_summary = financial_summary_service.get_user_financial_summary(current_user.id, db)
        
        if not financial_summary:
            return {
                "message": "Complete your financial profile to see tax optimization opportunities",
                "opportunities": []
            }
        
        # Build quick tax analysis
        annual_income = financial_summary.get('monthlyIncome', 0) * 12
        current_401k = financial_summary.get('annual401k', 0)
        age = financial_summary.get('age', 35)
        investment_total = financial_summary.get('investmentTotal', 0)
        
        opportunities = []
        
        # Use REAL calculations instead of hardcoded values
        opportunities = tax_calculations.get_quick_tax_opportunities(current_user.id, financial_summary)
        
        # Sort by potential savings
        opportunities.sort(key=lambda x: x["potential_savings"], reverse=True)
        
        total_potential_savings = sum(opp["potential_savings"] for opp in opportunities)
        
        return {
            "user_id": current_user.id,
            "total_potential_savings": round(total_potential_savings, 2),
            "opportunities": opportunities[:5],  # Top 5
            "generated_at": datetime.now().isoformat(),
            "note": "Rough estimates based on current financial data. Use detailed analysis endpoints for precise calculations."
        }
        
    except Exception as e:
        logger.error("Tax opportunities summary failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tax opportunities: {str(e)}"
        )

@router.get("/insights")
async def get_tax_insights_for_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get tax insights formatted for frontend dashboard display
    """
    try:
        # Get comprehensive tax analysis
        financial_summary = financial_summary_service.get_user_financial_summary(current_user.id, db)
        
        if not financial_summary:
            return {
                "insights": [],
                "total_potential_savings": 0,
                "message": "Complete your financial profile to see personalized tax insights"
            }
        
        # Build financial context
        financial_context = {
            'monthly_income': financial_summary.get('monthlyIncome', 0),
            'monthly_expenses': financial_summary.get('monthlyExpenses', 0),
            'total_assets': financial_summary.get('totalAssets', 0),
            'investment_total': financial_summary.get('investmentTotal', 0),
            'mortgage_balance': financial_summary.get('mortgageBalance', 0),
            'annual_401k': financial_summary.get('annual401k', 0),
            'tax_bracket': financial_summary.get('taxBracket', 24),
            'age': financial_summary.get('age', 35),
            'state': 'NC',
            'filing_status': 'married'
        }
        
        # Get tax analysis using unified TaxCalculations service
        tax_analysis = tax_calculations.analyze_comprehensive_tax_opportunities(
            user_id=current_user.id,
            financial_context=financial_context,
            db=db
        )
        
        # Format for frontend
        if tax_analysis and 'calculated_opportunities' in tax_analysis:
            insights = []
            for opp in tax_analysis['calculated_opportunities']:
                insights.append({
                    "strategy": opp.get('strategy', 'Tax Strategy'),
                    "potentialSavings": opp.get('annual_tax_savings', 0),
                    "difficulty": opp.get('difficulty', 'Medium'),
                    "timeline": opp.get('timeline', 'TBD'),
                    "priority": opp.get('priority', 3),
                    "description": opp.get('description', 'Tax optimization opportunity'),
                    "implementationSteps": [
                        "Review with tax professional",
                        "Implement strategy",
                        "Monitor results"
                    ]
                })
            
            return {
                "insights": insights,
                "total_potential_savings": tax_analysis.get('total_potential_savings', 0),
                "tax_profile": {
                    "annual_income": financial_context['monthly_income'] * 12,
                    "tax_bracket": financial_context['tax_bracket'],
                    "filing_status": financial_context['filing_status']
                },
                "generated_at": datetime.now().isoformat()
            }
        else:
            return {
                "insights": [],
                "total_potential_savings": 0,
                "message": "Unable to generate tax insights at this time"
            }
        
    except Exception as e:
        logger.error("Tax insights generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tax insights: {str(e)}"
        )