"""
Hybrid Context Service
Combines essential guaranteed data with intent-based vector search
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class HybridContextService:
    """
    Hybrid approach:
    1. Essential must-haves: profile, assets, liabilities, income, expenses, benefits, pre-calculations
    2. Intent-based: semantic search for supplementary context
    3. Validation: benchmark analysis before responding
    """
    
    def __init__(self):
        self.essential_categories = [
            'profile', 'assets', 'liabilities', 'income', 'expenses', 
            'retirement_benefits', 'taxes', 'cash_flow', 'asset_allocation'
        ]
    
    def build_hybrid_context(self, user_id: int, db: Session, user_query: str, intent: str) -> str:
        """
        Build hybrid context with essential data + intent-based vector search + validation prompts
        """
        try:
            # STEP 1: Get essential guaranteed data
            essential_data = self._get_essential_data(user_id, db)
            
            if 'error' in essential_data:
                return f"Error loading essential data: {essential_data['error']}"
            
            # STEP 2: Intent-based vector search for supplementary context
            supplementary_context = self._get_intent_based_context(user_id, user_query, intent)
            
            # STEP 3: Build comprehensive prompt with validation instructions
            context = self._build_validated_prompt(essential_data, supplementary_context, user_query, intent)
            
            return context
            
        except Exception as e:
            logger.error(f"Error building hybrid context for user {user_id}: {str(e)}")
            return f"Error building context: {str(e)}"
    
    def _get_essential_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get essential must-have financial data - guaranteed to be complete"""
        try:
            from .financial_summary_service import financial_summary_service
            from .financial_health_scorer import financial_health_scorer
            from ..models.user import User
            from ..models.user_profile import UserProfile, UserBenefit
            
            # Get financial summary
            summary = financial_summary_service.get_user_financial_summary(user_id, db)
            if 'error' in summary:
                return {'error': summary['error']}
            
            # Get user profile
            user = db.query(User).filter(User.id == user_id).first()
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            # Get Social Security benefits
            ss_benefits = db.query(UserBenefit).join(UserProfile).filter(
                UserProfile.user_id == user_id,
                UserBenefit.benefit_type == 'social_security'
            ).first()
            
            social_security_monthly = float(ss_benefits.estimated_monthly_benefit or 0) if ss_benefits else 0
            social_security_annual = social_security_monthly * 12
            
            # Get retirement goals from database
            from ..models.goals_v2 import Goal
            retirement_goals = db.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.name.ilike('%retirement%')
            ).all()
            
            retirement_goal = 3500000  # Default $3.5M
            if retirement_goals:
                retirement_goal = max(float(goal.target_amount) for goal in retirement_goals)
            
            # Get financial health score
            health_score = financial_health_scorer.calculate_comprehensive_score(user_id, db)
            
            # Pre-calculations
            net_worth = summary.get('netWorth', 0)
            monthly_income = summary.get('monthlyIncome', 0)
            monthly_expenses = summary.get('monthlyExpenses', 0)
            monthly_surplus = summary.get('monthlySurplus', 0)
            debt_to_income = summary.get('debtToIncomeRatio', 0)
            savings_rate = summary.get('savingsRate', 0)
            
            # Asset allocation and detailed breakdown
            assets_breakdown = summary.get('assetsBreakdown', {})
            total_assets = summary.get('totalAssets', 0)
            
            # Process detailed asset breakdown for display
            detailed_assets = self._build_detailed_asset_breakdown(assets_breakdown)
            detailed_liabilities = self._build_detailed_liability_breakdown(summary.get('liabilitiesBreakdown', []))
            
            return {
                # Profile essentials
                'user_name': f"{user.first_name} {user.last_name}".strip() if user else "Client",
                'age': profile.age if profile else 54,
                'risk_tolerance': profile.risk_tolerance if profile else 'moderate',
                
                # Financial position
                'net_worth': net_worth,
                'total_assets': total_assets,
                'total_liabilities': summary.get('totalLiabilities', 0),
                
                # Cash flow
                'monthly_income': monthly_income,
                'monthly_expenses': monthly_expenses,
                'monthly_surplus': monthly_surplus,
                'savings_rate': savings_rate,
                
                # Key ratios (pre-calculated)
                'debt_to_income_ratio': debt_to_income,
                'emergency_fund_months': (summary.get('totalAssets', 0) / monthly_expenses) if monthly_expenses > 0 else 0,
                
                # Asset breakdown
                'assets_breakdown': assets_breakdown,
                'detailed_assets': detailed_assets,
                'detailed_liabilities': detailed_liabilities,
                
                # Retirement benefits
                'social_security_monthly': social_security_monthly,
                'social_security_annual': social_security_annual,
                'retirement_goal': retirement_goal,
                
                # Financial health
                'financial_health_score': health_score.get('overall_score', 0),
                'financial_health_grade': health_score.get('grade', 'N/A'),
                'health_score_breakdown': health_score.get('component_scores', {}),
                
                # Benchmarks
                'peer_comparison': health_score.get('peer_comparison', {}),
            }
            
        except Exception as e:
            logger.error(f"Error getting essential data: {str(e)}")
            return {'error': f"Failed to retrieve essential data: {str(e)}"}
    
    def _get_intent_based_context(self, user_id: int, user_query: str, intent: str) -> List[str]:
        """Get supplementary context based on intent using vector search"""
        try:
            from .vector_db_service import FinancialVectorDB
            
            vector_db = FinancialVectorDB()
            
            # Intent-specific search terms
            intent_searches = {
                'retirement': ['retirement goal', 'pension', '401k contributions', 'IRA'],
                'investment': ['portfolio allocation', 'risk tolerance', 'investment performance'],
                'debt': ['debt payments', 'interest rates', 'loan terms'],
                'tax': ['tax deductions', 'tax planning', 'retirement tax'],
                'estate': ['beneficiaries', 'estate planning', 'insurance'],
                'education': ['529 plans', 'education savings'],
                'real_estate': ['property values', 'mortgage terms', 'rental income']
            }
            
            # Get intent-specific search terms + user query
            search_terms = intent_searches.get(intent, []) + [user_query]
            
            # Search for supplementary context
            supplementary_docs = []
            for term in search_terms[:3]:  # Limit to top 3 searches
                results = vector_db.search_context(user_id, term, n_results=5)
                for doc in results[:2]:  # Top 2 per search
                    content = doc.get('content', '')
                    if content and content not in supplementary_docs:
                        supplementary_docs.append(content)
            
            return supplementary_docs[:6]  # Max 6 supplementary documents
            
        except Exception as e:
            logger.warning(f"Could not get intent-based context: {str(e)}")
            return []
    
    def _build_validated_prompt(self, essential_data: Dict, supplementary_context: List[str], 
                               user_query: str, intent: str) -> str:
        """Build prompt with essential data + supplementary context + validation instructions"""
        
        # Format essential data
        essential_section = f"""
ESSENTIAL FINANCIAL DATA (GUARANTEED COMPLETE)
============================================

PROFILE:
--------
Name: {essential_data['user_name']}
Age: {essential_data['age']}
Risk Tolerance: {essential_data['risk_tolerance']}

FINANCIAL POSITION:
------------------
Net Worth: ${essential_data['net_worth']:,.0f}
Total Assets: ${essential_data['total_assets']:,.0f}
Total Liabilities: ${essential_data['total_liabilities']:,.0f}

DETAILED ASSET BREAKDOWN:
------------------------
{essential_data['detailed_assets']}

DETAILED LIABILITY BREAKDOWN:
----------------------------
{essential_data['detailed_liabilities']}

CASH FLOW ANALYSIS:
------------------
Monthly Income: ${essential_data['monthly_income']:,.0f}
Monthly Expenses: ${essential_data['monthly_expenses']:,.0f}
Monthly Surplus: ${essential_data['monthly_surplus']:,.0f}
Savings Rate: {essential_data['savings_rate']:.1f}%

KEY FINANCIAL RATIOS:
--------------------
Debt-to-Income: {essential_data['debt_to_income_ratio']:.1f}%
Emergency Fund: {essential_data['emergency_fund_months']:.1f} months

RETIREMENT BENEFITS:
-------------------
Retirement Goal: ${essential_data['retirement_goal']:,.0f}
Social Security: ${essential_data['social_security_monthly']:,.0f}/month (${essential_data['social_security_annual']:,.0f}/year)

FINANCIAL HEALTH ASSESSMENT:
----------------------------
Overall Score: {essential_data['financial_health_score']:.1f}/100 ({essential_data['financial_health_grade']})
Peer Comparison: {essential_data['peer_comparison'].get('status', 'unknown').upper()}
"""

        # Format supplementary context
        supplementary_section = ""
        if supplementary_context:
            supplementary_section = f"""
SUPPLEMENTARY CONTEXT (Intent: {intent})
======================================
"""
            for i, context in enumerate(supplementary_context, 1):
                supplementary_section += f"{i}. {context[:200]}...\n\n"

        # Validation and analysis instructions
        validation_section = f"""
USER QUESTION: "{user_query}"

CRITICAL ANALYSIS INSTRUCTIONS:
===============================

BEFORE RESPONDING, YOU MUST:

1. VALIDATE THE DATA:
   - Check if essential data is complete and realistic
   - Verify mathematical consistency (income - expenses = surplus)
   - Cross-reference with supplementary context for accuracy

2. BENCHMARK ANALYSIS:
   - Compare against industry standards (4% rule for retirement, 20% savings rate, etc.)
   - Use peer comparison data (age {essential_data['age']}, {essential_data['peer_comparison'].get('net_worth_percentile', 'N/A')}th percentile)
   - Assess financial health score components

3. RETIREMENT CALCULATION (if applicable):
   CRITICAL: When calculating retirement readiness, use this EXACT math:
   - Retirement Goal: ${essential_data['retirement_goal']:,.0f}
   - SUBTRACT Social Security value: ${essential_data['social_security_annual']:,.0f}/year × 25 years = ${essential_data['social_security_annual'] * 25:,.0f}
   - Net Portfolio Needed = ${essential_data['retirement_goal']:,.0f} - ${essential_data['social_security_annual'] * 25:,.0f} = ${essential_data['retirement_goal'] - (essential_data['social_security_annual'] * 25):,.0f}
   - Compare: Net Portfolio Needed (${essential_data['retirement_goal'] - (essential_data['social_security_annual'] * 25):,.0f}) vs Current Net Worth (${essential_data['net_worth']:,.0f})
   - STATUS: {'AHEAD OF SCHEDULE!' if essential_data['net_worth'] > (essential_data['retirement_goal'] - (essential_data['social_security_annual'] * 25)) else 'BEHIND SCHEDULE - NEED MORE SAVING'}

4. PROVIDE SPECIFIC ANALYSIS:
   - Use actual numbers from the essential data above
   - Reference specific financial health score ({essential_data['financial_health_score']:.1f}/100)
   - Give concrete, actionable advice based on the complete picture
   - State clearly if they're ahead, on track, or behind their goals

DO NOT:
- Ask for additional information (you have complete essential data)
- Give generic advice
- Ignore Social Security benefits in retirement calculations
- Provide vague assessments

RESPOND WITH:
- Specific numerical analysis using the essential data
- Clear assessment of their financial position
- Concrete recommendations based on benchmarks and validation
"""

        return essential_section + supplementary_section + validation_section
    
    def _build_detailed_asset_breakdown(self, assets_breakdown: Dict) -> str:
        """Build detailed asset breakdown for display"""
        
        breakdown_text = ""
        
        # Retirement Accounts
        retirement_accounts = assets_breakdown.get('retirement_accounts', [])
        if retirement_accounts:
            breakdown_text += "Retirement Accounts:\n"
            total_retirement = 0
            for account in retirement_accounts:
                if isinstance(account, dict):
                    name = account.get('name', 'Unknown Account')
                    value = account.get('value', 0)
                    breakdown_text += f"  • {name}: ${value:,.0f}\n"
                    total_retirement += value
            breakdown_text += f"  TOTAL RETIREMENT: ${total_retirement:,.0f}\n\n"
        
        # Investment Accounts
        investment_accounts = assets_breakdown.get('investment_accounts', [])
        if investment_accounts:
            breakdown_text += "Investment Accounts:\n"
            total_investments = 0
            for account in investment_accounts:
                if isinstance(account, dict):
                    name = account.get('name', 'Unknown Account')
                    value = account.get('value', 0)
                    breakdown_text += f"  • {name}: ${value:,.0f}\n"
                    total_investments += value
            breakdown_text += f"  TOTAL INVESTMENTS: ${total_investments:,.0f}\n\n"
        
        # Real Estate
        real_estate = assets_breakdown.get('real_estate', [])
        if real_estate:
            breakdown_text += "Real Estate:\n"
            total_real_estate = 0
            for property in real_estate:
                if isinstance(property, dict):
                    name = property.get('name', 'Unknown Property')
                    value = property.get('value', 0)
                    breakdown_text += f"  • {name}: ${value:,.0f}\n"
                    total_real_estate += value
            breakdown_text += f"  TOTAL REAL ESTATE: ${total_real_estate:,.0f}\n\n"
        
        # Cash Accounts
        cash_accounts = assets_breakdown.get('cash_bank_accounts', [])
        if cash_accounts:
            breakdown_text += "Cash & Bank Accounts:\n"
            total_cash = 0
            for account in cash_accounts:
                if isinstance(account, dict):
                    name = account.get('name', 'Unknown Account')
                    value = account.get('value', 0)
                    breakdown_text += f"  • {name}: ${value:,.0f}\n"
                    total_cash += value
            breakdown_text += f"  TOTAL CASH: ${total_cash:,.0f}\n\n"
        
        # Other Assets
        other_assets = assets_breakdown.get('other_assets', [])
        personal_property = assets_breakdown.get('personal_property', [])
        all_other = other_assets + personal_property
        
        if all_other:
            breakdown_text += "Other Assets:\n"
            total_other = 0
            for asset in all_other:
                if isinstance(asset, dict):
                    name = asset.get('name', 'Unknown Asset')
                    value = asset.get('value', 0)
                    breakdown_text += f"  • {name}: ${value:,.0f}\n"
                    total_other += value
            breakdown_text += f"  TOTAL OTHER: ${total_other:,.0f}\n"
        
        return breakdown_text if breakdown_text else "No detailed asset breakdown available"
    
    def _build_detailed_liability_breakdown(self, liabilities_breakdown: List) -> str:
        """Build detailed liability breakdown for display"""
        
        if not liabilities_breakdown:
            return "No liabilities or debt breakdown available"
        
        breakdown_text = ""
        total_liabilities = 0
        
        for liability in liabilities_breakdown:
            if isinstance(liability, dict):
                name = liability.get('name', 'Unknown Debt')
                balance = liability.get('balance', 0)
                rate = liability.get('interest_rate', 0)
                
                if rate and rate > 0:
                    breakdown_text += f"• {name}: ${balance:,.0f} @ {rate:.2f}% APR\n"
                else:
                    breakdown_text += f"• {name}: ${balance:,.0f}\n"
                
                total_liabilities += balance
        
        breakdown_text += f"\nTOTAL LIABILITIES: ${total_liabilities:,.0f}"
        
        return breakdown_text


# Global instance
hybrid_context_service = HybridContextService()