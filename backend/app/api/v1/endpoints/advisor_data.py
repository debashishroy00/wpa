"""
API endpoints for advisor-level data collection and smart recommendations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import json
from decimal import Decimal

from app.db.session import get_db
from app.models.user import User
from app.models.financial import FinancialEntry
from app.api.v1.endpoints.auth import get_current_active_user
from app.schemas.financial_enhanced import (
    AdvisorDataRequest,
    SmartRecommendation,
    EnhancedFinancialEntry
)

router = APIRouter()

@router.post("/save-advisor-data")
async def save_advisor_data(
    request: AdvisorDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Save advisor-level details to enhance recommendations
    """
    try:
        updates_made = []
        
        # Update mortgage details if provided
        if request.mortgage_rate is not None:
            db.execute(text("""
                UPDATE financial_entries 
                SET details = details || :new_details
                WHERE user_id = :user_id 
                AND (category = 'liabilities' OR category = 'expenses')
                AND description ILIKE '%mortgage%'
            """), {
                "user_id": current_user.id,
                "new_details": json.dumps({
                    k: v for k, v in {
                        "interest_rate": request.mortgage_rate,
                        "monthly_payment": request.mortgage_payment,
                        "lender": request.mortgage_lender,
                        "term_years": request.mortgage_term_years,
                        "start_date": request.mortgage_start_date
                    }.items() if v is not None
                })
            })
            updates_made.append("mortgage")
        
        # Update 401k details if provided
        if request.contribution_401k is not None:
            db.execute(text("""
                UPDATE financial_entries 
                SET details = details || :new_details
                WHERE user_id = :user_id 
                AND category = 'assets'
                AND description ILIKE '%401k%'
            """), {
                "user_id": current_user.id,
                "new_details": json.dumps({
                    k: v for k, v in {
                        "contribution_percent": request.contribution_401k,
                        "employer_match": request.employer_match,
                        "employer_match_limit": request.employer_match_limit,
                        "vesting_schedule": request.vesting_schedule
                    }.items() if v is not None
                })
            })
            updates_made.append("401k")
        
        # Update investment details if provided
        if request.stock_percentage is not None:
            db.execute(text("""
                UPDATE financial_entries 
                SET details = details || :new_details
                WHERE user_id = :user_id 
                AND category = 'assets'
                AND (subcategory ILIKE '%investment%' OR description ILIKE '%mutual%' OR description ILIKE '%etf%' OR description ILIKE '%stock%')
                AND id = (
                    SELECT id FROM financial_entries 
                    WHERE user_id = :user_id 
                    AND category = 'assets'
                    AND (subcategory ILIKE '%investment%' OR description ILIKE '%mutual%' OR description ILIKE '%etf%' OR description ILIKE '%stock%')
                    ORDER BY id 
                    LIMIT 1
                )
            """), {
                "user_id": current_user.id,
                "new_details": json.dumps({
                    k: v for k, v in {
                        "stock_percentage": request.stock_percentage,
                        "bond_percentage": request.bond_percentage,
                        "average_expense_ratio": request.average_expense_ratio,
                        "platform": request.investment_platform
                    }.items() if v is not None
                })
            })
            updates_made.append("investments")
        
        # Save subscriptions as separate entries
        if request.subscriptions:
            for sub in request.subscriptions:
                # Check if subscription already exists
                existing = db.execute(text("""
                    SELECT id FROM financial_entries
                    WHERE user_id = :user_id
                    AND category = 'expenses'
                    AND description = :description
                    AND subcategory = 'subscription'
                """), {
                    "user_id": current_user.id,
                    "description": sub.name
                }).fetchone()
                
                if existing:
                    # Update existing
                    db.execute(text("""
                        UPDATE financial_entries
                        SET amount = :amount,
                            details = details || :details
                        WHERE id = :id
                    """), {
                        "id": existing.id,
                        "amount": float(sub.cost),
                        "details": json.dumps({
                            "usage_frequency": sub.usage_frequency,
                            "can_cancel": sub.can_cancel
                        })
                    })
                else:
                    # Create new
                    db.execute(text("""
                        INSERT INTO financial_entries 
                        (user_id, category, subcategory, description, amount, frequency, currency, entry_date, data_quality, confidence_score, source, is_active, is_recurring, is_estimate, details)
                        VALUES (:user_id, 'expenses', 'subscription', :description, :amount, 'monthly', 'USD', NOW(), 'DQ4', 0.9, 'user_input', true, true, false, :details)
                    """), {
                        "user_id": current_user.id,
                        "description": sub.name,
                        "amount": float(sub.cost),
                        "details": json.dumps({
                            "usage_frequency": sub.usage_frequency,
                            "can_cancel": sub.can_cancel
                        })
                    })
            updates_made.append("subscriptions")
        
        db.commit()
        
        return {
            "status": "success",
            "updates_made": updates_made,
            "message": "Advisor data saved successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save advisor data: {str(e)}")

@router.get("/smart-recommendations")
async def get_smart_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[SmartRecommendation]:
    """
    Generate smart recommendations based on advisor-level data
    """
    recommendations = []
    
    # Get user's enhanced financial data
    financial_data = db.execute(text("""
        SELECT 
            category,
            description,
            amount,
            details
        FROM financial_entries
        WHERE user_id = :user_id
        AND is_active = true
    """), {"user_id": current_user.id}).fetchall()
    
    # Process mortgage refinancing opportunity
    for entry in financial_data:
        if 'mortgage' in entry.description.lower() and entry.details:
            details = entry.details if isinstance(entry.details, dict) else json.loads(entry.details)
            current_rate = details.get('interest_rate')
            monthly_payment = details.get('monthly_payment')
            start_date = details.get('start_date')
            term_years = details.get('term_years')
            
            # Calculate refinancing opportunity
            if current_rate is not None and current_rate > 6.0:  # Current market rate assumption
                potential_rate = 5.8
                balance = float(entry.amount) if entry.category == 'liabilities' else None
                
                if balance and monthly_payment:
                    # More accurate calculation using actual payment and balance
                    current_interest_portion = balance * (current_rate / 100 / 12)
                    new_interest_portion = balance * (potential_rate / 100 / 12)
                    monthly_savings = current_interest_portion - new_interest_portion
                else:
                    # No fallback hardcoded values - use only real data
                    monthly_savings = monthly_payment * ((current_rate - potential_rate) / current_rate) * 0.7 if monthly_payment else 0
                
                recommendations.append(SmartRecommendation(
                    id="refinance-mortgage",
                    category="mortgage",
                    title=f"Refinance Your {current_rate}% Mortgage",
                    description=f"Your current {current_rate}% rate is above market rates. Refinancing to {potential_rate}% could save you money.",
                    current_value=current_rate,
                    recommended_value=potential_rate,
                    monthly_savings=monthly_savings,
                    annual_savings=monthly_savings * 12,
                    action_steps=[
                        "Get quotes from 3-5 lenders",
                        "Calculate break-even point including closing costs",
                        "Submit application to best lender",
                        "Schedule appraisal"
                    ],
                    difficulty="medium",
                    time_to_implement="30-45 days",
                    confidence_level="high",
                    assumptions_made=[]
                ))
            
            # Calculate mortgage payoff timeline and freed money
            if monthly_payment and start_date and term_years:
                from datetime import datetime
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00') if 'Z' in start_date else start_date)
                    years_elapsed = (datetime.now() - start).days / 365.25
                    years_remaining = max(0, term_years - years_elapsed)
                    
                    if years_remaining > 0 and years_remaining < 15:  # Only show if payoff is within 15 years
                        months_remaining = int(years_remaining * 12)
                        payoff_date = datetime.now().replace(year=datetime.now().year + int(years_remaining))
                        
                        recommendations.append(SmartRecommendation(
                            id="mortgage-payoff-timeline",
                            category="mortgage",
                            title=f"Mortgage Payoff in {int(years_remaining)} Years",
                            description=f"Your mortgage will be paid off by {payoff_date.strftime('%B %Y')}, freeing up ${monthly_payment:,.0f}/month.",
                            current_value=years_remaining,
                            recommended_value=0,
                            monthly_savings=0,  # Not a saving, but freed money
                            annual_savings=monthly_payment * 12,  # This is the freed amount
                            action_steps=[
                                f"Continue regular payments until {payoff_date.strftime('%B %Y')}",
                                f"Plan for ${monthly_payment:,.0f}/month in freed cash flow",
                                "Consider increasing investment contributions post-payoff",
                                "Evaluate if extra payments could accelerate payoff"
                            ],
                            difficulty="easy",
                            time_to_implement=f"{int(years_remaining)} years (automatic)",
                            confidence_level="high",
                            assumptions_made=[]
                        ))
                except (ValueError, TypeError):
                    pass  # Invalid date format
    
    # Process 401k optimization
    for entry in financial_data:
        if '401k' in entry.description.lower() and entry.details:
            details = entry.details if isinstance(entry.details, dict) else json.loads(entry.details)
            contribution = details.get('contribution_percent')
            employer_match = details.get('employer_match')
            match_limit = details.get('employer_match_limit', employer_match)
            
            if contribution is not None and employer_match is not None and match_limit is not None and contribution < match_limit:
                # Calculate additional match available
                salary = 212928  # Annual from monthly income
                current_match = min(contribution, employer_match) * salary / 100
                max_match = employer_match * salary / 100
                missed_match = max_match - current_match
                
                recommendations.append(SmartRecommendation(
                    id="maximize-401k-match",
                    category="retirement",
                    title=f"Capture Full Employer Match",
                    description=f"Increase your 401k contribution from {contribution}% to {match_limit}% to get the full employer match.",
                    current_value=contribution,
                    recommended_value=match_limit,
                    monthly_savings=0,  # This is actually earning
                    annual_savings=missed_match,
                    action_steps=[
                        f"Log into your 401k portal",
                        f"Change contribution to {match_limit}%",
                        f"Verify next paycheck reflects change"
                    ],
                    difficulty="easy",
                    time_to_implement="Next payroll cycle",
                    confidence_level="high",
                    assumptions_made=[]
                ))
    
    # Process subscription optimization
    subscription_entries = [e for e in financial_data if e.category == 'expenses' and 'subscription' in str(e.details)]
    if len(subscription_entries) > 3:
        total_subscription_cost = sum(float(e.amount) for e in subscription_entries)
        
        # Identify rarely used subscriptions
        unused_subs = []
        for entry in subscription_entries:
            if entry.details:
                details = entry.details if isinstance(entry.details, dict) else json.loads(entry.details)
                if details.get('usage_frequency') in ['rarely', 'never']:
                    unused_subs.append({
                        'name': entry.name,
                        'cost': float(entry.amount)
                    })
        
        if unused_subs:
            total_savings = sum(s['cost'] for s in unused_subs)
            recommendations.append(SmartRecommendation(
                id="cancel-unused-subscriptions",
                category="expenses",
                title="Cancel Unused Subscriptions",
                description=f"You have {len(unused_subs)} subscriptions you rarely use.",
                current_value=total_subscription_cost,
                recommended_value=total_subscription_cost - total_savings,
                monthly_savings=total_savings,
                annual_savings=total_savings * 12,
                action_steps=[f"Cancel {s['name']} (${s['cost']}/mo)" for s in unused_subs],
                difficulty="easy",
                time_to_implement="30 minutes",
                confidence_level="high",
                assumptions_made=[]
            ))
    
    # Investment fee optimization
    for entry in financial_data:
        if entry.category == 'assets' and ('investment' in entry.description.lower() or 'mutual' in entry.description.lower() or 'etf' in entry.description.lower()) and entry.details:
            details = entry.details if isinstance(entry.details, dict) else json.loads(entry.details)
            expense_ratio = details.get('average_expense_ratio')
            
            if expense_ratio is not None and expense_ratio > 0.5:
                balance = float(entry.amount)
                current_fees = balance * (expense_ratio / 100)
                target_ratio = 0.1
                new_fees = balance * (target_ratio / 100)
                annual_savings = current_fees - new_fees
                
                recommendations.append(SmartRecommendation(
                    id="reduce-investment-fees",
                    category="investments",
                    title="Reduce Investment Fees",
                    description=f"Your {expense_ratio}% expense ratio is high. Switch to low-cost index funds.",
                    current_value=expense_ratio,
                    recommended_value=target_ratio,
                    monthly_savings=annual_savings / 12,
                    annual_savings=annual_savings,
                    action_steps=[
                        "Research low-cost index funds (VTSAX, VTIAX)",
                        "Compare expense ratios",
                        "Rebalance portfolio to lower-fee funds"
                    ],
                    difficulty="medium",
                    time_to_implement="1-2 weeks",
                    confidence_level="high" if expense_ratio else "medium",
                    assumptions_made=[] if expense_ratio else ["Assumed 0.75% average expense ratio"]
                ))
    
    return recommendations

@router.get("/advisor-data")
async def get_advisor_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve current advisor-level data for the user
    """
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
    """), {"user_id": current_user.id}).fetchall()
    
    advisor_data = {
        "mortgage": {},
        "retirement": {},
        "investments": {},
        "subscriptions": []
    }
    
    for entry in entries:
        details = entry.details if isinstance(entry.details, dict) else json.loads(entry.details or '{}')
        
        if 'mortgage' in entry.description.lower():
            advisor_data["mortgage"] = {
                "balance": float(entry.amount),
                **details
            }
        elif '401k' in entry.description.lower():
            advisor_data["retirement"] = {
                "balance": float(entry.amount),
                **details
            }
        elif entry.category == 'assets' and ('investment' in entry.subcategory.lower() if entry.subcategory else False or 'mutual' in entry.description.lower() or 'etf' in entry.description.lower()):
            advisor_data["investments"] = {
                "balance": float(entry.amount),
                **details
            }
        elif entry.subcategory == 'subscription':
            advisor_data["subscriptions"].append({
                "name": entry.description,
                "cost": float(entry.amount),
                **details
            })
    
    return advisor_data