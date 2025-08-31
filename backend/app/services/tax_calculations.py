"""
Tax Calculations Service
Precise tax calculations for optimization strategies
"""
from typing import Dict, List, Tuple, Optional
from decimal import Decimal, ROUND_HALF_UP
import structlog
from datetime import datetime

try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = object
    
try:
    from ..utils.safe_conversion import safe_float
except ImportError:
    def safe_float(value, default=0.0):
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

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

    def analyze_comprehensive_tax_opportunities(self, user_id: int, financial_context: Dict, db: Session = None) -> Dict:
        """Comprehensive tax opportunity analysis - SINGLE SOURCE OF TRUTH"""
        
        try:
            # Extract and validate key financial data
            annual_income = safe_float(financial_context.get('monthly_income', 0)) * 12
            tax_bracket = safe_float(financial_context.get('tax_bracket', 24))
            state = financial_context.get('state', 'NC')
            mortgage_balance = safe_float(financial_context.get('mortgage_balance', 0))
            investments = safe_float(financial_context.get('investment_total', 0))
            current_401k = safe_float(financial_context.get('annual_401k', 0))
            age = financial_context.get('age', 35)
            filing_status = financial_context.get('filing_status', 'married')
            
            # DEBUG: Log extracted values
            logger.error(f"DEBUG TAX CALC: current_401k extracted: {current_401k} from context: {financial_context.get('annual_401k', 'NOT_FOUND')}")
            logger.error(f"DEBUG TAX CALC: annual_income: {annual_income}, age: {age}")
            
            # Calculate mortgage interest estimate (assume 6.5% rate)
            mortgage_interest = mortgage_balance * 0.065 if mortgage_balance > 0 else 0
            
            # Get marginal tax rates for accurate calculations
            tax_analysis = self.calculate_marginal_tax_rate(annual_income, filing_status, state)
            marginal_rate = tax_analysis['marginal_rates']['combined']
            
            # Build comprehensive opportunities using existing methods
            opportunities = []
            
            # 1. Retirement Optimization using existing method
            current_contributions = {
                '401k': current_401k,
                'traditional_ira': financial_context.get('traditional_ira', 0),
                'roth_ira': financial_context.get('roth_ira', 0)
            }
            retirement_opt = self.retirement_contribution_optimization(
                current_contributions, annual_income, age, marginal_rate
            )
            
            for opt in retirement_opt['optimization_opportunities']:
                if opt.get('tax_savings', {}).get('total_tax_savings', 0) > 0:
                    opportunities.append({
                        'strategy': opt['strategy'],
                        'annual_tax_savings': opt['tax_savings']['total_tax_savings'],
                        'difficulty': 'Easy',
                        'timeline': 'Next payroll period',
                        'priority': opt['priority'],
                        'description': f"Increase {opt['strategy'].lower()} by ${opt['additional_needed']:,.0f}",
                        'implementation_details': opt['implementation']
                    })
            
            # 2. Itemization Analysis
            if mortgage_interest > 0:
                estimated_property_tax = min(annual_income * 0.015, 15000)
                state_local_taxes = min(annual_income * 0.05, self.SALT_CAP)
                
                deductions = {
                    'mortgage_interest': mortgage_interest,
                    'property_taxes': estimated_property_tax,
                    'state_local_taxes': state_local_taxes,
                    'charitable': financial_context.get('charitable_donations', 0),
                    'other': 0
                }
                
                itemization = self.should_itemize_analysis(deductions, filing_status)
                if itemization['recommendation']['should_itemize']:
                    benefit = itemization['recommendation']['benefit_over_alternative']
                    if benefit > 500:  # Meaningful benefit
                        opportunities.append({
                            'strategy': 'Itemize Deductions',
                            'annual_tax_savings': benefit * (marginal_rate / 100),
                            'difficulty': 'Easy',
                            'timeline': 'Tax filing',
                            'priority': 2,
                            'description': f"Itemize saves ${benefit:,.0f} over standard deduction",
                            'implementation_details': 'Track and organize deductible expenses'
                        })
                
                # 3. Bunching Strategy Analysis
                bunching = self.bunching_strategy_analysis(deductions, filing_status, marginal_rate)
                if bunching['analysis']['worthwhile']:
                    opportunities.append({
                        'strategy': 'Deduction Bunching',
                        'annual_tax_savings': bunching['analysis']['annual_tax_savings'],
                        'difficulty': 'Medium',
                        'timeline': 'Q4 planning',
                        'priority': 3,
                        'description': 'Bundle deductions into alternating years',
                        'implementation_details': '; '.join(bunching['analysis']['implementation_items'])
                    })
            
            # 4. Tax-Loss Harvesting
            if investments > 50000:
                harvesting = self.tax_loss_harvesting_analysis(investments, 0, marginal_rate)
                if harvesting['worthwhile']:
                    opportunities.append({
                        'strategy': 'Tax-Loss Harvesting',
                        'annual_tax_savings': harvesting['tax_benefits']['total_annual_savings'],
                        'difficulty': 'Medium',
                        'timeline': 'Before December 31',
                        'priority': 4,
                        'description': 'Harvest investment losses to offset gains',
                        'implementation_details': 'Review portfolio quarterly; avoid wash sales'
                    })
            
            # Calculate total potential savings
            total_savings = sum(opp['annual_tax_savings'] for opp in opportunities)
            
            # Sort by savings amount (descending)
            opportunities.sort(key=lambda x: x['annual_tax_savings'], reverse=True)
            
            return {
                'user_id': user_id,
                'taxpayer_profile': {
                    'annual_income': annual_income,
                    'tax_bracket': tax_bracket,
                    'marginal_rate': marginal_rate,
                    'filing_status': filing_status,
                    'state': state,
                    'age': age
                },
                'calculated_opportunities': opportunities,
                'total_potential_savings': total_savings,
                'tax_rates': tax_analysis,
                'analysis_summary': {
                    'opportunities_found': len(opportunities),
                    'implementation_priorities': {
                        'immediate': len([o for o in opportunities if o['difficulty'] == 'Easy']),
                        'planned': len([o for o in opportunities if o['difficulty'] == 'Medium']),
                        'complex': len([o for o in opportunities if o['difficulty'] == 'Complex'])
                    }
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Comprehensive tax analysis failed", error=str(e), user_id=user_id)
            return {
                'error': 'Tax analysis failed',
                'message': 'Unable to complete tax optimization analysis. Please try again.',
                'calculated_opportunities': [],
                'total_potential_savings': 0
            }
    
    def get_quick_tax_opportunities(self, user_id: int, financial_summary: Dict) -> List[Dict]:
        """Quick tax opportunities for dashboard - NO HARDCODING"""
        
        opportunities = []
        
        # Get basic data
        annual_income = financial_summary.get('monthlyIncome', 0) * 12
        current_401k = financial_summary.get('annual401k', 0)
        age = financial_summary.get('age', 35)
        investment_total = financial_summary.get('investmentTotal', 0)
        tax_bracket = financial_summary.get('taxBracket', 24)
        
        if annual_income == 0:
            return opportunities
        
        # Get real marginal rate
        tax_rates = self.calculate_marginal_tax_rate(annual_income, 'married', 'NC')
        combined_rate = tax_rates['marginal_rates']['combined'] / 100
        
        # 1. 401k Optimization - REAL CALCULATION
        max_401k = self.RETIREMENT_LIMITS['50_plus']['401k'] if age >= 50 else self.RETIREMENT_LIMITS['under_50']['401k']
        
        logger.error(f"DEBUG TAX CALC: 401k limits - current: ${current_401k:,.0f}, max: ${max_401k:,.0f}, age: {age}")
        
        if current_401k < max_401k:
            additional_401k = max_401k - current_401k
            # REAL calculation using actual marginal rate
            tax_savings = additional_401k * (combined_rate / 100)
            opportunities.append({
                "strategy": "Maximize 401k Contribution",
                "annual_tax_savings": tax_savings,
                "potential_savings": tax_savings,
                "difficulty": "Easy",
                "priority": 1,
                "timeline": "Next payroll period",
                "description": f"Increase 401k from ${current_401k:,.0f} to ${max_401k:,.0f}"
            })
        elif current_401k > max_401k:
            # User is over-contributing - this is a compliance issue
            over_contribution = current_401k - max_401k
            potential_penalty_savings = over_contribution * 0.06  # Avoid 6% excise tax
            opportunities.append({
                "strategy": "Reduce Excess 401k Contribution",
                "annual_tax_savings": potential_penalty_savings,
                "potential_savings": potential_penalty_savings,
                "difficulty": "Easy",
                "priority": 1,
                "timeline": "Immediately",
                "description": f"Reduce 401k from ${current_401k:,.0f} to ${max_401k:,.0f} (over by ${over_contribution:,.0f})"
            })
        
        # 2. Tax-Loss Harvesting - REAL CALCULATION
        if investment_total > 50000 and annual_income > 75000:
            # Use real calculation method
            harvesting = self.tax_loss_harvesting_analysis(investment_total, 0, tax_bracket)
            if harvesting['worthwhile']:
                estimated_savings = harvesting['tax_benefits']['total_annual_savings']
                opportunities.append({
                    "strategy": "Tax-Loss Harvesting",
                    "potential_savings": estimated_savings,
                    "difficulty": "Medium",
                    "priority": 2,
                    "description": "Harvest investment losses to offset gains"
                })
        
        # 3. IRA Contribution - REAL CALCULATION
        if self._ira_deduction_eligible(annual_income):
            max_ira = self.RETIREMENT_LIMITS['50_plus']['ira'] if age >= 50 else self.RETIREMENT_LIMITS['under_50']['ira']
            current_ira = financial_summary.get('traditionalIra', 0)
            if current_ira < max_ira:
                additional_ira = max_ira - current_ira
                ira_savings = additional_ira * combined_rate
                opportunities.append({
                    "strategy": "Maximize IRA Contribution",
                    "potential_savings": ira_savings,
                    "difficulty": "Easy",
                    "priority": 3,
                    "description": f"Contribute ${additional_ira:,.0f} to traditional IRA"
                })
        
        # Sort by potential savings
        opportunities.sort(key=lambda x: x["potential_savings"], reverse=True)
        
        return opportunities


# Global tax calculations instance
tax_calculations = TaxCalculations()