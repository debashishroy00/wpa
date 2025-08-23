"""
WealthPath AI - Financial Calculation Functions
Provides real dollar calculations for advisor recommendations
"""

import math
from typing import Dict, Optional, List
from datetime import datetime, date


def calculate_monthly_payment(balance: float, annual_rate: float, term_months: int) -> float:
    """Calculate monthly mortgage payment using standard formula"""
    if annual_rate == 0:
        return balance / term_months
    
    monthly_rate = annual_rate / 100 / 12
    payment = balance * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
    return payment


def calculate_early_payoff_savings(balance: float, annual_rate: float, current_payment: float, extra_payment: float) -> Dict:
    """Calculate savings from making extra mortgage payments"""
    monthly_rate = annual_rate / 100 / 12
    
    # Calculate normal payoff timeline
    normal_months = math.log(1 + (balance * monthly_rate) / current_payment) / math.log(1 + monthly_rate)
    normal_total_paid = current_payment * normal_months
    
    # Calculate accelerated payoff timeline
    accelerated_payment = current_payment + extra_payment
    accelerated_months = math.log(1 + (balance * monthly_rate) / accelerated_payment) / math.log(1 + monthly_rate)
    accelerated_total_paid = accelerated_payment * accelerated_months
    
    years_saved = (normal_months - accelerated_months) / 12
    interest_saved = normal_total_paid - accelerated_total_paid
    
    return {
        "years_saved": round(years_saved, 1),
        "months_saved": round(normal_months - accelerated_months),
        "interest_saved": round(interest_saved),
        "normal_payoff_years": round(normal_months / 12, 1),
        "accelerated_payoff_years": round(accelerated_months / 12, 1)
    }


def calculate_refinance_savings(current_balance: float, current_rate: float, new_rate: float, 
                              remaining_years: int, closing_costs: float = 3000) -> Dict:
    """Calculate savings from mortgage refinancing"""
    remaining_months = remaining_years * 12
    
    # Current payment calculation
    current_monthly_rate = current_rate / 100 / 12
    current_payment = current_balance * (current_monthly_rate * (1 + current_monthly_rate) ** remaining_months) / ((1 + current_monthly_rate) ** remaining_months - 1)
    
    # New payment calculation  
    new_monthly_rate = new_rate / 100 / 12
    new_payment = current_balance * (new_monthly_rate * (1 + new_monthly_rate) ** remaining_months) / ((1 + new_monthly_rate) ** remaining_months - 1)
    
    monthly_savings = current_payment - new_payment
    total_interest_savings = monthly_savings * remaining_months
    break_even_months = closing_costs / monthly_savings if monthly_savings > 0 else float('inf')
    
    return {
        "monthly_savings": round(monthly_savings),
        "annual_savings": round(monthly_savings * 12), 
        "total_savings": round(total_interest_savings),
        "break_even_months": round(break_even_months, 1),
        "closing_costs": closing_costs,
        "current_payment": round(current_payment),
        "new_payment": round(new_payment)
    }


def calculate_employer_match_benefit(annual_salary: float, current_contribution: float, 
                                    employer_match: float, match_limit: float) -> Dict:
    """
    Calculate the financial benefit of maximizing employer 401k match
    Professional-grade analysis with compound growth projections
    """
    # Current contribution amounts
    current_contribution_dollars = annual_salary * (current_contribution / 100)
    current_match_dollars = min(current_contribution_dollars * employer_match, 
                              annual_salary * (match_limit / 100) * employer_match)
    
    # Target contribution amounts  
    target_contribution_dollars = annual_salary * (match_limit / 100)
    target_match_dollars = target_contribution_dollars * employer_match
    
    # Calculate what's being missed
    missed_match = target_match_dollars - current_match_dollars
    missed_contribution = target_contribution_dollars - current_contribution_dollars
    total_missed_annual = missed_match + missed_contribution
    
    # Tax savings calculation
    tax_rate = 0.24  # Assume 24% bracket
    tax_savings = missed_contribution * tax_rate
    
    # Compound growth projections (assuming 8% annual growth)
    growth_rate = 0.08
    years_to_retirement = 27  # Age 38 to 65
    
    # Future value of missed annual contributions
    compound_retirement = total_missed_annual * (((1 + growth_rate) ** years_to_retirement - 1) / growth_rate)
    compound_20_year = total_missed_annual * (((1 + growth_rate) ** 20 - 1) / growth_rate)
    
    return {
        'current_contribution_percent': current_contribution,
        'target_contribution_percent': match_limit,
        'current_annual_contribution': round(current_contribution_dollars, 0),
        'target_annual_contribution': round(target_contribution_dollars, 0),
        'current_match': round(current_match_dollars, 0),
        'target_match': round(target_match_dollars, 0),
        'missed_annual': round(missed_match, 0),
        'missed_monthly': round(missed_match / 12, 0),
        'missed_contribution': round(missed_contribution, 0),
        'total_increase': round(total_missed_annual, 0),
        'tax_savings': round(tax_savings, 0),
        'compound_retirement': round(compound_retirement, 0),
        'compound_20_year': round(compound_20_year, 0),
        'roi_percent': round(employer_match * 100, 0)
    }


def calculate_401k_tax_savings(annual_income: float, current_contribution: float, new_contribution: float, tax_rate: float = 0.24) -> Dict:
    """Calculate tax savings from increasing 401k contribution"""
    contribution_increase = new_contribution - current_contribution
    additional_annual_contribution = annual_income * (contribution_increase / 100)
    annual_tax_savings = additional_annual_contribution * tax_rate
    
    return {
        "additional_contribution_annual": round(additional_annual_contribution),
        "additional_contribution_monthly": round(additional_annual_contribution / 12),
        "annual_tax_savings": round(annual_tax_savings),
        "monthly_tax_savings": round(annual_tax_savings / 12),
        "contribution_increase_percent": contribution_increase
    }


# Removed duplicate function - using the comprehensive version above


def calculate_investment_fee_savings(portfolio_value: float, current_expense_ratio: float, target_expense_ratio: float = 0.04) -> Dict:
    """Calculate savings from reducing investment fees"""
    current_annual_fees = portfolio_value * (current_expense_ratio / 100)
    target_annual_fees = portfolio_value * (target_expense_ratio / 100)
    annual_savings = current_annual_fees - target_annual_fees
    
    # Calculate compound effect over 20 years assuming 7% growth
    if annual_savings > 0:
        growth_rate = 0.07
        years = 20
        # Future value of annual savings compounded
        compound_savings = annual_savings * (((1 + growth_rate) ** years - 1) / growth_rate)
    else:
        compound_savings = 0
    
    return {
        "current_annual_fees": round(current_annual_fees),
        "target_annual_fees": round(target_annual_fees),
        "annual_savings": round(annual_savings),
        "monthly_savings": round(annual_savings / 12),
        "twenty_year_compound_savings": round(compound_savings),
        "current_ratio": current_expense_ratio,
        "target_ratio": target_expense_ratio
    }


def calculate_subscription_optimization(subscriptions: list, usage_threshold: str = "rarely") -> Dict:
    """Analyze subscription usage and identify savings opportunities"""
    total_cost = sum(s.get('cost', 0) for s in subscriptions)
    
    # Identify potentially unused subscriptions
    unused_subs = []
    for sub in subscriptions:
        usage = sub.get('usage_frequency', 'monthly')
        if usage in ['rarely', 'never']:
            unused_subs.append(sub)
    
    unused_cost = sum(s.get('cost', 0) for s in unused_subs)
    
    # If no unused, suggest bundle opportunities (estimate 15% savings)
    if not unused_subs and len(subscriptions) >= 3:
        bundle_savings = total_cost * 0.15
        return {
            "total_subscriptions": len(subscriptions),
            "total_monthly_cost": round(total_cost, 2),
            "unused_subscriptions": [],
            "bundle_opportunity": True,
            "potential_bundle_savings": round(bundle_savings, 2),
            "annual_bundle_savings": round(bundle_savings * 12, 2)
        }
    
    return {
        "total_subscriptions": len(subscriptions),
        "total_monthly_cost": round(total_cost, 2),
        "unused_subscriptions": unused_subs,
        "unused_monthly_cost": round(unused_cost, 2),
        "annual_savings": round(unused_cost * 12, 2),
        "bundle_opportunity": False
    }


# Removed duplicate function - using the professional version below


def calculate_mortgage_payoff_timeline(balance: float, annual_rate: float, monthly_payment: float, start_date: str) -> Dict:
    """Calculate when mortgage will be paid off and freed cash flow"""
    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00') if 'Z' in start_date else start_date)
        years_elapsed = (datetime.now() - start).days / 365.25
        
        # Calculate remaining term based on current payment
        monthly_rate = annual_rate / 100 / 12
        if monthly_rate > 0:
            remaining_months = math.log(1 + (balance * monthly_rate) / monthly_payment) / math.log(1 + monthly_rate)
        else:
            remaining_months = balance / monthly_payment
        
        remaining_years = remaining_months / 12
        payoff_date = datetime.now().replace(year=datetime.now().year + int(remaining_years))
        
        return {
            "years_elapsed": round(years_elapsed, 1),
            "remaining_years": round(remaining_years, 1),
            "payoff_date": payoff_date.strftime('%B %Y'),
            "monthly_payment_freed": monthly_payment,
            "annual_cash_flow_increase": monthly_payment * 12
        }
    except:
        return {}


def calculate_success_impact(monthly_benefit: float, current_gap: float) -> float:
    """
    Calculate the success rate improvement from a financial recommendation
    Professional-grade impact scoring based on gap closure percentage
    """
    if current_gap <= 0 or monthly_benefit <= 0:
        return 0.0
    
    # Calculate gap closure percentage
    gap_closure_percent = (monthly_benefit / current_gap) * 100
    
    # Professional impact scoring (matches industry standards)
    if gap_closure_percent >= 50:
        return 10.0  # +10% success rate - transformational impact
    elif gap_closure_percent >= 25:
        return 5.0   # +5% success rate - major impact
    elif gap_closure_percent >= 15:
        return 3.0   # +3% success rate - significant impact
    elif gap_closure_percent >= 10:
        return 2.0   # +2% success rate - moderate impact
    elif gap_closure_percent >= 5:
        return 1.5   # +1.5% success rate - meaningful impact
    elif gap_closure_percent >= 2:
        return 1.0   # +1% success rate - minor impact
    else:
        return 0.5   # +0.5% success rate - minimal impact


def calculate_priority_score(monthly_impact: float, implementation_ease: float, 
                           goal_alignment: int, risk_level: float) -> Dict:
    """
    Professional priority calculation using weighted scoring matrix
    """
    # Weighted scoring (matches professional advisory standards)
    impact_score = min(monthly_impact / 100, 40)     # Max 40 points (40% weight)
    ease_score = implementation_ease * 15             # Max 15 points (15% weight) 
    goal_score = (goal_alignment / 3) * 30           # Max 30 points (30% weight)
    risk_score = (10 - risk_level) * 1.5             # Max 15 points (15% weight)
    
    total_score = impact_score + ease_score + goal_score + risk_score
    
    # Professional priority classification
    if total_score >= 75:
        priority = 'HIGH'
        urgency = 'CRITICAL'
    elif total_score >= 50:
        priority = 'MEDIUM' 
        urgency = 'IMPORTANT'
    else:
        priority = 'LOW'
        urgency = 'OPTIONAL'
    
    return {
        'priority': priority,
        'urgency': urgency,
        'score': round(total_score, 1),
        'breakdown': {
            'impact': round(impact_score, 1),
            'ease': round(ease_score, 1), 
            'goals': round(goal_score, 1),
            'risk': round(risk_score, 1)
        }
    }


def calculate_portfolio_optimization_impact(current_allocation: Dict, target_allocation: Dict, 
                                          total_assets: float, time_horizon: int = 30) -> Dict:
    """
    Calculate the financial impact of portfolio rebalancing
    Professional analysis with expected returns and risk assessment
    """
    # Expected annual returns by asset class (industry standards)
    expected_returns = {
        'stocks': 0.10,      # 10% historical average
        'bonds': 0.04,       # 4% current environment
        'real_estate': 0.08, # 8% real estate appreciation
        'cash': 0.02,        # 2% money market
        'alternative': 0.12  # 12% but higher risk
    }
    
    # Calculate current expected return
    current_return = sum(
        current_allocation.get(asset, 0) * expected_returns.get(asset, 0) 
        for asset in expected_returns.keys()
    )
    
    # Calculate target expected return  
    target_return = sum(
        target_allocation.get(asset, 0) * expected_returns.get(asset, 0)
        for asset in expected_returns.keys()
    )
    
    # Calculate improvement
    return_improvement = target_return - current_return
    annual_benefit = total_assets * return_improvement
    lifetime_benefit = annual_benefit * time_horizon
    
    # Risk assessment
    current_risk = calculate_portfolio_risk(current_allocation)
    target_risk = calculate_portfolio_risk(target_allocation)
    
    return {
        'current_return': round(current_return * 100, 2),
        'target_return': round(target_return * 100, 2),
        'return_improvement': round(return_improvement * 100, 2),
        'annual_benefit': round(annual_benefit, 0),
        'lifetime_benefit': round(lifetime_benefit, 0),
        'current_risk': current_risk,
        'target_risk': target_risk,
        'risk_change': round(target_risk - current_risk, 1)
    }


def calculate_portfolio_risk(allocation: Dict) -> float:
    """
    Calculate portfolio risk score based on asset allocation
    Returns risk score from 1-10 (10 = highest risk)
    """
    # Risk scores by asset class
    risk_scores = {
        'stocks': 8,         # High volatility
        'bonds': 3,          # Low volatility
        'real_estate': 6,    # Medium volatility
        'cash': 1,           # No volatility
        'alternative': 9     # Very high volatility
    }
    
    weighted_risk = sum(
        allocation.get(asset, 0) * risk_scores.get(asset, 0)
        for asset in risk_scores.keys()
    )
    
    return round(weighted_risk, 1)


def calculate_tax_optimization_savings(income: float, current_tax_strategy: Dict, 
                                     proposed_strategy: Dict) -> Dict:
    """
    Calculate tax savings from optimization strategies
    Professional tax planning analysis
    """
    # Tax brackets for 2024 (simplified)
    tax_brackets = [
        (0, 22700, 0.10),      # 10%
        (22700, 89450, 0.12),  # 12%
        (89450, 190750, 0.22), # 22%
        (190750, 364200, 0.24) # 24%
    ]
    
    def calculate_tax(taxable_income):
        total_tax = 0
        for lower, upper, rate in tax_brackets:
            if taxable_income > lower:
                taxable_in_bracket = min(taxable_income - lower, upper - lower)
                total_tax += taxable_in_bracket * rate
        return total_tax
    
    # Current tax liability
    current_taxable = income - current_tax_strategy.get('deductions', 0)
    current_tax = calculate_tax(current_taxable)
    
    # Proposed tax liability
    proposed_taxable = income - proposed_strategy.get('deductions', 0)  
    proposed_tax = calculate_tax(proposed_taxable)
    
    # Calculate savings
    annual_savings = current_tax - proposed_tax
    
    return {
        'current_tax': round(current_tax, 0),
        'proposed_tax': round(proposed_tax, 0), 
        'annual_savings': round(annual_savings, 0),
        'monthly_savings': round(annual_savings / 12, 0),
        'effective_rate_current': round((current_tax / income) * 100, 2),
        'effective_rate_proposed': round((proposed_tax / income) * 100, 2)
    }