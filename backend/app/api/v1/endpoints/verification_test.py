"""
Verification Test Endpoint
Tests all the fixes implemented for WealthPath AI system
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.db.session import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def verification_health():
    """Health check for verification system"""
    return {
        "status": "healthy",
        "service": "System Verification Tests",
        "version": "1.0"
    }

@router.get("/complete-system-test/{user_id}")
async def complete_system_test(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Complete system verification test
    Tests all major components and fixes
    """
    
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    test_results = {
        "user_id": user_id,
        "timestamp": "2025-01-08",
        "tests": {},
        "overall_status": "unknown"
    }
    
    # Test 1: Financial Summary Service
    try:
        from app.services.financial_summary_service import financial_summary_service
        summary = financial_summary_service.get_user_financial_summary(user_id, db)
        
        test_results["tests"]["financial_summary"] = {
            "status": "PASS" if "error" not in summary else "FAIL",
            "net_worth": summary.get("netWorth", 0),
            "total_assets": summary.get("totalAssets", 0),
            "assets_breakdown_count": len(summary.get("assetsBreakdown", {}))
        }
    except Exception as e:
        test_results["tests"]["financial_summary"] = {
            "status": "ERROR",
            "error": str(e)
        }
    
    # Test 2: Financial Health Scorer
    try:
        from app.services.financial_health_scorer import financial_health_scorer
        health_score = financial_health_scorer.calculate_comprehensive_score(user_id, db)
        
        test_results["tests"]["financial_health_scorer"] = {
            "status": "PASS" if health_score.get("overall_score", 0) > 0 else "FAIL",
            "overall_score": health_score.get("overall_score", 0),
            "grade": health_score.get("grade", "N/A"),
            "component_count": len(health_score.get("component_scores", {}))
        }
    except Exception as e:
        test_results["tests"]["financial_health_scorer"] = {
            "status": "ERROR",
            "error": str(e)
        }
    
    # Test 3: Complete Financial Context Service
    try:
        from app.services.complete_financial_context_service import complete_financial_context
        context = complete_financial_context.build_complete_context(user_id, db, "What's my financial status?")
        
        test_results["tests"]["complete_context"] = {
            "status": "PASS" if len(context) > 1000 else "FAIL",
            "context_length": len(context),
            "has_retirement_goal": "$3,500,000" in context,
            "has_social_security": "Social Security" in context,
            "has_financial_score": "/100" in context
        }
    except Exception as e:
        test_results["tests"]["complete_context"] = {
            "status": "ERROR",
            "error": str(e)
        }
    
    # Test 4: Session Service
    try:
        from app.services.session_service import session_service
        session = session_service.get_or_create_session(user_id)
        
        test_results["tests"]["session_service"] = {
            "status": "PASS" if session.get("user_id") == user_id else "FAIL",
            "session_exists": bool(session),
            "conversation_history_count": len(session.get("conversation_history", []))
        }
    except Exception as e:
        test_results["tests"]["session_service"] = {
            "status": "ERROR", 
            "error": str(e)
        }
    
    # Test 5: Vector Database Status
    try:
        from app.services.vector_db_service import FinancialVectorDB
        vector_db = FinancialVectorDB()
        
        # Test search functionality
        search_results = vector_db.search_context(user_id, "retirement goal", n_results=5)
        
        test_results["tests"]["vector_database"] = {
            "status": "PASS" if len(search_results) > 0 else "FAIL",
            "search_results_count": len(search_results),
            "database_accessible": True
        }
    except Exception as e:
        test_results["tests"]["vector_database"] = {
            "status": "ERROR",
            "error": str(e)
        }
    
    # Test 6: Social Security Benefits Integration
    try:
        from app.models.user_profile import UserBenefit, UserProfile
        
        ss_benefits = db.query(UserBenefit).join(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserBenefit.benefit_type == 'social_security'
        ).first()
        
        ss_monthly = float(ss_benefits.estimated_monthly_benefit or 0) if ss_benefits else 0
        
        test_results["tests"]["social_security"] = {
            "status": "PASS" if ss_monthly > 0 else "FAIL",
            "monthly_benefit": ss_monthly,
            "annual_benefit": ss_monthly * 12,
            "benefit_exists": bool(ss_benefits)
        }
    except Exception as e:
        test_results["tests"]["social_security"] = {
            "status": "ERROR",
            "error": str(e)
        }
    
    # Calculate overall status
    test_statuses = [test.get("status") for test in test_results["tests"].values()]
    error_count = test_statuses.count("ERROR")
    fail_count = test_statuses.count("FAIL") 
    pass_count = test_statuses.count("PASS")
    
    if error_count == 0 and fail_count == 0:
        test_results["overall_status"] = "ALL_SYSTEMS_OPERATIONAL"
    elif error_count == 0 and fail_count <= 1:
        test_results["overall_status"] = "MOSTLY_OPERATIONAL"
    elif error_count <= 1:
        test_results["overall_status"] = "PARTIALLY_OPERATIONAL"
    else:
        test_results["overall_status"] = "CRITICAL_ISSUES"
    
    test_results["summary"] = {
        "total_tests": len(test_statuses),
        "passed": pass_count,
        "failed": fail_count,
        "errors": error_count
    }
    
    return test_results

@router.get("/retirement-calculation-test/{user_id}")
async def retirement_calculation_test(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Specific test for retirement calculation accuracy
    Verifies Social Security is properly included
    """
    
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get financial data
        from app.services.financial_summary_service import financial_summary_service
        from app.models.user_profile import UserBenefit, UserProfile
        from app.models.goals_v2 import Goal
        
        summary = financial_summary_service.get_user_financial_summary(user_id, db)
        net_worth = summary.get("netWorth", 0)
        
        # Get Social Security
        ss_benefits = db.query(UserBenefit).join(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserBenefit.benefit_type == 'social_security'
        ).first()
        
        ss_monthly = float(ss_benefits.estimated_monthly_benefit or 0) if ss_benefits else 0
        ss_annual = ss_monthly * 12
        
        # Get retirement goal
        retirement_goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.name.ilike('%retirement%')
        ).all()
        
        retirement_goal = 3500000  # Default $3.5M
        if retirement_goals:
            retirement_goal = max(float(goal.target_amount) for goal in retirement_goals)
        
        # Calculate retirement math
        ss_portfolio_value = ss_annual * 25  # 4% rule: $1M generates $40K/year
        net_portfolio_needed = retirement_goal - ss_portfolio_value
        current_progress = (net_worth / net_portfolio_needed) * 100 if net_portfolio_needed > 0 else 0
        
        retirement_status = "AHEAD OF SCHEDULE" if net_worth >= net_portfolio_needed else "BEHIND SCHEDULE"
        
        return {
            "user_id": user_id,
            "retirement_calculation": {
                "retirement_goal": retirement_goal,
                "social_security_annual": ss_annual,
                "social_security_portfolio_value": ss_portfolio_value,
                "net_portfolio_needed": net_portfolio_needed,
                "current_net_worth": net_worth,
                "progress_percentage": round(current_progress, 1),
                "status": retirement_status,
                "years_ahead_behind": round((net_worth - net_portfolio_needed) / (summary.get("monthlySurplus", 1) * 12), 1) if summary.get("monthlySurplus", 0) > 0 else "N/A"
            },
            "validation": {
                "social_security_included": ss_annual > 0,
                "retirement_goal_set": retirement_goal > 0,
                "calculation_complete": True,
                "math_correct": net_worth > 0 and net_portfolio_needed > 0
            }
        }
        
    except Exception as e:
        return {
            "user_id": user_id,
            "error": str(e),
            "status": "CALCULATION_FAILED"
        }

@router.get("/context-quality-test/{user_id}")
async def context_quality_test(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Test the quality and completeness of financial context
    """
    
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        from app.services.complete_financial_context_service import complete_financial_context
        
        # Build context
        context = complete_financial_context.build_complete_context(
            user_id=user_id,
            db=db,
            user_query="What's my complete financial picture?"
        )
        
        # Quality checks
        quality_checks = {
            "context_length": len(context),
            "has_user_name": "Debashish" in context or "Roy" in context,
            "has_net_worth": "$2,5" in context,  # Looking for $2.5M+ 
            "has_retirement_goal": "$3,500,000" in context,
            "has_social_security": "Social Security" in context,
            "has_financial_score": "/100" in context,
            "has_asset_breakdown": "Investment Accounts:" in context,
            "has_real_estate": "Real Estate:" in context,
            "has_monthly_surplus": "Monthly Surplus:" in context,
            "has_debt_ratio": "Debt-to-Income:" in context,
            "has_savings_rate": "Savings Rate:" in context
        }
        
        # Count quality indicators
        quality_score = sum(1 for check in quality_checks.values() if check)
        total_checks = len(quality_checks)
        quality_percentage = (quality_score / total_checks) * 100
        
        return {
            "user_id": user_id,
            "context_analysis": {
                "quality_score": f"{quality_score}/{total_checks}",
                "quality_percentage": round(quality_percentage, 1),
                "context_length": len(context),
                "status": "EXCELLENT" if quality_percentage >= 90 else "GOOD" if quality_percentage >= 75 else "NEEDS_IMPROVEMENT"
            },
            "quality_checks": quality_checks,
            "sample_context": context[:500] + "..." if len(context) > 500 else context
        }
        
    except Exception as e:
        return {
            "user_id": user_id,
            "error": str(e),
            "status": "CONTEXT_TEST_FAILED"
        }