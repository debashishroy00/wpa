"""
Tax Calculations Service
Precise tax calculations for optimization strategies
"""
from typing import Dict, List, Tuple, Optional
from decimal import Decimal, ROUND_HALF_UP
import structlog
from datetime import datetime

logger = structlog.get_logger()

class TaxCalculations:
    """Comprehensive tax calculations for accurate financial planning"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.FEDERAL_BRACKETS_2024 = {
            'single': [
                (11000, 0.10),
                (44725, 0.12),
                (95375, 0.22),
                (182050, 0.24),
                (231250, 0.32),
                (578125, 0.35),
                (float('inf'), 0.37)
            ],
            'married': [
                (22000, 0.10),
                (89450, 0.12),
                (190750, 0.22),
                (364200, 0.24),
                (462500, 0.32),
                (693750, 0.35),
                (float('inf'), 0.37)
            ]
        }
        
        # Standard deductions and limits for 2024
        self.STANDARD_DEDUCTIONS = {'single': 14600, 'married': 29200}
        self.SALT_CAP = 10000
        self.RETIREMENT_LIMITS = {
            'under_50': {'401k': 23000, 'ira': 7000},
            '50_plus': {'401k': 30500, 'ira': 8000}
        }
        
        # State tax rates (simplified - major states)
        self.STATE_TAX_RATES = {
            'NC': 0.0525, 'CA': 0.093, 'TX': 0.0, 'FL': 0.0,
            'NY': 0.0685, 'NJ': 0.0637, 'VA': 0.0575
        }
    
    def calculate_marginal_tax_rate(self, income: float, filing_status: str = 'married', 
                                  state: str = 'NC') -> Dict:
        """Calculate marginal and effective tax rates"""
        
        try:
            # Federal marginal rate
            federal_marginal = self._get_marginal_rate(income, filing_status)
            
            # State marginal rate
            state_marginal = self.STATE_TAX_RATES.get(state, 0.05)
            
            # Combined marginal rate
            combined_marginal = federal_marginal + state_marginal
            
            # Calculate effective rates
            federal_tax = self._calculate_federal_tax(income, filing_status)
            federal_effective = federal_tax / income if income > 0 else 0
            
            state_tax = income * state_marginal
            combined_effective = (federal_tax + state_tax) / income if income > 0 else 0
            
            return {
                'marginal_rates': {
                    'federal': round(federal_marginal * 100, 1),
                    'state': round(state_marginal * 100, 1),
                    'combined': round(combined_marginal * 100, 1)
                },
                'effective_rates': {
                    'federal': round(federal_effective * 100, 1),
                    'combined': round(combined_effective * 100, 1)
                },
                'tax_amounts': {
                    'federal': round(federal_tax, 2),
                    'state': round(state_tax, 2),
                    'total': round(federal_tax + state_tax, 2)
                }
            }
        except Exception as e:
            logger.error("Tax rate calculation failed", error=str(e))
            return {'error': 'Tax calculation failed'}
    
    def _get_marginal_rate(self, income: float, filing_status: str) -> float:
        """Get marginal tax rate for given income and filing status"""
        
        brackets = self.FEDERAL_BRACKETS_2024.get(filing_status, self.FEDERAL_BRACKETS_2024['married'])
        
        for threshold, rate in brackets:
            if income <= threshold:
                return rate
        
        return 0.37  # Highest bracket
    
    def _calculate_federal_tax(self, income: float, filing_status: str) -> float:
        """Calculate federal income tax using progressive brackets"""
        
        brackets = self.FEDERAL_BRACKETS_2024.get(filing_status, self.FEDERAL_BRACKETS_2024['married'])
        tax = 0
        previous_threshold = 0
        
        for threshold, rate in brackets:
            if income <= threshold:
                tax += (income - previous_threshold) * rate
                break
            else:
                tax += (threshold - previous_threshold) * rate
                previous_threshold = threshold
        
        return tax
    
    def calculate_tax_savings(self, amount: float, marginal_rate: float, 
                            state_rate: float = 0.0525) -> Dict:
        """Calculate tax savings from deduction or contribution"""
        
        federal_savings = amount * (marginal_rate / 100)
        state_savings = amount * state_rate
        total_savings = federal_savings + state_savings
        
        return {
            'contribution_amount': amount,
            'federal_tax_savings': round(federal_savings, 2),
            'state_tax_savings': round(state_savings, 2),
            'total_tax_savings': round(total_savings, 2),
            'after_tax_cost': round(amount - total_savings, 2),
            'effective_cost_percentage': round((amount - total_savings) / amount * 100, 1)
        }
    
    def should_itemize_analysis(self, deductions: Dict, filing_status: str = 'married') -> Dict:
        """Comprehensive itemization vs standard deduction analysis"""
        
        standard_deduction = self.STANDARD_DEDUCTIONS[filing_status]
        
        # Calculate total itemized deductions
        mortgage_interest = deductions.get('mortgage_interest', 0)
        property_taxes = deductions.get('property_taxes', 0)
        state_local_taxes = deductions.get('state_local_taxes', 0)
        charitable = deductions.get('charitable', 0)
        other_deductions = deductions.get('other', 0)
        
        # Apply SALT cap
        salt_total = min(property_taxes + state_local_taxes, self.SALT_CAP)
        total_itemized = mortgage_interest + salt_total + charitable + other_deductions
        
        # Determine best strategy
        should_itemize = total_itemized > standard_deduction
        benefit = max(0, total_itemized - standard_deduction)
        
        return {
            'itemized_breakdown': {
                'mortgage_interest': mortgage_interest,
                'salt_deductions': salt_total,
                'salt_limitation': property_taxes + state_local_taxes - salt_total,
                'charitable': charitable,
                'other': other_deductions,
                'total_itemized': total_itemized
            },
            'standard_deduction': standard_deduction,
            'recommendation': {
                'should_itemize': should_itemize,
                'deduction_used': total_itemized if should_itemize else standard_deduction,
                'benefit_over_alternative': benefit,
                'additional_deductions_needed': max(0, standard_deduction - total_itemized + 100)
            }
        }
    
    def bunching_strategy_analysis(self, base_deductions: Dict, filing_status: str = 'married',
                                 marginal_rate: float = 24) -> Dict:
        """Analyze deduction bunching strategy potential"""
        
        # Calculate current year benefit
        current_analysis = self.should_itemize_analysis(base_deductions, filing_status)
        current_benefit = current_analysis['recommendation']['benefit_over_alternative']
        
        # Simulate bunching by doubling certain flexible deductions
        bunched_deductions = base_deductions.copy()
        bunched_deductions['charitable'] = base_deductions.get('charitable', 0) * 2
        bunched_deductions['property_taxes'] = base_deductions.get('property_taxes', 0) + 5000  # Prepay next year
        
        # Calculate bunched year benefit
        bunched_analysis = self.should_itemize_analysis(bunched_deductions, filing_status)
        bunched_benefit = bunched_analysis['recommendation']['benefit_over_alternative']
        
        # Calculate off-year (using standard deduction)
        standard_deduction = self.STANDARD_DEDUCTIONS[filing_status]
        
        # Two-year comparison
        normal_two_year = current_benefit * 2
        bunched_two_year = bunched_benefit + 0  # Bunched year + standard deduction year
        
        two_year_advantage = bunched_two_year - normal_two_year
        annual_tax_savings = two_year_advantage * (marginal_rate / 100) / 2
        
        return {
            'current_strategy': {
                'annual_deduction': current_analysis['recommendation']['deduction_used'],
                'annual_benefit': current_benefit,
                'two_year_total': normal_two_year
            },
            'bunching_strategy': {
                'bunched_year_deduction': bunched_analysis['recommendation']['deduction_used'],
                'bunched_year_benefit': bunched_benefit,
                'off_year_deduction': standard_deduction,
                'off_year_benefit': 0,
                'two_year_total': bunched_two_year
            },
            'analysis': {
                'two_year_advantage': two_year_advantage,
                'annual_tax_savings': round(annual_tax_savings, 2),
                'worthwhile': two_year_advantage > 1000,  # Threshold for complexity
                'implementation_items': self._get_bunching_items(base_deductions)
            }
        }
    
    def _get_bunching_items(self, base_deductions: Dict) -> List[str]:
        """Get specific items that can be bunched"""
        
        items = []
        
        if base_deductions.get('charitable', 0) > 0:
            items.append("Double charitable contributions in alternating years")
        
        if base_deductions.get('property_taxes', 0) > 0:
            items.append("Pay next year's property taxes in December")
        
        if base_deductions.get('state_local_taxes', 0) > self.SALT_CAP:
            items.append("Time state tax payments to maximize SALT benefit")
        
        return items
    
    def retirement_contribution_optimization(self, current_contributions: Dict, 
                                           income: float, age: int, 
                                           marginal_rate: float = 24) -> Dict:
        """Optimize retirement contributions for maximum tax benefit"""
        
        # Determine limits
        limits = self.RETIREMENT_LIMITS['50_plus'] if age >= 50 else self.RETIREMENT_LIMITS['under_50']
        
        current_401k = current_contributions.get('401k', 0)
        current_ira = current_contributions.get('traditional_ira', 0)
        
        # Calculate gaps
        k401_gap = limits['401k'] - current_401k
        ira_gap = limits['ira'] - current_ira
        
        optimizations = []
        
        # 401k optimization (if employer plan available)
        if k401_gap > 0:
            tax_savings = self.calculate_tax_savings(k401_gap, marginal_rate)
            optimizations.append({
                'strategy': '401k Maximization',
                'current_contribution': current_401k,
                'recommended_contribution': limits['401k'],
                'additional_needed': k401_gap,
                'tax_savings': tax_savings,
                'priority': 1,  # Highest priority (employer match potential)
                'implementation': 'Update payroll deduction immediately'
            })
        
        # Traditional IRA optimization (if no 401k or after maxing 401k)
        if ira_gap > 0 and self._ira_deduction_eligible(income):
            tax_savings = self.calculate_tax_savings(ira_gap, marginal_rate)
            optimizations.append({
                'strategy': 'Traditional IRA Maximization',
                'current_contribution': current_ira,
                'recommended_contribution': limits['ira'],
                'additional_needed': ira_gap,
                'tax_savings': tax_savings,
                'priority': 2,
                'implementation': 'Contribute before tax deadline'
            })
        
        # Roth IRA consideration
        if self._roth_ira_eligible(income):
            optimizations.append({
                'strategy': 'Roth IRA Consideration',
                'current_contribution': current_contributions.get('roth_ira', 0),
                'recommended_contribution': limits['ira'],
                'additional_needed': limits['ira'] - current_contributions.get('roth_ira', 0),
                'tax_savings': {'note': 'Tax-free growth and withdrawals in retirement'},
                'priority': 3,
                'implementation': 'Consider if in low tax bracket or young'
            })
        
        total_additional = sum(opt['additional_needed'] for opt in optimizations[:2])  # 401k + IRA
        total_savings = sum(opt.get('tax_savings', {}).get('total_tax_savings', 0) for opt in optimizations[:2])
        
        return {
            'current_situation': current_contributions,
            'optimization_opportunities': optimizations,
            'summary': {
                'total_additional_contributions': total_additional,
                'total_annual_tax_savings': round(total_savings, 2),
                'after_tax_cost': round(total_additional - total_savings, 2),
                'effective_savings_rate': round((total_savings / total_additional * 100), 1) if total_additional > 0 else 0
            }
        }
    
    def _ira_deduction_eligible(self, income: float) -> bool:
        """Check if traditional IRA deduction is available (simplified)"""
        # Simplified - assumes no employer plan or income below phase-out
        return income < 150000  # Rough threshold
    
    def _roth_ira_eligible(self, income: float) -> bool:
        """Check if Roth IRA contribution is available (simplified)"""
        # Simplified phase-out rules
        return income < 200000  # Rough threshold for married filing jointly
    
    def tax_loss_harvesting_analysis(self, portfolio_value: float, 
                                   current_gains: float = 0,
                                   marginal_rate: float = 24) -> Dict:
        """Analyze tax-loss harvesting opportunities"""
        
        # Conservative estimates for harvestable losses
        estimated_losses = min(3000, portfolio_value * 0.02)  # 2% of portfolio, capped at $3k ordinary income offset
        
        # Calculate tax benefits
        ordinary_income_offset = min(estimated_losses, 3000)
        capital_gains_offset = max(0, estimated_losses - ordinary_income_offset)
        
        # Tax savings calculation
        ordinary_savings = ordinary_income_offset * (marginal_rate / 100)
        capital_gains_savings = capital_gains_offset * 0.15  # Assume 15% capital gains rate
        
        total_tax_savings = ordinary_savings + capital_gains_savings
        
        return {
            'portfolio_analysis': {
                'total_value': portfolio_value,
                'estimated_harvestable_losses': estimated_losses,
                'current_unrealized_gains': current_gains
            },
            'tax_benefits': {
                'ordinary_income_offset': ordinary_income_offset,
                'capital_gains_offset': capital_gains_offset,
                'ordinary_income_tax_savings': round(ordinary_savings, 2),
                'capital_gains_tax_savings': round(capital_gains_savings, 2),
                'total_annual_savings': round(total_tax_savings, 2)
            },
            'implementation': {
                'timing': 'Before December 31st',
                'wash_sale_warning': 'Avoid repurchasing same securities within 30 days',
                'frequency': 'Review quarterly for opportunities'
            },
            'worthwhile': total_tax_savings > 200  # Minimum threshold
        }
    
    def estimated_quarterly_payments(self, annual_income: float, 
                                   withholding: float = 0,
                                   filing_status: str = 'married') -> Dict:
        """Calculate if quarterly estimated payments are needed"""
        
        # Calculate estimated annual tax
        tax_rates = self.calculate_marginal_tax_rate(annual_income, filing_status)
        estimated_annual_tax = tax_rates['tax_amounts']['total']
        
        # Safe harbor calculations
        prior_year_tax = estimated_annual_tax * 0.9  # Assume similar to current year
        safe_harbor_100 = prior_year_tax  # 100% of prior year
        safe_harbor_110 = prior_year_tax * 1.1  # 110% if high income
        
        # Determine if payments needed
        remaining_tax = estimated_annual_tax - withholding
        needs_quarterly = remaining_tax > 1000
        
        if needs_quarterly:
            quarterly_amount = remaining_tax / 4
            safe_harbor_quarterly = min(safe_harbor_100, safe_harbor_110) / 4
            
            return {
                'needs_quarterly_payments': True,
                'estimated_annual_tax': round(estimated_annual_tax, 2),
                'current_withholding': withholding,
                'remaining_tax_due': round(remaining_tax, 2),
                'quarterly_payment_needed': round(quarterly_amount, 2),
                'safe_harbor_payment': round(safe_harbor_quarterly, 2),
                'due_dates': ['Jan 15', 'Apr 15', 'Jun 15', 'Sep 15'],
                'penalty_avoidance': 'Pay safe harbor amount to avoid penalties'
            }
        else:
            return {
                'needs_quarterly_payments': False,
                'estimated_annual_tax': round(estimated_annual_tax, 2),
                'current_withholding': withholding,
                'reason': 'Withholding sufficient or balance under $1,000'
            }

# Global tax calculations instance
tax_calculations = TaxCalculations()