"""
Step 4: Deterministic Plan Engine Service
Core calculation engine with no subjective language
"""
# import numpy as np # DISABLED FOR DEPLOYMENT
from app.services.ml_fallbacks import numpy_fallback as np
from typing import Dict, List, Tuple, Optional
from decimal import Decimal
from datetime import datetime
import json

from app.models.plan_engine import (
    PlanInput, PlanOutput, GapAnalysis, TargetAllocation,
    RebalancingTrade, ContributionSchedule, DebtAction,
    PlanMetrics, TaxStrategy
)


class DeterministicPlanEngine:
    """Pure calculation engine for financial planning"""
    
    def __init__(self):
        self.historical_returns = {
            'us_stocks': {'mean': 0.10, 'std': 0.16},
            'intl_stocks': {'mean': 0.08, 'std': 0.18},
            'bonds': {'mean': 0.04, 'std': 0.05},
            'reits': {'mean': 0.08, 'std': 0.19},
            'cash': {'mean': 0.02, 'std': 0.01},
            'commodities': {'mean': 0.05, 'std': 0.20},
            'crypto': {'mean': 0.15, 'std': 0.60}
        }
        
        self.contribution_limits = {
            '401k': 23000,
            '401k_catch_up': 7500,
            'ira': 7000,
            'ira_catch_up': 1000,
            'hsa_individual': 4150,
            'hsa_family': 8300,
            'hsa_catch_up': 1000
        }
    
    def calculate_plan(self, input_data: PlanInput) -> PlanOutput:
        """Main calculation entry point"""
        
        # 1. Gap Analysis with Monte Carlo
        gap_analysis = self._calculate_gap_analysis(input_data)
        
        # 2. Target Allocation based on risk and time horizon
        target_allocation = self._calculate_target_allocation(input_data)
        
        # 3. Rebalancing trades to reach target
        rebalancing_trades = self._calculate_rebalancing_trades(
            input_data, target_allocation
        )
        
        # 4. Contribution optimization
        contribution_schedule = self._optimize_contributions(input_data)
        
        # 5. Debt prioritization
        debt_schedule = self._prioritize_debt(input_data)
        
        # 6. Calculate plan metrics
        plan_metrics = self._calculate_metrics(
            input_data, target_allocation, contribution_schedule
        )
        
        # 7. Tax optimization (optional)
        tax_strategy = self._optimize_taxes(input_data) if input_data.constraints.tax_bracket > 0 else None
        
        return PlanOutput(
            gap_analysis=gap_analysis,
            target_allocation=target_allocation,
            rebalancing_trades=rebalancing_trades,
            contribution_schedule=contribution_schedule,
            debt_schedule=debt_schedule,
            plan_metrics=plan_metrics,
            tax_strategy=tax_strategy,
            calculation_timestamp=datetime.utcnow().isoformat(),
            calculation_version="1.0.0"
        )
    
    def _calculate_gap_analysis(self, input_data: PlanInput) -> GapAnalysis:
        """Calculate gap and run Monte Carlo simulation"""
        current = input_data.current_state.net_worth
        target = input_data.goals.target_net_worth
        years = input_data.goals.retirement_age - (input_data.goals.current_age or 40)
        
        # Monte Carlo simulation
        success_rate, percentiles = self._run_monte_carlo(
            current_value=float(current),
            target_value=float(target),
            years=years,
            monthly_contribution=self._estimate_monthly_contribution(input_data),
            current_allocation=input_data.current_state.current_allocation
        )
        
        return GapAnalysis(
            target_amount=target,
            current_amount=current,
            gap=target - current,
            time_horizon_years=years,
            monte_carlo_success_rate=success_rate,
            percentile_95_amount=Decimal(str(percentiles[95])),
            percentile_50_amount=Decimal(str(percentiles[50])),
            percentile_5_amount=Decimal(str(percentiles[5]))
        )
    
    def _run_monte_carlo(
        self, 
        current_value: float,
        target_value: float,
        years: int,
        monthly_contribution: float,
        current_allocation: Dict[str, float],
        simulations: int = 10000
    ) -> Tuple[float, Dict[int, float]]:
        """Run Monte Carlo simulation for success probability"""
        
        # Map allocation to asset classes
        portfolio_return, portfolio_std = self._get_portfolio_stats(current_allocation)
        
        # Run simulations
        final_values = []
        for _ in range(simulations):
            value = current_value
            for year in range(years):
                # Annual return with randomness
                annual_return = np.random.normal(portfolio_return, portfolio_std)
                value = value * (1 + annual_return) + (monthly_contribution * 12)
            final_values.append(value)
        
        # Calculate success rate
        successes = sum(1 for v in final_values if v >= target_value)
        success_rate = successes / simulations
        
        # Calculate percentiles
        percentiles = {
            5: np.percentile(final_values, 5),
            50: np.percentile(final_values, 50),
            95: np.percentile(final_values, 95)
        }
        
        return success_rate, percentiles
    
    def _get_portfolio_stats(self, allocation: Dict[str, float]) -> Tuple[float, float]:
        """Calculate portfolio expected return and standard deviation"""
        if not allocation:
            # Default balanced portfolio
            allocation = {
                'us_stocks': 0.4,
                'intl_stocks': 0.2,
                'bonds': 0.3,
                'reits': 0.05,
                'cash': 0.05
            }
        
        portfolio_return = 0
        portfolio_variance = 0
        
        for asset, weight in allocation.items():
            if asset in self.historical_returns:
                stats = self.historical_returns[asset]
                portfolio_return += weight * stats['mean']
                portfolio_variance += (weight ** 2) * (stats['std'] ** 2)
        
        portfolio_std = np.sqrt(portfolio_variance)
        return portfolio_return, portfolio_std
    
    def _calculate_target_allocation(self, input_data: PlanInput) -> TargetAllocation:
        """Calculate optimal allocation based on risk and time horizon"""
        risk_tolerance = input_data.goals.risk_tolerance
        years_to_retirement = input_data.goals.retirement_age - (input_data.goals.current_age or 40)
        
        # Glidepath: more conservative as approaching retirement
        equity_pct = min(0.9, max(0.3, (100 - input_data.goals.current_age or 40) / 100))
        
        # Adjust for risk tolerance (1-10 scale)
        risk_adjustment = (risk_tolerance - 5) * 0.05
        equity_pct = min(0.95, max(0.2, equity_pct + risk_adjustment))
        
        # Allocation based on equity percentage
        us_stocks = equity_pct * 0.6
        intl_stocks = equity_pct * 0.3
        reits = equity_pct * 0.1
        
        bonds = (1 - equity_pct) * 0.8
        cash = (1 - equity_pct) * 0.2
        
        return TargetAllocation(
            us_stocks=round(us_stocks, 3),
            intl_stocks=round(intl_stocks, 3),
            bonds=round(bonds, 3),
            reits=round(reits, 3),
            cash=round(cash, 3),
            commodities=0,
            crypto=0
        )
    
    def _calculate_rebalancing_trades(
        self, 
        input_data: PlanInput,
        target_allocation: TargetAllocation
    ) -> List[RebalancingTrade]:
        """Calculate trades needed to reach target allocation"""
        trades = []
        total_value = float(sum(input_data.current_state.assets.values()))
        
        # Map current holdings to target categories
        current_by_category = self._map_current_holdings(input_data.current_state.assets)
        
        # Calculate target values
        target_values = {
            'us_stocks': total_value * target_allocation.us_stocks,
            'intl_stocks': total_value * target_allocation.intl_stocks,
            'bonds': total_value * target_allocation.bonds,
            'reits': total_value * target_allocation.reits,
            'cash': total_value * target_allocation.cash
        }
        
        # Generate trades (simplified - would need account mapping)
        etf_map = {
            'us_stocks': 'VTI',
            'intl_stocks': 'VTIAX',
            'bonds': 'BND',
            'reits': 'VNQ',
            'cash': 'VMFXX'
        }
        
        for category, target_value in target_values.items():
            current_value = current_by_category.get(category, 0)
            diff = target_value - current_value
            
            if abs(diff) > 100:  # Only rebalance if difference > $100
                trades.append(RebalancingTrade(
                    action='buy' if diff > 0 else 'sell',
                    symbol=etf_map[category],
                    amount=Decimal(str(abs(diff))),
                    account='taxable',
                    tax_impact=Decimal('0') if diff > 0 else Decimal(str(abs(diff) * 0.15))
                ))
        
        return trades
    
    def _map_current_holdings(self, assets: Dict[str, Decimal]) -> Dict[str, float]:
        """Map current holdings to asset categories"""
        # Simplified mapping - would need more sophisticated logic
        mapped = {
            'us_stocks': 0,
            'intl_stocks': 0,
            'bonds': 0,
            'reits': 0,
            'cash': 0
        }
        
        for asset_name, value in assets.items():
            value_float = float(value)
            if 'stock' in asset_name.lower() or '401k' in asset_name.lower():
                mapped['us_stocks'] += value_float * 0.6
                mapped['intl_stocks'] += value_float * 0.2
                mapped['bonds'] += value_float * 0.2
            elif 'bond' in asset_name.lower():
                mapped['bonds'] += value_float
            elif 'cash' in asset_name.lower() or 'savings' in asset_name.lower():
                mapped['cash'] += value_float
            elif 'real' in asset_name.lower() or 'reit' in asset_name.lower():
                mapped['reits'] += value_float
            else:
                # Default balanced allocation
                mapped['us_stocks'] += value_float * 0.4
                mapped['bonds'] += value_float * 0.3
                mapped['cash'] += value_float * 0.1
        
        return mapped
    
    def _optimize_contributions(self, input_data: PlanInput) -> ContributionSchedule:
        """Optimize contribution schedule for tax efficiency"""
        annual_income = float(sum(input_data.current_state.income.values()))
        monthly_expenses = float(sum(input_data.current_state.expenses.values()))
        monthly_income = annual_income / 12
        available_monthly = monthly_income - monthly_expenses
        
        # Calculate optimal 401k percentage (max out if possible)
        max_401k = self.contribution_limits['401k']
        if input_data.goals.current_age and input_data.goals.current_age >= 50:
            max_401k += self.contribution_limits['401k_catch_up']
        
        optimal_401k_pct = min(0.5, max_401k / annual_income if annual_income > 0 else 0)
        annual_401k = annual_income * optimal_401k_pct
        
        # Roth IRA
        max_ira = self.contribution_limits['ira']
        if input_data.goals.current_age and input_data.goals.current_age >= 50:
            max_ira += self.contribution_limits['ira_catch_up']
        
        # HSA if eligible (assume family)
        hsa_annual = Decimal(str(self.contribution_limits['hsa_family']))
        
        # Remaining goes to taxable
        total_tax_advantaged = annual_401k + max_ira + float(hsa_annual)
        remaining_annual = max(0, available_monthly * 12 - total_tax_advantaged)
        taxable_monthly = Decimal(str(remaining_annual / 12))
        
        # Employer match (assume 3% typical)
        employer_match = annual_income * 0.03
        
        # Tax savings from deductions
        tax_savings = (annual_401k + float(hsa_annual)) * input_data.constraints.tax_bracket
        
        return ContributionSchedule(
            retirement_401k_percent=round(optimal_401k_pct, 3),
            retirement_401k_annual=Decimal(str(annual_401k)),
            roth_ira_annual=Decimal(str(max_ira)),
            hsa_annual=hsa_annual,
            taxable_monthly=taxable_monthly,
            total_monthly=Decimal(str((annual_401k + max_ira + float(hsa_annual)) / 12 + float(taxable_monthly))),
            employer_match_annual=Decimal(str(employer_match)),
            tax_savings_annual=Decimal(str(tax_savings))
        )
    
    def _prioritize_debt(self, input_data: PlanInput) -> List[DebtAction]:
        """Prioritize debt payoff using avalanche method"""
        debt_actions = []
        
        for debt_name, balance in input_data.current_state.liabilities.items():
            # Estimate rates based on debt type
            if 'credit' in debt_name.lower():
                rate = 0.2499
                action = 'payoff_months_1_3'
            elif 'student' in debt_name.lower():
                rate = 0.065
                action = 'income_driven_repayment'
            elif 'mortgage' in debt_name.lower():
                rate = 0.065
                action = 'maintain_payment'
                # Check for refinance opportunity
                if rate > 0.058:
                    action = f'refinance_to_5.8'
            elif 'auto' in debt_name.lower():
                rate = 0.055
                action = 'maintain_payment'
            else:
                rate = 0.08
                action = 'minimum_payment'
            
            # Calculate payment details
            monthly_payment = self._calculate_monthly_payment(float(balance), rate, 360)
            
            debt_actions.append(DebtAction(
                debt=debt_name,
                balance=balance,
                rate=rate,
                action=action,
                monthly_payment=Decimal(str(monthly_payment)),
                payoff_months=360 if 'mortgage' in debt_name.lower() else 60,
                total_interest=Decimal(str(monthly_payment * 360 - float(balance))),
                refinance_rate=0.058 if 'refinance' in action else None,
                refinance_savings=Decimal(str((rate - 0.058) * float(balance) / 12 * 360)) if 'refinance' in action else None
            ))
        
        # Sort by interest rate (avalanche method)
        debt_actions.sort(key=lambda x: x.rate, reverse=True)
        
        return debt_actions
    
    def _calculate_monthly_payment(self, principal: float, rate: float, months: int) -> float:
        """Calculate monthly payment for a loan"""
        if rate == 0:
            return principal / months
        monthly_rate = rate / 12
        payment = principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
        return payment
    
    def _calculate_metrics(
        self,
        input_data: PlanInput,
        target_allocation: TargetAllocation,
        contributions: ContributionSchedule
    ) -> PlanMetrics:
        """Calculate key plan metrics"""
        # Portfolio statistics
        allocation_dict = {
            'us_stocks': target_allocation.us_stocks,
            'intl_stocks': target_allocation.intl_stocks,
            'bonds': target_allocation.bonds,
            'reits': target_allocation.reits,
            'cash': target_allocation.cash
        }
        
        expected_return, expected_volatility = self._get_portfolio_stats(allocation_dict)
        
        # Sharpe ratio (assume risk-free rate of 2%)
        risk_free_rate = 0.02
        sharpe_ratio = (expected_return - risk_free_rate) / expected_volatility
        
        # Required savings rate
        annual_income = float(sum(input_data.current_state.income.values()))
        annual_savings = float(contributions.total_monthly) * 12
        required_savings_rate = annual_savings / annual_income if annual_income > 0 else 0
        
        # Stress tests
        current_value = float(input_data.current_state.net_worth)
        stress_30 = self._stress_test(current_value, 0.30, expected_return, years=1)
        stress_50 = self._stress_test(current_value, 0.50, expected_return, years=1)
        
        # Years to goal
        gap = float(input_data.goals.target_net_worth - input_data.current_state.net_worth)
        if annual_savings > 0 and expected_return > 0:
            years_to_goal = np.log(1 + (gap / annual_savings) * expected_return) / np.log(1 + expected_return)
        elif annual_savings > 0:
            years_to_goal = gap / annual_savings
        else:
            years_to_goal = 999  # Cannot reach goal without savings
        
        return PlanMetrics(
            expected_return=round(expected_return, 4),
            expected_volatility=round(expected_volatility, 4),
            sharpe_ratio=round(sharpe_ratio, 2),
            required_savings_rate=round(required_savings_rate, 3),
            stress_test_30pct_drop=round(stress_30, 2),
            stress_test_50pct_drop=round(stress_50, 2),
            max_drawdown_expected=round(expected_volatility * 2, 3),
            years_to_goal=round(years_to_goal, 1),
            inflation_assumption=0.03
        )
    
    def _stress_test(self, current_value: float, drop_pct: float, recovery_rate: float, years: int) -> float:
        """Calculate portfolio value after stress event"""
        # Immediate drop
        value_after_drop = current_value * (1 - drop_pct)
        
        # Recovery over time
        value_recovered = value_after_drop * (1 + recovery_rate) ** years
        
        # Return success probability
        return min(1.0, value_recovered / current_value)
    
    def _optimize_taxes(self, input_data: PlanInput) -> TaxStrategy:
        """Calculate tax optimization strategies"""
        annual_income = float(sum(input_data.current_state.income.values()))
        tax_bracket = input_data.constraints.tax_bracket
        
        # Tax loss harvesting potential (assume 0.3% of taxable assets)
        taxable_assets = float(sum(
            v for k, v in input_data.current_state.assets.items()
            if 'taxable' in k.lower() or 'brokerage' in k.lower()
        ))
        tax_loss_harvest = taxable_assets * 0.003
        
        # Roth conversion analysis
        roth_conversion = 0
        if tax_bracket < 0.24:  # Convert in lower tax brackets
            # Convert up to next bracket
            bracket_room = 50000  # Simplified
            roth_conversion = min(bracket_room, taxable_assets * 0.1)
        
        # Asset location optimization
        tax_efficient_placement = {
            'bonds': 'tax_deferred_401k',
            'reits': 'tax_deferred_ira',
            'international': 'taxable',
            'us_stocks': 'taxable',
            'cash': 'taxable'
        }
        
        # Total tax savings estimate
        estimated_savings = (tax_loss_harvest * tax_bracket) + (roth_conversion * 0.05)
        
        return TaxStrategy(
            tax_loss_harvest_annual=Decimal(str(tax_loss_harvest)),
            roth_conversion_annual=Decimal(str(roth_conversion)),
            tax_efficient_placement=tax_efficient_placement,
            estimated_tax_savings=Decimal(str(estimated_savings))
        )
    
    def _estimate_monthly_contribution(self, input_data: PlanInput) -> float:
        """Estimate monthly contribution capacity"""
        monthly_income = float(sum(input_data.current_state.income.values())) / 12
        monthly_expenses = float(sum(input_data.current_state.expenses.values()))
        return max(0, monthly_income - monthly_expenses)