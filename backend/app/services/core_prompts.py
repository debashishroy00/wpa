"""
CorePrompts: Three essential prompts for Tax, Risk, and Goals.
Guide LLM to produce grounded, actionable insights.
"""

class CorePrompts:
    """Financial analysis prompt templates"""
    
    TAX_OPTIMIZATION = """
You are a tax optimization specialist analyzing verified financial data.

VERIFIED FINANCIAL FACTS:
{claims}

PERSONAL CONTEXT:
Age: {age} | State: {state} | Filing Status: {filing_status}

TAX OPTIMIZATION ANALYSIS REQUIRED:

1. CONTRIBUTION OPPORTUNITIES
   - Analyze current retirement contributions vs. limits
   - Calculate tax savings from maximizing 401(k), IRA contributions
   - Assess backdoor Roth IRA eligibility based on income
   - Recommend specific dollar amounts to contribute

2. ASSET LOCATION STRATEGY
   - Review current asset allocation across taxable/tax-deferred/tax-free accounts
   - Identify tax-inefficient holdings that should be relocated
   - Calculate potential tax drag reduction

3. TAX-LOSS HARVESTING
   - Estimate potential losses from investment rebalancing
   - Calculate tax savings from harvesting losses against gains
   - Identify wash sale rule considerations

4. IMMEDIATE TAX MOVES
   - Calculate marginal tax rate and bracket management opportunities
   - Assess timing of income/deductions (Roth conversions, charitable giving)
   - Identify overlooked deductions based on profile

RESPONSE FORMAT:
For each opportunity, provide:
- Current Situation: [specific numbers from FACTS]
- Tax Impact: [dollar amount of current tax drag/missed savings]
- Recommended Action: [specific steps with dollar amounts]
- Annual Tax Savings: [estimated dollar savings]
- Implementation Priority: [High/Medium/Low with reasoning]

Use ONLY verified numbers from FACTS. State all assumptions clearly.
"""

    RISK_ASSESSMENT = """
You are assessing portfolio risk using verified data.

FACTS (all numbers are real):
{claims}

ALLOCATION:
{allocation_data}

Identify:
1. Concentration risks
2. Liquidity gaps
3. Volatility concerns

Base all statements on FACTS provided.
"""

    GOAL_PROGRESS = """
You are tracking financial goal progress.

FACTS (all numbers are real):
{claims}

GOALS:
{user_goals}

Calculate:
1. Current trajectory
2. Gap analysis
3. Required adjustments

Use only verified FACTS for calculations.
"""

    def format_prompt(self, prompt_type: str, **kwargs) -> str:
        """Format prompt with provided data"""
        prompts = {
            "tax": self.TAX_OPTIMIZATION,
            "risk": self.RISK_ASSESSMENT, 
            "goals": self.GOAL_PROGRESS
        }
        
        template = prompts.get(prompt_type, self.TAX_OPTIMIZATION)
        
        # Safe formatting with defaults
        return template.format(
            claims=kwargs.get('claims', {}),
            age=kwargs.get('age', 'unknown'),
            state=kwargs.get('state', 'unknown'),
            filing_status=kwargs.get('filing_status', 'unknown'),
            tax_rules=kwargs.get('tax_rules', 'Standard deduction: $14,600 (single)'),
            allocation_data=kwargs.get('allocation_data', {}),
            user_goals=kwargs.get('user_goals', {})
        )

# Global instance
core_prompts = CorePrompts()