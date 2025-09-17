"""
Complete Financial Context Service
Provides the COMPLETE financial picture with all details and accurate calculations
No more asking for data we already have!
"""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
import logging
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)


class CompleteFinancialContextService:
    """Service that provides the COMPLETE financial picture"""
    
    def build_complete_context(self, user_id: int, db: Session, user_query: str = "", insight_level: str = "balanced") -> str:
        """Build complete context with financial data AND conversation memory"""
        try:
            # Get complete financial data
            financial_data = self._get_complete_financial_data(user_id, db)
            
            if 'error' in financial_data:
                return f"Error loading financial data: {financial_data['error']}"
            
            # Build financial context only (memory handled at endpoint level)
            return self._build_financial_context(
                financial_data, 
                user_query, 
                insight_level
            )
            
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
  • Occupation: {financial_data.get('occupation', 'Unknown')}"""
                
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

TAX PROFILE:
-----------
{self._format_tax_profile(financial_data)}

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

KEY FINANCIAL METRICS:
----------------------
{self._format_key_financial_metrics(financial_data)}

MONTHLY CASH FLOW:
-----------------
Income Breakdown:
{self._format_income_breakdown(financial_data.get('income_breakdown', []))}
  • Total Monthly Income: ${financial_data['monthly_income']:,.0f}
  
Expense Breakdown:
{self._format_expense_breakdown(financial_data.get('expense_breakdown', []))}
  • Total Monthly Expenses: ${financial_data['monthly_expenses']:,.0f}
  
Net Surplus: ${financial_data['monthly_surplus']:,.0f} ({financial_data.get('savings_rate', 0):.1f}% savings rate)

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
    
    def _get_chat_memory(self, user_id: int, db: Session) -> Dict:
        """Retrieve conversation history and session memory"""
        try:
            from ..models.chat import ChatMessage, ChatSession
            from .simple_vector_store import get_vector_store
            
            # Get recent messages from ChatMessage table (newest first)
            recent_messages = db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id
            ).order_by(ChatMessage.created_at.desc()).limit(20).all()  # Get 20 to have 10 exchanges
            
            # Pair them into conversations (user + assistant) - handle DESC order properly
            recent_chats = []
            user_msg = None
            assistant_msg = None
            
            for message in recent_messages:
                if message.role == 'user' and user_msg is None:
                    user_msg = message
                elif message.role == 'assistant' and assistant_msg is None:
                    assistant_msg = message
                
                # When we have both, create the conversation pair
                if user_msg and assistant_msg:
                    # Ensure they're from the same conversation (within reasonable time)
                    time_diff = abs((user_msg.created_at - assistant_msg.created_at).total_seconds())
                    if time_diff < 300:  # Within 5 minutes
                        recent_chats.append({
                            'user_message': user_msg.content,
                            'assistant_response': assistant_msg.content,
                            'created_at': max(user_msg.created_at, assistant_msg.created_at)
                        })
                    user_msg = None
                    assistant_msg = None
                    
                    if len(recent_chats) >= 10:  # Limit to 10 conversation pairs
                        break
            
            # Get chat intelligence from vector store
            vector_store = get_vector_store()
            chat_intelligence = vector_store.get_document(f"user_{user_id}_chat_intelligence")
            
            memory = {
                'recent_conversations': [],
                'key_decisions': [],
                'user_preferences': [],
                'pending_actions': []
            }
            
            # Debug logging
            logger.info(f"🧠 Memory retrieval for user {user_id}: found {len(recent_messages)} messages, {len(recent_chats)} conversation pairs")
            
            # Process conversations (already in reverse chronological order)
            for chat in recent_chats:
                memory['recent_conversations'].append({
                    'user': chat.get('user_message', '')[:200],  # Limit length
                    'assistant': chat.get('assistant_response', '')[:200],
                    'timestamp': chat.get('created_at').isoformat() if chat.get('created_at') and hasattr(chat.get('created_at'), 'isoformat') else str(chat.get('created_at', ''))
                })
            
            # Extract intelligence if available
            if chat_intelligence and hasattr(chat_intelligence, 'content') and isinstance(chat_intelligence.content, str):
                try:
                    import json
                    content = json.loads(chat_intelligence.content)
                    memory['key_decisions'] = content.get('financial_decisions', [])[:5]
                    memory['user_preferences'] = content.get('stated_preferences', [])[:5]
                    memory['pending_actions'] = content.get('action_items', [])[:5]
                except json.JSONDecodeError:
                    pass
            
            return memory
            
        except Exception as e:
            logger.warning(f"Could not retrieve chat memory: {str(e)}")
            return {'recent_conversations': [], 'key_decisions': [], 'user_preferences': [], 'pending_actions': []}

    def _build_financial_context(self, financial_data: Dict, user_query: str, insight_level: str) -> str:
        """Build financial context that FORCES specific data usage"""
        
        # Calculate key metrics for enforcement
        total_assets = financial_data.get('total_assets', 0)
        if total_assets > 0:
            real_estate_pct = (financial_data['real_estate_properties']['total'] / total_assets) * 100
            investment_pct = (financial_data['investment_accounts']['total'] / total_assets) * 100
            retirement_pct = (financial_data['retirement_accounts']['total'] / total_assets) * 100
            cash_pct = (financial_data['cash_accounts']['total'] / total_assets) * 100
        else:
            real_estate_pct = investment_pct = retirement_pct = cash_pct = 0
        
        # Build the financial context with strict enforcement
        context = f"""===========================================================
MANDATORY DATA USAGE REQUIREMENTS
===========================================================
YOU MUST use these EXACT numbers in your response:

WEALTH METRICS:
- Net Worth: ${financial_data['net_worth']:,.0f}
- Monthly Income: ${financial_data['monthly_income']:,.0f}
- Monthly Expenses: ${financial_data['monthly_expenses']:,.0f}
- Monthly Surplus: ${financial_data['monthly_surplus']:,.0f}
- Savings Rate: {financial_data.get('savings_rate', 0):.1f}%

ASSET ALLOCATION (MUST reference for portfolio questions):
- Real Estate: {real_estate_pct:.1f}% (${financial_data['real_estate_properties']['total']:,.0f})
- Investments: {investment_pct:.1f}% (${financial_data['investment_accounts']['total']:,.0f})
- Retirement: {retirement_pct:.1f}% (${financial_data['retirement_accounts']['total']:,.0f})
- Cash: {cash_pct:.1f}% (${financial_data['cash_accounts']['total']:,.0f})

RETIREMENT STATUS:
- Goal: ${financial_data['retirement_goal']:,.0f}
- Progress: {financial_data['retirement_progress']:.1f}%
- Years to Goal: {financial_data['years_to_goal']:.1f}
- Social Security: ${financial_data.get('social_security_monthly', 0):,.0f}/month (${financial_data.get('social_security_annual', 0):,.0f}/year) starting at age {financial_data.get('social_security_age', 67)}

STANDARD FINANCIAL PLANNING ASSUMPTIONS (USE THESE FOR ALL CALCULATIONS):
- Investment Growth Rate: 7% annually (long-term stock market average)
- Conservative Growth Rate: 5% annually (for conservative projections)
- Inflation Rate: 3% annually (Federal Reserve target)
- Safe Withdrawal Rate: 4% annually (4% rule for retirement)
- Healthcare Cost Growth: 6% annually (above general inflation)
- Real Estate Appreciation: 3-4% annually (matches inflation)
- Cash/CD Rates: 4.5-5.0% APY (current high-yield savings)
- Emergency Fund: 6-12 months of expenses recommended
- Retirement Income Need: 70-80% of pre-retirement income
- 80% Rule: Assume retirement expenses = 80% of current monthly expenses (${int(financial_data['monthly_expenses'] * 0.8):,}/month)

RETIREMENT CALCULATION METHODOLOGY:
CRITICAL: Social Security benefits of ${financial_data.get('social_security_monthly', 0):,.0f}/month do NOT start until age {financial_data.get('social_security_age', 67)}!

PHASE 1 - EARLY RETIREMENT (Before Age {financial_data.get('social_security_age', 67)}):
1. Monthly retirement need: ${int(financial_data['monthly_expenses'] * 0.8):,}/month (NO Social Security yet)
2. Annual need from savings ONLY: ${int(financial_data['monthly_expenses'] * 0.8) * 12:,.0f}
3. Total savings needed for early retirement: ${(int(financial_data['monthly_expenses'] * 0.8) * 12) / 0.04:,.0f}

PHASE 2 - FULL RETIREMENT (After Age {financial_data.get('social_security_age', 67)}):
1. Monthly retirement need: ${int(financial_data['monthly_expenses'] * 0.8):,}/month - ${financial_data.get('social_security_monthly', 0):,.0f}/month (SS) = ${int(financial_data['monthly_expenses'] * 0.8) - financial_data.get('social_security_monthly', 0):,.0f}/month from savings
2. Annual need from savings with SS: ${(int(financial_data['monthly_expenses'] * 0.8) - financial_data.get('social_security_monthly', 0)) * 12:,.0f}
3. Total savings needed with SS: ${((int(financial_data['monthly_expenses'] * 0.8) - financial_data.get('social_security_monthly', 0)) * 12) / 0.04:,.0f}

CURRENT SITUATION:
4. Current liquid assets: ${financial_data['retirement_accounts']['total'] + financial_data['investment_accounts']['total']:,.0f}
5. Current age: {financial_data.get('age', 54)}
6. With ${financial_data['monthly_surplus']:,.0f}/month savings at 7% growth: CALCULATE YEARS TO EACH RETIREMENT PHASE

STEP-BY-STEP CALCULATION EXAMPLE FOR "WHEN CAN I RETIRE?":
ALWAYS SHOW THE ACTUAL MATH - DO NOT JUST SAY "approximately X years":

OPTION 1: EARLY RETIREMENT (Before Age {financial_data.get('social_security_age', 67)} - NO Social Security):
Step 1a: Early retirement gap calculation
- Need for early retirement: ${(int(financial_data['monthly_expenses'] * 0.8) * 12) / 0.04:,.0f}
- Have: ${financial_data['retirement_accounts']['total'] + financial_data['investment_accounts']['total']:,.0f}
- Early retirement gap: ${(int(financial_data['monthly_expenses'] * 0.8) * 12) / 0.04 - (financial_data['retirement_accounts']['total'] + financial_data['investment_accounts']['total']):,.0f}

Step 2a: Calculate years to early retirement (if gap > 0):
- Formula: ln(1 + (Gap × 0.07)/(Monthly_savings × 12)) / ln(1.07)
- Early retirement age: Current age {financial_data.get('age', 54)} + calculated years

OPTION 2: FULL RETIREMENT (Age {financial_data.get('social_security_age', 67)}+ with Social Security):
Step 1b: Full retirement gap calculation  
- Need with SS: ${((int(financial_data['monthly_expenses'] * 0.8) - financial_data.get('social_security_monthly', 0)) * 12) / 0.04:,.0f}
- Have: ${financial_data['retirement_accounts']['total'] + financial_data['investment_accounts']['total']:,.0f}
- Full retirement gap: ${((int(financial_data['monthly_expenses'] * 0.8) - financial_data.get('social_security_monthly', 0)) * 12) / 0.04 - (financial_data['retirement_accounts']['total'] + financial_data['investment_accounts']['total']):,.0f}

Step 2b: Calculate years to full retirement (if gap > 0):
- Full retirement age: Current age {financial_data.get('age', 54)} + calculated years (minimum age {financial_data.get('social_security_age', 67)})

CRITICAL: If current age + calculated years < {financial_data.get('social_security_age', 67)}, user must wait until {financial_data.get('social_security_age', 67)} for Social Security benefits!

ALWAYS SHOW THESE ACTUAL CALCULATIONS - NO SHORTCUTS OR "APPROXIMATELY"

{self._get_conditional_stress_testing(financial_data, user_query)}

===========================================================
USER'S CURRENT QUESTION: {user_query}
===========================================================

RESPONSE REQUIREMENTS:
1. Use at least 3 specific numbers from above
2. Reference previous conversations if relevant
3. For portfolio questions, MUST mention {real_estate_pct:.1f}% real estate allocation
4. For retirement questions, MUST mention Social Security: ${financial_data.get('social_security_monthly', 0):,.0f}/month
5. ALWAYS use the Standard Financial Planning Assumptions above - NEVER ask for rates
6. For retirement calculations, use 7% growth, 3% inflation, 4% withdrawal rate, and 80% expense rule
7. CALCULATE actual retirement dates/years - don't say "requires more analysis"
8. SHOW ALL ARITHMETIC: Do the math step-by-step, don't say "approximately X years"
9. BE DECISIVE: Give specific numbers and timelines, not vague recommendations
10. STRESS TEST CALCULATIONS: For market crash/negative scenarios, USE THE DATA YOU HAVE - don't ask for more info
11. Build on any decisions or preferences from chat history
12. NO generic advice without specific numbers

===========================================================
"""
        
        # Add detailed financial data based on insight level
        if insight_level == "focused":
            context += self._get_focused_details(financial_data)
        elif insight_level == "comprehensive":
            context += self._get_comprehensive_details(financial_data)
        else:  # balanced
            context += self._get_balanced_details(financial_data)
        
        # Add validation footer
        context += f"""

===========================================================
PRE-RESPONSE VALIDATION CHECKLIST
===========================================================
Before responding, verify:
□ Used at least 3 specific dollar amounts or percentages
□ Referenced conversation history if relevant
□ For portfolio questions: mentioned {real_estate_pct:.1f}% real estate
□ For retirement questions: mentioned Social Security ${financial_data.get('social_security_monthly', 0):,.0f}/month
□ Used standard assumptions (7% growth, 3% inflation, 4% withdrawal, 80% expenses) - NO rate requests
□ For retirement timing questions: PROVIDED SPECIFIC YEAR/DATE - not "requires analysis"
□ CALCULATED results using the methodology above - showed the math step-by-step
□ NO "approximately" or shortcuts - showed actual arithmetic calculations
□ Maintained consistency with previous advice
□ Direct answer to: {user_query}

FAILURE TO USE SPECIFIC DATA = INVALID RESPONSE

PEER COMPARISON INSTRUCTIONS:
When asked about peer comparisons, use the provided financial data and your knowledge of typical demographics.
- NEVER say "I don't have access to peer data" - you have the user's complete financial profile
- Use general demographic knowledge for age group {financial_data.get('age', 54)} comparisons
- Reference specific user metrics: ${financial_data['net_worth']:,.0f} net worth, {financial_data.get('savings_rate', 0):.1f}% savings rate, ${financial_data['monthly_surplus']:,.0f} monthly surplus
- Provide percentile estimates and specific insights about their financial position
- Use phrases like "based on typical demographics" rather than claiming lack of data

NOTE: Only include stress testing calculations if user specifically asks about market crashes, downturns, or risk scenarios.
==========================================================="""
        
        # CRITICAL DEBUG - Show what's being returned
        print(f"🔥 FINAL CONTEXT DEBUG - Context length: {len(context)} characters")
        print(f"🔥 FINAL CONTEXT DEBUG - Contains CRITICAL INSTRUCTION: {'CRITICAL INSTRUCTION' in context}")
        print(f"🔥 FINAL CONTEXT DEBUG - Contains STRESS TESTING: {'🚨 CRITICAL INSTRUCTION: USER IS ASKING ABOUT MARKET CRASH SCENARIOS' in context}")
        print(f"🔥 FINAL CONTEXT DEBUG - Last 200 characters: ...{context[-200:]}")
        
        return context

    def _get_focused_details(self, financial_data: Dict) -> str:
        """Minimal essential data for quick responses"""
        return f"""
ESSENTIAL DATA:
- Client: {financial_data['name']}, Age {financial_data['age']}, {financial_data['state']}
- Net Worth: ${financial_data['net_worth']:,.0f}
- Cash Flow: +${financial_data['monthly_surplus']:,.0f}/month
- Liquid Assets: ${financial_data['cash_accounts']['total']:,.0f}
"""

    def _get_balanced_details(self, financial_data: Dict) -> str:
        """Standard financial details"""
        expense_breakdown = financial_data.get('expense_breakdown', [])
        all_expenses = []
        itemized_total = 0
        
        # Show ALL expense categories, not just top 5
        for category in expense_breakdown:
            name = category.get('category', 'Unknown')
            amount = category.get('monthly_amount', 0)
            itemized_total += amount
            # Show subcategory items for housing/other
            if name == 'Housing & Other' and category.get('items'):
                for item in category['items']:
                    all_expenses.append(f"  • {item['description']}: ${item['monthly_amount']:,.0f}")
            else:
                all_expenses.append(f"  • {name}: ${amount:,.0f}")
        
        # Verify total matches
        total_expenses = financial_data.get('monthly_expenses', 0)
        if abs(itemized_total - total_expenses) > 1:  # Allow $1 rounding difference
            all_expenses.append(f"  • [Note: Itemized ${itemized_total:,.0f} vs Total ${total_expenses:,.0f}]")
        
        return f"""
COMPLETE FINANCIAL PROFILE:
- {financial_data['name']}, Age {financial_data['age']}, {financial_data['state']}
- {financial_data['marital_status']}, {financial_data['filing_status']}
- Tax Bracket: {financial_data.get('tax_bracket', 'Unknown')}%

EXPENSE BREAKDOWN (Total: ${total_expenses:,.0f}/month):
{chr(10).join(all_expenses) if all_expenses else '  • No breakdown available'}

LIABILITIES:
- Mortgage: ${financial_data.get('mortgage_balance', 0):,.0f}
- Other Debt: ${financial_data.get('total_liabilities', 0) - financial_data.get('mortgage_balance', 0):,.0f}
"""

    def _get_comprehensive_details(self, financial_data: Dict) -> str:
        """Full detailed analysis"""
        # Include everything from balanced plus additional details
        balanced = self._get_balanced_details(financial_data)
        
        return balanced + f"""

DETAILED ACCOUNTS:
{self._format_account_list(financial_data.get('retirement_accounts', {}).get('accounts', []))}
{self._format_account_list(financial_data.get('investment_accounts', {}).get('accounts', []))}

INSURANCE & ESTATE:
{self._format_insurance_policies(financial_data.get('insurance_policies', []))}
{self._format_estate_planning(financial_data.get('estate_planning', []))}
"""

    def _format_account_list(self, accounts: List) -> str:
        """Format account list for display"""
        if not accounts:
            return "  • No accounts found"
        
        result = ""
        for account in accounts:
            result += f"  • {account.get('name', 'Unknown')}: ${account.get('balance', 0):,.0f}\n"
        return result

    def _format_insurance_policies(self, policies: List) -> str:
        """Format insurance policies for display"""
        if not policies:
            return "  • No insurance policies on file"
        
        result = ""
        for policy in policies:
            result += f"  • {policy.get('type', 'Unknown')}: {policy.get('coverage_amount', 'Unknown')} coverage\n"
        return result

    def _format_estate_planning(self, estate_items: List) -> str:
        """Format estate planning items for display"""
        if not estate_items:
            return "  • No estate planning documents on file"
        
        result = ""
        for item in estate_items:
            result += f"  • {item.get('type', 'Unknown')}: {item.get('description', 'No description')}\n"
        return result

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
            
            # Get retirement goal - PRIORITY ORDER:
            # 1. User's actual goals from financial_goals table
            # 2. User's profile retirement_goal (if set)
            # 3. Safe fallback for calculation purposes
            retirement_goals = db.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.name.ilike('%retirement%')
            ).all()
            
            retirement_goal = None
            target_date = None
            retirement_age_target = 65  # Default
            
            # Priority 1: Use database goals if available
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
            
            # Priority 2: Use profile retirement goal if no database goal exists
            elif profile and profile.retirement_goal:
                retirement_goal = float(profile.retirement_goal)
                
            # Priority 3: Safe fallback based on user's current financial situation
            else:
                # Calculate reasonable retirement goal based on user's actual expenses
                monthly_expenses = summary.get('monthlyExpenses', 7500)  # Use actual or reasonable default
                # Standard rule: 25x annual expenses for 4% withdrawal rate
                retirement_goal = monthly_expenses * 12 * 25  # Safe, personalized estimate
            
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
            
            # Get Social Security benefits - PRIORITY ORDER:
            # 1. User benefits table (if exists and populated)
            # 2. Profile social_security_monthly (if set)
            # 3. Reasonable estimate based on income
            social_security_monthly = 0
            social_security_annual = 0
            social_security_age = 67
            
            try:
                # Priority 1: Check user benefits table
                from ..models.user_profile import UserBenefit
                ss_benefits = db.query(UserBenefit).join(UserProfile).filter(
                    UserProfile.user_id == user_id,
                    UserBenefit.benefit_type == 'social_security'
                ).first()
                
                if ss_benefits and ss_benefits.estimated_monthly_benefit:
                    social_security_monthly = float(ss_benefits.estimated_monthly_benefit)
                    social_security_annual = social_security_monthly * 12
                    social_security_age = ss_benefits.full_retirement_age or 67
                    
                # Priority 2: Check profile estimate
                elif profile and profile.social_security_monthly:
                    social_security_monthly = float(profile.social_security_monthly)
                    social_security_annual = social_security_monthly * 12
                    social_security_age = profile.social_security_age or 67
                    
                # Priority 3: Reasonable estimate based on income
                else:
                    # Rough SS estimate: ~40% of average earnings up to SS max
                    monthly_income = summary.get('monthlyIncome', 0)
                    if monthly_income > 0:
                        # Cap at roughly Social Security maximum benefit level
                        estimated_replacement = min(monthly_income * 0.4, 4500)  # Reasonable SS max
                        social_security_monthly = max(1000, estimated_replacement)  # Min of $1k/month
                    else:
                        social_security_monthly = 2000  # Very conservative fallback
                    social_security_annual = social_security_monthly * 12
                    social_security_age = 67
                    
            except Exception as e:
                logger.warning(f"Could not retrieve Social Security benefits: {str(e)}")
                # Safe fallback
                social_security_monthly = 2000
                social_security_annual = 24000
                social_security_age = 67
            
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
                logger.info(f"🏛️ Estate Planning debug: Querying UserEstatePlanning for user_id {user_id}")

                estate_docs = db.query(UserEstatePlanning).filter(
                    UserEstatePlanning.user_id == user_id
                ).all()

                logger.info(f"🏛️ Estate Planning debug: Found {len(estate_docs)} estate planning documents")

                for doc in estate_docs:
                    logger.info(f"🏛️ Estate Planning debug: Processing document {doc.document_type} - {doc.document_name}")
                    estate_planning.append({
                        'document_type': doc.document_type,
                        'document_name': doc.document_name,
                        'status': doc.status,
                        'last_updated': doc.last_updated.isoformat() if doc.last_updated else None,
                        'attorney_contact': doc.attorney_contact,
                        'document_location': doc.document_location,
                        'document_details': doc.document_details
                    })

                logger.info(f"🏛️ Estate Planning debug: Final estate_planning list has {len(estate_planning)} items")

            except Exception as e:
                logger.warning(f"Could not retrieve estate planning information: {str(e)}")
            
            try:
                from ..models.insurance import UserInsurancePolicy
                logger.info(f"🔍 Insurance debug: Querying UserInsurancePolicy for user_id {user_id}")

                insurance_docs = db.query(UserInsurancePolicy).filter(
                    UserInsurancePolicy.user_id == user_id
                ).all()

                logger.info(f"🔍 Insurance debug: Found {len(insurance_docs)} insurance policies")

                for policy in insurance_docs:
                    logger.info(f"🔍 Insurance debug: Processing policy {policy.policy_type} - {policy.policy_name}")
                    insurance_policies.append({
                        'policy_type': policy.policy_type,
                        'policy_name': policy.policy_name,
                        'coverage_amount': float(policy.coverage_amount) if policy.coverage_amount else 0,
                        'annual_premium': float(policy.annual_premium) if policy.annual_premium else 0,
                        'beneficiary_primary': policy.beneficiary_primary,
                        'beneficiary_secondary': policy.beneficiary_secondary,
                        'policy_details': policy.policy_details
                    })

                logger.info(f"🔍 Insurance debug: Final insurance_policies list has {len(insurance_policies)} items")

            except Exception as e:
                logger.warning(f"Could not retrieve insurance information: {str(e)}")
                import traceback
                logger.warning(f"Insurance retrieval traceback: {traceback.format_exc()}")
            
            try:
                from ..models.investment_preferences import UserInvestmentPreferences
                inv_prefs = db.query(UserInvestmentPreferences).filter(
                    UserInvestmentPreferences.user_id == user_id
                ).first()
                
                if inv_prefs:
                    investment_preferences = {
                        'risk_tolerance_score': inv_prefs.risk_tolerance_score,
                        'investment_timeline_years': inv_prefs.investment_timeline_years,
                        'investment_philosophy': inv_prefs.investment_philosophy,
                        'esg_preference_level': inv_prefs.esg_preference_level,
                        'sector_preferences': inv_prefs.sector_preferences,
                        'rebalancing_frequency': inv_prefs.rebalancing_frequency,
                        'alternative_investment_interest': inv_prefs.alternative_investment_interest
                    }
            except Exception as e:
                logger.warning(f"Could not retrieve investment preferences: {str(e)}")

            # Debug: Check final data package before returning
            logger.info(f"📦 Final data package contains {len(estate_planning)} estate planning items")
            logger.info(f"📦 Final data package contains {len(insurance_policies)} insurance policies")
            logger.info(f"📦 Estate planning data: {estate_planning}")
            logger.info(f"📦 Insurance policies data: {insurance_policies}")

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
                'social_security_age': social_security_age,
                
                # Income and expense breakdowns
                'income_breakdown': self._get_income_breakdown(user_id, db),
                'expense_breakdown': self._get_expense_breakdown(user_id, db)
            }
            
        except Exception as e:
            logger.error(f"Error getting complete financial data: {str(e)}")
            return {'error': f"Failed to retrieve financial data: {str(e)}"}
    
    def _get_income_breakdown(self, user_id: int, db: Session) -> List[Dict]:
        """Get detailed income breakdown by category"""
        try:
            from ..models.financial import FinancialEntry, EntryCategory, FrequencyType
            from collections import defaultdict
            
            # Get all income entries
            income_entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id,
                FinancialEntry.is_active == True,
                FinancialEntry.category == EntryCategory.income
            ).all()
            
            # Group by subcategory
            income_by_category = defaultdict(list)
            for entry in income_entries:
                category = entry.subcategory or 'Other Income'
                
                # Convert to monthly amount
                monthly_amount = float(entry.amount)
                if entry.frequency == FrequencyType.annually:
                    monthly_amount = monthly_amount / 12
                elif entry.frequency == FrequencyType.weekly:
                    monthly_amount = monthly_amount * 52 / 12
                
                income_by_category[category].append({
                    'description': entry.description,
                    'monthly_amount': monthly_amount,
                    'frequency': entry.frequency.value
                })
            
            # Format for output
            breakdown = []
            for category, items in income_by_category.items():
                total_monthly = sum(item['monthly_amount'] for item in items)
                breakdown.append({
                    'category': category,
                    'monthly_amount': total_monthly,
                    'items': items
                })
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Error getting income breakdown: {str(e)}")
            return []
    
    def _get_expense_breakdown(self, user_id: int, db: Session) -> List[Dict]:
        """Get detailed expense breakdown by category"""
        try:
            from ..models.financial import FinancialEntry, EntryCategory, FrequencyType
            from collections import defaultdict
            
            # Get all expense entries
            expense_entries = db.query(FinancialEntry).filter(
                FinancialEntry.user_id == user_id,
                FinancialEntry.is_active == True,
                FinancialEntry.category == EntryCategory.expenses
            ).all()
            
            # Group by subcategory
            expense_by_category = defaultdict(list)
            for entry in expense_entries:
                category = entry.subcategory or 'Other Expenses'
                
                # Convert to monthly amount
                monthly_amount = float(entry.amount)
                if entry.frequency == FrequencyType.annually:
                    monthly_amount = monthly_amount / 12
                elif entry.frequency == FrequencyType.weekly:
                    monthly_amount = monthly_amount * 52 / 12
                
                expense_by_category[category].append({
                    'description': entry.description,
                    'monthly_amount': monthly_amount,
                    'frequency': entry.frequency.value
                })
            
            # Format for output
            breakdown = []
            for category, items in expense_by_category.items():
                total_monthly = sum(item['monthly_amount'] for item in items)
                breakdown.append({
                    'category': category,
                    'monthly_amount': total_monthly,
                    'items': items
                })
            
            # Add housing/other expenses if there's a gap between itemized and total expenses
            from ..services.financial_summary_service import financial_summary_service
            summary = financial_summary_service.get_user_financial_summary(user_id, db)
            
            if summary and 'monthlyExpenses' in summary:
                total_monthly_expenses = float(summary['monthlyExpenses'])
                itemized_total = sum(cat['monthly_amount'] for cat in breakdown)
                
                # If there's a gap, add it as housing/other expenses
                expense_gap = total_monthly_expenses - itemized_total
                if expense_gap > 0:
                    # Check for mortgage in liabilities
                    mortgage_payment = 0
                    if 'liabilitiesBreakdown' in summary:
                        for liability in summary['liabilitiesBreakdown']:
                            if 'mortgage' in str(liability.get('name', '')).lower():
                                # Estimate monthly mortgage payment (rough calculation)
                                balance = float(liability.get('balance', 0))
                                # Assume 30-year at 5% for estimation
                                if balance > 0:
                                    mortgage_payment = balance * 0.005  # Simplified estimate
                                    break
                    
                    # Add the gap as housing/other expenses
                    breakdown.append({
                        'category': 'Housing & Other',
                        'monthly_amount': expense_gap,
                        'items': [
                            {
                                'description': 'Mortgage/Rent' if mortgage_payment > 0 else 'Housing',
                                'monthly_amount': min(expense_gap, mortgage_payment * 2) if mortgage_payment > 0 else expense_gap * 0.6,
                                'frequency': 'monthly'
                            },
                            {
                                'description': 'Insurance & Other',
                                'monthly_amount': expense_gap - (min(expense_gap, mortgage_payment * 2) if mortgage_payment > 0 else expense_gap * 0.6),
                                'frequency': 'monthly'
                            }
                        ]
                    })
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Error getting expense breakdown: {str(e)}")
            return []

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
    
    def _get_conditional_stress_testing(self, financial_data: Dict, user_query: str) -> str:
        """Include stress testing calculations only when user asks for risk analysis"""
        # Expanded keywords that indicate user wants stress testing
        stress_keywords = [
            'stress test', 'stress testing', 'market crash', 'crash', 'recession', 'downturn', 
            'bear market', 'market decline', 'economic crisis', 'worst case', 'risk', 'risks',
            'volatility', 'what if', 'drop', 'fall', 'decline', 'lose value', 'loses value',
            'market correction', 'portfolio risk', 'economic downturn', 'financial crisis',
            'market volatility', 'market drop', 'portfolio crash', 'investment loss',
            'market tumble', 'economic collapse', 'bear scenario', 'negative scenario',
            'downside risk', 'market plunge', 'stock market crash', 'portfolio decline',
            'severe downturn', 'market tank', 'if markets fall', 'if market crashes',
            'if there is a crash', 'during a crash', 'economic recession', 'market meltdown'
        ]
        
        # Check if user query contains any stress testing keywords
        query_lower = user_query.lower()
        matched_keywords = [kw for kw in stress_keywords if kw in query_lower]
        
        # FORCE CRITICAL DEBUG - Always show even if no logs visible
        print(f"🔥 STRESS TEST DEBUG - Query: '{user_query}'")
        print(f"🔥 STRESS TEST DEBUG - Query Lower: '{query_lower}'") 
        print(f"🔥 STRESS TEST DEBUG - Matched keywords: {matched_keywords}")
        print(f"🔥 STRESS TEST DEBUG - Will include stress testing: {len(matched_keywords) > 0}")
        
        if not matched_keywords:
            print(f"🔥 STRESS TEST DEBUG - NO KEYWORDS MATCHED, RETURNING EMPTY")
            return ""
        
        print(f"🔥 STRESS TEST DEBUG - STRESS TESTING CONTEXT WILL BE ADDED")
        
        # Only include stress testing if specifically requested
        stress_content = f"""

===============================================================================
🚨 CRITICAL INSTRUCTION: USER IS ASKING ABOUT MARKET CRASH SCENARIOS 🚨
===============================================================================

IGNORE ALL GENERIC RESPONSES ABOUT MARKET CRASHES. DO NOT PROVIDE ACADEMIC EXPLANATIONS.

THE USER HAS COMPLETE FINANCIAL DATA PROVIDED BELOW. USE IT IMMEDIATELY.

MANDATORY RESPONSE FORMAT: Perform these exact calculations using the provided data.

CURRENT PORTFOLIO DATA TO USE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Total Investment Portfolio: ${financial_data['investment_accounts']['total'] + financial_data['retirement_accounts']['total']:,.0f}
• Real Estate Holdings: ${financial_data['real_estate_properties']['total']:,.0f}  
• Cash Reserves: ${financial_data['cash_accounts']['total']:,.0f}
• CURRENT NET WORTH: ${financial_data['net_worth']:,.0f}
• Monthly Surplus: ${financial_data['monthly_surplus']:,.0f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 PERFORM THESE EXACT CALCULATIONS - NO SUBSTITUTIONS ALLOWED:

📊 SCENARIO 1: MILD RECESSION (20% stock decline, 10% real estate)
   💸 Investment Loss: ${financial_data['investment_accounts']['total'] + financial_data['retirement_accounts']['total']:,.0f} × 20% = ${(financial_data['investment_accounts']['total'] + financial_data['retirement_accounts']['total']) * 0.20:,.0f}
   🏠 Real Estate Loss: ${financial_data['real_estate_properties']['total']:,.0f} × 10% = ${financial_data['real_estate_properties']['total'] * 0.10:,.0f}
   📉 TOTAL PORTFOLIO LOSS: ${(financial_data['investment_accounts']['total'] + financial_data['retirement_accounts']['total']) * 0.20 + financial_data['real_estate_properties']['total'] * 0.10:,.0f}
   💰 NET WORTH AFTER CRASH: ${financial_data['net_worth'] - (financial_data['investment_accounts']['total'] + financial_data['retirement_accounts']['total']) * 0.20 - financial_data['real_estate_properties']['total'] * 0.10:,.0f}

📊 SCENARIO 2: SEVERE CRASH (40% stock decline, 20% real estate)  
   💸 Investment Loss: ${financial_data['investment_accounts']['total'] + financial_data['retirement_accounts']['total']:,.0f} × 40% = ${(financial_data['investment_accounts']['total'] + financial_data['retirement_accounts']['total']) * 0.40:,.0f}
   🏠 Real Estate Loss: ${financial_data['real_estate_properties']['total']:,.0f} × 20% = ${financial_data['real_estate_properties']['total'] * 0.20:,.0f}
   📉 TOTAL PORTFOLIO LOSS: ${(financial_data['investment_accounts']['total'] + financial_data['retirement_accounts']['total']) * 0.40 + financial_data['real_estate_properties']['total'] * 0.20:,.0f}
   💰 NET WORTH AFTER CRASH: ${financial_data['net_worth'] - (financial_data['investment_accounts']['total'] + financial_data['retirement_accounts']['total']) * 0.40 - financial_data['real_estate_properties']['total'] * 0.20:,.0f}

📈 RECOVERY ANALYSIS:
   • Monthly recovery power: ${financial_data['monthly_surplus']:,.0f}/month
   • Annual savings capacity: ${financial_data['monthly_surplus'] * 12:,.0f}/year
   • Calculate exact recovery years for each scenario using compound growth at 7%

🎯 REQUIRED OUTPUT: Show impact on retirement timeline for BOTH scenarios.

DO NOT PROVIDE GENERIC MARKET CRASH THEORY. USE ONLY THE NUMBERS PROVIDED ABOVE.
===============================================================================
"""
        
        print(f"🔥 STRESS TEST DEBUG - Stress content length: {len(stress_content)}")
        print(f"🔥 STRESS TEST DEBUG - First 100 chars: {stress_content[:100]}...")
        
        return stress_content

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
        logger.info(f"🏛️ Estate Planning format debug: Received {len(estate_planning) if estate_planning else 0} documents")
        logger.info(f"🏛️ Estate Planning format debug: Documents data: {estate_planning}")

        if not estate_planning:
            logger.info("🏛️ Estate Planning format debug: No documents found, returning default message")
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
        logger.info(f"🔍 Insurance format debug: Received {len(insurance_policies) if insurance_policies else 0} policies")
        logger.info(f"🔍 Insurance format debug: Policies data: {insurance_policies}")

        if not insurance_policies:
            logger.info("🔍 Insurance format debug: No policies found, returning default message")
            return "  • No insurance policies on record"

        formatted = []
        for policy in insurance_policies:
            policy_type = policy.get('policy_type', 'Unknown')
            policy_name = policy.get('policy_name', 'Unnamed')
            coverage = policy.get('coverage_amount', 0)
            annual_premium = policy.get('annual_premium', 0)
            beneficiary_primary = policy.get('beneficiary_primary', 'Not specified')
            beneficiary_secondary = policy.get('beneficiary_secondary', 'Not specified')
            
            formatted.append(f"  • {policy_type.title()}: {policy_name}")
            formatted.append(f"    Coverage: ${coverage:,.0f}, Annual Premium: ${annual_premium:,.0f}")
            formatted.append(f"    Primary Beneficiary: {beneficiary_primary}")
            if beneficiary_secondary != 'Not specified':
                formatted.append(f"    Secondary Beneficiary: {beneficiary_secondary}")
        
        return '\n'.join(formatted)
    
    def _format_investment_preferences(self, investment_preferences: Dict) -> str:
        """Format investment preferences"""
        if not investment_preferences:
            return "  • No investment preferences specified"
        
        formatted = []
        
        risk_score = investment_preferences.get('risk_tolerance_score', 'Not specified')
        timeline_years = investment_preferences.get('investment_timeline_years', 'Not specified')
        philosophy = investment_preferences.get('investment_philosophy', 'Not specified')
        esg_level = investment_preferences.get('esg_preference_level', 'Not specified')
        sectors = investment_preferences.get('sector_preferences', 'Not specified')
        rebalancing = investment_preferences.get('rebalancing_frequency', 'Not specified')
        alternatives = investment_preferences.get('alternative_investment_interest', 'Not specified')
        
        formatted.append(f"  • Risk Tolerance Score: {risk_score}")
        formatted.append(f"  • Investment Timeline: {timeline_years} years")
        formatted.append(f"  • Investment Philosophy: {philosophy}")
        formatted.append(f"  • Rebalancing Frequency: {rebalancing}")
        
        if esg_level != 'Not specified':
            formatted.append(f"  • ESG Preference Level: {esg_level}")
        
        if sectors != 'Not specified' and sectors:
            formatted.append(f"  • Sector Preferences: {sectors}")
        
        if alternatives != 'Not specified':
            formatted.append(f"  • Alternative Investment Interest: {alternatives}")
        
        return '\n'.join(formatted)
    
    def _format_income_breakdown(self, income_breakdown: List[Dict]) -> str:
        """Format income breakdown by category"""
        if not income_breakdown:
            return "  • No income breakdown available"
        
        formatted = []
        for category in income_breakdown:
            category_name = category.get('category', 'Unknown')
            monthly_amount = category.get('monthly_amount', 0)
            items = category.get('items', [])
            
            formatted.append(f"  • {category_name}: ${monthly_amount:,.0f}")
            for item in items[:3]:  # Show up to 3 items per category
                formatted.append(f"    - {item.get('description', 'Unknown')}: ${item.get('monthly_amount', 0):,.0f}")
        
        return '\n'.join(formatted)
    
    def _format_expense_breakdown(self, expense_breakdown: List[Dict]) -> str:
        """Format expense breakdown by category"""
        if not expense_breakdown:
            return "  • No expense breakdown available"
        
        formatted = []
        for category in expense_breakdown:
            category_name = category.get('category', 'Unknown')
            monthly_amount = category.get('monthly_amount', 0)
            items = category.get('items', [])
            
            formatted.append(f"  • {category_name}: ${monthly_amount:,.0f}")
            for item in items[:3]:  # Show up to 3 items per category
                formatted.append(f"    - {item.get('description', 'Unknown')}: ${item.get('monthly_amount', 0):,.0f}")
        
        return '\n'.join(formatted)

    def _format_key_financial_metrics(self, financial_data: Dict) -> str:
        """Format key financial health metrics"""
        try:
            # Calculate emergency fund coverage (months of expenses)
            monthly_expenses = financial_data.get('monthly_expenses', 0)
            cash_total = financial_data.get('cash_accounts', {}).get('total', 0)
            emergency_months = (cash_total / monthly_expenses) if monthly_expenses > 0 else 0

            # Calculate liquidity ratio (liquid assets / total assets)
            total_assets = financial_data.get('total_assets', 0)
            liquidity_ratio = (cash_total / total_assets * 100) if total_assets > 0 else 0

            # Get debt-to-income ratio
            dti_ratio = financial_data.get('debt_to_income', 0)

            # Calculate financial health score (simple scoring system)
            health_score = 0
            # Emergency fund scoring (0-25 points)
            if emergency_months >= 6:
                health_score += 25
            elif emergency_months >= 3:
                health_score += 20
            elif emergency_months >= 1:
                health_score += 15
            else:
                health_score += 5

            # DTI scoring (0-25 points)
            if dti_ratio <= 20:
                health_score += 25
            elif dti_ratio <= 30:
                health_score += 20
            elif dti_ratio <= 40:
                health_score += 15
            else:
                health_score += 5

            # Savings rate scoring (0-25 points)
            savings_rate = financial_data.get('savings_rate', 0)
            if savings_rate >= 20:
                health_score += 25
            elif savings_rate >= 15:
                health_score += 20
            elif savings_rate >= 10:
                health_score += 15
            else:
                health_score += 5

            # Net worth progress scoring (0-25 points)
            retirement_progress = financial_data.get('retirement_progress', 0)
            if retirement_progress >= 75:
                health_score += 25
            elif retirement_progress >= 50:
                health_score += 20
            elif retirement_progress >= 25:
                health_score += 15
            else:
                health_score += 5

            # Asset allocation score (basic diversification check)
            total_assets = financial_data.get('total_assets', 0)
            if total_assets > 0:
                real_estate_pct = (financial_data.get('real_estate_properties', {}).get('total', 0) / total_assets) * 100
                investment_pct = (financial_data.get('investment_accounts', {}).get('total', 0) / total_assets) * 100
                retirement_pct = (financial_data.get('retirement_accounts', {}).get('total', 0) / total_assets) * 100

                # Check for reasonable diversification (not too concentrated)
                max_allocation = max(real_estate_pct, investment_pct + retirement_pct, cash_total / total_assets * 100)
                if max_allocation < 80:  # Not overly concentrated
                    allocation_score = 9
                elif max_allocation < 90:
                    allocation_score = 7
                else:
                    allocation_score = 5
            else:
                allocation_score = 5
                real_estate_pct = 0

            return f"""  • Debt-to-Income Ratio: {dti_ratio:.1f}% {'(Excellent)' if dti_ratio <= 20 else '(Good)' if dti_ratio <= 30 else '(Fair)' if dti_ratio <= 40 else '(Needs Improvement)'}
  • Emergency Fund Coverage: {emergency_months:.1f} months {'(Excellent)' if emergency_months >= 6 else '(Good)' if emergency_months >= 3 else '(Fair)' if emergency_months >= 1 else '(Insufficient)'}
  • Liquidity Ratio: {liquidity_ratio:.1f}% of total assets in cash
  • Savings Rate: {savings_rate:.1f}% {'(Excellent)' if savings_rate >= 20 else '(Good)' if savings_rate >= 15 else '(Fair)' if savings_rate >= 10 else '(Low)'}
  • Asset Allocation Score: {allocation_score}/10 (Diversification: RE {real_estate_pct:.1f}%)
  • Financial Health Score: {health_score}/100 {'(Excellent)' if health_score >= 80 else '(Good)' if health_score >= 65 else '(Fair)' if health_score >= 50 else '(Needs Improvement)'}"""

        except Exception as e:
            logger.warning(f"Error calculating key financial metrics: {str(e)}")
            return "  • Key financial metrics calculation error"

    def _format_tax_profile(self, financial_data: Dict) -> str:
        """Format comprehensive tax profile information"""
        try:
            # Get basic tax info
            federal_bracket = financial_data.get('tax_bracket', 0)
            filing_status = financial_data.get('filing_status', 'Unknown')
            state = financial_data.get('state', 'Unknown')

            # Calculate effective tax rate estimate
            monthly_income = financial_data.get('monthly_income', 0)
            annual_income = monthly_income * 12

            # State tax rates (simplified lookup - could be enhanced with a proper state tax table)
            state_tax_rates = {
                'CA': 9.3, 'NY': 6.8, 'NJ': 8.9, 'CT': 6.9, 'MA': 5.0,
                'IL': 4.9, 'MD': 5.7, 'VA': 5.75, 'PA': 3.1, 'WA': 0.0,
                'TX': 0.0, 'FL': 0.0, 'NV': 0.0, 'TN': 0.0, 'NH': 0.0,
                'WY': 0.0, 'SD': 0.0, 'AK': 0.0, 'MT': 6.9, 'ND': 2.9
            }

            state_rate = state_tax_rates.get(state, 5.0)  # Default 5% if state not found

            # Estimate effective federal rate (simplified)
            if annual_income <= 22000:
                effective_federal = 10
            elif annual_income <= 89450:
                effective_federal = 12
            elif annual_income <= 190750:
                effective_federal = 16
            elif annual_income <= 364200:
                effective_federal = 20
            else:
                effective_federal = 24

            combined_marginal = federal_bracket + state_rate
            estimated_effective = effective_federal + (state_rate * 0.8)  # State effective usually lower

            # SALT limitation impact (for high-tax states)
            salt_limited = state_rate > 6.0 and annual_income > 100000
            salt_impact = "SALT deduction limited ($10K cap)" if salt_limited else "Full SALT deduction available"

            # Tax optimization opportunities
            optimization_tips = []
            if federal_bracket >= 22:  # Higher bracket taxpayers
                optimization_tips.append("Consider tax-advantaged retirement contributions")
            if state_rate > 7:
                optimization_tips.append("Municipal bonds may provide tax-free income")
            if annual_income > 200000:
                optimization_tips.append("Review estimated tax payments to avoid penalties")

            return f"""  • Filing Status: {filing_status}
  • Federal Marginal Rate: {federal_bracket}%
  • State: {state} (Est. {state_rate}% rate)
  • Combined Marginal Rate: {combined_marginal:.1f}%
  • Estimated Effective Rate: {estimated_effective:.1f}%
  • SALT Impact: {salt_impact}
  • Annual Income: ${annual_income:,.0f}
  • Tax Optimization: {'; '.join(optimization_tips) if optimization_tips else 'Standard deduction likely optimal'}"""

        except Exception as e:
            logger.warning(f"Error formatting tax profile: {str(e)}")
            return f"  • Tax Filing Status: {financial_data.get('filing_status', 'Unknown')}\n  • Federal Tax Bracket: {financial_data.get('tax_bracket', 'Unknown')}%"


# Global instance
complete_financial_context = CompleteFinancialContextService()