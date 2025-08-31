"""
Dynamic Prompt Builder Service
Creates focused, intent-specific prompts for financial advisory
"""

from typing import Dict, List
from app.services.intent_service import FinancialIntent
# Context validation now handled by CompleteFinancialContextService
import structlog

logger = structlog.get_logger()

class PromptBuilderService:
    """Build targeted prompts based on financial intent and context"""
    
    def build_system_prompt(self, intent: FinancialIntent, context: Dict, user_essentials: Dict, retirement_analysis: Dict = None) -> str:
        """
        Build a focused system prompt based on detected intent
        """
        # Base advisor persona
        base_prompt = f"""You are an expert financial advisor specializing in comprehensive financial planning.

CLIENT PROFILE:
- Name: {user_essentials.get('name', 'Client')}
- Age: {user_essentials.get('age', 'Unknown')}
- Location: {user_essentials.get('state', 'Unknown')}
- Net Worth: ${user_essentials.get('net_worth', 0):,.0f}
- Monthly Surplus: ${user_essentials.get('monthly_surplus', 0):,.0f}
- Risk Tolerance: {user_essentials.get('risk_tolerance', 'Unknown')}
"""
        
        # Add intent-specific context and instructions
        intent_section = self._get_intent_specific_prompt(intent, context, retirement_analysis)
        
        # Add general guidelines
        guidelines = self._get_response_guidelines(intent)
        
        return base_prompt + intent_section + guidelines
    
    def build_universal_system_prompt(self, intent: FinancialIntent, context: Dict, universal_context: str, retirement_analysis: Dict = None, session_context: Dict = None) -> str:
        """
        Build system prompt that ALWAYS includes core user facts regardless of intent
        This prevents the system from "forgetting" established facts
        """
        
        # Use session context for validation if available, otherwise fall back to vector context
        validation_context = session_context if session_context else context
        
        # Validate context against industry benchmarks
        validation_results = context_validator.validate_context(validation_context, {'age': validation_context.get('age', 54)})
        validation_summary = context_validator.get_validation_summary(validation_results)
        
        # Build validation section for the prompt
        validation_section = self._build_validation_section(validation_results, validation_summary)
        
        # Universal context that applies to ALL financial questions
        base_prompt = f"""You are an expert financial advisor providing personalized guidance.

UNIVERSAL USER CONTEXT (NEVER IGNORE THESE FACTS):
{universal_context}

{validation_section}

CRITICAL: The above facts are ESTABLISHED and should influence ALL your responses regardless of the specific question asked. 
For example:
- If the user asks about goals, reference their actual financial targets from the context
- If they ask about financial status, mention their actual retirement readiness percentage
- Always personalize with their name and current financial position from the data
- Maintain consistency with previous analyses
- Use ONLY the numbers provided in the context - do not make up or assume values
- ALWAYS consider the validation findings when providing advice

"""
        
        # Add intent-specific analysis
        intent_section = self._get_intent_specific_prompt(intent, context, retirement_analysis)
        
        # Add response guidelines that emphasize consistency
        guidelines = self._get_universal_response_guidelines(intent)
        
        return base_prompt + intent_section + guidelines
    
    def _get_intent_specific_prompt(self, intent: FinancialIntent, context: Dict, retirement_analysis: Dict = None) -> str:
        """Get specific prompt section based on intent"""
        
        primary_data = context.get('primary_data', [])
        supporting_data = context.get('supporting_data', [])
        
        intent_prompts = {
            FinancialIntent.RETIREMENT: self._build_retirement_prompt,
            FinancialIntent.DEBT_MANAGEMENT: self._build_debt_prompt,
            FinancialIntent.INVESTMENT: self._build_investment_prompt,
            FinancialIntent.TAX_PLANNING: self._build_tax_prompt,
            FinancialIntent.BUDGET: self._build_budget_prompt,
            FinancialIntent.EMERGENCY_FUND: self._build_emergency_prompt,
            FinancialIntent.EDUCATION: self._build_education_prompt,
            FinancialIntent.REAL_ESTATE: self._build_real_estate_prompt,
            FinancialIntent.NET_WORTH: self._build_net_worth_prompt,
            FinancialIntent.CASH_FLOW: self._build_cash_flow_prompt,
            FinancialIntent.SAVINGS: self._build_savings_prompt,
            FinancialIntent.GOAL_PLANNING: self._build_goal_prompt,
            FinancialIntent.GENERAL: self._build_general_prompt
        }
        
        builder_func = intent_prompts.get(intent, self._build_general_prompt)
        if intent == FinancialIntent.RETIREMENT and retirement_analysis:
            return self._build_retirement_prompt_with_analysis(primary_data, supporting_data, retirement_analysis)
        else:
            return builder_func(primary_data, supporting_data)
    
    def _build_retirement_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

RETIREMENT PLANNING FOCUS:
Primary Data:
{self._format_data_list(primary_data)}

Supporting Information:
{self._format_data_list(supporting_data)}

RETIREMENT ANALYSIS REQUIREMENTS:
1. Calculate retirement readiness using 4% withdrawal rule
2. Account for Social Security benefits if present in data
3. Consider all retirement accounts (401k, IRA, pensions)
4. Factor in current age and retirement timeline
5. Include healthcare and inflation considerations
6. Show specific dollar amounts and percentages
7. Provide actionable next steps with timelines

KEY CALCULATIONS TO INCLUDE:
- Required retirement portfolio size
- Current retirement savings progress
- Monthly savings needed (if behind)
- Social Security impact on required savings
- Asset allocation recommendations for age
"""

    def _build_retirement_prompt_with_analysis(self, primary_data: List[str], supporting_data: List[str], retirement_analysis: Dict) -> str:
        """Build retirement prompt with pre-calculated analysis"""
        
        # Extract key analysis data
        user_info = retirement_analysis.get('user_info', {})
        expenses = retirement_analysis.get('expenses', {})
        ss = retirement_analysis.get('social_security', {})
        portfolio = retirement_analysis.get('portfolio_analysis', {})
        status = retirement_analysis.get('status', {})
        user_goal = retirement_analysis.get('user_goal', {})
        strengths = retirement_analysis.get('strengths', [])
        recommendations = retirement_analysis.get('recommendations', [])
        
        return f"""

RETIREMENT PLANNING FOCUS WITH PRE-CALCULATED ANALYSIS:

CLIENT RETIREMENT PROFILE:
- Current Age: {user_info.get('current_age', 'Unknown')}
- Target Retirement Age: {user_info.get('target_retirement_age', 'Unknown')}
- Years to Retirement: {user_info.get('years_to_retirement', 'Unknown')}

EXPENSE PROJECTIONS (CALCULATED):
- Current Annual Expenses: ${expenses.get('current_annual', 0):,.0f}
- Future Annual Expenses (at retirement): ${expenses.get('future_annual', 0):,.0f}
- Current Monthly Expenses: ${expenses.get('monthly_current', 0):,.0f}

SOCIAL SECURITY BENEFITS (VERIFIED):
- Monthly Benefit: ${ss.get('monthly_benefit', 0):,.0f}
- Annual Benefit: ${ss.get('annual_benefit', 0):,.0f}
- Benefit Starts at Age: {ss.get('starts_at_age', 67)}

PORTFOLIO ANALYSIS (ACCURATE CALCULATIONS):
- Income Needed from Portfolio: ${portfolio.get('income_needed_from_portfolio', 0):,.0f}/year
- Required Portfolio Size (4% rule): ${portfolio.get('required_portfolio_size', 0):,.0f}
- Total Retirement-Capable Assets: ${portfolio.get('total_retirement_capable', 0):,.0f}

DETAILED ASSET BREAKDOWN:
{self._format_detailed_asset_breakdown(portfolio.get('asset_breakdown', {}), portfolio.get('current_retirement_assets', {}))}

- Surplus/Deficit: ${portfolio.get('surplus_deficit', 0):,.0f}
- Completion Percentage: {portfolio.get('completion_percentage', 0):.1f}%

RETIREMENT STATUS: {status.get('overall', 'UNKNOWN')}
Status Message: {status.get('message', 'Analysis unavailable')}
Early Retirement Possible at Age: {status.get('early_retirement_age', 'Unknown')}

USER'S RETIREMENT GOAL & TIMELINE:
- Target Amount: ${user_goal.get('target_amount', 0):,.0f}
- Progress Toward Goal: {user_goal.get('progress_toward_goal', 0):.1f}%

GOAL ACHIEVEMENT TIMELINE:
{self._format_goal_timeline(user_goal.get('goal_timeline', {}))}

IDENTIFIED STRENGTHS:
{self._format_strengths_list(strengths)}

PRE-CALCULATED RECOMMENDATIONS:
{self._format_recommendations_list(recommendations)}

Additional Context:
Primary Data:
{self._format_data_list(primary_data)}

Supporting Information:
{self._format_data_list(supporting_data)}

CRITICAL REQUIREMENTS FOR YOUR RESPONSE:
1. Use ONLY the pre-calculated numbers above - DO NOT perform your own calculations
2. The math has been done correctly in Python - trust these numbers
3. Address the user's specific retirement question using this analysis
4. Reference the surplus/deficit to determine if they're ahead or behind
5. If surplus is positive, they can consider early retirement or reduced savings
6. If deficit exists, provide specific guidance on closing the gap
7. Always mention Social Security benefits as a key component
8. Use the exact dollar amounts and percentages provided
9. Be encouraging if they're ahead of schedule
10. Provide specific, actionable next steps based on their status

ENHANCED DISPLAY REQUIREMENTS:
11. Show the DETAILED ASSET BREAKDOWN with specific amounts and percentages
12. Include the GOAL ACHIEVEMENT TIMELINE with milestone years
13. Reference specific years when they'll reach $2.5M, $3M, and $3.5M goals
14. Be more definitive about early retirement if they have surplus
15. Explain what the asset breakdown means for diversification

MATH VERIFICATION (DO NOT RECALCULATE):
✅ Future expenses calculated with 3% inflation over {user_info.get('years_to_retirement', 0)} years
✅ Social Security reduces required portfolio income by ${ss.get('annual_benefit', 0):,.0f}/year
✅ 4% withdrawal rule applied: ${portfolio.get('income_needed_from_portfolio', 0):,.0f} ÷ 0.04 = ${portfolio.get('required_portfolio_size', 0):,.0f}
✅ All retirement assets included: 401k, investments, Bitcoin, home equity
✅ Current completion: {portfolio.get('completion_percentage', 0):.1f}% of retirement needs met
"""

    def _build_debt_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

DEBT MANAGEMENT FOCUS:
Primary Data:
{self._format_data_list(primary_data)}

Supporting Information:
{self._format_data_list(supporting_data)}

DEBT ANALYSIS REQUIREMENTS:
1. Prioritize debts by interest rate (debt avalanche strategy)
2. Calculate total monthly debt payments and DTI ratio
3. Show payoff timelines for current vs accelerated payments
4. Calculate interest savings from early payoff
5. Consider debt consolidation if beneficial
6. Factor in available monthly surplus for extra payments
7. Address credit score impact

KEY CALCULATIONS TO INCLUDE:
- Debt-to-income ratio analysis
- Payoff timeline for each debt
- Total interest savings from extra payments
- Optimal payment strategy (avalanche vs snowball)
- Monthly surplus available for debt payments
"""

    def _build_investment_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

INVESTMENT ALLOCATION ANALYSIS:
Primary Data:
{self._format_data_list(primary_data)}

Supporting Information:
{self._format_data_list(supporting_data)}

CRITICAL: The user's asset allocation is ALREADY KNOWN from the universal context above. Do NOT ask them for information you already have.

INVESTMENT ANALYSIS REQUIREMENTS:
1. USE THE ASSET BREAKDOWN provided in the universal context to analyze current allocation
2. Calculate current percentages (exclude home equity for investment allocation)
3. Compare against age-appropriate target allocation for someone approaching retirement
4. Identify specific rebalancing actions using their ACTUAL account balances
5. Address any over-concentration in specific assets (like excessive cash or crypto)
6. Recommend tax-efficient moves based on their account types
7. Consider their 4-year retirement timeline in recommendations

REQUIRED CALCULATIONS TO SHOW:
- Current allocation percentages (stocks/bonds/alternatives/cash)
- Target allocation for their age and retirement timeline
- Specific dollar amounts to move between asset classes
- Expected risk reduction and return impact
- Tax implications of recommended changes

DO NOT ask for additional information - you have their complete financial picture in the context above.
"""

    def _build_budget_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

BUDGET ANALYSIS FOCUS:
Primary Data:
{self._format_data_list(primary_data)}

Supporting Information:
{self._format_data_list(supporting_data)}

BUDGET ANALYSIS REQUIREMENTS:
1. Break down income vs expenses by category
2. Calculate savings rate and compare to recommended 20%
3. Identify areas for expense reduction
4. Show monthly surplus/deficit clearly
5. Recommend budget allocation percentages
6. Address irregular expenses and seasonal variations
7. Suggest expense tracking methods

KEY METRICS TO INCLUDE:
- Savings rate percentage
- Expense breakdown by category
- Monthly surplus available
- Budget optimization recommendations
- Spending ratios vs recommended guidelines
"""

    def _build_tax_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

TAX PLANNING FOCUS:
Primary Data:
{self._format_data_list(primary_data)}

Supporting Information:
{self._format_data_list(supporting_data)}

TAX PLANNING REQUIREMENTS:
1. Analyze current tax bracket and marginal rates
2. Review retirement account contribution opportunities
3. Consider Roth vs traditional IRA/401k strategies
4. Evaluate tax-loss harvesting opportunities
5. Address state vs federal tax implications
6. Review HSA contributions if applicable
7. Plan for tax-efficient investment allocation

KEY STRATEGIES TO INCLUDE:
- Optimal retirement account contributions
- Tax-efficient asset location
- Timing of income and deductions
- Roth conversion opportunities
- HSA maximization strategies
"""

    def _build_emergency_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

EMERGENCY FUND ANALYSIS:
Primary Data:
{self._format_data_list(primary_data)}

Supporting Information:
{self._format_data_list(supporting_data)}

EMERGENCY FUND REQUIREMENTS:
1. Calculate recommended emergency fund (3-6 months expenses)
2. Evaluate current liquid savings adequacy
3. Identify best high-yield savings accounts
4. Plan building emergency fund without sacrificing other goals
5. Consider job stability and income variability
6. Address accessibility and safety of funds

KEY CALCULATIONS:
- Monthly expenses for emergency planning
- Current months of coverage available
- Target emergency fund amount
- Timeline to build adequate fund
- Best savings vehicles for emergency funds
"""

    def _build_net_worth_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

NET WORTH ANALYSIS:
Primary Data:
{self._format_data_list(primary_data)}

Supporting Information:
{self._format_data_list(supporting_data)}

NET WORTH ANALYSIS REQUIREMENTS:
1. Break down total assets by category
2. Analyze debt-to-asset ratios
3. Show net worth trend and growth rate
4. Compare to age-based benchmarks
5. Identify opportunities to increase assets
6. Address ways to reduce liabilities
7. Set net worth growth targets

KEY METRICS:
- Current net worth breakdown
- Asset allocation percentages
- Debt-to-asset ratio analysis
- Net worth growth recommendations
- Benchmark comparisons for age
"""

    def _build_cash_flow_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

CASH FLOW ANALYSIS:
Primary Data:
{self._format_data_list(primary_data)}

Supporting Information:
{self._format_data_list(supporting_data)}

CASH FLOW REQUIREMENTS:
1. Analyze monthly income vs expenses
2. Calculate and optimize monthly surplus
3. Identify seasonal cash flow variations
4. Plan for irregular expenses
5. Optimize timing of payments and income
6. Address cash flow improvement strategies

KEY ANALYSIS:
- Monthly cash flow breakdown
- Surplus optimization opportunities  
- Income and expense timing
- Emergency cash flow planning
- Growth strategies for positive cash flow
"""

    def _build_general_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

COMPREHENSIVE FINANCIAL ANALYSIS:
Primary Data:
{self._format_data_list(primary_data)}

Supporting Information:  
{self._format_data_list(supporting_data)}

GENERAL ANALYSIS REQUIREMENTS:
1. Provide holistic financial health assessment
2. Identify top 3 priority areas for improvement
3. Give specific, actionable recommendations
4. Consider all aspects: savings, debt, investments, protection
5. Address both short-term and long-term planning
6. Provide clear next steps with timelines
"""

    def _build_savings_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

SAVINGS OPTIMIZATION:
Primary Data:
{self._format_data_list(primary_data)}

SAVINGS REQUIREMENTS:
- Analyze current savings rate vs recommendations
- Evaluate savings vehicles (high-yield, CDs, money market)
- Plan automatic savings strategies
- Balance savings with other financial goals
- Optimize for both liquidity and returns
"""

    def _build_goal_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

GOAL PLANNING ANALYSIS:
Primary Data:
{self._format_data_list(primary_data)}

GOAL ANALYSIS REQUIREMENTS:
- Evaluate progress toward stated financial goals
- Calculate monthly savings required
- Prioritize multiple competing goals
- Adjust timelines based on available resources
- Create actionable milestone tracking
"""

    def _build_education_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

EDUCATION PLANNING:
Primary Data:
{self._format_data_list(primary_data)}

EDUCATION REQUIREMENTS:
- Analyze 529 plan contributions and performance
- Calculate education funding gaps
- Consider tax advantages of education savings
- Plan for multiple children if applicable
- Balance education vs retirement priorities
"""

    def _build_real_estate_prompt(self, primary_data: List[str], supporting_data: List[str]) -> str:
        return f"""

REAL ESTATE ANALYSIS:
Primary Data:
{self._format_data_list(primary_data)}

REAL ESTATE REQUIREMENTS:
- Evaluate home equity and mortgage optimization
- Consider refinancing opportunities
- Analyze rental property cash flow if applicable  
- Review property insurance and taxes
- Plan for maintenance and capital improvements
"""

    def _format_data_list(self, data_list: List[str]) -> str:
        """Format data list for prompt inclusion"""
        if not data_list:
            return "No specific data available for this analysis."
        
        formatted = ""
        for i, item in enumerate(data_list[:8], 1):  # Limit to top 8 items
            # Clean up the data formatting
            clean_item = item.strip()
            if clean_item:
                formatted += f"{i}. {clean_item}\n"
        
        return formatted

    def _format_retirement_assets(self, assets: Dict[str, float]) -> str:
        """Format retirement assets breakdown"""
        if not assets:
            return "No asset breakdown available"
        
        formatted = ""
        for asset_type, amount in assets.items():
            formatted += f"  • {asset_type.replace('_', ' ').title()}: ${amount:,.0f}\n"
        return formatted
    
    def _format_strengths_list(self, strengths: List[str]) -> str:
        """Format strengths list"""
        if not strengths:
            return "Analysis pending"
        
        formatted = ""
        for strength in strengths:
            formatted += f"✅ {strength}\n"
        return formatted
    
    def _format_recommendations_list(self, recommendations: List[str]) -> str:
        """Format recommendations list"""
        if not recommendations:
            return "Analysis pending"
        
        formatted = ""
        for rec in recommendations:
            formatted += f"💡 {rec}\n"
        return formatted
    
    def _format_detailed_asset_breakdown(self, asset_breakdown: Dict, raw_assets: Dict) -> str:
        """Format detailed asset breakdown with amounts and percentages"""
        if not asset_breakdown and not raw_assets:
            return "Asset breakdown not available"
        
        formatted = ""
        
        # Use breakdown if available, otherwise format raw assets
        if asset_breakdown:
            for asset_type, details in asset_breakdown.items():
                name = asset_type.replace('_', ' ').title()
                amount = details.get('amount', 0)
                percentage = details.get('percentage', 0)
                formatted += f"  • {name}: ${amount:,.0f} ({percentage:.1f}%)\n"
        else:
            # Fallback to raw assets
            total = sum(raw_assets.values()) if raw_assets else 1
            for asset_type, amount in raw_assets.items():
                name = asset_type.replace('_', ' ').title()
                percentage = (amount / total * 100) if total > 0 else 0
                formatted += f"  • {name}: ${amount:,.0f} ({percentage:.1f}%)\n"
        
        return formatted
    
    def _format_goal_timeline(self, timeline: Dict) -> str:
        """Format goal achievement timeline"""
        if not timeline:
            return "Timeline calculation not available"
        
        if timeline.get('goal_achieved'):
            return f"🎉 {timeline.get('message', 'Goal already achieved!')}"
        
        formatted = f"📈 {timeline.get('message', 'Timeline not available')}\n"
        
        # Add milestone projections
        milestones = timeline.get('milestone_years', [])
        if milestones:
            formatted += "\nKey Milestones:\n"
            for milestone in milestones:
                year = milestone.get('year', 'TBD')
                age = milestone.get('age', 'TBD')
                description = milestone.get('description', '')
                formatted += f"  • {year} (age {age}): {description}\n"
        
        # Add a few year projections
        projections = timeline.get('projections', [])
        if projections:
            formatted += "\nProjected Growth:\n"
            for i, proj in enumerate(projections[:5]):  # Show first 5 years
                year = proj.get('year', 'TBD')
                age = proj.get('age', 'TBD')
                assets = proj.get('projected_assets', 0)
                formatted += f"  • {year} (age {age}): ${assets:,.0f}\n"
        
        return formatted

    def _build_validation_section(self, validation_results, validation_summary) -> str:
        """Build validation section for the prompt based on benchmark analysis"""
        
        if not validation_results:
            return ""
        
        critical_findings = [v for v in validation_results if v.severity.value == 'critical']
        warning_findings = [v for v in validation_results if v.severity.value == 'warning']
        
        validation_text = "BENCHMARK ANALYSIS & VALIDATION:\n"
        
        # Overall assessment
        overall = validation_summary.get('overall_assessment', 'good')
        validation_text += f"Overall Financial Health: {overall.upper().replace('_', ' ')}\n"
        
        # Critical issues that MUST be addressed
        if critical_findings:
            validation_text += "\n🚨 CRITICAL CONCERNS (ADDRESS IMMEDIATELY):\n"
            for finding in critical_findings:
                validation_text += f"  • {finding.message}\n"
                if finding.recommendation:
                    validation_text += f"    → {finding.recommendation}\n"
        
        # Warning issues that should be considered
        if warning_findings:
            validation_text += "\n⚠️ AREAS FOR IMPROVEMENT:\n"
            for finding in warning_findings:
                validation_text += f"  • {finding.message}\n"
                if finding.recommendation:
                    validation_text += f"    → {finding.recommendation}\n"
        
        # Positive findings
        info_findings = [v for v in validation_results if v.severity.value == 'info']
        if info_findings:
            validation_text += "\n✅ STRENGTHS:\n"
            for finding in info_findings[:3]:  # Show top 3 strengths
                validation_text += f"  • {finding.message}\n"
        
        validation_text += f"\nValidation Summary: {validation_summary['total_findings']} findings "
        validation_text += f"({validation_summary['by_severity']['critical']} critical, "
        validation_text += f"{validation_summary['by_severity']['warning']} warnings)\n"
        
        return validation_text

    def _get_universal_response_guidelines(self, intent: FinancialIntent) -> str:
        """Get response guidelines that emphasize consistency across all conversations"""
        
        guidelines = f"""

UNIVERSAL RESPONSE REQUIREMENTS:
1. ALWAYS reference the user by name and acknowledge their established financial status
2. NEVER contradict previously established facts (retirement readiness, goals, etc.)
3. Build upon existing context rather than starting from scratch
4. Reference their ACTUAL goals and financial targets as provided in the context
5. Use their REAL financial numbers - net worth, income, expenses, etc.
6. Maintain the same tone and level of detail as previous responses
7. If you cannot find specific information, ask clarifying questions rather than making assumptions

INTENT-SPECIFIC GUIDANCE FOR {intent.value.upper()}:
Use the user's actual financial data from the context above to provide personalized advice.

CONSISTENCY CHECKS:
- Does this response align with their actual financial situation from the context?
- Am I referencing the correct goal amounts and timelines from their data?
- Would this advice contradict what the data shows about their situation?
- Am I maintaining appropriate confidence level based on their real financial strength?
"""
        
        return guidelines

    def _get_intent_specific_guidelines(self, intent: FinancialIntent) -> str:
        """Get specific guidelines for each intent type - REMOVED HARD-CODED VALUES"""
        
        guidelines_map = {
            FinancialIntent.RETIREMENT: "Focus on their actual retirement funding status and early retirement possibilities based on their data",
            FinancialIntent.GOAL_PLANNING: "Reference their actual financial goals and timeline from the context",
            FinancialIntent.INVESTMENT: "Consider their current financial position and asset allocation from their data",
            FinancialIntent.DEBT_MANAGEMENT: "Acknowledge their actual DTI ratio and monthly surplus from the context",
            FinancialIntent.TAX_PLANNING: "Factor in their actual savings rate and asset types from their portfolio",
            FinancialIntent.BUDGET: "Reference their actual monthly surplus and savings rate from the data",
            FinancialIntent.NET_WORTH: "Build on their actual net worth and asset breakdown provided",
            FinancialIntent.CASH_FLOW: "Acknowledge their actual cash flow situation from the financial data",
            FinancialIntent.GENERAL: "Provide holistic advice considering their actual overall financial position"
        }
        
        return guidelines_map.get(intent, "Provide specific, actionable advice based on their actual financial status from the context")

    def _get_response_guidelines(self, intent: FinancialIntent) -> str:
        """Get response guidelines tailored to intent"""
        
        calculation_intents = {
            FinancialIntent.RETIREMENT,
            FinancialIntent.DEBT_MANAGEMENT, 
            FinancialIntent.GOAL_PLANNING,
            FinancialIntent.TAX_PLANNING
        }
        
        guidelines = """

RESPONSE GUIDELINES:
1. Be specific with dollar amounts, percentages, and timelines
2. Provide clear, actionable next steps
3. Use bullet points for easy readability  
4. Include relevant calculations with assumptions shown
5. Address both short-term (1 year) and long-term implications
6. Consider tax implications where relevant
7. Stay within your expertise - refer to professionals when needed
8. Be encouraging but realistic about financial goals

RESPONSE STYLE:
- Use conversational, professional tone
- Avoid jargon - explain financial terms simply
- Focus on answering the specific question asked
- Provide context for recommendations
- Include confidence levels when making projections
"""

        if intent in calculation_intents:
            guidelines += """
- Show your math clearly with step-by-step calculations
- State assumptions used in calculations
- Provide ranges rather than exact predictions
- Include sensitivity analysis when relevant"""

        return guidelines