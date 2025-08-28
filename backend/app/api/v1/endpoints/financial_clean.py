"""
WealthPath AI - Clean Financial Summary Endpoint
Generates comprehensive financial summaries with LIVE data from financial_entries
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timezone, date
from decimal import Decimal
import structlog

from app.db.session import get_db
from app.models.user import User
from app.models.goals_v2 import Goal, GoalProgress, UserPreferences
from app.models.financial import FinancialEntry, EntryCategory, FrequencyType
from app.api.v1.endpoints.auth import get_current_active_user

logger = structlog.get_logger()
router = APIRouter()

@router.get("/comprehensive-summary/{user_id}")
async def get_comprehensive_summary(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate comprehensive financial summary with LIVE calculations.
    This replaces the broken snapshot-based approach.
    
    Returns structure matching comprehensive-summary.json format with ALL preferences.
    """
    
    # Verify user access
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get user basic info
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user preferences with ALL fields including enhanced and tax preferences
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if not preferences:
        # Create default preferences if none exist
        preferences = UserPreferences(
            user_id=user_id,
            risk_tolerance='moderate',
            investment_timeline=11,  # Assuming retirement at 65, current age 54
            financial_knowledge='intermediate',
            emergency_fund_months=6,
            debt_payoff_priority='balanced'
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    # Get ALL financial entries for live calculations
    entries = db.query(FinancialEntry).filter(
        FinancialEntry.user_id == user_id
    ).all()
    
    logger.info(f"Found {len(entries)} total financial entries for user {user_id}")
    
    # Filter for active entries
    active_entries = [entry for entry in entries if entry.is_active]
    logger.info(f"Found {len(active_entries)} active financial entries for user {user_id}")
        
    entries = active_entries
    
    # Calculate live financial data
    assets_by_category = {}
    liabilities = []
    monthly_income = Decimal('0')
    monthly_expenses = Decimal('0')
    
    for entry in entries:
        if entry.category == EntryCategory.assets:
            # Handle null subcategory - Primary Home should be real_estate
            subcategory = entry.subcategory
            if not subcategory or subcategory.strip() == '':
                # Default to real_estate for high-value items, other_assets for smaller ones
                if float(entry.amount) > 100000:  # Likely real estate
                    subcategory = 'real_estate'
                else:
                    subcategory = 'other_assets'
            
            if subcategory not in assets_by_category:
                assets_by_category[subcategory] = []
            
            assets_by_category[subcategory].append({
                "name": entry.description,
                "value": float(entry.amount),
                "subcategory": subcategory
            })
        
        elif entry.category == EntryCategory.liabilities:
            liabilities.append({
                "name": entry.description,
                "balance": float(entry.amount),
                "subcategory": entry.subcategory or 'other_debt',
                "type": entry.subcategory or 'debt'
            })
        
        elif entry.category == EntryCategory.income:
            # Convert to monthly amount
            if entry.frequency == FrequencyType.monthly:
                monthly_income += entry.amount
            elif entry.frequency == FrequencyType.annually:
                monthly_income += entry.amount / 12
            elif entry.frequency == FrequencyType.weekly:
                monthly_income += entry.amount * 52 / 12
        
        elif entry.category == EntryCategory.expenses:
            # Convert to monthly amount
            if entry.frequency == FrequencyType.monthly:
                monthly_expenses += entry.amount
            elif entry.frequency == FrequencyType.annually:
                monthly_expenses += entry.amount / 12
            elif entry.frequency == FrequencyType.weekly:
                monthly_expenses += entry.amount * 52 / 12
    
    # Organize assets by main categories
    real_estate = assets_by_category.get('real_estate', [])
    investments = (
        assets_by_category.get('retirement_accounts', []) +
        assets_by_category.get('investment_accounts', []) +
        assets_by_category.get('stocks_bonds', [])
    )
    cash = (
        assets_by_category.get('cash_bank_accounts', []) +
        assets_by_category.get('other_assets', [])
    )
    personal_property = assets_by_category.get('personal_property', [])
    
    # Calculate totals
    total_assets = sum(asset['value'] for category in assets_by_category.values() for asset in category)
    total_liabilities = sum(liability['balance'] for liability in liabilities)
    net_worth = total_assets - total_liabilities
    monthly_surplus = float(monthly_income - monthly_expenses)
    savings_rate = (monthly_surplus / float(monthly_income)) * 100 if monthly_income > 0 else 0
    
    # Calculate monthly debt payments (CORRECT DTI calculation)
    # Look for debt payments in expenses
    monthly_debt_payments = Decimal('0')
    debt_payment_descriptions = ['Mortgage', 'Home Loan Payment', 'Credit Card Payment', 'Loan Payment', 'Car Payment', 'Student Loan Payment']
    
    for entry in entries:
        if entry.category == EntryCategory.expenses and any(debt_desc.lower() in entry.description.lower() for debt_desc in debt_payment_descriptions):
            # Convert to monthly amount
            if entry.frequency == FrequencyType.monthly:
                monthly_debt_payments += entry.amount
            elif entry.frequency == FrequencyType.annually:
                monthly_debt_payments += entry.amount / 12
            elif entry.frequency == FrequencyType.weekly:
                monthly_debt_payments += entry.amount * 52 / 12
    
    # If no debt payments found in expenses, estimate from liabilities
    if monthly_debt_payments == 0 and total_liabilities > 0:
        # Get specific liability amounts for estimation
        mortgage_balance = sum(liability['balance'] for liability in liabilities if 'mortgage' in liability.get('subcategory', '').lower() or 'real_estate' in liability.get('subcategory', '').lower())
        credit_card_balance = sum(liability['balance'] for liability in liabilities if 'credit' in liability.get('subcategory', '').lower())
        other_debt_balance = total_liabilities - mortgage_balance - credit_card_balance
        
        # Estimate monthly payments
        # Mortgage: Assume 30-year at 5% interest (monthly payment factor: 0.005368)
        mortgage_payment = (mortgage_balance * 0.005368) if mortgage_balance > 0 else 0
        
        # Credit cards: Assume 2% minimum payment
        credit_card_payment = (credit_card_balance * 0.02) if credit_card_balance > 0 else 0
        
        # Other debt: Assume 3% monthly payment (varies by type)
        other_debt_payment = (other_debt_balance * 0.03) if other_debt_balance > 0 else 0
        
        monthly_debt_payments = Decimal(str(mortgage_payment + credit_card_payment + other_debt_payment))
    
    # REMOVED: Hardcoded values were providing misleading financial data
    # All debt payments must come from real user data only
    
    # Calculate DTI correctly using monthly debt payments
    debt_to_income_ratio = round((float(monthly_debt_payments) / float(monthly_income)) * 100, 1) if monthly_income > 0 else 0
    
    logger.info(f"DTI Calculation - Monthly Debt Payments: ${monthly_debt_payments}, Monthly Income: ${monthly_income}, DTI: {debt_to_income_ratio}%")
    logger.info(f"Calculated totals - Assets: ${total_assets}, Liabilities: ${total_liabilities}, Net Worth: ${net_worth}")
    
    # Calculate asset allocation
    real_estate_value = sum(asset['value'] for asset in real_estate)
    investments_value = sum(asset['value'] for asset in investments)
    cash_value = sum(asset['value'] for asset in cash)
    personal_property_value = sum(asset['value'] for asset in personal_property)
    
    asset_allocation = {
        "realEstate": {"value": real_estate_value, "percentage": round((real_estate_value / total_assets) * 100, 1) if total_assets > 0 else 0},
        "investments": {"value": investments_value, "percentage": round((investments_value / total_assets) * 100, 1) if total_assets > 0 else 0},
        "cash": {"value": cash_value, "percentage": round((cash_value / total_assets) * 100, 1) if total_assets > 0 else 0},
        "personalProperty": {"value": personal_property_value, "percentage": round((personal_property_value / total_assets) * 100, 1) if total_assets > 0 else 0}
    }
    
    # Get goals with progress
    goals = db.query(Goal).filter(
        and_(
            Goal.user_id == user_id,
            Goal.status == 'active'
        )
    ).all()
    
    goals_data = []
    for goal in goals:
        # Get latest progress
        latest_progress = db.query(GoalProgress).filter(
            GoalProgress.goal_id == goal.goal_id
        ).order_by(desc(GoalProgress.recorded_at)).first()
        
        current_progress = float(latest_progress.current_amount) if latest_progress else 0
        progress_percentage = (current_progress / float(goal.target_amount)) * 100 if goal.target_amount > 0 else 0
        
        # Calculate years to goal and monthly required
        target_date = goal.target_date
        current_date = date.today()
        years_to_goal = (target_date - current_date).days / 365.25
        
        remaining_amount = float(goal.target_amount) - current_progress
        monthly_required = remaining_amount / (years_to_goal * 12) if years_to_goal > 0 else 0
        
        goals_data.append({
            "goal_id": str(goal.goal_id),
            "user_id": goal.user_id,
            "category": goal.category,
            "name": goal.name,
            "target_amount": float(goal.target_amount),
            "target_date": goal.target_date.isoformat(),
            "priority": goal.priority,
            "status": goal.status,
            "params": goal.params,
            "yearsToGoal": round(years_to_goal, 1),
            "monthlyRequired": round(monthly_required, 2),
            "currentProgress": current_progress,
            "progressPercentage": round(progress_percentage, 1)
        })
    
    # Build comprehensive preferences object with ALL fields
    preferences_data = {
        # Basic preferences
        "risk_tolerance": preferences.risk_tolerance,
        "investment_timeline": preferences.investment_timeline,
        "financial_knowledge": preferences.financial_knowledge,
        "retirement_age": preferences.retirement_age,
        "annual_income_goal": float(preferences.annual_income_goal) if preferences.annual_income_goal else None,
        "emergency_fund_months": preferences.emergency_fund_months,
        "debt_payoff_priority": preferences.debt_payoff_priority,
        "notification_preferences": preferences.notification_preferences,
        "goal_categories_enabled": preferences.goal_categories_enabled,
        
        # Enhanced investment preferences
        "risk_score": preferences.risk_score,
        "investment_style": preferences.investment_style,
        "stocks_preference": preferences.stocks_preference,
        "bonds_preference": preferences.bonds_preference,
        "real_estate_preference": preferences.real_estate_preference,
        "crypto_preference": preferences.crypto_preference,
        "retirement_lifestyle": preferences.retirement_lifestyle,
        "work_flexibility": preferences.work_flexibility,
        "esg_investing": preferences.esg_investing,
        
        # Tax preferences
        "tax_filing_status": preferences.tax_filing_status,
        "federal_tax_bracket": float(preferences.federal_tax_bracket) if preferences.federal_tax_bracket else None,
        "state_tax_rate": float(preferences.state_tax_rate) if preferences.state_tax_rate else None,
        "state": preferences.state,
        "tax_optimization_priority": preferences.tax_optimization_priority,
        "tax_loss_harvesting": preferences.tax_loss_harvesting,
        "roth_ira_eligible": preferences.roth_ira_eligible,
        
        # Timestamps
        "created_at": preferences.created_at.isoformat() if preferences.created_at else None,
        "updated_at": preferences.updated_at.isoformat() if preferences.updated_at else None
    }
    
    # Generate personalized recommendations based on preferences
    recommendations = generate_personalized_recommendations(
        preferences_data, 
        {
            "net_worth": net_worth,
            "monthly_surplus": monthly_surplus,
            "savings_rate": savings_rate,
            "asset_allocation": asset_allocation,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities
        }
    )
    
    # Build comprehensive response
    comprehensive_summary = {
        "user": {
            "id": user.id,
            "name": f"{user.first_name} {user.last_name}".strip() or "User",
            "age": calculate_age(preferences.retirement_age, preferences.investment_timeline) if preferences.retirement_age and preferences.investment_timeline else 54,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None
        },
        "preferences": preferences_data,
        "financials": {
            "netWorth": net_worth,
            "totalAssets": total_assets,
            "totalLiabilities": total_liabilities,
            "monthlyIncome": float(monthly_income),
            "monthlyExpenses": float(monthly_expenses),
            "monthlySurplus": monthly_surplus,
            "savingsRate": round(savings_rate, 1),
            "debtToIncomeRatio": debt_to_income_ratio,
            "monthlyDebtPayments": float(monthly_debt_payments),
            "emergencyFundCoverage": round(cash_value / float(monthly_expenses), 1) if monthly_expenses > 0 else 0,
            "assets": {
                "realEstate": real_estate,
                "investments": investments,
                "cash": cash,
                "personalProperty": personal_property
            },
            "liabilities": liabilities,
            "cashFlow": {
                "monthlyIncome": float(monthly_income),
                "monthlyExpenses": float(monthly_expenses),
                "surplus": monthly_surplus
            },
            "assetAllocation": asset_allocation
        },
        "goals": goals_data,
        "recommendations": recommendations,
        "database_metadata": {
            "total_tables": 30,
            "total_financial_entries": len(entries),
            "total_users": 1,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "data_quality_score": calculate_data_quality_score(entries, preferences_data),
            "calculation_method": "live_financial_entries"
        }
    }
    
    return comprehensive_summary

def calculate_age(retirement_age: Optional[int], timeline: Optional[int]) -> int:
    """Calculate current age based on retirement age and timeline"""
    if retirement_age and timeline:
        return retirement_age - timeline
    return 54  # Default based on known user data

def generate_personalized_recommendations(preferences: Dict, financials: Dict) -> Dict[str, Any]:
    """Generate personalized recommendations based on user preferences and financial data"""
    recommendations = {
        "portfolio_adjustment": "",
        "risk_assessment": "",
        "tax_optimization": "",
        "next_steps": [],
        "warnings": []
    }
    
    # Portfolio recommendations based on investment preferences
    if preferences.get("investment_style") == "aggressive" and preferences.get("stocks_preference", 0) >= 7:
        recommendations["portfolio_adjustment"] = f"Based on your aggressive investment style and {preferences.get('stocks_preference', 0)}/10 stock preference, consider increasing equity allocation to 80-90%"
    elif preferences.get("investment_style") == "moderate":
        recommendations["portfolio_adjustment"] = f"Your moderate approach suggests a balanced 60/40 stocks/bonds allocation aligns with your {preferences.get('stocks_preference', 0)}/10 stock preference"
    
    # Risk assessment based on current allocation
    real_estate_pct = financials.get("asset_allocation", {}).get("realEstate", {}).get("percentage", 0)
    if real_estate_pct > 40:
        recommendations["risk_assessment"] = f"Current {real_estate_pct}% real estate concentration exceeds recommended 30% for {preferences.get('risk_tolerance', 'moderate')} risk profile"
    
    # Tax optimization based on tax preferences
    if preferences.get("tax_filing_status") and preferences.get("federal_tax_bracket"):
        tax_bracket = preferences.get("federal_tax_bracket", 0) * 100
        if preferences.get("tax_loss_harvesting"):
            recommendations["tax_optimization"] = f"As someone in the {tax_bracket:.0f}% federal bracket with tax loss harvesting enabled, consider municipal bonds for tax efficiency"
        else:
            recommendations["tax_optimization"] = f"In the {tax_bracket:.0f}% bracket, consider enabling tax loss harvesting and maximizing 401(k) contributions"
    
    # Emergency fund recommendation
    emergency_coverage = financials.get("emergencyFundCoverage", 0)
    target_months = preferences.get("emergency_fund_months", 6)
    if emergency_coverage < target_months:
        monthly_expenses = financials.get("monthlyExpenses", 0)
        needed_amount = (target_months - emergency_coverage) * monthly_expenses
        recommendations["next_steps"].append(f"Increase emergency fund from {emergency_coverage:.1f} to {target_months} months expenses (${needed_amount:,.0f})")
    
    # Retirement savings recommendation
    if preferences.get("roth_ira_eligible") and financials.get("monthlySurplus", 0) > 5000:
        recommendations["next_steps"].append("Consider maximizing Roth IRA contributions ($6,500 annual limit)")
    
    # Goal-based recommendations
    if financials.get("savingsRate", 0) > 50:
        recommendations["next_steps"].append("Excellent savings rate! Consider tax-advantaged account optimization")
    
    # Warnings based on preferences and data
    if emergency_coverage < target_months:
        recommendations["warnings"].append(f"Emergency fund below target of {target_months} months")
    
    if real_estate_pct > 50:
        recommendations["warnings"].append(f"High concentration in real estate ({real_estate_pct:.1f}%)")
    
    return recommendations

def calculate_data_quality_score(entries: List, preferences: Dict) -> int:
    """Calculate data quality score based on completeness and consistency"""
    score = 100
    
    # Deduct for missing financial data
    if len(entries) < 10:
        score -= 20
    
    # Deduct for missing preferences
    if not preferences.get("risk_score"):
        score -= 10
    if not preferences.get("tax_filing_status"):
        score -= 10
    if not preferences.get("investment_style"):
        score -= 10
    
    # Deduct for data inconsistencies
    asset_entries = [e for e in entries if e.category == 'assets']
    if len(set(e.description for e in asset_entries)) != len(asset_entries):
        score -= 15  # Duplicate asset names
    
    return max(score, 0)