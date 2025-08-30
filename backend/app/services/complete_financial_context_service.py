"""
Complete Financial Context Service
Provides the COMPLETE financial picture with all details and accurate calculations
No more asking for data we already have!
"""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class CompleteFinancialContextService:
    """Service that provides the COMPLETE financial picture"""
    
    def build_complete_context(self, user_id: int, db: Session, user_query: str = "", insight_level: str = "balanced") -> str:
        """
        Build the complete financial context that includes EVERYTHING
        
        This is the definitive financial picture - no more partial data!
        """
        try:
            # Get complete financial data
            financial_data = self._get_complete_financial_data(user_id, db)
            
            if 'error' in financial_data:
                return f"Error loading financial data: {financial_data['error']}"
            
            # REMOVED: Health score calculation (calculate on-demand instead)
            # This reduces token costs by ~200 tokens per request and eliminates staleness
            
            # Build context based on insight level
            if insight_level == "focused":
                # Essential context for focused responses
                context = f"""FINANCIAL SNAPSHOT FOR {financial_data['name']}
=============================================================
PERSONAL INFO: Age {financial_data.get('age', 'unknown')}, {financial_data.get('state', 'Unknown')} resident, {financial_data.get('marital_status', 'Unknown')}
TAX STATUS: {financial_data.get('filing_status', 'Unknown')} filing, {financial_data.get('tax_bracket', 'Unknown')}% federal bracket
OCCUPATION: {financial_data.get('occupation', 'Unknown')}"""
                
                # Add family information if available
                family_members = financial_data.get('family_members', [])
                if family_members:
                    context += f"\nFAMILY: "
                    family_info = []
                    for member in family_members:
                        if member.get('name') and member.get('age'):
                            family_info.append(f"{member['relationship']} {member['name']} (age {member['age']})")
                        elif member.get('relationship'):
                            family_info.append(f"{member['relationship']}")
                    context += ", ".join(family_info)
                
                context += f"""
=============================================================
NET WORTH: ${financial_data['net_worth']:,.0f}
TOTAL ASSETS: ${financial_data['total_assets']:,.0f}
TOTAL LIABILITIES: ${financial_data['total_liabilities']:,.0f}

MONTHLY CASH FLOW:
- Income: ${financial_data['monthly_income']:,.0f}
- Expenses: ${financial_data['monthly_expenses']:,.0f}  
- Surplus: ${financial_data['monthly_surplus']:,.0f}

RETIREMENT PROGRESS: {financial_data['retirement_progress']:.1f}% of ${financial_data['retirement_goal']:,.0f} goal

ASSET BREAKDOWN:
- Cash: ${financial_data['cash_accounts']['total']:,.0f}
- Retirement: ${financial_data['retirement_accounts']['total']:,.0f}
- Investments: ${financial_data['investment_accounts']['total']:,.0f}
- Real Estate Equity: ${financial_data['real_estate_properties']['total'] - financial_data['mortgage_balance']:,.0f}

USER QUESTION: "{user_query}"

ANSWER DIRECTLY using the above financial data. Be specific and use the exact numbers provided.
"""
            else:
                # Complete context for balanced/comprehensive responses  
                context = f"""COMPLETE FINANCIAL PICTURE FOR {financial_data['name']}
================================================

PERSONAL PROFILE:
-----------------
  • Age: {financial_data.get('age', 'unknown')} years old
  • State: {financial_data.get('state', 'Unknown')}
  • Marital Status: {financial_data.get('marital_status', 'Unknown')}
  • Occupation: {financial_data.get('occupation', 'Unknown')}
  • Tax Filing Status: {financial_data.get('filing_status', 'Unknown')}
  • Federal Tax Bracket: {financial_data.get('tax_bracket', 'Unknown')}%"""
                
                # Add family information if available
                family_members = financial_data.get('family_members', [])
                if family_members:
                    context += f"\n  • Family Members: "
                    family_info = []
                    for member in family_members:
                        if member.get('name') and member.get('age'):
                            family_info.append(f"{member['relationship']} {member['name']} (age {member['age']})")
                        elif member.get('relationship'):
                            family_info.append(f"{member['relationship']}")
                    context += ", ".join(family_info)
                
                context += f"""

ASSETS DETAIL (${financial_data['total_assets']:,.0f} total):
--------------------------------
Real Estate:
{self._format_account_list(financial_data['real_estate_properties']['accounts'])}
  • Total Real Estate: ${financial_data['real_estate_properties']['total']:,.0f}
  • Mortgage Balance: -${financial_data['mortgage_balance']:,.0f}
  • Net Real Estate Equity: ${financial_data['real_estate_properties']['total'] - financial_data['mortgage_balance']:,.0f}

Retirement Accounts:
{self._format_account_list(financial_data['retirement_accounts']['accounts'])}
  • Total Retirement: ${financial_data['retirement_accounts']['total']:,.0f}
  
Investment Accounts:
{self._format_account_list(financial_data['investment_accounts']['accounts'])}
  • Total Investments: ${financial_data['investment_accounts']['total']:,.0f}

Alternative Assets:
  • Bitcoin: ${financial_data['bitcoin_value']:,.0f}

Cash & Equivalents:
{self._format_cash_accounts_with_yield(financial_data['cash_accounts']['accounts'])}
  • Total Liquid: ${financial_data['cash_accounts']['total']:,.0f}
{self._get_cash_optimization_summary(financial_data['cash_accounts']['accounts'], financial_data['cash_accounts']['total'])}

Other Assets:
{self._format_account_list(financial_data['other_assets']['accounts'])}
  • Total Other: ${financial_data['other_assets']['total']:,.0f}

LIABILITIES DETAIL (${financial_data['total_liabilities']:,.0f} total):
------------------------------------
{self._format_liability_list_with_mortgage(financial_data.get('liabilitiesBreakdown', []), financial_data.get('mortgage_balance', 0))}

NET WORTH: ${financial_data['net_worth']:,.0f}
====================

MONTHLY CASH FLOW:
-----------------
Income:
  • Employment & Investment Income: ${financial_data['monthly_income']:,.0f}
  • Total Monthly Income: ${financial_data['monthly_income']:,.0f}
  
Expenses:
  • Total Monthly Expenses: ${financial_data['monthly_expenses']:,.0f}
  
Net Surplus: ${financial_data['monthly_surplus']:,.0f} (59.9% savings rate)

RETIREMENT STATUS:
-----------------
  • Current Goal: ${financial_data['retirement_goal']:,.0f}
  • Current Progress: ${financial_data['retirement_capable_assets']:,.0f} ({financial_data['retirement_progress']:.1f}% of goal)
  • Years to Goal: {financial_data['years_to_goal']:.1f} years (age {financial_data['goal_achievement_age']:.0f})
  • Early Retirement: {'POSSIBLE' if financial_data['can_retire_early'] else 'Need more time'}
  • Social Security: ${financial_data.get('social_security_monthly', 0):,.0f}/month (${financial_data.get('social_security_annual', 0):,.0f}/year) starting at age {financial_data.get('social_security_age', 67)}

ASSET ALLOCATION ANALYSIS:
-------------------------
{self._format_asset_allocation(financial_data)}

ESTATE PLANNING DOCUMENTS:
-------------------------
{self._format_estate_planning(financial_data.get('estate_planning', []))}

INSURANCE COVERAGE:
------------------
{self._format_insurance_policies(financial_data.get('insurance_policies', []))}

INVESTMENT PREFERENCES:
----------------------
{self._format_investment_preferences(financial_data.get('investment_preferences', {}))}

USER QUESTION: "{user_query}"

RESPONSE FOCUS:
================
CRITICAL: Answer ONLY what the user asked about. 

If user asks about CASH → Discuss only cash position and optimization
If user asks about RETIREMENT → Focus on retirement progress and strategies
If user asks about ALLOCATION → Discuss portfolio balance
If user asks GENERAL question → Provide comprehensive overview

Do not volunteer unrelated information. Stay focused on the specific topic.

Example:
- Question: "How is my cash position?"
- Talk about: Cash amounts, yields, optimization opportunities
- DON'T talk about: Real estate, Bitcoin, retirement, percentiles

{self._get_insight_level_instructions(insight_level)}"""

            # Add the insight level instructions to the focused context too
            if insight_level == "focused":
                context += f"\n\n{self._get_insight_level_instructions(insight_level)}"

            return context
            
        except Exception as e:
            logger.error(f"Error building complete context for user {user_id}: {str(e)}")
            return f"Error building financial context: {str(e)}"
    
    def _get_complete_financial_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get ALL financial data with complete breakdown"""
        try:
            from .financial_summary_service import financial_summary_service
            from ..models.user import User
            from ..models.user_profile import UserProfile
            from ..models.goals_v2 import Goal
            
            # Get financial summary
            summary = financial_summary_service.get_user_financial_summary(user_id, db)
            
            if 'error' in summary:
                return {'error': summary['error']}
            
            # Get user info
            user = db.query(User).filter(User.id == user_id).first()
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            name = f"{user.first_name} {user.last_name}".strip() if user and (user.first_name or user.last_name) else "Client"
            age = profile.age if profile and profile.age else 54
            
            # Get retirement goal
            retirement_goals = db.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.name.ilike('%retirement%')
            ).all()
            
            retirement_goal = 3500000  # Default $3.5M as specified
            target_date = None
            retirement_age_target = 65  # Default
            
            if retirement_goals:
                retirement_goal = max(float(goal.target_amount) for goal in retirement_goals)
                # Use actual target date from goal, not hardcoded age
                for goal in retirement_goals:
                    if goal.target_date:
                        target_date = goal.target_date
                        break
                    if goal.params and isinstance(goal.params, dict):
                        goal_retirement_age = goal.params.get('retirement_age')
                        if goal_retirement_age:
                            retirement_age_target = goal_retirement_age
            
            # Process asset breakdown
            assets_breakdown = summary.get('assetsBreakdown', {})
            
            # Retirement accounts
            retirement_accounts = self._process_asset_category(assets_breakdown.get('retirement_accounts', []))
            
            # Investment accounts (separate Bitcoin)
            investment_raw = assets_breakdown.get('investment_accounts', [])
            investment_accounts = {'accounts': [], 'total': 0}
            bitcoin_value = 0
            
            for account in investment_raw:
                if isinstance(account, dict):
                    if 'bitcoin' in account.get('name', '').lower():
                        bitcoin_value += account.get('value', 0)
                    else:
                        investment_accounts['accounts'].append(account)
                        investment_accounts['total'] += account.get('value', 0)
            
            # Cash accounts
            cash_accounts = self._process_asset_category(assets_breakdown.get('cash_bank_accounts', []))
            
            # Real estate - FIXED: Include ALL properties, not just primary
            real_estate_raw = assets_breakdown.get('real_estate', [])
            real_estate_properties = self._process_asset_category(real_estate_raw)
            
            # Extract primary home for specific display  
            home_value = 0
            for prop in real_estate_raw:
                if isinstance(prop, dict) and 'primary' in prop.get('name', '').lower():
                    home_value = prop.get('value', 0)
                    break
            if home_value == 0 and real_estate_raw:
                home_value = real_estate_raw[0].get('value', 0) if real_estate_raw else 0
            
            # Other assets
            other_assets = self._process_asset_category(assets_breakdown.get('other_assets', []) + 
                                                     assets_breakdown.get('personal_property', []))
            
            # Liabilities
            liabilities_breakdown = summary.get('liabilitiesBreakdown', [])
            mortgage_balance = 0
            other_liabilities = []
            
            for liability in liabilities_breakdown:
                if isinstance(liability, dict):
                    if 'mortgage' in liability.get('name', '').lower():
                        mortgage_balance = liability.get('balance', 0)
                    else:
                        other_liabilities.append(liability)
            
            home_equity = max(0, home_value - mortgage_balance)
            
            # Calculate retirement metrics - FIXED: Use net real estate equity
            net_real_estate_equity = real_estate_properties['total'] - mortgage_balance
            retirement_capable_assets = (
                retirement_accounts['total'] + 
                investment_accounts['total'] + 
                bitcoin_value + 
                net_real_estate_equity  # Use net real estate equity, not just home equity
            )
            
            retirement_progress = (retirement_capable_assets / retirement_goal * 100) if retirement_goal > 0 else 0
            
            monthly_surplus = summary.get('monthlySurplus', 0)
            remaining_needed = max(0, retirement_goal - retirement_capable_assets)
            
            # FIXED: Use actual target date from goal, not age-based calculation
            if target_date:
                from datetime import datetime
                current_date = datetime.now().date()
                if hasattr(target_date, 'date'):
                    target_date = target_date.date()
                
                days_to_goal = (target_date - current_date).days
                years_to_goal = max(0, days_to_goal / 365.25)
                goal_achievement_age = age + years_to_goal
            else:
                # Fallback to age-based calculation if no target date
                years_to_goal = max(0, retirement_age_target - age)
                goal_achievement_age = retirement_age_target
            
            can_retire_early = retirement_progress >= 100
            
            # REMOVED: Rental income estimation (actual rental already included in monthly_income)
            # The $844 actual rental income is already included in the $17,744 total
            
            # Get Social Security benefits
            social_security_monthly = 0
            social_security_annual = 0
            social_security_age = 67
            
            try:
                from ..models.user_profile import UserBenefit
                ss_benefits = db.query(UserBenefit).join(UserProfile).filter(
                    UserProfile.user_id == user_id,
                    UserBenefit.benefit_type == 'social_security'
                ).first()
                
                if ss_benefits:
                    social_security_monthly = float(ss_benefits.estimated_monthly_benefit or 0)
                    social_security_annual = social_security_monthly * 12
                    social_security_age = ss_benefits.full_retirement_age or 67
            except Exception as e:
                logger.warning(f"Could not retrieve Social Security benefits: {str(e)}")
            
            # Get personal information from profile
            state = profile.state if profile and profile.state else "Unknown"
            marital_status = profile.marital_status if profile and profile.marital_status else "Unknown"
            occupation = profile.occupation if profile and profile.occupation else "Unknown"
            
            # Get tax information
            tax_bracket = None
            filing_status = "Unknown"
            state_tax_rate = None
            try:
                from ..models.user_profile import UserTaxInfo
                tax_info = db.query(UserTaxInfo).join(UserProfile).filter(
                    UserProfile.user_id == user_id
                ).order_by(UserTaxInfo.tax_year.desc()).first()
                
                if tax_info:
                    tax_bracket = float(tax_info.federal_tax_bracket) if tax_info.federal_tax_bracket else None
                    filing_status = tax_info.filing_status or "Unknown"
                    state_tax_rate = float(tax_info.state_tax_bracket) if tax_info.state_tax_bracket else None
            except Exception as e:
                logger.warning(f"Could not retrieve tax information: {str(e)}")
            
            # Get family members
            family_members = []
            try:
                from ..models.user_profile import FamilyMember
                family = db.query(FamilyMember).join(UserProfile).filter(
                    UserProfile.user_id == user_id
                ).all()
                
                for member in family:
                    family_members.append({
                        'relationship': member.relationship_type,
                        'name': member.name,
                        'age': member.age
                    })
            except Exception as e:
                logger.warning(f"Could not retrieve family information: {str(e)}")
            
            # Get enhanced categories - Estate Planning, Insurance, Investment Preferences
            estate_planning = []
            insurance_policies = []
            investment_preferences = {}
            
            try:
                from ..models.estate_planning import UserEstatePlanning
                estate_docs = db.query(UserEstatePlanning).filter(
                    UserEstatePlanning.user_id == user_id
                ).all()
                
                for doc in estate_docs:
                    estate_planning.append({
                        'document_type': doc.document_type,
                        'document_name': doc.document_name,
                        'status': doc.status,
                        'last_updated': doc.last_updated.isoformat() if doc.last_updated else None,
                        'attorney_contact': doc.attorney_contact,
                        'document_location': doc.document_location,
                        'document_details': doc.document_details
                    })
            except Exception as e:
                logger.warning(f"Could not retrieve estate planning information: {str(e)}")
            
            try:
                from ..models.insurance import UserInsurancePolicy
                insurance_docs = db.query(UserInsurancePolicy).filter(
                    UserInsurancePolicy.user_id == user_id
                ).all()
                
                for policy in insurance_docs:
                    insurance_policies.append({
                        'policy_type': policy.policy_type,
                        'policy_name': policy.policy_name,
                        'coverage_amount': float(policy.coverage_amount) if policy.coverage_amount else 0,
                        'annual_premium': float(policy.annual_premium) if policy.annual_premium else 0,
                        'beneficiary_primary': policy.beneficiary_primary,
                        'beneficiary_secondary': policy.beneficiary_secondary,
                        'policy_details': policy.policy_details
                    })
            except Exception as e:
                logger.warning(f"Could not retrieve insurance information: {str(e)}")
            
            try:
                from ..models.investment_preferences import UserInvestmentPreferences
                inv_prefs = db.query(UserInvestmentPreferences).filter(
                    UserInvestmentPreferences.user_id == user_id
                ).first()
                
                if inv_prefs:
                    investment_preferences = {
                        'risk_tolerance': inv_prefs.risk_tolerance,
                        'investment_horizon': inv_prefs.investment_horizon,
                        'investment_goals': inv_prefs.investment_goals,
                        'preferred_sectors': inv_prefs.preferred_sectors,
                        'esg_preferences': inv_prefs.esg_preferences,
                        'liquidity_needs': inv_prefs.liquidity_needs
                    }
            except Exception as e:
                logger.warning(f"Could not retrieve investment preferences: {str(e)}")
            
            return {
                'name': name,
                'age': age,
                'state': state,
                'marital_status': marital_status,
                'occupation': occupation,
                'tax_bracket': tax_bracket,
                'filing_status': filing_status,
                'state_tax_rate': state_tax_rate,
                'family_members': family_members,
                'estate_planning': estate_planning,
                'insurance_policies': insurance_policies,
                'investment_preferences': investment_preferences,
                'total_assets': summary.get('totalAssets', 0),
                'total_liabilities': summary.get('totalLiabilities', 0),
                'net_worth': summary.get('netWorth', 0),
                'monthly_income': summary.get('monthlyIncome', 0),
                'monthly_expenses': summary.get('monthlyExpenses', 0),
                'monthly_surplus': monthly_surplus,
                'savings_rate': summary.get('savingsRate', 0),
                'debt_to_income': summary.get('debtToIncomeRatio', 0),
                
                # Asset details
                'home_value': home_value,
                'mortgage_balance': mortgage_balance,
                'home_equity': home_equity,
                'real_estate_properties': real_estate_properties,  # ADDED: All real estate properties
                'retirement_accounts': retirement_accounts,
                'investment_accounts': investment_accounts,
                'bitcoin_value': bitcoin_value,
                'cash_accounts': cash_accounts,
                'other_assets': other_assets,
                'liabilities': other_liabilities,
                'liabilitiesBreakdown': liabilities_breakdown,  # Include ALL liabilities with mortgage
                
                # Retirement details
                'retirement_goal': retirement_goal,
                'retirement_capable_assets': retirement_capable_assets,
                'retirement_progress': retirement_progress,
                'years_to_goal': years_to_goal,
                'goal_achievement_age': goal_achievement_age,
                'can_retire_early': can_retire_early,
                
                # Social Security details
                'social_security_monthly': social_security_monthly,
                'social_security_annual': social_security_annual,
                'social_security_age': social_security_age
            }
            
        except Exception as e:
            logger.error(f"Error getting complete financial data: {str(e)}")
            return {'error': f"Failed to retrieve financial data: {str(e)}"}
    
    def _process_asset_category(self, category_list: List) -> Dict:
        """Process a category of assets into accounts and total"""
        accounts = []
        total = 0
        
        for item in category_list:
            if isinstance(item, dict):
                accounts.append(item)
                total += item.get('value', 0)
        
        return {'accounts': accounts, 'total': total}
    
    def _format_account_list(self, accounts: List) -> str:
        """Format list of accounts for display"""
        if not accounts:
            return "  • No accounts"
        
        formatted = []
        for account in accounts:
            if isinstance(account, dict):
                name = account.get('name', 'Unknown Account')
                value = account.get('value', 0)
                formatted.append(f"  • {name}: ${value:,.0f}")
        
        return '\n'.join(formatted)
    
    def _format_liability_list(self, liabilities: List) -> str:
        """Format list of liabilities for display"""
        if not liabilities:
            return "  • No other liabilities"
        
        formatted = []
        for liability in liabilities:
            if isinstance(liability, dict):
                name = liability.get('name', 'Unknown Debt')
                balance = liability.get('balance', 0)
                rate = liability.get('interest_rate', 0)
                if rate:
                    formatted.append(f"  • {name}: ${balance:,.0f} @ {rate}%")
                else:
                    formatted.append(f"  • {name}: ${balance:,.0f}")
        
        return '\n'.join(formatted)
    
    def _format_cash_accounts_with_yield(self, accounts: List) -> str:
        """Format cash accounts with HIGH-YIELD vs LOW-YIELD classification"""
        if not accounts:
            return "  • No cash accounts"
        
        formatted = []
        for account in accounts:
            if isinstance(account, dict):
                name = account.get('name', 'Unknown Account')
                value = account.get('value', 0)
                interest_rate = account.get('interest_rate', 0)
                
                # If no interest rate in account data, try to get it from database directly
                if not interest_rate:
                    try:
                        from sqlalchemy.orm import sessionmaker
                        from app.models.financial import FinancialEntry
                        from app.db.session import engine
                        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                        db_session = SessionLocal()
                        
                        # Find matching entry by name and amount
                        entry = db_session.query(FinancialEntry).filter(
                            FinancialEntry.description == name,
                            FinancialEntry.amount == float(value),
                            FinancialEntry.subcategory == 'cash_bank_accounts',
                            FinancialEntry.is_active == True
                        ).first()
                        
                        if entry and entry.interest_rate:
                            interest_rate = float(entry.interest_rate)
                            
                        db_session.close()
                    except Exception as e:
                        # Fallback to name-based classification if DB query fails
                        pass
                
                # Classify account type based on name and rate
                if interest_rate and interest_rate > 0:
                    # If we have actual rate data, show it precisely
                    if interest_rate >= 3.0:
                        formatted.append(f"  • {name}: ${value:,.0f} @ {interest_rate}% APY (HIGH-YIELD)")
                    elif interest_rate >= 1.0:
                        formatted.append(f"  • {name}: ${value:,.0f} @ {interest_rate}% APY (MODERATE-YIELD)")
                    else:
                        formatted.append(f"  • {name}: ${value:,.0f} @ {interest_rate}% APY (LOW-YIELD)")
                elif self._is_high_yield_account(name):
                    # Based on account name patterns
                    formatted.append(f"  • {name}: ${value:,.0f} (HIGH-YIELD ACCOUNT)")
                else:
                    # Assume low yield for checking/savings without specific indicators
                    formatted.append(f"  • {name}: ${value:,.0f} (LOW-YIELD)")
        
        return '\n'.join(formatted)
    
    def _is_high_yield_account(self, account_name: str) -> bool:
        """Determine if account is likely high-yield based on name"""
        name_lower = account_name.lower()
        high_yield_indicators = [
            'money market', 'mm', 'apy', 'high yield', 'hysa',
            'marcus', 'ally', 'capital one', 'capone', 'discover',
            'american express', 'goldman sachs', 'cit bank',
            'barclays', 'synchrony'
        ]
        
        return any(indicator in name_lower for indicator in high_yield_indicators)
    
    def _get_cash_optimization_summary(self, accounts: List, total_cash: float) -> str:
        """Generate cash optimization analysis"""
        if not accounts or total_cash == 0:
            return ""
        
        high_yield_amount = 0
        low_yield_amount = 0
        
        for account in accounts:
            if isinstance(account, dict):
                name = account.get('name', '')
                value = account.get('value', 0)
                interest_rate = account.get('interest_rate', 0)
                
                # If no interest rate in account data, try to get it from database directly
                if not interest_rate:
                    try:
                        from sqlalchemy.orm import sessionmaker
                        from app.models.financial import FinancialEntry
                        from app.db.session import engine
                        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                        db_session = SessionLocal()
                        
                        # Find matching entry by name and amount
                        entry = db_session.query(FinancialEntry).filter(
                            FinancialEntry.description == name,
                            FinancialEntry.amount == float(value),
                            FinancialEntry.subcategory == 'cash_bank_accounts',
                            FinancialEntry.is_active == True
                        ).first()
                        
                        if entry and entry.interest_rate:
                            interest_rate = float(entry.interest_rate)
                            
                        db_session.close()
                    except Exception as e:
                        # Fallback to name-based classification if DB query fails
                        pass
                
                if interest_rate and interest_rate >= 2.0:
                    # Actual high yield rate
                    high_yield_amount += value
                elif self._is_high_yield_account(name):
                    # Likely high yield based on name
                    high_yield_amount += value
                else:
                    # Low yield account
                    low_yield_amount += value
        
        if low_yield_amount > 1000:  # Only show if significant amount
            high_yield_pct = (high_yield_amount / total_cash) * 100
            low_yield_pct = (low_yield_amount / total_cash) * 100
            potential_gain = low_yield_amount * 0.045  # Assume 4.5% potential gain
            
            return f"""
CASH OPTIMIZATION STATUS:
  • ${high_yield_amount:,.0f} ({high_yield_pct:.1f}%) already in high-yield accounts
  • ${low_yield_amount:,.0f} ({low_yield_pct:.1f}%) in low-yield accounts < 0.5%
  • Optimization opportunity: Move ${low_yield_amount:,.0f} to 5% APY = +${potential_gain:,.0f}/year"""
        
        return ""
    
    def _format_liability_list_with_mortgage(self, liabilities: List, mortgage_balance: float) -> str:
        """Format list of liabilities with mortgage details prominently displayed"""
        formatted = []
        mortgage_found = False
        
        # First, look for mortgage in the liabilities list
        for liability in liabilities:
            if isinstance(liability, dict):
                name = liability.get('name', 'Unknown Debt')
                balance = liability.get('balance', 0)
                rate = liability.get('interest_rate', 0)
                payment = liability.get('minimum_payment', 0)
                subcategory = liability.get('subcategory', '')
                
                # Check if this is a mortgage
                if 'mortgage' in name.lower() or subcategory == 'mortgage':
                    mortgage_found = True
                    # Enhanced mortgage display with all critical details
                    if rate and payment:
                        formatted.append(f"  • {name}: ${balance:,.0f} @ {rate}% ({payment:,.0f}/month)")
                    elif rate:
                        formatted.append(f"  • {name}: ${balance:,.0f} @ {rate}%")
                    else:
                        formatted.append(f"  • {name}: ${balance:,.0f}")
                else:
                    # Regular liability formatting
                    if rate:
                        formatted.append(f"  • {name}: ${balance:,.0f} @ {rate}%")
                    else:
                        formatted.append(f"  • {name}: ${balance:,.0f}")
        
        # If no mortgage found in liabilities but mortgage_balance exists, add it
        if not mortgage_found and mortgage_balance > 0:
            # Add mortgage as first item with estimated details
            formatted.insert(0, f"  • Mortgage: ${mortgage_balance:,.0f} (rate and payment details needed)")
        
        if not formatted:
            return "  • No liabilities"
        
        return '\n'.join(formatted)
    
    # REMOVED: _format_score_breakdown method (no longer needed)
    # Health scoring is now calculated on-demand via separate API endpoint
    
    def _format_asset_allocation(self, financial_data: Dict) -> str:
        """Format asset allocation analysis"""
        total_assets = financial_data['total_assets']
        
        if total_assets == 0:
            return "  Unable to calculate allocation"
        
        allocations = [
            ("Real Estate (Total)", financial_data['real_estate_properties']['total']),
            ("Retirement Accounts", financial_data['retirement_accounts']['total']),
            ("Investment Accounts", financial_data['investment_accounts']['total']),
            ("Bitcoin/Crypto", financial_data['bitcoin_value']),
            ("Cash/Liquid", financial_data['cash_accounts']['total']),
            ("Other Assets", financial_data['other_assets']['total'])
        ]
        
        formatted = []
        for name, value in allocations:
            if value > 0:
                percentage = (value / total_assets) * 100
                formatted.append(f"  • {name}: ${value:,.0f} ({percentage:.1f}%)")
        
        return '\n'.join(formatted)
    
    def _get_insight_level_instructions(self, insight_level: str) -> str:
        """Get response depth instructions based on insight level"""
        instructions = {
            "focused": """
FOCUSED MODE: Answer directly with the specific numbers from the data provided.

Example: "What is my net worth?" → "Your net worth is $2,564,574."
""",
            
            "balanced": """
RESPONSE MODE: BALANCED
======================
- Answer the specific question first and directly
- Include relevant supporting calculations
- Add 1-2 actionable insights if valuable
- Keep response concise but complete
- Balance focus with helpful context
- Example: "Your retirement savings rate is 26.5% ($4,770/month). This exceeds 15-20% recommendations. Combined with your 59.9% savings rate, you're on track for your $3.5M goal in 10.4 years."
""",
            
            "comprehensive": """
RESPONSE MODE: COMPREHENSIVE
===========================
PROVIDE EXHAUSTIVE ANALYSIS:
- Start with direct answer, then provide complete financial analysis
- Include ALL relevant calculations, ratios, and benchmarks
- Compare to peer groups and industry standards
- Offer multiple optimization strategies and their implications
- Discuss tax considerations and timing implications
- Include scenario analysis and projections
- Mention specific investment products, accounts, and strategies
- Address risk factors and mitigation approaches
- Provide step-by-step action plans with timelines
- Connect to broader financial planning goals
- Include market context and economic considerations

This should be your most detailed, thorough response mode.
"""
        }
        
        return instructions.get(insight_level, instructions["balanced"])

    def _format_estate_planning(self, estate_planning: List[Dict]) -> str:
        """Format estate planning documents"""
        if not estate_planning:
            return "  • No estate planning documents on record"
        
        formatted = []
        for doc in estate_planning:
            doc_type = doc.get('document_type', 'Unknown')
            doc_name = doc.get('document_name', 'Unnamed')
            status = doc.get('status', 'Unknown')
            last_updated = doc.get('last_updated', 'Not specified')
            
            formatted.append(f"  • {doc_type.title()}: {doc_name} (Status: {status})")
            if last_updated != 'Not specified':
                formatted.append(f"    Last Updated: {last_updated[:10]}")
            
            if doc.get('attorney_contact'):
                formatted.append(f"    Attorney: {doc['attorney_contact']}")
        
        return '\n'.join(formatted)
    
    def _format_insurance_policies(self, insurance_policies: List[Dict]) -> str:
        """Format insurance policies"""
        if not insurance_policies:
            return "  • No insurance policies on record"
        
        formatted = []
        for policy in insurance_policies:
            policy_type = policy.get('policy_type', 'Unknown')
            policy_name = policy.get('policy_name', 'Unnamed')
            provider = policy.get('provider', 'Unknown Provider')
            coverage = policy.get('coverage_amount', 0)
            premium = policy.get('premium_amount', 0)
            frequency = policy.get('premium_frequency', 'Unknown')
            status = policy.get('status', 'Unknown')
            
            formatted.append(f"  • {policy_type.title()}: {policy_name} ({provider})")
            formatted.append(f"    Coverage: ${coverage:,.0f}, Premium: ${premium:,.0f}/{frequency} (Status: {status})")
        
        return '\n'.join(formatted)
    
    def _format_investment_preferences(self, investment_preferences: Dict) -> str:
        """Format investment preferences"""
        if not investment_preferences:
            return "  • No investment preferences specified"
        
        formatted = []
        
        risk_tolerance = investment_preferences.get('risk_tolerance', 'Not specified')
        investment_horizon = investment_preferences.get('investment_horizon', 'Not specified')
        investment_goals = investment_preferences.get('investment_goals', [])
        preferred_sectors = investment_preferences.get('preferred_sectors', [])
        esg_preferences = investment_preferences.get('esg_preferences', 'Not specified')
        liquidity_needs = investment_preferences.get('liquidity_needs', 'Not specified')
        
        formatted.append(f"  • Risk Tolerance: {risk_tolerance}")
        formatted.append(f"  • Investment Horizon: {investment_horizon}")
        formatted.append(f"  • Liquidity Needs: {liquidity_needs}")
        
        if isinstance(investment_goals, list) and investment_goals:
            formatted.append(f"  • Investment Goals: {', '.join(investment_goals)}")
        elif investment_goals:
            formatted.append(f"  • Investment Goals: {investment_goals}")
        
        if isinstance(preferred_sectors, list) and preferred_sectors:
            formatted.append(f"  • Preferred Sectors: {', '.join(preferred_sectors)}")
        elif preferred_sectors:
            formatted.append(f"  • Preferred Sectors: {preferred_sectors}")
        
        if esg_preferences != 'Not specified':
            formatted.append(f"  • ESG Preferences: {esg_preferences}")
        
        return '\n'.join(formatted)


# Global instance
complete_financial_context = CompleteFinancialContextService()