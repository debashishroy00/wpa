"""
Tax Optimization Service
Provides sophisticated tax analysis and actionable optimization strategies
"""
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import structlog
from sqlalchemy.orm import Session

from ..utils.safe_conversion import safe_float

logger = structlog.get_logger()

class TaxOptimizationService:
    """Generate deep tax insights and optimization strategies with specific dollar amounts"""
    
    def __init__(self, db: Session, llm_service):
        self.db = db
        self.llm_service = llm_service
        self.current_year = datetime.now().year
        
        # Tax constants for 2024
        self.STANDARD_DEDUCTION_MFJ = 29200
        self.STANDARD_DEDUCTION_SINGLE = 14600
        self.MAX_401K_CONTRIBUTION = 23000
        self.MAX_401K_CATCHUP = 30500  # Age 50+
        self.SALT_CAP = 10000
        self.NC_STATE_TAX_RATE = 0.0525
        
    async def analyze_tax_opportunities(self, user_id: int, financial_context: Dict) -> Dict:
        """Identify specific tax savings opportunities with dollar amounts"""
        
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
            
            # Calculate mortgage interest estimate (assume 6.5% rate)
            mortgage_interest = mortgage_balance * 0.065 if mortgage_balance > 0 else 0
            
            # Build comprehensive tax analysis prompt
            prompt = self._build_tax_analysis_prompt(
                annual_income, tax_bracket, state, mortgage_balance, 
                mortgage_interest, investments, current_401k, age, filing_status
            )
            
            # Get AI analysis
            logger.info("Requesting tax analysis from LLM", user_id=user_id)
            analysis = await self.llm_service.generate(
                system_prompt="You are a CPA and tax strategist. Provide specific, actionable tax advice with exact calculations and dollar amounts.",
                user_prompt=prompt,
                temperature=0.2  # Lower temperature for factual accuracy
            )
            
            # Parse and structure the analysis
            structured_analysis = self._parse_and_structure_analysis(
                analysis, annual_income, tax_bracket, current_401k, age, filing_status
            )
            
            # Add specific calculations
            structured_analysis['calculated_opportunities'] = self._calculate_specific_opportunities(
                annual_income, tax_bracket, current_401k, age, mortgage_interest
            )
            
            logger.info("Tax analysis completed", 
                       user_id=user_id, 
                       opportunities_found=len(structured_analysis['calculated_opportunities']))
            
            return structured_analysis
            
        except Exception as e:
            logger.error("Failed to analyze tax opportunities", error=str(e), user_id=user_id)
            return {
                'error': 'Tax analysis failed',
                'message': 'Unable to complete tax optimization analysis. Please try again.',
                'calculated_opportunities': []
            }
    
    def _build_tax_analysis_prompt(self, annual_income: float, tax_bracket: float, 
                                 state: str, mortgage_balance: float, mortgage_interest: float,
                                 investments: float, current_401k: float, age: int, 
                                 filing_status: str) -> str:
        """Build comprehensive tax analysis prompt"""
        
        standard_deduction = self.STANDARD_DEDUCTION_MFJ if filing_status == 'married' else self.STANDARD_DEDUCTION_SINGLE
        max_401k = self.MAX_401K_CATCHUP if age >= 50 else self.MAX_401K_CONTRIBUTION
        
        return f"""
        COMPREHENSIVE TAX OPTIMIZATION ANALYSIS
        
        TAXPAYER PROFILE:
        - Annual Income: ${annual_income:,.0f}
        - Federal Tax Bracket: {tax_bracket}% (marginal)
        - Age: {age} (401k limit: ${max_401k:,})
        - Filing Status: {filing_status.title()}
        - State: {state} (Est. rate: 5.25%)
        - Current 401k Contribution: ${current_401k:,.0f}
        
        FINANCIAL POSITION:
        - Mortgage Balance: ${mortgage_balance:,.0f}
        - Estimated Annual Mortgage Interest: ${mortgage_interest:,.0f}
        - Investment Accounts: ${investments:,.0f}
        - Standard Deduction ({self.current_year}): ${standard_deduction:,}
        
        ANALYZE THESE SPECIFIC STRATEGIES WITH EXACT DOLLAR SAVINGS:
        
        1. RETIREMENT CONTRIBUTION OPTIMIZATION:
           - Current 401k gap: ${max_401k - current_401k:,.0f} remaining
           - Tax savings from maximizing: Calculate exact amount
           - Roth vs Traditional analysis for their bracket
           - Backdoor Roth conversion opportunities
        
        2. ITEMIZATION vs STANDARD DEDUCTION:
           - Mortgage interest: ${mortgage_interest:,.0f}
           - Property taxes: Estimate based on income level
           - State taxes (SALT cap): ${self.SALT_CAP:,} max
           - Total itemized vs ${standard_deduction:,} standard
           - Bunching strategy potential
        
        3. TAX-LOSS HARVESTING:
           - Portfolio size: ${investments:,.0f}
           - Estimated harvestable losses (conservative 2-3%)
           - Tax savings calculation at {tax_bracket}% bracket
           - Wash sale rule considerations
        
        4. ADVANCED STRATEGIES:
           - Charitable giving optimization
           - HSA maximization if available
           - State-specific deductions and credits
           - Estimated tax payments and safe harbor
        
        REQUIREMENTS:
        - Provide specific dollar amounts for each strategy
        - Rank by implementation difficulty (Easy/Medium/Complex)
        - Include timeline for implementation
        - Calculate total potential annual savings
        - Flag any risks or limitations
        
        Format with clear sections and exact calculations.
        """
    
    def _parse_and_structure_analysis(self, raw_analysis: str, annual_income: float, 
                                    tax_bracket: float, current_401k: float, 
                                    age: int, filing_status: str) -> Dict:
        """Parse LLM analysis and add structure"""
        
        # Extract dollar amounts from analysis
        dollar_matches = re.findall(r'\$[\d,]+(?:\.\d{2})?', raw_analysis)
        dollar_amounts = [float(match.replace('$', '').replace(',', '')) for match in dollar_matches]
        
        # Calculate estimated total savings
        potential_savings = self._estimate_total_savings(dollar_amounts, raw_analysis)
        
        # Extract key recommendations
        recommendations = self._extract_key_recommendations(raw_analysis)
        
        return {
            'raw_analysis': raw_analysis,
            'taxpayer_profile': {
                'annual_income': annual_income,
                'tax_bracket': tax_bracket,
                'current_401k': current_401k,
                'age': age,
                'filing_status': filing_status
            },
            'total_potential_savings': potential_savings,
            'key_recommendations': recommendations,
            'implementation_priority': self._determine_priority(recommendations),
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_specific_opportunities(self, annual_income: float, tax_bracket: float,
                                       current_401k: float, age: int, 
                                       mortgage_interest: float) -> List[Dict]:
        """Calculate specific tax opportunities with exact amounts"""
        
        opportunities = []
        
        # 1. 401k Maximization Opportunity
        max_401k = self.MAX_401K_CATCHUP if age >= 50 else self.MAX_401K_CONTRIBUTION
        if current_401k < max_401k:
            additional_contribution = max_401k - current_401k
            tax_savings = additional_contribution * (tax_bracket / 100) + additional_contribution * self.NC_STATE_TAX_RATE
            
            opportunities.append({
                'strategy': 'Maximize 401k Contribution',
                'current_amount': current_401k,
                'recommended_amount': max_401k,
                'additional_contribution': additional_contribution,
                'annual_tax_savings': tax_savings,
                'difficulty': 'Easy',
                'timeline': 'Next payroll period',
                'priority': 1,
                'description': f"Increase 401k from ${current_401k:,.0f} to ${max_401k:,.0f}"
            })
        
        # 2. Itemization Analysis
        estimated_property_tax = min(annual_income * 0.015, 15000)  # Conservative estimate
        total_itemized = mortgage_interest + min(self.SALT_CAP, estimated_property_tax + annual_income * 0.05)
        
        if total_itemized > self.STANDARD_DEDUCTION_MFJ * 0.9:  # Close to beneficial
            bunching_benefit = self._calculate_bunching_strategy(total_itemized, tax_bracket)
            if bunching_benefit > 0:
                opportunities.append({
                    'strategy': 'Deduction Bunching',
                    'current_itemized': total_itemized,
                    'standard_deduction': self.STANDARD_DEDUCTION_MFJ,
                    'annual_tax_savings': bunching_benefit,
                    'difficulty': 'Medium',
                    'timeline': 'Q4 2024 planning',
                    'priority': 2,
                    'description': 'Bundle deductible expenses into alternating years'
                })
        
        # 3. Tax-Loss Harvesting (if significant investments)
        if annual_income > 100000:  # Focus on higher earners with investments
            estimated_losses = min(3000, annual_income * 0.01)  # Conservative 1% loss harvesting
            tax_savings = estimated_losses * (tax_bracket / 100)
            
            opportunities.append({
                'strategy': 'Tax-Loss Harvesting',
                'harvestable_losses': estimated_losses,
                'annual_tax_savings': tax_savings,
                'difficulty': 'Medium',
                'timeline': 'Before year-end',
                'priority': 3,
                'description': 'Realize investment losses to offset gains'
            })
        
        return opportunities
    
    def _calculate_bunching_strategy(self, base_itemized: float, tax_bracket: float) -> float:
        """Calculate potential savings from bunching deductions"""
        
        # Simulate bunching by doubling certain deductions every other year
        enhanced_itemized = base_itemized + 8000  # Extra charitable and property tax prepayment
        
        # Year 1: Enhanced itemization
        year1_benefit = max(0, enhanced_itemized - self.STANDARD_DEDUCTION_MFJ)
        year1_savings = year1_benefit * (tax_bracket / 100)
        
        # Year 2: Standard deduction
        year2_savings = 0  # Use standard deduction
        
        # Two-year average benefit
        two_year_benefit = (year1_savings + year2_savings) / 2
        current_benefit = max(0, base_itemized - self.STANDARD_DEDUCTION_MFJ) * (tax_bracket / 100)
        
        return max(0, two_year_benefit - current_benefit)
    
    def _estimate_total_savings(self, dollar_amounts: List[float], raw_analysis: str) -> float:
        """Estimate total potential tax savings from analysis"""
        
        # Look for explicit savings mentions in the text
        savings_pattern = r'sav(?:e|ing)s?[:\s]*\$?([\d,]+)'
        savings_matches = re.findall(savings_pattern, raw_analysis.lower())
        
        if savings_matches:
            total_savings = sum(float(match.replace(',', '')) for match in savings_matches[-3:])  # Last 3 mentions
            return min(total_savings, 15000)  # Cap at reasonable amount
        
        # Fallback: estimate from dollar amounts
        if dollar_amounts:
            return min(sum(dollar_amounts[-2:]) if len(dollar_amounts) >= 2 else dollar_amounts[0], 10000)
        
        return 0
    
    def _extract_key_recommendations(self, analysis: str) -> List[str]:
        """Extract key actionable recommendations"""
        
        recommendations = []
        
        # Look for numbered or bulleted recommendations
        bullet_pattern = r'[•\-\*]\s*(.+?)(?=\n|$)'
        number_pattern = r'\d+\.\s*(.+?)(?=\n|$)'
        
        bullets = re.findall(bullet_pattern, analysis)
        numbers = re.findall(number_pattern, analysis)
        
        # Combine and clean up
        all_recommendations = bullets + numbers
        
        for rec in all_recommendations[:5]:  # Top 5 recommendations
            clean_rec = rec.strip()
            if len(clean_rec) > 20 and '$' in clean_rec:  # Focus on substantial recommendations with amounts
                recommendations.append(clean_rec)
        
        return recommendations
    
    def _determine_priority(self, recommendations: List[str]) -> List[Dict]:
        """Determine implementation priority for recommendations"""
        
        priority_keywords = {
            1: ['401k', '401(k)', 'retirement', 'contribution'],
            2: ['itemize', 'deduction', 'bunching'],
            3: ['harvest', 'loss', 'investment'],
            4: ['roth', 'conversion'],
            5: ['charitable', 'hsa', 'advanced']
        }
        
        prioritized = []
        
        for i, rec in enumerate(recommendations):
            priority = 3  # Default priority
            
            for p, keywords in priority_keywords.items():
                if any(keyword in rec.lower() for keyword in keywords):
                    priority = p
                    break
            
            prioritized.append({
                'recommendation': rec,
                'priority': priority,
                'order': i + 1
            })
        
        return sorted(prioritized, key=lambda x: x['priority'])
    
    async def calculate_specific_strategy(self, user_id: int, strategy_type: str, 
                                        financial_context: Dict) -> Dict:
        """Deep dive calculation for specific tax strategy"""
        
        strategy_calculators = {
            'roth_conversion': self._calculate_roth_conversion,
            'bunching': self._calculate_bunching_detailed,
            'tax_loss_harvesting': self._calculate_tax_loss_harvesting,
            'retirement_optimization': self._calculate_retirement_optimization
        }
        
        if strategy_type not in strategy_calculators:
            return {'error': f'Unknown strategy type: {strategy_type}'}
        
        try:
            return await strategy_calculators[strategy_type](user_id, financial_context)
        except Exception as e:
            logger.error("Strategy calculation failed", 
                        strategy=strategy_type, user_id=user_id, error=str(e))
            return {'error': 'Calculation failed', 'details': str(e)}
    
    async def _calculate_roth_conversion(self, user_id: int, financial_context: Dict) -> Dict:
        """Calculate optimal Roth conversion strategy"""
        
        current_age = financial_context.get('age', 35)
        retirement_age = 65
        current_bracket = safe_float(financial_context.get('tax_bracket', 24))
        traditional_ira = safe_float(financial_context.get('traditional_ira', 0))
        
        # Assume retirement bracket will be 2% lower
        retirement_bracket = max(12, current_bracket - 2)
        
        conversion_amounts = [10000, 25000, 50000, 100000]
        analyses = []
        
        for amount in conversion_amounts:
            if amount <= traditional_ira:
                tax_cost_now = amount * (current_bracket / 100)
                years_to_retirement = retirement_age - current_age
                
                # Future value assuming 7% growth
                future_value = amount * (1.07 ** years_to_retirement)
                future_tax_saved = future_value * (retirement_bracket / 100)
                
                net_benefit = future_tax_saved - tax_cost_now
                
                analyses.append({
                    'conversion_amount': amount,
                    'tax_cost_now': tax_cost_now,
                    'future_value': future_value,
                    'future_tax_saved': future_tax_saved,
                    'net_benefit': net_benefit,
                    'years_to_breakeven': tax_cost_now / (future_tax_saved / years_to_retirement) if future_tax_saved > tax_cost_now else None
                })
        
        return {
            'strategy': 'Roth Conversion Analysis',
            'current_situation': {
                'age': current_age,
                'current_bracket': current_bracket,
                'retirement_bracket': retirement_bracket,
                'traditional_ira_balance': traditional_ira
            },
            'conversion_scenarios': analyses,
            'recommendation': self._get_roth_recommendation(analyses)
        }
    
    def _get_roth_recommendation(self, analyses: List[Dict]) -> str:
        """Get recommendation based on Roth conversion analysis"""
        
        if not analyses:
            return "Insufficient IRA balance for meaningful conversion"
        
        best_scenario = max(analyses, key=lambda x: x['net_benefit'] if x['net_benefit'] > 0 else 0)
        
        if best_scenario['net_benefit'] > 5000:
            return f"Convert ${best_scenario['conversion_amount']:,.0f} - Net benefit: ${best_scenario['net_benefit']:,.0f}"
        elif best_scenario['net_benefit'] > 0:
            return f"Small benefit from ${best_scenario['conversion_amount']:,.0f} conversion - consider tax diversification"
        else:
            return "Current tax bracket too high for beneficial conversion - wait for lower income year"