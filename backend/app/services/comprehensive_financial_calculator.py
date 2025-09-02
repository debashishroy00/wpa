"""
Comprehensive Financial Calculator
Single source of truth for ALL financial calculations
Eliminates LLM confusion by providing precise mathematical results
"""

from typing import Dict, List, Tuple, Optional, Any
from decimal import Decimal, ROUND_HALF_UP
import structlog
from datetime import datetime
import math

logger = structlog.get_logger()


class GrowthRateManager:
    """Manages growth rate defaults and assumptions"""
    
    def __init__(self):
        # Asset-specific historical returns
        self.ASSET_RETURNS = {
            'real_estate': 0.04,      # 4% property appreciation
            'stock_investments': 0.07, # 7% historical S&P 500
            'bonds': 0.03,            # 3% bond yields
            'retirement_401k': 0.06,  # 6% conservative retirement
            'bitcoin': 0.12,          # 12% volatile crypto
            'cash': 0.01,             # 1% savings account
            'investment_accounts': 0.07, # 7% diversified investing
            'alternative': 0.08       # 8% alternative investments
        }
        
        # Goal-specific defaults
        self.GOAL_DEFAULTS = {
            'retirement_planning': {
                'conservative': 0.05,
                'moderate': 0.06,
                'aggressive': 0.08
            },
            'short_term_goals': {
                'emergency_fund': 0.02,
                'house_down_payment': 0.04,
                'college_savings': 0.06
            },
            'debt_analysis': {
                'investment_vs_payoff': 0.07,
                'refinancing': 0.04
            }
        }
    
    def get_appropriate_rate(self, calculation_type: str, user_context: Dict, 
                           user_specified_rate: Optional[float] = None) -> Dict[str, Any]:
        """Get appropriate growth rate with full transparency"""
        
        if user_specified_rate is not None:
            return {
                'rate': user_specified_rate,
                'source': 'user_specified',
                'explanation': f"Using your specified {user_specified_rate:.1%} growth rate",
                'confidence': 'high',
                'assumptions': [f"User-specified rate: {user_specified_rate:.1%}"]
            }
        
        # Try portfolio-weighted rate first
        portfolio_rate = self._calculate_portfolio_weighted_rate(user_context)
        if portfolio_rate['rate'] > 0:
            return portfolio_rate
        
        # Fall back to risk profile default
        return self._get_risk_profile_default(user_context, calculation_type)
    
    def _calculate_portfolio_weighted_rate(self, user_context: Dict) -> Dict[str, Any]:
        """Calculate blended rate based on user's actual asset allocation"""
        
        assets = user_context.get('assets_breakdown', {})
        if not assets:
            return {'rate': 0, 'source': 'no_data'}
        
        total_assets = sum(assets.values())
        if total_assets == 0:
            return {'rate': 0, 'source': 'no_assets'}
        
        weighted_rate = 0
        breakdown = {}
        assumptions_list = []
        
        for asset_category, amount in assets.items():
            weight = amount / total_assets
            asset_key = self._map_asset_category(asset_category)
            asset_rate = self.ASSET_RETURNS.get(asset_key, 0.06)
            
            weighted_rate += weight * asset_rate
            breakdown[asset_category] = {
                'amount': amount,
                'weight': weight,
                'assumed_rate': asset_rate,
                'contribution': weight * asset_rate
            }
            assumptions_list.append(f"{asset_category}: {asset_rate:.1%}")
        
        return {
            'rate': weighted_rate,
            'source': 'portfolio_weighted',
            'explanation': f"Using {weighted_rate:.1%} blended rate based on your portfolio allocation",
            'confidence': 'high',
            'breakdown': breakdown,
            'assumptions': assumptions_list
        }
    
    def _map_asset_category(self, category: str) -> str:
        """Map user asset categories to our return assumptions"""
        category_lower = category.lower()
        
        mapping = {
            'real estate': 'real_estate',
            'house': 'real_estate',
            'home': 'real_estate',
            'property': 'real_estate',
            'investments': 'stock_investments',
            'investment': 'stock_investments',
            'stocks': 'stock_investments',
            'retirement': 'retirement_401k',
            '401k': 'retirement_401k',
            'ira': 'retirement_401k',
            'bitcoin': 'bitcoin',
            'crypto': 'bitcoin',
            'cash': 'cash',
            'savings': 'cash',
            'alternative': 'alternative',
            'other': 'stock_investments'  # Default unknown to stock returns
        }
        
        for key, value in mapping.items():
            if key in category_lower:
                return value
        
        return 'stock_investments'  # Default fallback
    
    def _get_risk_profile_default(self, user_context: Dict, calculation_type: str) -> Dict[str, Any]:
        """Get default based on user risk profile"""
        
        age = user_context.get('age') or user_context.get('_context', {}).get('age', 50)
        net_worth = user_context.get('net_worth', 0)
        
        # Age-based risk assessment
        if age < 40:
            risk_level = 'aggressive'
        elif age < 55:
            risk_level = 'moderate'
        else:
            risk_level = 'conservative'
        
        # Wealth adjustment (higher net worth = can take more risk)
        if net_worth > 2000000 and risk_level != 'aggressive':
            if risk_level == 'conservative':
                risk_level = 'moderate'
            elif risk_level == 'moderate':
                risk_level = 'aggressive'
        
        # Get rate for calculation type and risk level
        goal_category = 'retirement_planning'  # Default
        if 'emergency' in calculation_type.lower() or 'cash' in calculation_type.lower():
            goal_category = 'short_term_goals'
        elif 'debt' in calculation_type.lower() or 'payoff' in calculation_type.lower():
            goal_category = 'debt_analysis'
        
        rate = self.GOAL_DEFAULTS[goal_category].get(risk_level, 0.06)
        
        return {
            'rate': rate,
            'source': 'risk_profile',
            'explanation': f"Using {risk_level} {rate:.1%} rate based on your age ({age}) and financial profile",
            'confidence': 'medium',
            'risk_level': risk_level,
            'assumptions': [
                f"Age: {age} → {risk_level} risk profile",
                f"Net worth: ${net_worth:,.0f}",
                f"{goal_category} default: {rate:.1%}"
            ]
        }
    
    def assess_growth_sensitivity(self, calculation_func, params: Dict, base_rate: float = 0.07) -> Dict[str, Any]:
        """Assess how sensitive results are to growth rate assumptions"""
        
        try:
            # Test with ±2% from base rate
            low_rate = base_rate - 0.02
            high_rate = base_rate + 0.02
            
            base_result = calculation_func(**params, growth_rate=base_rate)
            low_result = calculation_func(**params, growth_rate=low_rate)
            high_result = calculation_func(**params, growth_rate=high_rate)
            
            # Calculate variance in key metric (usually years or amount)
            if 'years' in base_result:
                variance = high_result['years'] - low_result['years']
                metric = 'years'
            elif 'amount' in base_result:
                variance = abs(high_result['amount'] - low_result['amount'])
                metric = 'amount'
            else:
                return {'sensitivity': 'unknown', 'show_ranges': False}
            
            if metric == 'years':
                if variance > 5:
                    sensitivity = 'high'
                elif variance > 2:
                    sensitivity = 'medium'
                else:
                    sensitivity = 'low'
            else:  # amount
                if variance > base_result[metric] * 0.2:  # >20% change
                    sensitivity = 'high'
                elif variance > base_result[metric] * 0.1:  # >10% change
                    sensitivity = 'medium'
                else:
                    sensitivity = 'low'
            
            return {
                'sensitivity': sensitivity,
                'show_ranges': sensitivity in ['high', 'medium'],
                'variance': variance,
                'metric': metric,
                'scenarios': {
                    'conservative': {f'{metric}': low_result[metric], 'rate': low_rate},
                    'moderate': {f'{metric}': base_result[metric], 'rate': base_rate},
                    'optimistic': {f'{metric}': high_result[metric], 'rate': high_rate}
                }
            }
            
        except Exception as e:
            logger.warning(f"Growth sensitivity assessment failed: {e}")
            return {'sensitivity': 'unknown', 'show_ranges': False}


class RetirementCalculations:
    """All retirement-related calculations"""
    
    @staticmethod
    def years_to_goal(current_assets: float, target_goal: float, growth_rate: float, 
                     monthly_additions: float = 0) -> Dict[str, Any]:
        """Calculate years needed to reach retirement goal"""
        
        if current_assets >= target_goal:
            return {
                'years': 0,
                'already_achieved': True,
                'surplus': current_assets - target_goal,
                'message': f"Goal already achieved! You have ${current_assets:,.0f} vs goal of ${target_goal:,.0f}"
            }
        
        # Need to solve: target = current * (1 + r)^t + monthly * [((1+r)^t - 1) / r]
        # This requires iterative solution
        annual_additions = monthly_additions * 12
        
        if growth_rate == 0:
            # Simple case: no growth
            years = (target_goal - current_assets) / annual_additions if annual_additions > 0 else float('inf')
        else:
            # Use iterative approach to solve compound growth equation
            years = 0
            projected_assets = current_assets
            
            while projected_assets < target_goal and years < 50:  # Max 50 years
                projected_assets = projected_assets * (1 + growth_rate) + annual_additions
                years += 1
            
            if years >= 50:
                years = float('inf')
        
        return {
            'years': years,
            'already_achieved': False,
            'final_amount': projected_assets if years < 50 else target_goal,
            'total_contributions': annual_additions * years if years < 50 else 0,
            'growth_component': (projected_assets - current_assets - annual_additions * years) if years < 50 else 0
        }
    
    @staticmethod
    def goal_adjustment_impact(current_assets: float, original_goal: float, new_goal: float,
                              growth_rate: float, monthly_additions: float = 0) -> Dict[str, Any]:
        """Calculate impact of changing retirement goal"""
        
        original_timeline = RetirementCalculations.years_to_goal(
            current_assets, original_goal, growth_rate, monthly_additions
        )
        
        new_timeline = RetirementCalculations.years_to_goal(
            current_assets, new_goal, growth_rate, monthly_additions
        )
        
        years_saved = original_timeline['years'] - new_timeline['years']
        goal_reduction = original_goal - new_goal
        
        return {
            'original_goal': original_goal,
            'new_goal': new_goal,
            'goal_reduction': goal_reduction,
            'goal_reduction_percent': (goal_reduction / original_goal) * 100,
            'original_years': original_timeline['years'],
            'new_years': new_timeline['years'],
            'years_saved': years_saved,
            'timeline_reduction_percent': (years_saved / original_timeline['years']) * 100 if original_timeline['years'] > 0 else 0,
            'message': f"Reducing goal by ${goal_reduction:,.0f} ({goal_reduction/original_goal:.1%}) saves {years_saved:.1f} years"
        }
    
    @staticmethod
    def required_monthly_savings(current_assets: float, target_goal: float, years: int,
                                growth_rate: float) -> Dict[str, Any]:
        """Calculate monthly savings needed to reach goal in specified years"""
        
        if years <= 0:
            return {'monthly_needed': float('inf'), 'error': 'Invalid timeframe'}
        
        if current_assets >= target_goal:
            return {'monthly_needed': 0, 'already_achieved': True}
        
        # Future value of current assets
        fv_current = current_assets * (1 + growth_rate) ** years
        
        # Amount still needed after growth
        amount_needed = target_goal - fv_current
        
        if amount_needed <= 0:
            return {'monthly_needed': 0, 'growth_sufficient': True}
        
        # Monthly payment for annuity formula
        if growth_rate == 0:
            monthly_needed = amount_needed / (years * 12)
        else:
            monthly_rate = growth_rate / 12
            months = years * 12
            # PMT = FV * r / ((1+r)^n - 1)
            monthly_needed = amount_needed * monthly_rate / ((1 + monthly_rate) ** months - 1)
        
        return {
            'monthly_needed': monthly_needed,
            'annual_needed': monthly_needed * 12,
            'total_contributions': monthly_needed * 12 * years,
            'current_assets_future_value': fv_current,
            'growth_from_current': fv_current - current_assets,
            'growth_from_contributions': amount_needed
        }
    
    @staticmethod
    def withdrawal_sustainability(assets: float, annual_withdrawal: float, 
                                 years_needed: int = 30, growth_rate: float = 0.06) -> Dict[str, Any]:
        """Analyze withdrawal rate sustainability"""
        
        withdrawal_rate = annual_withdrawal / assets if assets > 0 else float('inf')
        
        # Test if portfolio can sustain withdrawals
        remaining_assets = assets
        sustainable = True
        years_sustained = 0
        
        for year in range(years_needed):
            if remaining_assets <= 0:
                sustainable = False
                break
            
            # Withdraw at beginning of year
            remaining_assets -= annual_withdrawal
            
            # Apply growth to remaining assets
            if remaining_assets > 0:
                remaining_assets *= (1 + growth_rate)
            
            years_sustained += 1
        
        return {
            'withdrawal_rate': withdrawal_rate,
            'is_sustainable': sustainable,
            'years_sustained': years_sustained,
            'remaining_assets': max(0, remaining_assets),
            'safe_withdrawal_rate': 0.04,  # 4% rule
            'recommended_annual': assets * 0.04,
            'excess_risk': withdrawal_rate - 0.04 if withdrawal_rate > 0.04 else 0
        }


class TaxCalculations:
    """Tax optimization calculations"""
    
    def __init__(self):
        # 2024 tax brackets
        self.FEDERAL_BRACKETS_MARRIED = [
            (22000, 0.10),
            (89450, 0.12),
            (190750, 0.22),
            (364200, 0.24),
            (462500, 0.32),
            (693750, 0.35),
            (float('inf'), 0.37)
        ]
        
        self.STATE_RATES = {
            'NC': 0.0525, 'CA': 0.093, 'TX': 0.0, 'FL': 0.0,
            'NY': 0.0685, 'NJ': 0.0637, 'VA': 0.0575
        }
        
        self.RETIREMENT_LIMITS_2024 = {
            'under_50': {'401k': 23000, 'ira': 7000},
            '50_plus': {'401k': 30500, 'ira': 8000}
        }
    
    def marginal_tax_analysis(self, income: float, state: str = 'NC', 
                             filing_status: str = 'married') -> Dict[str, Any]:
        """Calculate marginal and effective tax rates"""
        
        # Federal marginal rate
        federal_marginal = self._get_marginal_rate(income)
        
        # State rate
        state_rate = self.STATE_RATES.get(state, 0.05)
        
        # Combined marginal
        combined_marginal = federal_marginal + state_rate
        
        # Effective rates
        federal_tax = self._calculate_federal_tax(income)
        federal_effective = federal_tax / income if income > 0 else 0
        
        state_tax = income * state_rate
        combined_effective = (federal_tax + state_tax) / income if income > 0 else 0
        
        return {
            'marginal_rates': {
                'federal': federal_marginal,
                'state': state_rate,
                'combined': combined_marginal
            },
            'effective_rates': {
                'federal': federal_effective,
                'combined': combined_effective
            },
            'tax_amounts': {
                'federal': federal_tax,
                'state': state_tax,
                'total': federal_tax + state_tax
            }
        }
    
    def retirement_contribution_optimization(self, salary: float, current_401k: float,
                                           age: int = 54) -> Dict[str, Any]:
        """Optimize 401k contributions for tax savings"""
        
        limit_category = '50_plus' if age >= 50 else 'under_50'
        max_401k = self.RETIREMENT_LIMITS_2024[limit_category]['401k']
        
        # Current tax savings
        current_tax_savings = current_401k * self._get_marginal_rate(salary)
        
        # Potential additional contribution
        additional_possible = max_401k - current_401k
        
        # Tax savings from maxing out
        additional_tax_savings = additional_possible * self._get_marginal_rate(salary - current_401k)
        
        return {
            'current_contribution': current_401k,
            'current_tax_savings': current_tax_savings,
            'max_allowed': max_401k,
            'additional_possible': additional_possible,
            'additional_tax_savings': additional_tax_savings,
            'total_tax_savings_if_maxed': current_tax_savings + additional_tax_savings,
            'recommendation': 'increase' if additional_possible > 0 else 'optimized'
        }
    
    def _get_marginal_rate(self, income: float) -> float:
        """Get federal marginal tax rate"""
        for threshold, rate in self.FEDERAL_BRACKETS_MARRIED:
            if income <= threshold:
                return rate
        return 0.37  # Highest bracket
    
    def _calculate_federal_tax(self, income: float) -> float:
        """Calculate total federal tax owed"""
        tax = 0
        previous_threshold = 0
        
        for threshold, rate in self.FEDERAL_BRACKETS_MARRIED:
            if income <= threshold:
                tax += (income - previous_threshold) * rate
                break
            else:
                tax += (threshold - previous_threshold) * rate
                previous_threshold = threshold
        
        return tax


class CashFlowCalculations:
    """Cash flow and budget calculations"""
    
    @staticmethod
    def emergency_fund_analysis(current_fund: float, monthly_expenses: float,
                               target_months: int = 6) -> Dict[str, Any]:
        """Analyze emergency fund adequacy"""
        
        target_amount = monthly_expenses * target_months
        current_months = current_fund / monthly_expenses if monthly_expenses > 0 else 0
        
        return {
            'current_fund': current_fund,
            'monthly_expenses': monthly_expenses,
            'target_months': target_months,
            'target_amount': target_amount,
            'current_months_covered': current_months,
            'surplus_deficit': current_fund - target_amount,
            'is_adequate': current_fund >= target_amount,
            'status': 'adequate' if current_fund >= target_amount else 'needs_funding'
        }
    
    @staticmethod
    def savings_rate_optimization(monthly_income: float, monthly_expenses: float) -> Dict[str, Any]:
        """Calculate current and potential savings rates"""
        
        current_surplus = monthly_income - monthly_expenses
        current_savings_rate = current_surplus / monthly_income if monthly_income > 0 else 0
        
        # Analyze expense categories for optimization potential
        potential_reductions = {
            'discretionary_10_percent': monthly_expenses * 0.1,
            'discretionary_20_percent': monthly_expenses * 0.2,
            'aggressive_30_percent': monthly_expenses * 0.3
        }
        
        optimized_scenarios = {}
        for scenario, reduction in potential_reductions.items():
            new_expenses = monthly_expenses - reduction
            new_surplus = monthly_income - new_expenses
            new_savings_rate = new_surplus / monthly_income
            
            optimized_scenarios[scenario] = {
                'new_expenses': new_expenses,
                'new_surplus': new_surplus,
                'new_savings_rate': new_savings_rate,
                'additional_savings': reduction
            }
        
        return {
            'current': {
                'monthly_surplus': current_surplus,
                'savings_rate': current_savings_rate,
                'annual_surplus': current_surplus * 12
            },
            'optimization_scenarios': optimized_scenarios
        }


class InvestmentCalculations:
    """Investment and portfolio calculations"""
    
    @staticmethod
    def compound_growth_scenarios(principal: float, rates: List[float], 
                                 years: int, monthly_contributions: float = 0) -> Dict[str, Any]:
        """Calculate compound growth for multiple rate scenarios"""
        
        scenarios = {}
        
        for rate in rates:
            annual_contributions = monthly_contributions * 12
            
            if rate == 0:
                # Simple case: no growth
                final_value = principal + (annual_contributions * years)
                growth = annual_contributions * years
            else:
                # Compound growth with regular contributions
                # FV = PV(1+r)^n + PMT[((1+r)^n - 1) / r]
                pv_growth = principal * (1 + rate) ** years
                
                if annual_contributions > 0:
                    annuity_fv = annual_contributions * (((1 + rate) ** years - 1) / rate)
                else:
                    annuity_fv = 0
                
                final_value = pv_growth + annuity_fv
                growth = final_value - principal - (annual_contributions * years)
            
            scenarios[f'{rate:.1%}'] = {
                'rate': rate,
                'final_value': final_value,
                'total_contributions': annual_contributions * years,
                'growth_from_principal': pv_growth - principal if rate > 0 else 0,
                'growth_from_contributions': annuity_fv if rate > 0 else 0,
                'total_growth': growth
            }
        
        return {
            'principal': principal,
            'years': years,
            'monthly_contributions': monthly_contributions,
            'scenarios': scenarios
        }
    
    @staticmethod
    def asset_allocation_analysis(current_allocation: Dict[str, float],
                                 target_allocation: Dict[str, float]) -> Dict[str, Any]:
        """Analyze current vs target asset allocation"""
        
        total_current = sum(current_allocation.values())
        rebalancing_needed = {}
        
        for asset, target_amount in target_allocation.items():
            current_amount = current_allocation.get(asset, 0)
            difference = target_amount - current_amount
            percentage_diff = difference / total_current if total_current > 0 else 0
            
            rebalancing_needed[asset] = {
                'current': current_amount,
                'target': target_amount,
                'difference': difference,
                'percentage_difference': percentage_diff,
                'action': 'buy' if difference > 0 else 'sell' if difference < 0 else 'hold'
            }
        
        total_rebalancing = sum(abs(item['difference']) for item in rebalancing_needed.values()) / 2
        
        return {
            'current_allocation': current_allocation,
            'target_allocation': target_allocation,
            'rebalancing_needed': rebalancing_needed,
            'total_rebalancing_amount': total_rebalancing,
            'rebalancing_percentage': total_rebalancing / total_current if total_current > 0 else 0
        }


class ComprehensiveFinancialCalculator:
    """
    Master financial calculator - single source of truth for all calculations
    Eliminates LLM mathematical confusion
    """
    
    def __init__(self):
        self.growth_manager = GrowthRateManager()
        self.retirement = RetirementCalculations()
        self.tax = TaxCalculations()
        self.cash_flow = CashFlowCalculations()
        self.investments = InvestmentCalculations()
        
        logger.info("ComprehensiveFinancialCalculator initialized")
    
    def calculate_with_assumptions(self, calculation_type: str, user_context: Dict,
                                 calculation_params: Dict) -> Dict[str, Any]:
        """
        Main entry point - handles growth rate assumptions and routes calculations
        """
        
        # Extract user-specified growth rate if provided
        user_rate = calculation_params.pop('growth_rate', None)
        
        # Get appropriate growth rate with full transparency
        rate_info = self.growth_manager.get_appropriate_rate(
            calculation_type, user_context, user_rate
        )
        
        # Add growth rate to calculation parameters
        calculation_params['growth_rate'] = rate_info['rate']
        
        # Route to appropriate calculation method
        try:
            if calculation_type == 'years_to_retirement_goal':
                result = self.retirement.years_to_goal(**calculation_params)
                
            elif calculation_type == 'retirement_goal_adjustment':
                result = self.retirement.goal_adjustment_impact(**calculation_params)
                
            elif calculation_type == 'required_monthly_savings':
                result = self.retirement.required_monthly_savings(**calculation_params)
                
            elif calculation_type == 'withdrawal_sustainability':
                result = self.retirement.withdrawal_sustainability(**calculation_params)
                
            elif calculation_type == 'tax_analysis':
                result = self.tax.marginal_tax_analysis(**calculation_params)
                
            elif calculation_type == 'retirement_contribution_optimization':
                result = self.tax.retirement_contribution_optimization(**calculation_params)
                
            elif calculation_type == 'emergency_fund_analysis':
                result = self.cash_flow.emergency_fund_analysis(**calculation_params)
                
            elif calculation_type == 'savings_rate_optimization':
                result = self.cash_flow.savings_rate_optimization(**calculation_params)
                
            elif calculation_type == 'compound_growth_scenarios':
                result = self.investments.compound_growth_scenarios(**calculation_params)
                
            elif calculation_type == 'asset_allocation_analysis':
                result = self.investments.asset_allocation_analysis(**calculation_params)
                
            else:
                raise ValueError(f"Unknown calculation type: {calculation_type}")
            
            # Add assumption information to result
            result['assumptions'] = rate_info
            
            # Assess growth rate sensitivity if applicable
            if 'growth_rate' in calculation_params and calculation_type in [
                'years_to_retirement_goal', 'retirement_goal_adjustment', 'required_monthly_savings'
            ]:
                # Map calculation types to actual method names
                method_mapping = {
                    'years_to_retirement_goal': 'years_to_goal',
                    'retirement_goal_adjustment': 'goal_adjustment_impact',
                    'required_monthly_savings': 'required_monthly_savings'
                }
                
                method_name = method_mapping.get(calculation_type)
                if method_name and hasattr(self.retirement, method_name):
                    calc_method = getattr(self.retirement, method_name)
                    sensitivity = self.growth_manager.assess_growth_sensitivity(
                        calc_method, calculation_params, rate_info['rate']
                    )
                    result['sensitivity'] = sensitivity
            
            result['calculation_type'] = calculation_type
            result['success'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Calculation failed: {calculation_type}, error: {e}")
            return {
                'success': False,
                'error': str(e),
                'calculation_type': calculation_type,
                'assumptions': rate_info
            }


# Global instance
comprehensive_calculator = ComprehensiveFinancialCalculator()