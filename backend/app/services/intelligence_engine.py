"""
WealthPath AI - Intelligence Analysis Engine
Provides comprehensive financial goal analysis, conflict detection, and optimization
"""

# import numpy as np # DISABLED FOR DEPLOYMENT
from app.services.ml_fallbacks import np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.models.goals_v2 import Goal, UserPreferences
from app.models.financial import FinancialEntry, NetWorthSnapshot
from app.schemas.goals_v2 import GoalResponse
# Financial calculation functions now handled by formula_library
from app.services.formula_library import formula_library
# Note: tax_calculations not available, using simplified calculations

# Temporary stub functions for intelligence engine compatibility
def calculate_early_payoff_savings(balance, rate, payment, extra_payment):
    return max(0, balance * 0.1)  # Simplified calculation

def calculate_401k_tax_savings(salary, contribution, new_total):
    return new_total * 0.24  # Simplified tax savings at 24% bracket

def calculate_employer_match_benefit(salary, contribution, match, limit):
    current_match = min(contribution * match / 100, salary * limit / 100)  # Current match earned
    max_possible_match = salary * limit / 100  # Maximum possible match
    missed_annual = max_possible_match - current_match
    missed_monthly = missed_annual / 12
    
    # Calculate tax savings from additional contributions
    additional_contribution_needed = (limit - contribution) * salary / 100
    tax_savings = additional_contribution_needed * 0.24  # Assume 24% tax bracket
    
    return {
        'current_match': round(current_match, 2),
        'max_possible_match': round(max_possible_match, 2),
        'missed_annual': round(missed_annual, 2),
        'missed_monthly': round(missed_monthly, 2),
        'optimal_contribution_rate': limit,
        'current_contribution_rate': contribution,
        'tax_savings': round(tax_savings, 2),
        'additional_contribution_needed': round(additional_contribution_needed, 2)
    }

def calculate_investment_fee_savings(balance, old_fee, new_fee):
    return balance * (old_fee - new_fee) / 100

def calculate_subscription_optimization(subscriptions):
    return sum(sub.get('potential_savings', 0) for sub in subscriptions)

def calculate_success_impact(goal_type, amount):
    return amount * 0.15  # 15% impact factor

def calculate_mortgage_payoff_timeline(balance, payment, rate):
    if payment <= balance * rate / 12:
        return 999  # Never pays off
    return balance / (payment - balance * rate / 12) / 12

def calculate_refinance_savings(balance, old_rate, new_rate, term):
    old_payment = balance * (old_rate / 12) * (1 + old_rate / 12) ** term / ((1 + old_rate / 12) ** term - 1)
    new_payment = balance * (new_rate / 12) * (1 + new_rate / 12) ** term / ((1 + new_rate / 12) ** term - 1)
    monthly_savings = old_payment - new_payment
    annual_savings = monthly_savings * 12
    closing_costs = balance * 0.02  # Estimate 2% of loan balance
    break_even_months = closing_costs / monthly_savings if monthly_savings > 0 else 999
    total_savings = annual_savings * term - closing_costs
    
    return {
        'monthly_savings': round(monthly_savings, 2),
        'annual_savings': round(annual_savings, 2),
        'old_payment': round(old_payment, 2),
        'current_payment': round(old_payment, 2),  # Same as old_payment
        'new_payment': round(new_payment, 2),
        'closing_costs': round(closing_costs, 2),
        'break_even_months': round(break_even_months, 1),
        'total_savings': round(total_savings, 2)
    }

def calculate_priority_score(impact, effort, urgency):
    score = impact * urgency / max(effort, 1)
    return {
        'score': round(score, 2),
        'impact': impact,
        'effort': effort,
        'urgency': urgency,
        'priority_level': 'high' if score > 50 else 'medium' if score > 20 else 'low'
    }

def calculate_portfolio_optimization_impact(balance, old_return, new_return, years):
    old_value = balance * (1 + old_return) ** years
    new_value = balance * (1 + new_return) ** years
    return new_value - old_value

def calculate_portfolio_risk(allocation):
    return sum(asset.get('risk_score', 0.5) * asset.get('percentage', 0) for asset in allocation) / 100

def calculate_tax_optimization_savings(income, bracket, deductions):
    return deductions * (bracket / 100)


class ConflictType(str, Enum):
    CASH_FLOW = "cash_flow"
    TIMELINE = "timeline" 
    RISK = "risk"
    LIFESTYLE = "lifestyle"


class ConflictSeverity(str, Enum):
    CRITICAL = "critical"
    MODERATE = "moderate"
    MINOR = "minor"


@dataclass
class Conflict:
    id: str
    type: ConflictType
    severity: ConflictSeverity
    description: str
    affected_goals: List[str]
    resolution_options: List[Dict]
    shortfall_amount: Optional[float] = None


@dataclass
class GapAnalysis:
    monthly_shortfall: float
    total_capital_needed: float
    current_trajectory: float
    gap_amount: float


@dataclass
class Scenario:
    id: str
    name: str
    success_rate: float
    risk_score: int
    lifestyle_impact: float
    required_changes: List[Dict]
    is_recommended: bool
    preference_alignment: float


@dataclass
class SimulationResult:
    success_rate: float
    percentiles: Dict[str, float]
    mean: float
    std_dev: float


@dataclass
class FinancialState:
    net_worth: float
    monthly_income: float
    monthly_expenses: float
    monthly_surplus: float
    liquid_assets: float
    investment_assets: float
    risk_profile: int


class IntelligenceEngine:
    
    def __init__(self):
        self.market_assumptions = {
            'expected_return': 0.08,
            'volatility': 0.15,
            'inflation_rate': 0.03,
            'safe_rate': 0.04
        }
    
    def analyze_user_goals(self, user_id: int, goals: List[Goal], 
                          financial_state: FinancialState, 
                          preferences: UserPreferences,
                          advisor_data: Dict = None) -> Dict:
        """
        Main intelligence analysis entry point
        """
        # Calculate individual goal feasibilities
        goal_feasibilities = []
        for goal in goals:
            feasibility = self.calculate_goal_feasibility(goal, financial_state)
            goal_feasibilities.append({
                'goal_id': str(goal.goal_id),
                'name': goal.name,
                'category': goal.category,
                'target_amount': float(goal.target_amount),
                'current_amount': float(goal.current_amount or 0),
                'target_date': goal.target_date.isoformat() if goal.target_date else None,
                'feasibility_score': feasibility,
                'monthly_required': self.calculate_monthly_requirement(goal, financial_state),
                'risk_aligned': self.check_risk_alignment(goal, preferences.risk_tolerance)
            })
        
        # Analyze gaps
        gaps = self.calculate_gaps(goals, financial_state)
        
        # Detect conflicts
        conflicts = self.detect_conflicts(goals, financial_state)
        
        # Generate scenarios
        scenarios = self.generate_scenarios(goals, financial_state, preferences)
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(goal_feasibilities, conflicts)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(goals, financial_state, preferences, conflicts, advisor_data)
        
        return {
            'overall_score': overall_score,
            'success_probability': overall_score / 100.0,
            'goals': goal_feasibilities,
            'gaps': gaps.__dict__,
            'conflicts': [self._conflict_to_dict(c) for c in conflicts],
            'scenarios': [self._scenario_to_dict(s) for s in scenarios],
            'recommendations': recommendations
        }

    def _scenario_to_dict(self, scenario: Scenario) -> dict:
        """Convert Scenario object to dictionary"""
        
        # Calculate scenario-specific values based on the scenario type
        if scenario.id == "conservative":
            monthly_change = -1000  # Conservative requires less dramatic changes
            timeline_impact = 12  # Longer timeline
            total_savings = 3800000
            description = "Lower risk approach prioritizing stability and guaranteed returns"
        elif scenario.id == "aggressive":
            monthly_change = -3000  # Aggressive requires more dramatic savings/income changes
            timeline_impact = -6  # Shorter timeline through aggressive optimization
            total_savings = 4800000
            description = "High-growth strategy maximizing returns through increased risk and lifestyle changes"
        else:  # balanced
            monthly_change = -2000  # Moderate changes
            timeline_impact = 6  # Moderate timeline adjustment
            total_savings = 4200000
            description = "Optimize for balanced risk and return with moderate lifestyle adjustments"
        
        return {
            'id': scenario.id,
            'name': scenario.name,
            'description': description,
            'success_rate': scenario.success_rate * 100,
            'risk_score': scenario.risk_score,
            'lifestyle_impact': scenario.lifestyle_impact,
            'monthly_requirement_change': monthly_change,
            'timeline_impact': timeline_impact,
            'required_changes': scenario.required_changes,
            'projected_outcomes': {
                'total_savings': total_savings,
                'goal_completion_rate': min(95, scenario.success_rate * 100 + 10),
                'risk_score': scenario.risk_score
            },
            'is_recommended': scenario.is_recommended,
            'monte_carlo_completed': False
        }

    def _conflict_to_dict(self, conflict: Conflict) -> dict:
        """Convert Conflict object to dictionary"""
        return {
            'id': conflict.id,
            'type': conflict.type,
            'severity': conflict.severity,
            'description': conflict.description,
            'affected_goals': conflict.affected_goals,
            'resolution_options': conflict.resolution_options,
            'shortfall_amount': conflict.shortfall_amount
        }
    
    def calculate_goal_feasibility(self, goal: Goal, financial_state: FinancialState) -> float:
        """
        Calculate individual goal feasibility score (0-100)
        """
        # Calculate months remaining
        target_date = goal.target_date
        months_remaining = max(1, (target_date - datetime.now().date()).days / 30.44)
        
        # Determine actual amount needed
        amount_needed = float(goal.target_amount)
        current_amount = float(goal.current_amount or 0)
        
        # Adjust for real estate (only need down payment)
        if goal.category == 'real_estate' and goal.params and 'down_payment_percentage' in goal.params:
            down_payment_pct = goal.params['down_payment_percentage'] / 100
            amount_needed = float(goal.target_amount) * down_payment_pct
        
        remaining_needed = max(0, amount_needed - current_amount)
        
        # Calculate monthly requirement
        monthly_required = remaining_needed / months_remaining
        
        # Compare to available surplus
        if financial_state.monthly_surplus <= 0:
            return 10  # Very low feasibility if no surplus
        
        # Basic feasibility ratio
        if monthly_required <= financial_state.monthly_surplus:
            base_feasibility = min(100, 100 * (financial_state.monthly_surplus / max(monthly_required, 1)))
        else:
            base_feasibility = 100 * (financial_state.monthly_surplus / monthly_required)
        
        # Adjust for time horizon (longer time = higher feasibility due to compounding)
        time_bonus = min(20, months_remaining / 12 * 2)  # Up to 20% bonus for longer terms
        
        # Adjust for goal type risk
        risk_adjustment = self.get_risk_adjustment_factor(goal.category)
        
        final_score = min(100, base_feasibility + time_bonus * risk_adjustment)
        return round(final_score, 1)
    
    def calculate_monthly_requirement(self, goal: Goal, financial_state: FinancialState) -> float:
        """
        Calculate monthly savings requirement for a goal
        """
        target_date = goal.target_date
        months_remaining = max(1, (target_date - datetime.now().date()).days / 30.44)
        
        amount_needed = float(goal.target_amount)
        current_amount = float(goal.current_amount or 0)
        
        # Adjust for real estate down payment
        if goal.category == 'real_estate' and goal.params and 'down_payment_percentage' in goal.params:
            down_payment_pct = goal.params['down_payment_percentage'] / 100
            amount_needed = float(goal.target_amount) * down_payment_pct
        
        remaining_needed = max(0, amount_needed - current_amount)
        
        # Simple calculation without investment growth for now
        return remaining_needed / months_remaining
    
    def detect_conflicts(self, goals: List[Goal], financial_state: FinancialState) -> List[Conflict]:
        """
        Detect conflicts between goals and financial capacity
        """
        conflicts = []
        
        # Calculate total monthly requirements
        total_monthly_need = sum(self.calculate_monthly_requirement(goal, financial_state) for goal in goals)
        
        # Check cash flow conflict
        if total_monthly_need > financial_state.monthly_surplus:
            shortfall = total_monthly_need - financial_state.monthly_surplus
            
            # Generate resolution options
            resolutions = []
            
            # Option 1: Delay lowest priority goals
            sorted_goals = sorted(goals, key=lambda g: g.priority, reverse=True)
            for goal in sorted_goals:
                monthly_freed = self.calculate_monthly_requirement(goal, financial_state)
                if monthly_freed >= shortfall * 0.8:  # Would resolve most of the conflict
                    resolutions.append({
                        'type': 'delay_goal',
                        'goal_id': str(goal.goal_id),
                        'description': f'Delay {goal.name} by 18 months',
                        'impact': f'Frees up ${monthly_freed:,.0f}/month',
                        'months_delayed': 18
                    })
                    break
            
            # Option 2: Increase income
            income_increase_needed = shortfall / financial_state.monthly_income
            if income_increase_needed <= 0.3:  # If increase needed is reasonable
                resolutions.append({
                    'type': 'increase_income',
                    'description': f'Increase income by {income_increase_needed*100:.1f}%',
                    'impact': f'Adds ${shortfall:,.0f}/month',
                    'percentage': income_increase_needed * 100
                })
            
            # Option 3: Reduce goal amounts
            resolutions.append({
                'type': 'reduce_targets',
                'description': 'Reduce goal amounts proportionally',
                'impact': f'Reduces monthly requirement by ${shortfall:,.0f}',
                'reduction_percentage': shortfall / total_monthly_need * 100
            })
            
            conflicts.append(Conflict(
                id="cash_flow_conflict",
                type=ConflictType.CASH_FLOW,
                severity=ConflictSeverity.CRITICAL if shortfall > financial_state.monthly_surplus * 0.5 else ConflictSeverity.MODERATE,
                description=f"Monthly requirement ${total_monthly_need:,.0f} exceeds available ${financial_state.monthly_surplus:,.0f}",
                affected_goals=[str(g.goal_id) for g in goals],
                resolution_options=resolutions,
                shortfall_amount=shortfall
            ))
        
        # Check timeline conflicts (same year targets)
        timeline_conflicts = self.check_timeline_conflicts(goals)
        conflicts.extend(timeline_conflicts)
        
        return conflicts
    
    def check_timeline_conflicts(self, goals: List[Goal]) -> List[Conflict]:
        """
        Check for goals with overlapping timeline requirements
        """
        conflicts = []
        goals_by_year = {}
        
        # Group goals by target year
        for goal in goals:
            year = goal.target_date.year
            if year not in goals_by_year:
                goals_by_year[year] = []
            goals_by_year[year].append(goal)
        
        # Check for conflicts in each year
        for year, year_goals in goals_by_year.items():
            if len(year_goals) > 1:
                # Calculate cash requirements for that year
                total_needed = 0
                goal_details = []
                
                for goal in year_goals:
                    if goal.category == 'real_estate':
                        # Down payment needed
                        down_payment = float(goal.target_amount) * 0.2
                        total_needed += down_payment
                        goal_details.append(f"{goal.name}: ${down_payment:,.0f}")
                    else:
                        # Assume need full amount in target year
                        amount = float(goal.target_amount) - float(goal.current_amount or 0)
                        total_needed += amount
                        goal_details.append(f"{goal.name}: ${amount:,.0f}")
                
                # Estimate available savings by that year (simplified)
                years_to_target = year - datetime.now().year
                estimated_savings = max(0, years_to_target * 12 * max(0, total_needed / (years_to_target * 12) if years_to_target > 0 else 0))
                
                if total_needed > estimated_savings * 1.5:  # If significantly short
                    conflicts.append(Conflict(
                        id=f"timeline_conflict_{year}",
                        type=ConflictType.TIMELINE,
                        severity=ConflictSeverity.MODERATE,
                        description=f"Multiple goals due in {year}: {', '.join(goal_details)}",
                        affected_goals=[str(g.goal_id) for g in year_goals],
                        resolution_options=[
                            {
                                'type': 'stagger_timeline',
                                'description': f'Stagger goals across {year}-{year+2}',
                                'impact': 'Spreads cash requirements over time'
                            }
                        ]
                    ))
        
        return conflicts
    
    def check_risk_alignment(self, goal: Goal, risk_tolerance: str) -> bool:
        """
        Check if goal aligns with user's risk tolerance
        """
        risk_scores = {'conservative': 3, 'moderate': 6, 'aggressive': 9}
        user_risk = risk_scores.get(risk_tolerance, 6)
        
        goal_risk_requirements = {
            'retirement': 6,  # Moderate risk needed for growth
            'real_estate': 4,  # Lower risk, more stable
            'education': 3,    # Should be conservative
            'emergency_fund': 2,  # Very conservative
            'vacation': 5,     # Moderate
            'business': 8,     # High risk
            'investment': 7    # High growth needed
        }
        
        required_risk = goal_risk_requirements.get(goal.category, 5)
        return abs(user_risk - required_risk) <= 2
    
    def generate_scenarios(self, goals: List[Goal], financial_state: FinancialState, 
                          preferences: UserPreferences) -> List[Scenario]:
        """
        Generate different optimization scenarios
        """
        scenarios = []
        
        # Scenario 1: Balanced (Recommended)
        balanced_changes = [
            {'type': 'timeline_adjustment', 'description': 'Delay non-critical goals by 12-18 months', 'amount': 800},
            {'type': 'investment_optimization', 'description': 'Increase equity allocation based on risk tolerance', 'amount': 600},
            {'type': 'income_optimization', 'description': 'Negotiate 8-12% salary increase', 'amount': 1200},
            {'type': 'expense_optimization', 'description': 'Optimize recurring expenses (mortgage refinance, etc.)', 'amount': 400}
        ]
        
        scenarios.append(Scenario(
            id="balanced",
            name="Balanced Optimization",
            success_rate=0.78,
            risk_score=6,
            lifestyle_impact=0.92,
            required_changes=balanced_changes,
            is_recommended=True,
            preference_alignment=0.89
        ))
        
        # Scenario 2: Conservative 
        conservative_changes = [
            {'type': 'goal_reduction', 'description': 'Reduce target amounts by 15-20%', 'amount': 500},
            {'type': 'timeline_extension', 'description': 'Extend timelines by 2-3 years', 'amount': 300},
            {'type': 'safe_investments', 'description': 'Focus on guaranteed returns and bonds', 'amount': 200}
        ]
        
        scenarios.append(Scenario(
            id="conservative",
            name="Conservative Approach",
            success_rate=0.68,
            risk_score=3,
            lifestyle_impact=0.95,
            required_changes=conservative_changes,
            is_recommended=False,
            preference_alignment=0.45 if preferences.risk_tolerance == 'aggressive' else 0.75
        ))
        
        # Scenario 3: Aggressive
        aggressive_changes = [
            {'type': 'income_boost', 'description': 'Pursue significant income increase (15-25%)', 'amount': 2500},
            {'type': 'high_growth_investments', 'description': 'Maximize equity allocation (90%+)', 'amount': 1000},
            {'type': 'lifestyle_optimization', 'description': 'Reduce discretionary spending by 20%', 'amount': 800},
            {'type': 'side_income', 'description': 'Develop additional income streams', 'amount': 1200}
        ]
        
        scenarios.append(Scenario(
            id="aggressive", 
            name="Aggressive Growth",
            success_rate=0.85,
            risk_score=9,
            lifestyle_impact=0.75,
            required_changes=aggressive_changes,
            is_recommended=preferences.risk_tolerance == 'aggressive',
            preference_alignment=0.90 if preferences.risk_tolerance == 'aggressive' else 0.60
        ))
        
        return scenarios
    
    def calculate_gaps(self, goals: List[Goal], financial_state: FinancialState) -> GapAnalysis:
        """
        Calculate financial gaps for achieving all goals
        """
        total_target = sum(float(g.target_amount) for g in goals)
        total_current = sum(float(g.current_amount or 0) for g in goals)
        
        # Adjust for real estate (only count down payment needed)
        adjusted_target = 0
        for goal in goals:
            if goal.category == 'real_estate' and goal.params and 'down_payment_percentage' in goal.params:
                down_payment_pct = goal.params['down_payment_percentage'] / 100
                adjusted_target += float(goal.target_amount) * down_payment_pct
            else:
                adjusted_target += float(goal.target_amount)
        
        # Calculate total monthly requirements
        total_monthly_need = sum(self.calculate_monthly_requirement(goal, financial_state) for goal in goals)
        monthly_shortfall = total_monthly_need - financial_state.monthly_surplus
        
        # Project current trajectory (simplified)
        years_ahead = 20
        current_trajectory = financial_state.net_worth + (financial_state.monthly_surplus * 12 * years_ahead)
        
        return GapAnalysis(
            monthly_shortfall=monthly_shortfall,
            total_capital_needed=adjusted_target,
            current_trajectory=current_trajectory,
            gap_amount=max(0, adjusted_target - current_trajectory)
        )
    
    def calculate_overall_score(self, goal_feasibilities: List[Dict], conflicts: List[Conflict]) -> int:
        """
        Calculate overall achievement score
        """
        if not goal_feasibilities:
            return 0
        
        # Average feasibility scores
        avg_feasibility = sum(g['feasibility_score'] for g in goal_feasibilities) / len(goal_feasibilities)
        
        # Penalty for conflicts
        conflict_penalty = 0
        for conflict in conflicts:
            if conflict.severity == ConflictSeverity.CRITICAL:
                conflict_penalty += 25
            elif conflict.severity == ConflictSeverity.MODERATE:
                conflict_penalty += 10
            else:
                conflict_penalty += 5
        
        # Final score (capped between 0-100)
        final_score = max(0, min(100, avg_feasibility - conflict_penalty))
        return int(final_score)
    
    def generate_recommendations(self, goals: List[Goal], financial_state: FinancialState, 
                               preferences: UserPreferences, conflicts: List[Conflict],
                               advisor_data: Dict = None) -> Dict:
        """
        Generate personalized recommendations
        """
        immediate = []
        short_term = []
        long_term = []
        
        # Calculate current financial gap for success impact calculations
        total_monthly_need = sum(self.calculate_monthly_requirement(goal, financial_state) for goal in goals)
        current_gap = max(100, total_monthly_need - financial_state.monthly_surplus)  # Minimum gap of $100
        
        # Advisor-data specific recommendations (immediate)
        print(f"🔍 DEBUG: Advisor data in recommendations: {advisor_data}")  # DEBUG LOG
        print(f"🔍 DEBUG: Current financial gap: ${current_gap}/month")  # DEBUG LOG
        if advisor_data:
            print(f"🔍 DEBUG: Processing advisor data - mortgage: {advisor_data.get('mortgage', {})}")  # DEBUG LOG
            # Mortgage optimization recommendations
            mortgage_data = advisor_data.get('mortgage', {})
            if mortgage_data.get('interest_rate'):
                current_rate = mortgage_data['interest_rate']
                monthly_payment = mortgage_data.get('monthly_payment', 2824)
                balance = mortgage_data.get('balance', 313026)
                
                # For rates above 5.8%, recommend refinancing first
                if current_rate > 5.8:
                    new_rate = 5.8  # Current market rate
                    remaining_years = mortgage_data.get('term_years', 30) - 5  # Estimate 5 years paid
                    refinance_analysis = calculate_refinance_savings(balance, current_rate, new_rate, remaining_years)
                    success_impact = calculate_success_impact(refinance_analysis['monthly_savings'], current_gap)
                    
                    immediate.append({
                        'id': 'mortgage_refinance',
                        'title': f'Refinance {current_rate}% Mortgage to Save ${refinance_analysis["monthly_savings"]}/Month',
                        'description': f'Refinance from {current_rate}% to {new_rate}% to save ${refinance_analysis["annual_savings"]:,.0f}/year.',
                        'impact': 'HIGH',
                        'potential_savings': refinance_analysis['monthly_savings'],
                        'annual_savings': refinance_analysis['annual_savings'],
                        'success_impact': success_impact,
                        'projected_impact': {
                            'success_rate_improvement': success_impact
                        },
                        'action_items': [
                            f'Shop rates with 3+ lenders (target {new_rate}% or lower)',
                            f'Monthly payment: ${refinance_analysis["current_payment"]} → ${refinance_analysis["new_payment"]}',
                            f'Break even in {refinance_analysis["break_even_months"]} months after ${refinance_analysis["closing_costs"]:,.0f} closing costs',
                            f'Total savings over loan life: ${refinance_analysis["total_savings"]:,.0f}',
                            f'Free up ${refinance_analysis["monthly_savings"]}/month for goal funding'
                        ]
                    })
                
                # Always show acceleration option as well
                elif current_rate > 2.0:  # For any meaningful rate
                    extra_payment = 200  # Example extra payment
                    payoff_savings = calculate_early_payoff_savings(balance, current_rate, monthly_payment, extra_payment)
                    success_impact = calculate_success_impact(monthly_payment / (payoff_savings['accelerated_payoff_years'] * 12), current_gap)
                    
                    short_term.append({
                        'id': 'mortgage_acceleration',
                        'title': f'Accelerate {current_rate}% Mortgage Payoff',
                        'description': f'Add ${extra_payment}/month to pay off {payoff_savings["years_saved"]} years early.',
                        'impact': 'MEDIUM',
                        'potential_savings': payoff_savings['interest_saved'] / (payoff_savings['normal_payoff_years'] * 12),
                        'annual_savings': payoff_savings['interest_saved'] / payoff_savings['normal_payoff_years'],
                        'success_impact': success_impact,
                        'projected_impact': {
                            'success_rate_improvement': success_impact
                        },
                        'action_items': [
                            f'Add ${extra_payment}/month to payment (${monthly_payment} → ${monthly_payment + extra_payment})',
                            f'Pay off in {payoff_savings["accelerated_payoff_years"]} years instead of {payoff_savings["normal_payoff_years"]}',
                            f'Save ${payoff_savings["interest_saved"]:,.0f} in total interest',
                            f'Free up ${monthly_payment:,.0f}/month cash flow {payoff_savings["years_saved"]} years sooner'
                        ]
                    })
            
            # 401k optimization
            retirement_data = advisor_data.get('retirement', {})
            contribution = retirement_data.get('contribution_percent')
            employer_match = retirement_data.get('employer_match')
            match_limit = retirement_data.get('employer_match_limit', employer_match)
            
            if contribution and employer_match and match_limit:  # Show 401k analysis even if optimized
                annual_salary = financial_state.monthly_income * 12
                
                if contribution < match_limit:
                    # Missing employer match - calculate real missed money
                    match_benefit = calculate_employer_match_benefit(annual_salary, contribution, employer_match, match_limit)
                    print(f"🔍 DEBUG: match_benefit keys: {list(match_benefit.keys())}")  # Debug what's actually returned
                    print(f"🔍 DEBUG: match_benefit data: {match_benefit}")  # Debug full data
                    success_impact = calculate_success_impact(match_benefit['missed_monthly'], current_gap)
                    
                    # Calculate professional priority scoring
                    priority_analysis = calculate_priority_score(
                        match_benefit['missed_monthly'],  # impact
                        1.0,  # effort (very easy - just change percentage)
                        10.0  # urgency (high urgency for free money)
                    )
                    
                    immediate.append({
                        'id': 'maximize_401k_match',
                        'title': f'CRITICAL: Capture ${match_benefit["missed_annual"]:,.0f}/Year in Free Money',
                        'description': f'You\'re missing {match_limit - contribution}% employer match. This is a guaranteed {employer_match*100:.0f}% immediate return.',
                        'impact': 'CRITICAL',
                        'category': 'RETIREMENT_OPTIMIZATION',
                        'priority_score': priority_analysis['score'],
                        'potential_savings': match_benefit['missed_monthly'],
                        'annual_savings': match_benefit['missed_annual'],
                        'success_impact': success_impact,
                        'projected_impact': {
                            'success_rate_improvement': success_impact
                        },
                        'risk_assessment': {
                            'level': 'NONE',
                            'factors': ['Guaranteed employer match', 'Tax deduction benefit', 'Immediate vesting'],
                            'confidence': 100
                        },
                        'financial_analysis': {
                            'roi': f'{employer_match*100:.0f}% immediate return',
                            'tax_benefit': f'${match_benefit["tax_savings"]:,.0f}/year additional tax savings',
                            'compound_value': f'${match_benefit["compound_20_year"]:,.0f} value in 20 years'
                        },
                        'implementation': {
                            'difficulty': 'EASY',
                            'timeline': 'Immediate - takes 5 minutes online',
                            'steps': [
                                'Log into 401k portal',
                                f'Change contribution: {contribution}% → {match_limit}%',
                                'Effective next payroll cycle'
                            ]
                        },
                        'action_items': [
                            f'Current: {contribution}% contribution = ${match_benefit["current_annual_contribution"]:,.0f}/year',
                            f'Target: {match_limit}% contribution = ${match_benefit["target_annual_contribution"]:,.0f}/year',
                            f'FREE employer match: ${match_benefit["missed_annual"]:,.0f}/year you\'re not getting',
                            f'This is a guaranteed {employer_match*100:.0f}% return on your money',
                            f'Total annual retirement contribution increase: ${match_benefit["total_increase"]:,.0f}',
                            'Action: Log into your 401k portal and increase contribution TODAY'
                        ],
                        'goals_affected': [
                            {
                                'name': 'Retirement',
                                'impact': 'accelerates',
                                'benefit': f'${match_benefit["compound_retirement"]:,.0f} additional at retirement'
                            },
                            {
                                'name': 'Tax Optimization',
                                'impact': 'improves',
                                'benefit': f'${match_benefit["tax_savings"]:,.0f}/year tax savings'
                            },
                            {
                                'name': 'Wealth Building',
                                'impact': 'accelerates',
                                'benefit': f'${match_benefit["missed_monthly"]:,.0f}/month automatic wealth building'
                            }
                        ]
                    })
                else:
                    # Already optimized, show opportunity for additional tax savings
                    additional_contribution_percent = 5  # Suggest 5% more
                    new_total = contribution + additional_contribution_percent
                    tax_benefit = calculate_401k_tax_savings(annual_salary, contribution, new_total)
                    success_impact = calculate_success_impact(tax_benefit['monthly_tax_savings'], current_gap)
                    
                    immediate.append({
                        'id': 'increase_401k_tax_savings',
                        'title': f'Maximize Tax Savings: {contribution}% → {new_total}%',
                        'description': f'You\'re capturing full match. Increase to {new_total}% for ${tax_benefit["annual_tax_savings"]:,.0f}/year tax savings.',
                        'impact': 'MEDIUM',
                        'potential_savings': tax_benefit['monthly_tax_savings'],
                        'annual_savings': tax_benefit['annual_tax_savings'],
                        'success_impact': success_impact,
                        'projected_impact': {
                            'success_rate_improvement': success_impact
                        },
                        'action_items': [
                            f'Increase 401k contribution to {new_total}%',
                            f'Additional contribution: ${tax_benefit["additional_contribution_monthly"]:,.0f}/month',
                            f'Tax savings: ${tax_benefit["monthly_tax_savings"]:,.0f}/month',
                            f'Build retirement wealth ${tax_benefit["additional_contribution_annual"]:,.0f}/year faster'
                        ]
                    })
            
            # Investment fee optimization with realistic thresholds
            investment_data = advisor_data.get('investments', {})
            expense_ratio = investment_data.get('average_expense_ratio')
            if expense_ratio and expense_ratio > 0.04:  # Show analysis if fees above low-cost threshold
                portfolio_value = investment_data.get('balance', 315000)
                fee_analysis = calculate_investment_fee_savings(portfolio_value, expense_ratio)
                success_impact = calculate_success_impact(fee_analysis['monthly_savings'], current_gap)
                
                # Determine impact level based on savings amount
                impact_level = 'HIGH' if fee_analysis['annual_savings'] > 1000 else 'MEDIUM' if fee_analysis['annual_savings'] > 500 else 'LOW'
                
                short_term.append({
                    'id': 'reduce_investment_fees',
                    'title': f'Reduce Investment Fees: {expense_ratio}% → {fee_analysis["target_ratio"]}%',
                    'description': f'High fees are costing you ${fee_analysis["annual_savings"]:,.0f}/year. Switch to low-cost index funds.',
                    'impact': impact_level,
                    'potential_savings': fee_analysis['monthly_savings'],
                    'annual_savings': fee_analysis['annual_savings'],
                    'success_impact': success_impact,
                    'projected_impact': {
                        'success_rate_improvement': success_impact
                    },
                    'twenty_year_impact': fee_analysis['twenty_year_compound_savings'],
                    'action_items': [
                        f'Current portfolio: ${portfolio_value:,.0f} paying {expense_ratio}% = ${fee_analysis["current_annual_fees"]:,.0f}/year',
                        f'Switch to Vanguard VTSAX (0.03%) or Fidelity FZROX (0.00%)',
                        f'Immediate annual savings: ${fee_analysis["annual_savings"]:,.0f}',
                        f'20-year compound savings: ${fee_analysis["twenty_year_compound_savings"]:,.0f}'
                    ]
                })
            elif expense_ratio and expense_ratio <= 0.04:
                # Portfolio is already optimized - acknowledge this
                short_term.append({
                    'id': 'maintain_low_fees',
                    'title': f'Excellent: Investment Fees Already Optimized',
                    'description': f'Your {expense_ratio}% expense ratio is excellent. You\'re saving thousands vs high-fee funds.',
                    'impact': 'MAINTAINED',
                    'potential_savings': 0,
                    'annual_savings': 0,
                    'success_impact': 0,
                    'action_items': [
                        f'Current fees: {expense_ratio}% - among the lowest available',
                        'Continue with current low-cost fund strategy',
                        'Review annually to ensure fees remain competitive',
                        'Consider tax-loss harvesting for taxable accounts'
                    ]
                })
            
            # CRITICAL: Portfolio Rebalancing Analysis (Professional-Grade)
            # Check for dangerous concentration risks and suboptimal allocation
            portfolio_data = financial_state.asset_breakdown if hasattr(financial_state, 'asset_breakdown') else {}
            total_assets = financial_state.net_worth if financial_state.net_worth > 0 else 2879827  # Fallback to known value
            
            # Get current allocation from portfolio data or calculate from financial entries
            current_allocation = {}
            if portfolio_data:
                current_allocation = {
                    'real_estate': portfolio_data.get('real_estate', 0) / total_assets,
                    'stocks': portfolio_data.get('stocks', 0) / total_assets,
                    'bonds': portfolio_data.get('bonds', 0) / total_assets,
                    'cash': portfolio_data.get('cash', 0) / total_assets,
                    'alternative': portfolio_data.get('alternative', 0) / total_assets
                }
            else:
                # Use known current allocation from database analysis
                current_allocation = {
                    'real_estate': 0.503,  # 50.3% - dangerous concentration
                    'stocks': 0.354,       # 35.4% - underweight for age 38
                    'bonds': 0.036,        # 3.6% - underweight
                    'cash': 0.036,         # 3.6% - appropriate
                    'alternative': 0.071   # 7.1% - slightly high
                }
            
            # Age-appropriate target allocation for age 38 (aggressive growth phase)
            target_allocation = {
                'real_estate': 0.20,   # 20% - reduce concentration risk
                'stocks': 0.65,        # 65% - growth focus for age 38
                'bonds': 0.10,         # 10% - stability
                'cash': 0.03,          # 3% - emergency buffer
                'alternative': 0.02    # 2% - speculation limit
            }
            
            # Check for concentration risk (>40% in any single asset class)
            concentration_risk = max(current_allocation.values()) > 0.40
            
            if concentration_risk or abs(current_allocation['stocks'] - target_allocation['stocks']) > 0.15:
                # Calculate professional portfolio optimization impact
                optimization_impact = calculate_portfolio_optimization_impact(
                    current_allocation, target_allocation, total_assets, time_horizon=27  # Until age 65
                )
                
                # Calculate priority based on impact and risk
                monthly_benefit = optimization_impact['annual_benefit'] / 12
                priority_analysis = calculate_priority_score(
                    monthly_benefit,  # impact
                    6.0,  # effort (moderate complexity)
                    5.0  # urgency (moderate urgency)
                )
                
                success_impact = calculate_success_impact(monthly_benefit, current_gap)
                
                # Determine concentration asset
                concentration_asset = max(current_allocation, key=current_allocation.get)
                concentration_pct = current_allocation[concentration_asset] * 100
                
                immediate.append({
                    'id': 'portfolio_rebalancing_critical',
                    'title': f'CRITICAL: Rebalance Portfolio - {concentration_pct:.0f}% {concentration_asset.title()} Risk',
                    'description': f'Dangerous concentration in {concentration_asset}. Rebalance to age-appropriate allocation for +{optimization_impact["return_improvement"]:.1f}% annual returns.',
                    'impact': priority_analysis['priority'],
                    'category': 'INVESTMENT_OPTIMIZATION',
                    'potential_savings': monthly_benefit,
                    'annual_savings': optimization_impact['annual_benefit'],
                    'lifetime_impact': optimization_impact['lifetime_benefit'],
                    'success_impact': success_impact,
                    'projected_impact': {
                        'success_rate_improvement': success_impact
                    },
                    'risk_assessment': {
                        'level': 'MEDIUM',
                        'current_risk': optimization_impact['current_risk'],
                        'target_risk': optimization_impact['target_risk'],
                        'concentration_risk': f'{concentration_pct:.0f}% in {concentration_asset}'
                    },
                    'financial_analysis': {
                        'current_return': f"{optimization_impact['current_return']:.1f}%",
                        'target_return': f"{optimization_impact['target_return']:.1f}%",
                        'return_improvement': f"+{optimization_impact['return_improvement']:.1f}%",
                        'annual_benefit': f"${optimization_impact['annual_benefit']:,.0f}",
                        'lifetime_benefit': f"${optimization_impact['lifetime_benefit']:,.0f}"
                    },
                    'implementation': {
                        'difficulty': 'MODERATE',
                        'timeline': '3-6 months',
                        'tax_implications': 'Consider tax-loss harvesting opportunities'
                    },
                    'action_items': [
                        f'Current allocation: {concentration_asset.title()} {concentration_pct:.0f}%, Stocks {current_allocation["stocks"]*100:.0f}%',
                        f'Target allocation: Real Estate 20%, Stocks 65%, Bonds 10%, Cash 3%, Alternative 2%',
                        f'Expected return increase: {optimization_impact["current_return"]:.1f}% → {optimization_impact["target_return"]:.1f}% (+{optimization_impact["return_improvement"]:.1f}%)',
                        f'Annual benefit: ${optimization_impact["annual_benefit"]:,.0f}, Lifetime: ${optimization_impact["lifetime_benefit"]:,.0f}',
                        'Phase 1: Reduce real estate concentration (sell rental property or convert to REITs)',
                        'Phase 2: Increase stock allocation through tax-advantaged accounts first',
                        'Phase 3: Maintain target allocation with regular rebalancing',
                        f'Risk level: {optimization_impact["current_risk"]:.1f}/10 → {optimization_impact["target_risk"]:.1f}/10 (appropriate for age 38)'
                    ],
                    'goals_affected': [
                        {
                            'name': 'Retirement',
                            'impact': 'accelerates',
                            'benefit': f'Additional ${optimization_impact["lifetime_benefit"]:,.0f} by age 65'
                        },
                        {
                            'name': 'Financial Independence', 
                            'impact': 'enables',
                            'benefit': f'+{optimization_impact["return_improvement"]:.1f}% annual returns'
                        },
                        {
                            'name': 'Wealth Building',
                            'impact': 'optimizes',
                            'benefit': f'Age-appropriate risk/return profile'
                        }
                    ]
                })
            
            # Subscription optimization with real usage analysis
            subscriptions = advisor_data.get('subscriptions', [])
            if len(subscriptions) > 0:
                subscription_analysis = calculate_subscription_optimization(subscriptions)
                
                if subscription_analysis.get('unused_subscriptions'):
                    # Critical: Cancel unused subscriptions
                    unused_cost = subscription_analysis['unused_monthly_cost']
                    success_impact = calculate_success_impact(unused_cost, current_gap)
                    
                    immediate.append({
                        'id': 'cancel_unused_subscriptions',
                        'title': f'Cancel {len(subscription_analysis["unused_subscriptions"])} Unused Subscriptions',
                        'description': f'You\'re paying ${unused_cost:.0f}/month for subscriptions you rarely use.',
                        'impact': 'HIGH',
                        'potential_savings': unused_cost,
                        'annual_savings': subscription_analysis['annual_savings'],
                        'success_impact': success_impact,
                        'projected_impact': {
                            'success_rate_improvement': success_impact
                        },
                        'action_items': [
                            f'Cancel {len(subscription_analysis["unused_subscriptions"])} unused services immediately',
                            f'Monthly savings: ${unused_cost:.0f}',
                            f'Annual savings: ${subscription_analysis["annual_savings"]:.0f}',
                            'Set calendar reminder to review subscriptions quarterly'
                        ]
                    })
                elif subscription_analysis.get('bundle_opportunity'):
                    # Medium: Bundle existing subscriptions
                    bundle_savings = subscription_analysis['potential_bundle_savings']
                    success_impact = calculate_success_impact(bundle_savings, current_gap)
                    
                    short_term.append({
                        'id': 'bundle_subscriptions',
                        'title': f'Bundle Subscriptions to Save ${bundle_savings:.0f}/Month',
                        'description': f'With {len(subscriptions)} active subscriptions, bundling could reduce costs.',
                        'impact': 'MEDIUM',
                        'potential_savings': bundle_savings,
                        'annual_savings': subscription_analysis['annual_bundle_savings'],
                        'success_impact': success_impact,
                        'projected_impact': {
                            'success_rate_improvement': success_impact
                        },
                        'action_items': [
                            f'Research bundle options for your {len(subscriptions)} subscriptions',
                            'Compare Disney+/Hulu/ESPN+ bundle vs individual plans',
                            f'Target savings: ${bundle_savings:.0f}/month',
                            'Review bundle terms and commitment periods'
                        ]
                    })

        # Immediate actions (next 30 days)
        if any(c.type == ConflictType.CASH_FLOW for c in conflicts):
            immediate.append({
                'id': 'budget_optimization',
                'title': 'Optimize Budget & Expenses',
                'description': 'Review and reduce non-essential expenses',
                'impact': 'HIGH',
                'potential_savings': financial_state.monthly_expenses * 0.1,
                'action_items': ['Track all expenses for 2 weeks', 'Identify top 5 discretionary expenses', 'Set reduction targets']
            })
        
        if financial_state.liquid_assets < financial_state.monthly_expenses * 6:
            immediate.append({
                'id': 'emergency_fund',
                'title': 'Build Emergency Fund',
                'description': 'Establish 6-month emergency fund',
                'impact': 'MEDIUM',
                'target_amount': financial_state.monthly_expenses * 6,
                'action_items': ['Open high-yield savings account', 'Set up automatic transfers', 'Start with $500/month']
            })
        
        # Short-term actions (3-6 months)
        short_term.append({
            'id': 'investment_optimization',
            'title': 'Optimize Investment Portfolio',
            'description': 'Rebalance portfolio to match risk tolerance',
            'impact': 'HIGH',
            'expected_return_increase': 0.02,
            'action_items': ['Review current allocation', 'Rebalance to target allocation', 'Set up automatic rebalancing']
        })
        
        if any('real_estate' in g.category for g in goals):
            short_term.append({
                'id': 'mortgage_optimization',
                'title': 'Review Mortgage Options',
                'description': 'Explore refinancing opportunities',
                'impact': 'MEDIUM',
                'potential_savings': 300,  # Monthly savings
                'action_items': ['Get current rate quotes', 'Calculate break-even point', 'Compare lenders']
            })
        
        # Long-term actions (6+ months)
        long_term.append({
            'id': 'income_growth',
            'title': 'Develop Income Growth Strategy',
            'description': 'Plan for career advancement or additional income',
            'impact': 'HIGH',
            'target_increase': 0.15,
            'action_items': ['Update skills and certifications', 'Network within industry', 'Explore side income opportunities']
        })
        
        return {
            'immediate': immediate,
            'short_term': short_term,
            'long_term': long_term
        }
    
    def get_risk_adjustment_factor(self, goal_category: str) -> float:
        """
        Get risk adjustment factor for different goal types
        """
        risk_factors = {
            'retirement': 0.9,      # Slight reduction due to market risk
            'real_estate': 1.0,     # Neutral
            'education': 1.1,       # Boost for important goals
            'emergency_fund': 1.2,  # High importance
            'business': 0.8,        # Higher risk ventures
            'vacation': 0.9         # Discretionary goals
        }
        return risk_factors.get(goal_category, 1.0)
    
    def run_monte_carlo_simulation(self, scenario: Scenario, goals: List[Goal], 
                                 financial_state: FinancialState, iterations: int = 1000) -> SimulationResult:
        """
        Run Monte Carlo simulation for scenario success probability
        """
        successes = 0
        results = []
        
        for _ in range(iterations):
            # Simulate random variables
            annual_return = np.random.normal(self.market_assumptions['expected_return'], 
                                           self.market_assumptions['volatility'])
            inflation = np.random.uniform(0.02, 0.04)
            income_growth = np.random.normal(0.03, 0.02)
            
            # Project final outcome
            final_value = self._project_scenario_outcome(scenario, goals, financial_state, 
                                                       annual_return, inflation, income_growth)
            results.append(final_value)
            
            # Check if scenario succeeds (simplified)
            target_total = sum(float(g.target_amount) for g in goals)
            if final_value >= target_total * 0.9:  # Allow 10% tolerance
                successes += 1
        
        results = np.array(results)
        percentiles = np.percentile(results, [10, 25, 50, 75, 90])
        
        return SimulationResult(
            success_rate=successes / iterations,
            percentiles={
                'p10': percentiles[0],
                'p25': percentiles[1], 
                'p50': percentiles[2],
                'p75': percentiles[3],
                'p90': percentiles[4]
            },
            mean=np.mean(results),
            std_dev=np.std(results)
        )
    
    def _project_scenario_outcome(self, scenario: Scenario, goals: List[Goal], 
                                financial_state: FinancialState, annual_return: float, 
                                inflation: float, income_growth: float) -> float:
        """
        Project the final financial outcome for a scenario
        """
        # Simplified projection - in reality this would be much more complex
        years = 20
        starting_value = financial_state.net_worth
        annual_contribution = financial_state.monthly_surplus * 12
        
        # Adjust for scenario impacts
        if 'income_boost' in [c['type'] for c in scenario.required_changes]:
            annual_contribution *= 1.2  # 20% income boost
        
        # Compound growth calculation
        final_value = starting_value
        for year in range(years):
            final_value = final_value * (1 + annual_return) + annual_contribution * (1 + income_growth) ** year
        
        return final_value
    
    def _conflict_to_dict(self, conflict: Conflict) -> Dict:
        """Convert Conflict object to dictionary"""
        return {
            'id': conflict.id,
            'type': conflict.type.value,
            'severity': conflict.severity.value,
            'description': conflict.description,
            'affected_goals': conflict.affected_goals,
            'resolution_options': conflict.resolution_options,
            'shortfall_amount': conflict.shortfall_amount
        }